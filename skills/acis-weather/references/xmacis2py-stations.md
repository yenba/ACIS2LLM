# xmACIS2Py — Station Metadata

> Vendored from [edrewitz/xmACIS2Py](https://github.com/edrewitz/xmACIS2Py) (MIT
> license, © Eric J. Drewitz). Sources merged: `single_station_meta.md`,
> `multi_station_meta.md`.

These functions return the metadata record (name, lat/lon, valid date ranges,
ICAO/COOP IDs, etc.) for ACIS stations. For *finding* the right station from a
city or ZIP, use `acis2llm.find_best_station` instead — it wraps these calls
plus geocoding and proximity scoring.

## single_station_meta()

```python
xmacis2py.single_station_meta(
    station_id,
    proxies=None,
    to_csv=False,
    path="XMACIS META",
    return_pandas_df=True,
)
```

**Required**

- `station_id` (str) — 4-letter ICAO station ID.

**Optional**

- `proxies` (dict or None) — `{"http": "...", "https": "..."}`.
- `to_csv` (bool) — also save a CSV.
- `path` (str) — output directory.
- `return_pandas_df` (bool) — return DataFrame.

**Returns** — single-row `pandas.DataFrame` of metadata for the station.

## multi_station_meta()

```python
xmacis2py.multi_station_meta(
    station_ids,         # list[str]
    proxies=None,
    to_csv=False,
    path="XMACIS META",
    return_pandas_df=True,
)
```

Same options as the single-station variant. Returns one DataFrame containing
metadata rows for all requested stations.
