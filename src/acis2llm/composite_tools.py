import calendar
import re
import requests
import pandas as pd
from datetime import datetime
import numpy as np

try:
    import xmacis2py
    from xmacis2py import get_single_station_acis_data
    XMACIS2PY_AVAILABLE = True
except ImportError:
    XMACIS2PY_AVAILABLE = False

from acis2llm.execution import VARIABLE_COLUMN_MAP

CENSUS_GEOCODER_URL = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
ACIS_STNMETA_URL = "https://data.rcc-acis.org/StnMeta"


_STATE_TO_FIPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06", "CO": "08", "CT": "09", "DE": "10",
    "FL": "12", "GA": "13", "HI": "15", "ID": "16", "IL": "17", "IN": "18", "IA": "19", "KS": "20",
    "KY": "21", "LA": "22", "ME": "23", "MD": "24", "MA": "25", "MI": "26", "MN": "27", "MS": "28",
    "MO": "29", "MT": "30", "NE": "31", "NV": "32", "NH": "33", "NJ": "34", "NM": "35", "NY": "36",
    "NC": "37", "ND": "38", "OH": "39", "OK": "40", "OR": "41", "PA": "42", "RI": "44", "SC": "45",
    "SD": "46", "TN": "47", "TX": "48", "UT": "49", "VT": "50", "VA": "51", "WA": "53", "WV": "54",
    "WI": "55", "WY": "56", "AS": "60", "GU": "66", "MP": "69", "PR": "72", "VI": "78", "DC": "11"
}

def geocode_census(location: str):
    """Geocodes a location string using Census Geocoder or Zippopotam.us."""
    location = location.strip()

    # Check if it's a zip code
    if is_zip_code(location):
        try:
            # Zippopotam.us is free, no key, and great for bare zip codes
            zip_only = location.split("-")[0]
            resp = requests.get(f"https://api.zippopotam.us/us/{zip_only}", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("places"):
                    place = data["places"][0]
                    return {
                        "lat": float(place["latitude"]),
                        "lon": float(place["longitude"]),
                        "display_name": f"{place['place name']}, {place['state abbreviation']} {location}"
                    }
        except Exception:
            pass

    # Generic geocoding via Census
    params = {
        "address": location,
        "benchmark": "Public_AR_Current",
        "format": "json"
    }
    try:
        resp = requests.get(CENSUS_GEOCODER_URL, params=params, timeout=15)
        if resp.status_code == 200:
            data = resp.json()
            matches = data.get("result", {}).get("addressMatches", [])
            if matches:
                match = matches[0]
                return {
                    "lat": match["coordinates"]["y"],
                    "lon": match["coordinates"]["x"],
                    "display_name": match["matchedAddress"]
                }
    except Exception:
        pass

    return None


_MONTH_NAMES = {name.lower(): num for num, name in enumerate(calendar.month_name) if num}
_MONTH_ABBRS = {name.lower(): num for num, name in enumerate(calendar.month_abbr) if num}

def _parse_month(month_input):
    """Convert month name or number to integer 1-12.

    Args:
        month_input: String or int.

    Returns:
        Int 1-12.

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


_SEASON_MAP = {
    "winter": [12, 1, 2],
    "spring": [3, 4, 5],
    "summer": [6, 7, 8],
    "fall": [9, 10, 11],
    "autumn": [9, 10, 11]
}

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
        summary_parts.append(f"Max: {np.max(values):.2f}")
        summary_parts.append(f"Min: {np.min(values):.2f}")
    
    return {
        "table": table,
        "summary": ", ".join(summary_parts)
    }


def _assign_season_year(date, season_months):
    """Assign a date to the correct season-year.

    For seasons that straddle year boundaries (winter: Dec, Jan, Feb),
    the season is labeled by the year of the last month.
    e.g., Dec 2023 belongs to Winter 2024.
    """
    month = date.month
    year = date.year
    if 12 in season_months and month == 12:
        return year + 1
    return year

def _aggregate_seasonal_by_year(df, column, season_months, aggregation="sum",
                                 start_year=None, end_year=None):
    """Aggregate a column by year for a specific season.

    Args:
        df: DataFrame with 'Date' column and target column.
        column: Column to aggregate.
        season_months: List of month numbers (e.g., [12, 1, 2]).
        aggregation: "sum", "mean", "max", or "min".
        start_year: Optional first year.
        end_year: Optional last year.

    Returns:
        Dict with 'table' and 'summary'.
    """
    df = df.copy()
    df["Date"] = pd.to_datetime(df["Date"])
    df["_month"] = df["Date"].dt.month
    df["_season_year"] = df["Date"].apply(lambda d: _assign_season_year(d, season_months))

    # Filter to target months
    filtered = df[df["_month"].isin(season_months)].copy()

    # Filter year range
    if start_year is not None:
        filtered = filtered[filtered["_season_year"] >= start_year]
    if end_year is not None:
        filtered = filtered[filtered["_season_year"] <= end_year]

    if filtered.empty:
        return {
            "table": [],
            "summary": "No data found for the specified season and years.",
        }

    # Convert column to numeric
    filtered[column] = pd.to_numeric(filtered[column], errors="coerce")

    # Group by season-year
    agg_func = {"sum": "sum", "mean": "mean", "max": "max", "min": "min"}[aggregation]
    grouped = filtered.groupby("_season_year").agg(
        value=(column, agg_func),
        missing_days=(column, lambda x: x.isna().sum()),
        obs_count=(column, "count")
    ).reset_index()

    # Filter out partial seasons (e.g., if we only have 1 month of data)
    # A full season should have ~90 days. We'll be lenient and require at least 20 days per month.
    min_days = len(season_months) * 20
    grouped = grouped[grouped["obs_count"] >= min_days]

    # Build table
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

    # Summary
    values = [r["value"] for r in table if r["value"] is not None]
    year_range = f"{table[0]['year']}-{table[-1]['year']}"
    summary_parts = [f"Seasonal {column} ({aggregation}) across {len(table)} years ({year_range})"]
    if values:
        summary_parts.append(f"Average: {np.mean(values):.2f}")
        summary_parts.append(f"Median: {np.median(values):.2f}")
        summary_parts.append(f"Max: {np.max(values):.2f}")
        summary_parts.append(f"Min: {np.min(values):.2f}")

    return {
        "table": table,
        "summary": ", ".join(summary_parts)
    }


def _calculate_frequency(df, column, threshold, comparison, month=None, season=None,
                         start_year=None, end_year=None):
    """Calculate frequency of occurrence for a threshold.

    Returns:
        Dict with stats and breakdown by year.
    """
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

    # Filter to target months and years
    filtered = df[df["_month"].isin(target_months)].copy()
    if start_year:
        filtered = filtered[filtered["_year"] >= start_year]
    if end_year:
        filtered = filtered[filtered["_year"] <= end_year]

    if filtered.empty:
        return {"error": "No data found for the specified period."}

    # Convert to numeric
    filtered[column] = pd.to_numeric(filtered[column], errors="coerce")
    
    # Apply comparison
    if comparison == "above":
        filtered["_match"] = filtered[column] > threshold
    elif comparison == "at_or_above":
        filtered["_match"] = filtered[column] >= threshold
    elif comparison == "below":
        filtered["_match"] = filtered[column] < threshold
    elif comparison == "at_or_below":
        filtered["_match"] = filtered[column] <= threshold
    else:
        raise ValueError(f"Unknown comparison: {comparison}")

    # Group by year
    # Determine which extreme value is relevant for the comparison
    extreme_func = "min" if comparison in ["below", "at_or_below"] else "max"
    
    grouped = filtered.groupby("_year").agg(
        days_matched=("_match", "sum"),
        total_days=("_match", "count"),
        mean_value=(column, "mean"),
        extreme_value=(column, extreme_func),
        missing_days=(column, lambda x: x.isna().sum())
    ).reset_index()

    # Filter out years with too much missing data (e.g., > 10% of target days)
    grouped = grouped[grouped["missing_days"] <= (grouped["total_days"] * 0.1)]
    
    if grouped.empty:
        return {"error": "No years with sufficient data found."}

    years_with_occurrence = (grouped["days_matched"] > 0).sum()
    total_years = len(grouped)
    percentage = (years_with_occurrence / total_years) * 100

    table = []
    for _, row in grouped.iterrows():
        table.append({
            "year": int(row["_year"]),
            "days_met": int(row["days_matched"]),
            "value": round(float(row["extreme_value"]), 3) if pd.notna(row["extreme_value"]) else None,
            "mean_value": round(float(row["mean_value"]), 3) if pd.notna(row["mean_value"]) else None,
            "extreme_value": round(float(row["extreme_value"]), 3) if pd.notna(row["extreme_value"]) else None,
            "met_condition": bool(row["days_matched"] > 0)
        })

    period_desc = calendar.month_name[month] if month else season
    summary = (f"In {period_desc}, {column} was {comparison} {threshold} "
               f"in {years_with_occurrence} out of {total_years} years ({percentage:.1f}%).")

    return {
        "count": int(years_with_occurrence),
        "total_years": int(total_years),
        "percentage": round(float(percentage), 1),
        "table": table,
        "summary": summary
    }


def _get_station_start_year(station):
    """Fetch earliest record year for a station from ACIS."""
    try:
        payload = {"sids": station, "meta": "valid_daterange"}
        resp = requests.post(ACIS_STNMETA_URL, json=payload, timeout=10)
        if resp.status_code == 200:
            meta = resp.json().get("meta", [])
            if meta:
                valid_ranges = meta[0].get("valid_daterange", [])
                earliest = 9999
                for vr in valid_ranges:
                    if vr and len(vr) >= 1:
                        try:
                            year = int(vr[0][:4])
                            if year < earliest: earliest = year
                        except (ValueError, IndexError):
                            continue
                if earliest != 9999:
                    return earliest
    except Exception:
        pass
    return 1850 # Fallback


def frequency_of_occurrence(station, variable, threshold, comparison,
                             month=None, season=None, start_year=None, end_year=None):
    """Calculate how often a threshold is met across years."""
    if not XMACIS2PY_AVAILABLE:
        raise ImportError("xmacis2py is not installed.")

    if month is None and season is None:
        raise ValueError("Either 'month' or 'season' must be provided.")
    if month is not None and season is not None:
        raise ValueError("Provide 'month' or 'season', not both.")

    column = VARIABLE_COLUMN_MAP.get(variable, variable)

    # Determine date range and fetch data
    if start_year is None:
        first_year = _get_station_start_year(station)
    else:
        first_year = start_year
    
    last_year = end_year or pd.Timestamp.now().year

    if month is not None:
        month_num = _parse_month(month)
        last_day = calendar.monthrange(last_year, month_num)[1]
        start_date = f"{first_year}-{month_num:02d}-01"
        end_date = f"{last_year}-{month_num:02d}-{last_day:02d}"
        df = get_single_station_acis_data(station, start_date=start_date, end_date=end_date)
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
        
        df = get_single_station_acis_data(station, start_date=start_date, end_date=end_date)
        return _calculate_frequency(df, column, threshold, comparison,
                                     season=season,
                                     start_year=start_year, end_year=end_year)


def seasonal_summary(station, variable, season, start_year=None,
                      end_year=None, aggregation="sum"):
    """Summarize a variable across a season by year."""
    if not XMACIS2PY_AVAILABLE:
        raise ImportError("xmacis2py is not installed.")

    season_months = _get_season_months(season)
    column = VARIABLE_COLUMN_MAP.get(variable, variable)

    if start_year is None:
        first_year = _get_station_start_year(station)
    else:
        first_year = start_year
        
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

    df = get_single_station_acis_data(station, start_date=start_date, end_date=end_date)

    return _aggregate_seasonal_by_year(df, column, season_months,
                                         aggregation=aggregation,
                                         start_year=start_year,
                                         end_year=end_year)


def monthly_totals_by_year(station, variable, month, start_year=None,
                            end_year=None, aggregation="sum"):
    """Get a variable's monthly aggregate for a single month across years."""
    if not XMACIS2PY_AVAILABLE:
        raise ImportError("xmacis2py is not installed.")

    month_num = _parse_month(month)
    column = VARIABLE_COLUMN_MAP.get(variable, variable)

    # Build date range for the full period
    if start_year is None:
        first_year = _get_station_start_year(station)
    else:
        first_year = start_year
        
    last_year = end_year or pd.Timestamp.now().year
    last_day = calendar.monthrange(last_year, month_num)[1]
    start_date = f"{first_year}-{month_num:02d}-01"
    end_date = f"{last_year}-{month_num:02d}-{last_day:02d}"

    df = get_single_station_acis_data(station, start_date=start_date, end_date=end_date)

    return _aggregate_monthly_by_year(df, column, month_num,
                                       aggregation=aggregation,
                                       start_year=start_year,
                                       end_year=end_year)


def monthly_threshold_counts(station, variable, threshold, comparison,
                             month=None, season=None, start_year=None, end_year=None):
    """Count how many days meet a threshold per year for a specific month or season."""
    return frequency_of_occurrence(station, variable, threshold, comparison,
                                   month=month, season=season, 
                                   start_year=start_year, end_year=end_year)


def is_zip_code(location: str) -> bool:
    """Detect 5-digit zip patterns (and optional +4 extension)."""
    return bool(re.match(r"^\d{5}(-\d{4})?$", location.strip()))


def find_best_station(location):
    """Find the ACIS station with the best data record near a location.

    Follows a waterfall logic:
    1. Direct ID Match (ACIS stnmeta) - Only if location looks like an ID
    2. Zip Code Centroid (Census Geocoder)
    3. City/State Geocoding (Census Geocoder)
    4. ACIS Radius Search (if coordinates found)

    Returns:
        Dict with 'station_id', 'name', 'coordinates', 'data_start', 
        'data_end', 'all_ids', 'geocoded_location', and 'nearby_stations'.
    """
    location = location.strip()
    current_year = datetime.now().year

    # Phase 1: Direct ID Match (only if it looks like a station/airport ID, not a zip code)
    # Skip direct ID lookup for zip codes and ambiguous formats that could match valid IDs
    # at unrelated locations (e.g., "90001" is both a LA zip and a valid ACIS station ID)
    looks_like_station_id = (
        (len(location) == 4 and location.isalpha() and location.upper() == location) or
        (len(location) == 5 and location.isdigit())
    )
    
    if looks_like_station_id:
        acis_payload = {
            "sids": location,
            "meta": "name,state,ll,valid_daterange,sids",
            "elems": "maxt",
        }
        try:
            resp = requests.post(ACIS_STNMETA_URL, json=acis_payload, timeout=10)
            resp.raise_for_status()
            meta = resp.json().get("meta", [])
            if len(meta) == 1:
                stn = meta[0]
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

                sids = stn.get("sids", [])
                primary_id = sids[0].split()[0] if sids else location
                for sid_entry in sids:
                    sid_code = sid_entry.split()[0]
                    if (sid_code.startswith("K") and len(sid_code) == 4) or \
                       (sid_code.startswith(("PA", "PH")) and len(sid_code) == 4):
                        primary_id = sid_code
                        break
                
                # For 5-digit IDs that look like zip codes, verify the station is 
                # in the US before returning (avoid Antarctic stations, etc.)
                if len(location) == 5 and location.isdigit():
                    state = stn.get("state", "")
                    if state not in _STATE_TO_FIPS:
                        # Not a US station, fall through to geocoding
                        pass
                    else:
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
                else:
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
        return {"error": f"Location '{location}' is not a valid 5-digit zip code or airport/station ID. Please provide a 5-digit zip code (e.g. '33126') or a 4-letter airport code (e.g. 'KMIA') for better accuracy."}

    lat = geo["lat"]
    lon = geo["lon"]
    display_name = geo["display_name"]
    # Handle display names like "1 MAIN ST, NEW YORK, NY, 10044" or "New York, NY"
    target_state = None
    parts = [p.strip() for p in display_name.split(",")]
    for p in reversed(parts):
        # Look for 2-letter state code
        subparts = p.split()
        for sp in subparts:
            if len(sp) == 2 and sp.isupper() and sp.isalpha():
                target_state = sp
                break
        if target_state: break
    
    # DEBUG
    # print(f"DEBUG: location='{location}', display_name='{display_name}', target_state='{target_state}'")

    # Phase 4: ACIS Radius Search
    bbox_offset = 0.5  # Broad search area
    bbox = f"{lon - bbox_offset},{lat - bbox_offset},{lon + bbox_offset},{lat + bbox_offset}"

    acis_payload = {
        "bbox": bbox,
        "meta": "name,state,ll,valid_daterange,sids",
        "elems": "maxt",
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
        stn_ll = stn.get("ll", [0, 0])
        dist = ((stn_ll[0] - lon)**2 + (stn_ll[1] - lat)**2)**0.5
        
        stn_state = stn.get("state")
        state_match = stn_state == target_state if target_state else True

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

        # Scoring: 
        # Active? +1000
        # Earliest start? -1 point per year after 1800
        # State match? +500
        # Proximity? -200 per degree
        score = 0
        if is_active: score += 1000
        score -= (earliest_start - 1800)
        if state_match: score += 2000 # Heavily favor same-state stations
        score -= (dist * 200)

        scored.append({
            "score": score,
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

    scored.sort(key=lambda s: s["score"], reverse=True)
    best = scored[0]

    # Smart Threading Logic (Radius: ~10 miles)
    threaded_id = best["id"]
    combined_start = best["earliest_start"]
    for s in scored:
        if s["dist"] < 0.15 and s["earliest_start"] < combined_start:
            threaded_id = f"{best['id']}+{s['id']}"
            combined_start = s["earliest_start"]

    return {
        "station_id": threaded_id,
        "name": f"{best['name']}, {best['state']}",
        "coordinates": best["coordinates"],
        "data_start": combined_start,
        "data_end": best["latest_end"],
        "record_length_years": best["latest_end"] - combined_start,
        "all_ids": best["all_ids"],
        "geocoded_location": display_name,
        "nearby_stations": [
            f"{s['id']} — {s['name']}, {s['state']} ({s['earliest_start']}-{s['latest_end']}, {'active' if s['is_active'] else 'inactive'})"
            for s in scored[1:6]
        ],
    }
