---
name: acis-weather
description: Query NOAA RCC ACIS historical weather and climate observations for US stations. Use when the user asks about historical temperature, precipitation, snow, degree days, climate normals, departures from normal, station records, or threshold/percentile statistics for any US location identified by city, ZIP code, or airport/station code (e.g. KNYC, KLAX, KORD). Resolves city or ZIP names to the best ACIS station, supports multi-station aggregation and backfilled long records, and provides seasonal/monthly composites and 25+ statistical analyses built on top of the xmACIS2Py library and the rcc-acis.org API. No API key required. Do not use for forecasts (this is observational data only) or for non-US locations.
license: MIT
compatibility: Requires Python 3.10+, `uv` (https://docs.astral.sh/uv/), and network access to data.rcc-acis.org, geocoding.geo.census.gov, and api.zippopotam.us.
metadata:
  version: "0.3.1"
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
acis2llm.find_best_station(location, prioritize_distance=False) ── resolve "10001" (ZIP) / "KDEN" (station ID) → station ID
                                    (city-state strings like "Denver, CO" do NOT resolve;
                                     use a ZIP, station ID, or full street address)
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

## API gotchas (read before writing code)

These are the failure modes real agents have hit. Every line below is a pattern that *looks* reasonable and *will not work* — verified against the actual installed library.

| Wrong | Right |
|---|---|
| `seasonal_summary(station="KLEX", variable="snow", season="winter")` or `monthly_totals_by_year(station="KNYC", variable="prcp", month="july")` | `seasonal_summary(station="KLEX", parameter="snow", season="winter")` or `monthly_totals_by_year(station="KNYC", parameter="prcp", month="july")`. The keyword is **`parameter=`**, not `variable=`. This is the single most common error — agents trained on xmACIS2Py analysis functions (which use `parameter=`) or generic patterns tend to emit `variable=`. The keyword is `parameter` in ALL `acis2llm` composites AND in `xmacis2py.analysis.*` functions. |
| `import xmacis2py.analysis` | `import xmacis2py` then `xmacis2py.analysis.period_mean(...)`, **or** `from xmacis2py import analysis`. The `analysis` name is an attribute alias, not a real submodule — `import xmacis2py.analysis` raises `ModuleNotFoundError`. |
| `get_single_station_acis_data(station, variables="tmax")` or `get_single_station_acis_data(station, data_type="daily")` | `get_single_station_acis_data(station, start_date, end_date)`. There is **no `variables=` / `variable=` / `data_type=` parameter**. The function always returns all columns; filter the DataFrame yourself: `df[["Date", "Maximum Temperature"]]`. |
| `df["tmax"]`, `df["tmin"]`, `df["prcp"]` | `df["Maximum Temperature"]`, `df["Minimum Temperature"]`, `df["Precipitation"]`. Returned columns are the **full English** names from the table below. Short codes (`tmax`, `tmin`, …) are only accepted by `acis2llm` composites, never by xmACIS2Py functions or the returned DataFrame. |
| `xmacis2py.analysis.period_mean(df, variable="tmax")` | `xmacis2py.analysis.period_mean(df, parameter="Maximum Temperature")`. Both namespaces use the **`parameter=`** keyword (as of acis2llm 0.3.0). For `xmacis2py.analysis.*` the value must be the **full English column name** (`"Maximum Temperature"`); the short codes (`"tmax"`, `"snow"`) only work on `acis2llm` composites. |
| `seasonal_summary(station_ids="KLEX", season="JJA")` | `seasonal_summary(station="KLEX", parameter="tavg", season="summer")`. Param is `station` (singular). Season values are full English words: `"winter"`, `"spring"`, `"summer"`, `"fall"`/`"autumn"` — meteorological codes (`"DJF"`, `"JJA"`) are **not** accepted. |
| `xmacis2py.analysis.number_of_days_above(df, "Maximum Temperature", 90)` | `xmacis2py.analysis.number_of_days_above_value(df, "Maximum Temperature", 90)`. The actual names all end in `_value`: `number_of_days_above_value`, `number_of_days_at_or_above_value`, `number_of_days_below_value`, `number_of_days_at_or_below_value`, `number_of_days_at_value`. There is no shorter `_above` / `_below` form. |
| `get_single_station_climate_normals(station, start_year=1991, end_year=2020)` | `get_single_station_climate_normals(station, interval="daily", start_date="1991-01-01", end_date="2020-12-31")`. Normals/departures use **date strings**, not year integers, and have an `interval` arg (`"daily"`/`"monthly"`/`"yearly"`). Only the `acis2llm` composites take `start_year`/`end_year`. |
| `seasonal_summary(...)` returns a DataFrame; do `.loc[...]` / `.idxmax()` | Composites return a **`dict`** — `{"table": [...], "summary": str}`. Convert with `pd.DataFrame(result["table"])` before DataFrame ops. See "Return shapes at a glance" below. |
| Counting zero-snowfall years with `(annual_snow == 0)` | Use `(annual_snow <= 0.01)`. ACIS reports trace amounts as `0.0` or near-zero values, so strict `== 0` undercounts genuinely snowless years. (For the threshold-count functions, pass the literal `value="T"` to count trace-or-above precip days.) |
| `df[df['Month'] == 6 & df['Day'] == 9]` | `df[(df['Month'] == 6) & (df['Day'] == 9)]`. Always wrap each condition in parentheses when using `&`/`|` in DataFrame filters — `&` binds tighter than `==` in Python, so without parens the expression evaluates `6 & df['Day']` first, raising `ValueError: The truth value of a Series is ambiguous`. |
| `get_single_station_climate_normals(station, interval="monthly")` returned fewer than 12 months | Pass explicit `start_date`/`end_date` covering at least one full year: `start_date="2020-01-01", end_date="2020-12-31"`. The default `end_date` is yesterday and may clip results if `start_date` is not also set to span a full year. For custom climatologies (e.g. a 50-year window) or calendar-date normals, use `xmacis2py.analysis.calculate_daily_normals(station, df=df)` instead — it computes normals from a DataFrame without upstream smoothing. |
| `fetch_stations(stations="KNYC,KBOS")` or `fetch_stations(station_list=["KNYC"])` | `fetch_stations("KNYC,KBOS", start_date="2024-01-01", end_date="2024-01-31")`. The first argument is a positional **`spec`** string — not a keyword argument named `stations` or `station_list`. Extra kwargs (`start_date`, `end_date`) are forwarded to the underlying xmACIS2Py call. |
| `normals_df["Average Temperature Normal"]` or `normals_df["Max Temperature Normal"]` | `normals_df["Average Temperature"]`, `normals_df["Max Temperature"]`, `normals_df["Min Temperature"]`, `normals_df["Precipitation"]`. The `get_single_station_climate_normals()` DataFrame uses the **same full English column names** as observation DataFrames — there is no " Normal" suffix. |

If a call fails with `TypeError: unexpected keyword argument` or `KeyError`, **don't guess** — check this table or run `inspect.signature(fn)`.

## Decision tree

| User question shape | Use |
|---|---|
| Names a ZIP / street address / "near X" | Call `acis2llm.find_best_station(location)` to get a station ID. Pass `result["station_id"]` to everything downstream. **City-state strings like "Denver, CO" do NOT resolve** — convert to a ZIP first, or ask the user for a ZIP/airport code. |
| Already gives a 4-letter code (KNYC, KLAX, KDEN) | Use it directly — no lookup needed. |
| Vague location ("the East Coast", "somewhere warm") | Ask a clarifying question. Do **not** guess. |
| Single-period stat ("avg high in July 2024", "rainiest day in 2023") | `xmacis2py.get_single_station_acis_data(station, start_date, end_date)` then `xmacis2py.analysis.period_*` (e.g. `period_mean`, `period_sum`, `period_percentile`) or `xmacis2py.analysis.number_of_days_{above,at_or_above,below,at_or_below,at}_value` (note the trailing `_value`). |
| Cross-year question ("hottest July ever", "snowiest winter on record", "% of years that freeze") | Use an `acis2llm` composite — `monthly_totals_by_year`, `seasonal_summary`, `frequency_of_occurrence`. These fetch the multi-decade window and aggregate in one call. |
| Multiple stations ("compare NYC to Boston to Chicago") | `acis2llm.fetch_stations("KNYC,KBOS,KORD", ...)` — the comma form returns one DataFrame with a `station` column. |
| Long record needed for a small station ("data going back as far as possible for downtown LA") | `find_best_station` may return a `+`-joined `station_id` (e.g. `"KCQT+OLD_LA"`) that backfills automatically — just pass it to `fetch_stations` unchanged. |
| 30-year normals ("what's normal for X") | `xmacis2py.get_single_station_climate_normals(station, ...)` — distinct from observations. |
| Departure-from-normal ("how much warmer than normal?") | `xmacis2py.get_single_station_departures(station, ...)`. |
| Custom or calendar-date normals ("average for June 9 across 30 years") | `xmacis2py.analysis.calculate_daily_normals(station, df=df)` — computes normals from a DataFrame without upstream smoothing, useful for custom windows. Pair with `calendar_date_records` for same-day-across-years ranking. |
| Degree days query ("heating degree days in January") | `xmacis2py.get_single_station_acis_data(station, start_date, end_date)` then `xmacis2py.analysis.period_sum(df, "Heating Degree Days")` or `period_mean(df, "Heating Degree Days")`. The column name is the full English name from the variable table. |
| "Wettest/hottest/snowiest X ever" (cross-year ranking) | Use `acis2llm.seasonal_summary()` or `monthly_totals_by_year()` to get per-year data, then sort `result["table"]` by `"value"` to find the extreme year. |
| "Compared to other X's, how Y has this one been?" (historical comparison) | Use `monthly_totals_by_year()` or `seasonal_summary()` for the ranking/percentile, **AND** `get_single_station_climate_normals()` for the official 30-year normal as a second anchor. Report both: the observed historical mean (from the composite) and the WMO-standard normal (from the normals endpoint). |
| Comparing local microclimates ("Lexington vs Nicholasville") | Pass `prioritize_distance=True` to `find_best_station` for the suburb. Otherwise, both towns might resolve to the same regional airport due to its long record length. If they still resolve to the same ID, check the `nearby_stations` list in the return dictionary and pick a local station ID manually. |

## Variable codes

Both `acis2llm` composites and `xmacis2py.analysis.*` use a `parameter=` keyword for "which variable". The **value** type differs:

- `acis2llm` composites accept either form — `parameter="tavg"` or `parameter="Average Temperature"`.
- `xmacis2py.analysis.*` accepts only the full English column name — `parameter="Average Temperature"`.

The "Full" column below is also **literally the column name in the DataFrame** returned by `get_single_station_acis_data` / `fetch_stations` — e.g. `df["Average Temperature"]`, not `df["tavg"]`.

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

## Return shapes at a glance

| Call | Returns |
|---|---|
| `xmacis2py.get_single_station_acis_data(...)` | `pandas.DataFrame` — columns are the **Full** names from the table above (e.g. `"Average Temperature"`, `"Maximum Temperature"`), plus a `"Date"` column. Not snake_case. |
| `xmacis2py.get_single_station_climate_normals(...)` / `get_single_station_departures(...)` | `pandas.DataFrame` (NOT a dict) — same Full column names as observations. The `acis2llm` dict shape only applies to the `acis2llm.*` composites. |
| `xmacis2py.single_station_meta(...)` / `multi_station_meta(...)` | `pandas.DataFrame` — metadata about the station (note `"Station Name"` column, not `"name"`). Distinct from `acis2llm.find_best_station`, which returns a **dict** (`result["station_id"]`, `result["name"]`, …). |
| `acis2llm.fetch_stations(...)` | `pandas.DataFrame` — same columns plus a `station` column. |
| `acis2llm.seasonal_summary(...)` / `monthly_totals_by_year(...)` | `dict` — `{"table": [{"year", "value", "missing_days"}, ...], "summary": str}` |
| `acis2llm.frequency_of_occurrence(...)` / `monthly_threshold_counts(...)` | `dict` — adds `count`, `total_years`, `percentage`. **Per-row keys**: `year` (int), `days_met` (int — *the count of days the threshold was met*), `mean_value` (float — average of the parameter that year), `extreme_value` (float — most extreme **observed value** that year, e.g. coldest temp; **not** a day count), `met_condition` (bool — was the threshold met at least once). To find the worst year, sort by `days_met`, not `extreme_value`. |
| `xmacis2py.analysis.<func>(df, "Full Column Name", ...)` | scalar or list — `period_*` and `number_of_days_*` return a single number (sum, mean, count, etc.). `period_rankings` returns a list. See `references/xmacis2py-analysis.md`. |

## Multi-station spec syntax

When passing a station identifier to `acis2llm.fetch_stations`:

| Form | Meaning |
|---|---|
| `"KNYC"` | Single station. |
| `"KNYC,KJFK,KLGA"` | **Aggregate** — fetch all in parallel, return one DataFrame with a `station` column. |
| `"KNYC+OLDER_ID"` | **Backfill** — primary first, fill missing dates from later stations in priority order. Returned `station` column is the full spec. |
| `"ALL"` | Region-wide query — forwards to `xmacis2py.get_multi_station_acis_data`. Large; use sparingly. |

**Backfill spec note:** The `+`-joined station ID returned by `find_best_station()` (e.g. `"KPDX+24274"`) is designed to be passed to `acis2llm.fetch_stations()`, NOT to `xmacis2py.get_single_station_acis_data()`. If you need to use `get_single_station_acis_data()`, use only the primary station ID (the part before the `+`). The backfill spec format is an `acis2llm` convention — upstream xmACIS2Py functions do not understand it.

## Date conventions

- Explicit dates are `YYYY-MM-DD` strings: `start_date="2023-01-01"`.
- Relative dates use `from_when` (a `YYYY-MM-DD` anchor or `datetime`) + `time_delta` (days back). The literal string `"yesterday"` is **not** accepted — pass an actual date. If you omit `from_when`, xmACIS2Py defaults the anchor to yesterday's date.
- `acis2llm` composite functions (`seasonal_summary`, `monthly_totals_by_year`, `frequency_of_occurrence`) take `start_year` / `end_year` (integers). If omitted, they fetch the station's full record.
- `xmacis2py.get_single_station_climate_normals` / `get_single_station_departures` take `start_date` / `end_date` (date strings) plus an `interval` arg, **not** year integers. See the gotchas table above.
- For `frequency_of_occurrence` and `monthly_threshold_counts`, provide *exactly one* of `month` or `season` — never both, never neither. (Despite the name, `monthly_threshold_counts` does not iterate every month; it's a thin alias for `frequency_of_occurrence` with a different framing of the result.)
- Threshold `comparison` accepts both long forms (`"above"`, `"at_or_above"`, `"below"`, `"at_or_below"`) and symbol forms (`">"`, `">="`, `"<"`, `"<="`). They're equivalent.
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
8. **ACIS data lag: current-day observations may be missing.** There is typically a 1-2 day reporting lag. If the current year/month shows `missing_days > 0`, the total is incomplete and will likely increase. Note this when comparing the current period to historical data — don't rank an incomplete month as final.
9. **Microclimate Comparisons:** When a user wants to compare two nearby locations, use `find_best_station(..., prioritize_distance=True)` to force strict proximity. If both locations still resolve to the same major airport, do not compare the airport to itself. Look at the `nearby_stations` list returned by `find_best_station` and pick the true local station ID.

## Pointers — load when needed

**Read `acis2llm-api.md` BEFORE writing code** that uses composites or `find_best_station` — don't wait until a call fails. It has the authoritative return shapes, scoring algorithm for station selection, and `VARIABLE_COLUMN_MAP` constant. The other references are for deep dives on specific functions.

For deeper detail, read these from `references/`:

- `acis2llm-api.md` — full reference for `find_best_station` (including scoring algorithm), `fetch_stations`, all composites (return shapes, extra fields), and `VARIABLE_COLUMN_MAP` constant
- `xmacis2py-data-access.md` — full signatures for `get_single_station_acis_data`, `get_multi_station_acis_data`, climate-normals and departures variants
- `xmacis2py-analysis.md` — every per-period stat, threshold count, ranking, running window, detrend, analog-year function
- `xmacis2py-stations.md` — `single_station_meta` / `multi_station_meta` for raw metadata access
- `recipes.md` — 7 worked end-to-end examples covering the common shapes (hottest month, threshold counts, top-N seasons, freeze frequency, multi-city compare, long-record backfill, plotting)

If the user asks for a chart, plot it yourself with `matplotlib` against the
fetched DataFrame — that's faster and more flexible than xmACIS2Py's `plot_*`
helpers, which save PNGs with a fixed style.

## Data source

All data is fetched live from the [Regional Climate Centers](https://www.rcc-acis.org/overview) (RCCs) via the Applied Climate Information System (ACIS). The numbers are authoritative for US station-based daily observations.
