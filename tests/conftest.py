"""Shared fixtures for the claude-claims-triage test suite."""
import pytest
from claims_triage.agent import ClaimsTriageAgent, _DEFAULT_MOCK_RESPONSES


# ── Fixtures ──────────────────────────────────────────────────────────────────

@pytest.fixture
def mock_agent():
    """A ClaimsTriageAgent using the default mock client."""
    return ClaimsTriageAgent(mock=True)


@pytest.fixture
def water_claim():
    return (
        "CLM-T-001",
        (
            "Policyholder: Anna Müller. Policy: HAV-001. "
            "On 10 June 2024 a pipe burst in my Munich bathroom, flooding the hallway. "
            "Parquet flooring (~18 m²) destroyed. Estimate: €6,800."
        ),
    )


@pytest.fixture
def burglary_claim():
    return (
        "CLM-T-002",
        (
            "Thomas Berger, Berlin. Policy HHV-002. Burglary on 14 July — "
            "balcony door forced, laptop €2,200 and jewellery €3,000 stolen. "
            "Police report PD-BER-2024-078234 filed."
        ),
    )


@pytest.fixture
def incomplete_claim():
    """A very sparse claim — minimal information provided."""
    return (
        "CLM-T-003",
        "My roof was damaged. Please help.",
    )


@pytest.fixture
def mock_result(mock_agent, water_claim):
    claim_id, claim_text = water_claim
    return mock_agent.process_claim(claim_text, claim_id=claim_id)
