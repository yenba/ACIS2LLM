# Stress Test Batch 8

**Date:** 2026-06-27
**Type:** Automated edge-case stress test
**Queries tested:** 1
**Status:** Issues found

---

## Results Summary

| # | Query | Category | Difficulty | Status | Answer Quality |
|---|-------|----------|------------|--------|----------------|
| 1 | My cousin swears it's way hotter in Tucson than Las Vegas du... | multi-station comparison | medium | error_recovered | correct |

## Query 1: My cousin swears it's way hotter in Tucson than Las Vegas during the summer. Can you compare the average high temperatures for both cities in June over the last 10 years to see if there's really that big of a difference?

**Category:** multi-station comparison
**Difficulty:** medium
**Status:** error_recovered
**Answer Quality:** correct

### Issues

#### single_station_meta returns DataFrame, not dict

- **Category:** parameter_mismatch
- **Severity:** medium
- **Description:** The agent encountered a KeyError when calling single_station_meta because it assumed the function returns a dict, but it actually returns a DataFrame. This is a return shape mismatch that caused the initial error.
- **Suggestion:** Update SKILL.md to explicitly state the return type of single_station_meta (DataFrame vs dict). If it returns a DataFrame, document how to extract fields from it (e.g., df['field_name'] or df.iloc[0]['field_name']). Consider adding a gotcha: 'single_station_meta returns a pandas DataFrame, not a dictionary - use DataFrame indexing to access fields.'
- **Pointer:** `SKILL.md - single_station_meta function documentation`

#### fetch_stations returned empty DataFrame on first call

- **Category:** api_error
- **Severity:** medium
- **Description:** The initial fetch_stations call returned an empty DataFrame, suggesting incorrect parameters or a transient issue. The agent had to retry to get valid station data.
- **Suggestion:** Add a gotcha entry documenting that fetch_stations may return empty results if the search parameters are too restrictive or if there's a transient API issue. Document the expected retry pattern. Consider adding validation logic in the skill to warn when fetch_stations returns empty results and suggest broader search parameters.
- **Pointer:** `SKILL.md - fetch_stations function documentation`

#### No recipe for multi-station comparison queries

- **Category:** missing_function
- **Severity:** medium
- **Description:** The skill lacks a dedicated recipe for comparing weather data across multiple stations over time. This is a common query pattern (marked as 'multi-station comparison' in the test) but has no documented workflow.
- **Suggestion:** Add a recipe in recipes.md for 'Multi-Station Comparison' that shows: (1) how to fetch both stations, (2) how to call monthly_totals_by_year for each, (3) how to align and compare the results, (4) error handling patterns. This would guide agents through the complete workflow for comparison queries.
- **Pointer:** `recipes.md - missing multi-station comparison recipe`

### What Worked

- The agent correctly identified station codes TUS (Tucson) and LAS (Las Vegas)
- monthly_totals_by_year function worked correctly and provided the needed yearly temperature data
- The agent successfully computed average highs, yearly differences, and summary statistics from the raw data
- The agent recovered from errors through retries (2 retries) and produced a complete, well-structured answer
- The final output included a clear narrative answer plus structured yearly_comparison and summary_stats data
- The agent correctly interpreted the query as requiring a 10-year historical comparison and delivered that scope

---

## Consolidated Issues

| Title | Category | Severity | Suggestion |
|-------|----------|----------|------------|
| single_station_meta returns DataFrame, not dict | parameter_mismatch | medium | Update SKILL.md to explicitly state the return type of single_station_meta (Data... |
| fetch_stations returned empty DataFrame on first call | api_error | medium | Add a gotcha entry documenting that fetch_stations may return empty results if t... |
| No recipe for multi-station comparison queries | missing_function | medium | Add a recipe in recipes.md for 'Multi-Station Comparison' that shows: (1) how to... |
