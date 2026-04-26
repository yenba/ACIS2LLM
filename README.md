# ACIS2LLM

> **The professional weather & climate data layer for LLMs.**

ACIS2LLM connects your AI agents to the **Applied Climate Information System (ACIS)**, providing high-fidelity historical data and statistical analysis from NOAA Regional Climate Centers—no API keys, no rate limits, just pure climate science.

---

## Quick Start

Install with one command, then ask your LLM:

```bash
claude mcp add ACIS2LLM -- uvx --from acis2llm acis2llm-mcp
```

> *"What's the likelihood of snow in Denver this month?"*
> *"How many days over 100°F did Phoenix have in 2023?"*
> *"Show me the top 5 snowiest winters on record in Buffalo."*

---

## Setup

ACIS2LLM is designed to run via **uv** for zero-config installation. [Install uv first](https://docs.astral.sh/uv/getting-started/installation/) if you don't have it.

### Claude Code / CLI
```bash
claude mcp add ACIS2LLM -- uvx --from acis2llm acis2llm-mcp
```

### Gemini CLI
```bash
gemini mcp add ACIS2LLM -- uvx --from acis2llm acis2llm-mcp
```

### Claude Desktop
Add this to your `claude_desktop_config.json`:

```json
{
  "mcpServers": {
    "ACIS2LLM": {
      "command": "uvx",
      "args": ["--from", "acis2llm", "acis2llm-mcp"]
    }
  }
}
```

### Cursor
Add a new MCP server in **Settings > Features > MCP**:
- **Name:** `ACIS2LLM`
- **Type:** `command`
- **Command:** `uvx --from acis2llm acis2llm-mcp`

### Universal MCP (Codex, OpenCode, Pi, etc.)
ACIS2LLM supports any MCP-compliant environment. Generally, you only need to provide the startup command:
`uvx --from acis2llm acis2llm-mcp`

### Uninstall
```bash
claude mcp remove ACIS2LLM
```
(Or remove the entry from your config file.)

---

## Data Variables

| Code | Variable | Unit |
|------|----------|------|
| `tmax` | Maximum Temperature | °F |
| `tmin` | Minimum Temperature | °F |
| `tavg` | Average Temperature | °F |
| `prcp` | Precipitation | inches |
| `snow` | Snowfall | inches |
| `snow_depth` | Snow Depth | inches |
| `awdb` | Average Daily Water Balance | inches |
| `hdd` | Heating Degree Days | base 65°F |
| `cdd` | Cooling Degree Days | base 65°F |
| `gdd` | Growing Degree Days | base 32°F |
| `tdpa` | Average Temperature Departure | °F |

---

## Capabilities

### Geospatial Discovery

| Tool | Use When |
|------|----------|
| `find_best_station` | You have a zip code or airport code and need the most reliable nearby station with the longest record |
| `clarify_location` | The user's location is ambiguous or missing |

### Raw Data & Quick Queries

| Tool | Use When |
|------|----------|
| `get_data` | Download raw daily observations for any date range. Supports relative dates like `from_when="last_year"`, multi-station queries with `"ALL"`, and CSV export via `to_csv=true` |

### Statistical Analysis (Single Values)

| Tool | Answers |
|------|---------|
| `period_mean` | "What was the average high in July?" |
| `period_median` / `period_mode` | Median or most common value |
| `period_maximum` / `period_minimum` | Record highs and lows |
| `period_sum` | Total precipitation or snowfall |
| `period_standard_deviation` / `period_variance` | How much did values vary? |
| `period_skewness` / `period_kurtosis` | Distribution shape |
| `period_percentile` | "What's the 90th percentile for daily snowfall?" |

### Rankings & Time Series

| Tool | Answers |
|------|---------|
| `period_rankings` | Top/bottom extremes with rank order. Use `sort_order="ascending"` for coldest/lowest |
| `running_sum` | Cumulative totals over time (e.g., year-to-date rainfall) |
| `running_mean` | Moving averages |
| `detrend_data` | Remove linear trends to analyze cyclical patterns |

### Threshold Analysis

| Tool | Answers |
|------|---------|
| `number_of_days_above` / `below` | "How many days over 90°F?" |
| `number_of_days_at_or_above` / `at_or_below` | Inclusive thresholds (e.g., freezing: `<= 32`) |
| `number_of_days_at` | Exact match (e.g., days with exactly 0 precipitation) |
| `number_of_missing_days` | Data quality check for a period |

### Monthly & Seasonal Aggregates

| Tool | Answers |
|------|---------|
| `monthly_totals_by_year` | April snowfall across 50 years of records |
| `seasonal_summary` | Meteorological seasons (winter Dec-Feb, etc.) by year |
| `frequency_of_occurrence` | Likelihood: "What's the % chance of snow in October?" |
| `monthly_threshold_counts` | Year-by-year count of days meeting a threshold |

---

## The Climate Cookbook

| If you want to know... | Use this tool |
|:---|:---|
| *"What was the hottest July in NYC history?"* | `monthly_totals_by_year(station="KNYC", variable="tmax", aggregation="max", month="july")` |
| *"Is it likely to freeze in Miami during January?"* | `frequency_of_occurrence(station="KMIA", variable="tmin", threshold=32, comparison="at_or_below", month="january")` |
| *"How does this year's rainfall compare to the 30-year average?"* | `running_sum` + `period_mean` |
| *"Show me the top 5 snowiest winters in Buffalo."* | `seasonal_summary(station="KBUF", variable="snow", season="winter", aggregation="sum")` |
| *"What was the weather last week in Chicago?"* | `get_data(station="KORD", from_when="last_week")` |
| *"Compare snowfall across all stations in a region"* | `get_data(station="ALL", start_date="...", end_date="...")` |

---

## Troubleshooting

| Problem | Solution |
|---------|----------|
| `uv: command not found` | Install uv: `curl -LsSf https://astral.sh/uv/install.sh \| sh` |
| Station not found | Use `find_best_station` with a 5-digit zip code or airport code |
| Empty results | Check date range and that the station has records for that period. Use `number_of_missing_days` to check data gaps |
| Slow responses | Large date ranges fetch more data. Narrow the range or use aggregated tools instead of `get_data` |

---

## Data & Credits

All data is served in real-time from the **Regional Climate Centers (RCCs)** via the **Applied Climate Information System (ACIS)**.

- **Primary Source**: [rcc-acis.org](https://www.rcc-acis.org/overview)
- **Engine**: Built on [xmACIS2Py](https://github.com/edrewitz/xmACIS2Py) by Eric J. Drewitz (@edrewitz).

---

**License**: MIT | **Author**: [yenba](https://github.com/yenba) | **Issues**: [GitHub](https://github.com/yenba/acis2LLM/issues)
