"""FastAPI entry point.

POST /simulate   -> compare rotations for a field (climate engine + rules)
POST /satellite  -> NASA satellite evidence for the field (Earth Engine; optional)
GET  /options    -> crops, strategies and soils for the UI
GET  /health     -> which data sources are reachable"""
from __future__ import annotations

import time
from pathlib import Path

from dotenv import load_dotenv

load_dotenv(Path(__file__).resolve().parent.parent / ".env")

from fastapi import FastAPI, HTTPException  # noqa: E402
from fastapi.middleware.cors import CORSMiddleware  # noqa: E402
from fastapi.staticfiles import StaticFiles  # noqa: E402
from pydantic import BaseModel, Field  # noqa: E402

from . import gee, sources  # noqa: E402
from .analysis import RULES, card, explain, run_strategy, score  # noqa: E402
from .crops import CROPS, DEFAULT_SOIL, SOILS, STRATEGIES  # noqa: E402
from .engine import Scenario, prepare  # noqa: E402

app = FastAPI(title="Rotation explorer (rehearsal)")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])


class Weights(BaseModel):
    """How much each criterion counts in the ranking (normalised server-side)."""
    success: float = 0.45   # winter crop success rate (sown + enough water + no frost/heat at flowering)
    summer: float = 0.2     # summer (soy) success rate, so a winter crop that hurts the soy is penalised
    soil: float = 0.25      # bare-soil days, erosion exposure, residue
    pests: float = 0.1      # crop-family repetition rule


class ScenarioIn(BaseModel):
    rain_scale: float = Field(1.0, ge=0.5, le=1.5)
    temp_shift_c: float = Field(0.0, ge=-2, le=4)


class SimIn(BaseModel):
    lat: float = Field(-17.40, ge=-60, le=70)
    lon: float = Field(-63.20, ge=-180, le=180)
    polygon: list[list[float]] | None = None          # [[lat, lon], ...]
    soil_texture: str | None = None
    current: str = "A"
    strategies: list[str] | None = None
    weights: Weights = Weights()
    scenario: ScenarioIn = ScenarioIn()
    prices: dict[str, float] = {}
    exclude_crops: list[str] = []
    slope_pct: float | None = None
    lang: str = "es"


@app.get("/health")
def health():
    return {"ok": True, "earth_engine": gee.status()}


@app.get("/options")
def options(lang: str = "es"):
    return {
        "crops": [{"id": k, "name": v[lang], "season": v.get("season"), "price": v["price"], "cost": v["cost"]}
                  for k, v in CROPS.items()],
        "strategies": [{"id": k, "name": v[lang], "cycle": v["cycle"]} for k, v in STRATEGIES.items()],
        "soils": [{"id": k, "name": v[lang]} for k, v in SOILS.items()],
    }


@app.post("/simulate")
def simulate_ep(body: SimIn):
    t0 = time.time()
    lang = "en" if body.lang == "en" else "es"
    warnings = []
    lat, lon = body.lat, body.lon
    if body.polygon:
        lat = sum(p[0] for p in body.polygon) / len(body.polygon)
        lon = sum(p[1] for p in body.polygon) / len(body.polygon)
    try:
        raw = sources.get_power(lat, lon)
    except Exception as e:
        raise HTTPException(502, f"NASA POWER unavailable: {e}")
    days = sources.parse_power(raw)

    cell_elev = sources.power_cell_elevation(raw)
    field_elev = sources.get_elevation(lat, lon)
    lapse = -0.0065 * (field_elev - cell_elev) if field_elev is not None else 0.0

    texture, soil_src = body.soil_texture, "input"
    sg = None
    if not texture:
        sg = sources.get_soil(lat, lon)
        if sg:
            texture, soil_src = sources.texture_class(sg["sand"], sg["clay"]), "soilgrids"
        else:
            texture, soil_src = DEFAULT_SOIL, "default"
            warnings.append("soilgrids_unavailable")
    if texture not in SOILS:
        raise HTTPException(400, f"unknown soil texture {texture}")

    slope = body.slope_pct
    if slope is None:
        try:
            slope = gee.srtm_terrain(lat, lon, body.polygon)["slope_pct"]
        except Exception:
            slope = 1.0
            warnings.append("slope_default")

    clim = prepare(days, lat, Scenario(body.scenario.rain_scale, body.scenario.temp_shift_c), lapse)
    oni = sources.get_oni()
    ids = body.strategies or list(STRATEGIES)
    if body.current not in ids:
        ids = [body.current] + ids
    strats = [run_strategy(clim, sid, texture, slope, body.prices, oni) for sid in ids]
    score(strats, body.weights.model_dump(), set(body.exclude_crops))
    by = {s["id"]: s for s in strats}
    for s in strats:
        s["name"] = STRATEGIES[s["id"]][lang]
        s["is_current"] = s["id"] == body.current
        s["card"] = card(s, by[body.current], lang)

    last = oni[-1]
    outlook = {"oni": last["anom"], "season": last["season"], "year": last["year"], "phase": sources.enso_phase(last["anom"])}
    return {
        "point": {"lat": lat, "lon": lon, "field_elevation_m": field_elev, "power_cell_elevation_m": cell_elev,
                  "lapse_c": round(lapse, 2), "soil": texture, "soil_source": soil_src, "slope_pct": slope},
        "period": {"start": days[0]["date"], "end": days[-1]["date"]},
        "current": body.current,
        "strategies": strats,
        "outlook": outlook,
        "explain": explain(strats, body.current, outlook, None, lang),
        "warnings": warnings,
        "rules": RULES,
        "data": data_evidence(days, raw, lat, lon, cell_elev, field_elev, slope, sg, texture, soil_src, oni, warnings),
        "sources": ["NASA POWER (daily, AG community)", "NASA SRTM (OpenTopoData / Earth Engine)",
                    "NOAA CPC ONI", "ISRIC SoilGrids 2.0", "FAO-56 / FAO-33 crop coefficients"],
        "compute_ms": round((time.time() - t0) * 1000),
    }


def data_evidence(days, raw, lat, lon, cell_elev, field_elev, slope, sg, texture, soil_src, oni, warnings):
    """The raw inputs behind the answer, summarised so the UI can show (and prove) them."""
    years = {}
    for d in days:
        y = years.setdefault(d["date"][:4], {"n": 0, "rain": 0.0, "tmax": 0.0, "tmin": 0.0, "srad": 0.0, "ns": 0})
        y["n"] += 1
        y["rain"] += d["rain"] or 0
        y["tmax"] += d["tmax"] or 0
        y["tmin"] += d["tmin"] or 0
        if (d.get("srad") or -999) > -900:
            y["srad"] += d["srad"]
            y["ns"] += 1
    annual = [{"year": int(k), "days": v["n"], "rain_mm": round(v["rain"]), "tmax_c": round(v["tmax"] / v["n"], 1),
               "tmin_c": round(v["tmin"] / v["n"], 1), "srad": round(v["srad"] / v["ns"], 1) if v["ns"] else None, "complete": v["n"] >= 365}
              for k, v in sorted(years.items())]
    params = list(raw.get("properties", {}).get("parameter", {}).keys())
    return {
        "power": {
            "dataset": "NASA POWER Daily (AG community)", "url": "https://power.larc.nasa.gov/api/temporal/daily/point",
            "query": {"latitude": round(lat, 4), "longitude": round(lon, 4), "start": days[0]["date"], "end": days[-1]["date"]},
            "parameters": params, "n_days": len(days), "cell_elevation_m": cell_elev,
            "annual": annual, "last_days": days[-14:],
        },
        "soil": {"dataset": "ISRIC SoilGrids 2.0 (0-30 cm)", "url": "https://rest.isric.org/soilgrids/v2.0/properties/query",
                 "values": {k: round(v, 1) for k, v in (sg or {}).items()}, "texture": texture, "source": soil_src},
        "terrain": {"dataset": "NASA SRTM 30 m (OpenTopoData / Earth Engine)", "elevation_m": field_elev, "slope_pct": slope,
                    "slope_source": "default" if "slope_default" in warnings else "srtm"},
        "enso": {"dataset": "NOAA CPC Oceanic Nino Index (ONI)", "url": "https://www.cpc.ncep.noaa.gov/data/indices/oni.ascii.txt",
                 "recent": oni[-24:]},
    }


class SatIn(BaseModel):
    lat: float = -17.40
    lon: float = -63.20
    polygon: list[list[float]] | None = None


@app.post("/satellite")
def satellite(body: SatIn):
    """NASA satellite evidence for the field. Each block fails independently."""
    out, errors = {}, {}
    for key, fn in (("imerg", gee.imerg_monthly), ("smap", gee.smap_recent),
                    ("landsat", gee.landsat_ndvi), ("terrain", gee.srtm_terrain)):
        try:
            out[key] = fn(body.lat, body.lon, body.polygon)
        except Exception as e:
            errors[key] = f"{type(e).__name__}: {e}"[:200]
    # derived: SMAP anomaly of the latest week, observed bare months from Landsat NDVI
    sm = [w for w in out.get("smap", []) if w.get("sm") is not None and w.get("clim")]
    if sm:
        out["smap_anomaly"] = round(sm[-1]["sm"] / sm[-1]["clim"] - 1, 3)
    nd = out.get("landsat", [])
    if nd:
        months = [0] * 12
        counts = [0] * 12
        for r in nd:
            m = int(r["month"][5:7]) - 1
            counts[m] += 1
            if r["ndvi"] < 0.35:
                months[m] += 1
        out["bare_month_share"] = [round(b / c, 2) if c else None for b, c in zip(months, counts)]
    return {"data": out, "errors": errors}


_dist = Path(__file__).resolve().parents[2] / "frontend" / "dist"
if _dist.exists():
    app.mount("/", StaticFiles(directory=_dist, html=True), name="web")
