"""Composite tools that aggregate xmacis2py daily data into high-level results.

Each tool fetches raw daily data via get_data() and aggregates with pandas,
returning structured results that answer common climatological queries in one call.
"""

import calendar
import re
import time
from datetime import datetime

import numpy as np
import pandas as pd
import requests

try:
    from xmacis2py import get_data
    XMACIS2PY_AVAILABLE = True
except ImportError:
    XMACIS2PY_AVAILABLE = False

from execution import VARIABLE_COLUMN_MAP
from config import CENSUS_GEOCODER_URL

ACIS_STNMETA_URL = "https://data.rcc-acis.org/StnMeta"


def geocode_census(location: str):
    """Geocodes a location string using the US Census Geocoder."""
    params = {
        "address": location,
        "benchmark": "Public_AR_Current",
        "format": "json"
    }
    try:
        resp = requests.get(CENSUS_GEOCODER_URL, params=params, timeout=10)
        resp.raise_for_status()
        data = resp.json()
        matches = data.get("result", {}).get("addressMatches", [])
        if not matches:
            return None

        first = matches[0]
        return {
            "lat": first["coordinates"]["y"],
            "lon": first["coordinates"]["x"],
            "display_name": first["matchedAddress"]
        }
    except Exception:
        return None


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
    """Convert month input (name, abbreviation, or number) to integer 1-12.

    Args:
        month_input: "april", "Apr", "4", or 4

    Returns:
        Integer month number (1-12).

    Raises:
        ValueError: If input cannot be parsed or is out of range.
    """
    if isinstance(month_input, int):
        if 1 <= month_input <= 12:
            return month_input
        raise ValueError(f"Month must be between 1 and 12, got {month_input}")

    month_str = str(month_input).strip().lower()

    # Try as integer string
    try:
        month_num = int(month_str)
        if 1 <= month_num <= 12:
            return month_num
        raise ValueError(f"Month must be between 1 and 12, got {month_num}")
    except ValueError:
        if month_str.isdigit() or (month_str.startswith("-") and month_str[1:].isdigit()):
            raise

    # Try full name
    if month_str in _MONTH_NAMES:
        return _MONTH_NAMES[month_str]

    # Try abbreviation
    if month_str in _MONTH_ABBRS:
        return _MONTH_ABBRS[month_str]

    raise ValueError(f"Could not parse month: '{month_input}'")


def _get_season_months(season):
    """Get the list of month numbers for a season.

    Args:
        season: "winter", "spring", "summer", "fall", or "autumn"

    Returns:
        List of month numbers (e.g., [12, 1, 2] for winter).

    Raises:
        ValueError: If season name is not recognized.
    """
    key = season.strip().lower()
    if key not in _SEASON_MAP:
        raise ValueError(f"Unknown season: '{season}'. Use winter, spring, summer, fall, or autumn.")
    return _SEASON_MAP[key]


def _aggregate_monthly_by_year(df, column, month, aggregation="sum",
                                start_year=None, end_year=None):
    """Aggregate a column by year for a specific month.

    Args:
        df: DataFrame with 'Date' column and the target column.
        column: Column name to aggregate (e.g., 'Snowfall').
        month: Integer month number (1-12).
        aggregation: "sum", "mean", "max", or "min".
        start_year: Optional first year to include.
        end_year: Optional last year to include.

    Returns:
        Dict with 'table' (list of row dicts) and 'summary' (string).
    """
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df["_month"] = df["Date"].dt.month
    df["_year"] = df["Date"].dt.year

    # Filter to target month
    filtered = df[df["_month"] == month].copy()

    # Filter year range
    if start_year is not None:
        filtered = filtered[filtered["_year"] >= start_year]
    if end_year is not None:
        filtered = filtered[filtered["_year"] <= end_year]

    if filtered.empty:
        month_name = calendar.month_name[month]
        return {
            "table": [],
            "summary": f"No data found for {month_name}.",
        }

    # Convert column to numeric, coercing errors to NaN
    filtered[column] = pd.to_numeric(filtered[column], errors="coerce")

    # Group by year and aggregate
    agg_func = {"sum": "sum", "mean": "mean", "max": "max", "min": "min"}[aggregation]
    grouped = filtered.groupby("_year").agg(
        value=(column, agg_func),
        missing_days=(column, lambda x: x.isna().sum()),
    ).reset_index()

    # Build table
    table = []
    for _, row in grouped.iterrows():
        val = row["value"]
        table.append({
            "year": int(row["_year"]),
            "value": round(float(val), 2) if pd.notna(val) else None,
            "missing_days": int(row["missing_days"]),
        })

    # Build summary
    month_name = calendar.month_name[month]
    values = [r["value"] for r in table if r["value"] is not None]
    year_count = len(table)
    year_range = f"{table[0]['year']}-{table[-1]['year']}"

    summary_parts = [f"{month_name} {column} ({aggregation}) across {year_count} years ({year_range})"]
    if values:
        summary_parts.append(f"Average: {np.mean(values):.2f}")
        summary_parts.append(f"Median: {np.median(values):.2f}")
        summary_parts.append(f"Max: {max(values):.2f}")
        summary_parts.append(f"Min: {min(values):.2f}")

    return {
        "table": table,
        "summary": ", ".join(summary_parts),
    }


def _assign_season_year(date, season_months):
    """Assign a date to the correct season-year.

    For seasons that straddle year boundaries (winter: Dec, Jan, Feb),
    the season is labeled by the year of the last month.
    e.g., Dec 2023 belongs to Winter 2024.

    Args:
        date: A datetime object.
        season_months: List of month numbers (e.g., [12, 1, 2]).

    Returns:
        Integer year label for this season.
    """
    if date.month == 12 and 12 in season_months and 1 in season_months:
        return date.year + 1
    return date.year


def _aggregate_seasonal_by_year(df, column, season_months, aggregation="sum",
                                 start_year=None, end_year=None):
    """Aggregate a column by season-year for a set of months.

    Args:
        df: DataFrame with 'Date' column and the target column.
        column: Column name to aggregate.
        season_months: List of month numbers (e.g., [12, 1, 2] for winter).
        aggregation: "sum", "mean", "max", or "min".
        start_year: Optional first year.
        end_year: Optional last year.

    Returns:
        Dict with 'table' (list of row dicts) and 'summary' (string).
    """
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df["_month"] = df["Date"].dt.month

    # Filter to season months
    filtered = df[df["_month"].isin(season_months)].copy()

    if filtered.empty:
        return {"table": [], "summary": "No data found for the specified season."}

    # Assign season-year
    filtered["_season_year"] = filtered["Date"].apply(
        lambda d: _assign_season_year(d, season_months)
    )

    # Filter year range
    if start_year is not None:
        filtered = filtered[filtered["_season_year"] >= start_year]
    if end_year is not None:
        filtered = filtered[filtered["_season_year"] <= end_year]

    if filtered.empty:
        return {"table": [], "summary": "No data found for the specified year range."}

    # Convert column to numeric
    filtered[column] = pd.to_numeric(filtered[column], errors="coerce")

    # Group by season-year and aggregate
    agg_func = {"sum": "sum", "mean": "mean", "max": "max", "min": "min"}[aggregation]
    grouped = filtered.groupby("_season_year").agg(
        value=(column, agg_func),
        missing_days=(column, lambda x: x.isna().sum()),
    ).reset_index()

    # Build table
    table = []
    for _, row in grouped.iterrows():
        val = row["value"]
        table.append({
            "year": int(row["_season_year"]),
            "value": round(float(val), 2) if pd.notna(val) else None,
            "missing_days": int(row["missing_days"]),
        })

    # Build summary
    values = [r["value"] for r in table if r["value"] is not None]
    year_count = len(table)
    year_range = f"{table[0]['year']}-{table[-1]['year']}"

    summary_parts = [f"Seasonal {column} ({aggregation}) across {year_count} years ({year_range})"]
    if values:
        summary_parts.append(f"Average: {np.mean(values):.2f}")
        summary_parts.append(f"Median: {np.median(values):.2f}")
        summary_parts.append(f"Max: {max(values):.2f}")
        summary_parts.append(f"Min: {min(values):.2f}")

    return {"table": table, "summary": ", ".join(summary_parts)}


_COMPARISONS = {
    "above": lambda val, threshold: val > threshold,
    "at_or_above": lambda val, threshold: val >= threshold,
    "below": lambda val, threshold: val < threshold,
    "at_or_below": lambda val, threshold: val <= threshold,
}


def _calculate_frequency(df, column, threshold, comparison, month=None,
                          season_months=None, start_year=None, end_year=None):
    """Calculate how often a variable's aggregated value meets a condition.

    Args:
        df: DataFrame with 'Date' column and the target column.
        column: Column name to check.
        threshold: Value to compare against.
        comparison: "above", "at_or_above", "below", or "at_or_below".
        month: Integer month number (use month OR season_months, not both).
        season_months: List of month numbers for a season.
        start_year: Optional first year.
        end_year: Optional last year.

    Returns:
        Dict with 'count', 'total_years', 'percentage', 'table', 'summary'.
    """
    if comparison not in _COMPARISONS:
        raise ValueError(f"Unknown comparison: '{comparison}'. Use: {', '.join(_COMPARISONS.keys())}")

    # Get per-year aggregated values
    if month is not None:
        yearly = _aggregate_monthly_by_year(df, column, month, aggregation="sum",
                                             start_year=start_year, end_year=end_year)
    elif season_months is not None:
        yearly = _aggregate_seasonal_by_year(df, column, season_months, aggregation="sum",
                                              start_year=start_year, end_year=end_year)
    else:
        raise ValueError("Either 'month' or 'season_months' must be provided.")

    compare_fn = _COMPARISONS[comparison]

    # Evaluate each year
    table = []
    met_count = 0
    total = 0
    for row in yearly["table"]:
        val = row["value"]
        if val is not None:
            met = compare_fn(val, threshold)
            table.append({
                "year": row["year"],
                "value": val,
                "met_condition": met,
            })
            if met:
                met_count += 1
            total += 1
        else:
            table.append({
                "year": row["year"],
                "value": None,
                "met_condition": None,
            })

    percentage = (met_count / total * 100) if total > 0 else 0

    # Build summary
    comp_label = comparison.replace("_", " ")
    if month is not None:
        period_label = calendar.month_name[month]
    else:
        period_label = "the season"

    summary = (
        f"{column} {comp_label} {threshold} occurred in {met_count} of "
        f"{total} years ({percentage:.1f}%) for {period_label}."
    )

    return {
        "count": met_count,
        "total_years": total,
        "percentage": round(percentage, 1),
        "table": table,
        "summary": summary,
    }


def frequency_of_occurrence(station, variable, threshold, comparison,
                              month=None, season=None,
                              start_year=None, end_year=None):
    """Calculate how often a variable exceeds/falls below a threshold.

    Answers "how often does X happen" by aggregating per-year values
    and checking against the threshold.

    Args:
        station: 4-letter station ID.
        variable: Weather variable code.
        threshold: Value to compare against.
        comparison: "above", "at_or_above", "below", or "at_or_below".
        month: Month number or name (provide month OR season, not both).
        season: Season name ("winter", "spring", etc.).
        start_year: Optional first year.
        end_year: Optional last year.

    Returns:
        Dict with 'count', 'total_years', 'percentage', 'table', 'summary'.
    """
    if not XMACIS2PY_AVAILABLE:
        raise ImportError("xmacis2py is not installed.")

    if month is None and season is None:
        raise ValueError("Either 'month' or 'season' must be provided.")
    if month is not None and season is not None:
        raise ValueError("Provide 'month' or 'season', not both.")

    column = VARIABLE_COLUMN_MAP.get(variable, variable)

    # Determine date range and fetch data
    first_year = start_year or 1890
    last_year = end_year or pd.Timestamp.now().year

    if month is not None:
        month_num = _parse_month(month)
        last_day = calendar.monthrange(last_year, month_num)[1]
        start_date = f"{first_year}-{month_num:02d}-01"
        end_date = f"{last_year}-{month_num:02d}-{last_day:02d}"
        df = get_data(station, start_date=start_date, end_date=end_date)
        return _calculate_frequency(df, column, threshold, comparison,
                                     month=month_num,
                                     start_year=start_year, end_year=end_year)
    else:
        season_months = _get_season_months(season)
        first_month = min(season_months)
        last_month = max(season_months)

        if 12 in season_months and 1 in season_months:
            start_date = f"{first_year - 1}-12-01"
            end_date = f"{last_year}-02-28"
        else:
            last_day = calendar.monthrange(last_year, last_month)[1]
            start_date = f"{first_year}-{first_month:02d}-01"
            end_date = f"{last_year}-{last_month:02d}-{last_day:02d}"

        df = get_data(station, start_date=start_date, end_date=end_date)
        return _calculate_frequency(df, column, threshold, comparison,
                                     season_months=season_months,
                                     start_year=start_year, end_year=end_year)


def seasonal_summary(station, variable, season, start_year=None,
                      end_year=None, aggregation="sum"):
    """Summarize a variable across a meteorological season by year.

    Args:
        station: 4-letter station ID.
        variable: Weather variable code.
        season: "winter", "spring", "summer", "fall", or "autumn".
        start_year: Optional first year.
        end_year: Optional last year.
        aggregation: "sum", "mean", "max", or "min". Default "sum".

    Returns:
        Dict with 'table', 'summary'.
    """
    if not XMACIS2PY_AVAILABLE:
        raise ImportError("xmacis2py is not installed.")

    season_months = _get_season_months(season)
    column = VARIABLE_COLUMN_MAP.get(variable, variable)

    first_year = start_year or 1890
    last_year = end_year or pd.Timestamp.now().year

    # For seasons that straddle year boundaries, extend the date range
    first_month = min(season_months)
    last_month = max(season_months)

    if 12 in season_months and 1 in season_months:
        # Winter: need Dec of (first_year - 1) through Feb of last_year
        start_date = f"{first_year - 1}-12-01"
        end_date = f"{last_year}-02-28"
    else:
        last_day = calendar.monthrange(last_year, last_month)[1]
        start_date = f"{first_year}-{first_month:02d}-01"
        end_date = f"{last_year}-{last_month:02d}-{last_day:02d}"

    df = get_data(station, start_date=start_date, end_date=end_date)

    return _aggregate_seasonal_by_year(df, column, season_months,
                                        aggregation=aggregation,
                                        start_year=start_year,
                                        end_year=end_year)


def monthly_totals_by_year(station, variable, month, start_year=None,
                            end_year=None, aggregation="sum"):
    """Get a variable's monthly aggregate for a single month across years.

    Fetches daily data via get_data and aggregates by year.

    Args:
        station: 4-letter station ID (e.g., "KLEX").
        variable: Weather variable code (e.g., "snow", "tmax").
        month: Month number (1-12) or name ("april", "Apr").
        start_year: Optional first year.
        end_year: Optional last year.
        aggregation: "sum", "mean", "max", or "min". Default "sum".

    Returns:
        Dict with 'table', 'summary'.
    """
    if not XMACIS2PY_AVAILABLE:
        raise ImportError("xmacis2py is not installed.")

    month_num = _parse_month(month)
    column = VARIABLE_COLUMN_MAP.get(variable, variable)

    # Build date range for the full period
    first_year = start_year or 1890
    last_year = end_year or pd.Timestamp.now().year
    last_day = calendar.monthrange(last_year, month_num)[1]
    start_date = f"{first_year}-{month_num:02d}-01"
    end_date = f"{last_year}-{month_num:02d}-{last_day:02d}"

    df = get_data(station, start_date=start_date, end_date=end_date)

    return _aggregate_monthly_by_year(df, column, month_num,
                                       aggregation=aggregation,
                                       start_year=start_year,
                                       end_year=end_year)


def is_zip_code(location: str) -> bool:
    """Detect 5-digit zip patterns (and optional +4 extension)."""
    return bool(re.match(r"^\d{5}(-\d{4})?$", location.strip()))


def find_best_station(location):
    """Find the ACIS station with the best data record near a location.

    Follows a waterfall logic:
    1. Direct ID Match (ACIS stnmeta)
    2. Zip Code Centroid (Census Geocoder)
    3. City/State Geocoding (Census Geocoder)
    4. ACIS Radius Search (if coordinates found)

    Returns:
        Dict with 'station_id', 'name', 'state', 'coordinates',
        'data_start', 'data_end', 'all_ids', and 'nearby_stations'.
    """
    location = location.strip()
    current_year = datetime.now().year

    # Phase 1: Direct ID Match
    acis_payload = {
        "sids": location,
        "meta": "name,state,ll,valid_daterange,sids",
    }
    try:
        resp = requests.post(ACIS_STNMETA_URL, json=acis_payload, timeout=10)
        resp.raise_for_status()
        meta = resp.json().get("meta", [])
        # If exactly one active station matches, return it
        if len(meta) == 1:
            stn = meta[0]
            # Check if active
            valid_ranges = stn.get("valid_daterange", [])
            latest_end = 0
            earliest_start = 9999
            for vr in valid_ranges:
                if vr and len(vr) >= 2:
                    try:
                        start_y = int(vr[0][:4])
                        end_y = int(vr[1][:4])
                        latest_end = max(latest_end, end_y)
                        earliest_start = min(earliest_start, start_y)
                    except (ValueError, IndexError):
                        continue
            
            if latest_end >= current_year - 1:
                # Return this station
                sids = stn.get("sids", [])
                primary_id = sids[0].split()[0] if sids else location
                for sid_entry in sids:
                    sid_code = sid_entry.split()[0]
                    if (sid_code.startswith("K") and len(sid_code) == 4) or \
                       (sid_code.startswith(("PA", "PH")) and len(sid_code) == 4):
                        primary_id = sid_code
                        break
                
                return {
                    "station_id": primary_id,
                    "name": f"{stn.get('name')}, {stn.get('state')}",
                    "coordinates": stn.get("ll"),
                    "data_start": earliest_start,
                    "data_end": latest_end,
                    "record_length_years": latest_end - earliest_start,
                    "all_ids": [s.split()[0] for s in sids],
                    "geocoded_location": location,
                    "nearby_stations": []
                }
    except Exception:
        pass

    # Phase 2 & 3: Geocoding
    geo = geocode_census(location)
    if not geo:
        return {"error": f"Could not geocode location: '{location}'. Try a more specific place name or zip code."}

    lat = geo["lat"]
    lon = geo["lon"]
    display_name = geo["display_name"]

    # Phase 4: ACIS Radius Search
    bbox_offset = 0.3
    bbox = f"{lon - bbox_offset},{lat - bbox_offset},{lon + bbox_offset},{lat + bbox_offset}"

    acis_payload = {
        "bbox": bbox,
        "meta": "name,state,ll,valid_daterange,sids",
    }
    try:
        resp = requests.post(ACIS_STNMETA_URL, json=acis_payload, timeout=15)
        resp.raise_for_status()
        stations = resp.json().get("meta", [])
    except Exception as e:
        return {"error": f"ACIS metadata query failed: {str(e)}"}

    if not stations:
        return {
            "error": f"No ACIS stations found near '{location}' (lat={lat:.4f}, lon={lon:.4f}).",
            "geocoded_location": display_name,
            "coordinates": [lon, lat],
        }

    # "History King" Logic
    scored = []
    for stn in stations:
        valid_ranges = stn.get("valid_daterange", [])
        earliest_start = 9999
        latest_end = 0
        for vr in valid_ranges:
            if vr and len(vr) >= 2:
                try:
                    start_y = int(vr[0][:4])
                    end_y = int(vr[1][:4])
                    earliest_start = min(earliest_start, start_y)
                    latest_end = max(latest_end, end_y)
                except (ValueError, IndexError):
                    continue
        
        if earliest_start == 9999:
            continue

        is_active = latest_end >= current_year - 1
        
        # Proximity (Euclidean distance for tie-breaker)
        stn_ll = stn.get("ll", [0, 0])
        dist = ((stn_ll[0] - lon)**2 + (stn_ll[1] - lat)**2)**0.5

        sids = stn.get("sids", [])
        primary_id = sids[0].split()[0] if sids else "Unknown"
        has_icao = False
        all_ids = []
        for sid_entry in sids:
            sid_code = sid_entry.split()[0]
            all_ids.append(sid_code)
            if (sid_code.startswith("K") and len(sid_code) == 4) or \
               (sid_code.startswith(("PA", "PH")) and len(sid_code) == 4):
                if not has_icao:
                    primary_id = sid_code
                    has_icao = True

        scored.append({
            "id": primary_id,
            "name": stn.get("name"),
            "state": stn.get("state"),
            "coordinates": stn_ll,
            "earliest_start": earliest_start,
            "latest_end": latest_end,
            "is_active": is_active,
            "has_icao": has_icao,
            "dist": dist,
            "all_ids": all_ids
        })

    if not scored:
        return {"error": "No stations with valid date ranges found."}

    # History King Sorting:
    # a. Must be active (end date >= current year - 1)
    # b. Sort by earliest start date (ascending)
    # c. Tie-breaker: proximity (ascending)
    
    # We'll filter active first, or just sort by is_active descending
    scored.sort(key=lambda s: (not s["is_active"], s["earliest_start"], s["dist"]))

    best = scored[0]

    # Build nearby stations list
    nearby = []
    for s in scored[:5]:
        nearby.append({
            "id": s["id"],
            "name": f"{s['name']}, {s['state']}",
            "record": f"{s['earliest_start']}-{s['latest_end']}",
            "active": s["is_active"],
        })

    return {
        "station_id": best["id"],
        "name": f"{best['name']}, {best['state']}",
        "coordinates": best["coordinates"],
        "data_start": best["earliest_start"],
        "data_end": best["latest_end"],
        "record_length_years": best["latest_end"] - best["earliest_start"],
        "all_ids": best["all_ids"],
        "geocoded_location": display_name,
        "nearby_stations": nearby,
    }

