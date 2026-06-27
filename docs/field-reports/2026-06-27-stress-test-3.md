# Stress Test Batch 3

**Date:** 2026-06-27
**Type:** Automated edge-case stress test
**Queries tested:** 5
**Status:** Issues found

---

## Results Summary

| # | Query | Category | Difficulty | Status | Answer Quality |
|---|-------|----------|------------|--------|----------------|
| 1 | How much snow did Buffalo get compared to Cleveland during t... | multi-station comparison | medium | clean | correct |
| 2 | Back in July 2015, how many days did the high temp in Miami ... | threshold count | easy | error_recovered | correct |
| 3 | I'm moving to the 33139 area. What's the typical rainfall th... | ambiguous or tricky location | medium | error_recovered | correct |
| 4 | How much did the average temperature in Phoenix deviate from... | climate normals or departures | medium | clean | correct |
| 5 | What was the maximum snow depth recorded at LaGuardia Airpor... | edge-case time period | hard | error_unrecovered | incorrect |

## Query 1: How much snow did Buffalo get compared to Cleveland during the 2014 winter season?

**Category:** multi-station comparison
**Difficulty:** medium
**Status:** clean
**Answer Quality:** correct

### What Worked

- Agent successfully performed multi-station comparison between Buffalo (KBUF) and Cleveland (KCLE)
- Correctly interpreted '2014 winter season' as December 2013 - February 2014
- Provided comprehensive breakdown including monthly totals, snow days, and biggest single-day events
- Clear comparative answer with both absolute values (94.6

---

## Query 2: Back in July 2015, how many days did the high temp in Miami actually exceed 90 degrees?

**Category:** threshold count
**Difficulty:** easy
**Status:** error_recovered
**Answer Quality:** correct

### Issues

#### Function name confusion: number_of_days_above vs number_of_days_above_value

- **Category:** skill_doc_unclear
- **Severity:** medium
- **Description:** The agent initially called a function named 'number_of_days_above' which doesn't exist (AttributeError). The correct function is 'number_of_days_above_value'. This suggests the skill documentation doesn't clearly distinguish between similarly-named functions or doesn't provide a clear recipe for threshold count queries. The naming similarity between potential functions could be confusing.
- **Suggestion:** Add a clear recipe in recipes.md for 'threshold count' queries that explicitly shows the correct function name 'number_of_days_above_value'. Also add a gotcha entry in SKILL.md noting that 'number_of_days_above' does not exist and users should use 'number_of_days_above_value' instead. Consider adding a 'Common Mistakes' section to the skill docs.
- **Pointer:** `SKILL.md or recipes.md`

#### Agent required retry to find correct function

- **Category:** agent_confusion
- **Severity:** low
- **Description:** While the agent recovered from the error, the fact that it needed a retry suggests the documentation could better guide agents to the correct function on first attempt. This is a minor issue since recovery was successful, but indicates room for improvement in discoverability.
- **Suggestion:** Consider adding function aliases or deprecation warnings in the code if 'number_of_days_above' is a common mistake. Alternatively, enhance the function descriptions in SKILL.md to be more explicit about when to use each analysis function.

### What Worked

- The agent successfully recovered from the AttributeError and used the correct function on retry
- The agent correctly identified KMIA (Miami International Airport) as the appropriate station for Miami
- The agent used the correct overall workflow: find_best_station -> get_single_station_acis_data -> number_of_days_above_value
- The final answer was well-structured with the count, time period, threshold value, and station information
- The agent demonstrated good error handling by retrying with the corrected function name

---

## Query 3: I'm moving to the 33139 area. What's the typical rainfall there in January?

**Category:** ambiguous or tricky location
**Difficulty:** medium
**Status:** error_recovered
**Answer Quality:** correct

### Issues

#### Climate normals returned incomplete monthly data

- **Category:** data_quality
- **Severity:** medium
- **Description:** The get_single_station_climate_normals API returned only May/June rows instead of data for all 12 months. The agent had to work around this to find January rainfall data, likely by using monthly_totals_by_year as a fallback.
- **Suggestion:** Add a gotcha to SKILL.md noting that climate normals may not always return all 12 months of data, and recommend using monthly_totals_by_year as a more reliable alternative for getting complete monthly statistics. Consider adding a recipe for 'getting typical monthly rainfall' that shows this fallback pattern.
- **Pointer:** `SKILL.md - Gotchas section`

#### monthly_totals_by_year failed with backfill station spec format

- **Category:** wrong_api_usage
- **Severity:** high
- **Description:** The agent encountered a KeyError 'data' when calling monthly_totals_by_year with a backfill station specification. This suggests the station spec format used (possibly from find_best_station) was incompatible with what monthly_totals_by_year expects.
- **Suggestion:** Add a gotcha entry explaining the difference between station specification formats used by different functions. Document that monthly_totals_by_year may require a specific station ID format (e.g., just the station ID like '083909' rather than '083909+12859'). Add a recipe showing how to properly extract and format station IDs when switching between functions.
- **Pointer:** `SKILL.md - Gotchas section, references/station-specs.md`

#### Table row key confusion: 'value' vs 'total'

- **Category:** wrong_api_usage
- **Severity:** medium
- **Description:** The agent expected to find data under a 'total' key in table rows but found it under 'value' instead. This suggests the documentation doesn't clearly specify the exact key names used in the return structure of certain API calls.
- **Suggestion:** Update the API reference documentation to include exact example return values with all key names clearly shown. Add a gotcha noting that table/data row keys may vary between endpoints (e.g., 'value' vs 'total') and recommend checking actual return structures.
- **Pointer:** `references/ - API response schemas`

### What Worked

- The agent correctly identified 33139 as Miami Beach, FL and found a nearby appropriate station (Hialeah, FL)
- The agent successfully used find_best_station to locate a station for the ZIP code
- The agent demonstrated good recovery behavior by retrying 3 times and ultimately producing a complete answer despite encountering errors
- The final answer was comprehensive, including average (2.1 inches), median (1.7 inches), range (0.00-7.10 inches), and contextual information about the dry season
- The agent correctly identified that get_single_station_climate_normals was the appropriate function for getting 'typical' climate data, even though it had incomplete month coverage

---

## Query 4: How much did the average temperature in Phoenix deviate from the 30-year normal in June 2020?

**Category:** climate normals or departures
**Difficulty:** medium
**Status:** clean
**Answer Quality:** correct

### Issues

#### Column name mismatch in climate normals DataFrame

- **Category:** skill_doc_unclear
- **Severity:** medium
- **Description:** The agent encountered a KeyError when trying to access 'Average Temperature Normal' column in the climate normals DataFrame. The actual column name appears to be 'Average Temperature'. This naming is ambiguous because it doesn't clearly indicate it's the normal/climate value rather than an observed value.
- **Suggestion:** Update SKILL.md or references/ to explicitly document the exact column names returned by get_single_station_climate_normals(). Add a gotcha entry: 'Climate normals DataFrame uses column name "Average Temperature" (not "Average Temperature Normal") for the 30-year normal value. This can be confusing since the function returns normals, not observations.'
- **Pointer:** `SKILL.md - get_single_station_climate_normals section`

#### Missing recipe for climate normals/departures questions

- **Category:** missing_function
- **Severity:** low
- **Description:** The agent had to figure out which functions to combine for answering a climate normals departure question. While it succeeded, there's no explicit recipe showing the pattern for this common question type.
- **Suggestion:** Add a recipe to recipes.md showing the workflow for 'deviation from normal' questions: (1) find_best_station, (2) get_single_station_departures OR (3) get_single_station_acis_data + get_single_station_climate_normals. Include a code snippet showing how to access the correct column names.
- **Pointer:** `recipes.md`

### What Worked

- Agent successfully recovered from the KeyError by retrying with the correct column name, demonstrating good error handling
- Agent used appropriate API functions for the task: find_best_station, get_single_station_departures, get_single_station_acis_data, and get_single_station_climate_normals
- The final answer was well-structured, providing the deviation (+0.6°F), observed value (92.0°F), normal value (91.4°F), and data quality note
- Agent correctly identified station KPHX for Phoenix
- The error recovery mechanism (retries) worked as intended

---

## Query 5: What was the maximum snow depth recorded at LaGuardia Airport (KLGA) on February 29th, 2016?

**Category:** edge-case time period
**Difficulty:** hard
**Status:** error_unrecovered
**Answer Quality:** incorrect

### Issues

#### Incorrect Answer - Snow Depth on Feb 29, 2016

- **Category:** data_quality
- **Severity:** critical
- **Description:** The agent reported 0 inches of snow depth at KLGA on February 29, 2016, but this date was during a major Northeast blizzard that deposited 20+ inches of snow in NYC. The maximum snow depth should NOT be 0 inches. The agent either received incorrect data from the API, misinterpreted the data, or queried the wrong parameters.
- **Suggestion:** 1. Add a recipe for querying historical snow depth data with a known test case (e.g., this exact date). 2. Add validation logic to cross-check extreme weather dates against known storm events. 3. Review the API implementation to ensure snow depth (snow on ground) is being queried correctly, not confused with snowfall (snow that fell).
- **Pointer:** `SKILL.md - missing recipe for historical snow depth queries`

#### Possible Leap Year Date Edge Case Bug

- **Category:** other
- **Severity:** high
- **Description:** The query category is labeled 'edge-case time period' and February 29 is a leap year date. There may be a bug in date parsing or API parameter formatting for leap year dates that caused incorrect data to be returned.
- **Suggestion:** 1. Add a gotcha entry in SKILL.md about leap year dates (Feb 29) as edge cases. 2. Add test cases for leap year dates in the skill documentation. 3. Verify the API handles leap year dates correctly in the date parameter format.
- **Pointer:** `SKILL.md - missing gotcha for leap year dates`

#### Snow Depth vs Snowfall Confusion

- **Category:** skill_doc_unclear
- **Severity:** medium
- **Description:** The agent's answer mentions 'no snowfall' but the question asked for 'snow depth' (snow on the ground). These are different meteorological measurements. The documentation may not clearly distinguish between these two data types or explain which API parameters return which measurement.
- **Suggestion:** 1. Add a clarification in SKILL.md or references/ explaining the difference between snow depth (snow on ground) and snowfall (snow that fell on a given day). 2. Add a table or example showing which API parameters correspond to which measurements. 3. Add a recipe example that specifically queries for snow depth on a date with known snowfall.
- **Pointer:** `references/ - missing clarification on snow depth vs snowfall`

### What Worked

- Agent correctly identified and used station code KLGA for LaGuardia Airport
- Agent used the appropriate API function (xmacis2py.get_single_station_acis_data) for single station historical data queries
- Agent provided a complete, structured response with temperature and precipitation context
- Agent reported no errors, suggesting the API call completed successfully (even if the data was wrong)
- Agent's output format was clean and well-structured

---

## Consolidated Issues

| Title | Category | Severity | Suggestion |
|-------|----------|----------|------------|
| Function name confusion: number_of_days_above vs number_of_days_above_value | skill_doc_unclear | medium | Add a clear recipe in recipes.md for 'threshold count' queries that explicitly s... |
| Agent required retry to find correct function | agent_confusion | low | Consider adding function aliases or deprecation warnings in the code if 'number_... |
| Climate normals returned incomplete monthly data | data_quality | medium | Add a gotcha to SKILL.md noting that climate normals may not always return all 1... |
| monthly_totals_by_year failed with backfill station spec format | wrong_api_usage | high | Add a gotcha entry explaining the difference between station specification forma... |
| Table row key confusion: 'value' vs 'total' | wrong_api_usage | medium | Update the API reference documentation to include exact example return values wi... |
| Column name mismatch in climate normals DataFrame | skill_doc_unclear | medium | Update SKILL.md or references/ to explicitly document the exact column names ret... |
| Missing recipe for climate normals/departures questions | missing_function | low | Add a recipe to recipes.md showing the workflow for 'deviation from normal' ques... |
| Incorrect Answer - Snow Depth on Feb 29, 2016 | data_quality | critical | 1. Add a recipe for querying historical snow depth data with a known test case (... |
| Possible Leap Year Date Edge Case Bug | other | high | 1. Add a gotcha entry in SKILL.md about leap year dates (Feb 29) as edge cases. ... |
| Snow Depth vs Snowfall Confusion | skill_doc_unclear | medium | 1. Add a clarification in SKILL.md or references/ explaining the difference betw... |
