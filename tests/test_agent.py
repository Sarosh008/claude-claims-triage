"""Tests for ClaimsTriageAgent (claims_triage/agent.py).

All tests use mock=True — no Anthropic API key required.
"""
import pytest
from claims_triage.agent import (
    ClaimsTriageAgent, TriageResult, _MockClient, _DEFAULT_MOCK_RESPONSES
)


# ── Initialisation ────────────────────────────────────────────────────────────

class TestAgentInit:
    def test_mock_mode_no_key_needed(self):
        """Should not raise even without ANTHROPIC_API_KEY."""
        agent = ClaimsTriageAgent(mock=True)
        assert agent._mock is True

    def test_missing_key_raises(self, monkeypatch):
        """Real mode without API key should raise ValueError."""
        monkeypatch.delenv("ANTHROPIC_API_KEY", raising=False)
        with pytest.raises((ValueError, ImportError)):
            ClaimsTriageAgent(mock=False)

    def test_default_model(self):
        agent = ClaimsTriageAgent(mock=True)
        assert agent.model == ClaimsTriageAgent.DEFAULT_MODEL

    def test_custom_model(self):
        agent = ClaimsTriageAgent(mock=True, model="claude-haiku-4-5-20251001")
        assert agent.model == "claude-haiku-4-5-20251001"


# ── process_claim ─────────────────────────────────────────────────────────────

class TestProcessClaim:
    def test_returns_triage_result(self, mock_agent, water_claim):
        claim_id, text = water_claim
        result = mock_agent.process_claim(text, claim_id=claim_id)
        assert isinstance(result, TriageResult)

    def test_claim_id_preserved(self, mock_agent, water_claim):
        claim_id, text = water_claim
        result = mock_agent.process_claim(text, claim_id=claim_id)
        assert result.claim_id == claim_id

    def test_raw_text_preserved(self, mock_agent, water_claim):
        claim_id, text = water_claim
        result = mock_agent.process_claim(text, claim_id=claim_id)
        assert result.raw_text == text

    def test_auto_claim_id_generated(self, mock_agent):
        result = mock_agent.process_claim("Some claim text")
        assert result.claim_id.startswith("CLM-")
        assert len(result.claim_id) == 12  # "CLM-" + 8 hex chars

    def test_no_error_on_valid_claim(self, mock_result):
        assert mock_result.error is None

    def test_processing_time_recorded(self, mock_result):
        assert mock_result.processing_time_ms >= 0

    def test_model_recorded(self, mock_result):
        assert mock_result.model == ClaimsTriageAgent.DEFAULT_MODEL

    def test_extracted_populated(self, mock_result):
        assert isinstance(mock_result.extracted, dict)
        assert len(mock_result.extracted) > 0

    def test_classification_populated(self, mock_result):
        assert isinstance(mock_result.classification, dict)
        assert "peril_category" in mock_result.classification

    def test_completeness_populated(self, mock_result):
        assert isinstance(mock_result.completeness, dict)
        assert "completeness_score" in mock_result.completeness

    def test_decision_populated(self, mock_result):
        assert isinstance(mock_result.decision, dict)
        assert "decision" in mock_result.decision

    def test_decision_is_valid_enum(self, mock_result):
        valid = {"auto_approve", "manual_review", "request_information", "reject"}
        assert mock_result.triage_decision in valid

    def test_severity_is_valid_enum(self, mock_result):
        valid = {"low", "medium", "high", "extreme"}
        assert mock_result.severity in valid

    def test_completeness_score_in_range(self, mock_result):
        assert 0.0 <= mock_result.completeness_score <= 1.0


# ── process_batch ─────────────────────────────────────────────────────────────

class TestProcessBatch:
    def test_returns_list(self, mock_agent, water_claim, burglary_claim):
        claims = [water_claim, burglary_claim]
        results = mock_agent.process_batch(claims)
        assert isinstance(results, list)
        assert len(results) == 2

    def test_all_results_are_triage_results(self, mock_agent, water_claim, burglary_claim):
        results = mock_agent.process_batch([water_claim, burglary_claim])
        assert all(isinstance(r, TriageResult) for r in results)

    def test_claim_ids_preserved(self, mock_agent, water_claim, burglary_claim):
        results = mock_agent.process_batch([water_claim, burglary_claim])
        assert results[0].claim_id == water_claim[0]
        assert results[1].claim_id == burglary_claim[0]


# ── TriageResult convenience properties ───────────────────────────────────────

class TestTriageResultProperties:
    def test_to_dict_keys(self, mock_result):
        d = mock_result.to_dict()
        required_keys = {
            "claim_id", "raw_text", "extracted", "classification",
            "completeness", "decision", "processing_time_ms", "model", "error"
        }
        assert required_keys.issubset(d.keys())

    def test_to_dict_claim_id_matches(self, mock_result):
        assert mock_result.to_dict()["claim_id"] == mock_result.claim_id

    def test_peril_property(self, mock_result):
        assert mock_result.peril == mock_result.classification.get("peril_category")

    def test_unknown_severity_returns_unknown(self):
        r = TriageResult(claim_id="X", raw_text="x")
        assert r.severity == "unknown"

    def test_unknown_decision_returns_unknown(self):
        r = TriageResult(claim_id="X", raw_text="x")
        assert r.triage_decision == "unknown"
