"""
Claude tool definitions for the four-stage claims triage pipeline.

Each tool maps to one processing stage. Forcing tool_choice ensures Claude
returns deterministic structured JSON — safe for batch processing at scale.
"""

# ── Stage 1: Extract structured fields from raw claim text ────────────────────

EXTRACT_TOOL = {
    "name": "extract_claim_fields",
    "description": (
        "Extract structured fields from an unstructured insurance claim submission. "
        "Return null for fields not mentioned in the text — never invent values."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "policyholder_name": {
                "type": "string",
                "description": "Name of the insured person or entity"
            },
            "policy_number": {
                "type": "string",
                "description": "Insurance policy number if stated"
            },
            "incident_date": {
                "type": "string",
                "description": "Date of the incident (ISO 8601 preferred, or as stated)"
            },
            "incident_type": {
                "type": "string",
                "description": "Concise incident label (e.g. 'burst pipe', 'burglary', 'hail damage')"
            },
            "damage_description": {
                "type": "string",
                "description": "What was damaged and how, as described in the submission"
            },
            "claimed_amount_eur": {
                "type": "number",
                "description": "Claimed amount in EUR if stated, otherwise null"
            },
            "incident_location": {
                "type": "string",
                "description": "Address or location of the incident"
            },
            "third_parties_involved": {
                "type": "boolean",
                "description": "Whether any third parties (other persons/vehicles) are involved"
            },
        },
        "required": ["incident_type", "damage_description"],
    },
}

# ── Stage 2: Classify peril category and severity ─────────────────────────────

CLASSIFY_TOOL = {
    "name": "classify_claim",
    "description": (
        "Classify the insurance claim by peril category and severity. "
        "Base severity on described damage extent and context, not the claimed amount alone."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "peril_category": {
                "type": "string",
                "enum": [
                    "water_damage", "fire", "theft_burglary",
                    "natural_hazard", "liability", "vehicle", "glass", "other"
                ],
                "description": "Primary peril category"
            },
            "severity": {
                "type": "string",
                "enum": ["low", "medium", "high", "extreme"],
                "description": "Estimated damage severity"
            },
            "auto_processable": {
                "type": "boolean",
                "description": "Whether the claim can be settled automatically without human review"
            },
            "flags": {
                "type": "array",
                "items": {"type": "string"},
                "description": (
                    "Special attention flags, e.g. 'possible_fraud', "
                    "'structural_damage', 'third_party_injury', 'repeat_claimant'"
                )
            },
        },
        "required": ["peril_category", "severity", "auto_processable"],
    },
}

# ── Stage 3: Assess information completeness ──────────────────────────────────

ASSESS_TOOL = {
    "name": "assess_completeness",
    "description": (
        "Identify missing information and required documents for claims processing. "
        "Be specific — list actual field names and document types, not vague categories."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "missing_fields": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Information fields not provided but typically required for this peril"
            },
            "required_documents": {
                "type": "array",
                "items": {"type": "string"},
                "description": "Documents to be submitted, e.g. 'police report', 'repair estimate', 'damage photos'"
            },
            "completeness_score": {
                "type": "number",
                "description": "0.0 (nothing) to 1.0 (all required info present)"
            },
            "information_sufficient_for_triage": {
                "type": "boolean",
                "description": "Whether existing info is sufficient to make an initial triage decision"
            },
        },
        "required": [
            "missing_fields", "required_documents",
            "completeness_score", "information_sufficient_for_triage"
        ],
    },
}

# ── Stage 4: Generate triage decision ─────────────────────────────────────────

DECIDE_TOOL = {
    "name": "generate_triage_decision",
    "description": (
        "Generate a triage decision and workflow routing for the claim based on all "
        "extracted, classified, and completeness information."
    ),
    "input_schema": {
        "type": "object",
        "properties": {
            "decision": {
                "type": "string",
                "enum": ["auto_approve", "manual_review", "request_information", "reject"],
                "description": (
                    "Triage outcome: "
                    "auto_approve = meets all criteria for straight-through processing; "
                    "manual_review = sufficient info but needs human judgment; "
                    "request_information = missing critical info before triage can proceed; "
                    "reject = policy exclusion or fraud indicator"
                )
            },
            "rationale": {
                "type": "string",
                "description": "Client-readable explanation of the decision (1–2 sentences)"
            },
            "priority": {
                "type": "string",
                "enum": ["urgent", "standard", "low"],
                "description": "Processing priority"
            },
            "estimated_processing_days": {
                "type": "integer",
                "description": "Estimated calendar days to resolution"
            },
            "next_action": {
                "type": "string",
                "description": "Specific next action for the claims handler or automated system"
            },
        },
        "required": ["decision", "rationale", "priority", "estimated_processing_days"],
    },
}

# Convenience list of all tools in pipeline order
ALL_TOOLS = [EXTRACT_TOOL, CLASSIFY_TOOL, ASSESS_TOOL, DECIDE_TOOL]
