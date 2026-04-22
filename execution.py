"""Tool execution engine — executes xmacis2py function calls."""

from formatter import format_error, format_result

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

# Try to import xmacis2py at module load
try:
    import xmacis2py
    XMACIS2PY_AVAILABLE = True
except ImportError:
    XMACIS2PY_AVAILABLE = False

# Analysis functions live in xmacis2py.analysis in v2.x
try:
    from xmacis2py import analysis as analysis_mod
    ANALYSIS_AVAILABLE = True
except ImportError:
    ANALYSIS_AVAILABLE = False


# Map tool names to their analysis module function names
_ANALYSIS_TOOL_MAP = {
    "period_mean": "period_mean",
    "period_median": "period_median",
    "period_mode": "period_mode",
    "period_percentile": "period_percentile",
    "period_standard_deviation": "period_standard_deviation",
    "period_variance": "period_variance",
    "period_skewness": "period_skewness",
    "period_kurtosis": "period_kurtosis",
    "period_maximum": "period_maximum",
    "period_minimum": "period_minimum",
    "period_sum": "period_sum",
    "period_rankings": "period_rankings",
    "running_sum": "running_sum",
    "running_mean": "running_mean",
    "detrend_data": "detrend_data",
    "number_of_days_at_or_below": "number_of_days_at_or_below_value",
    "number_of_days_at_or_above": "number_of_days_at_or_above_value",
    "number_of_days_below": "number_of_days_below_value",
    "number_of_days_above": "number_of_days_above_value",
    "number_of_days_at": "number_of_days_at_value",
    "number_of_missing_days": "number_of_missing_days",
}

_COMPOSITE_TOOLS = {
    "monthly_totals_by_year",
    "seasonal_summary",
    "frequency_of_occurrence",
    "find_best_station",
}

# Threshold functions that take an extra 'value' argument
_THRESHOLD_TOOLS = {
    "number_of_days_at_or_below",
    "number_of_days_at_or_above",
    "number_of_days_below",
    "number_of_days_above",
    "number_of_days_at",
}

_REQUIRED_ARGS = {
    "get_data": ["station"],
    "period_mean": ["station", "variable", "start_date", "end_date"],
    "period_median": ["station", "variable", "start_date", "end_date"],
    "period_mode": ["station", "variable", "start_date", "end_date"],
    "period_percentile": ["station", "variable", "start_date", "end_date", "percentile"],
    "period_standard_deviation": ["station", "variable", "start_date", "end_date"],
    "period_variance": ["station", "variable", "start_date", "end_date"],
    "period_skewness": ["station", "variable", "start_date", "end_date"],
    "period_kurtosis": ["station", "variable", "start_date", "end_date"],
    "period_maximum": ["station", "variable", "start_date", "end_date"],
    "period_minimum": ["station", "variable", "start_date", "end_date"],
    "period_sum": ["station", "variable", "start_date", "end_date"],
    "period_rankings": ["station", "variable", "start_date", "end_date"],
    "running_sum": ["station", "variable", "start_date", "end_date"],
    "running_mean": ["station", "variable", "start_date", "end_date"],
    "detrend_data": ["station", "variable", "start_date", "end_date"],
    "number_of_days_at_or_below": ["station", "variable", "start_date", "end_date", "value"],
    "number_of_days_at_or_above": ["station", "variable", "start_date", "end_date", "value"],
    "number_of_days_below": ["station", "variable", "start_date", "end_date", "value"],
    "number_of_days_above": ["station", "variable", "start_date", "end_date", "value"],
    "number_of_days_at": ["station", "variable", "start_date", "end_date", "value"],
    "number_of_missing_days": ["station", "variable", "start_date", "end_date"],
    "monthly_totals_by_year": ["station", "variable", "month"],
    "seasonal_summary": ["station", "variable", "season"],
    "frequency_of_occurrence": ["station", "variable", "threshold", "comparison"],
    "find_best_station": ["location"],
}


def _get_function(tool_name):
    """Get the xmacis2py function for a given tool name.

    Args:
        tool_name: Name of the tool.

    Returns:
        The function object.

    Raises:
        ImportError: If xmacis2py is not installed.
        AttributeError: If the function doesn't exist.
    """
    if not XMACIS2PY_AVAILABLE:
        raise ImportError("xmacis2py is not installed. Install with: pip install xmacis2py")

    if tool_name == "get_data":
        return getattr(xmacis2py, "get_data")

    # Analysis functions are in xmacis2py.analysis (v2.x)
    func_name = _ANALYSIS_TOOL_MAP.get(tool_name)
    if not func_name:
        raise AttributeError(f"Unknown tool: {tool_name}")

    if not ANALYSIS_AVAILABLE:
        raise ImportError(f"Could not import xmacis2py.analysis. Is xmacis2py v2.x installed?")

    return getattr(analysis_mod, func_name)


def _validate_args(tool_name, args):
    """Check that all required arguments are present.

    Args:
        tool_name: Name of the tool.
        args: Dict of arguments.

    Returns:
        Error message string if missing args, or None if all good.
    """
    required = _REQUIRED_ARGS.get(tool_name, [])
    missing = [arg for arg in required if arg not in args or args[arg] is None]
    if missing:
        return f"Missing required argument(s): {', '.join(missing)}"
    return None


def _run_get_data(args):
    """Execute get_data and return the DataFrame.

    Args:
        args: Dict of get_data arguments.

    Returns:
        pandas DataFrame.

    Raises:
        Exception: If get_data fails.
    """
    func = _get_function("get_data")
    return func(**args)


def _run_analysis_tool(tool_name, args):
    """Execute an analysis tool by first fetching data, then analyzing.

    Args:
        tool_name: Name of the analysis tool.
        args: Dict of tool arguments.

    Returns:
        The analysis result.
    """
    # Map the 'value' arg for threshold functions (they use the same name in xmacis2py)
    func = _get_function(tool_name)

    # First fetch the data
    data_args = {k: v for k, v in args.items() if k in ("station", "start_date", "end_date",
                                                          "from_when", "time_delta",
                                                          "to_csv", "return_pandas_df")}
    df = _run_get_data(data_args)

    # Map short variable codes to DataFrame column names
    col_name = VARIABLE_COLUMN_MAP.get(args["variable"], args["variable"])

    if tool_name in _THRESHOLD_TOOLS:
        # threshold functions take (df, parameter, value)
        result = func(df, col_name, args["value"])
    elif tool_name == "period_percentile":
        # period_percentile takes (df, parameter, percentile, ...)
        result = func(df, col_name, percentile=args["percentile"])
    elif tool_name == "detrend_data":
        result = func(df, col_name)
    elif tool_name in ("running_sum", "running_mean"):
        result = func(df, col_name)
    elif tool_name == "period_rankings":
        result = func(df, col_name).copy()
        if args.get("sort_order") == "ascending":
            result = result.sort_values(by=col_name, ascending=True).reset_index(drop=True)
            result.insert(0, "Ascending Rank (1=Lowest)", range(1, len(result) + 1))
        else:
            result.insert(0, "Descending Rank (1=Highest)", range(1, len(result) + 1))
    else:
        # Most analysis functions take (df, parameter, ...)
        result = func(df, col_name)

    return result


def execute_tool_call(tool_name, tool_args):
    """Execute a tool call and return the formatted result.

    Args:
        tool_name: Name of the tool to call.
        tool_args: Dict of arguments for the tool.

    Returns:
        Formatted result string.
    """
    # Validate required arguments
    validation_error = _validate_args(tool_name, tool_args)
    if validation_error:
        return format_error(validation_error)

    # Execute the function
    try:
        if tool_name in _COMPOSITE_TOOLS:
            from composite_tools import (
                monthly_totals_by_year,
                seasonal_summary,
                frequency_of_occurrence,
                find_best_station,
            )
            func_map = {
                "monthly_totals_by_year": monthly_totals_by_year,
                "seasonal_summary": seasonal_summary,
                "frequency_of_occurrence": frequency_of_occurrence,
                "find_best_station": find_best_station,
            }
            result = func_map[tool_name](**tool_args)
            return format_result(result, tool_name)
        elif tool_name == "get_data":
            func = _get_function(tool_name)
            result = func(**tool_args)
            return format_result(result, tool_name)
        else:
            result = _run_analysis_tool(tool_name, tool_args)
            return format_result(result, tool_name)

    except ImportError as e:
        return format_error(str(e))

    except TypeError as e:
        error_msg = str(e)
        if "missing" in error_msg.lower() or "required" in error_msg.lower():
            return format_error(f"Argument error: {error_msg}")
        return format_error(f"TypeError: {error_msg}")

    except Exception as e:
        error_type = type(e).__name__
        error_msg = str(e)
        return format_error(f"{error_type}: {error_msg}")
