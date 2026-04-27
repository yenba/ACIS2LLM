# xmACIS2Py — Data Access

> Vendored from [edrewitz/xmACIS2Py](https://github.com/edrewitz/xmACIS2Py) (MIT
> license, © Eric J. Drewitz). Source:
> `Documentation/xmACIS2.0/data_access.md`. Lightly reformatted.

The xmACIS2Py library exposes six primary data-fetch functions. Use these
directly from `xmacis2py` for raw daily observations, 30-year normals, or
departures-from-normal. For multi-station aggregation/backfill or for
city/ZIP lookups, prefer the helpers in `acis2llm` (see `acis2llm-api.md`).

All functions return `pandas.DataFrame` by default and support optional CSV
output and HTTP proxies.

## get_single_station_acis_data()

```python
xmacis2py.get_single_station_acis_data(
    station,
    start_date=None,
    end_date=None,
    from_when=_yesterday,
    time_delta=30,
    proxies=None,
    clear_recycle_bin=False,
    to_csv=False,
    path='default',
    filename='default',
    notifications='on',
    return_pandas_df=True,
)
```

Daily observations for a single station.

**Required**

- `station` (str) — 4-letter station ID (e.g. `"KRAL"` for Riverside Municipal Airport, CA).

**Optional**

- `start_date`, `end_date` (str `YYYY-MM-DD` or datetime) — explicit range.
- `from_when` (str/datetime, default = yesterday) — anchor date for relative ranges.
- `time_delta` (int, default `30`) — days back from `from_when`. Used when `start_date`/`end_date` are not provided.
- `proxies` (dict or None) — `{"http": "...", "https": "..."}`.
- `clear_recycle_bin` (bool) — if True, clears the system recycle bin per call.
- `to_csv` (bool) — also write a CSV alongside returning the DataFrame.
- `path`, `filename` (str) — CSV output location; `'default'` uses `XMACIS2 DATA/<station>`.
- `notifications` (str, `'on'`/`'off'`) — print save messages.
- `return_pandas_df` (bool) — return the DataFrame (set False to write CSV only).

**Returns** — `pandas.DataFrame` with columns including `Date`, `Maximum Temperature`, `Minimum Temperature`, `Average Temperature`, `Precipitation`, `Snowfall`, `Snow Depth`, `Heating Degree Days`, `Cooling Degree Days`, `Growing Degree Days`, `Average Temperature Departure`.

## get_multi_station_acis_data()

```python
xmacis2py.get_multi_station_acis_data(
    stations,            # list[str] OR the literal "ALL"
    start_date=None,
    end_date=None,
    from_when=_yesterday,
    time_delta=30,
    proxies=None,
    clear_recycle_bin=False,
    to_csv=False,
    path='default',
    filename='default',
    notifications='on',
    return_pandas_df=True,
)
```

Same parameters as single-station, but `stations` is a list of IDs. Returns a list of DataFrames (one per station).

For convenience-aggregating these into a single DataFrame, prefer
`acis2llm.fetch_stations("KNYC,KJFK,...")`.

## get_single_station_climate_normals() / get_multi_station_climate_normals()

```python
xmacis2py.get_single_station_climate_normals(
    station,
    interval='daily',     # 'daily' | 'monthly' | 'yearly'
    start_date=_default_start,
    end_date=_yesterday,
    to_csv=False,
    proxies=None,
    path="XMACIS2 NORMALS",
    notifications='on',
    return_pandas_df=True,
)
```

Returns the published 30-year climate normals for the station(s). The
multi-station variant takes a list of station IDs and returns a list of DataFrames.

Use this when the user asks "what's *normal* for date X" — distinct from
historical observations.

## get_single_station_departures() / get_multi_station_departures()

```python
xmacis2py.get_single_station_departures(
    station,
    interval='daily',
    start_date=_default_start,
    end_date=_yesterday,
    to_csv=False,
    proxies=None,
    path="XMACIS2 DEPARTURES",
    notifications='on',
    return_pandas_df=True,
)
```

Returns observed-minus-normal departures (signed deltas) for the station(s).
Use this for "how much warmer/colder/wetter than normal" questions. For raw
observations, use `get_*_acis_data` instead.
