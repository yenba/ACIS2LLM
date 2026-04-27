"""Tests for composite tool formatting."""

from acis2llm.formatter import format_composite_result


class TestFormatCompositeResult:
    def test_monthly_totals_format(self):
        result = {
            "table": [
                {"year": 2020, "value": 0.0, "missing_days": 0},
                {"year": 2021, "value": 1.5, "missing_days": 0},
                {"year": 2022, "value": 0.0, "missing_days": 2},
            ],
            "summary": "April Snowfall (sum) across 3 years (2020-2022), Average: 0.50",
        }
        output = format_composite_result(result, "monthly_totals_by_year")
        assert "2020" in output
        assert "2021" in output
        assert "1.5" in output or "1.50" in output
        assert "Average" in output

    def test_frequency_format(self):
        result = {
            "count": 2,
            "total_years": 10,
            "percentage": 20.0,
            "table": [
                {"year": 2020, "value": 0.0, "met_condition": False},
                {"year": 2021, "value": 1.5, "met_condition": True},
            ],
            "summary": "Snowfall above 0 occurred in 2 of 10 years (20.0%).",
        }
        output = format_composite_result(result, "frequency_of_occurrence")
        assert "20.0%" in output
        assert "2 of 10" in output

    def test_empty_table(self):
        result = {
            "table": [],
            "summary": "No data found for April.",
        }
        output = format_composite_result(result, "monthly_totals_by_year")
        assert "No data" in output
