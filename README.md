# claude-claims-triage

**Agentic insurance claims triage pipeline built on the Anthropic Claude API.**

Processes unstructured claim submissions through a four-stage Claude-powered pipeline — extracting fields, classifying perils, assessing completeness, and routing each claim to the correct handling workflow. Outputs structured JSON, CSV, and an interactive HTML dashboard.

---

## Why This Exists

Insurance carriers receive thousands of unstructured claims every day. Traditional rule-based triage systems require extensive engineering to cover every peril type and submission format. This project demonstrates how Claude's tool-use API enables a **generalist agentic pipeline** that:

- Reads any free-text claim submission
- Extracts structured fields (policyholder, dates, amounts, locations)
- Classifies peril and severity
- Identifies missing documentation before human review
- Routes to the optimal workflow without hard-coded rules

The pipeline mirrors production architectures at AI-first insurers: Claude provides judgment and language understanding; tool schemas ensure the output is always structured and machine-readable.

---

## Architecture

```
┌─────────────────────────────────────────────────────────────┐
│              ClaimsTriageAgent.process_claim()               │
│                                                             │
│  raw claim text                                             │
│       │                                                     │
│       ▼                                                     │
│  ┌─────────────┐   forced tool_choice → structured JSON     │
│  │  Stage 1    │   extract_claim_fields                     │
│  │  EXTRACT    │   policyholder, dates, amounts, location   │
│  └──────┬──────┘                                            │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────┐                                            │
│  │  Stage 2    │   classify_claim                           │
│  │  CLASSIFY   │   peril_category, severity, flags          │
│  └──────┬──────┘                                            │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────┐                                            │
│  │  Stage 3    │   assess_completeness                      │
│  │  ASSESS     │   missing_fields, required_documents       │
│  └──────┬──────┘                                            │
│         │                                                   │
│         ▼                                                   │
│  ┌─────────────┐                                            │
│  │  Stage 4    │   generate_triage_decision                 │
│  │  DECIDE     │   decision, rationale, priority, ETA       │
│  └──────┬──────┘                                            │
│         │                                                   │
│         ▼                                                   │
│    TriageResult  →  JSON / CSV / HTML                       │
└─────────────────────────────────────────────────────────────┘
```

**Why forced `tool_choice`?**
Each stage calls Claude with `tool_choice={"type": "tool", "name": "..."}`, forcing structured JSON output on every call. This eliminates output parsing code entirely and makes the pipeline deterministic, testable, and safe for batch processing at scale.

---

## Triage decisions

| Decision | Meaning |
|---|---|
| `auto_approve` | Meets all criteria for straight-through processing — no human review needed |
| `manual_review` | Sufficient info but requires human judgment (high severity, edge case, fraud flag) |
| `request_information` | Missing critical fields — system requests docs before triage can proceed |
| `reject` | Policy exclusion or fraud indicator |

---

## Quickstart

### Real API

```bash
pip install anthropic
export ANTHROPIC_API_KEY=sk-ant-...
python demo/run_demo.py
```

### Mock mode (no API key required)

```bash
python demo/run_demo.py --mock
```

Output written to `demo/output/`:
- `triage_results.json` — full structured output per claim
- `triage_results.csv` — flat table, ready for Excel / BI tools
- `triage_report.html` — interactive dashboard, open in browser

### Python API

```python
from claims_triage import ClaimsTriageAgent

agent = ClaimsTriageAgent()  # set ANTHROPIC_API_KEY in env
# or: agent = ClaimsTriageAgent(mock=True)

result = agent.process_claim(
    """
    Policyholder: Maria Schmidt. Policy: HHV-2024-001.
    On 10 June my apartment flooded after a pipe burst in the bathroom.
    Parquet flooring destroyed (~18 m²), drywall soaked. Repair estimate pending.
    """,
    claim_id="CLM-2024-001"
)

print(result.triage_decision)   # "manual_review"
print(result.severity)          # "medium"
print(result.completeness_score)  # 0.72
print(result.decision["rationale"])
```

Batch processing:

```python
claims = [
    ("CLM-001", "Pipe burst, water damage, Munich..."),
    ("CLM-002", "Burglary, balcony door forced, Berlin..."),
    ("CLM-003", "Hail damage, car, Stuttgart..."),
]
results = agent.process_batch(claims)
```

---

## Output format

Each `TriageResult` contains:

```json
{
  "claim_id": "CLM-2024-MUC-001",
  "extracted": {
    "policyholder_name": "Anna Müller",
    "incident_type": "burst pipe / water damage",
    "claimed_amount_eur": 6800.0,
    "incident_location": "Schillerstraße 14, 80336 Munich",
    "third_parties_involved": false
  },
  "classification": {
    "peril_category": "water_damage",
    "severity": "medium",
    "auto_processable": false,
    "flags": []
  },
  "completeness": {
    "missing_fields": ["repair_estimate"],
    "required_documents": ["repair_estimate", "damage_photos", "plumber_report"],
    "completeness_score": 0.72
  },
  "decision": {
    "decision": "manual_review",
    "rationale": "Medium-severity water damage — sufficient for initial triage but repair estimate required before settlement.",
    "priority": "standard",
    "estimated_processing_days": 7,
    "next_action": "Request repair estimate and damage photos; assign to water damage specialist."
  },
  "processing_time_ms": 1340,
  "model": "claude-sonnet-4-6"
}
```

---

## Sample claims (demo)

Five realistic German insurance claim scenarios:

| ID | Peril | Scenario |
|---|---|---|
| CLM-2024-MUC-001 | Water damage | Burst pipe, Munich apartment, €6,800 |
| CLM-2024-BER-002 | Theft/burglary | Balcony door forced, Berlin, €10,600 |
| CLM-2024-STU-003 | Vehicle / hail | VW Golf hail damage, Stuttgart |
| CLM-2024-HAM-004 | Fire | Kitchen fire, structural concern, Hamburg |
| CLM-2024-FFM-005 | Natural hazard | Storm roof damage + shed, Frankfurt |

---

## Running tests

```bash
pip install pytest
pytest tests/ -v
```

Tests use mock mode — no API key required. Tests verify:
- All four tool schemas (structure, required fields, enum values)
- `process_claim` and `process_batch` (results, IDs, properties)
- `TriageResult` properties and `to_dict()`
- JSON, CSV, and HTML reporters

---

## Tech stack

| Component | Technology |
|---|---|
| LLM provider | Anthropic Claude API (`claude-sonnet-4-6`) |
| SDK | `anthropic` Python SDK |
| Agentic pattern | Forced `tool_choice` per stage (structured extraction) |
| Output | JSON / CSV / HTML (stdlib only) |
| Testing | pytest, mock client (no API key needed) |

---

## Relation to production AI operations

This project was built to demonstrate the core technical capabilities required in AI operations roles at insurance carriers:

- **Claude API proficiency** — `tool_use`, `tool_choice`, context management, multi-stage agentic workflows
- **Prompt engineering** — stage-specific prompts designed to elicit accurate extraction, classification, and routing decisions
- **Agentic pipeline design** — composing LLM calls into deterministic, auditable workflows
- **Insurance domain understanding** — peril categories, triage decisions, and document requirements grounded in standard claims handling practice

See [MODEL_CARD.md](MODEL_CARD.md) for methodology, limitations, and evaluation notes.

---

**Author:** Syed Sarosh Sulaiman · [github.com/Sarosh008](https://github.com/Sarosh008)  
**Portfolio:** [portfolio-sulaiman-06-2026-v2.vercel.app](https://portfolio-sulaiman-06-2026-v2.vercel.app)
