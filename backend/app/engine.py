"""Daily process engine: runs a rotation (summer + winter crops per campaign) over the
whole daily climate record of a point.

Per day: Hargreaves ET0 -> two-layer soil water balance with runoff limited by cover ->
crop phenology by growing degree days (GDD) -> FAO-56 water stress (Ks) -> FAO-33 yield
response by stage (Ky) -> heat/frost damage at flowering -> ground cover (canopy + residue)
-> erosion exposure. Campaign = Oct 1 (year Y) .. Sep 30 (Y+1)."""
from __future__ import annotations

import math
from dataclasses import dataclass, field
from datetime import date, timedelta

from .crops import CROPS, PROFILE_M, SOILS, TOP_M

GOOD, FAIR = 0.75, 0.50


@dataclass
class Scenario:
    rain_scale: float = 1.0
    temp_shift_c: float = 0.0


def _ra(lat: float, doy: int) -> float:
    """Extraterrestrial radiation (MJ m-2 day-1), FAO-56 eq. 21."""
    phi = math.radians(lat)
    dr = 1 + 0.033 * math.cos(2 * math.pi * doy / 365)
    d = 0.409 * math.sin(2 * math.pi * doy / 365 - 1.39)
    ws = math.acos(max(-1.0, min(1.0, -math.tan(phi) * math.tan(d))))
    return 24 * 60 / math.pi * 0.0820 * dr * (ws * math.sin(phi) * math.sin(d) + math.cos(phi) * math.cos(d) * math.sin(ws))


def prepare(days: list[dict], lat: float, sc: Scenario, lapse_c: float = 0.0) -> list[dict]:
    out = []
    for d in days:
        dt = date.fromisoformat(d["date"])
        tmin = d["tmin"] + sc.temp_shift_c + lapse_c
        tmax = d["tmax"] + sc.temp_shift_c + lapse_c
        tmean = (tmin + tmax) / 2
        et0 = 0.0023 * (tmean + 17.8) * math.sqrt(max(0.0, tmax - tmin)) * _ra(lat, dt.timetuple().tm_yday) * 0.408
        out.append({"d": dt, "tmin": tmin, "tmax": tmax, "rain": max(0.0, d["rain"]) * sc.rain_scale,
                    "et0": max(0.0, et0)})
    return out


@dataclass
class Soil:
    taw: float          # mm per m
    infil: float        # mm/day for bare soil
    top: float = 0.0
    deep: float = 0.0

    @property
    def top_cap(self):
        return self.taw * TOP_M

    @property
    def deep_cap(self):
        return self.taw * (PROFILE_M - TOP_M)

    def rain(self, mm: float, cover: float) -> tuple[float, float]:
        """Returns (runoff, drainage)."""
        cap = self.infil * (1 + 1.5 * cover)
        runoff = max(0.0, mm - cap)
        inf = mm - runoff
        self.top += inf
        drain = 0.0
        if self.top > self.top_cap:
            self.deep += self.top - self.top_cap
            self.top = self.top_cap
        if self.deep > self.deep_cap:
            drain = self.deep - self.deep_cap
            self.deep = self.deep_cap
        return runoff, drain

    def frac(self) -> float:
        return (self.top + self.deep) / (self.top_cap + self.deep_cap)


@dataclass
class CropRun:
    crop: str
    campaign: int
    season: str
    sow_start: date
    sow_end: date
    state: str = "waiting"           # waiting | growing | done | not_sown
    sown: date | None = None
    harvest: date | None = None
    gdd: float = 0.0
    eta: dict = field(default_factory=lambda: {"veg": 0.0, "flower": 0.0, "grain": 0.0})
    etm: dict = field(default_factory=lambda: {"veg": 0.0, "flower": 0.0, "grain": 0.0})
    heat_days: int = 0
    frost_loss: float = 0.0
    frost_events: int = 0
    forced: bool = False
    rain_mm: float = 0.0
    note: str = ""

    @property
    def c(self):
        return CROPS[self.crop]

    def stage(self) -> str:
        g = self.c["gdd"]
        if self.gdd < g["flower"]:
            return "veg"
        if self.gdd < g["flower_end"]:
            return "flower"
        return "grain"

    def kc(self) -> float:
        k0, km, ke = self.c["kc"]
        g = self.c["gdd"]
        fl = min(g["flower"], g["maturity"] * 0.5)
        x = self.gdd
        if x < 0.15 * fl:
            return k0
        if x < fl:
            return k0 + (km - k0) * (x - 0.15 * fl) / (0.85 * fl)
        if x < g["flower_end"] or g["flower_end"] >= g["maturity"]:
            return km
        return km + (ke - km) * min(1.0, (x - g["flower_end"]) / (g["maturity"] - g["flower_end"]))

    def canopy(self) -> float:
        g = self.c["gdd"]
        return self.c["max_cover"] * min(1.0, self.gdd / max(1.0, min(g["flower"], g["maturity"] * 0.6)))

    def root(self) -> float:
        g = self.c["gdd"]
        return 0.3 + (self.c["root_m"] - 0.3) * min(1.0, self.gdd / max(1.0, min(g["flower"], g["maturity"] * 0.6)))

    def result(self) -> dict:
        c = self.c
        base = {"crop": self.crop, "campaign": self.campaign, "season": self.season,
                "sown": self.sown.isoformat() if self.sown else None,
                "harvest": self.harvest.isoformat() if self.harvest else None, "rain_mm": round(self.rain_mm)}
        if self.state == "not_sown":
            return {**base, "rel": 0.0, "yield": 0, "class": "not_sown", "cause": "not_sown", "note": self.note,
                    "water": 0, "heat": 1, "frost": 1}
        water = 1.0
        stage_loss = {}
        for st, ky in c["ky"].items():
            if self.etm[st] > 0:
                f = max(0.0, 1 - ky * (1 - self.eta[st] / self.etm[st]))
                stage_loss[st] = 1 - f
                water *= f
        heat = max(0.6, 1 - 0.025 * self.heat_days)
        frost = 1 - min(0.8, self.frost_loss)
        late = 0.5 if self.forced else 1.0
        rel = max(0.0, water * heat * frost * late)
        losses = {"drought": 1 - water, "heat": 1 - heat, "frost": 1 - frost, "late": 1 - late}
        worst = max(losses, key=losses.get)
        cause = worst if losses[worst] >= 0.12 else "none"
        cls = "good" if rel >= GOOD else "fair" if rel >= FAIR else "bad"
        if c["potential"] == 0:   # cover crop: success = established and grew
            cls = "good" if rel >= 0.5 else "fair"
        drought_stage = max(stage_loss, key=stage_loss.get) if stage_loss else None
        return {**base, "rel": round(rel, 3), "yield": round(rel * c["potential"]), "class": cls, "cause": cause,
                "water": round(water, 3), "heat": round(heat, 3), "frost": round(frost, 3),
                "heat_days": self.heat_days, "frost_events": self.frost_events,
                "drought_stage": drought_stage if cause == "drought" else None, "note": self.note}


def _window(y: int, md: tuple[str, str], season: str) -> tuple[date, date]:
    """Summer windows fall in campaign year y (Oct-Dec); winter windows in y+1."""
    yy = y if season == "summer" else y + 1
    s = date.fromisoformat(f"{yy}-{md[0]}")
    e = date.fromisoformat(f"{yy}-{md[1]}")
    return s, e


def simulate(clim: list[dict], cycle: list[tuple[str, str]], texture: str, phase: int = 0) -> dict:
    """Run one rotation. Returns per-campaign records and a monthly cover/soil-water profile."""
    soil_p = SOILS[texture]
    soil = Soil(taw=soil_p["taw"], infil=soil_p["infil"])
    soil.top, soil.deep = soil.top_cap * 0.5, soil.deep_cap * 0.5

    first = clim[0]["d"]
    y0 = first.year if first <= date(first.year, 10, 1) else first.year + 1
    last = clim[-1]["d"]
    y_last = last.year - 1 if last >= date(last.year, 9, 30) else last.year - 2

    # plan: one summer + one winter item per campaign
    plan: list[CropRun] = []
    for k, y in enumerate(range(y0, y_last + 1)):
        summer, winter = cycle[(k + phase) % len(cycle)]
        for crop, season in ((summer, "summer"), (winter, "winter")):
            if crop == "barbecho":
                plan.append(CropRun(crop, y, season, date(y + 1, 3, 1), date(y + 1, 3, 1), state="fallow"))
            else:
                s, e = _window(y, CROPS[crop]["sow"], season)
                plan.append(CropRun(crop, y, season, s, e))

    camp = {y: {"campaign": y, "rain": 0.0, "bare_days": 0, "erosion": 0.0, "runoff": 0.0,
                "drain": 0.0, "cover_sum": 0.0, "days": 0} for y in range(y0, y_last + 1)}
    monthly: dict[str, list[float]] = {}
    cover_by_month = [[0.0, 0] for _ in range(12)]

    active: CropRun | None = None
    residue = 0.10
    residue_decay = 0.0
    i_plan = 0

    for day in clim:
        d = day["d"]
        if d < date(y0, 10, 1):
            continue
        cy = d.year if d.month >= 10 else d.year - 1
        if cy > y_last:
            break

        # move past fallow items / expired windows
        while i_plan < len(plan) and active is None:
            item = plan[i_plan]
            if item.state == "fallow":
                i_plan += 1
                continue
            if d > item.sow_end:
                item.state = "not_sown"
                item.note = item.note or "dry_soil"
                i_plan += 1
                continue
            break
        # sowing
        if active is None and i_plan < len(plan):
            item = plan[i_plan]
            if item.sow_start <= d <= item.sow_end:
                top_frac = soil.top / soil.top_cap
                if top_frac >= item.c["sow_frac"] or d == item.sow_end and top_frac >= item.c["sow_frac"] * 0.6:
                    item.state, item.sown, active = "growing", d, item
                    i_plan += 1
        # a winter item whose window ends while the summer crop is still growing
        if active is not None and i_plan < len(plan):
            nxt = plan[i_plan]
            if nxt.state == "waiting" and d > nxt.sow_end:
                nxt.state, nxt.note = "not_sown", "previous_crop_late"
                i_plan += 1

        cover = residue
        if active is not None:
            cover = max(residue, active.canopy())

        runoff, drain = soil.rain(day["rain"], cover)
        et0 = day["et0"]

        if active is not None:
            c = active.c
            tmean = (day["tmin"] + day["tmax"]) / 2
            active.gdd += max(0.0, min(tmean, 32.0) - c["t_base"])
            active.rain_mm += day["rain"]
            st = active.stage()
            kc = active.kc()
            root = active.root()
            fa = min(1.0, root / TOP_M)
            fd = max(0.0, (root - TOP_M) / (PROFILE_M - TOP_M))
            cap = soil.top_cap * fa + soil.deep_cap * fd
            avail = soil.top * fa + soil.deep * fd
            w = avail / cap if cap > 0 else 0
            ks = 1.0 if w >= (1 - c["p"]) else max(0.0, w / (1 - c["p"]))
            etm = kc * et0
            eta = min(ks * etm, avail)
            take_top = min(eta, soil.top * fa)
            soil.top -= take_top
            soil.deep = max(0.0, soil.deep - (eta - take_top))
            active.etm[st] += etm
            active.eta[st] += eta
            if st == "flower" and day["tmax"] > c["heat"]:
                active.heat_days += 1
            if c.get("frost") is not None and st in ("flower", "grain") and day["tmin"] < c["frost"]:
                active.frost_loss = 1 - (1 - active.frost_loss) * (1 - (0.30 if st == "flower" else 0.15))
                active.frost_events += 1
            soil.top = max(0.0, soil.top - et0 * 0.10 * (1 - cover) * (soil.top / soil.top_cap))
            # end of crop
            age = (d - active.sown).days
            limit_end = date(active.campaign + (1 if active.season == "summer" else 1), 9 if active.season == "winter" else 6, 30)
            if active.gdd >= c["gdd"]["maturity"] or age > 210 or d >= limit_end:
                active.forced = active.gdd < c["gdd"]["maturity"] and c["potential"] > 0
                active.harvest, active.state = d, "done"
                r = active.result()
                residue = c["residue_cover"] * max(0.3, r["rel"] if c["potential"] else 1.0)
                residue_decay = residue / (150 if active.crop == "cobertura" else 110)
                active = None
        else:
            evap = et0 * 0.5 * (1 - cover) * (soil.top / soil.top_cap)
            soil.top = max(0.0, soil.top - evap)
            residue = max(0.08, residue - residue_decay)

        # bookkeeping
        cmp_ = camp[cy]
        cmp_["rain"] += day["rain"]
        cmp_["runoff"] += runoff
        cmp_["drain"] += drain
        cmp_["cover_sum"] += cover
        cmp_["days"] += 1
        if cover < 0.30:
            cmp_["bare_days"] += 1
        if day["rain"] > 12.7:
            cmp_["erosion"] += (day["rain"] ** 2 / 100) * (1 - cover)
        cover_by_month[d.month - 1][0] += cover
        cover_by_month[d.month - 1][1] += 1
        monthly.setdefault(d.strftime("%Y-%m"), []).append(soil.frac())

    results = [p.result() for p in plan if p.state in ("done", "not_sown")]
    by_c: dict[int, dict] = {}
    for r in results:
        by_c.setdefault(r["campaign"], {})[r["season"]] = r
    campaigns = []
    for y, cmp_ in camp.items():
        if cmp_["days"] < 300:
            continue
        summer, winter = cycle[((y - y0) + phase) % len(cycle)]
        rec = {"campaign": y, "label": f"{y}-{str(y + 1)[2:]}", "rain": round(cmp_["rain"]),
               "runoff": round(cmp_["runoff"]), "drain": round(cmp_["drain"]),
               "bare_days": cmp_["bare_days"], "erosion": round(cmp_["erosion"], 1),
               "mean_cover": round(cmp_["cover_sum"] / cmp_["days"], 3),
               "summer": by_c.get(y, {}).get("summer"),
               "winter": by_c.get(y, {}).get("winter") if winter != "barbecho" else
               {"crop": "barbecho", "class": "fallow", "rel": 0, "yield": 0, "cause": "none", "campaign": y, "season": "winter"}}
        campaigns.append(rec)
    return {
        "campaigns": campaigns,
        "cover_by_month": [round(s / n, 3) if n else None for s, n in cover_by_month],
        "soil_water_monthly": [{"month": m, "frac": round(sum(v) / len(v), 3)} for m, v in monthly.items()],
    }
