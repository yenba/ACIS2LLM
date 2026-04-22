# ACIS2LLM

> **The professional weather & climate data layer for LLMs.**

ACIS2LLM connects your AI agents to the **Applied Climate Information System (ACIS)**, providing high-fidelity historical data and statistical analysis from NOAA Regional Climate Centers—no API keys, no rate limits, just pure climate science.

---

## 🛠 Setup

ACIS2LLM is designed to run via **uv** for zero-config installation.

### 1. Claude Code / CLI
```bash
claude mcp add ACIS2LLM -- uvx --from acis2llm acis2llm-mcp
```

### 2. Gemini CLI
```bash
gemini mcp add ACIS2LLM -- uvx --from acis2llm acis2llm-mcp
```

### 3. Claude Desktop
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

### 4. Cursor
Add a new MCP server in **Settings > Features > MCP**:
- **Name:** `ACIS2LLM`
- **Type:** `command`
- **Command:** `uvx --from acis2llm acis2llm-mcp`

### 5. Universal MCP (Codex, OpenCode, Pi, etc.)
ACIS2LLM supports any MCP-compliant environment. Generally, you only need to provide the startup command:
`uvx --from acis2llm acis2llm-mcp`

---

## 🌪 Capabilities

ACIS2LLM transforms your LLM into a climate researcher. It doesn't just "get the weather"—it performs statistical analysis over decades of historical records.

### 1. Geospatial Discovery
*   **`find_best_station`**: Don't guess IDs. Find the most reliable station near a city or zip code based on historical record length.

### 2. Statistical Core
*   **Moments & Distribution**: Calculate `period_mean`, `period_median`, `period_mode`, `period_standard_deviation`, `period_variance`, `period_skewness`, and `period_kurtosis` over any period.
*   **Percentiles**: Determine where a specific value falls in a historical context using `period_percentile`.

### 3. Trend & Extreme Analysis
*   **Threshold Counts**: "How many days were above 100°F last summer?" (`number_of_days_above`).
*   **Rankings**: Automatically find records and extremes with `period_rankings`.
*   **Detrending**: Remove linear trends from time series data with `detrend_data` to analyze cyclical patterns.

### 4. Seasonal & Monthly Aggregates
*   **`seasonal_summary`**: Analyze meteorological seasons (Winter, Spring, Summer, Fall) across years.
*   **`monthly_totals_by_year`**: Compare April precipitation across the last 50 years.
*   **`frequency_of_occurrence`**: Calculate the likelihood of specific events (e.g., "What is % chance of snow in October in Denver?").

---

## 📖 The Climate Cookbook

| If you want to know... | Use this tool |
| :--- | :--- |
| "What was the hottest July in NYC history?" | `monthly_totals_by_year(station="KNYC", variable="tmax", aggregation="max", month="july")` |
| "Is it likely to freeze in Miami during January?" | `frequency_of_occurrence(station="KMIA", variable="tmin", threshold=32, comparison="at_or_below", month="january")` |
| "How does this year's rainfall compare to the 30-year average?" | `running_sum` + `period_mean` |
| "Show me the top 5 snowiest winters in Buffalo." | `seasonal_summary(station="KBUF", season="winter", aggregation="sum")` |

---

## 🗄️ Data & Credits

All data is served in real-time from the **Regional Climate Centers (RCCs)** via the **Applied Climate Information System (ACIS)**.

- **Primary Source**: [rcc-acis.org](https://www.rcc-acis.org/overview)
- **Engine**: Built on [xmACIS2Py](https://github.com/edrewitz/xmACIS2Py) by Eric J. Drewitz (@edrewitz).

---
**License**: MIT | **Author**: yenba
