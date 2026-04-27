"""Tests for the multi_station fetch helper."""

import pandas as pd

from acis2llm.multi_station import fetch_stations


def test_single_station(mocker):
    mock = mocker.patch("xmacis2py.get_single_station_acis_data")
    mock.return_value = pd.DataFrame({
        "Date": ["2023-01-01"],
        "Maximum Temperature": [45],
    })

    result = fetch_stations("KNYC", start_date="2023-01-01", end_date="2023-01-01")

    assert isinstance(result, pd.DataFrame)
    assert len(result) == 1
    mock.assert_called_once()


def test_all_stations(mocker):
    mock = mocker.patch("xmacis2py.get_multi_station_acis_data")
    mock.return_value = pd.DataFrame({
        "station": ["KNYC", "KLAX"],
        "Date": ["2023-01-01", "2023-01-01"],
        "Maximum Temperature": [45, 60],
    })

    result = fetch_stations("ALL", start_date="2023-01-01", end_date="2023-01-01")

    mock.assert_called_once_with(stations="ALL", start_date="2023-01-01", end_date="2023-01-01")
    assert len(result) == 2


def test_comma_aggregate(mocker):
    """Comma-separated stations fetch in parallel and concat with a station column."""
    def fake(station, **_):
        return pd.DataFrame({
            "Date": ["2023-01-01"],
            "Maximum Temperature": [{"KNYC": 45, "KJFK": 44}[station]],
        })

    mocker.patch("xmacis2py.get_single_station_acis_data", side_effect=fake)

    result = fetch_stations("KNYC,KJFK", start_date="2023-01-01", end_date="2023-01-01")

    assert "station" in result.columns
    assert set(result["station"]) == {"KNYC", "KJFK"}
    assert len(result) == 2


def test_plus_backfill(mocker):
    """Plus-separated stations backfill: primary first, then later stations fill gaps."""
    def fake(station, **_):
        if station == "PRIMARY":
            return pd.DataFrame({
                "Date": ["2023-01-02"],   # only has Jan 2
                "Maximum Temperature": [50],
            })
        return pd.DataFrame({
            "Date": ["2023-01-01", "2023-01-02"],
            "Maximum Temperature": [99, 99],   # backfill candidate, also has Jan 2 (should not overwrite)
        })

    mocker.patch("xmacis2py.get_single_station_acis_data", side_effect=fake)

    result = fetch_stations("PRIMARY+OLDER", start_date="2023-01-01", end_date="2023-01-02")

    # Should have both dates, with Jan 2 keeping PRIMARY's value (50, not 99)
    assert len(result) == 2
    jan2 = result[result["Date"] == "2023-01-02"]
    assert jan2["Maximum Temperature"].iloc[0] == 50
    assert (result["station"] == "PRIMARY+OLDER").all()


def test_error_returns_empty(mocker):
    mocker.patch("xmacis2py.get_single_station_acis_data", side_effect=Exception("boom"))
    result = fetch_stations("KNYC")
    assert isinstance(result, pd.DataFrame)
    assert result.empty
