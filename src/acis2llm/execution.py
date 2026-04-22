"""Tool execution engine — executes xmacis2py function calls."""

import xmacis2py
import pandas as pd
from concurrent.futures import ThreadPoolExecutor
from xmacis2py import analysis as analysis_mod

from acis2llm.formatter import format_error, format_result
from acis2llm.tools import TOOL_MAP

# Map short variable codes to get_data column names
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


def _validate_args(tool_name, args):
    """Check that all required arguments are present based on the tool's inputSchema.

    Args:
        tool_name: Name of the tool.
        args: Dict of arguments.

    Returns:
        Error message string if missing args, or None if all good.
    """
    tool_info = TOOL_MAP.get(tool_name)
    if not tool_info:
        return f"Unknown tool: {tool_name}"

    required = tool_info["inputSchema"].get("required", [])
    missing = [arg for arg in required if arg not in args or args[arg] is None]
    if missing:
        return f"Missing required argument(s): {', '.join(missing)}"
    return None


def _fetch_station_data(station, args):
    """Fetch data for a single station. Helper for concurrent execution."""
    try:
        s_args = args.copy()
        s_args["station"] = station
        df = xmacis2py.get_data(**s_args)
        return station, df
    except Exception:
        return station, None


def _run_get_data(args):
    """Execute get_data and return the result.
    
    Handles multiple stations via comma (aggregation) or plus (backfilling).
    Includes try-except protection against library/API errors.

    Args:
        args: Dict of get_data arguments.

    Returns:
        pandas DataFrame or CSV string.
    """
    station_str = args.get("station", "")
    
    try:
        # Handle multiple stations via comma
        if isinstance(station_str, str) and "," in station_str:
            stations = [s.strip() for s in station_str.split(",") if s.strip()]
            dfs = []
            with ThreadPoolExecutor() as executor:
                # Fetch all stations in parallel
                results = list(executor.map(lambda s: _fetch_station_data(s, args), stations))

            for s, df in results:
                if isinstance(df, pd.DataFrame) and not df.empty:
                    if "station" not in df.columns:
                        df.insert(0, "station", s)
                    dfs.append(df)
            return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()

        # Handle backfilling via plus
        if isinstance(station_str, str) and "+" in station_str:
            stations = [s.strip() for s in station_str.split("+") if s.strip()]

            with ThreadPoolExecutor() as executor:
                # Fetch all stations in parallel
                results_map = dict(executor.map(lambda s: _fetch_station_data(s, args), stations))

            base_df = None
            # Process in order of stations to maintain backfill priority
            for s in stations:
                df = results_map.get(s)
                if not isinstance(df, pd.DataFrame) or df.empty:
                    continue

                # Use Date as index for combining
                if "Date" in df.columns:
                    df = df.set_index("Date")
                elif "valid_date" in df.columns:
                    df = df.set_index("valid_date")

                if base_df is None:
                    base_df = df
                else:
                    base_df = base_df.combine_first(df)
            
            if base_df is None: return pd.DataFrame()
            
            # Restore index and set station
            base_df = base_df.reset_index()
            base_df["station"] = station_str
            return base_df

        return xmacis2py.get_data(**args)
    except Exception as e:
        # Fallback for unexpected top-level errors
        import logging
        logging.error(f"Error in _run_get_data: {e}")
        return pd.DataFrame()


def _run_analysis_tool(tool_name, tool_info, args):
    """Execute an analysis tool by first fetching data, then analyzing.

    Args:
        tool_name: Name of the analysis tool.
        tool_info: Tool definition from registry.
        args: Dict of tool arguments.

    Returns:
        The analysis result.
    """
    # Get the correct xmacis2py function
    func_name = tool_info.get("xmacis2py_func", tool_name)
    func = getattr(analysis_mod, func_name)

    # First fetch the data using our wrapper
    data_args = {k: v for k, v in args.items() if k in ("station", "start_date", "end_date",
                                                          "from_when", "time_delta",
                                                          "to_csv", "return_pandas_df")}
    df = _run_get_data(data_args)
    
    if df.empty:
        raise ValueError(f"No data returned for station {args.get('station')} in the specified period.")

    # Map short variable codes to DataFrame column names
    col_name = VARIABLE_COLUMN_MAP.get(args["variable"], args["variable"])

    category = tool_info["category"]

    try:
        if category == "threshold":
            # threshold functions take (df, parameter, value)
            return func(df, col_name, args["value"])
        elif tool_name == "period_percentile":
            # period_percentile takes (df, parameter, percentile, ...)
            return func(df, col_name, percentile=args["percentile"])
        elif tool_name == "period_rankings":
            result = func(df, col_name).copy()
            if args.get("sort_order") == "ascending":
                result = result.sort_values(by=col_name, ascending=True).reset_index(drop=True)
                result.insert(0, "Ascending Rank (1=Lowest)", range(1, len(result) + 1))
            else:
                result.insert(0, "Descending Rank (1=Highest)", range(1, len(result) + 1))
            return result
        else:
            # Generic analysis: func(df, col_name)
            return func(df, col_name)
    except Exception as e:
        raise RuntimeError(f"Analysis error in {tool_name}: {str(e)}")


def execute_tool_call(tool_name, tool_args):
    """Execute a tool call and return the formatted result.

    Args:
        tool_name: Name of the tool to call.
        tool_args: Dict of arguments for the tool.

    Returns:
        Formatted result string.
    """
    # Special handling for clarification tool
    if tool_name == "clarify_location":
        suggestions = tool_args.get("suggested_locations", [])
        if suggestions:
            loc_list = ", ".join(suggestions)
            return f"I need to know which location you're interested in. We've discussed {loc_list}, or you can provide a new 5-digit ZIP code or 4-letter airport code."
        return "I need to know which location you're interested in. Please provide a 5-digit ZIP code or a 4-letter airport code (e.g., 'KNYC' for New York City)."

    # Pre-check for missing location in tools that require it
    tool_info = TOOL_MAP.get(tool_name)
    if tool_info:
        required = tool_info["inputSchema"].get("required", [])
        if "station" in required and "station" not in tool_args:
             return "ERROR: Missing 'station' argument. You MUST ask the user for a location (ZIP or airport code) using the 'clarify_location' tool if the intent is ambiguous."
        if "location" in required and "location" not in tool_args:
             return "ERROR: Missing 'location' argument. You MUST ask the user for a location (ZIP or airport code) using the 'clarify_location' tool if the intent is ambiguous."

    # Validate required arguments
    validation_error = _validate_args(tool_name, tool_args)
    if validation_error:
        return format_error(validation_error)

    tool_info = TOOL_MAP[tool_name]
    category = tool_info["category"]

    try:
        if category in ("composite", "composite_station"):
            from acis2llm.composite_tools import (
                monthly_totals_by_year,
                seasonal_summary,
                frequency_of_occurrence,
                find_best_station,
                monthly_threshold_counts,
            )
            func_map = {
                "monthly_totals_by_year": monthly_totals_by_year,
                "seasonal_summary": seasonal_summary,
                "frequency_of_occurrence": frequency_of_occurrence,
                "find_best_station": find_best_station,
                "monthly_threshold_counts": monthly_threshold_counts,
            }
            result = func_map[tool_name](**tool_args)
            return format_result(result, tool_name)
        elif category == "data":
            result = _run_get_data(tool_args)
            return format_result(result, tool_name)
        else:
            result = _run_analysis_tool(tool_name, tool_info, tool_args)
            return format_result(result, tool_name)

    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        return format_error(f"{error_type}: {error_msg}")
