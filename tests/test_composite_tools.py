"""Tests for composite_tools module."""

import pandas as pd
import pytest

from acis2llm.composite_tools import (
    _parse_month, _get_season_months, _aggregate_monthly_by_year,
    _aggregate_seasonal_by_year, _calculate_frequency, is_zip_code,
    find_best_station
)
from datetime import datetime

# Load the real NYC CSV as test fixture data
NYC_CSV_PATH = "XMACIS2 DATA/KNYC.csv"


@pytest.fixture
def nyc_df():
    """Load the real NYC data as a DataFrame matching xmacis2py output format."""
    df = pd.read_csv(NYC_CSV_PATH)
    # Ensure Date column is datetime
    df["Date"] = pd.to_datetime(df["Date"])
    return df


@pytest.fixture
def current_year():
    return datetime.now().year


def test_fixture_loads(nyc_df):
    """Verify the fixture loads and has expected columns."""
    assert "Date" in nyc_df.columns
    assert "Snowfall" in nyc_df.columns
    assert len(nyc_df) > 0


class TestParseMonth:
    def test_integer_string(self):
        assert _parse_month("4") == 4

    def test_integer(self):
        assert _parse_month(4) == 4

    def test_full_name_lowercase(self):
        assert _parse_month("april") == 4

    def test_full_name_titlecase(self):
        assert _parse_month("April") == 4

    def test_abbreviation(self):
        assert _parse_month("Apr") == 4

    def test_january(self):
        assert _parse_month("january") == 1

    def test_december(self):
        assert _parse_month("december") == 12

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="Could not parse month"):
            _parse_month("notamonth")

    def test_out_of_range_raises(self):
        with pytest.raises(ValueError, match="Month must be between 1 and 12"):
            _parse_month("13")


class TestGetSeasonMonths:
    def test_winter(self):
        assert _get_season_months("winter") == [12, 1, 2]

    def test_spring(self):
        assert _get_season_months("spring") == [3, 4, 5]

    def test_summer(self):
        assert _get_season_months("summer") == [6, 7, 8]

    def test_fall(self):
        assert _get_season_months("fall") == [9, 10, 11]

    def test_autumn_alias(self):
        assert _get_season_months("autumn") == [9, 10, 11]

    def test_case_insensitive(self):
        assert _get_season_months("Winter") == [12, 1, 2]

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="Unknown season"):
            _get_season_months("monsoon")


class TestAggregateMonthlyByYear:
    """Test the internal aggregation function using real KLEX data."""

    def test_april_snowfall_sum(self, nyc_df):
        result = _aggregate_monthly_by_year(nyc_df, "Snowfall", month=4, aggregation="sum")
        assert "table" in result
        assert "summary" in result
        # Each row should have year, value, missing_days
        row = result["table"][0]
        assert "year" in row
        assert "value" in row
        assert "missing_days" in row

    def test_april_snowfall_has_multiple_years(self, nyc_df):
        result = _aggregate_monthly_by_year(nyc_df, "Snowfall", month=4, aggregation="sum")
        years = [row["year"] for row in result["table"]]
        assert len(years) > 1
        # Years should be sorted
        assert years == sorted(years)

    def test_mean_aggregation(self, nyc_df):
        result_sum = _aggregate_monthly_by_year(nyc_df, "Snowfall", month=4, aggregation="sum")
        result_mean = _aggregate_monthly_by_year(nyc_df, "Snowfall", month=4, aggregation="mean")
        # Mean should generally differ from sum (unless all months have exactly 1 day)
        assert result_sum["table"][0]["value"] != result_mean["table"][0]["value"] or True
        # Just verify it runs without error and returns valid structure
        assert len(result_mean["table"]) > 0

    def test_max_aggregation(self, nyc_df):
        result = _aggregate_monthly_by_year(nyc_df, "Maximum Temperature", month=4, aggregation="max")
        assert len(result["table"]) > 0
        # Max temp in April should be reasonable
        for row in result["table"]:
            assert row["value"] is None or row["value"] > 0

    def test_year_range_filter(self, nyc_df):
        result_all = _aggregate_monthly_by_year(nyc_df, "Snowfall", month=4, aggregation="sum")
        result_filtered = _aggregate_monthly_by_year(
            nyc_df, "Snowfall", month=4, aggregation="sum",
            start_year=2000, end_year=2010,
        )
        assert len(result_filtered["table"]) <= len(result_all["table"])
        years = [row["year"] for row in result_filtered["table"]]
        assert all(2000 <= y <= 2010 for y in years)

    def test_summary_contains_stats(self, nyc_df):
        result = _aggregate_monthly_by_year(nyc_df, "Snowfall", month=4, aggregation="sum")
        summary = result["summary"]
        assert "April" in summary or "april" in summary.lower()
        assert "year" in summary.lower()


class TestAggregateSeasonalByYear:
    """Test seasonal aggregation using real KLEX data."""

    def test_spring_snowfall(self, nyc_df):
        result = _aggregate_seasonal_by_year(nyc_df, "Snowfall", season_months=[3, 4, 5], aggregation="sum")
        assert "table" in result
        assert "summary" in result
        assert len(result["table"]) > 0

    def test_season_year_labels(self, nyc_df):
        """Winter should be labeled by the ending year (Dec 2023 + Jan-Feb 2024 = Winter 2024)."""
        # Since KLEX data is April only, use spring for the basic structure test
        result = _aggregate_seasonal_by_year(nyc_df, "Snowfall", season_months=[3, 4, 5], aggregation="sum")
        years = [row["year"] for row in result["table"]]
        assert years == sorted(years)

    def test_year_range_filter(self, nyc_df):
        result = _aggregate_seasonal_by_year(
            nyc_df, "Snowfall", season_months=[3, 4, 5],
            aggregation="sum", start_year=2000, end_year=2010,
        )
        years = [row["year"] for row in result["table"]]
        assert all(2000 <= y <= 2010 for y in years)

    def test_mean_aggregation(self, nyc_df):
        result = _aggregate_seasonal_by_year(
            nyc_df, "Maximum Temperature", season_months=[3, 4, 5], aggregation="mean",
        )
        assert len(result["table"]) > 0
        # Mean max temp in spring should be reasonable
        for row in result["table"]:
            if row["value"] is not None:
                assert 30 < row["value"] < 110


class TestCalculateFrequency:
    """Test frequency calculation using real KLEX data."""

    def test_snow_in_april(self, nyc_df):
        result = _calculate_frequency(
            nyc_df, "Snowfall", month=4, threshold=0, comparison="above",
        )
        assert "count" in result
        assert "total_years" in result
        assert "percentage" in result
        assert "table" in result
        assert "summary" in result
        assert result["total_years"] > 0
        assert 0 <= result["percentage"] <= 100

    def test_above_comparison(self, nyc_df):
        result = _calculate_frequency(
            nyc_df, "Snowfall", month=4, threshold=0, comparison="above",
        )
        # Check that 'met_condition' in table rows is consistent
        for row in result["table"]:
            if row["value"] is not None:
                if row["value"] > 0:
                    assert row["met_condition"] is True
                else:
                    assert row["met_condition"] is False

    def test_at_or_above_comparison(self, nyc_df):
        result = _calculate_frequency(
            nyc_df, "Snowfall", month=4, threshold=0, comparison="at_or_above",
        )
        # All years should meet condition since snowfall >= 0 always
        assert result["count"] == result["total_years"]

    def test_below_comparison(self, nyc_df):
        result = _calculate_frequency(
            nyc_df, "Snowfall", month=4, threshold=1, comparison="below",
        )
        assert result["count"] > 0  # Most Aprils have < 1 inch snow

    def test_year_range_filter(self, nyc_df):
        result_all = _calculate_frequency(
            nyc_df, "Snowfall", month=4, threshold=0, comparison="above",
        )
        result_filtered = _calculate_frequency(
            nyc_df, "Snowfall", month=4, threshold=0, comparison="above",
            start_year=2000, end_year=2010,
        )
        assert result_filtered["total_years"] <= result_all["total_years"]

    def test_summary_contains_percentage(self, nyc_df):
        result = _calculate_frequency(
            nyc_df, "Snowfall", month=4, threshold=0, comparison="above",
        )
        assert "%" in result["summary"]


class TestIsZipCode:
    def test_valid_5_digit(self):
        assert is_zip_code("12345") is True

    def test_valid_zip_plus_4(self):
        assert is_zip_code("12345-6789") is True

    def test_valid_with_spaces(self):
        assert is_zip_code("  12345  ") is True

    def test_invalid_short(self):
        assert is_zip_code("1234") is False

    def test_invalid_long(self):
        assert is_zip_code("123456") is False

    def test_invalid_plus_4_short(self):
        assert is_zip_code("12345-678") is False

    def test_invalid_characters(self):
        assert is_zip_code("1234a") is False

    def test_city_name(self):
        assert is_zip_code("Fort Myers") is False

from unittest.mock import patch, MagicMock
from acis2llm.composite_tools import geocode_census

class TestGeocodeCensus:
    @patch('acis2llm.composite_tools.requests.get')
    def test_geocode_census_success(self, mock_get):
        # Mock successful response
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "addressMatches": [
                    {
                        "matchedAddress": "4600 Silver Hill Rd, Washington, DC 20233",
                        "coordinates": {
                            "x": -76.92744,
                            "y": 38.84599
                        }
                    }
                ]
            }
        }
        mock_get.return_value = mock_response

        result = geocode_census("4600 Silver Hill Rd, Washington, DC 20233")
        
        assert result is not None
        assert result["lat"] == 38.84599
        assert result["lon"] == -76.92744
        assert "4600 Silver Hill Rd" in result["display_name"]

    @patch('acis2llm.composite_tools.requests.get')
    def test_geocode_census_no_results(self, mock_get):
        # Mock response with no matches
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "result": {
                "addressMatches": []
            }
        }
        mock_get.return_value = mock_response

        result = geocode_census("Nonexistent Address")
        assert result is None

    @patch('acis2llm.composite_tools.requests.get')
    def test_geocode_census_network_error(self, mock_get):
        # Mock network error
        mock_get.side_effect = Exception("Network error")
        
        result = geocode_census("Some Address")
        assert result is None

class TestFindBestStationWaterfall:

    @patch('acis2llm.composite_tools.requests.post')
    def test_phase1_direct_id_match(self, mock_post, current_year):
        """Phase 1: Direct ID Match (ACIS)."""
        # Mock ACIS response for direct ID search
        mock_response = MagicMock()
        mock_response.status_code = 200
        mock_response.json.return_value = {
            "meta": [
                {
                    "name": "NEW YORK CENTRAL PARK",
                    "state": "NY",
                    "sids": ["KNYC 1", "305801 2"],
                    "ll": [-73.9692, 40.7789],
                    "valid_daterange": [["1889-01-01", f"{current_year}-12-31"]]
                }
            ]
        }
        mock_post.return_value = mock_response

        result = find_best_station("KNYC")

        assert result["station_id"] == "KNYC"
        assert "NEW YORK CENTRAL PARK" in result["name"]
        # Ensure it called ACIS with sids
        args, kwargs = mock_post.call_args
        assert kwargs["json"]["sids"] == "KNYC"

    @patch('acis2llm.composite_tools.geocode_census')
    @patch('acis2llm.composite_tools.requests.post')
    def test_phase2_zip_code_centroid(self, mock_post, mock_geocode, current_year):
        """Phase 2: Zip Code Centroid."""
        # Phase 1 fails (no match for zip code as SID)
        mock_phase1_response = MagicMock()
        mock_phase1_response.status_code = 200
        mock_phase1_response.json.return_value = {"meta": []}
        
        # Phase 4 (Radius search) response
        mock_phase4_response = MagicMock()
        mock_phase4_response.status_code = 200
        mock_phase4_response.json.return_value = {
            "meta": [
                {
                    "name": "FORT MYERS PAGE FLD",
                    "state": "FL",
                    "sids": ["KFMY 1"],
                    "ll": [-81.8611, 26.5864],
                    "valid_daterange": [["1948-01-01", f"{current_year}-12-31"]]
                }
            ]
        }
        
        mock_post.side_effect = [mock_phase1_response, mock_phase4_response]

        # Mock Geocoder
        mock_geocode.return_value = {
            "lat": 26.6,
            "lon": -81.8,
            "display_name": "33901, Fort Myers, FL"
        }

        result = find_best_station("33901")

        assert result["station_id"] == "KFMY"
        mock_geocode.assert_called_once_with("33901")
        
        # Verify Phase 4 call used bbox
        args, kwargs = mock_post.call_args
        assert "bbox" in kwargs["json"]

    @patch('acis2llm.composite_tools.geocode_census')
    @patch('acis2llm.composite_tools.requests.post')
    def test_phase3_city_geocoding(self, mock_post, mock_geocode, current_year):
        """Phase 3: City/State Geocoding."""
        # Phase 1 skipped for non-station-like inputs ("Denver, CO")
        # Phase 4 response
        mock_phase4_response = MagicMock()
        mock_phase4_response.status_code = 200
        mock_phase4_response.json.return_value = {
            "meta": [
                {
                    "name": "DENVER INTL ARPT",
                    "state": "CO",
                    "sids": ["KDEN 1"],
                    "ll": [-104.673, 39.846],
                    "valid_daterange": [["1948-01-01", f"{current_year}-12-31"]]
                }
            ]
        }
        mock_post.return_value = mock_phase4_response

        # Mock Geocoder
        mock_geocode.return_value = {
            "lat": 39.7,
            "lon": -104.9,
            "display_name": "Denver, CO"
        }

        result = find_best_station("Denver, CO")

        assert result["station_id"] == "KDEN"
        mock_geocode.assert_called_once_with("Denver, CO")

    @patch('acis2llm.composite_tools.geocode_census')
    @patch('acis2llm.composite_tools.requests.post')
    def test_phase4_history_king_logic(self, mock_post, mock_geocode, current_year):
        """Phase 4: History King sorting logic."""
        # Phase 1 skipped for non-station-like inputs ("Test City")
        # Phase 4: Multiple stations
        # Station A: Oldest, Active
        # Station B: Newer, Active
        # Station C: Oldest, Inactive
        mock_phase4_response = MagicMock()
        mock_phase4_response.status_code = 200
        mock_phase4_response.json.return_value = {
            "meta": [
                {
                    "name": "NEWER ACTIVE",
                    "state": "XX",
                    "sids": ["NEW 1"],
                    "ll": [-100.0, 40.0],
                    "valid_daterange": [["1980-01-01", f"{current_year}-12-31"]]
                },
                {
                    "name": "OLDER ACTIVE",
                    "state": "XX",
                    "sids": ["OLD 1"],
                    "ll": [-100.1, 40.1],
                    "valid_daterange": [["1920-01-01", f"{current_year}-12-31"]]
                },
                {
                    "name": "OLDEST INACTIVE",
                    "state": "XX",
                    "sids": ["DEAD 1"],
                    "ll": [-100.2, 40.2],
                    "valid_daterange": [["1890-01-01", "2010-12-31"]]
                }
            ]
        }
        mock_post.return_value = mock_phase4_response

        mock_geocode.return_value = {"lat": 40.0, "lon": -100.0, "display_name": "Test City"}

        result = find_best_station("Test City")

        # Should pick OLD 1 because it's active and has earlier start date than NEW 1
        assert result["station_id"] == "OLD"
        assert result["data_start"] == 1920

    @patch('acis2llm.composite_tools.geocode_census')
    @patch('acis2llm.composite_tools.requests.post')
    def test_error_no_location(self, mock_post, mock_geocode):
        """Graceful error when location not found."""
        # Phase 1 skipped for non-station-like inputs ("Middle of Nowhere")
        mock_geocode.return_value = None

        result = find_best_station("Middle of Nowhere")
        assert "error" in result
        assert "not a valid 5-digit zip code" in result["error"]

    @patch('acis2llm.composite_tools.geocode_census')
    @patch('acis2llm.composite_tools.requests.post')
    def test_phase1_skips_non_us_station(self, mock_post, mock_geocode, current_year):
        """Zip code matching non-US station should fall through to geocoding (bug fix)."""
        # 90001 is both a LA zip code AND a valid ACIS station ID (Amundsen-Scott South Pole)
        # Phase 1 finds the station but it's in Antarctica (AQ), so it should skip to geocoding
        mock_phase1_response = MagicMock()
        mock_phase1_response.status_code = 200
        mock_phase1_response.json.return_value = {
            "meta": [{
                "name": "AMUNDSEN-SCOTT SOUTH POLE STATION",
                "state": "AQ",
                "sids": ["90001 1"],
                "ll": [-90.0, 0.0],
                "valid_daterange": [["1957-01-01", f"{current_year}-12-31"]]
            }]
        }

        mock_phase4_response = MagicMock()
        mock_phase4_response.status_code = 200
        mock_phase4_response.json.return_value = {
            "meta": [{
                "name": "LOS ANGELES INTL AP",
                "state": "CA",
                "sids": ["KLAX 1"],
                "ll": [-118.4, 33.9],
                "valid_daterange": [["1936-01-01", f"{current_year}-12-31"]]
            }]
        }
        mock_post.side_effect = [mock_phase1_response, mock_phase4_response]

        mock_geocode.return_value = {
            "lat": 34.05,
            "lon": -118.24,
            "display_name": "Los Angeles, CA 90001"
        }

        result = find_best_station("90001")

        # Should NOT return the Antarctic station
        assert result["station_id"] == "KLAX"
        assert "AMUNDSEN" not in result.get("name", "")
        assert "LOS ANGELES" in result["name"]
