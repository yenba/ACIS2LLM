# Changelog

## [0.2.4] - 2026-04-28

### Changed
- SKILL.md gotchas table grew two rows from a third field report (Crush + Qwen3.6 35B running 10 Lexington KY queries):
  - `acis2llm` composites take `variable=` with a **short code** (`"tavg"`, `"snow"`); `xmacis2py.analysis.*` takes `parameter=` with the **full English column name** (`"Average Temperature"`). Two namespaces, two keyword names — agents conflate them and get `TypeError: missing 1 required positional argument: 'variable'` or `unexpected keyword argument 'parameter'`.
  - `xmacis2py.analysis.number_of_days_above` does **not** exist; the actual names all end in `_value` (`number_of_days_above_value`, `number_of_days_at_or_above_value`, etc.). The decision tree's old `number_of_days_*` wildcard invited the truncation.
- "Return shapes at a glance" gained three rows: `get_single_station_climate_normals` / `get_single_station_departures` return `DataFrame` (not the `acis2llm`-style dict); `single_station_meta` / `multi_station_meta` return `DataFrame` with a `"Station Name"` column (distinct from `find_best_station`'s dict).
- The `frequency_of_occurrence` row in the same table now spells out every per-row key: `days_met` is the **count**, `extreme_value` is the most-extreme **observed value** (e.g. coldest temp), and `value` mirrors `extreme_value`. Agents have read `extreme_value=25.0` as "25 days" — clarified to "sort by `days_met`, not `extreme_value`".

## [0.2.3] - 2026-04-28

### Changed
- `xmacis2py` floor raised from `>=2.0` to `>=2.4`. Versions 2.0–2.3 ship a renamed/abridged top-level API (`get_data` instead of `get_single_station_acis_data`, no normals/departures functions) so `from acis2llm import seasonal_summary` raised `ImportError` against any of those installs. 2.4 restores the names this package and SKILL.md reference.
- SKILL.md: new "API gotchas" section listing seven wrong-vs-right call patterns observed in field reports — `import xmacis2py.analysis` failing (it's an attribute alias, not a real submodule), `variables=`/`variable=` not being a valid arg on `get_single_station_acis_data` (always returns all columns), `parameter=` being the keyword for `xmacis2py.analysis.*` (with full English column names as values), `seasonal_summary` taking `station=` not `station_ids=` and English-only season names (`"summer"`, not `"JJA"`), `get_single_station_climate_normals` taking date strings + `interval` rather than `start_year`/`end_year`, composites returning `dict` not DataFrame, and `<= 0.01` for trace zero-snowfall comparisons.
- "Date conventions" section now distinguishes `acis2llm` composite year-int args from `xmacis2py` normals/departures date-string args.
- `references/xmacis2py-analysis.md` now spells out the three import paths that work for `xmacis2py.analysis` and the one that doesn't.

## [0.2.2] - 2026-04-28

### Fixed
- SKILL.md frontmatter version had drifted to `0.2.0` while package was at `0.2.1`. Synced.

### Changed
- Composite return shapes are now spelled out in `seasonal_summary`, `monthly_totals_by_year`, and `frequency_of_occurrence` docstrings (`"Returns a dict (NOT a DataFrame)"` with the full key/value layout). Surfaced from real LLM friction: agents called these expecting a DataFrame and had to inspect to discover the dict shape.
- SKILL.md "Variable codes" section now states explicitly that the "Full xmACIS2Py column" names are the literal column names in the DataFrame returned by `get_single_station_acis_data` / `fetch_stations` (e.g. `df["Average Temperature"]`, not `df["tavg"]`).
- New "Return shapes at a glance" table in SKILL.md summarising what each call returns (DataFrame vs dict, with row schemas inline).

## [0.2.1] - 2026-04-27

### Fixed
- `find_best_station` doc/promise mismatch: README, SKILL.md, recipes, and api ref claimed `"City, State"` strings (e.g. `"Denver, CO"`) resolved, but the US Census `onelineaddress` endpoint requires a street-level address so they returned `None` and the function errored. Examples and waterfall docstring updated to reflect what actually resolves: 5-digit ZIPs, station IDs, and full street addresses.
- `from_when="yesterday"` was shown in README, SKILL.md, and a recipe as a usage example, but xmACIS2Py only accepts a `YYYY-mm-dd` anchor or `datetime`. Examples replaced with explicit-date computation.
- `monthly_threshold_counts` docstring + api ref now make it explicit that this function does **not** iterate every month — it's a thin alias for `frequency_of_occurrence` requiring exactly one of `month`/`season`.

### Added
- `frequency_of_occurrence` and `monthly_threshold_counts` accept symbol comparison forms (`">"`, `">="`, `"<"`, `"<="`) as aliases for the long-form names (`"above"`, `"at_or_above"`, `"below"`, `"at_or_below"`).
- Unknown-comparison and missing-month/season errors now list the valid values.
- API reference documents the `find_best_station` scoring trade-off (distance can outweigh record length, e.g. KLUF beats KPHX for ZIP 85001 by ~40 points despite KPHX having an 18-year-longer record).

## [0.2.0] - 2026-04-27

### Changed
- **Breaking**: Removed the MCP server entirely. `acis2llm` is now a pip-installable Python helper library; agents consume the `acis-weather` skill in `skills/acis-weather/`.
- Repo now ships an [agentskills.io](https://agentskills.io)-compliant skill with `SKILL.md` and 5 reference files (vendored xmACIS2Py docs + recipes + helper-API reference).
- Module split: `composite_tools.py` → `geocoding.py` + `composites.py`; multi-station fetch logic lifted into `multi_station.py`.
- All install/usage docs use `uv`.

### Removed
- `acis2llm.mcp_server`, `acis2llm.tools`, `acis2llm.execution`, `acis2llm.formatter` — no longer needed without the MCP transport.
- `clarify_location` pseudo-tool — replaced by skill guidance.
- `mcp` runtime dependency.

### Added
- `acis2llm.fetch_stations(spec, **kwargs)` as a public helper (was buried inside the execution dispatcher).
- `skills/acis-weather/` directory with `SKILL.md`, vendored xmACIS2Py reference docs, an `acis2llm` API reference, and 7 worked recipes.

## [0.1.0] - 2026-04-26

### Added
- Initial release of ACIS2LLM MCP server
- 20+ weather/climate tools powered by NOAA RCC ACIS
- Statistical analysis: mean, median, mode, std dev, variance, skewness, kurtosis, percentiles
- Threshold counts and rankings for extreme weather analysis
- Seasonal and monthly aggregations across years
- Frequency of occurrence / likelihood calculations
- Detrending support for time series analysis
- Station discovery via zip code or airport code
- Multi-platform MCP integration (Claude Code, Gemini CLI, Claude Desktop, Cursor, etc.)
- CI/CD with automated PyPI and GitHub release on tag push
- Full test suite (61 tests)
