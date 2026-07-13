"""Tests for tool schema definitions (claims_triage/tools.py)."""
import pytest
from claims_triage.tools import (
    EXTRACT_TOOL, CLASSIFY_TOOL, ASSESS_TOOL, DECIDE_TOOL, ALL_TOOLS
)


# ── Structure tests ───────────────────────────────────────────────────────────

class TestToolSchemas:
    def test_all_tools_list_length(self):
        assert len(ALL_TOOLS) == 4

    def test_all_tools_have_required_keys(self):
        for tool in ALL_TOOLS:
            assert "name" in tool
            assert "description" in tool
            assert "input_schema" in tool

    def test_all_tools_have_object_schema(self):
        for tool in ALL_TOOLS:
            assert tool["input_schema"]["type"] == "object"

    def test_all_tools_have_properties(self):
        for tool in ALL_TOOLS:
            assert "properties" in tool["input_schema"]
            assert len(tool["input_schema"]["properties"]) > 0


class TestExtractTool:
    def test_name(self):
        assert EXTRACT_TOOL["name"] == "extract_claim_fields"

    def test_has_incident_type_required(self):
        assert "incident_type" in EXTRACT_TOOL["input_schema"]["required"]

    def test_has_damage_description_required(self):
        assert "damage_description" in EXTRACT_TOOL["input_schema"]["required"]

    def test_claimed_amount_is_number(self):
        prop = EXTRACT_TOOL["input_schema"]["properties"]["claimed_amount_eur"]
        assert prop["type"] == "number"

    def test_third_parties_is_boolean(self):
        prop = EXTRACT_TOOL["input_schema"]["properties"]["third_parties_involved"]
        assert prop["type"] == "boolean"


class TestClassifyTool:
    def test_name(self):
        assert CLASSIFY_TOOL["name"] == "classify_claim"

    def test_severity_enum_values(self):
        sev = CLASSIFY_TOOL["input_schema"]["properties"]["severity"]
        assert set(sev["enum"]) == {"low", "medium", "high", "extreme"}

    def test_peril_enum_includes_water_fire_theft(self):
        peril = CLASSIFY_TOOL["input_schema"]["properties"]["peril_category"]
        perils = set(peril["enum"])
        assert {"water_damage", "fire", "theft_burglary"}.issubset(perils)

    def test_auto_processable_is_boolean(self):
        prop = CLASSIFY_TOOL["input_schema"]["properties"]["auto_processable"]
        assert prop["type"] == "boolean"

    def test_flags_is_array(self):
        prop = CLASSIFY_TOOL["input_schema"]["properties"]["flags"]
        assert prop["type"] == "array"


class TestAssessTool:
    def test_name(self):
        assert ASSESS_TOOL["name"] == "assess_completeness"

    def test_completeness_score_is_number(self):
        prop = ASSESS_TOOL["input_schema"]["properties"]["completeness_score"]
        assert prop["type"] == "number"

    def test_missing_fields_is_array(self):
        prop = ASSESS_TOOL["input_schema"]["properties"]["missing_fields"]
        assert prop["type"] == "array"

    def test_has_information_sufficient_field(self):
        assert "information_sufficient_for_triage" in ASSESS_TOOL["input_schema"]["properties"]


class TestDecideTool:
    def test_name(self):
        assert DECIDE_TOOL["name"] == "generate_triage_decision"

    def test_decision_enum_values(self):
        dec = DECIDE_TOOL["input_schema"]["properties"]["decision"]
        assert set(dec["enum"]) == {
            "auto_approve", "manual_review", "request_information", "reject"
        }

    def test_required_fields(self):
        req = set(DECIDE_TOOL["input_schema"]["required"])
        assert {"decision", "rationale", "priority", "estimated_processing_days"}.issubset(req)

    def test_estimated_processing_days_is_integer(self):
        prop = DECIDE_TOOL["input_schema"]["properties"]["estimated_processing_days"]
        assert prop["type"] == "integer"
