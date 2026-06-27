# Stress Test Batch 5

**Date:** 2026-06-27
**Type:** Automated edge-case stress test
**Queries tested:** 1
**Status:** Issues found

---

## Results Summary

| # | Query | Category | Difficulty | Status | Answer Quality |
|---|-------|----------|------------|--------|----------------|
| 1 | I'm trying to figure out how often it actually gets brutally... | frequency of occurrence | medium | error_recovered | correct |

## Query 1: I'm trying to figure out how often it actually gets brutally hot in the 85034 area during August. On average, how many days see a high of 105 degrees or higher at the nearby airport?

**Category:** frequency of occurrence
**Difficulty:** medium
**Status:** error_recovered
**Answer Quality:** correct

### Issues

#### KeyError on monthly_threshold_counts due to wrong parameter names

- **Category:** skill_doc_unclear
- **Severity:** medium
- **Description:** The agent encountered a KeyError when calling monthly_threshold_counts with incorrect argument names. This indicates the skill documentation doesn't clearly specify the expected parameter names/format for this function. The agent recovered after retries but this cost 5 function calls and significant processing time.
- **Suggestion:** Add a clear parameter specification table for monthly_threshold_counts in the skill docs, showing exact parameter names (e.g., station_id, month, threshold, element). Include a worked example showing the correct call format, especially for frequency-of-occurrence queries. Consider adding this to recipes.md as a 'frequency of extreme values' pattern.
- **Pointer:** `SKILL.md or recipes.md - monthly_threshold_counts documentation`

#### No recipe for frequency-of-occurrence queries

- **Category:** missing_function
- **Severity:** medium
- **Description:** The agent had to figure out how to answer a 'how often' / 'frequency of occurrence' question through trial and error (5 retries). There's no documented pattern for this common weather question type.
- **Suggestion:** Add a dedicated recipe in recipes.md for 'frequency of occurrence' questions. Show the pattern: (1) find_best_station, (2) monthly_threshold_counts with appropriate parameters, (3) present statistics (mean, median, range, percent of years). This would guide agents directly to the solution without retries.

### What Worked

- The agent correctly identified KPHX (Phoenix Airport) as the best station for ZIP code 85034 using find_best_station
- The agent successfully used monthly_threshold_counts after recovering from the initial error, demonstrating the function works correctly when called with proper parameters
- The agent provided a comprehensive, well-structured answer with multiple useful statistics (average, median, range, years with at least one occurrence)
- The error recovery mechanism worked - the agent detected the KeyError and successfully retried with corrected parameters
- The agent appropriately attempted to backfill data using alternative station IDs, showing good problem-solving (even though no additional data was available)

---

## Consolidated Issues

| Title | Category | Severity | Suggestion |
|-------|----------|----------|------------|
| KeyError on monthly_threshold_counts due to wrong parameter names | skill_doc_unclear | medium | Add a clear parameter specification table for monthly_threshold_counts in the sk... |
| No recipe for frequency-of-occurrence queries | missing_function | medium | Add a dedicated recipe in recipes.md for 'frequency of occurrence' questions. Sh... |
