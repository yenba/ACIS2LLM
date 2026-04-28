"""acis2llm — agent-friendly helpers around xmACIS2Py.

Adds three things on top of `xmacis2py`:

  * ``find_best_station`` — resolve "Denver, CO" / "10001" / "KNYC" → station ID
  * ``fetch_stations`` — multi-station aggregation (``"A,B"``) and backfill (``"A+B"``)
  * Composite analyses — ``seasonal_summary``, ``monthly_totals_by_year``,
    ``frequency_of_occurrence``, ``monthly_threshold_counts``

For raw daily fetches and per-period statistics (mean/sum/percentile/etc.), use
`xmacis2py` directly. The accompanying `acis-weather` skill in ``skills/`` is
the agent-facing playbook.
"""

from acis2llm.composites import (
    VARIABLE_COLUMN_MAP,
    frequency_of_occurrence,
    monthly_threshold_counts,
    monthly_totals_by_year,
    seasonal_summary,
)
from acis2llm.geocoding import (
    find_best_station,
    geocode_census,
    is_zip_code,
)
from acis2llm.multi_station import fetch_stations

__version__ = "0.2.3"

__all__ = [
    "VARIABLE_COLUMN_MAP",
    "fetch_stations",
    "find_best_station",
    "frequency_of_occurrence",
    "geocode_census",
    "is_zip_code",
    "monthly_threshold_counts",
    "monthly_totals_by_year",
    "seasonal_summary",
]
