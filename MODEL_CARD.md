# Model Card — claude-claims-triage

**Version:** 0.1.0  
**Date:** July 2026  
**Author:** Syed Sarosh Sulaiman  
**Model used:** Anthropic Claude (default: `claude-sonnet-4-6`)

---

## Purpose

`claude-claims-triage` is a four-stage agentic pipeline that triages insurance claim submissions using the Anthropic Claude API. It processes unstructured natural-language claim text and outputs structured JSON with an extraction, classification, completeness assessment, and routing decision.

**Intended users:** Claims operations teams, AI/ML engineers evaluating LLM-based automation for insurance intake workflows.

**Out of scope:** Final settlement decisions, fraud detection (only a flag, not a determination), legal advice, medical claims.

---

## Pipeline stages and Claude's role

| Stage | Tool | Claude's task | Output |
|---|---|---|---|
| 1 — Extract | `extract_claim_fields` | Read unstructured text; identify named entities, dates, amounts | Structured dict of claim fields |
| 2 — Classify | `classify_claim` | Infer peril category and severity from damage description | `peril_category`, `severity`, `flags` |
| 3 — Assess | `assess_completeness` | Identify what documentation is missing given peril type | `missing_fields`, `required_documents`, `completeness_score` |
| 4 — Decide | `generate_triage_decision` | Synthesise all prior outputs into a routing decision | `decision`, `rationale`, `priority`, `ETA` |

Each stage uses `tool_choice` to force Claude to return schema-valid JSON — ensuring deterministic, parseable output on every call.

---

## Peril categories

| Category | Example incidents |
|---|---|
| `water_damage` | Burst pipe, flood ingress, appliance leak |
| `fire` | Kitchen fire, electrical fire, arson |
| `theft_burglary` | Forced entry, opportunistic theft, robbery |
| `natural_hazard` | Storm, hail, flood, earthquake |
| `liability` | Third-party bodily injury or property damage |
| `vehicle` | Collision, hail damage, theft of vehicle |
| `glass` | Windscreen, window breakage |
| `other` | Perils not fitting the above categories |

---

## Decision logic

Claude is not given explicit decision rules; it reasons from the extracted information. The prompt for Stage 4 provides the decision schema and definitions (documented in `tools.py`). Observed behaviour in mock mode:

| Typical situation | Expected decision |
|---|---|
| Low severity, complete info, standard peril | `auto_approve` |
| Medium/high severity, complete info | `manual_review` |
| Missing required fields | `request_information` |
| Policy exclusion keyword detected | `reject` |

**Note:** In real deployments, Stage 4 prompts should be augmented with carrier-specific policy rules and exclusion language to ensure correct rejection decisions.

---

## Limitations

**Language and format:** The pipeline is optimised for English and German claim text. Performance on other languages has not been evaluated.

**Mock mode vs. live mode:** The demo runs in mock mode with static pre-defined responses. Live mode responses vary by Claude model version, prompt context, and claim complexity. Stage outputs in live mode will differ across runs for ambiguous claims.

**Severity calibration:** Claude infers severity from the damage description, not from actuarial loss curves. For production use, severity should be validated against historical claim amounts for the carrier's specific portfolio.

**Fraud detection:** The `flags` field may surface a `possible_fraud` indicator, but this pipeline is not a fraud detection system. Flagged claims require human investigation.

**Completeness scoring:** The `completeness_score` is Claude's estimate, not a rule-based checklist. It may vary across models and should be validated against carrier-specific intake requirements.

**Token limits:** Very long claim submissions (>3,000 words) may require chunking before Stage 1. The pipeline does not currently handle chunking.

---

## Prompt engineering notes

Each stage prompt includes:
1. **Role framing** — what the stage is responsible for (extraction, classification, etc.)
2. **Input context** — the raw claim text and outputs from prior stages
3. **Instruction** — what to do with the information
4. **Null handling** — Stage 1 is instructed to return `null` rather than invent missing values

No few-shot examples are currently included. Adding 2–3 examples per stage (especially for ambiguous perils and severity calibration) is expected to improve accuracy on edge cases.

---

## Evaluation

No systematic evaluation dataset exists for v0.1.0. Manual review of the five demo claims (covering water damage, burglary, hail/vehicle, fire, and windstorm) confirmed:
- Correct peril classification in all five cases (live mode)
- Appropriate severity inference given damage descriptions
- Accurate identification of missing documents by peril type
- Coherent routing decisions with relevant rationale

**Recommended before production deployment:**
- Evaluate on ≥200 labelled historical claims per peril category
- Measure extraction accuracy for key fields (dates, amounts, policy numbers)
- A/B test routing decisions against adjuster outcomes
- Benchmark against carrier's existing triage rules

---

## Ethical considerations

- **Human oversight:** All `manual_review` decisions are explicitly routed to human adjusters. The pipeline does not replace human judgment for complex or high-severity claims.
- **Transparency:** The `rationale` field provides an auditable, client-readable explanation for every routing decision.
- **Bias:** Claude's severity and classification judgments may reflect biases present in its training data. Peril classifications should be audited across demographic and geographic subgroups before deployment.
- **Data privacy:** Claim text contains personal data (names, addresses, policy numbers). In production, PII should be redacted or pseudonymised before sending to the Claude API, in line with the carrier's data processing agreements.

---

## References

- Anthropic Claude documentation: https://docs.anthropic.com
- Anthropic tool use guide: https://docs.anthropic.com/en/docs/build-with-claude/tool-use
- Swiss Re sigma reports (for peril weight calibration context): https://www.swissre.com/sigma
- GDV (German Insurance Association) claims statistics: https://www.gdv.de

---

*This model card follows the format established by Mitchell et al. (2019), "Model Cards for Model Reporting."*
