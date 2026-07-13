"""
Demo: process 5 sample German insurance claims through the triage pipeline.

Usage
-----
    # Real API (set ANTHROPIC_API_KEY first)
    python demo/run_demo.py

    # Mock mode — no API key needed
    python demo/run_demo.py --mock

Output files written to demo/output/:
    triage_results.json
    triage_results.csv
    triage_report.html
"""
from __future__ import annotations

import argparse
import os
import sys
import time
from pathlib import Path

# Allow running from repo root or from demo/ directory
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from claims_triage import ClaimsTriageAgent
from claims_triage.reporter import to_json, to_csv, to_html
from demo.sample_claims import SAMPLE_CLAIMS


BANNER = """
╔══════════════════════════════════════════════════════════════╗
║         claude-claims-triage  ·  Demo Pipeline              ║
║         github.com/Sarosh008/claude-claims-triage            ║
╚══════════════════════════════════════════════════════════════╝
"""

SEVERITY_ICON = {
    "low": "🟢", "medium": "🟡", "high": "🔴", "extreme": "🚨"
}
DECISION_ICON = {
    "auto_approve": "✅", "manual_review": "👁",
    "request_information": "📋", "reject": "❌"
}


def main():
    parser = argparse.ArgumentParser(description="Run the claims triage demo")
    parser.add_argument(
        "--mock", action="store_true",
        help="Use mock responses (no Anthropic API key required)"
    )
    parser.add_argument(
        "--model", default=None,
        help="Claude model to use (default: claude-sonnet-4-6)"
    )
    args = parser.parse_args()

    print(BANNER)

    # ── Initialise agent ──────────────────────────────────────────────────────
    use_mock = args.mock or os.environ.get("ANTHROPIC_API_KEY") == "mock"
    if use_mock:
        print("  Mode : MOCK (pre-defined responses, no API calls)")
    else:
        print(f"  Mode : LIVE — model: {args.model or ClaimsTriageAgent.DEFAULT_MODEL}")
    print(f"  Claims: {len(SAMPLE_CLAIMS)}\n")

    agent = ClaimsTriageAgent(model=args.model, mock=use_mock)

    # ── Process each claim ────────────────────────────────────────────────────
    results = []
    total_start = time.time()

    for claim_id, claim_text, _ in SAMPLE_CLAIMS:
        print(f"  Processing {claim_id} ...", end="", flush=True)
        result = agent.process_claim(claim_text.strip(), claim_id=claim_id)
        results.append(result)

        if result.error:
            print(f"  ERROR: {result.error}")
        else:
            sev_icon = SEVERITY_ICON.get(result.severity, "❓")
            dec_icon = DECISION_ICON.get(result.triage_decision, "❓")
            print(
                f"  {sev_icon} {result.severity.upper():8s} "
                f"| {dec_icon} {result.triage_decision.replace('_',' '):22s}"
                f"| {result.completeness_score:.0%} complete "
                f"| {result.processing_time_ms}ms"
            )

    total_ms = int((time.time() - total_start) * 1000)

    # ── Summary ───────────────────────────────────────────────────────────────
    print(f"\n  ─────────────────────────────────────")
    print(f"  {len(results)} claims processed in {total_ms}ms")
    decisions = [r.triage_decision for r in results]
    for dec in ["auto_approve", "manual_review", "request_information", "reject"]:
        n = decisions.count(dec)
        if n:
            icon = DECISION_ICON[dec]
            print(f"  {icon}  {n}× {dec.replace('_',' ')}")

    # ── Write output files ────────────────────────────────────────────────────
    out_dir = Path(__file__).parent / "output"
    out_dir.mkdir(exist_ok=True)

    json_path = out_dir / "triage_results.json"
    csv_path  = out_dir / "triage_results.csv"
    html_path = out_dir / "triage_report.html"

    json_path.write_text(to_json(results), encoding="utf-8")
    csv_path.write_text(to_csv(results), encoding="utf-8")
    html_path.write_text(to_html(results), encoding="utf-8")

    print(f"\n  Output written to {out_dir}/")
    print(f"    📄 {json_path.name}")
    print(f"    📊 {csv_path.name}")
    print(f"    🌐 {html_path.name}  ← open in browser for full dashboard")


if __name__ == "__main__":
    main()
