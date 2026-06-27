# Stress Test Batch 1

**Date:** 2026-06-27
**Type:** Automated edge-case stress test
**Queries tested:** 5
**Status:** Issues found

---

## Results Summary

| # | Query | Category | Difficulty | Status | Answer Quality |
|---|-------|----------|------------|--------|----------------|
| 1 | What was the average high temperature in Denver during July ... | single-period stat | easy | error_recovered | correct |
| 2 | Has Fairbanks, Alaska ever gotten snow in June? How often do... | frequency of occurrence | medium | error_recovered | correct |
| 3 | I'm curious — which winter dumped the most snow on Buffalo, ... | snowfall or winter-specific query | medium | error_recovered | partially_correct |
| 4 | How many days did it get above 100°F in Phoenix last summer ... | multi-station comparison | hard | clean | correct |
| 5 | My zip code is 04401 — what's the oldest temperature data yo... | ambiguous or tricky location | hard | clean | correct |

## Query 1: What was the average high temperature in Denver during July 2023?

**Category:** single-period stat
**Difficulty:** easy
**Status:** error_recovered
**Answer Quality:** correct

### Issues

#### Import path confusion: dot-path vs 'from' import

- **Category:** skill_doc_unclear
- **Severity:** medium
- **Description:** The agent first tried to import xmacis2py.analysis using a dot-path import (e.g., 'import xmacis2py.analysis') which caused a ModuleNotFoundError. It had to retry using 'from xmacis2py import analysis'. This suggests the skill docs don't clearly specify the correct import pattern for submodules like 'analysis'.
- **Suggestion:** Add an explicit 'Import Patterns' section to SKILL.md or a gotcha entry that shows the correct import syntax for all submodules. For example: '# Correct: from xmacis2py import analysis\n# Correct: from xmacis2py.analysis import period_mean\n# May fail: import xmacis2py.analysis'. This would prevent the initial ModuleNotFoundError and save a retry.
- **Pointer:** `SKILL.md or references/analysis.md`

#### Missing recipe for basic single-period stat queries

- **Category:** doc_gap
- **Severity:** low
- **Description:** While the agent figured out the correct workflow (fetch → validate → compute), having an explicit recipe for 'average high/low temperature for a single month' would prevent the import error and ensure agents follow the optimal path on the first try.
- **Suggestion:** Add a recipe to recipes.md like: '## Average Temperature for a Single Month\n```python\nfrom xmacis2py import analysis\nfrom xmacis2py import get_single_station_acis_data\n\ndata = get_single_station_acis_data(station="KDEN", start_date="2023-07-01", end_date="2023-07-31", elements=["maxt"])\nmissing = analysis.number_of_missing_days(data, "maxt")\nmean = analysis.period_mean(data, "maxt")\n```'

### What Worked

- Agent correctly identified this as a single-period stat question and used the appropriate workflow: fetch data → check missing days → compute period mean
- Correct station selection (KDEN for Denver)
- Used xmacis2py.get_single_station_acis_data to fetch the raw data
- Used xmacis2py.analysis.number_of_missing_days to validate data completeness before reporting
- Used xmacis2py.analysis.period_mean to compute the average high temperature
- Final answer of 88.0°F is plausible for Denver in July 2023 and includes appropriate precision (both rounded and unrounded)
- Agent reported 0 missing days out of 31, showing good data quality awareness
- Agent successfully recovered from the import error on its own without user intervention

---

## Query 2: Has Fairbanks, Alaska ever gotten snow in June? How often does that actually happen?

**Category:** frequency of occurrence
**Difficulty:** medium
**Status:** error_recovered
**Answer Quality:** correct

### Issues

#### Parameter name mismatch: 'parameter' vs 'variable'

- **Category:** skill_doc_unclear
- **Severity:** medium
- **Description:** The agent reported that the frequency_of_occurrence and monthly_totals_by_year functions use 'parameter' as the argument name, but the skill docs apparently document it as 'variable'. This caused at least 2 retries before the agent figured out the correct parameter name.
- **Suggestion:** Audit the skill documentation (SKILL.md, references/, recipes.md) to ensure the parameter names match the actual function signatures. If the function accepts 'parameter', the docs should say 'parameter' not 'variable'. Add a gotcha entry: 'Note: The argument for specifying the weather element (e.g., snow, maxt) is called `parameter`, not `variable`, in frequency_of_occurrence and monthly_totals_by_year.'
- **Pointer:** `SKILL.md or references/ documentation for frequency_of_occurrence and monthly_totals_by_year`

#### Missing recipe for frequency-of-occurrence weather questions

- **Category:** doc_gap
- **Severity:** low
- **Description:** While the agent eventually succeeded, a recipe specifically for 'has X weather event ever happened in month Y at location Z' pattern would have made the process smoother and potentially avoided the retries.
- **Suggestion:** Add a recipe in recipes.md for the 'frequency of occurrence' pattern, e.g.: 'To determine how often a weather event occurs in an unusual month: 1) Use find_best_station to get station ID, 2) Use frequency_of_occurrence with parameter=snow/pcpn/etc and the target month, 3) Use monthly_totals_by_year to get specific amounts for years with non-zero values.' Include the correct parameter names explicitly.

### What Worked

- Agent correctly identified this as a frequency-of-occurrence question and used appropriate functions (frequency_of_occurrence, monthly_totals_by_year)
- Agent used find_best_station to identify two relevant stations (University Experimental Station 26441 and Fairbanks Intl Airport PAFA), providing a more comprehensive answer
- Agent provided specific years, amounts, and percentages - the answer is detailed and well-structured
- Agent correctly distinguished between trace and measurable snowfall, which is an important nuance for this type of question
- Agent successfully recovered from parameter naming errors (2 retries) and still produced a thorough, accurate answer
- The bottom-line summary is clear and directly answers the user's two-part question (has it happened? how often?)
- Agent used multiple stations to cross-validate findings and explained the discrepancy between them

---

## Query 3: I'm curious — which winter dumped the most snow on Buffalo, NY? Like, all-time snowiest winter on record.

**Category:** snowfall or winter-specific query
**Difficulty:** medium
**Status:** error_recovered
**Answer Quality:** partially_correct

### Issues

#### TypeError from using keyword arg instead of positional for seasonal_summary

- **Category:** skill_doc_unclear
- **Severity:** medium
- **Description:** The agent's first call to acis2llm.seasonal_summary failed because it used 'variable' as a keyword argument instead of a positional argument. The agent noted this in its summary: 'TypeError on first seasonal_summary call due to using keyword arg variable instead of positional'. This suggests the function signature or docs don't make it clear enough which parameters are positional vs keyword.
- **Suggestion:** In SKILL.md and/or the function docstrings, explicitly show example calls with positional arguments clearly labeled. Add a gotcha entry like: 'GOTCHA: seasonal_summary takes `variable` as a positional argument, not a keyword argument. Use `seasonal_summary("snow", ...)` not `seasonal_summary(variable="snow", ...)`'.
- **Pointer:** `SKILL.md or acis2llm.seasonal_summary docstring`

#### Answer accuracy is uncertain — 1976-77 snowiest winter figure may be wrong

- **Category:** data_quality
- **Severity:** medium
- **Description:** The agent claims Winter 1976-77 had 151.7 inches at KBUF. Various historical sources cite the 2001-02 winter (with ~82+ inches in a single December storm) or 2014-15 as contenders, and the Blizzard of '77 was notable more for wind/cold than total seasonal accumulation. The 199.4 inches figure for 1976-77 is sometimes cited from different stations or measurement periods. The answer of 151.7 inches for a Dec-Feb window may be correct for that specific station and seasonal definition, but the claim needs verification. The agent's use of Dec-Feb only (rather than Oct-Apr or Nov-Mar) may also miss significant early/late season snow, potentially changing the ranking.
- **Suggestion:** Document clearly in SKILL.md or recipes.md what seasonal window is used for 'winter' in seasonal_summary (e.g., Dec-Feb vs Oct-Apr), and note that different seasonal definitions can produce different 'snowiest winter' answers. Add a recipe for 'snowiest winter' queries that discusses this nuance.

#### Winter season definition may be too narrow (Dec-Feb only)

- **Category:** doc_gap
- **Severity:** medium
- **Description:** The agent used a Dec-Feb definition of winter, but Buffalo frequently receives significant snowfall in November, March, and even October and April (e.g., the famous October 2006 storm, the November 2014 lake-effect event with 7+ feet). A Dec-Feb window could significantly undercount total winter snowfall and produce misleading rankings.
- **Suggestion:** Add a recipe or gotcha noting that for snowfall queries, especially in lake-effect regions like Buffalo, the winter season should ideally span at least Nov-Mar or even Oct-Apr. Show how to configure seasonal_summary for custom date ranges if supported, or document the limitation clearly.

#### Station data coverage starts at 1944, missing earlier records

- **Category:** data_quality
- **Severity:** low
- **Description:** The agent reports 83 winters of data starting from 1944, but Buffalo has weather records going back much further. The 'all-time snowiest winter on record' claim is limited to the KBUF station's available data, which may not cover the full historical record. The agent did acknowledge this is 83 winters of data but still framed it as 'all-time.'
- **Suggestion:** Add a gotcha or note in SKILL.md that ACIS station data coverage varies and agents should qualify 'all-time' claims with the actual period of record. Suggest the agent note limitations like 'based on available data from 1944-present at KBUF.'

### What Worked

- The agent correctly identified and used acis2llm.find_best_station to locate the Buffalo station (KBUF)
- The agent used the appropriate function (acis2llm.seasonal_summary) for a seasonal snowfall query — this is the right tool for the job
- The agent successfully recovered from the TypeError on its first attempt and retried with the correct calling convention
- The agent provided good context including top 5 rankings, average snowfall, and explanation of the winter labeling convention
- The agent's summary section was well-structured with clear metadata about errors, retries, functions used, and station
- The agent correctly noted that 'Winter 1977' means Dec 1976 through Feb 1977, showing good understanding of seasonal labeling conventions
- The agent mentioned zero missing days for the top result, which is good data quality awareness

---

## Query 4: How many days did it get above 100°F in Phoenix last summer compared to Las Vegas and Tucson?

**Category:** multi-station comparison
**Difficulty:** hard
**Status:** clean
**Answer Quality:** correct

### Issues

#### Temporal ambiguity: 'last summer' interpreted as 2025 instead of 2024

- **Category:** agent_confusion
- **Severity:** medium
- **Description:** The user asked about 'last summer,' which depending on the current date likely means summer 2024 rather than summer 2025. The agent answered with 'summer 2025 (June 1 – August 31).' If the query was made before September 2025, summer 2025 would not yet be complete. If made after, 2025 could be correct as 'last summer.' However, for most reasonable interpretation windows, 'last summer' should refer to the most recently completed summer (2024). The data itself may still be accurate if the agent queried for the correct date range and the API returned valid data, but the labeling is potentially misleading.
- **Suggestion:** Add a gotcha or recipe note in SKILL.md about resolving temporal references like 'last summer,' 'last winter,' etc. The agent should determine the current date and select the most recently *completed* season. For example: 'last summer' before June 1, 2025 = summer 2024; 'last summer' after August 31, 2025 = summer 2025; during summer 2025 = ambiguous, prefer summer 2024.
- **Pointer:** `SKILL.md:gotchas or recipes.md`

#### Station selection retry logic worked well but could be documented

- **Category:** doc_gap
- **Severity:** low
- **Description:** The agent initially tried KLUF for Phoenix, encountered 3 missing days, and retried with KPHX which had 0 missing days. This is good behavior but the retry strategy (preferring stations with fewer missing days) isn't explicitly documented as a recommended pattern.
- **Suggestion:** Add a recipe or best practice in recipes.md for handling missing data: 'If a station returns significant missing data, try the next best station from find_best_station results. Prefer major airport stations (KPHX, KLAS, etc.) for recent data as they tend to have fewer gaps.'
- **Pointer:** `recipes.md`

### What Worked

- Multi-station comparison pattern executed correctly: agent queried three separate stations and compared results, which is the right approach for this query category.
- Correct use of find_best_station to identify appropriate weather stations for each city (KPHX, KLAS, KTUS).
- Proper use of the analysis.number_of_days_above_value function for threshold counting — this is exactly the right function for 'how many days above X°F' questions.
- Good error recovery: agent detected missing data at KLUF and retried with KPHX, resulting in a complete dataset with 0 missing days.
- Clear, well-structured output with specific numbers, percentages, and comparative context.
- The summary section is well-formatted with ERRORS, RETRIES, FUNCTIONS_USED, and STATION fields — good observability.
- Agent correctly used 92 days as the denominator for June 1 – August 31, showing proper date range handling.
- The answer is plausible and consistent with known climate patterns (Phoenix > Las Vegas ≈ Tucson for extreme heat days).

---

## Query 5: My zip code is 04401 — what's the oldest temperature data you can pull up for here, and what was the coldest day ever recorded?

**Category:** ambiguous or tricky location
**Difficulty:** hard
**Status:** clean
**Answer Quality:** correct

### What Worked

- The agent correctly resolved ZIP code 04401 to Bangor, Maine and identified the appropriate weather station (KBGR) with historical backfill station (176430).
- The agent properly identified the oldest available data (August 1, 1893) by leveraging historical backfill station records, showing good understanding of the ACIS station merging/backfill concept.
- The agent correctly found the all-time coldest temperature record (-40°F on January 17, 1907), which is a plausible extreme cold record for Bangor, Maine.
- The agent went above and beyond by providing the top 5 coldest days, adding useful context to the answer.
- The agent used appropriate functions (find_best_station, fetch_stations) for this type of location-based historical query.
- The agent correctly handled the 'ambiguous or tricky location' aspect — ZIP codes can be tricky but 04401 maps cleanly to Bangor, and the agent resolved it without issues.
- The summary format is clean, well-structured, and includes all the metadata (station, functions used, errors, retries) needed for debugging.
- No errors were encountered and no retries were needed, indicating smooth execution.

---

## Consolidated Issues

| Title | Category | Severity | Suggestion |
|-------|----------|----------|------------|
| Import path confusion: dot-path vs 'from' import | skill_doc_unclear | medium | Add an explicit 'Import Patterns' section to SKILL.md or a gotcha entry that sho... |
| Missing recipe for basic single-period stat queries | doc_gap | low | Add a recipe to recipes.md like: '## Average Temperature for a Single Month\n```... |
| Parameter name mismatch: 'parameter' vs 'variable' | skill_doc_unclear | medium | Audit the skill documentation (SKILL.md, references/, recipes.md) to ensure the ... |
| Missing recipe for frequency-of-occurrence weather questions | doc_gap | low | Add a recipe in recipes.md for the 'frequency of occurrence' pattern, e.g.: 'To ... |
| TypeError from using keyword arg instead of positional for seasonal_summary | skill_doc_unclear | medium | In SKILL.md and/or the function docstrings, explicitly show example calls with p... |
| Answer accuracy is uncertain — 1976-77 snowiest winter figure may be wrong | data_quality | medium | Document clearly in SKILL.md or recipes.md what seasonal window is used for 'win... |
| Winter season definition may be too narrow (Dec-Feb only) | doc_gap | medium | Add a recipe or gotcha noting that for snowfall queries, especially in lake-effe... |
| Station data coverage starts at 1944, missing earlier records | data_quality | low | Add a gotcha or note in SKILL.md that ACIS station data coverage varies and agen... |
| Temporal ambiguity: 'last summer' interpreted as 2025 instead of 2024 | agent_confusion | medium | Add a gotcha or recipe note in SKILL.md about resolving temporal references like... |
| Station selection retry logic worked well but could be documented | doc_gap | low | Add a recipe or best practice in recipes.md for handling missing data: 'If a sta... |
