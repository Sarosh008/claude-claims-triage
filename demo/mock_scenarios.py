"""
Per-claim mock responses for the 5 sample claims in ``sample_claims.py``.

Used only when running the demo with ``--mock`` (no Anthropic API key). Without
this file, ``ClaimsTriageAgent(mock=True)`` returns the exact same canned
response for every claim regardless of its content — fine for unit tests, but
misleading for a demo dashboard where 5 different claims should visibly differ.

Each entry is keyed by a substring that appears in the claim's raw text (and,
via the extracted-fields JSON, propagates into later-stage prompts too), and
maps to hand-written — not API-generated — responses for all four pipeline
stages, grounded in what that claim's text actually says. This is still mock
data: it demonstrates what a correctly-functioning pipeline *should* produce
for each scenario, not a live Claude API call. Run without ``--mock`` (real
ANTHROPIC_API_KEY) to get genuine model output instead.
"""

MOCK_SCENARIOS: dict[str, dict[str, dict]] = {

    # CLM-2024-MUC-001 — Anna Müller, Munich, burst pipe / water damage
    "Schillerstraße": {
        "extract_claim_fields": {
            "policyholder_name": "Anna Müller",
            "policy_number": "HAV-MUC-88432",
            "incident_date": "2024-06-10",
            "incident_type": "burst pipe / water damage",
            "damage_description": (
                "Pipe burst behind the bathroom wall; parquet flooring in the "
                "hallway (~18 m²) warped beyond repair; living room drywall "
                "soaked and requires full replacement. Plumber confirmed the "
                "pipe had corroded through."
            ),
            "claimed_amount_eur": 8500.0,
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
            "completeness_score": 0.75,
            "information_sufficient_for_triage": True,
        },
        "generate_triage_decision": {
            "decision": "manual_review",
            "rationale": (
                "Medium-severity water damage with a plumber's preliminary report "
                "already on file; a formal repair estimate is still required "
                "before settlement can be authorised."
            ),
            "priority": "standard",
            "estimated_processing_days": 7,
            "next_action": "Request formal repair estimate and damage photos; assign to water damage specialist.",
        },
    },

    # CLM-2024-BER-002 — Thomas Berger, Berlin, burglary
    "Prenzlauer Allee": {
        "extract_claim_fields": {
            "policyholder_name": "Thomas Berger",
            "policy_number": "HHV-BER-29107",
            "incident_date": "2024-07-14",
            "incident_type": "burglary / theft",
            "damage_description": (
                "Balcony door forced on the 2nd floor overnight. MacBook Pro, "
                "Canon EOS R5 with two lenses, jewellery, and cash stolen."
            ),
            "claimed_amount_eur": 10600.0,
            "incident_location": "Prenzlauer Allee 77, 10405 Berlin",
            "third_parties_involved": True,
        },
        "classify_claim": {
            "peril_category": "theft_burglary",
            "severity": "high",
            "auto_processable": False,
            "flags": ["high_value_items"],
        },
        "assess_completeness": {
            "missing_fields": ["itemised_receipts_or_valuations"],
            "required_documents": ["police_report_copy", "itemised_receipts_or_valuations", "proof_of_ownership"],
            "completeness_score": 0.80,
            "information_sufficient_for_triage": True,
        },
        "generate_triage_decision": {
            "decision": "manual_review",
            "rationale": (
                "High-value burglary claim with a police report already filed; "
                "itemised proof of ownership is needed to substantiate the "
                "claimed amount before settlement."
            ),
            "priority": "urgent",
            "estimated_processing_days": 5,
            "next_action": "Request itemised receipts/valuations for stolen items; assign to theft claims specialist.",
        },
    },

    # CLM-2024-STU-003 — Klaus Brandt, Stuttgart, hail damage to vehicle
    "Königstraße": {
        "extract_claim_fields": {
            "policyholder_name": "Klaus Brandt",
            "policy_number": None,
            "incident_date": None,
            "incident_type": "hail damage / vehicle",
            "damage_description": (
                "Multiple dents across bonnet, roof and boot lid; cracked "
                "windscreen. Vehicle was parked outside during a severe "
                "hailstorm."
            ),
            "claimed_amount_eur": None,
            "incident_location": "Königstraße, Stuttgart",
            "third_parties_involved": False,
        },
        "classify_claim": {
            "peril_category": "vehicle",
            "severity": "medium",
            "auto_processable": False,
            "flags": [],
        },
        "assess_completeness": {
            "missing_fields": ["policy_number", "incident_date", "repair_estimate"],
            "required_documents": ["repair_estimate", "damage_photos", "vehicle_registration"],
            "completeness_score": 0.45,
            "information_sufficient_for_triage": False,
        },
        "generate_triage_decision": {
            "decision": "request_information",
            "rationale": (
                "Plausible hail-damage claim, but policy number, exact incident "
                "date, and a repair estimate are all missing — triage cannot "
                "proceed without them."
            ),
            "priority": "standard",
            "estimated_processing_days": 10,
            "next_action": "Request policy number, confirmed incident date, and a garage repair estimate from the policyholder.",
        },
    },

    # CLM-2024-HAM-004 — Fatima Al-Hassan, Hamburg, kitchen fire
    "Elbchaussee": {
        "extract_claim_fields": {
            "policyholder_name": "Fatima Al-Hassan",
            "policy_number": "GHV-HAM-51903",
            "incident_date": "2024-08-02",
            "incident_type": "kitchen fire",
            "damage_description": (
                "Electrical fault in the built-in oven caused a fire that spread "
                "to the kitchen cupboards and ceiling; possible load-bearing "
                "wall concern flagged by the fire brigade; smoke damage to the "
                "dining room and hallway. Kitchen is a complete write-off."
            ),
            "claimed_amount_eur": None,
            "incident_location": "Elbchaussee 200, 22605 Hamburg",
            "third_parties_involved": False,
        },
        "classify_claim": {
            "peril_category": "fire",
            "severity": "extreme",
            "auto_processable": False,
            "flags": ["structural_damage"],
        },
        "assess_completeness": {
            "missing_fields": ["repair_estimate", "structural_survey"],
            "required_documents": ["fire_brigade_report", "structural_survey", "repair_estimate", "damage_photos"],
            "completeness_score": 0.65,
            "information_sufficient_for_triage": True,
        },
        "generate_triage_decision": {
            "decision": "manual_review",
            "rationale": (
                "Extreme-severity fire with a flagged structural concern and a "
                "displaced policyholder — requires urgent senior handler review "
                "and a structural survey before any settlement figure can be "
                "assessed."
            ),
            "priority": "urgent",
            "estimated_processing_days": 14,
            "next_action": "Escalate to senior claims handler; commission structural survey; arrange interim accommodation support.",
        },
    },

    # CLM-2024-FFM-005 — Peter Hoffmann, Frankfurt, storm damage
    "Sachsenhäuser Berg": {
        "extract_claim_fields": {
            "policyholder_name": "Peter Hoffmann",
            "policy_number": "GHV-FFM-30041",
            "incident_date": "2024-10-19",
            "incident_type": "storm damage / roof and garden shed",
            "damage_description": (
                "Storm 'Axel' displaced ~30 roof tiles on the west-facing slope; "
                "rain has penetrated the attic space. Garden shed (approx. 4×3 m) "
                "completely destroyed — roof and walls collapsed, damaging "
                "lawnmower and tools stored inside."
            ),
            "claimed_amount_eur": 7150.0,
            "incident_location": "Am Sachsenhäuser Berg 12, 60594 Frankfurt am Main",
            "third_parties_involved": False,
        },
        "classify_claim": {
            "peril_category": "natural_hazard",
            "severity": "high",
            "auto_processable": False,
            "flags": [],
        },
        "assess_completeness": {
            "missing_fields": ["roof_repair_estimate"],
            "required_documents": ["repair_estimate", "damage_photos", "weather_service_confirmation"],
            "completeness_score": 0.70,
            "information_sufficient_for_triage": True,
        },
        "generate_triage_decision": {
            "decision": "manual_review",
            "rationale": (
                "High-severity storm damage across two structures; final roof "
                "repair estimate is still pending, but sufficient detail exists "
                "to begin triage, and interim tarpaulin mitigation is already "
                "in place."
            ),
            "priority": "standard",
            "estimated_processing_days": 9,
            "next_action": "Request final roof repair estimate; confirm storm event via regional weather service record; assign to natural hazard team.",
        },
    },
}
