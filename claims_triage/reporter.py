"""
Output reporters for TriageResult lists.

    to_json(results)  → JSON string
    to_csv(results)   → CSV string
    to_html(results)  → self-contained HTML report
"""
from __future__ import annotations

import csv
import io
import json

_SEVERITY_COLOURS = {
    "low":     "#4CAF50",
    "medium":  "#FF9800",
    "high":    "#F44336",
    "extreme": "#880E4F",
}

_DECISION_COLOURS = {
    "auto_approve":        "#4CAF50",
    "manual_review":       "#FF9800",
    "request_information": "#2196F3",
    "reject":              "#D32F2F",
}


def to_json(results) -> str:
    """Return JSON array of all triage results."""
    return json.dumps([r.to_dict() for r in results], indent=2, ensure_ascii=False)


def to_csv(results) -> str:
    """Return flat CSV with one row per claim."""
    buf = io.StringIO()
    w = csv.writer(buf)
    w.writerow([
        "claim_id", "policyholder", "incident_type",
        "peril_category", "severity", "auto_processable",
        "completeness_score", "decision", "priority",
        "estimated_processing_days", "claimed_amount_eur",
        "flags", "missing_fields", "processing_time_ms", "error",
    ])
    for r in results:
        w.writerow([
            r.claim_id,
            r.extracted.get("policyholder_name", ""),
            r.extracted.get("incident_type", ""),
            r.classification.get("peril_category", ""),
            r.classification.get("severity", ""),
            r.classification.get("auto_processable", ""),
            r.completeness.get("completeness_score", ""),
            r.decision.get("decision", ""),
            r.decision.get("priority", ""),
            r.decision.get("estimated_processing_days", ""),
            r.extracted.get("claimed_amount_eur", ""),
            "|".join(r.classification.get("flags", [])),
            "|".join(r.completeness.get("missing_fields", [])),
            r.processing_time_ms,
            r.error or "",
        ])
    return buf.getvalue()


def to_html(results) -> str:
    """Return a self-contained HTML dashboard for all triage results."""
    rows = _build_table_rows(results)
    stats = _compute_stats(results)
    model_label = results[0].model if results else "—"

    return f"""<!DOCTYPE html>
<html lang="en">
<head>
<meta charset="UTF-8">
<meta name="viewport" content="width=device-width, initial-scale=1">
<title>Claims Triage Report — claude-claims-triage</title>
<style>
  *, *::before, *::after {{ box-sizing: border-box; margin: 0; padding: 0; }}
  body   {{ font-family: Arial, Helvetica, sans-serif; background: #f4f4f4;
             color: #1a1a1a; padding: 2rem; }}
  header {{ margin-bottom: 1.5rem; }}
  header h1 {{ font-size: 1.5rem; font-weight: 700; color: #1a1a1a; }}
  header p  {{ font-size: 0.85rem; color: #666; margin-top: 0.25rem; }}
  .accent {{ color: #D97757; }}

  /* Stat cards */
  .stats  {{ display: flex; gap: 1rem; flex-wrap: wrap; margin-bottom: 1.5rem; }}
  .stat   {{ background: #fff; border: 1px solid #ddd; border-radius: 6px;
             padding: 0.75rem 1.25rem; min-width: 130px; }}
  .stat .val {{ font-size: 1.7rem; font-weight: 700; color: #D97757; }}
  .stat .lbl {{ font-size: 0.75rem; color: #888; margin-top: 0.15rem; }}

  /* Table */
  .table-wrap {{ overflow-x: auto; background: #fff; border-radius: 6px;
                 border: 1px solid #ddd; }}
  table  {{ width: 100%; border-collapse: collapse; font-size: 0.82rem; }}
  th     {{ background: #1a1a1a; color: #fff; padding: 0.55rem 0.75rem;
             text-align: left; white-space: nowrap; }}
  td     {{ padding: 0.5rem 0.75rem; border-bottom: 1px solid #eee;
             vertical-align: top; }}
  tr:last-child td {{ border-bottom: none; }}
  tr:hover td  {{ background: #fafafa; }}

  .badge {{ display: inline-block; border-radius: 3px; padding: 0.1rem 0.4rem;
             font-size: 0.75rem; font-weight: 600; color: #fff; }}

  .meta  {{ font-size: 0.75rem; color: #888; }}
  footer {{ margin-top: 1.5rem; font-size: 0.75rem; color: #aaa; }}
</style>
</head>
<body>
<header>
  <h1>Claims Triage Report <span class="accent">·</span> claude-claims-triage</h1>
  <p>Powered by <strong>Anthropic Claude API</strong> ({model_label}) ·
     github.com/Sarosh008/claude-claims-triage</p>
</header>

<div class="stats">
  <div class="stat">
    <div class="val">{stats["total"]}</div>
    <div class="lbl">Claims processed</div>
  </div>
  <div class="stat">
    <div class="val" style="color:#4CAF50">{stats["auto_approve"]}</div>
    <div class="lbl">Auto-approved</div>
  </div>
  <div class="stat">
    <div class="val" style="color:#FF9800">{stats["manual_review"]}</div>
    <div class="lbl">Manual review</div>
  </div>
  <div class="stat">
    <div class="val" style="color:#2196F3">{stats["request_info"]}</div>
    <div class="lbl">Info requested</div>
  </div>
  <div class="stat">
    <div class="val" style="color:#D32F2F">{stats["rejected"]}</div>
    <div class="lbl">Rejected</div>
  </div>
  <div class="stat">
    <div class="val">{stats["avg_completeness"]:.0%}</div>
    <div class="lbl">Avg completeness</div>
  </div>
</div>

<div class="table-wrap">
<table>
<thead>
<tr>
  <th>Claim ID</th>
  <th>Policyholder</th>
  <th>Incident</th>
  <th>Peril</th>
  <th>Severity</th>
  <th>Decision</th>
  <th>Priority</th>
  <th>ETA</th>
  <th>Completeness</th>
  <th>Rationale</th>
  <th>Flags / Missing</th>
</tr>
</thead>
<tbody>
{rows}
</tbody>
</table>
</div>

<footer>
  Generated by claude-claims-triage v0.1.0 ·
  Total claims: {stats["total"]} ·
  Model: {model_label}
</footer>
</body>
</html>"""


# ── Helpers ───────────────────────────────────────────────────────────────────

def _badge(label: str, colour: str) -> str:
    return f'<span class="badge" style="background:{colour}">{label.replace("_"," ").upper()}</span>'


def _build_table_rows(results) -> str:
    rows = []
    for r in results:
        sev = r.classification.get("severity", "—")
        dec = r.decision.get("decision", "—")
        sev_c = _SEVERITY_COLOURS.get(sev, "#9E9E9E")
        dec_c = _DECISION_COLOURS.get(dec, "#9E9E9E")

        flags   = r.classification.get("flags", [])
        missing = r.completeness.get("missing_fields", [])
        flag_str = (", ".join(flags) if flags else "—")
        miss_str = (", ".join(missing) if missing else "—")

        score = r.completeness.get("completeness_score", 0)
        score_pct = f"{float(score):.0%}"

        eta = r.decision.get("estimated_processing_days", "—")
        eta_str = f"{eta}d" if eta != "—" else "—"

        rows.append(f"""<tr>
  <td><strong>{r.claim_id}</strong></td>
  <td>{r.extracted.get("policyholder_name", "—")}</td>
  <td>{r.extracted.get("incident_type", "—")}</td>
  <td>{r.classification.get("peril_category","—").replace("_"," ")}</td>
  <td>{_badge(sev, sev_c)}</td>
  <td>{_badge(dec, dec_c)}</td>
  <td>{r.decision.get("priority","—")}</td>
  <td>{eta_str}</td>
  <td>{score_pct}</td>
  <td style="max-width:260px">{r.decision.get("rationale","—")}</td>
  <td class="meta">⚑ {flag_str}<br>📋 {miss_str}</td>
</tr>""")
    return "\n".join(rows)


def _compute_stats(results) -> dict:
    decisions = [r.decision.get("decision", "") for r in results]
    scores = [
        float(r.completeness.get("completeness_score", 0))
        for r in results
        if r.completeness.get("completeness_score") is not None
    ]
    return {
        "total":            len(results),
        "auto_approve":     decisions.count("auto_approve"),
        "manual_review":    decisions.count("manual_review"),
        "request_info":     decisions.count("request_information"),
        "rejected":         decisions.count("reject"),
        "avg_completeness": (sum(scores) / len(scores)) if scores else 0.0,
    }
