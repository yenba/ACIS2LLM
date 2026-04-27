"""Composite climate analyses built on top of xmACIS2Py.

Each public function fetches ACIS data and returns a structured result with a
``table`` (per-year rows) and a ``summary`` string. These are higher-level than
the per-period statistics in ``xmacis2py.analysis``.
"""

import calendar
from datetime import datetime

import numpy as np
import pandas as pd
from xmacis2py import get_single_station_acis_data

from acis2llm.geocoding import get_station_start_year


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
    ).reset_index()

    table = []
    for _, row in grouped.iterrows():
        val = row["value"]
        table.append({
            "year": int(row["_year"]),
            "value": round(float(val), 2) if pd.notna(val) else None,
            "missing_days": int(row["missing_days"]),
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
            "value": round(float(ev), 3) if pd.notna(ev) else None,
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


def frequency_of_occurrence(station, variable, threshold, comparison,
                             month=None, season=None, start_year=None, end_year=None):
    """How often (across years) a daily threshold is met in a given month or season.

    Returns a dict with `count`, `total_years`, `percentage`, `table`, `summary`.
    Provide exactly one of ``month`` or ``season``.

    `comparison` accepts ``"above"`` / ``">"``, ``"at_or_above"`` / ``">="``,
    ``"below"`` / ``"<"``, or ``"at_or_below"`` / ``"<="``.
    """
    if month is None and season is None:
        raise ValueError(
            "Pass either month=<1-12 or month name> or "
            "season=<'winter'|'spring'|'summer'|'fall'>."
        )
    if month is not None and season is not None:
        raise ValueError("Provide 'month' or 'season', not both.")

    column = VARIABLE_COLUMN_MAP.get(variable, variable)
    first_year, last_year = _resolve_year_window(station, start_year, end_year)

    if month is not None:
        month_num = _parse_month(month)
        last_day = calendar.monthrange(last_year, month_num)[1]
        start_date = f"{first_year}-{month_num:02d}-01"
        end_date = f"{last_year}-{month_num:02d}-{last_day:02d}"
        df = get_single_station_acis_data(station, start_date=start_date, end_date=end_date)
        return _calculate_frequency(df, column, threshold, comparison,
                                     month=month_num,
                                     start_year=start_year, end_year=end_year)

    season_months = _get_season_months(season)
    if 12 in season_months and 1 in season_months:
        start_date = f"{first_year - 1}-12-01"
        end_date = f"{last_year}-02-28"
    else:
        first_month = min(season_months)
        last_month = max(season_months)
        last_day = calendar.monthrange(last_year, last_month)[1]
        start_date = f"{first_year}-{first_month:02d}-01"
        end_date = f"{last_year}-{last_month:02d}-{last_day:02d}"

    df = get_single_station_acis_data(station, start_date=start_date, end_date=end_date)
    return _calculate_frequency(df, column, threshold, comparison,
                                 season=season,
                                 start_year=start_year, end_year=end_year)


def seasonal_summary(station, variable, season, start_year=None, end_year=None,
                      aggregation="sum"):
    """Aggregate a variable across a meteorological season, year by year.

    Winter is Dec–Feb and is labeled by the *ending* year (Dec 2023 → Winter 2024).
    `aggregation` is one of "sum", "mean", "max", "min".
    """
    season_months = _get_season_months(season)
    column = VARIABLE_COLUMN_MAP.get(variable, variable)
    first_year, last_year = _resolve_year_window(station, start_year, end_year)

    if 12 in season_months and 1 in season_months:
        start_date = f"{first_year - 1}-12-01"
        end_date = f"{last_year}-02-28"
    else:
        first_month = min(season_months)
        last_month = max(season_months)
        last_day = calendar.monthrange(last_year, last_month)[1]
        start_date = f"{first_year}-{first_month:02d}-01"
        end_date = f"{last_year}-{last_month:02d}-{last_day:02d}"

    df = get_single_station_acis_data(station, start_date=start_date, end_date=end_date)
    return _aggregate_seasonal_by_year(df, column, season_months,
                                        aggregation=aggregation,
                                        start_year=start_year, end_year=end_year)


def monthly_totals_by_year(station, variable, month, start_year=None, end_year=None,
                            aggregation="sum"):
    """Aggregate a variable for one calendar month across many years.

    e.g. April snowfall every year on record → ``aggregation="sum"``.
    """
    month_num = _parse_month(month)
    column = VARIABLE_COLUMN_MAP.get(variable, variable)
    first_year, last_year = _resolve_year_window(station, start_year, end_year)

    last_day = calendar.monthrange(last_year, month_num)[1]
    start_date = f"{first_year}-{month_num:02d}-01"
    end_date = f"{last_year}-{month_num:02d}-{last_day:02d}"

    df = get_single_station_acis_data(station, start_date=start_date, end_date=end_date)
    return _aggregate_monthly_by_year(df, column, month_num,
                                       aggregation=aggregation,
                                       start_year=start_year, end_year=end_year)


def monthly_threshold_counts(station, variable, threshold, comparison,
                              month=None, season=None, start_year=None, end_year=None):
    """Per-year count of days meeting a threshold in a single month or season.

    Despite the name, this does NOT iterate every month — it's a thin alias for
    `frequency_of_occurrence` that surfaces the per-year ``days_met`` counts.
    Provide exactly one of ``month`` or ``season``. To compare counts across
    every month, call this once per month and assemble the results yourself.

    `comparison` accepts ``"above"`` / ``">"``, ``"at_or_above"`` / ``">="``,
    ``"below"`` / ``"<"``, or ``"at_or_below"`` / ``"<="``.
    """
    return frequency_of_occurrence(station, variable, threshold, comparison,
                                    month=month, season=season,
                                    start_year=start_year, end_year=end_year)
