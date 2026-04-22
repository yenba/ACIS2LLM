"""Tests for the waterfall logic in find_best_station."""

import pytest
from unittest.mock import patch, MagicMock
from datetime import datetime
from composite_tools import find_best_station

@pytest.fixture
def current_year():
    return datetime.now().year

class TestFindBestStationWaterfall:

    @patch('composite_tools.requests.post')
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

    @patch('composite_tools.geocode_census')
    @patch('composite_tools.requests.post')
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

    @patch('composite_tools.geocode_census')
    @patch('composite_tools.requests.post')
    def test_phase3_city_geocoding(self, mock_post, mock_geocode, current_year):
        """Phase 3: City/State Geocoding."""
        # Phase 1 fails
        mock_phase1_response = MagicMock()
        mock_phase1_response.status_code = 200
        mock_phase1_response.json.return_value = {"meta": []}
        
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
        mock_post.side_effect = [mock_phase1_response, mock_phase4_response]

        # Mock Geocoder
        mock_geocode.return_value = {
            "lat": 39.7,
            "lon": -104.9,
            "display_name": "Denver, CO"
        }

        result = find_best_station("Denver, CO")

        assert result["station_id"] == "KDEN"
        mock_geocode.assert_called_once_with("Denver, CO")

    @patch('composite_tools.geocode_census')
    @patch('composite_tools.requests.post')
    def test_phase4_history_king_logic(self, mock_post, mock_geocode, current_year):
        """Phase 4: History King sorting logic."""
        # Phase 1 fails
        mock_phase1_response = MagicMock()
        mock_phase1_response.status_code = 200
        mock_phase1_response.json.return_value = {"meta": []}
        
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
        mock_post.side_effect = [mock_phase1_response, mock_phase4_response]

        mock_geocode.return_value = {"lat": 40.0, "lon": -100.0, "display_name": "Test City"}

        result = find_best_station("Test City")

        # Should pick OLD 1 because it's active and has earlier start date than NEW 1
        assert result["station_id"] == "OLD"
        assert result["data_start"] == 1920

    @patch('composite_tools.geocode_census')
    @patch('composite_tools.requests.post')
    def test_error_no_location(self, mock_post, mock_geocode):
        """Graceful error when location not found."""
        # Phase 1 fails
        mock_phase1_response = MagicMock()
        mock_phase1_response.status_code = 200
        mock_phase1_response.json.return_value = {"meta": []}
        mock_post.return_value = mock_phase1_response

        # Geocoder fails
        mock_geocode.return_value = None

        result = find_best_station("Middle of Nowhere")
        assert "error" in result
        assert "Could not geocode" in result["error"]
