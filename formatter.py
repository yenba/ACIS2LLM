"""Result formatting for xmacis2py outputs."""

import pandas as pd


ANALYSIS_FUNCTIONS = {
    "period_mean",
    "period_median",
    "period_mode",
    "period_percentile",
    "period_standard_deviation",
    "period_variance",
    "period_skewness",
    "period_kurtosis",
    "period_maximum",
    "period_minimum",
    "period_sum",
}

DATAFRAME_FUNCTIONS = {
    "get_data",
    "period_rankings",
    "running_sum",
    "running_mean",
    "detrend_data",
}

THRESHOLD_FUNCTIONS = {
    "number_of_days_at_or_below",
    "number_of_days_at_or_above",
    "number_of_days_below",
    "number_of_days_above",
    "number_of_days_at",
}

MISSING_DAYS_FUNCTION = "number_of_missing_days"

COMPOSITE_FUNCTIONS = {
    "monthly_totals_by_year",
    "seasonal_summary",
    "frequency_of_occurrence",
    "find_best_station",
}

MAX_DISPLAY_ROWS = 60


def _format_dataframe_table(df):
    """Format a DataFrame as a text table (up to MAX_DISPLAY_ROWS rows)."""
    if not isinstance(df, pd.DataFrame):
        return str(df)

    head = df.head(MAX_DISPLAY_ROWS)
    table = head.to_string(index=False, justify="right")

    total_rows = len(df)
    if total_rows > MAX_DISPLAY_ROWS:
        table += f"\n\n[... {total_rows - MAX_DISPLAY_ROWS} more rows ...]"

    return table


def _format_summary(df, tool_name=None):
    """Add a summary section below a table."""
    lines = []

    if not isinstance(df, pd.DataFrame):
        return str(df)

    lines.append(f"\n--- Summary ---")
    lines.append(f"Rows: {len(df)}")
    lines.append(f"Columns: {', '.join(df.columns)}")

    if "valid_date" in df.columns:
        date_min = df["valid_date"].min()
        date_max = df["valid_date"].max()
        lines.append(f"Date range: {date_min} to {date_max}")

    if tool_name:
        lines.append(f"Tool: {tool_name}")

    return "\n".join(lines)


def format_get_data_result(result):
    """Format the result of a get_data call.

    Args:
        result: pandas DataFrame or CSV string from get_data.

    Returns:
        Formatted string with table and summary.
    """
    if isinstance(result, str):
        return result

    if not isinstance(result, pd.DataFrame):
        result_str = str(result)
        return f"--- Data Retrieved ---\n{result_str}"

    table = _format_dataframe_table(result)
    summary = _format_summary(result, "get_data")

    return f"--- Data Retrieved ---\n{table}\n{summary}"


def format_analysis_result(result, tool_name=""):
    """Format the result of an analysis function call.

    Args:
        result: scalar value or DataFrame from analysis tool.
        tool_name: name of the tool that produced the result.

    Returns:
        Formatted string with result.
    """
    if isinstance(result, pd.DataFrame):
        table = _format_dataframe_table(result)
        summary = _format_summary(result, tool_name)
        return f"--- {tool_name} Result ---\n{table}\n{summary}"

    if isinstance(result, (int, float)):
        return f"--- {tool_name} Result ---\n{result}"

    if isinstance(result, (list, tuple)) and len(result) > 0:
        if isinstance(result[0], (int, float)):
            values = ", ".join(str(v) for v in result)
            return f"--- {tool_name} Result ---\n{values}"

    result_str = str(result)
    if len(result_str) > 500:
        result_str = result_str[:500] + "..."
    return f"--- {tool_name} Result ---\n{result_str}"


def format_threshold_result(result, tool_name=""):
    """Format the result of a threshold count function.

    Args:
        result: integer count from the threshold function.
        tool_name: name of the tool that produced the result.

    Returns:
        Formatted string with count.
    """
    if isinstance(result, (int, float)):
        count = int(result)
        return f"--- {tool_name} Result ---\nNumber of days: {count}"

    return f"--- {tool_name} Result ---\n{result}"


def format_missing_days_result(result):
    """Format the result of number_of_missing_days.

    Args:
        result: integer count of missing days.

    Returns:
        Formatted string with count.
    """
    if isinstance(result, (int, float)):
        count = int(result)
        return f"--- number_of_missing_days Result ---\nMissing days: {count}"

    return f"--- number_of_missing_days Result ---\n{result}"


def format_station_result(result):
    """Format the result of a find_best_station call.

    Args:
        result: Dict with station info or error.

    Returns:
        Formatted string.
    """
    if "error" in result:
        return f"--- find_best_station Result ---\n{result['error']}"

    parts = ["--- find_best_station Result ---"]
    parts.append(f"Best station: {result['station_id']} — {result['name']}")
    parts.append(f"Record: {result['data_start']}-{result['data_end']} ({result['record_length_years']} years)")
    parts.append(f"Location: {result.get('geocoded_location', 'N/A')}")
    parts.append(f"All IDs: {', '.join(result.get('all_ids', []))}")

    nearby = result.get("nearby_stations", [])
    if len(nearby) > 1:
        parts.append("")
        parts.append("Nearby alternatives:")
        for s in nearby[1:]:
            active = "active" if s["active"] else "inactive"
            parts.append(f"  {s['id']} — {s['name']} ({s['record']}, {active})")

    return "\n".join(parts)


def format_composite_result(result, tool_name):
    """Format the result of a composite tool call.

    Args:
        result: Dict with 'table', 'summary', and optionally 'count'/'percentage'.
        tool_name: Name of the composite tool.

    Returns:
        Formatted string.
    """
    parts = [f"--- {tool_name} Result ---"]

    table = result.get("table", [])
    if not table:
        parts.append(result.get("summary", "No data available."))
        return "\n".join(parts)

    # Format frequency results
    if "count" in result:
        parts.append(result["summary"])
        parts.append("")
        parts.append(f"{'Year':<8} {'Value':<12} {'Meets Condition'}")
        parts.append("-" * 36)
        for row in table:
            val = f"{row['value']:.2f}" if row["value"] is not None else "N/A"
            met = "Yes" if row.get("met_condition") else "No" if row.get("met_condition") is not None else "N/A"
            parts.append(f"{row['year']:<8} {val:<12} {met}")
    else:
        # Format monthly/seasonal results
        parts.append(f"{'Year':<8} {'Value':<12} {'Missing Days'}")
        parts.append("-" * 32)
        for row in table:
            val = f"{row['value']:.2f}" if row["value"] is not None else "N/A"
            parts.append(f"{row['year']:<8} {val:<12} {row.get('missing_days', 0)}")
        parts.append("")
        parts.append(result.get("summary", ""))

    return "\n".join(parts)


def format_error(error_msg):
    """Wrap an error message for LLM consumption.

    Args:
        error_msg: The error message string.

    Returns:
        String prefixed with ERROR:.
    """
    return f"ERROR: {error_msg}"


def format_result(result, tool_name):
    """Automatically select the appropriate formatter based on tool name.

    Args:
        result: The tool result (DataFrame, scalar, or string).
        tool_name: Name of the tool that produced the result.

    Returns:
        Formatted string.
    """
    if tool_name == "get_data":
        return format_get_data_result(result)
    elif tool_name in ANALYSIS_FUNCTIONS:
        return format_analysis_result(result, tool_name)
    elif tool_name in THRESHOLD_FUNCTIONS:
        return format_threshold_result(result, tool_name)
    elif tool_name == MISSING_DAYS_FUNCTION:
        return format_missing_days_result(result)
    elif tool_name in DATAFRAME_FUNCTIONS:
        return format_analysis_result(result, tool_name)
    elif tool_name == "find_best_station":
        return format_station_result(result)
    elif tool_name in COMPOSITE_FUNCTIONS:
        return format_composite_result(result, tool_name)
    else:
        return format_analysis_result(result, tool_name)
