"""
claude-claims-triage
====================
Agentic insurance claims triage pipeline built on the Anthropic Claude API.

Usage:
    from claims_triage import ClaimsTriageAgent
    agent = ClaimsTriageAgent()                # real API (needs ANTHROPIC_API_KEY)
    agent = ClaimsTriageAgent(mock=True)       # mock mode (no key required)
    result = agent.process_claim("My pipe burst...", claim_id="CLM-001")
"""
from .agent import ClaimsTriageAgent, TriageResult

__all__ = ["ClaimsTriageAgent", "TriageResult"]
__version__ = "0.1.0"
