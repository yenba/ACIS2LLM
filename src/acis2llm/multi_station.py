"""Multi-station fetch helpers for xmACIS2Py.

Adds two conveniences on top of `xmacis2py.get_single_station_acis_data`:

  * Comma-separated stations  →  fetch each in parallel and concatenate
    (e.g. ``"KNYC,KJFK,KLGA"``  →  one DataFrame with a ``station`` column)

  * Plus-separated stations   →  fetch each, then backfill missing dates from
    later stations in priority order (e.g. ``"KNYC+OLDER"`` extends KNYC's
    record back in time using OLDER for any dates KNYC doesn't cover)

Also passes through the literal ``"ALL"`` keyword to
``xmacis2py.get_multi_station_acis_data`` for region-wide queries.
"""

from concurrent.futures import ThreadPoolExecutor

import pandas as pd
import xmacis2py


def _fetch_one(station, args):
    try:
        a = args.copy()
        a["station"] = station
        return station, xmacis2py.get_single_station_acis_data(**a)
    except Exception:
        return station, None


def _concat_aggregate(stations, args):
    with ThreadPoolExecutor() as ex:
        results = list(ex.map(lambda s: _fetch_one(s, args), stations))
    dfs = []
    for station, df in results:
        if isinstance(df, pd.DataFrame) and not df.empty:
            if "station" not in df.columns:
                df.insert(0, "station", station)
            dfs.append(df)
    return pd.concat(dfs, ignore_index=True) if dfs else pd.DataFrame()


def _backfill(stations, args, label):
    with ThreadPoolExecutor() as ex:
        results_map = dict(ex.map(lambda s: _fetch_one(s, args), stations))

    base = None
    for s in stations:
        df = results_map.get(s)
        if not isinstance(df, pd.DataFrame) or df.empty:
            continue

        if "Date" in df.columns:
            df = df.set_index("Date")
        elif "valid_date" in df.columns:
            df = df.set_index("valid_date")

        base = df if base is None else base.combine_first(df)

    if base is None:
        return pd.DataFrame()

    base = base.reset_index()
    base["station"] = label
    return base


def fetch_stations(spec, **kwargs) -> pd.DataFrame:
    """Fetch ACIS data for one or more stations.

    Parameters
    ----------
    spec : str
        Station spec. One of:

        - Single station ID (``"KNYC"``)
        - Comma-separated for aggregation (``"KNYC,KJFK"`` — concatenated rows)
        - Plus-separated for backfill (``"KNYC+OLDER"`` — primary + fallback in priority order)
        - The literal ``"ALL"`` to query every station in the region (forwarded to
          ``xmacis2py.get_multi_station_acis_data``)
    **kwargs
        Forwarded to the underlying xmACIS2Py call. Common ones:
        ``start_date``, ``end_date``, ``from_when``, ``time_delta``,
        ``to_csv``, ``return_pandas_df``.

    Returns
    -------
    pandas.DataFrame
        Empty DataFrame on total failure (network down, no rows, etc.).
    """
    if not isinstance(spec, str):
        raise TypeError(f"spec must be a string, got {type(spec).__name__}")

    args = {"station": spec, **kwargs}

    try:
        if "," in spec:
            stations = [s.strip() for s in spec.split(",") if s.strip()]
            return _concat_aggregate(stations, args)

        if "+" in spec:
            stations = [s.strip() for s in spec.split("+") if s.strip()]
            return _backfill(stations, args, label=spec)

        if spec.strip().upper() == "ALL":
            multi_args = {k: v for k, v in args.items() if k != "station"}
            multi_args["stations"] = "ALL"
            return xmacis2py.get_multi_station_acis_data(**multi_args)

        return xmacis2py.get_single_station_acis_data(**args)
    except Exception:
        import logging
        logging.exception("fetch_stations failed for spec=%r", spec)
        return pd.DataFrame()
