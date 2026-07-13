"""Tests for output reporters (claims_triage/reporter.py)."""
import csv
import io
import json
import pytest

from claims_triage.agent import ClaimsTriageAgent
from claims_triage.reporter import to_json, to_csv, to_html


@pytest.fixture
def two_results(mock_agent, water_claim, burglary_claim):
    r1 = mock_agent.process_claim(water_claim[1], claim_id=water_claim[0])
    r2 = mock_agent.process_claim(burglary_claim[1], claim_id=burglary_claim[0])
    return [r1, r2]


class TestToJson:
    def test_returns_string(self, two_results):
        assert isinstance(to_json(two_results), str)

    def test_parses_to_list(self, two_results):
        data = json.loads(to_json(two_results))
        assert isinstance(data, list)

    def test_correct_count(self, two_results):
        data = json.loads(to_json(two_results))
        assert len(data) == 2

    def test_contains_claim_ids(self, two_results):
        data = json.loads(to_json(two_results))
        ids = {d["claim_id"] for d in data}
        assert "CLM-T-001" in ids
        assert "CLM-T-002" in ids

    def test_nested_structure(self, two_results):
        data = json.loads(to_json(two_results))
        for item in data:
            assert "extracted" in item
            assert "classification" in item
            assert "completeness" in item
            assert "decision" in item


class TestToCsv:
    def test_returns_string(self, two_results):
        assert isinstance(to_csv(two_results), str)

    def test_parseable_as_csv(self, two_results):
        reader = csv.reader(io.StringIO(to_csv(two_results)))
        rows = list(reader)
        assert len(rows) == 3  # header + 2 data rows

    def test_header_row(self, two_results):
        reader = csv.reader(io.StringIO(to_csv(two_results)))
        header = next(reader)
        assert "claim_id" in header
        assert "decision" in header
        assert "severity" in header

    def test_data_rows_have_claim_ids(self, two_results):
        reader = csv.reader(io.StringIO(to_csv(two_results)))
        header = next(reader)
        id_col = header.index("claim_id")
        ids = [row[id_col] for row in reader]
        assert "CLM-T-001" in ids
        assert "CLM-T-002" in ids


class TestToHtml:
    def test_returns_string(self, two_results):
        assert isinstance(to_html(two_results), str)

    def test_is_valid_html(self, two_results):
        html = to_html(two_results)
        assert html.strip().startswith("<!DOCTYPE html>")

    def test_contains_claim_ids(self, two_results):
        html = to_html(two_results)
        assert "CLM-T-001" in html
        assert "CLM-T-002" in html

    def test_contains_anthropic_attribution(self, two_results):
        html = to_html(two_results)
        assert "Anthropic" in html

    def test_contains_stats_section(self, two_results):
        html = to_html(two_results)
        # Stats section shows decision counts
        assert "Claims processed" in html

    def test_table_present(self, two_results):
        html = to_html(two_results)
        assert "<table>" in html and "</table>" in html
