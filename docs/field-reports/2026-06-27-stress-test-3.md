# Stress Test Batch 3

**Date:** 2026-06-27
**Type:** Automated edge-case stress test
**Queries tested:** 1
**Status:** Issues found

---

## Results Summary

| # | Query | Category | Difficulty | Status | Answer Quality |
|---|-------|----------|------------|--------|----------------|
| 1 | What's the hottest July ever recorded in Phoenix, AZ? | cross-year ranking (hottest/coldest/wettest/driest month or season ever) | easy | error_recovered | correct |

## Query 1: What's the hottest July ever recorded in Phoenix, AZ?

**Category:** cross-year ranking (hottest/coldest/wettest/driest month or season ever)
**Difficulty:** easy
**Status:** error_recovered
**Answer Quality:** correct

### Issues

#### Backfill station spec (+) not supported by monthly_totals_by_year()

- **Category:** doc_gap
- **Severity:** medium
- **Description:** The agent encountered a KeyError 'data' when passing a plus-joined backfill station spec (KLUF+025282) to monthly_totals_by_year(). The skill docs do not clearly indicate which API functions support plus-joined backfill station specs and which do not. The agent had to discover through trial-and-error that individual stations needed to be queried separately.
- **Suggestion:** Add a gotcha entry in SKILL.md or the API reference for monthly_totals_by_year() stating: 'Plus-joined backfill station specs (e.g., KLUF+025282) may not be supported by all functions. If you encounter a KeyError or unexpected error, split the spec into individual stations and query them separately, then merge the results.' Also add this to the parameter documentation for monthly_totals_by_year().
- **Pointer:** `SKILL.md - API reference for monthly_totals_by_year()`

#### Missing error recovery recipe for backfill station spec failures

- **Category:** missing_function
- **Severity:** low
- **Description:** While the agent successfully recovered by querying individual stations separately, there's no documented recipe or pattern for handling this specific failure mode. Future agents would need to rediscover this workaround.
- **Suggestion:** Add a recipe in recipes.md titled 'Handling backfill station spec errors' that shows the pattern: (1) Try the plus-joined spec, (2) If it fails, split into individual stations, (3) Query each separately, (4) Merge/deduplicate results by date.

### What Worked

- Agent correctly identified monthly_totals_by_year() as the appropriate function for cross-year monthly ranking queries
- Agent used find_best_station() correctly to identify relevant stations for Phoenix, AZ
- Agent successfully recovered from the backfill station spec error by querying individual stations (KLUF, 025282, KPHX) separately
- Agent provided a comprehensive answer covering both interpretations of 'hottest July' (single-day record and monthly average)
- The error reporting in the output was clear and helpful for debugging
- Agent included supporting data (top 5 single-day highs) to enrich the answer

---

## Consolidated Issues

| Title | Category | Severity | Suggestion |
|-------|----------|----------|------------|
| Backfill station spec (+) not supported by monthly_totals_by_year() | doc_gap | medium | Add a gotcha entry in SKILL.md or the API reference for monthly_totals_by_year()... |
| Missing error recovery recipe for backfill station spec failures | missing_function | low | Add a recipe in recipes.md titled 'Handling backfill station spec errors' that s... |
