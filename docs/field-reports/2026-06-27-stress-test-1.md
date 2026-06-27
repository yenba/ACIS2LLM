# Stress Test Batch 1

**Date:** 2026-06-27
**Type:** Automated edge-case stress test
**Queries tested:** 5
**Status:** Issues found

---

## Results Summary

| # | Query | Category | Difficulty | Status | Answer Quality |
|---|-------|----------|------------|--------|----------------|
| 1 | What was the average temperature in Fargo over the holidays,... | single-period stat (avg/max/min for a specific month or date range) | easy | wrong_answer | incorrect |
| 2 | What was the absolute wettest spring ever recorded in Seattl... | cross-year ranking (hottest/coldest/wettest/driest month or season ever) | medium | error_recovered | correct |
| 3 | Which city was actually hotter last July: Phoenix, Las Vegas... | multi-station comparison (compare 2-3 cities) | medium | wrong_answer | incorrect |
| 4 | What's the most snow Denver (KDEN) has ever gotten on a leap... | edge-case time period (partial month, current year, leap year Feb 29) | hard | error_unrecovered | incorrect |
| 5 | I'm trying to settle a bet. Did it ever get above freezing i... | unusual phrasing (colloquial, indirect, multi-part question) | hard | error_recovered | correct |

## Query 1: What was the average temperature in Fargo over the holidays, specifically from December 15, 2022 to January 15, 2023?

**Category:** single-period stat (avg/max/min for a specific month or date range)
**Difficulty:** easy
**Status:** wrong_answer
**Answer Quality:** incorrect

### Issues

#### Agent failed to fetch weather data and hallucinated answer

- **Category:** wrong_api_usage
- **Severity:** critical
- **Description:** The agent called `find_best_station` and `fetch_stations` but never called a function to retrieve actual weather data (e.g., `StnData`, `fetch_weather_data`, or equivalent) for the requested date range. Consequently, the agent hallucinated the average temperature of 6.64°F.
- **Suggestion:** Add a clear end-to-end recipe in `recipes.md` for 'single-period stat' queries that explicitly demonstrates the two-step process: first finding the station ID, and then passing that ID to the correct data-fetching function to get temperature data.

#### Agent confused `fetch_stations` with a data-fetching function

- **Category:** agent_confusion
- **Severity:** medium
- **Description:** The agent called `fetch_stations` after `find_best_station`. It likely thought `fetch_stations` would return the historical weather observations for the station, not realizing it only returns station metadata.
- **Suggestion:** Update the docstring for `fetch_stations` (and in `SKILL.md`) to explicitly state: 'Returns station metadata ONLY. Does NOT return weather observations, temperatures, or climate data.' If possible, rename the function to `fetch_station_metadata` to avoid ambiguity.

### What Worked

- The agent successfully used `find_best_station` to resolve the location 'Fargo' to a valid station identifier ('KFAR+215586').
- The agent correctly understood the date range (Dec 15, 2022 to Jan 15, 2023) and formatted its final output without syntax errors.

---

## Query 2: What was the absolute wettest spring ever recorded in Seattle?

**Category:** cross-year ranking (hottest/coldest/wettest/driest month or season ever)
**Difficulty:** medium
**Status:** error_recovered
**Answer Quality:** correct

### Issues

#### Hallucinated parameter var/variable

- **Category:** wrong_api_usage
- **Severity:** medium
- **Description:** The agent assumed a parameter named `var` or `variable` existed for specifying the weather variable (e.g., precipitation), leading to a TypeError. This is a common LLM hallucination when guessing API parameters.
- **Suggestion:** Highlight the correct parameter name (e.g., `elements` or `elems`) prominently in the SKILL.md and docstrings. Add a explicit "Gotcha" warning the agent not to invent parameter names like `var` or `variable`.

#### KeyError 'data' on threaded station without dates

- **Category:** doc_gap
- **Severity:** medium
- **Description:** Running `seasonal_summary` on a threaded/backfilled station (KBFI+24281) without explicit date bounds returned an object missing the 'data' key, causing a KeyError. The API or docs do not make it clear how to handle date defaults for threaded stations.
- **Suggestion:** Update the `seasonal_summary` documentation to explicitly state that date bounds (e.g., `start_date`, `end_date`) are required or highly recommended when querying threaded stations. Additionally, the underlying code should ideally raise a descriptive `ValueError` (e.g., "Missing dates for threaded station") rather than returning a malformed dict without a 'data' key.

#### KeyError 'Precipitation' on empty stations

- **Category:** agent_confusion
- **Severity:** low
- **Description:** The agent assumed that the 'Precipitation' key would always be present in the returned data, leading to a KeyError when querying a station (Portage Bay) that was empty or lacked that specific variable.
- **Suggestion:** Add a best-practice note in `recipes.md` instructing agents to check for column existence (e.g., using `.get('Precipitation')` or `if 'Precipitation' in data`) before accessing variables, since not all stations track all weather elements.

### What Worked

- The agent successfully used `find_best_station` to discover not only the primary airport station (KSEA) but also older threaded records (KBFI+24281) to ensure it checked the absolute longest period of record.
- The agent correctly compared multiple stations to verify the absolute wettest spring, which is the correct methodology for this type of query.
- The agent demonstrated excellent resilience, successfully recovering from three different errors over 5 retries to arrive at a highly accurate and comprehensive answer.

---

## Query 3: Which city was actually hotter last July: Phoenix, Las Vegas, or KLAX?

**Category:** multi-station comparison (compare 2-3 cities)
**Difficulty:** medium
**Status:** wrong_answer
**Answer Quality:** incorrect

### Issues

#### Hallucinated observation data

- **Category:** agent_confusion
- **Severity:** high
- **Description:** The agent called `fetch_stations`, which typically only returns station metadata (names, IDs, coordinates), but then it answered with specific historical temperature averages. Since it didn't call any observation/data endpoint (like `fetch_data` or `StnData`), it hallucinated the weather values.
- **Suggestion:** Update the skill documentation to explicitly distinguish between metadata functions (finding stations) and data functions (fetching observations). Add a clear warning: "Do not guess or hallucinate weather data. You must call [Data Function] to get actual temperatures."

#### Invalid multiple-station parameter format

- **Category:** wrong_api_usage
- **Severity:** medium
- **Description:** The agent passed a comma-separated string `"KPHX, KLAS, KLAX"` to the `station` parameter. If the API expects a single station ID per call, or a proper JSON array `["KPHX", "KLAS", "KLAX"]`, this usage is invalid.
- **Suggestion:** Clarify the parameter types in the docstrings/OpenAPI spec. If the API only supports one station at a time, add a recipe demonstrating how to loop over multiple stations to do a comparison.

### What Worked

- Correctly resolved "Phoenix" to KPHX and "Las Vegas" to KLAS
- Understood the intent of comparing average/max temperatures for a specific time period ("last July")

---

## Query 4: What's the most snow Denver (KDEN) has ever gotten on a leap day?

**Category:** edge-case time period (partial month, current year, leap year Feb 29)
**Difficulty:** hard
**Status:** error_unrecovered
**Answer Quality:** incorrect

### Issues

#### Agent hallucinated weather data without fetching it

- **Category:** agent_confusion
- **Severity:** critical
- **Description:** The agent provided a specific historical weather answer (0.0 inches for KDEN, 1.8 inches for Central Park) but the `functions_used` list shows it never called a data-fetching function (like `get_daily_data`). The agent hallucinated the final answer after successfully finding the stations.
- **Suggestion:** Add a strict instruction in `SKILL.md` emphasizing that agents MUST call data retrieval functions to answer historical weather queries, and that station metadata does not contain actual weather records.

#### Unhandled JSONDecodeError/AttributeError

- **Category:** api_error
- **Severity:** high
- **Description:** The agent encountered `JSONDecodeError` and `AttributeError`. This typically happens if the agent sends malformed parameters causing the API to return a non-JSON error page (like a 400 or 500 HTML response), or if the agent misuses a Python helper function and tries to parse its return value as a JSON string when it is already a dictionary/object.
- **Suggestion:** Improve error handling in the `acis2llm` wrappers to catch `JSONDecodeError` and return a clean, descriptive text error to the agent (e.g., 'API returned an invalid response, check parameters').

#### Missing recipe for day-of-year specific queries (Leap Day)

- **Category:** doc_gap
- **Severity:** medium
- **Description:** The query asks for 'leap day' (Feb 29) records across all years. The agent might not know how to efficiently query this—whether to fetch all historical daily data and filter locally, or if there is a specific ACIS summary/smry endpoint feature to use. This confusion could have contributed to its failure to fetch data.
- **Suggestion:** Add a concrete recipe in `recipes.md` demonstrating how to fetch and filter records for a specific day of the year (e.g., Leap Day or holidays) across a long historical period.

### What Worked

- The agent successfully used `fetch_stations` and `find_best_station` to identify the correct station identifiers (KDEN, 052220, 03017).
- The agent demonstrated good semantic understanding of the domain by recognizing the distinction between KDEN (Denver International) and the older Denver Central Park station.

---

## Query 5: I'm trying to settle a bet. Did it ever get above freezing in ZIP code 04736 during January 2000, or was it freezing cold every single day?

**Category:** unusual phrasing (colloquial, indirect, multi-part question)
**Difficulty:** hard
**Status:** error_recovered
**Answer Quality:** correct

### Issues

#### Unclear return data structure (List of Lists vs Dict)

- **Category:** doc_gap
- **Severity:** medium
- **Description:** The agent encountered TypeError and KeyError, likely because it incorrectly assumed `get_single_station_acis_data` returns a list of dictionaries (e.g., accessing data via `row['maxt']`) rather than the ACIS standard list of lists (e.g., `row[1]`). Agents often expect structured object records instead of positional arrays.
- **Suggestion:** Add a 'Gotchas' section in SKILL.md explicitly stating the return data shape is a list of lists. Provide a clear mapping of list indices to weather variables (e.g., index 0 is Date, index 1 is Max Temp). Include a code snippet in recipes.md demonstrating how to iterate over `response['data']` and access elements by index.

#### Missing documentation on handling 'M' and 'T' string values

- **Category:** skill_doc_unclear
- **Severity:** medium
- **Description:** Type errors during ACIS data processing are frequently caused by the agent attempting to cast string representations of missing ('M') or trace ('T') values directly to floats or integers. If the agent is unaware of these special characters, it will crash during data aggregation.
- **Suggestion:** Update the API documentation and recipes to explicitly document ACIS special values ('M' for missing, 'T' for trace, 'S' for subsequent). Provide an example function showing how to safely parse these values (e.g., filtering out 'M' and converting 'T' to 0.0) before numerical comparisons.

### What Worked

- The agent successfully understood the colloquially phrased, multi-part prompt and mapped ZIP code 04736 to Caribou, Maine (Station KCAR).
- The agent correctly extracted daily maximum temperatures and compared them against the freezing point (32°F) rather than relying on average temperatures.
- The agent successfully recovered from its initial KeyError and TypeError (likely by inspecting the actual return object and correcting its indexing code) and produced a factually correct answer.

---

## Consolidated Issues

| Title | Category | Severity | Suggestion |
|-------|----------|----------|------------|
| Agent failed to fetch weather data and hallucinated answer | wrong_api_usage | critical | Add a clear end-to-end recipe in `recipes.md` for 'single-period stat' queries t... |
| Agent confused `fetch_stations` with a data-fetching function | agent_confusion | medium | Update the docstring for `fetch_stations` (and in `SKILL.md`) to explicitly stat... |
| Hallucinated parameter var/variable | wrong_api_usage | medium | Highlight the correct parameter name (e.g., `elements` or `elems`) prominently i... |
| KeyError 'data' on threaded station without dates | doc_gap | medium | Update the `seasonal_summary` documentation to explicitly state that date bounds... |
| KeyError 'Precipitation' on empty stations | agent_confusion | low | Add a best-practice note in `recipes.md` instructing agents to check for column ... |
| Hallucinated observation data | agent_confusion | high | Update the skill documentation to explicitly distinguish between metadata functi... |
| Invalid multiple-station parameter format | wrong_api_usage | medium | Clarify the parameter types in the docstrings/OpenAPI spec. If the API only supp... |
| Agent hallucinated weather data without fetching it | agent_confusion | critical | Add a strict instruction in `SKILL.md` emphasizing that agents MUST call data re... |
| Unhandled JSONDecodeError/AttributeError | api_error | high | Improve error handling in the `acis2llm` wrappers to catch `JSONDecodeError` and... |
| Missing recipe for day-of-year specific queries (Leap Day) | doc_gap | medium | Add a concrete recipe in `recipes.md` demonstrating how to fetch and filter reco... |
| Unclear return data structure (List of Lists vs Dict) | doc_gap | medium | Add a 'Gotchas' section in SKILL.md explicitly stating the return data shape is ... |
| Missing documentation on handling 'M' and 'T' string values | skill_doc_unclear | medium | Update the API documentation and recipes to explicitly document ACIS special val... |
