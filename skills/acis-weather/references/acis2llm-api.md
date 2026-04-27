# acis2llm — API Reference

The `acis2llm` package adds three layers on top of `xmacis2py`:

1. **Station discovery** — resolve `"10001"` (ZIP) / `"KNYC"` (station ID) / a full street address → station ID. Plain `"City, State"` strings do **not** resolve — convert to a ZIP first.
2. **Multi-station fetch** — comma-aggregate and `+`-backfill helpers
3. **Composite analyses** — seasonal/monthly aggregates and threshold frequencies, computed across many years with one call

Everything is a normal Python function returning DataFrames or dicts. There is no MCP server, no JSON tool layer.

```python
import xmacis2py
import acis2llm
```

---

## Station discovery — `acis2llm.geocoding`

### `find_best_station(location)`

```python
acis2llm.find_best_station(location: str) -> dict
```

Resolve a free-form location to the ACIS station with the longest, most-recent record nearby. Tries, in order:

1. Direct ACIS StnMeta lookup if `location` looks like a station ID (4-letter ICAO or 5-digit COOP).
2. Geocode via Zippopotam (5-digit ZIP) or US Census (full street address). Plain `"City, State"` strings will **not** resolve — convert to a ZIP first.
3. ACIS bbox search (~0.5° around the geocoded point), scored by:
   - Active record (latest year ≥ current − 1): **+1000**
   - State match with geocoded address: **+2000**
   - Earlier start year: **−1 per year after 1800**
   - Distance: **−200 per degree**

   The single highest-scoring station wins. With these weights, distance can outweigh record length when stations are tightly clustered: e.g. for ZIP 85001 (Phoenix), KLUF (Luke AFB, dist 0.16°, 1951–) beats KPHX (Sky Harbor, dist 0.44°, 1933–) by ~40 points despite KPHX having an 18-year-longer record.
4. Backfill: if a co-located station within ~10mi has an earlier start, the returned `station_id` is a `+`-joined spec like `"KLUF+025282"`. Pass that string straight to `acis2llm.fetch_stations` to get the combined record.

**Returns** — dict with:

```python
{
    "station_id":          str,        # may be plus-joined for backfill
    "name":                str,
    "coordinates":         [lon, lat],
    "data_start":          int,        # year
    "data_end":            int,
    "record_length_years": int,
    "all_ids":             list[str],
    "geocoded_location":   str,
    "nearby_stations":     list[str],  # up to 5 alternates
}
```

On failure, returns `{"error": "..."}`.

### `geocode_census(location)`

Lower-level geocoder — returns `{"lat", "lon", "display_name"}` or `None`. Tries Zippopotam first for 5-digit ZIPs, falls back to US Census Geocoder (street-address only). Plain `"City, State"` queries return `None` because the Census `onelineaddress` endpoint requires a street-level address.

### `is_zip_code(location) -> bool`

True for `"12345"` or `"12345-6789"`.

---

## Multi-station fetch — `acis2llm.multi_station`

### `fetch_stations(spec, **kwargs)`

```python
acis2llm.fetch_stations(spec: str, **kwargs) -> pandas.DataFrame
```

One DataFrame for one or many stations. `spec` is a station-spec string:

| Spec form | Behavior |
|---|---|
| `"KNYC"` | Single station — calls `xmacis2py.get_single_station_acis_data`. |
| `"KNYC,KJFK,KLGA"` | **Aggregate**: fetch each in parallel, concat with a `station` column. |
| `"KNYC+OLDER"` | **Backfill**: fetch each, then fill missing dates from later stations in priority order. The returned DataFrame has `station=spec`. |
| `"ALL"` | Region-wide — calls `xmacis2py.get_multi_station_acis_data(stations="ALL", ...)`. |

`**kwargs` are forwarded to the underlying xmACIS2Py call. Common ones:
`start_date`, `end_date`, `from_when`, `time_delta`, `to_csv`, `return_pandas_df`.

Returns an empty DataFrame on total failure (network down, no rows). Per-station errors during aggregation are silently skipped — surviving stations are still returned.

---

## Composites — `acis2llm.composites`

Each composite fetches its own data window and returns a structured dict:

```python
{
    "table":   list[dict],   # per-year rows
    "summary": str,          # one-line headline
}
```

`frequency_of_occurrence` and `monthly_threshold_counts` additionally include `count`, `total_years`, and `percentage` fields.

All composites accept short variable codes (`"tmax"`, `"prcp"`, `"snow"`, …) and translate them to the xmACIS2Py column names via `acis2llm.VARIABLE_COLUMN_MAP`.

### `seasonal_summary(station, variable, season, ...)`

```python
acis2llm.seasonal_summary(
    station,                    # str — accepts the same specs as fetch_stations
    variable,                   # short code or full xmACIS2Py column name
    season,                     # 'winter' | 'spring' | 'summer' | 'fall' | 'autumn'
    start_year=None,            # default: station's earliest year on record
    end_year=None,              # default: current year
    aggregation='sum',          # 'sum' | 'mean' | 'max' | 'min'
)
```

Aggregates `variable` over a meteorological season, year by year. Winter is Dec–Feb and is labeled by the *ending* year (Dec 2023 → Winter 2024). Years with fewer than ~20 days/month are dropped as partial seasons.

### `monthly_totals_by_year(station, variable, month, ...)`

```python
acis2llm.monthly_totals_by_year(
    station, variable, month,   # month: int 1-12, name, or abbreviation
    start_year=None, end_year=None,
    aggregation='sum',          # 'sum' | 'mean' | 'max' | 'min'
)
```

Aggregates `variable` for one calendar month across many years. e.g. April snowfall in NYC every year on record.

### `frequency_of_occurrence(station, variable, threshold, comparison, ...)`

```python
acis2llm.frequency_of_occurrence(
    station, variable, threshold,
    comparison,                 # 'above'/'>', 'at_or_above'/'>=', 'below'/'<', 'at_or_below'/'<='
    month=None,                 # provide month OR season, not both
    season=None,
    start_year=None, end_year=None,
)
```

How often (across years) the daily value meets a threshold during a given month or season. Years with > 10% missing data in the target window are dropped.

Returned dict adds `count` (years where it happened at all), `total_years`, and `percentage`.

### `monthly_threshold_counts(...)`

Same signature and return shape as `frequency_of_occurrence` — a thin alias emphasizing the per-year `days_met` counts in `table`. **Despite the name it does not iterate every month**: you must still pass exactly one of `month` or `season`. To compare counts across all twelve months, call this once per month and assemble the results yourself.

---

## Constants

### `acis2llm.VARIABLE_COLUMN_MAP`

```python
{
    "tmax":       "Maximum Temperature",
    "tmin":       "Minimum Temperature",
    "tavg":       "Average Temperature",
    "prcp":       "Precipitation",
    "snow":       "Snowfall",
    "snow_depth": "Snow Depth",
    "awdb":       "Average Daily Water Balance",
    "hdd":        "Heating Degree Days",
    "cdd":        "Cooling Degree Days",
    "gdd":        "Growing Degree Days",
    "tdpa":       "Average Temperature Departure",
}
```

All composite functions accept either short codes or full column names. The xmACIS2Py analysis functions only accept full column names.
