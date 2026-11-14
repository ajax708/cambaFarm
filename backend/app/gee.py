"""NASA satellite products through Google Earth Engine (GPM IMERG, SMAP, Landsat, SRTM).

Every function takes a field polygon/point and returns small summaries (not images).
If Earth Engine is not authenticated the functions raise GeeUnavailable and the API
degrades gracefully."""
from __future__ import annotations

import json
import os
import time
from pathlib import Path

CACHE = Path(__file__).resolve().parent.parent / "cache"
PROJECT = os.getenv("EE_PROJECT", "")

_ee = None
_init_error: str | None = None


class GeeUnavailable(RuntimeError):
    pass


def _client():
    global _ee, _init_error
    if _ee is not None:
        return _ee
    if _init_error:
        raise GeeUnavailable(_init_error)
    try:
        import ee
        ee.Initialize(project=PROJECT or None)
        _ee = ee
        return ee
    except Exception as e:  # not authenticated, no project, no network
        _init_error = f"{type(e).__name__}: {e}"[:300]
        raise GeeUnavailable(_init_error)


def status() -> dict:
    try:
        _client()
        return {"ok": True, "project": PROJECT}
    except GeeUnavailable as e:
        return {"ok": False, "error": str(e)}


def _cached(name: str, max_age_days: float, fn):
    path = CACHE / name
    if path.exists() and (time.time() - path.stat().st_mtime) < max_age_days * 86400:
        return json.loads(path.read_text())
    data = fn()
    path.write_text(json.dumps(data))
    return data


def _geom(ee, lat, lon, polygon):
    if polygon:
        return ee.Geometry.Polygon([[[p[1], p[0]] for p in polygon]])
    return ee.Geometry.Point([lon, lat]).buffer(150)


def _key(lat, lon, polygon):
    if polygon:
        return "poly" + str(abs(hash(json.dumps(polygon))) % 10**10)
    return f"{lat:.4f}_{lon:.4f}"


# --------------------------------------------------------------- GPM IMERG
def imerg_monthly(lat, lon, polygon=None) -> list[dict]:
    """Monthly precipitation (mm) from GPM IMERG V07 monthly, 2001-present."""
    def run():
        ee = _client()
        g = _geom(ee, lat, lon, polygon).centroid().buffer(5000)
        col = ee.ImageCollection("NASA/GPM_L3/IMERG_MONTHLY_V07").select("precipitation")

        def per_img(img):
            days = ee.Date(img.get("system:time_start")).advance(1, "month").difference(
                ee.Date(img.get("system:time_start")), "day")
            v = img.reduceRegion(ee.Reducer.mean(), g, 10000).get("precipitation")
            return ee.Feature(None, {"t": img.date().format("YYYY-MM"), "mmhr": v, "days": days})

        feats = col.map(per_img).getInfo()["features"]
        return [{"month": f["properties"]["t"],
                 "rain_mm": round(f["properties"]["mmhr"] * 24 * f["properties"]["days"], 1)}
                for f in feats if f["properties"].get("mmhr") is not None]

    return _cached(f"imerg_{_key(lat, lon, polygon)}.json", 20, run)


# --------------------------------------------------------------- SMAP
def smap_recent(lat, lon, polygon=None, days=120) -> list[dict]:
    """Surface soil moisture (m3/m3) from SMAP L4 (3-hourly, 9 km) averaged per day,
    plus the same calendar days' climatology 2016-present for an anomaly."""
    def run():
        ee = _client()
        g = _geom(ee, lat, lon, polygon).centroid().buffer(4500)
        col = ee.ImageCollection("NASA/SMAP/SPL4SMGP/008").select("sm_surface")
        # latest image: look only at the last few weeks (sorting the whole collection runs out of memory)
        now = ee.Date(int(time.time() * 1000))
        end = ee.Date(col.filterDate(now.advance(-30, "day"), now).aggregate_max("system:time_start"))
        start = end.advance(-days, "day")
        n = ee.List.sequence(0, days - 1, 7)
        past_years = ee.List.sequence(1, 9)  # SMAP L4 starts in 2015

        def week_mean(d0):
            return col.filterDate(d0, d0.advance(7, "day")).mean()

        def per_week(i):
            d0 = start.advance(i, "day")
            v = week_mean(d0).reduceRegion(ee.Reducer.mean(), g, 9000).get("sm_surface")
            # climatology: the same week in each of the previous years
            clim_img = ee.ImageCollection(past_years.map(lambda y: week_mean(d0.advance(ee.Number(y).multiply(-1), "year")))).mean()
            clim = clim_img.reduceRegion(ee.Reducer.mean(), g, 9000).get("sm_surface")
            return ee.Feature(None, {"t": d0.format("YYYY-MM-dd"), "sm": v, "clim": clim})

        feats = ee.FeatureCollection(n.map(per_week)).getInfo()["features"]
        return [{"week": f["properties"]["t"], "sm": f["properties"].get("sm"),
                 "clim": f["properties"].get("clim")} for f in feats]

    return _cached(f"smap_{_key(lat, lon, polygon)}.json", 3, run)


# --------------------------------------------------------------- Landsat NDVI
def landsat_ndvi(lat, lon, polygon=None, start="2013-04-01") -> list[dict]:
    """Field NDVI from Landsat 8/9 Collection 2 Level 2 (30 m), cloud-masked,
    median per month."""
    def run():
        ee = _client()
        g = _geom(ee, lat, lon, polygon)

        def prep(img):
            qa = img.select("QA_PIXEL")
            clear = qa.bitwiseAnd(0b11111).eq(0)  # fill, dilated cloud, cirrus, cloud, shadow
            sr = img.select(["SR_B4", "SR_B5"]).multiply(0.0000275).add(-0.2)
            return sr.normalizedDifference(["SR_B5", "SR_B4"]).rename("ndvi").updateMask(clear) \
                .copyProperties(img, ["system:time_start"])

        col = ee.ImageCollection("LANDSAT/LC08/C02/T1_L2").merge(
            ee.ImageCollection("LANDSAT/LC09/C02/T1_L2")).filterBounds(g).filterDate(start, "2100-01-01").map(prep)

        def per_img(img):
            v = img.reduceRegion(ee.Reducer.median(), g, 30).get("ndvi")
            return ee.Feature(None, {"t": img.date().format("YYYY-MM-dd"), "ndvi": v})

        feats = col.map(per_img).filter(ee.Filter.notNull(["ndvi"])).getInfo()["features"]
        by_month: dict[str, list[float]] = {}
        for f in feats:
            by_month.setdefault(f["properties"]["t"][:7], []).append(f["properties"]["ndvi"])
        return [{"month": m, "ndvi": round(sorted(v)[len(v) // 2], 3), "n": len(v)}
                for m, v in sorted(by_month.items())]

    return _cached(f"landsat_{_key(lat, lon, polygon)}.json", 15, run)


# --------------------------------------------------------------- SRTM terrain
def srtm_terrain(lat, lon, polygon=None) -> dict:
    """Mean elevation (m) and slope (%) of the field from NASA SRTM 30 m."""
    def run():
        ee = _client()
        g = _geom(ee, lat, lon, polygon)
        dem = ee.Image("USGS/SRTMGL1_003")
        slope_deg = ee.Terrain.slope(dem)
        v = dem.rename("elev").addBands(slope_deg.rename("slope")).reduceRegion(
            ee.Reducer.mean(), g, 30).getInfo()
        import math
        return {"elevation_m": round(v["elev"], 1), "slope_pct": round(math.tan(math.radians(v["slope"])) * 100, 2)}

    return _cached(f"srtm_{_key(lat, lon, polygon)}.json", 3650, run)
