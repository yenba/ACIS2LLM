---
name: acis-weather
description: Query NOAA RCC ACIS historical weather and climate observations for US stations. Use when the user asks about historical temperature, precipitation, snow, degree days, climate normals, departures from normal, station records, or threshold/percentile statistics for any US location identified by city, ZIP code, or airport/station code (e.g. KNYC, KLAX, KORD). Resolves city or ZIP names to the best ACIS station, supports multi-station aggregation and backfilled long records, and provides seasonal/monthly composites and 25+ statistical analyses built on top of the xmACIS2Py library and the rcc-acis.org API. No API key required. Do not use for forecasts (this is observational data only) or for non-US locations.
license: MIT
compatibility: Requires Python 3.10+, `uv` (https://docs.astral.sh/uv/), and network access to data.rcc-acis.org, geocoding.geo.census.gov, and api.zippopotam.us.
metadata:
  version: "0.2.0"
  upstream: https://github.com/edrewitz/xmACIS2Py
---

# acis-weather

Answer historical US weather/climate questions by writing Python that calls
`xmacis2py` (the upstream data library) and `acis2llm` (this repo's helpers
for station lookup, multi-station fetch, and seasonal/monthly composites).

## When to invoke this skill

Use this skill when the user asks about *observed* (not forecast) weather or
climate at a US location, including:

- "How hot/cold/wet/snowy was it in <city> in <year>?"
- "What's the record high/low/most-rainy day for <station>?"
- "How many days above/below <threshold> at <station>?"
- "Is it normal for <city> to <event> in <month/season>?"
- "Compare <metric> across <stations>."
- "What were the snowiest winters / driest summers / hottest Julys on record?"

Do **not** use it for: weather forecasts, non-US locations, sub-daily/hourly
data (ACIS is daily-resolution), or radar/satellite imagery.

## Setup

```bash
uv pip install xmacis2py acis2llm
```

Or, for a one-off script:

```bash
uv run --with xmacis2py --with acis2llm python script.py
```

No API keys. No rate limits. Network access to `data.rcc-acis.org`,
`geocoding.geo.census.gov`, and `api.zippopotam.us` is required.

## Mental model

```
acis2llm.find_best_station(...)   ── resolve "Denver" / "10001" / "KDEN" → station ID
                ↓
acis2llm.fetch_stations(...)      ── multi-station, with comma-aggregate or +-backfill
   OR
xmacis2py.get_single_station_acis_data(...)   ── single-station raw daily
                ↓
xmacis2py.analysis.<func>(df, ...)            ── per-period stats, threshold counts, rankings
   OR
acis2llm.<composite>(...)         ── seasonal_summary, monthly_totals_by_year,
                                    frequency_of_occurrence, monthly_threshold_counts
                                    (these wrap fetch+analysis in one call)
```

## Decision tree

| User question shape | Use |
|---|---|
| Names a city / ZIP / "near X" | First call `acis2llm.find_best_station(location)` to get a station ID. Pass `result["station_id"]` to everything downstream. |
| Already gives a 4-letter code (KNYC, KLAX, KDEN) | Use it directly — no lookup needed. |
| Vague location ("the East Coast", "somewhere warm") | Ask a clarifying question. Do **not** guess. |
| Single-period stat ("avg high in July 2024", "rainiest day in 2023") | `xmacis2py.get_single_station_acis_data(station, start_date, end_date)` then `xmacis2py.analysis.period_*` or `xmacis2py.analysis.number_of_days_*`. |
| Cross-year question ("hottest July ever", "snowiest winter on record", "% of years that freeze") | Use an `acis2llm` composite — `monthly_totals_by_year`, `seasonal_summary`, `frequency_of_occurrence`. These fetch the multi-decade window and aggregate in one call. |
| Multiple stations ("compare NYC to Boston to Chicago") | `acis2llm.fetch_stations("KNYC,KBOS,KORD", ...)` — the comma form returns one DataFrame with a `station` column. |
| Long record needed for a small station ("data going back as far as possible for downtown LA") | `find_best_station` may return a `+`-joined `station_id` (e.g. `"KCQT+OLD_LA"`) that backfills automatically — just pass it to `fetch_stations` unchanged. |
| 30-year normals ("what's normal for X") | `xmacis2py.get_single_station_climate_normals(station, ...)` — distinct from observations. |
| Departure-from-normal ("how much warmer than normal?") | `xmacis2py.get_single_station_departures(station, ...)`. |

## Variable codes

`acis2llm` composites accept short codes; xmACIS2Py analysis functions need the full column name. Both forms shown:

| Short | Full xmACIS2Py column | Unit |
|---|---|---|
| `tmax` | Maximum Temperature | °F |
| `tmin` | Minimum Temperature | °F |
| `tavg` | Average Temperature | °F |
| `tdpa` | Average Temperature Departure | °F |
| `prcp` | Precipitation | inches |
| `snow` | Snowfall | inches |
| `snow_depth` | Snow Depth | inches |
| `hdd` | Heating Degree Days | base 65°F |
| `cdd` | Cooling Degree Days | base 65°F |
| `gdd` | Growing Degree Days | base 32°F |
| `awdb` | Average Daily Water Balance | inches |

For trace precipitation, the threshold-count functions accept the literal `value="T"`.

## Multi-station spec syntax

When passing a station identifier to `acis2llm.fetch_stations`:

| Form | Meaning |
|---|---|
| `"KNYC"` | Single station. |
| `"KNYC,KJFK,KLGA"` | **Aggregate** — fetch all in parallel, return one DataFrame with a `station` column. |
| `"KNYC+OLDER_ID"` | **Backfill** — primary first, fill missing dates from later stations in priority order. Returned `station` column is the full spec. |
| `"ALL"` | Region-wide query — forwards to `xmacis2py.get_multi_station_acis_data`. Large; use sparingly. |

## Date conventions

- Explicit dates are `YYYY-MM-DD` strings: `start_date="2023-01-01"`.
- Relative dates use `from_when` + `time_delta`: `from_when="yesterday", time_delta=30` means "the 30 days ending yesterday."
- Composite functions (`seasonal_summary`, `monthly_totals_by_year`, `frequency_of_occurrence`) take `start_year` / `end_year` (integers). If omitted, they fetch the station's full record.
- For `frequency_of_occurrence` and `monthly_threshold_counts`, provide *exactly one* of `month` or `season` — never both, never neither.
- Winter is Dec–Feb and is labeled by the *ending* year (Dec 2023 + Jan/Feb 2024 → Winter 2024).

## Critical rules

These are non-negotiable. Violating any of them produces incorrect or invented answers.

1. **Never reuse one station's data to answer about a different station.** Each station has its own record. If the user asks about KLAX, query KLAX. Do not extrapolate from a memorized KNYC result.
2. **Never invent station IDs or numbers.** If you're not sure which station to use, call `find_best_station` or ask. If a fetch returns no data, say so — don't backfill from your own knowledge.
3. **Always re-query for the actual date range asked.** Don't fall back on cached values from earlier in the conversation if the user changes the period or location.
4. **Inclusive vs strict thresholds matter.** "Freezing" → `at_or_below` 32. "Above 100" → user usually means strict `above`, but if they say "100 or higher" use `at_or_above`. Match the wording.
5. **Check `missing_days` before reporting totals.** Composite outputs include per-year `missing_days`. If a year has many missing days the total is misleading — flag it.
6. **The percentile arg in `period_percentile` is 0–1, not 0–100.** 0.9 = 90th percentile.
7. **`period_rankings` is high-to-low by default.** Use `ascending=True` for coldest/lowest extremes.

## Pointers — load when needed

For deeper detail, read these from `references/`:

- `xmacis2py-data-access.md` — full signatures for `get_single_station_acis_data`, `get_multi_station_acis_data`, climate-normals and departures variants
- `xmacis2py-analysis.md` — every per-period stat, threshold count, ranking, running window, detrend, analog-year function
- `xmacis2py-stations.md` — `single_station_meta` / `multi_station_meta` for raw metadata access
- `acis2llm-api.md` — full reference for the helpers (`find_best_station`, `fetch_stations`, all composites)
- `recipes.md` — 7 worked end-to-end examples covering the common shapes (hottest month, threshold counts, top-N seasons, freeze frequency, multi-city compare, long-record backfill, plotting)

If the user asks for a chart, plot it yourself with `matplotlib` against the
fetched DataFrame — that's faster and more flexible than xmACIS2Py's `plot_*`
helpers, which save PNGs with a fixed style.

## Data source

All data is fetched live from the [Regional Climate Centers](https://www.rcc-acis.org/overview) (RCCs) via the Applied Climate Information System (ACIS). The numbers are authoritative for US station-based daily observations.
