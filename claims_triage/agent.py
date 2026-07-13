"""
ClaimsTriageAgent
=================
Multi-stage Claude-powered insurance claims triage pipeline.

Architecture
------------
Each stage calls Claude's messages API with a forced tool_choice, ensuring
structured JSON output at every step — suitable for batch processing thousands
of claims with deterministic, auditable results.

  Stage 1 · extract_claim_fields   →  structured field extraction
  Stage 2 · classify_claim         →  peril category + severity
  Stage 3 · assess_completeness    →  missing docs / completeness score
  Stage 4 · generate_triage_decision → routing decision + rationale

Why forced tool_choice?
-----------------------
Compared to free-form text generation, forcing tool use makes Claude output
schema-valid JSON on every call. This removes all output parsing code, enables
direct downstream processing, and makes the pipeline fully testable via mocks.
"""
from __future__ import annotations

import json
import os
import time
from dataclasses import dataclass, field
from typing import Any

from .tools import EXTRACT_TOOL, CLASSIFY_TOOL, ASSESS_TOOL, DECIDE_TOOL


# ── Result model ──────────────────────────────────────────────────────────────

@dataclass
class TriageResult:
    """Full pipeline output for one claim."""

    claim_id: str
    raw_text: str
    extracted: dict[str, Any] = field(default_factory=dict)
    classification: dict[str, Any] = field(default_factory=dict)
    completeness: dict[str, Any] = field(default_factory=dict)
    decision: dict[str, Any] = field(default_factory=dict)
    processing_time_ms: int = 0
    model: str = ""
    error: str | None = None

    # ── Convenience properties ────────────────────────────────────────────────

    @property
    def triage_decision(self) -> str:
        return self.decision.get("decision", "unknown")

    @property
    def severity(self) -> str:
        return self.classification.get("severity", "unknown")

    @property
    def peril(self) -> str:
        return self.classification.get("peril_category", "unknown")

    @property
    def completeness_score(self) -> float:
        return float(self.completeness.get("completeness_score", 0.0))

    def to_dict(self) -> dict:
        return {
            "claim_id": self.claim_id,
            "raw_text": self.raw_text,
            "extracted": self.extracted,
            "classification": self.classification,
            "completeness": self.completeness,
            "decision": self.decision,
            "processing_time_ms": self.processing_time_ms,
            "model": self.model,
            "error": self.error,
        }


# ── Mock infrastructure (testing / demo without API key) ─────────────────────

_DEFAULT_MOCK_RESPONSES: dict[str, dict] = {
    "extract_claim_fields": {
        "policyholder_name": "Anna Müller",
        "policy_number": "POL-2024-88432",
        "incident_date": "2024-06-10",
        "incident_type": "burst pipe / water damage",
        "damage_description": (
            "A pipe burst in the bathroom, flooding the hallway and living room. "
            "Parquet flooring and drywall affected."
        ),
        "claimed_amount_eur": 6800.0,
        "incident_location": "Schillerstraße 14, 80336 Munich",
        "third_parties_involved": False,
    },
    "classify_claim": {
        "peril_category": "water_damage",
        "severity": "medium",
        "auto_processable": False,
        "flags": [],
    },
    "assess_completeness": {
        "missing_fields": ["repair_estimate"],
        "required_documents": ["repair_estimate", "damage_photos", "plumber_report"],
        "completeness_score": 0.72,
        "information_sufficient_for_triage": True,
    },
    "generate_triage_decision": {
        "decision": "manual_review",
        "rationale": (
            "Medium-severity water damage with sufficient initial information for triage. "
            "Requires a certified repair estimate before settlement can be authorised."
        ),
        "priority": "standard",
        "estimated_processing_days": 7,
        "next_action": (
            "Request repair estimate and damage photos from policyholder; "
            "assign to water damage specialist team."
        ),
    },
}


class _ToolUseBlock:
    """Minimal mock of an Anthropic ToolUseBlock."""
    type = "tool_use"

    def __init__(self, name: str, input_data: dict):
        self.name = name
        self.input = input_data


class _MockMessage:
    """Minimal mock of an Anthropic Message with a single ToolUseBlock."""
    stop_reason = "tool_use"
    model = "mock"

    def __init__(self, name: str, input_data: dict):
        self.content = [_ToolUseBlock(name, input_data)]


class _MockMessages:
    """Mock messages.create that returns pre-defined tool inputs."""

    def __init__(self, responses: dict[str, dict]):
        self._responses = responses

    def create(
        self,
        *,
        tools: list,
        tool_choice: dict,
        messages: list,
        model: str,
        max_tokens: int = 1024,
        **kwargs,
    ) -> _MockMessage:
        tool_name = tool_choice["name"]
        response_input = self._responses.get(tool_name, {})
        return _MockMessage(tool_name, response_input)


class _MockClient:
    """Minimal mock Anthropic client with a .messages.create interface."""

    def __init__(self, responses: dict[str, dict] | None = None):
        self.messages = _MockMessages(responses or _DEFAULT_MOCK_RESPONSES)


# ── Agent ─────────────────────────────────────────────────────────────────────

class ClaimsTriageAgent:
    """
    Agentic pipeline that triages insurance claims through four Claude-powered stages.

    Parameters
    ----------
    api_key : str, optional
        Anthropic API key. Falls back to ANTHROPIC_API_KEY environment variable.
        Pass ``mock=True`` to skip the API entirely (for testing).
    model : str, optional
        Claude model to use. Defaults to ``claude-sonnet-4-6``.
    mock : bool
        If True, uses a mock client that returns pre-defined responses without
        calling the Anthropic API. Useful for CI, testing, and demos.

    Examples
    --------
    >>> agent = ClaimsTriageAgent(mock=True)
    >>> result = agent.process_claim("My roof was damaged in a hailstorm.", "CLM-001")
    >>> result.triage_decision
    'manual_review'
    """

    DEFAULT_MODEL = "claude-sonnet-4-6"

    def __init__(
        self,
        api_key: str | None = None,
        model: str | None = None,
        mock: bool = False,
    ):
        self.model = model or self.DEFAULT_MODEL
        self._mock = mock or os.environ.get("ANTHROPIC_API_KEY") == "mock"

        if self._mock:
            self._client = _MockClient()
        else:
            try:
                import anthropic  # type: ignore[import]
            except ImportError:
                raise ImportError(
                    "Anthropic SDK not installed. Run: pip install anthropic\n"
                    "Or use ClaimsTriageAgent(mock=True) for offline testing."
                )
            key = api_key or os.environ.get("ANTHROPIC_API_KEY")
            if not key:
                raise ValueError(
                    "No API key found. Set ANTHROPIC_API_KEY environment variable, "
                    "pass api_key=, or use mock=True."
                )
            self._client = anthropic.Anthropic(api_key=key)

    # ── Internal helpers ──────────────────────────────────────────────────────

    def _call_tool(self, tool: dict, prompt: str, max_tokens: int = 1024) -> dict:
        """
        Call Claude with a forced tool_choice for one stage.

        Forces Claude to use the specified tool, guaranteeing structured JSON
        output. This is the core mechanism enabling deterministic batch processing.
        """
        response = self._client.messages.create(
            model=self.model,
            max_tokens=max_tokens,
            tools=[tool],
            tool_choice={"type": "tool", "name": tool["name"]},
            messages=[{"role": "user", "content": prompt}],
        )
        block = response.content[0]
        if hasattr(block, "input"):
            return block.input  # type: ignore[return-value]
        raise RuntimeError(
            f"Unexpected Claude response — expected ToolUseBlock, got: {type(block)}"
        )

    # ── Pipeline stages ───────────────────────────────────────────────────────

    def _stage_extract(self, claim_text: str) -> dict:
        prompt = (
            "Extract all available structured information from the following "
            "insurance claim submission. Use null for any field not mentioned.\n\n"
            f"CLAIM SUBMISSION:\n{claim_text}"
        )
        return self._call_tool(EXTRACT_TOOL, prompt)

    def _stage_classify(self, claim_text: str, extracted: dict) -> dict:
        prompt = (
            "Classify this insurance claim by peril category and severity.\n\n"
            f"ORIGINAL SUBMISSION:\n{claim_text}\n\n"
            f"EXTRACTED FIELDS:\n{json.dumps(extracted, indent=2, ensure_ascii=False)}"
        )
        return self._call_tool(CLASSIFY_TOOL, prompt)

    def _stage_assess(
        self, claim_text: str, extracted: dict, classification: dict
    ) -> dict:
        prompt = (
            "Assess the completeness of this insurance claim and list missing information.\n\n"
            f"ORIGINAL SUBMISSION:\n{claim_text}\n\n"
            f"EXTRACTED FIELDS:\n{json.dumps(extracted, indent=2, ensure_ascii=False)}\n\n"
            f"CLASSIFICATION:\n{json.dumps(classification, indent=2, ensure_ascii=False)}"
        )
        return self._call_tool(ASSESS_TOOL, prompt, max_tokens=512)

    def _stage_decide(
        self, extracted: dict, classification: dict, completeness: dict
    ) -> dict:
        prompt = (
            "Generate a triage decision for this insurance claim.\n\n"
            f"EXTRACTED:\n{json.dumps(extracted, indent=2, ensure_ascii=False)}\n\n"
            f"CLASSIFICATION:\n{json.dumps(classification, indent=2, ensure_ascii=False)}\n\n"
            f"COMPLETENESS:\n{json.dumps(completeness, indent=2, ensure_ascii=False)}"
        )
        return self._call_tool(DECIDE_TOOL, prompt, max_tokens=512)

    # ── Public API ────────────────────────────────────────────────────────────

    def process_claim(
        self, claim_text: str, claim_id: str | None = None
    ) -> TriageResult:
        """
        Process a single insurance claim through all four pipeline stages.

        Parameters
        ----------
        claim_text : str
            Raw claim submission text (unstructured).
        claim_id : str, optional
            Unique identifier. Auto-generated from claim text hash if not provided.

        Returns
        -------
        TriageResult
            Fully populated result object. On error, ``result.error`` is set and
            partial stage outputs are preserved for debugging.
        """
        if not claim_id:
            import hashlib
            claim_id = "CLM-" + hashlib.md5(claim_text.encode()).hexdigest()[:8].upper()

        result = TriageResult(claim_id=claim_id, raw_text=claim_text, model=self.model)
        t0 = time.time()

        try:
            result.extracted = self._stage_extract(claim_text)
            result.classification = self._stage_classify(
                claim_text, result.extracted
            )
            result.completeness = self._stage_assess(
                claim_text, result.extracted, result.classification
            )
            result.decision = self._stage_decide(
                result.extracted, result.classification, result.completeness
            )
        except Exception as exc:  # noqa: BLE001
            result.error = f"{type(exc).__name__}: {exc}"

        result.processing_time_ms = int((time.time() - t0) * 1000)
        return result

    def process_batch(
        self, claims: list[tuple[str, str]]
    ) -> list[TriageResult]:
        """
        Process a list of claims sequentially.

        Parameters
        ----------
        claims : list of (claim_id, claim_text) tuples

        Returns
        -------
        list[TriageResult]
        """
        return [self.process_claim(text, cid) for cid, text in claims]
