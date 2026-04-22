# xmacis2py Reference

Quick reference for xmacis2py tools used by acis2llm.

## Data Retrieval

### `get_data`

Download weather data from ACIS.

```python
from xmacis2py import get_data

df = get_data(
    station="KRAL",          # 4-letter station code (required)
    start_date="2023-01-01", # Start date (optional)
    end_date="2023-12-31",   # End date (optional)
    from_when="last_year",   # Relative date (alternative to start/end)
    time_delta="daily",      # Aggregation: daily, monthly, seasonal, annual
    to_csv=False,            # Return CSV string instead of DataFrame
    return_pandas_df=True,   # Return pandas DataFrame
)
```

**Returns:** pandas DataFrame with columns `station`, `valid_date`, and variable columns.

## Period Statistics

All period functions require: `station`, `variable`, `start_date`, `end_date`.

```python
from xmacis2py import (
    period_mean,
    period_median,
    period_mode,
    period_percentile,
    period_standard_deviation,
    period_variance,
    period_skewness,
    period_kurtosis,
    period_maximum,
    period_minimum,
    period_sum,
)

# Example
mean_val = period_mean(
    station="KRAL",
    variable="tavg",
    start_date="2023-01-01",
    end_date="2023-12-31",
)
# Returns: 52.3 (degrees Fahrenheit)

# Percentile example
p90 = period_percentile(
    station="KRAL",
    variable="tmax",
    start_date="2023-01-01",
    end_date="2023-12-31",
    percentile=90,
)
# Returns: 91.0 (degrees Fahrenheit)
```

**Returns:** scalar value (int or float) per station.

## Period Extremes

```python
from xmacis2py import period_maximum, period_minimum, period_sum
```

## Rankings

```python
from xmacis2py import period_rankings

rankings = period_rankings(
    station="KRAL",
    variable="tmax",
    start_date="2023-01-01",
    end_date="2023-12-31",
)
# Returns: DataFrame with date and rank columns
```

## Running Calculations

```python
from xmacis2py import running_sum, running_mean

rsum = running_sum(
    station="KRAL",
    variable="prcp",
    start_date="2023-01-01",
    end_date="2023-12-31",
)
# Returns: DataFrame with cumulative precipitation

rmean = running_mean(
    station="KRAL",
    variable="tavg",
    start_date="2023-01-01",
    end_date="2023-12-31",
)
# Returns: DataFrame with running average temperature
```

## Detrending

```python
from xmacis2py import detrend_data

detrended = detrend_data(
    station="KRAL",
    variable="tavg",
    start_date="2000-01-01",
    end_date="2023-12-31",
)
# Returns: DataFrame with detrended values
```

## Threshold Counts

```python
from xmacis2py import (
    number_of_days_at_or_below,
    number_of_days_at_or_above,
    number_of_days_below,
    number_of_days_above,
    number_of_days_at,
)

# Count days with max temp >= 90°F
hot_days = number_of_days_at_or_above(
    station="KRAL",
    variable="tmax",
    start_date="2023-06-01",
    end_date="2023-08-31",
    value=90,
)
# Returns: 15

# Count days with exactly 0°F
freezing_days = number_of_days_at(
    station="KRAL",
    variable="tmin",
    start_date="2023-01-01",
    end_date="2023-02-28",
    value=0,
)
# Returns: 3
```

## Missing Data

```python
from xmacis2py import number_of_missing_days

missing = number_of_missing_days(
    station="KRAL",
    variable="tavg",
    start_date="2023-01-01",
    end_date="2023-12-31",
)
# Returns: 5 (days with no data)
```

## Common Station Codes

| Code | Location |
|------|----------|
| KRAL | Raleigh, NC |
| KLAX | Los Angeles, CA |
| KORD | Chicago, IL |
| KJFK | New York, NY |
| KDEN | Denver, CO |
| KATL | Atlanta, GA |
| KMIA | Miami, FL |
| KSEA | Seattle, WA |
| KBOS | Boston, MA |
| KDFW | Dallas, TX |

## Common Variables

| Variable | Description | Units |
|----------|-------------|-------|
| `tmax` | Maximum temperature | °F |
| `tmin` | Minimum temperature | °F |
| `tavg` | Average temperature | °F |
| `prcp` | Precipitation | inches |
| `snow` | Snowfall | inches |
| `awdb` | Average daily water balance | inches |
| `hdd` | Heating degree days | °F-days |
| `cdd` | Cooling degree days | °F-days |
| `gdd` | Growing degree days | °F-days |
