# ACIS2LLM

Weather and climate data tools powered by NOAA RCC ACIS. Use as an MCP server in Claude Code, Cursor, and other AI tools.

## Features

- 26 weather/climate analysis tools via the `xmacis2py` Python library
- **MCP server** — works with Claude Code, Claude Desktop, Cursor, and any MCP-compatible client
- Station lookup by city name or zip code via geocoding
- No API keys needed — all data comes from the public NOAA RCC ACIS database

## Installation and Usage

acis2llm is an MCP server so you can use all 26 weather/climate tools directly in Claude Code, Claude Desktop, Cursor, or any MCP-compatible client.

Requires Python 3.10+ and [uv](https://github.com/astral-sh/uv).

### Claude Code

```bash
claude mcp add acis2llm -- uvx --from acis2llm acis2llm-mcp
```

### Claude Desktop

Add to your Claude Desktop config (`~/Library/Application Support/Claude/claude_desktop_config.json` on macOS):

```json
{
  "mcpServers": {
    "acis2llm": {
      "command": "uvx",
      "args": ["--from", "acis2llm", "acis2llm-mcp"]
    }
  }
}
```

### Local development

```bash
claude mcp add acis2llm-dev -- uv run mcp_server.py
```

No API keys are needed — all weather data comes from the public NOAA RCC ACIS database.

## Tools Available

| Tool | Description |
|------|-------------|
| `get_data` | Download weather data from ACIS |
| `period_mean` | Calculate period mean |
| `period_median` | Calculate period median |
| `period_mode` | Calculate period mode |
| `period_percentile` | Calculate period percentile |
| `period_standard_deviation` | Calculate period std dev |
| `period_variance` | Calculate period variance |
| `period_skewness` | Calculate period skewness |
| `period_kurtosis` | Calculate period kurtosis |
| `period_maximum` | Calculate period maximum |
| `period_minimum` | Calculate period minimum |
| `period_sum` | Calculate period sum |
| `period_rankings` | Calculate period rankings |
| `running_sum` | Calculate running sum |
| `running_mean` | Calculate running mean |
| `detrend_data` | Detrend time series data |
| `number_of_days_at_or_below` | Count days at or below value |
| `number_of_days_at_or_above` | Count days at or above value |
| `number_of_days_below` | Count days below value |
| `number_of_days_above` | Count days above value |
| `number_of_days_at` | Count days at value |
| `number_of_missing_days` | Count missing data days |
| `monthly_totals_by_year` | Monthly aggregate across years |
| `seasonal_summary` | Seasonal aggregate by year |
| `frequency_of_occurrence` | How often a threshold is met |
| `find_best_station` | Find nearest station by location |

### Common Station Codes

Station codes are 4-letter identifiers (e.g., `KRAL`, `KLAX`, `KORD`).

### Common Variables

| Variable | Description |
|----------|-------------|
| `tmax` | Maximum temperature |
| `tmin` | Minimum temperature |
| `tavg` | Average temperature |
| `prcp` | Precipitation |
| `snow` | Snowfall |
| `awdb` | Average daily water balance |
| `hdd` | Heating degree days |
| `cdd` | Cooling degree days |
| `gdd` | Growing degree days |

## Architecture

```
MCP Client (Claude Code, Cursor, etc.)
    │ stdio
    ▼
mcp_server.py ──▶ execution.py ──▶ xmacis2py ──▶ NOAA RCC ACIS
                                 ──▶ composite_tools.py
```

## Data Sources & Credits

This project is built upon the following data sources and libraries:

- **Data Source**: All weather and climate data is provided by the **Regional Climate Centers (RCCs)** through the **Applied Climate Information System (ACIS)**. For more information about ACIS, visit [rcc-acis.org](https://www.rcc-acis.org/overview).
- **Python Library**: This project uses [xmACIS2Py](https://github.com/edrewitz/xmACIS2Py), a Python library developed by **Eric J. Drewitz** (@edrewitz) for analyzing and retrieving ACIS climate data.

Special thanks to the Regional Climate Centers and Eric J. Drewitz for maintaining these essential tools for the climate community.

## License

MIT
