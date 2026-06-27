"""Composite climate analyses built on top of xmACIS2Py.

Each public function fetches ACIS data and returns a structured result with a
``table`` (per-year rows) and a ``summary`` string. These are higher-level than
the per-period statistics in ``xmacis2py.analysis``.
"""

import calendar
from datetime import datetime

import numpy as np
import pandas as pd


from acis2llm.geocoding import get_station_start_year
from acis2llm.multi_station import fetch_stations
import functools

def _handle_variable_alias(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        if 'variable' in kwargs:
            if 'parameter' in kwargs:
                raise TypeError("got multiple values for argument 'parameter'")
            kwargs['parameter'] = kwargs.pop('variable')
        return func(*args, **kwargs)
    return wrapper



VARIABLE_COLUMN_MAP = {
    "tmax": "Maximum Temperature",
    "tmin": "Minimum Temperature",
    "tavg": "Average Temperature",
    "prcp": "Precipitation",
    "snow": "Snowfall",
    "awdb": "Average Daily Water Balance",
    "hdd": "Heating Degree Days",
    "cdd": "Cooling Degree Days",
    "gdd": "Growing Degree Days",
    "snow_depth": "Snow Depth",
    "tdpa": "Average Temperature Departure",
}

_MONTH_NAMES = {name.lower(): num for num, name in enumerate(calendar.month_name) if num}
_MONTH_ABBRS = {name.lower(): num for num, name in enumerate(calendar.month_abbr) if num}

_SEASON_MAP = {
    "winter": [12, 1, 2],
    "spring": [3, 4, 5],
    "summer": [6, 7, 8],
    "fall": [9, 10, 11],
    "autumn": [9, 10, 11],
}


def _parse_month(month_input):
    if isinstance(month_input, int):
        if 1 <= month_input <= 12:
            return month_input
        raise ValueError(f"Month must be between 1 and 12, got {month_input}")

    s = str(month_input).strip().lower()
    try:
        n = int(s)
        if 1 <= n <= 12:
            return n
        raise ValueError(f"Month must be between 1 and 12, got {n}")
    except ValueError:
        if s.isdigit() or (s.startswith("-") and s[1:].isdigit()):
            raise

    if s in _MONTH_NAMES:
        return _MONTH_NAMES[s]
    if s in _MONTH_ABBRS:
        return _MONTH_ABBRS[s]
    raise ValueError(f"Could not parse month: '{month_input}'")


def _get_season_months(season):
    key = season.strip().lower()
    if key not in _SEASON_MAP:
        raise ValueError(f"Unknown season: '{season}'. Use winter, spring, summer, fall, or autumn.")
    return _SEASON_MAP[key]


def _assign_season_year(date, season_months):
    """Assign a date to its season-year. Winter Dec belongs to the *next* calendar year."""
    if 12 in season_months and date.month == 12:
        return date.year + 1
    return date.year


def _aggregate_monthly_by_year(df, column, month, aggregation="sum",
                                start_year=None, end_year=None):
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df["_month"] = df["Date"].dt.month
    df["_year"] = df["Date"].dt.year

    filtered = df[df["_month"] == month].copy()
    if start_year is not None:
        filtered = filtered[filtered["_year"] >= start_year]
    if end_year is not None:
        filtered = filtered[filtered["_year"] <= end_year]

    if filtered.empty:
        return {"table": [], "summary": f"No data found for {calendar.month_name[month]}."}

    filtered[column] = pd.to_numeric(filtered[column], errors="coerce")
    agg_func = {"sum": "sum", "mean": "mean", "max": "max", "min": "min"}[aggregation]
    grouped = filtered.groupby("_year").agg(
        value=(column, agg_func),
        missing_days=(column, lambda x: x.isna().sum()),
        obs_count=(column, "count"),
    ).reset_index()

    table = []
    for _, row in grouped.iterrows():
        val = row["value"]
        table.append({
            "year": int(row["_year"]),
            "value": round(float(val), 2) if pd.notna(val) else None,
            "missing_days": int(row["missing_days"]),
            "partial": int(row["obs_count"]) < calendar.monthrange(int(row["_year"]), month)[1],
        })

    month_name = calendar.month_name[month]
    values = [r["value"] for r in table if r["value"] is not None]
    summary_parts = [f"{month_name} {column} ({aggregation}) across {len(table)} years ({table[0]['year']}-{table[-1]['year']})"]
    if values:
        summary_parts.append(f"Average: {np.mean(values):.2f}")
        summary_parts.append(f"Median: {np.median(values):.2f}")
        summary_parts.append(f"Max: {np.max(values):.2f}")
        summary_parts.append(f"Min: {np.min(values):.2f}")

    return {"table": table, "summary": ", ".join(summary_parts)}


def _aggregate_seasonal_by_year(df, column, season_months, aggregation="sum",
                                 start_year=None, end_year=None):
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df["_month"] = df["Date"].dt.month
    df["_season_year"] = df["Date"].apply(lambda d: _assign_season_year(d, season_months))

    filtered = df[df["_month"].isin(season_months)].copy()
    if start_year is not None:
        filtered = filtered[filtered["_season_year"] >= start_year]
    if end_year is not None:
        filtered = filtered[filtered["_season_year"] <= end_year]

    if filtered.empty:
        return {"table": [], "summary": "No data found for the specified season and years."}

    filtered[column] = pd.to_numeric(filtered[column], errors="coerce")
    agg_func = {"sum": "sum", "mean": "mean", "max": "max", "min": "min"}[aggregation]
    grouped = filtered.groupby("_season_year").agg(
        value=(column, agg_func),
        missing_days=(column, lambda x: x.isna().sum()),
        obs_count=(column, "count"),
    ).reset_index()

    # Drop partial seasons (require ~20 days per month)
    min_days = len(season_months) * 20
    grouped = grouped[grouped["obs_count"] >= min_days]

    table = []
    for _, row in grouped.iterrows():
        val = row["value"]
        table.append({
            "year": int(row["_season_year"]),
            "value": round(float(val), 2) if pd.notna(val) else None,
            "missing_days": int(row["missing_days"]),
        })

    if not table:
        return {"table": [], "summary": "No complete seasons found."}

    values = [r["value"] for r in table if r["value"] is not None]
    summary_parts = [f"Seasonal {column} ({aggregation}) across {len(table)} years ({table[0]['year']}-{table[-1]['year']})"]
    if values:
        summary_parts.append(f"Average: {np.mean(values):.2f}")
        summary_parts.append(f"Median: {np.median(values):.2f}")
        summary_parts.append(f"Max: {np.max(values):.2f}")
        summary_parts.append(f"Min: {np.min(values):.2f}")

    return {"table": table, "summary": ", ".join(summary_parts)}


def _calculate_frequency(df, column, threshold, comparison, month=None, season=None,
                          start_year=None, end_year=None):
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df["_month"] = df["Date"].dt.month

    if month:
        df["_year"] = df["Date"].dt.year
        target_months = [month]
    else:
        season_months = _get_season_months(season)
        df["_year"] = df["Date"].apply(lambda d: _assign_season_year(d, season_months))
        target_months = season_months

    filtered = df[df["_month"].isin(target_months)].copy()
    if start_year:
        filtered = filtered[filtered["_year"] >= start_year]
    if end_year:
        filtered = filtered[filtered["_year"] <= end_year]

    if filtered.empty:
        return {"error": "No data found for the specified period."}

    filtered[column] = pd.to_numeric(filtered[column], errors="coerce")

    comparison_aliases = {
        ">": "above", "above": "above",
        ">=": "at_or_above", "at_or_above": "at_or_above",
        "<": "below", "below": "below",
        "<=": "at_or_below", "at_or_below": "at_or_below",
    }
    canonical = comparison_aliases.get(comparison)
    if canonical is None:
        raise ValueError(
            f"Unknown comparison: {comparison!r}. "
            "Use one of: 'above' / '>', 'at_or_above' / '>=', "
            "'below' / '<', 'at_or_below' / '<='."
        )
    comparisons = {
        "above": lambda s: s > threshold,
        "at_or_above": lambda s: s >= threshold,
        "below": lambda s: s < threshold,
        "at_or_below": lambda s: s <= threshold,
    }
    filtered["_match"] = comparisons[canonical](filtered[column])

    extreme_func = "min" if canonical in ("below", "at_or_below") else "max"
    grouped = filtered.groupby("_year").agg(
        days_matched=("_match", "sum"),
        total_days=("_match", "count"),
        mean_value=(column, "mean"),
        extreme_value=(column, extreme_func),
        missing_days=(column, lambda x: x.isna().sum()),
    ).reset_index()

    grouped = grouped[grouped["missing_days"] <= grouped["total_days"] * 0.1]

    # Drop partial boundary seasons. A season window (e.g. winter = Dec-Feb)
    # fetched over a multi-year span picks up a leading fragment (Jan/Feb of
    # the first year, with no preceding December) and a trailing fragment
    # (December of the final year, with no following Jan/Feb). Counting those
    # as full "years" inflates the denominator in the X-of-N summary. Require
    # ~20 days per season month, mirroring _aggregate_seasonal_by_year.
    if season is not None:
        min_days = len(target_months) * 20
        grouped = grouped[grouped["total_days"] >= min_days]

    if grouped.empty:
        return {"error": "No years with sufficient data found."}

    years_with = (grouped["days_matched"] > 0).sum()
    total = len(grouped)
    pct = (years_with / total) * 100

    table = []
    for _, row in grouped.iterrows():
        ev = row["extreme_value"]
        mv = row["mean_value"]
        table.append({
            "year": int(row["_year"]),
            "days_met": int(row["days_matched"]),
            "mean_value": round(float(mv), 3) if pd.notna(mv) else None,
            "extreme_value": round(float(ev), 3) if pd.notna(ev) else None,
            "met_condition": bool(row["days_matched"] > 0),
        })

    period_desc = calendar.month_name[month] if month else season
    summary = (
        f"In {period_desc}, {column} was {comparison} {threshold} "
        f"in {years_with} out of {total} years ({pct:.1f}%)."
    )

    return {
        "count": int(years_with),
        "total_years": int(total),
        "percentage": round(float(pct), 1),
        "table": table,
        "summary": summary,
    }


def _resolve_year_window(station, start_year, end_year):
    first = start_year if start_year is not None else get_station_start_year(station)
    last = end_year if end_year is not None else pd.Timestamp.now().year
    return first, last


@_handle_variable_alias
def frequency_of_occurrence(station, parameter, threshold, comparison,
                             month=None, season=None, start_year=None, end_year=None):
    """How often (across years) a daily threshold is met in a given month or season.

    Provide exactly one of ``month`` or ``season``.

    `comparison` accepts ``"above"`` / ``">"``, ``"at_or_above"`` / ``">="``,
    ``"below"`` / ``"<"``, or ``"at_or_below"`` / ``"<="``.

    Returns a dict (NOT a DataFrame):
        {
            "count": int,           # years where threshold was met at all
            "total_years": int,
            "percentage": float,    # 0-100
            "table": [{"year": int, "days_met": int,
                       "mean_value": float|None, "extreme_value": float|None,
                       "met_condition": bool}, ...],
            "summary": str,
        }

    `days_met` is the count of days the threshold was met that year (sort by
    this to find the worst year). `extreme_value` is the most-extreme observed
    value that year (e.g. coldest temp for `"at_or_below"`), NOT a count.
    """
    if month is None and season is None:
        raise ValueError(
            "Pass either month=<1-12 or month name> or "
            "season=<'winter'|'spring'|'summer'|'fall'>."
        )
    if month is not None and season is not None:
        raise ValueError("Provide 'month' or 'season', not both.")

    column = VARIABLE_COLUMN_MAP.get(parameter, parameter)
    first_year, last_year = _resolve_year_window(station, start_year, end_year)

    if month is not None:
        month_num = _parse_month(month)
        last_day = calendar.monthrange(last_year, month_num)[1]
        start_date = f"{first_year}-{month_num:02d}-01"
        end_date = f"{last_year}-{month_num:02d}-{last_day:02d}"
        df = fetch_stations(station, start_date=start_date, end_date=end_date)
        return _calculate_frequency(df, column, threshold, comparison,
                                     month=month_num,
                                     start_year=start_year, end_year=end_year)

    season_months = _get_season_months(season)
    if 12 in season_months and 1 in season_months:
        feb_last = calendar.monthrange(last_year, 2)[1]
        start_date = f"{first_year - 1}-12-01"
        end_date = f"{last_year}-02-{feb_last:02d}"
    else:
        first_month = min(season_months)
        last_month = max(season_months)
        last_day = calendar.monthrange(last_year, last_month)[1]
        start_date = f"{first_year}-{first_month:02d}-01"
        end_date = f"{last_year}-{last_month:02d}-{last_day:02d}"

    df = fetch_stations(station, start_date=start_date, end_date=end_date)
    return _calculate_frequency(df, column, threshold, comparison,
                                 season=season,
                                 start_year=start_year, end_year=end_year)


@_handle_variable_alias
def seasonal_summary(station, parameter, season, start_year=None, end_year=None,
                      aggregation="sum"):
    """Aggregate a variable across a meteorological season, year by year.

    Winter is Dec–Feb and is labeled by the *ending* year (Dec 2023 → Winter 2024).
    `aggregation` is one of "sum", "mean", "max", "min".

    Returns a dict (NOT a DataFrame):
        {
            "table": [{"year": int, "value": float|None, "missing_days": int}, ...],
            "summary": str,
        }
    """
    season_months = _get_season_months(season)
    column = VARIABLE_COLUMN_MAP.get(parameter, parameter)
    first_year, last_year = _resolve_year_window(station, start_year, end_year)

    if 12 in season_months and 1 in season_months:
        feb_last = calendar.monthrange(last_year, 2)[1]
        start_date = f"{first_year - 1}-12-01"
        end_date = f"{last_year}-02-{feb_last:02d}"
    else:
        first_month = min(season_months)
        last_month = max(season_months)
        last_day = calendar.monthrange(last_year, last_month)[1]
        start_date = f"{first_year}-{first_month:02d}-01"
        end_date = f"{last_year}-{last_month:02d}-{last_day:02d}"

    df = fetch_stations(station, start_date=start_date, end_date=end_date)
    return _aggregate_seasonal_by_year(df, column, season_months,
                                        aggregation=aggregation,
                                        start_year=start_year, end_year=end_year)


@_handle_variable_alias
def monthly_totals_by_year(station, parameter, month, start_year=None, end_year=None,
                            aggregation="sum"):
    """Aggregate a variable for one calendar month across many years.

    e.g. April snowfall every year on record → ``aggregation="sum"``.

    Returns a dict (NOT a DataFrame):
        {
            "table": [{"year": int, "value": float|None, "missing_days": int}, ...],
            "summary": str,
        }
    """
    month_num = _parse_month(month)
    column = VARIABLE_COLUMN_MAP.get(parameter, parameter)
    first_year, last_year = _resolve_year_window(station, start_year, end_year)

    last_day = calendar.monthrange(last_year, month_num)[1]
    start_date = f"{first_year}-{month_num:02d}-01"
    end_date = f"{last_year}-{month_num:02d}-{last_day:02d}"

    df = fetch_stations(station, start_date=start_date, end_date=end_date)
    return _aggregate_monthly_by_year(df, column, month_num,
                                       aggregation=aggregation,
                                       start_year=start_year, end_year=end_year)


@_handle_variable_alias
def monthly_threshold_counts(station, parameter, threshold, comparison,
                              month=None, season=None, start_year=None, end_year=None):
    """Per-year count of days meeting a threshold in a single month or season.

    Despite the name, this does NOT iterate every month — it's a thin alias for
    `frequency_of_occurrence` that surfaces the per-year ``days_met`` counts.
    Provide exactly one of ``month`` or ``season``. To compare counts across
    every month, call this once per month and assemble the results yourself.

    `comparison` accepts ``"above"`` / ``">"``, ``"at_or_above"`` / ``">="``,
    ``"below"`` / ``"<"``, or ``"at_or_below"`` / ``"<="``.
    """
    return frequency_of_occurrence(station, parameter, threshold, comparison,
                                    month=month, season=season,
                                    start_year=start_year, end_year=end_year)


@_handle_variable_alias
def calendar_date_records(
    station: str,
    month: int,
    day: int,
    parameter: str,
    n: int = 5,
    start_year: int | None = None,
    end_year: int | None = None,
) -> dict:
    """Rank historical values for a specific calendar date across all years.

    For example, find the hottest July 4th on record, or see where this year's
    precipitation ranks for a given date.

    Parameters
    ----------
    station : str
        Station identifier (e.g. ``"KNYC"``).
    month : int
        Calendar month (1–12).
    day : int
        Calendar day of month.
    parameter : str
        Short code (e.g. ``"tmax"``) or full column name
        (e.g. ``"Maximum Temperature"``).
    n : int, optional
        Number of top records to return, by default 5.
    start_year : int or None, optional
        First year to include. Defaults to the station's start year.
    end_year : int or None, optional
        Last year to include. Defaults to the current year.

    Returns
    -------
    dict
        ``current_year`` : int
            This calendar year.
        ``current_value`` : float or None
            This year's value, or ``None`` if no data yet.
        ``current_rank`` : int or None
            Rank where 1 = highest. ``None`` if no current data.
        ``is_record`` : bool
            ``True`` if ``current_rank == 1``.
        ``top_n`` : list of dict
            Top *n* years, each with ``rank``, ``year``, ``value``.
        ``total_years`` : int
            Years with non-null data for this date.
        ``summary`` : str
            Human-readable summary sentence.
    """
    column = VARIABLE_COLUMN_MAP.get(parameter.lower(), parameter)
    first_year, last_year = _resolve_year_window(station, start_year, end_year)

    df = fetch_stations(
        station,
        start_date=f"{first_year}-01-01",
        end_date=f"{last_year}-12-31",
    )

    df["Date"] = pd.to_datetime(df["Date"])
    df["_month"] = df["Date"].dt.month
    df["_day"] = df["Date"].dt.day
    filtered = df[(df["_month"] == month) & (df["_day"] == day)].copy()

    current_year = pd.Timestamp.now().year
    month_name = calendar.month_name[month]
    date_label = f"{month_name} {day}"

    if filtered.empty:
        return {
            "current_year": current_year,
            "current_value": None,
            "current_rank": None,
            "is_record": False,
            "top_n": [],
            "total_years": 0,
            "summary": f"No data for {date_label} {column}.",
        }

    filtered[column] = pd.to_numeric(filtered[column], errors="coerce")
    filtered = filtered.dropna(subset=[column])
    filtered["_year"] = filtered["Date"].dt.year

    if filtered.empty:
        return {
            "current_year": current_year,
            "current_value": None,
            "current_rank": None,
            "is_record": False,
            "top_n": [],
            "total_years": 0,
            "summary": f"No data for {date_label} {column}.",
        }

    ranked = filtered.sort_values(column, ascending=False).reset_index(drop=True)
    ranked["_rank"] = range(1, len(ranked) + 1)
    total_years = len(ranked)

    # Current year lookup
    cur_row = ranked[ranked["_year"] == current_year]
    if cur_row.empty:
        current_value = None
        current_rank = None
        is_record = False
    else:
        current_value = round(float(cur_row.iloc[0][column]), 2)
        current_rank = int(cur_row.iloc[0]["_rank"])
        is_record = current_rank == 1

    top_n = []
    for _, row in ranked.head(n).iterrows():
        top_n.append({
            "rank": int(row["_rank"]),
            "year": int(row["_year"]),
            "value": round(float(row[column]), 2),
        })

    if current_value is not None:
        summary = (
            f"{date_label} {column}: {current_year} value {current_value} "
            f"ranks #{current_rank} of {total_years} years"
        )
    else:
        summary = (
            f"{date_label} {column}: no {current_year} data yet, "
            f"{total_years} years on record"
        )

    return {
        "current_year": current_year,
        "current_value": current_value,
        "current_rank": current_rank,
        "is_record": is_record,
        "top_n": top_n,
        "total_years": total_years,
        "summary": summary,
    }
