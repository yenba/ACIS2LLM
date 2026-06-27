# Stress Test Batch 2

**Date:** 2026-06-27
**Type:** Automated edge-case stress test
**Queries tested:** 5
**Status:** Issues found

---

## Results Summary

| # | Query | Category | Difficulty | Status | Answer Quality |
|---|-------|----------|------------|--------|----------------|
| 1 | What's the normal high temperature for Chicago in January, a... | climate normals or departures | medium | error_recovered | correct |
| 2 | How many days has it actually rained in Seattle during Octob... | frequency of occurrence | medium | error_recovered | correct |
| 3 | I'm looking at KLAX vs KJFK — which airport has had more day... | multi-station comparison | hard | clean | correct |
| 4 | How many cooling degree days did Houston rack up in 2023? Th... | degree days (heating, cooling, growing) query | medium | clean | correct |
| 5 | Did it rain at all in Bakersfield, CA during February 2020? ... | trace precipitation or zero-value edge case | hard | clean | correct |

## Query 1: What's the normal high temperature for Chicago in January, and how did this past January compare? Was it way off from average?

**Category:** climate normals or departures
**Difficulty:** medium
**Status:** error_recovered
**Answer Quality:** correct

### Issues

#### Subprocess install failed using 'python -m uv' instead of 'uv' directly

- **Category:** skill_doc_unclear
- **Severity:** medium
- **Description:** The agent's summary indicates the initial subprocess install failed because it tried 'python -m uv' instead of running 'uv' directly. This caused a retry, adding latency. This is a common gotcha when agents try to install dependencies.
- **Suggestion:** Add a gotcha or note in SKILL.md explicitly stating the correct way to install/invoke dependencies (e.g., 'Use `uv pip install` or `!uv pip install` directly, NOT `python -m uv`'). If there's already an installation recipe, make the exact command more prominent.
- **Pointer:** `SKILL.md or recipes.md: dependency installation section`

#### No explicit recipe for 'normals vs actuals comparison' pattern

- **Category:** doc_gap
- **Severity:** low
- **Description:** This is a common question pattern (compare recent period to climate normals) that could benefit from a dedicated recipe showing how to combine get_single_station_climate_normals and get_single_station_acis_data results to compute departures. The agent figured it out but a recipe would make this more reliable.
- **Suggestion:** Add a recipe in recipes.md for 'Compare recent month to climate normals' showing: 1) fetch normals for the station/month, 2) fetch daily data for the target month, 3) compute averages and departures. This would help agents get it right on the first try without needing to reason through the approach.

### What Worked

- Agent correctly identified this as a climate normals + recent observations question and used both appropriate functions: get_single_station_climate_normals for the 30-year average and get_single_station_acis_data for January 2026 actuals
- Agent selected the correct station (KORD) for Chicago without ambiguity
- The answer is well-structured, comprehensive, and directly addresses the user's question about whether January was 'way off from average' — providing both the quantitative departure and a qualitative interpretation
- Agent provided excellent context with specific examples of daily swings (the Jan 8-9 warmth and Jan 23 cold snap) that enriched the answer beyond the simple normal vs. actual comparison
- The summary is well-formatted with all required fields (ANSWER, ERRORS, RETRIES, FUNCTIONS_USED, STATION)

---

## Query 2: How many days has it actually rained in Seattle during October over the last 30 years? Like, on average, is it really as rainy as people say?

**Category:** frequency of occurrence
**Difficulty:** medium
**Status:** error_recovered
**Answer Quality:** correct

### Issues

#### Parameter name mismatch: 'parameter' vs 'variable' in monthly_threshold_counts

- **Category:** parameter_mismatch
- **Severity:** medium
- **Description:** The agent reported that the monthly_threshold_counts function uses 'parameter' as the parameter name rather than 'variable' as documented. This caused a failed first call and required a retry. The agent explicitly noted this in its ERRORS section: 'monthly_threshold_counts parameter name was parameter not variable as documented'.
- **Suggestion:** Audit the skill docs (SKILL.md, references/, recipes.md) to ensure the parameter naming for monthly_threshold_counts is consistent between documentation and actual API implementation. If the API accepts 'parameter', update docs to say 'parameter'. If it accepts 'variable', fix the API. Add a gotcha entry noting the correct parameter name.
- **Pointer:** `SKILL.md or references/monthly_threshold_counts`

#### Missing recipe for 'frequency of rain days' pattern

- **Category:** doc_gap
- **Severity:** low
- **Description:** The frequency-of-occurrence / rain day counting pattern is a very common weather question type but may not have a dedicated recipe showing the correct parameter names and workflow for monthly_threshold_counts with precipitation thresholds.
- **Suggestion:** Add a recipe in recipes.md for 'How many days did it rain in [city] during [month]?' showing the exact function calls with correct parameter names, threshold values (≥0.01 for measurable precip), and how to aggregate across years for averages.

### What Worked

- Agent correctly identified this as a frequency-of-occurrence question and chose appropriate functions (monthly_threshold_counts for rain day counting, monthly_totals_by_year for precipitation totals)
- Station selection was appropriate — KSEA (Seattle-Tacoma Airport) is the canonical long-record station for Seattle weather questions
- Agent correctly used a 30-year window (1996-2025) matching the user's request
- The answer is well-structured with key stats, range, and context — excellent communication
- Agent provided genuinely useful context comparing Seattle to NYC rainfall patterns, addressing the 'is it really as rainy as people say' part of the question
- Agent correctly used ≥0.01 inches as the threshold for measurable precipitation, which is the standard meteorological definition
- The find_best_station function worked correctly to identify the right station
- Agent successfully recovered from the parameter naming error on retry

---

## Query 3: I'm looking at KLAX vs KJFK — which airport has had more days below freezing since 2000?

**Category:** multi-station comparison
**Difficulty:** hard
**Status:** clean
**Answer Quality:** correct

### Issues

#### Only fetch_stations listed in FUNCTIONS_USED despite needing data retrieval

- **Category:** skill_doc_unclear
- **Severity:** low
- **Description:** The summary section lists only 'acis2llm.fetch_stations' as the function used, but to actually count freezing days the agent would have needed to call a data retrieval function (e.g., fetch_data or similar) for both stations. Either the agent used additional functions and failed to log them, or the summary is incomplete. This doesn't affect the answer quality but makes the audit trail incomplete.
- **Suggestion:** Encourage agents to log all functions used in the summary, not just the station lookup. Consider adding a recipe or template for multi-station comparison queries that explicitly lists the full function chain (fetch_stations → fetch_data for each station → aggregate/compare).
- **Pointer:** `SKILL.md or recipes.md`

#### Date range extends into the future (2026-06-27)

- **Category:** other
- **Severity:** low
- **Description:** The reported date range is '2000-01-01 to 2026-06-27', which appears to use the current date as the end date. This is fine operationally — the API will simply return data up to the latest available — but it's worth noting that the 'days_with_data_each: 9674' count and the freezing day counts are only valid through the most recent available data, not literally through June 27, 2026.
- **Suggestion:** In recipes or gotchas, note that when using 'today' or the current date as edate, the agent should clarify that results are through the most recent available observation date, which may lag the current date.
- **Pointer:** `recipes.md`

### What Worked

- The agent correctly identified both stations by their ICAO identifiers (KLAX, KJFK) and understood the question as a multi-station comparison
- The answer is factually correct: KJFK has vastly more freezing days than KLAX, and the 1,978 count for KJFK (~80 days/year over 25 years) is plausible for a New York metro area station
- KLAX reporting 0 freezing days is correct — LAX coastal station essentially never reaches 32°F
- The agent correctly used minimum temperature (tmin) with a threshold of ≤ 32°F to define 'below freezing'
- The response is well-structured with a clear answer, supporting details object, and summary
- The agent provided useful meteorological context explaining why the results make sense (coastal LA vs. winter-exposed NYC)
- The date range from 2000 to present is appropriate for the 'since 2000' query
- The agent handled the hard difficulty multi-station comparison cleanly with no errors or retries

---

## Query 4: How many cooling degree days did Houston rack up in 2023? That summer felt absolutely brutal.

**Category:** degree days (heating, cooling, growing) query
**Difficulty:** medium
**Status:** clean
**Answer Quality:** correct

### Issues

#### Monthly CDD values sum does not match reported total

- **Category:** data_quality
- **Severity:** low
- **Description:** Summing the monthly_cdd values provided (41+91+155+127+371+609+716+812+615+267+58+18) yields 3,880, which does match the stated total. However, August having 812 CDD (implying an average daily temp of ~91.2°F) and July having 716 CDD (~88.1°F) are plausible for Houston 2023, which had a record-breaking heat wave. The numbers are internally consistent and climatologically reasonable.
- **Suggestion:** No action needed — this was a false alarm on initial inspection. The values check out.

#### Only one function listed in FUNCTIONS_USED

- **Category:** skill_doc_unclear
- **Severity:** low
- **Description:** The summary block lists only 'acis2llm.fetch_stations' in FUNCTIONS_USED, but fetching CDD data would also require a data retrieval call (e.g., acis2llm.fetch_data or similar). Either the agent collapsed multiple function calls into one listing, or the skill routes station lookup and data fetch through a single function. This makes it harder to audit the actual API call chain.
- **Suggestion:** The skill docs or summary template should encourage listing ALL functions used in the chain, not just the first one. If fetch_stations actually handles data retrieval too, that should be documented clearly.

#### Base temperature not explicitly confirmed early

- **Category:** skill_doc_unclear
- **Severity:** low
- **Description:** The agent correctly used base 65°F for CDD (mentioned in the summary block) but didn't state this assumption prominently in the main answer. For degree day queries, the base temperature is critical context since different applications use different bases.
- **Suggestion:** Recipes or skill docs could recommend always stating the base temperature (e.g., 'base 65°F') in the primary answer text, not just the summary block.

### What Worked

- Agent correctly identified Houston and selected KIAH (George Bush Intercontinental) as an appropriate station — a major first-order ASOS station with reliable data.
- The answer is climatologically plausible for Houston 2023, which experienced a historically brutal summer with extended heat. August 2023 was indeed the hottest month.
- Monthly CDD values sum correctly to the stated total of 3,880.
- The agent correctly reported no missing data for the full year, which is expected for a major airport ASOS station.
- The response is well-structured with both a natural language answer and structured data (monthly breakdown, station ID, error status).
- The agent engaged with the user's conversational tone ('brutal summer') while still providing precise data.
- The agent provided useful additional context by breaking out the summer core (Jun-Aug) total and highlighting shoulder months with significant CDD contributions.
- Zero retries indicates clean API interaction with no transient errors.

---

## Query 5: Did it rain at all in Bakersfield, CA during February 2020? I feel like that whole month was bone dry but I can't remember — even a trace?

**Category:** trace precipitation or zero-value edge case
**Difficulty:** hard
**Status:** clean
**Answer Quality:** correct

### Issues

#### Only one function listed in functions_used

- **Category:** other
- **Severity:** low
- **Description:** The agent reports only 'acis2llm.fetch_stations' in functions_used, but to retrieve daily precipitation data for February 2020 it almost certainly also called a data-fetching function (e.g., acis2llm.fetch_data or similar). Either the agent under-reported its tool usage or the logging/summary mechanism doesn't capture all calls. This makes it harder to audit the agent's methodology.
- **Suggestion:** Ensure the agent's summary/logging framework captures all function calls made, not just the first one. If the skill exposes a single endpoint that both resolves the station and fetches data, document that clearly so reviewers understand the data flow.
- **Pointer:** `summary.functions_used`

#### Trace precipitation encoding could use explicit documentation

- **Category:** doc_gap
- **Severity:** low
- **Description:** The agent correctly explains that ACIS encodes a 'T' (trace) as 0.001", which is a key nuance for zero-value and trace precipitation queries. However, if this convention isn't explicitly documented in SKILL.md or a gotcha/recipe, future agents might misinterpret 0.001" as an actual measurement rather than a trace indicator.
- **Suggestion:** Add a gotcha or reference entry in SKILL.md explaining: 'ACIS encodes trace precipitation ("T") as 0.001 inches. This is not a real measurement — it indicates that precipitation was observed but was too small to measure. When answering questions about whether it rained, trace values should be reported as trace, not as 0.001".' The agent handled this correctly here, so this is a preventive suggestion.
- **Pointer:** `SKILL.md or references/gotchas`

### What Worked

- The agent correctly identified the station (KBFL) for Bakersfield, CA — a sensible, well-known airport weather station.
- The agent properly handled the trace precipitation edge case, correctly interpreting 0.001" as a trace ('T') rather than presenting it as an actual measured value. This is exactly the kind of nuance the query was designed to test.
- The answer directly addresses the user's specific question ('even a trace?') by confirming that yes, there was a trace on Feb 21 and a tiny measurable amount on Feb 22.
- The agent provided helpful context by comparing the 0.011" total to the normal February precipitation (~1 inch), giving the user a sense of scale.
- The tone matched the conversational nature of the query — validating the user's memory while providing precise data.
- The answer included specific dates, which adds credibility and usefulness beyond a simple yes/no.
- No errors or retries were needed, indicating smooth API interaction.

---

## Consolidated Issues

| Title | Category | Severity | Suggestion |
|-------|----------|----------|------------|
| Subprocess install failed using 'python -m uv' instead of 'uv' directly | skill_doc_unclear | medium | Add a gotcha or note in SKILL.md explicitly stating the correct way to install/i... |
| No explicit recipe for 'normals vs actuals comparison' pattern | doc_gap | low | Add a recipe in recipes.md for 'Compare recent month to climate normals' showing... |
| Parameter name mismatch: 'parameter' vs 'variable' in monthly_threshold_counts | parameter_mismatch | medium | Audit the skill docs (SKILL.md, references/, recipes.md) to ensure the parameter... |
| Missing recipe for 'frequency of rain days' pattern | doc_gap | low | Add a recipe in recipes.md for 'How many days did it rain in [city] during [mont... |
| Only fetch_stations listed in FUNCTIONS_USED despite needing data retrieval | skill_doc_unclear | low | Encourage agents to log all functions used in the summary, not just the station ... |
| Date range extends into the future (2026-06-27) | other | low | In recipes or gotchas, note that when using 'today' or the current date as edate... |
| Monthly CDD values sum does not match reported total | data_quality | low | No action needed — this was a false alarm on initial inspection. The values chec... |
| Only one function listed in FUNCTIONS_USED | skill_doc_unclear | low | The skill docs or summary template should encourage listing ALL functions used i... |
| Base temperature not explicitly confirmed early | skill_doc_unclear | low | Recipes or skill docs could recommend always stating the base temperature (e.g.,... |
| Trace precipitation encoding could use explicit documentation | doc_gap | low | Add a gotcha or reference entry in SKILL.md explaining: 'ACIS encodes trace prec... |
