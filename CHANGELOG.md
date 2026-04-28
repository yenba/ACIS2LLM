# Changelog

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
