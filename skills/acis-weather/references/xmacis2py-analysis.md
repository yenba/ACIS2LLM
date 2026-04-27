# xmACIS2Py — Analysis Tools

> Vendored from [edrewitz/xmACIS2Py](https://github.com/edrewitz/xmACIS2Py) (MIT
> license, © Eric J. Drewitz). Source:
> `Documentation/xmACIS2.0/analysis_tools.md`. Lightly reformatted and
> deduplicated (the upstream file repeats parameter blocks per function).

All analysis functions live under `xmacis2py.analysis` and operate on a
DataFrame returned by `get_single_station_acis_data` (or any equivalent —
including DataFrames built from `acis2llm.fetch_stations`). They take the
DataFrame plus a `parameter` string naming the column.

## Valid `parameter` values

```
'Maximum Temperature'
'Minimum Temperature'
'Average Temperature'
'Average Temperature Departure'
'Heating Degree Days'
'Cooling Degree Days'
'Growing Degree Days'
'Precipitation'
'Snowfall'
'Snow Depth'
```

These are the long-form column names xmACIS2Py emits. The `acis2llm` package
also exports `VARIABLE_COLUMN_MAP` mapping short codes (`tmax`, `tmin`, `prcp`,
…) to these strings — see `acis2llm-api.md`.

## Common rounding controls

Most period-statistic functions accept the same set of optional rounding args:

| Argument | Default | Notes |
|---|---|---|
| `round_value` (bool) | `False` | Set True to enable rounding. |
| `round_up` (bool) | `True` | If True round up, else round down. |
| `to_nearest` (int) | `0` | `0`=whole, `1`=tenth (0.1), `2`=hundredth (0.01). |
| `data_type` (str) | `'float'` | Use `'integer'` to coerce to int. |

These are documented once here and omitted from the per-function signatures below.

## Period statistics (scalar return)

Each takes `(df, parameter, **rounding_args)` and returns a single number.

- `period_mean(df, parameter)` — arithmetic mean.
- `period_median(df, parameter)` — median.
- `period_mode(df, parameter)` — most-frequent value.
- `period_maximum(df, parameter)` — max.
- `period_minimum(df, parameter)` — min.
- `period_sum(df, parameter)` — sum (e.g. total precip).
- `period_standard_deviation(df, parameter)` — stddev.
- `period_variance(df, parameter)` — variance.
- `period_skewness(df, parameter)` — distribution skewness.
- `period_kurtosis(df, parameter)` — distribution kurtosis.
- `period_percentile(df, parameter, percentile=0.25)` — *percentile is 0-1, not 0-100*. e.g. `0.9` for the 90th.

## Threshold day-counts (scalar return)

Each takes `(df, parameter, value)` and returns an integer count of days.

- `number_of_days_above_value(df, parameter, value)` — strictly `>`.
- `number_of_days_at_or_above_value(df, parameter, value)` — `>=`.
- `number_of_days_below_value(df, parameter, value)` — strictly `<`.
- `number_of_days_at_or_below_value(df, parameter, value)` — `<=`.
- `number_of_days_at_value(df, parameter, value)` — exact match.
- `number_of_missing_days(df, parameter)` — count of missing-data days.

For precipitation, pass `value='T'` to count trace-or-above days.

## Rankings & rolling windows

```python
period_rankings(
    df,
    parameter,
    ascending=False,        # default: high→low
    rank_subset=None,       # None | 'first' | 'last' | 'between'
    first=5, last=5, between=[],
    date_name='Date',
)
```

Returns a DataFrame ranked by `parameter`. Pass `rank_subset='first', first=5`
for top 5, `rank_subset='last', last=5` for bottom 5, or
`rank_subset='between', between=[5, 10]` for a custom slice.

```python
running_sum(df, parameter, interpolation_limit=3)
running_mean(df, parameter, interpolation_limit=3)
```

Cumulative sum / running mean. `interpolation_limit` caps the number of
consecutive missing days that get interpolated across.

```python
detrend_data(df, parameter, detrend_type='linear')
```

Returns a DataFrame with the trend removed. `'linear'` subtracts a least-squares
linear fit; `'constant'` subtracts the mean. Useful for isolating anomalies
from a long-term trend.

## Custom normals

```python
calculate_daily_normals(
    station,
    df=None, input_path=None,    # provide one
    start_date=None, end_date=None,
    to_csv=False,
    output_path="XMACIS2 DAILY NORMALS",
    return_pandas_df=True,
)
```

Like `get_single_station_climate_normals` but computed without the upstream
smoothing — useful for custom climatologies (e.g. a 50-year window). Pass
either an already-loaded `df` or an `input_path` to a CSV.

## Analog-year analysis

```python
filter_analog_years(
    station,
    analogs,                     # list[(year, month)]
    df=None, input_path=None,
    to_csv=False,
    output_path="XMACIS2 ANALOGS",
    return_pandas_df=True,
)
```

Given a list of `(year, month)` tuples, returns a DataFrame containing only
those analog periods. Example for winters 2006/2016/2026:

```python
[(2005, 12), (2006, 1), (2006, 2),
 (2015, 12), (2016, 1), (2016, 2),
 (2025, 12), (2026, 1), (2026, 2)]
```

```python
analog_weighted_mean(df, parameter, weights)
analog_weighted_percentile(df, parameter, weights, percentile)
```

Weighted-mean and weighted-percentile across the analog set. `weights` is an
array (float or int) the same length as the analog set.
