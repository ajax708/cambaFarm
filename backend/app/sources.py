"""Data connectors (HTTP APIs, no keys). Every fetch is cached on disk and returns
plain Python data so the engine never knows where a value came from."""
from __future__ import annotations

import json
import os
import time
from datetime import date, timedelta
from pathlib import Path

import httpx

CACHE = Path(__file__).resolve().parent.parent / "cache"
CACHE.mkdir(exist_ok=True)
UA = {"User-Agent": "rotation-explorer-rehearsal/0.1 (NASA Space Apps 2026 prototype)"}


def _cached(name: str, max_age_days: float, fetch):
    path = CACHE / name
    if path.exists() and (time.time() - path.stat().st_mtime) < max_age_days * 86400:
        return json.loads(path.read_text())
    try:
        data = fetch()
    except Exception:
        if path.exists():  # stale cache beats no data
            return json.loads(path.read_text())
        raise
    path.write_text(json.dumps(data))
    return data


# ---------------------------------------------------------------- NASA POWER
POWER_PARAMS = "T2M_MIN,T2M_MAX,PRECTOTCORR,WS2M,RH2M,ALLSKY_SFC_SW_DWN"


def get_power(lat: float, lon: float, start: str = "19810101") -> dict:
    """Daily agroclimatology for a point (NASA POWER, community AG)."""
    end = (date.today() - timedelta(days=7)).strftime("%Y%m%d")

    def fetch():
        r = httpx.get(
            "https://power.larc.nasa.gov/api/temporal/daily/point",
            params={"parameters": POWER_PARAMS, "community": "AG", "longitude": lon,
                    "latitude": lat, "start": start, "end": end, "format": "JSON"},
            headers=UA, timeout=120)
        r.raise_for_status()
        return r.json()

    return _cached(f"power_{lat:.2f}_{lon:.2f}.json", 30, fetch)


def parse_power(raw: dict) -> list[dict]:
    """-> list of {date, tmin, tmax, rain, wind, rh, srad}; trailing gaps dropped,
    interior gaps filled with the previous day."""
    p = raw["properties"]["parameter"]
    keys = sorted(p["T2M_MIN"].keys())
    out, last = [], None
    for k in keys:
        row = {
            "date": f"{k[:4]}-{k[4:6]}-{k[6:]}",
            "tmin": p["T2M_MIN"][k], "tmax": p["T2M_MAX"][k], "rain": p["PRECTOTCORR"][k],
            "wind": p["WS2M"][k], "rh": p["RH2M"][k], "srad": p["ALLSKY_SFC_SW_DWN"][k],
        }
        if any(row[v] == -999 for v in ("tmin", "tmax", "rain")):
            if last is None:
                continue
            row = {**last, "date": row["date"], "filled": True}
        out.append(row)
        last = row
    while out and out[-1].get("filled"):
        out.pop()
    return out


def power_cell_elevation(raw: dict) -> float:
    return float(raw["geometry"]["coordinates"][2])


# ---------------------------------------------------------------- NOAA ENSO
def get_oni() -> list[dict]:
    """NOAA CPC Oceanic Niño Index: [{season:'DJF', year:2025, anom:-0.6}, ...]."""
    def fetch():
        r = httpx.get("https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt", headers=UA, timeout=30)
        r.raise_for_status()
        rows = []
        for line in r.text.splitlines()[1:]:
            parts = line.split()
            if len(parts) == 4:
                rows.append({"season": parts[0], "year": int(parts[1]), "anom": float(parts[3])})
        return rows

    return _cached("oni.json", 7, fetch)


def enso_phase(value: float | None) -> str:
    if value is None:
        return "unknown"
    return "el_nino" if value >= 0.5 else "la_nina" if value <= -0.5 else "neutral"


def oni_for_summer(oni: list[dict], year: int) -> float | None:
    """ENSO state that matters for a summer crop sown in Nov of `year`: the OND/NDJ value."""
    lookup = {(r["season"], r["year"]): r["anom"] for r in oni}
    for s in ("NDJ", "OND", "SON", "ASO"):
        if (s, year) in lookup:
            return lookup[(s, year)]
    return None


# ---------------------------------------------------------------- ISRIC SoilGrids
_SOILGRIDS_DOWN_UNTIL = 0.0


def get_soil(lat: float, lon: float) -> dict | None:
    """Topsoil (0-30 cm) sand/clay/SOC from SoilGrids 2.0; None if the service is down."""
    global _SOILGRIDS_DOWN_UNTIL
    if time.time() < _SOILGRIDS_DOWN_UNTIL:
        return None

    def fetch():
        r = httpx.get(
            "https://rest.isric.org/soilgrids/v2.0/properties/query",
            params=[("lon", lon), ("lat", lat), ("property", "sand"), ("property", "clay"),
                    ("property", "soc"), ("depth", "0-5cm"), ("depth", "5-15cm"),
                    ("depth", "15-30cm"), ("value", "mean")],
            headers=UA, timeout=8)
        r.raise_for_status()
        out = {}
        for layer in r.json()["properties"]["layers"]:
            vals = [d["values"]["mean"] for d in layer["depths"] if d["values"]["mean"] is not None]
            if vals:
                out[layer["name"]] = sum(vals) / len(vals) / layer["unit_measure"]["d_factor"]
        if "sand" not in out:
            raise ValueError("no data")
        return out  # sand %, clay %, soc g/kg

    try:
        return _cached(f"soil_{lat:.3f}_{lon:.3f}.json", 365, fetch)
    except Exception:
        _SOILGRIDS_DOWN_UNTIL = time.time() + 1800
        return None


def texture_class(sand: float, clay: float) -> str:
    if clay >= 35:
        return "clay"
    if clay >= 27:
        return "clay_loam"
    if sand >= 70:
        return "sandy_loam" if clay >= 10 else "loamy_sand"
    if sand >= 45:
        return "sandy_loam" if clay < 20 else "sandy_clay_loam"
    return "loam" if clay < 20 else "clay_loam"


# ---------------------------------------------------------------- Elevation (SRTM)
def get_elevation(lat: float, lon: float) -> float | None:
    """NASA SRTM 30 m via OpenTopoData (fallback when Earth Engine is unavailable)."""
    def fetch():
        r = httpx.get("https://api.opentopodata.org/v1/srtm30m", params={"locations": f"{lat},{lon}"},
                      headers=UA, timeout=15)
        r.raise_for_status()
        return r.json()["results"][0]["elevation"]

    try:
        return _cached(f"elev_{lat:.4f}_{lon:.4f}.json", 3650, fetch)
    except Exception:
        return None
