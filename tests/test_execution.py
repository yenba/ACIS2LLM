import pandas as pd
from execution import _run_get_data
import pytest

def test_threaded_station_data(mocker):
    # Mock _get_function to return a dummy get_data
    mock_func = mocker.patch("execution._get_function")
    
    def dummy_get_data(**kwargs):
        station = kwargs.get("station")
        if station == "KPHX":
            return pd.DataFrame({"station": ["KPHX", "KPHX"], "Date": ["1950-01-01", "1950-01-02"], "Maximum Temperature": [100, pd.NA]})
        elif station == "026486":
            return pd.DataFrame({"station": ["026486", "026486"], "Date": ["1950-01-01", "1950-01-02"], "Maximum Temperature": [pd.NA, 95]})
        return pd.DataFrame()

    mock_func.return_value = dummy_get_data
    
    df = _run_get_data({"station": "KPHX+026486"})
    
    # Should prioritize KPHX, backfill with 026486
    assert len(df) == 2
    assert df["Maximum Temperature"].iloc[0] == 100
    assert df["Maximum Temperature"].iloc[1] == 95
