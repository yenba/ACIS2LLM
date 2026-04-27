# Changelog

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
