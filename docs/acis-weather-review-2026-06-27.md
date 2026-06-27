# acis-weather Skill & acis2llm Module Review

**Date:** 2026-06-27
**Trigger Query:** "have there been any rain related records in lexington this spring/early summer?"
**Station:** KLEX (Lexington, KY)
**Reviewers:** Session agent + Opus 4.8 subagent review

---

## Executive Summary

The query surfaced one real capability gap (calendar-date record checking), one recurring agent error (pandas boolean precedence), and several documentation improvements. One initially-identified issue was already documented in the skill and requires no action.

---

## Priority 1: Calendar-Date Record Helper

**Gap:** No function to check "is this value a record for this calendar date?"

**What happened:** The core question was "any rain records?" Answering required checking if 3.45" on June 9 is a record for June 9 across all years. The agent had to:
1. Fetch 126 years of daily data
2. Filter to `Month == 6 & Day == 9`
3. Sort descending and check rank

This pattern repeated for each notable date (June 9, June 22, June 18, June 26).

**Why existing tools don't cover it:**
- `period_rankings` ranks rows *within* a DataFrame, not same-calendar-date across years
- Composites aggregate by *month* or *season*, not by specific day-of-year
- No `acis2llm` or `xmacis2py.analysis` function groups by month+day and ranks historically

**Proposed function:**

```python
def calendar_date_records(
    station: str,
    month: int,
    day: int,
    parameter: str,
    n: int = 5,
    start_year: int | None = None,
    end_year: int | None = None,
) -> dict:
    """Rank a specific calendar date across all years on record.

    Returns a dict with:
      - current_value: float       # this year's value (or None)
      - current_rank: int          # 1 = highest
      - is_record: bool            # True if rank == 1
      - top_n: list[dict]          # top N years with year, value
      - total_years: int           # years with data for this date
    """
```

**Edge cases to handle:**
- Leap year Feb 29 (skip non-leap years)
- Partial current year (flag if current year's value is present)
- Place in `acis2llm.composites`, export from `__init__.py`

**Review verdict:** Well-motivated, well-scoped. Follows existing composite pattern. Fetch cost is acceptable (same as other composites).

---

## Priority 2: Pandas Boolean Precedence Gotcha

**Error hit:**

```python
# BROKE:
june9 = spring_summer[spring_summer['Month'] == 6 & spring_summer['Day'] == 9]
# ValueError: The truth value of a Series is ambiguous.

# FIXED:
june9 = spring_summer[(spring_summer['Month'] == 6) & (spring_summer['Day'] == 9)]
```

**Why it matters:** `&` has higher precedence than `==` in Python. Agents consistently miss this when writing multi-condition DataFrame filters. The skill doc has no example of parenthesized boolean conditions.

**Fix:** Add a gotcha entry in SKILL.md:

```
| Multi-condition DataFrame filter | Always wrap each condition in parentheses:
   `df[(df['Month'] == 6) & (df['Day'] == 9)]`.
   `&` binds tighter than `==` in Python. |
```

---

## Priority 3: Climate Normals Gotcha

**Error hit:** `get_single_station_climate_normals(KLEX, interval="monthly")` returned only May and June -- 2 of 12 months.

**Root cause:** The function defaults `end_date` to yesterday and returns only months within the `start_date`/`end_date` window. Without explicit date bounds, it may return a narrow slice.

**Fix:** Add gotcha entry:

```
| Climate normals returned fewer than 12 months | Pass explicit start_date/end_date
   covering at least one full year, e.g. start_date="2020-01-01",
   end_date="2020-12-31". The default end_date=_yesterday may clip
   results if start_date is not also set. |
```

**Better alternative:** `xmacis2py.analysis.calculate_daily_normals` computes custom normals from a DataFrame without upstream smoothing. Useful for custom climatologies (e.g., a 50-year window) and calendar-date context ("what's the average for June 9 across 30 years?"). This function is documented in the analysis reference but not surfaced in the skill's decision tree or mental model.

---

## Priority 4: Record-Check Recipe

**Gap:** The recipes doc covers: hottest month, threshold counts, top-N seasons, freeze frequency, multi-city compare, long-record backfill, plotting. None cover "is this a record for this date?" -- the exact query shape that triggered this review.

**Fix:** Add a recipe that walks through the manual pattern (fetch long record, filter by month+day, rank) as a stopgap until the `calendar_date_records` helper is implemented. This recipe doubles as the implementation spec for the helper.

---

## Priority 5: Partial-Month Detection

**Issue:** When the current month isn't over, composites and manual rankings don't distinguish "not yet observed" from "truly missing data." The agent had to manually note partial months, project full-month totals, and flag them in rankings.

**Fix (code):** Add a cheap `partial` boolean flag in composite table rows by comparing observed days to `calendar.monthrange()`. One-line addition that surfaces the issue in the return shape.

**Fix (doc):** Note in the skill that partial months should be flagged and projected: `partial_total / observed_days * calendar.monthrange(year, month)[1]`.

---

## No Action Required

### `get_single_station_acis_data` has no `parameter` arg

The agent opened with `parameter="prcp"` and got a `TypeError`. This is **already documented** in the skill's gotchas table (line 72):

> There is **no `variables=` / `variable=` parameter**. The function always returns all columns; filter the DataFrame yourself.

The agent hit it despite the warning -- this is an agent compliance issue, not a documentation gap. The variable codes table shows short codes (`prcp`, `tmax`) used by `acis2llm` composites; agents incorrectly generalize them to raw fetch calls. Adding redundant examples would be noise.

### `xmacis2py.analysis` functions didn't map to the query

The agent didn't use any `xmacis2py.analysis` functions because `period_rankings` ranks rows within a DataFrame, not cross-year same-calendar-date. This is a validation point that confirms the calendar-date records gap is real, not a separate issue.

---

## Final Priority Order

| # | Issue | Type | Status |
|---|-------|------|--------|
| 1 | Calendar-date record helper | Code + doc | Proposed |
| 2 | Pandas boolean precedence gotcha | Doc | Proposed |
| 3 | Climate normals date-range gotcha | Doc | Proposed |
| 4 | Record-check recipe | Doc | Proposed |
| 5 | Partial-month detection | Code + doc | Proposed |
| 6 | No `parameter` arg | -- | Already documented |
| 7 | Analysis functions gap | -- | Validation only |
