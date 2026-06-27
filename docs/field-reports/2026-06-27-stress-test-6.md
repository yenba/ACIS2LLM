# Stress Test Batch 6

**Date:** 2026-06-27
**Type:** Automated edge-case stress test
**Queries tested:** 1
**Status:** Issues found

---

## Results Summary

| # | Query | Category | Difficulty | Status | Answer Quality |
|---|-------|----------|------------|--------|----------------|
| 1 | I'm curious about how snowy the winter of 2021-2022 was in B... | snowfall or winter-specific query (snowiest winter, snow depth, etc.) | medium | error_recovered | incorrect |

## Query 1: I'm curious about how snowy the winter of 2021-2022 was in Buffalo, NY. What was the total snowfall that season, and how does it compare to the long-term average?

**Category:** snowfall or winter-specific query (snowiest winter, snow depth, etc.)
**Difficulty:** medium
**Status:** error_recovered
**Answer Quality:** incorrect

### Issues

#### Incorrect snowfall data - significantly lower than actual records

- **Category:** data_quality
- **Severity:** critical
- **Description:** The agent reported 80.92 inches for Buffalo's 2021-2022 winter, but historical records show approximately 107.5 inches at KBUF, making it the 4th snowiest on record. The reported value is ~27% too low, suggesting a data retrieval or calculation error.
- **Suggestion:** Verify the seasonal_summary() function is correctly aggregating December-February data for the winter season. Add validation checks to flag implausible values (e.g., Buffalo winters below 70 inches should trigger a warning). Consider adding a recipe example for Buffalo winter snowfall queries.
- **Pointer:** `acis2llm.seasonal_summary`

#### Future date range in record period (1944-2026)

- **Category:** data_quality
- **Severity:** high
- **Description:** The agent reported '83 winters on record (1944–2026)' which includes future years. This is impossible and indicates either a data parsing error, hallucination, or incorrect calculation of the record period length.
- **Suggestion:** Add input validation to ensure date ranges don't extend beyond the current date. The skill should validate that the 'total_winters' count matches the actual historical record length. Add a gotcha about verifying temporal bounds in returned data.
- **Pointer:** `acis2llm.seasonal_summary`

#### TypeError with 'variable' keyword argument in seasonal_summary()

- **Category:** api_error
- **Severity:** medium
- **Description:** The agent encountered a TypeError when calling seasonal_summary() with a 'variable' keyword argument, suggesting either incorrect parameter usage or unclear documentation about valid parameters.
- **Suggestion:** Update SKILL.md to explicitly document all valid parameters for seasonal_summary() with their types and required/optional status. Add a gotcha entry about parameter validation. Consider adding type hints to the function signature.
- **Pointer:** `SKILL.md - seasonal_summary documentation`

#### KeyError 'data' with backfilled station spec

- **Category:** wrong_api_usage
- **Severity:** medium
- **Description:** When using a backfilled station specification ('304844+94753'), the agent encountered a KeyError for 'data'. This suggests the API doesn't handle backfilled station specs consistently or the docs don't clarify the expected return format.
- **Suggestion:** Add documentation about how backfilled station specs should be used and what return format to expect. Consider adding a recipe for handling stations with data gaps. The skill should provide clearer error messages when backfilled specs fail.
- **Pointer:** `SKILL.md - station specification documentation`

### What Worked

- The agent correctly identified KBUF (Buffalo Niagara International Airport) as the appropriate station for Buffalo weather data
- The agent used the correct API functions (find_best_station and seasonal_summary) for this query type
- The agent successfully recovered from errors and produced a structured answer despite encountering TypeError and KeyError
- The agent provided a complete response with all requested fields: snowfall total, long-term average, difference, percentage, and rank
- The retry mechanism worked - the agent attempted 2 retries and eventually produced output

---

## Consolidated Issues

| Title | Category | Severity | Suggestion |
|-------|----------|----------|------------|
| Incorrect snowfall data - significantly lower than actual records | data_quality | critical | Verify the seasonal_summary() function is correctly aggregating December-Februar... |
| Future date range in record period (1944-2026) | data_quality | high | Add input validation to ensure date ranges don't extend beyond the current date.... |
| TypeError with 'variable' keyword argument in seasonal_summary() | api_error | medium | Update SKILL.md to explicitly document all valid parameters for seasonal_summary... |
| KeyError 'data' with backfilled station spec | wrong_api_usage | medium | Add documentation about how backfilled station specs should be used and what ret... |
