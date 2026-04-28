"""Geocoding and ACIS station discovery.

Resolves user-friendly location strings (city names, ZIP codes, airport codes,
station IDs) to the best matching ACIS station, ranked by record length and
proximity. Wraps the US Census Geocoder, Zippopotam.us, and the ACIS StnMeta
endpoint.
"""

import re
from datetime import datetime

import requests

CENSUS_GEOCODER_URL = "https://geocoding.geo.census.gov/geocoder/locations/onelineaddress"
ZIPPOPOTAM_URL = "https://api.zippopotam.us/us"
ACIS_STNMETA_URL = "https://data.rcc-acis.org/StnMeta"

_STATE_TO_FIPS = {
    "AL": "01", "AK": "02", "AZ": "04", "AR": "05", "CA": "06", "CO": "08", "CT": "09", "DE": "10",
    "FL": "12", "GA": "13", "HI": "15", "ID": "16", "IL": "17", "IN": "18", "IA": "19", "KS": "20",
    "KY": "21", "LA": "22", "ME": "23", "MD": "24", "MA": "25", "MI": "26", "MN": "27", "MS": "28",
    "MO": "29", "MT": "30", "NE": "31", "NV": "32", "NH": "33", "NJ": "34", "NM": "35", "NY": "36",
    "NC": "37", "ND": "38", "OH": "39", "OK": "40", "OR": "41", "PA": "42", "RI": "44", "SC": "45",
    "SD": "46", "TN": "47", "TX": "48", "UT": "49", "VT": "50", "VA": "51", "WA": "53", "WV": "54",
    "WI": "55", "WY": "56", "AS": "60", "GU": "66", "MP": "69", "PR": "72", "VI": "78", "DC": "11",
}


def is_zip_code(location: str) -> bool:
    """True for 5-digit US ZIPs and ZIP+4 patterns."""
    return bool(re.match(r"^\d{5}(-\d{4})?$", location.strip()))


def geocode_census(location: str):
    """Resolve a location string to lat/lon via Zippopotam (for ZIPs) or US Census.

    Returns dict with `lat`, `lon`, `display_name` on success, else None.
    """
    location = location.strip()

    if is_zip_code(location):
        try:
            zip_only = location.split("-")[0]
            resp = requests.get(f"{ZIPPOPOTAM_URL}/{zip_only}", timeout=10)
            if resp.status_code == 200:
                data = resp.json()
                if data.get("places"):
                    place = data["places"][0]
                    return {
                        "lat": float(place["latitude"]),
                        "lon": float(place["longitude"]),
                        "display_name": f"{place['place name']}, {place['state abbreviation']} {location}",
                    }
        except Exception:
            pass

    params = {"address": location, "benchmark": "Public_AR_Current", "format": "json"}
    try:
        resp = requests.get(CENSUS_GEOCODER_URL, params=params, timeout=15)
        if resp.status_code == 200:
            matches = resp.json().get("result", {}).get("addressMatches", [])
            if matches:
                match = matches[0]
                return {
                    "lat": match["coordinates"]["y"],
                    "lon": match["coordinates"]["x"],
                    "display_name": match["matchedAddress"],
                }
    except Exception:
        pass

    return None


def get_station_start_year(station: str) -> int:
    """Earliest year of record for a station from ACIS StnMeta. Falls back to 1850."""
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
                            if year < earliest:
                                earliest = year
                        except (ValueError, IndexError):
                            continue
                if earliest != 9999:
                    return earliest
    except Exception:
        pass
    return 1850


def _looks_like_station_id(location: str) -> bool:
    return (
        (len(location) == 4 and location.isalpha() and location.upper() == location)
        or (len(location) == 5 and location.isdigit())
    )


def _pick_primary_id(sids):
    """Prefer ICAO codes (K-prefix continental US, PA/PH for Alaska/Hawaii) when present."""
    if not sids:
        return None, []
    primary = sids[0].split()[0]
    all_ids = [s.split()[0] for s in sids]
    for sid in all_ids:
        if (sid.startswith("K") and len(sid) == 4) or (sid.startswith(("PA", "PH")) and len(sid) == 4):
            primary = sid
            break
    return primary, all_ids


def _date_range(valid_ranges):
    earliest, latest = 9999, 0
    for vr in valid_ranges:
        if vr and len(vr) >= 2:
            try:
                earliest = min(earliest, int(vr[0][:4]))
                latest = max(latest, int(vr[1][:4]))
            except (ValueError, IndexError):
                continue
    return earliest, latest


def _try_direct_id(location: str):
    """Phase 1 — direct ACIS ID lookup. Returns station dict or None."""
    payload = {
        "sids": location,
        "meta": "name,state,ll,valid_daterange,sids",
        "elems": "maxt",
    }
    try:
        resp = requests.post(ACIS_STNMETA_URL, json=payload, timeout=10)
        resp.raise_for_status()
        meta = resp.json().get("meta", [])
        if len(meta) != 1:
            return None
        stn = meta[0]
        earliest, latest = _date_range(stn.get("valid_daterange", []))
        if earliest == 9999:
            return None

        # For 5-digit IDs (which collide with ZIPs), require a US state
        if len(location) == 5 and location.isdigit() and stn.get("state") not in _STATE_TO_FIPS:
            return None

        primary_id, all_ids = _pick_primary_id(stn.get("sids", []))
        return {
            "station_id": primary_id or location,
            "name": f"{stn.get('name')}, {stn.get('state')}",
            "coordinates": stn.get("ll"),
            "data_start": earliest,
            "data_end": latest,
            "record_length_years": latest - earliest,
            "all_ids": all_ids,
            "geocoded_location": location,
            "nearby_stations": [],
        }
    except Exception:
        return None


def _extract_state(display_name: str):
    parts = [p.strip() for p in display_name.split(",")]
    for p in reversed(parts):
        for sp in p.split():
            if len(sp) == 2 and sp.isupper() and sp.isalpha():
                return sp
    return None


def _bbox_search(lat, lon, target_state, current_year):
    """Phase 4 — search ACIS for stations within ~0.5 degrees and score them."""
    bbox_offset = 0.5
    bbox = f"{lon - bbox_offset},{lat - bbox_offset},{lon + bbox_offset},{lat + bbox_offset}"
    payload = {"bbox": bbox, "meta": "name,state,ll,valid_daterange,sids", "elems": "maxt"}
    resp = requests.post(ACIS_STNMETA_URL, json=payload, timeout=15)
    resp.raise_for_status()
    stations = resp.json().get("meta", [])

    scored = []
    for stn in stations:
        earliest, latest = _date_range(stn.get("valid_daterange", []))
        if earliest == 9999:
            continue
        is_active = latest >= current_year - 1
        stn_ll = stn.get("ll", [0, 0])
        dist = ((stn_ll[0] - lon) ** 2 + (stn_ll[1] - lat) ** 2) ** 0.5
        state_match = (stn.get("state") == target_state) if target_state else True

        primary_id, all_ids = _pick_primary_id(stn.get("sids", []))
        has_icao = primary_id is not None and (
            (primary_id.startswith("K") and len(primary_id) == 4)
            or (primary_id.startswith(("PA", "PH")) and len(primary_id) == 4)
        )

        score = 0
        if is_active:
            score += 1000
        score -= earliest - 1800
        if state_match:
            score += 2000
        score -= dist * 200

        scored.append({
            "score": score,
            "id": primary_id or "Unknown",
            "name": stn.get("name"),
            "state": stn.get("state"),
            "coordinates": stn_ll,
            "earliest_start": earliest,
            "latest_end": latest,
            "is_active": is_active,
            "has_icao": has_icao,
            "dist": dist,
            "all_ids": all_ids,
        })

    scored.sort(key=lambda s: s["score"], reverse=True)
    return scored


def find_best_station(location: str):
    """Find the ACIS station with the best record near a location.

    Waterfall:
      1. Direct ACIS StnMeta lookup if `location` looks like a station ID
      2. Geocode via Zippopotam (5-digit ZIP) or US Census (street address —
         note: "City, State" alone does *not* resolve via Census; pass a ZIP
         or station ID for cities)
      3. ACIS bbox search around the geocoded coordinates, scored by:
         active record (+1000), state match (+2000), record length, proximity
      4. If a co-located older station exists within ~10mi, return a backfill
         spec like "KNYC+OLDER" (see `multi_station.fetch_stations`)
    """
    location = location.strip()
    if not location:
        return {"error": "Empty location. Provide a 5-digit ZIP, a 4-letter airport code, or a US street address."}
    current_year = datetime.now().year

    if _looks_like_station_id(location):
        direct = _try_direct_id(location)
        if direct:
            return direct

    geo = geocode_census(location)
    if not geo:
        return {
            "error": (
                f"Could not resolve '{location}' to a US location. ACIS covers US stations only; "
                "non-US locations are not supported. For US locations, a 5-digit ZIP (e.g. '33126') "
                "or a 4-letter airport code (e.g. 'KMIA') gives the most reliable result."
            )
        }

    target_state = _extract_state(geo["display_name"])

    try:
        scored = _bbox_search(geo["lat"], geo["lon"], target_state, current_year)
    except Exception as e:
        return {"error": f"ACIS metadata query failed: {e}"}

    if not scored:
        return {
            "error": f"No ACIS stations found near '{location}' (lat={geo['lat']:.4f}, lon={geo['lon']:.4f}).",
            "geocoded_location": geo["display_name"],
            "coordinates": [geo["lon"], geo["lat"]],
        }

    best = scored[0]

    # Backfill: if a co-located (within ~10mi) station has an earlier start, thread the IDs
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
        "geocoded_location": geo["display_name"],
        "nearby_stations": [
            f"{s['id']} — {s['name']}, {s['state']} "
            f"({s['earliest_start']}-{s['latest_end']}, {'active' if s['is_active'] else 'inactive'})"
            for s in scored[1:6]
        ],
    }
