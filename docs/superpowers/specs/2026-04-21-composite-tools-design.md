# Composite Tools for Efficient Query Handling

## Problem

The agent handles vague natural-language queries like "what's the likelihood of snow in April in Lexington, KY" inefficiently. It fetches daily data across many years via multiple `get_data` calls, then chains several analysis tool calls to compute the answer. This burns through multiple LLM round-trips for something the SC ACIS web UI answers in one click via its "Monthly Summarized Data" or "Seasonal Time Series" products.

The root causes:
1. No high-level tools exist for common climatological queries (monthly summaries by year, seasonal aggregations, frequency/likelihood calculations).
2. The system prompt gives no guidance on query strategy — the LLM has to figure out multi-step plans on its own.
3. The `time_delta` parameter description in tool schemas is wrong (says "monthly, seasonal, annual" but it's actually an integer for "days back"), actively misleading the LLM.

## Approach

Add three new "composite" tools that fetch daily data via `xmacis2py.get_data` under the hood and aggregate in Python. This reduces most climatological queries to a single tool call. Also overhaul the system prompt with query-planning guidance and fix the `time_delta` description.

Designed so the internals of composite tools can later be swapped to use the RCC-ACIS API directly (Approach C) without changing the tool interface.

## New Tools

### 1. `monthly_totals_by_year`

Retrieves a variable's monthly aggregate for a single month across all available years.

**Parameters:**
- `station` (string, required) — 4-letter station ID
- `variable` (string, required) — weather variable (e.g., "snow", "prcp", "tmax")
- `month` (string, required) — month number (1-12) or name ("january", "april", etc.)
- `start_year` (integer, optional) — first year to include (default: earliest available)
- `end_year` (integer, optional) — last year to include (default: most recent available)
- `aggregation` (string, optional) — "sum" (default), "mean", "max", "min"

**Returns:** A formatted table with columns: Year, Value, Missing Days. Followed by a summary line (e.g., "Average April snowfall: 0.3 inches across 35 years, median: 0.0 inches").

**Implementation:**
1. Determine date range: `{start_year}-{month}-01` to `{end_year}-{month}-{last_day}`
2. Call `get_data(station, start_date, end_date)` once for the full range
3. Filter DataFrame to only rows in the target month
4. Map variable name to DataFrame column via `VARIABLE_COLUMN_MAP`
5. Group by year, apply aggregation function
6. Count missing values per year
7. Format and return

**Example queries this handles:**
- "How much snow does Lexington get in April?"
- "What's the average high temperature in July in Chicago?"
- "Show me October rainfall in Denver over the years"

### 2. `seasonal_summary`

Summarizes a variable across a meteorological season by year.

**Parameters:**
- `station` (string, required) — 4-letter station ID
- `variable` (string, required) — weather variable
- `season` (string, required) — "winter" (Dec-Feb), "spring" (Mar-May), "summer" (Jun-Aug), "fall" (Sep-Nov)
- `start_year` (integer, optional) — first year to include
- `end_year` (integer, optional) — last year to include
- `aggregation` (string, optional) — "sum" (default), "mean", "max", "min"

**Returns:** Same format as `monthly_totals_by_year` — Year, Value, Missing Days, plus summary.

**Implementation:**
1. Map season name to months (winter = Dec, Jan, Feb; winter 2024 = Dec 2023 + Jan-Feb 2024)
2. Call `get_data` once for the full date range
3. Assign each row to a season-year (winter is labeled by the ending year, e.g., Dec 2023 + Jan-Feb 2024 = Winter 2024)
4. Group by season-year, apply aggregation
5. Format and return

**Example queries:**
- "How was this past winter's snowfall compared to average?"
- "Show me summer precipitation trends in Atlanta"

### 3. `frequency_of_occurrence`

Answers "how often does X happen" questions — the likelihood/probability pattern.

**Parameters:**
- `station` (string, required) — 4-letter station ID
- `variable` (string, required) — weather variable
- `month` (string, optional) — month number or name (provide month OR season, not both)
- `season` (string, optional) — season name
- `threshold` (number, required) — value to compare against
- `comparison` (string, required) — "above", "at_or_above", "below", "at_or_below"
- `start_year` (integer, optional) — first year
- `end_year` (integer, optional) — last year

**Returns:** A structured result with:
- Count of years meeting the condition
- Total years in the record
- Percentage
- Year-by-year breakdown (year, value, met_condition: yes/no)

**Implementation:**
1. Use `monthly_totals_by_year` or `seasonal_summary` internally to get the per-year aggregated values
2. Apply the threshold comparison to each year's aggregated value (e.g., total April snowfall for that year, not individual daily values)
3. Calculate count and percentage
4. Format and return

**Example queries:**
- "What's the likelihood of snow in April in Lexington?" → `frequency_of_occurrence("KLEX", "snow", month="april", threshold=0, comparison="above")`
- "How often does it get above 100 degrees in July in Phoenix?"

## File Changes

### New file: `composite_tools.py`

Contains the implementation of all three composite tools. Imports `xmacis2py.get_data` and uses pandas for aggregation. Exports three public functions:

- `monthly_totals_by_year(station, variable, month, start_year=None, end_year=None, aggregation="sum")`
- `seasonal_summary(station, variable, season, start_year=None, end_year=None, aggregation="sum")`
- `frequency_of_occurrence(station, variable, month=None, season=None, threshold=0, comparison="above", start_year=None, end_year=None)`

Each returns a dict with `table` (list of row dicts), `summary` (string), and `raw_df` (pandas DataFrame for potential further use).

Also contains helper functions:
- `_parse_month(month_input)` — converts "april", "Apr", "4" to integer 4
- `_get_season_months(season)` — returns list of month numbers
- `_assign_season_year(date, season_months)` — assigns a date to the correct season-year (handles winter straddling Dec/Jan)

### Modified: `tools.py`

Add three new tool schemas to `TOOL_DEFINITIONS`. Fix the `time_delta` description from "Time aggregation (e.g. 'daily', 'hourly', 'monthly', 'seasonal', 'annual')" to "Number of days in the past from the `from_when` date (integer, e.g. 30 means 30 days back). Only used when start_date/end_date are not provided."

### Modified: `execution.py`

Add a `_COMPOSITE_TOOLS` set and dispatch to `composite_tools` functions when a composite tool name is detected. Add required args entries for the three new tools.

### Modified: `formatter.py`

Add `format_composite_result(result, tool_name)` — formats the dict returned by composite tools into a clean table with summary. Compact format: no 30-row truncation needed since these results are already aggregated (one row per year).

### Modified: `system_prompt.py`

Three changes:

**1. New "Query Strategy" section:**
```
## Query Strategy — Choosing the Right Tool

Match the user's question to the most efficient tool:

- Likelihood, frequency, "how often", "chance of" → frequency_of_occurrence
- Monthly totals/averages across years for a specific month → monthly_totals_by_year
- Seasonal trends or comparisons → seasonal_summary
- Specific day or short date range lookups → get_data
- Statistical analysis of a known date range → period_* tools
- Threshold day counts within a known date range → number_of_days_* tools

Always prefer the composite tools (monthly_totals_by_year, seasonal_summary, frequency_of_occurrence) over chaining get_data + multiple analysis calls. They return pre-computed results in one call.
```

**2. New "Natural Language Examples" section:**
```
## Natural Language → Tool Mapping Examples

- "Will it snow in April?" → frequency_of_occurrence(station, "snow", month="april", threshold=0, comparison="above")
- "What's the average high in July?" → monthly_totals_by_year(station, "tmax", month="july", aggregation="mean")
- "How was this winter's snowfall?" → seasonal_summary(station, "snow", season="winter")
- "How much rain does Atlanta get in the summer?" → seasonal_summary(station, "prcp", season="summer")
- "What was yesterday's high?" → get_data(station, from_when="yesterday")
- "How many days above 90 last summer?" → number_of_days_above(station, "tmax", start_date, end_date, value=90)
```

**3. Fix time_delta description** — correct the misleading description in the tool list summary and in the `tools.py` schema.

## Design Decisions

**Why aggregate in Python instead of adding more xmacis2py API calls:**
`xmacis2py.get_data` is the only data-fetching function in the library. The analysis module operates on DataFrames, not on the API. Aggregation in pandas is straightforward and keeps us within the existing dependency set.

**Why return dicts instead of pre-formatted strings from composite_tools.py:**
Separating data from formatting lets `formatter.py` handle presentation. If we later swap to direct ACIS API calls (Approach C), only `composite_tools.py` changes — formatter stays the same.

**Why season-year labels winter by the ending year:**
Meteorological convention. "Winter 2024" = Dec 2023 + Jan-Feb 2024. This matches how the SC ACIS UI labels seasons.

**Default aggregation is "sum":**
Most common use case for precipitation and snowfall. Temperature queries will typically override to "mean" or "max"/"min", and the LLM can infer this from context.

## Future Extensibility

This design is intentionally modular. Additional composite tools can be added by:
1. Writing the function in `composite_tools.py`
2. Adding a schema in `tools.py`
3. Adding the tool name to `_COMPOSITE_TOOLS` in `execution.py`
4. Adding query strategy guidance in `system_prompt.py`

Potential future tools: `year_over_year_comparison`, `record_extremes`, `first_last_date_of_season`, `consecutive_days_analysis`.

When ready for Approach C (direct ACIS API), swap the internals of `composite_tools.py` to hit the API instead of calling `get_data` — the tool interface and everything downstream stays identical.
