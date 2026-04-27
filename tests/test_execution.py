import pandas as pd
from acis2llm.execution import _run_get_data, execute_tool_call
import pytest

def test_run_get_data(mocker):
    mock_get_data = mocker.patch("xmacis2py.get_single_station_acis_data")
    mock_df = pd.DataFrame({"station": ["KNYC"], "valid_date": ["2023-01-01"], "Maximum Temperature": [45]})
    mock_get_data.return_value = mock_df
    
    result = _run_get_data({"station": "KNYC", "start_date": "2023-01-01", "end_date": "2023-01-01"})
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 1
    assert result["station"].iloc[0] == "KNYC"

def test_execute_tool_call_get_data(mocker):
    mock_get_data = mocker.patch("xmacis2py.get_single_station_acis_data")
    mock_df = pd.DataFrame({"station": ["KNYC"], "valid_date": ["2023-01-01"], "Maximum Temperature": [45]})
    mock_get_data.return_value = mock_df
    
    result = execute_tool_call("get_data", {"station": "KNYC"})
    assert "--- Data Retrieved ---" in result
    assert "KNYC" in result

def test_execute_tool_call_analysis(mocker):
    # Mock data fetch
    mock_get_data = mocker.patch("xmacis2py.get_single_station_acis_data")
    mock_df = pd.DataFrame({"station": ["KNYC"], "valid_date": ["2023-01-01"], "Maximum Temperature": [45]})
    mock_get_data.return_value = mock_df
    
    # Mock analysis
    mock_analysis = mocker.patch("xmacis2py.analysis.period_mean")
    mock_analysis.return_value = 45.0
    
    result = execute_tool_call("period_mean", {
        "station": "KNYC", 
        "variable": "tmax", 
        "start_date": "2023-01-01", 
        "end_date": "2023-01-01"
    })
    assert "--- period_mean Result ---" in result
    assert "45.0" in result

def test_execute_tool_call_missing_args():
    result = execute_tool_call("period_mean", {"station": "KNYC"})
    assert "ERROR: Missing required argument(s):" in result

def test_run_get_data_all_stations(mocker):
    mock_get_multi = mocker.patch("xmacis2py.get_multi_station_acis_data")
    mock_df = pd.DataFrame({"station": ["KNYC", "KLAX"], "valid_date": ["2023-01-01", "2023-01-01"], "Maximum Temperature": [45, 60]})
    mock_get_multi.return_value = mock_df

    result = _run_get_data({"station": "ALL", "start_date": "2023-01-01", "end_date": "2023-01-01"})

    mock_get_multi.assert_called_once_with(stations="ALL", start_date="2023-01-01", end_date="2023-01-01")
    assert isinstance(result, pd.DataFrame)
    assert len(result) == 2
    assert result["station"].iloc[0] == "KNYC"
