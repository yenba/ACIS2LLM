"""xmacis2py tool definitions and execution metadata."""

STATION_DESC = "4-letter station ID (e.g. KRAL, KLAX, KORD, KJFK, KDEN). Use 'ALL' to query all stations."
START_DATE_DESC = "Start date in YYYY-MM-DD format (e.g. 2023-01-01)"
END_DATE_DESC = "End date in YYYY-MM-DD format (e.g. 2023-12-31)"
VARIABLE_DESC = "Variable to query (e.g. tmax, tmin, tavg, prcp, snow, awdb, hdd, cdd, gdd, snow_depth, tdpa)"
VALUE_DESC = "Threshold value to compare against"
PERCENTILE_VALUE = "Percentile to calculate (0-100, e.g. 90 for 90th percentile)"


def _base_get_data_params():
    return {
        "station": {"type": "string", "description": STATION_DESC},
        "start_date": {"type": "string", "description": START_DATE_DESC},
        "end_date": {"type": "string", "description": END_DATE_DESC},
        "from_when": {
            "type": "string",
            "description": "Relative date filter (e.g. 'yesterday', 'last_week', 'last_year'). Overrides start_date/end_date if provided.",
        },
        "time_delta": {
            "type": "integer",
            "description": "Number of days in the past from the from_when date (e.g. 30 means 30 days back). Only used when start_date/end_date are not provided. Default is 30.",
        },
        "to_csv": {
            "type": "boolean",
            "description": "If True, return data as CSV string instead of DataFrame.",
        },
        "return_pandas_df": {
            "type": "boolean",
            "description": "If True, return a pandas DataFrame. Default is True.",
        },
    }


def _base_period_params():
    return {
        "station": {"type": "string", "description": STATION_DESC},
        "variable": {"type": "string", "description": VARIABLE_DESC},
        "start_date": {"type": "string", "description": START_DATE_DESC},
        "end_date": {"type": "string", "description": END_DATE_DESC},
    }


TOOL_REGISTRY = [
    {
        "name": "get_data",
        "description": "Download weather/climate data from NOAA RCC ACIS. Returns a pandas DataFrame with station, date, and variable columns. Supports multiple stations, time aggregations, and date ranges.",
        "category": "data",
        "inputSchema": {
            "type": "object",
            "properties": _base_get_data_params(),
            "required": ["station"],
        },
    },
    {
        "name": "period_mean",
        "description": "Calculate the mean (average) of a weather variable over a specified period. Returns a single scalar value (or per-station value).",
        "category": "analysis_scalar",
        "inputSchema": {
            "type": "object",
            "properties": _base_period_params(),
            "required": ["station", "variable", "start_date", "end_date"],
        },
    },
    {
        "name": "period_median",
        "description": "Calculate the median of a weather variable over a specified period. Returns a single scalar value.",
        "category": "analysis_scalar",
        "inputSchema": {
            "type": "object",
            "properties": _base_period_params(),
            "required": ["station", "variable", "start_date", "end_date"],
        },
    },
    {
        "name": "period_mode",
        "description": "Calculate the mode (most frequent value) of a weather variable over a specified period. Returns a single scalar value.",
        "category": "analysis_scalar",
        "inputSchema": {
            "type": "object",
            "properties": _base_period_params(),
            "required": ["station", "variable", "start_date", "end_date"],
        },
    },
    {
        "name": "period_percentile",
        "description": "Calculate a specific percentile of a weather variable over a specified period. For example, the 90th percentile means 90% of values fall below this number.",
        "category": "analysis_scalar",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_base_period_params(),
                "percentile": {"type": "number", "description": PERCENTILE_VALUE},
            },
            "required": ["station", "variable", "start_date", "end_date", "percentile"],
        },
    },
    {
        "name": "period_standard_deviation",
        "description": "Calculate the standard deviation of a weather variable over a specified period. Measures how much values vary from the mean.",
        "category": "analysis_scalar",
        "inputSchema": {
            "type": "object",
            "properties": _base_period_params(),
            "required": ["station", "variable", "start_date", "end_date"],
        },
    },
    {
        "name": "period_variance",
        "description": "Calculate the variance of a weather variable over a specified period. Variance is the square of the standard deviation.",
        "category": "analysis_scalar",
        "inputSchema": {
            "type": "object",
            "properties": _base_period_params(),
            "required": ["station", "variable", "start_date", "end_date"],
        },
    },
    {
        "name": "period_skewness",
        "description": "Calculate the skewness of a weather variable over a specified period. Positive skewness means a long right tail; negative means a long left tail.",
        "category": "analysis_scalar",
        "inputSchema": {
            "type": "object",
            "properties": _base_period_params(),
            "required": ["station", "variable", "start_date", "end_date"],
        },
    },
    {
        "name": "period_kurtosis",
        "description": "Calculate the kurtosis of a weather variable over a specified period. Kurtosis measures the 'tailedness' of the distribution.",
        "category": "analysis_scalar",
        "inputSchema": {
            "type": "object",
            "properties": _base_period_params(),
            "required": ["station", "variable", "start_date", "end_date"],
        },
    },
    {
        "name": "period_maximum",
        "description": "Calculate the maximum (highest) value of a weather variable over a specified period.",
        "category": "analysis_scalar",
        "inputSchema": {
            "type": "object",
            "properties": _base_period_params(),
            "required": ["station", "variable", "start_date", "end_date"],
        },
    },
    {
        "name": "period_minimum",
        "description": "Calculate the minimum (lowest) value of a weather variable over a specified period.",
        "category": "analysis_scalar",
        "inputSchema": {
            "type": "object",
            "properties": _base_period_params(),
            "required": ["station", "variable", "start_date", "end_date"],
        },
    },
    {
        "name": "period_sum",
        "description": "Calculate the sum of a weather variable over a specified period. Commonly used for total precipitation or total snowfall.",
        "category": "analysis_scalar",
        "inputSchema": {
            "type": "object",
            "properties": _base_period_params(),
            "required": ["station", "variable", "start_date", "end_date"],
        },
    },
    {
        "name": "period_rankings",
        "description": "Calculate rankings of a weather variable over a specified period. Returns a DataFrame with each observation and its rank. **To find the lowest or coldest extremes, you MUST set sort_order='ascending' so they appear at the top. For highest records, use 'descending' (default).**",
        "category": "analysis_dataframe",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_base_period_params(),
                "sort_order": {
                    "type": "string",
                    "enum": ["descending", "ascending"],
                    "description": "Sort order: 'descending' for highest values at top, or 'ascending' for lowest values at top."
                }
            },
            "required": ["station", "variable", "start_date", "end_date"],
        },
    },
    {
        "name": "running_sum",
        "description": "Calculate a running (cumulative) sum of a weather variable over a specified period. Returns a DataFrame with dates and cumulative values.",
        "category": "analysis_dataframe",
        "inputSchema": {
            "type": "object",
            "properties": _base_period_params(),
            "required": ["station", "variable", "start_date", "end_date"],
        },
    },
    {
        "name": "running_mean",
        "description": "Calculate a running (moving) mean of a weather variable over a specified period. Returns a DataFrame with dates and running averages.",
        "category": "analysis_dataframe",
        "inputSchema": {
            "type": "object",
            "properties": _base_period_params(),
            "required": ["station", "variable", "start_date", "end_date"],
        },
    },
    {
        "name": "detrend_data",
        "description": "Remove the linear trend from a weather variable's time series. Returns a DataFrame with detrended values. Useful for analyzing cyclical patterns.",
        "category": "analysis_dataframe",
        "inputSchema": {
            "type": "object",
            "properties": _base_period_params(),
            "required": ["station", "variable", "start_date", "end_date"],
        },
    },
    {
        "name": "number_of_days_at_or_below",
        "description": "Count the number of days where a weather variable is at or below a specific threshold value.",
        "category": "threshold",
        "xmacis2py_func": "number_of_days_at_or_below_value",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_base_period_params(),
                "value": {"type": "number", "description": VALUE_DESC + " (inclusive)"},
            },
            "required": ["station", "variable", "start_date", "end_date", "value"],
        },
    },
    {
        "name": "number_of_days_at_or_above",
        "description": "Count the number of days where a weather variable is at or above a specific threshold value.",
        "category": "threshold",
        "xmacis2py_func": "number_of_days_at_or_above_value",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_base_period_params(),
                "value": {"type": "number", "description": VALUE_DESC + " (inclusive)"},
            },
            "required": ["station", "variable", "start_date", "end_date", "value"],
        },
    },
    {
        "name": "number_of_days_below",
        "description": "Count the number of days where a weather variable is strictly below a specific threshold value.",
        "category": "threshold",
        "xmacis2py_func": "number_of_days_below_value",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_base_period_params(),
                "value": {"type": "number", "description": VALUE_DESC + " (exclusive)"},
            },
            "required": ["station", "variable", "start_date", "end_date", "value"],
        },
    },
    {
        "name": "number_of_days_above",
        "description": "Count the number of days where a weather variable is strictly above a specific threshold value.",
        "category": "threshold",
        "xmacis2py_func": "number_of_days_above_value",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_base_period_params(),
                "value": {"type": "number", "description": VALUE_DESC + " (exclusive)"},
            },
            "required": ["station", "variable", "start_date", "end_date", "value"],
        },
    },
    {
        "name": "number_of_days_at",
        "description": "Count the number of days where a weather variable is exactly equal to a specific value.",
        "category": "threshold",
        "xmacis2py_func": "number_of_days_at_value",
        "inputSchema": {
            "type": "object",
            "properties": {
                **_base_period_params(),
                "value": {"type": "number", "description": VALUE_DESC + " (exact match)"},
            },
            "required": ["station", "variable", "start_date", "end_date", "value"],
        },
    },
    {
        "name": "number_of_missing_days",
        "description": "Count the number of days with missing data for a weather variable over a specified period. Useful for identifying data gaps.",
        "category": "missing_days",
        "inputSchema": {
            "type": "object",
            "properties": _base_period_params(),
            "required": ["station", "variable", "start_date", "end_date"],
        },
    },
    {
        "name": "monthly_totals_by_year",
        "description": "Get a weather variable's monthly total (or average/max/min) for a specific month across all available years. Returns one row per year. Use this for questions like 'how much snow does Lexington get in April' or 'what's the average high in July over the years'.",
        "category": "composite",
        "inputSchema": {
            "type": "object",
            "properties": {
                "station": {"type": "string", "description": STATION_DESC},
                "variable": {"type": "string", "description": VARIABLE_DESC},
                "month": {
                    "type": "string",
                    "description": "Month number (1-12) or name (e.g. 'april', 'Apr', '4')",
                },
                "start_year": {
                    "type": "integer",
                    "description": "First year to include (optional, defaults to earliest available)",
                },
                "end_year": {
                    "type": "integer",
                    "description": "Last year to include (optional, defaults to most recent)",
                },
                "aggregation": {
                    "type": "string",
                    "description": "How to aggregate daily values within each month: 'sum' (default, best for precipitation/snowfall), 'mean' (best for temperatures), 'max', or 'min'",
                },
            },
            "required": ["station", "variable", "month"],
        },
    },
    {
        "name": "seasonal_summary",
        "description": "Summarize a weather variable across a meteorological season by year. Seasons: winter (Dec-Feb), spring (Mar-May), summer (Jun-Aug), fall (Sep-Nov). Returns one row per year. Use for questions like 'how was this winter's snowfall' or 'show me summer precipitation trends'.",
        "category": "composite",
        "inputSchema": {
            "type": "object",
            "properties": {
                "station": {"type": "string", "description": STATION_DESC},
                "variable": {"type": "string", "description": VARIABLE_DESC},
                "season": {
                    "type": "string",
                    "description": "Season name: 'winter' (Dec-Feb), 'spring' (Mar-May), 'summer' (Jun-Aug), 'fall' (Sep-Nov), or 'autumn'",
                },
                "start_year": {
                    "type": "integer",
                    "description": "First year to include (optional)",
                },
                "end_year": {
                    "type": "integer",
                    "description": "Last year to include (optional)",
                },
                "aggregation": {
                    "type": "string",
                    "description": "How to aggregate: 'sum' (default), 'mean', 'max', or 'min'",
                },
            },
            "required": ["station", "variable", "season"],
        },
    },
    {
        "name": "frequency_of_occurrence",
        "description": "Calculate how often a weather variable exceeds or falls below a threshold for a given month or season across all years. Answers 'likelihood', 'how often', 'chance of', 'probability' questions. Returns count, percentage, and year-by-year breakdown. Example: 'what's the likelihood of snow in April' -> frequency_of_occurrence with variable='snow', month='april', threshold=0, comparison='above'.",
        "category": "composite",
        "inputSchema": {
            "type": "object",
            "properties": {
                "station": {"type": "string", "description": STATION_DESC},
                "variable": {"type": "string", "description": VARIABLE_DESC},
                "threshold": {
                    "type": "number",
                    "description": "Value to compare against (e.g. 0 for any occurrence, 1 for at least 1 inch)",
                },
                "comparison": {
                    "type": "string",
                    "description": "Comparison type: 'above' (strictly greater), 'at_or_above' (>=), 'below' (strictly less), 'at_or_below' (<=)",
                },
                "month": {
                    "type": "string",
                    "description": "Month number or name (e.g. 'april', '4'). Provide month OR season, not both.",
                },
                "season": {
                    "type": "string",
                    "description": "Season name (e.g. 'winter'). Provide month OR season, not both.",
                },
                "start_year": {
                    "type": "integer",
                    "description": "First year to include (optional)",
                },
                "end_year": {
                    "type": "integer",
                    "description": "Last year to include (optional)",
                },
            },
            "required": ["station", "variable", "threshold", "comparison"],
        },
    },
    {
        "name": "monthly_threshold_counts",
        "description": "Count the number of days meeting a threshold (e.g. days <= 32) for a specific month or season across all available years. Returns a year-by-year breakdown of counts and extreme values.",
        "category": "composite",
        "inputSchema": {
            "type": "object",
            "properties": {
                "station": {"type": "string", "description": STATION_DESC},
                "variable": {"type": "string", "description": VARIABLE_DESC},
                "threshold": {"type": "number", "description": "Value to compare against"},
                "comparison": {
                    "type": "string",
                    "enum": ["above", "at_or_above", "below", "at_or_below"],
                    "description": "Comparison type",
                },
                "month": {
                    "type": "string",
                    "description": "Month number or name (e.g. 'january', '1'). Provide month OR season.",
                },
                "season": {
                    "type": "string",
                    "description": "Season name (e.g. 'winter'). Provide month OR season.",
                },
                "start_year": {
                    "type": "integer",
                    "description": "First year to include (optional)",
                },
                "end_year": {
                    "type": "integer",
                    "description": "Last year to include (optional)",
                },
            },
            "required": ["station", "variable", "threshold", "comparison"],
        },
    },
    {
        "name": "find_best_station",
        "description": "Find the best ACIS weather station near a location. Returns the active station with the longest historical data record. IMPORTANT: For city names, you MUST provide a 5-digit zip code or a 4-letter airport code (e.g. '33126' or 'KMIA' for Miami) to ensure accuracy. DO NOT pass raw city names like 'Miami, FL'.",
        "category": "composite_station",
        "inputSchema": {
            "type": "object",
            "properties": {
                "location": {
                    "type": "string",
                    "description": "5-digit zip code, 4-letter airport code, or ACIS station ID (e.g. '33126', 'KMIA', 'KNYC').",
                },
            },
            "required": ["location"],
        },
    },
]

TOOL_MAP = {tool["name"]: tool for tool in TOOL_REGISTRY}
