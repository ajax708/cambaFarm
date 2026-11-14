"""Indicators, multi-criteria scoring and template explanations.

Each indicator carries a `basis` tag so the UI can show where it comes from:
  data  -> computed from NASA observations through the engine
  rule  -> agronomic rule of thumb (literature), not measured on the field
  input -> provided or overridable by the farmer"""
from __future__ import annotations

from statistics import mean

from .crops import CROPS, GAPS, SOILS, STRATEGIES, TRAIT_TEXT
from .engine import simulate
from .sources import enso_phase, oni_for_summer

PEST_PAIR = {("legume", "legume"): 1.0, ("grass", "grass"): 0.5, ("composite", "composite"): 1.0}


def _crop_name(cid, lang):
    return CROPS[cid][lang]


def _margin(r: dict | None, prices: dict) -> float:
    if not r:
        return 0.0
    crop = r["crop"]
    c = CROPS[crop]
    if r.get("class") == "not_sown":
        return 0.0
    price = prices.get(crop, c["price"])
    return r.get("yield", 0) * price - c["cost"]


def pest_index(cycle) -> float:
    """Rule: same-family crops back to back (fallow skipped, cover crop breaks the chain),
    plus how often soybean (main host of rust/nematodes/stink bugs) is in the field."""
    seq = []
    for s, w in cycle * 2:
        seq += [s, w]
    seq = [c for c in seq if c != "barbecho"]
    pairs = [(CROPS[a]["family"], CROPS[b]["family"]) for a, b in zip(seq, seq[1:])]
    repeat = mean(PEST_PAIR.get(p, 0.0) for p in pairs) if pairs else 0.0
    soy_share = sum(1 for s, _ in cycle if s == "soya") / len(cycle)
    return round(repeat + 0.5 * soy_share, 2)


def run_strategy(clim, sid: str, texture: str, slope_pct: float, prices: dict, oni) -> dict:
    st = STRATEGIES[sid]
    cycle = st["cycle"]
    runs = [simulate(clim, cycle, texture, ph) for ph in range(len(cycle))]
    camps = [c for r in runs for c in r["campaigns"]]
    erod = SOILS[texture]["erod"] * (1 + slope_pct / 5)

    margins, crop_seasons, drought, om, nbal = [], [], 0, [], []
    for c in camps:
        m = _margin(c["summer"], prices) + (_margin(c["winter"], prices) if c["winter"] else 0)
        c["margin"] = round(m)
        margins.append(m)
        for key in ("summer", "winter"):
            r = c[key]
            if not r or r["crop"] == "barbecho":
                if r:
                    om.append(CROPS["barbecho"]["residue_t"])
                continue
            crop = CROPS[r["crop"]]
            if crop["potential"] > 0:
                crop_seasons.append(r)
                if r["cause"] in ("drought", "not_sown"):
                    drought += 1
            om.append(crop["residue_t"] * (r["rel"] if crop["potential"] else (1 if r["class"] != "not_sown" else 0)))
            nbal.append(crop["n_balance"] if r["class"] != "not_sown" else 0)
        c["enso"] = enso_phase(oni_for_summer(oni, c["campaign"]))

    n = len(camps)
    phase_runs = []
    for ph, r in enumerate(runs):
        phase_runs.append({"phase": ph, "campaigns": r["campaigns"]})

    summer = [c["summer"] for c in camps if c["summer"]]
    main_bad = sum(1 for r in summer if r["class"] in ("bad", "not_sown"))
    by_enso = {}
    for ph in ("el_nino", "la_nina", "neutral"):
        sub = [c for c in camps if c["enso"] == ph]
        if sub:
            by_enso[ph] = {
                "n": len(sub),
                "bad_summer_share": round(sum(1 for c in sub if c["summer"] and c["summer"]["class"] in ("bad", "not_sown")) / len(sub), 3),
                "mean_margin": round(mean(c["margin"] for c in sub)),
                "loss_share": round(sum(1 for c in sub if c["margin"] < 0) / len(sub), 3),
            }
    sorted_m = sorted(margins)
    p10 = sorted_m[max(0, int(len(sorted_m) * 0.1) - 1)]
    ind = {
        "margin": {"value": round(mean(margins)), "unit": "USD/ha/año", "basis": "data+input"},
        "margin_p10": {"value": round(p10), "unit": "USD/ha/año", "basis": "data+input"},
        "loss_share": {"value": round(sum(1 for m in margins if m < 0) / n, 3), "unit": "share", "basis": "data+input"},
        "bad_summer_share": {"value": round(main_bad / len(summer), 3) if summer else 0, "unit": "share", "basis": "data"},
        "drought_share": {"value": round(drought / len(crop_seasons), 3) if crop_seasons else 0, "unit": "share", "basis": "data"},
        "bare_days": {"value": round(mean(c["bare_days"] for c in camps)), "unit": "días/año", "basis": "data"},
        "erosion": {"value": round(mean(c["erosion"] for c in camps) * erod, 1), "unit": "índice", "basis": "data+rule"},
        "runoff": {"value": round(mean(c["runoff"] for c in camps)), "unit": "mm/año", "basis": "data"},
        "organic_matter": {"value": round(sum(om) / n, 1), "unit": "t rastrojo/ha/año", "basis": "rule+data"},
        "n_balance": {"value": round(sum(nbal) / n), "unit": "kg N/ha/año", "basis": "rule"},
        "pest_risk": {"value": pest_index(cycle), "unit": "índice", "basis": "rule"},
        "crops_per_year": {"value": round(len(crop_seasons) / n, 2), "unit": "cosechas/año", "basis": "data"},
    }
    crops_in = sorted({c for pair in cycle for c in pair})
    return {
        "id": sid, "cycle": cycle, "crops": crops_in, "n_campaigns": n,
        "indicators": ind, "by_enso": by_enso, "phases": phase_runs,
        "cover_by_month": [round(mean(x for x in col if x is not None), 3)
                           for col in zip(*[r["cover_by_month"] for r in runs])],
        "soil_water_monthly": runs[0]["soil_water_monthly"],
    }


def score(strats: list[dict], weights: dict, excluded: set[str]) -> None:
    def norm(vals, invert=False):
        lo, hi = min(vals), max(vals)
        return [(1 - (v - lo) / (hi - lo) if invert else (v - lo) / (hi - lo)) if hi > lo else 1.0 for v in vals]

    g = lambda k: [s["indicators"][k]["value"] for s in strats]
    income = norm(g("margin"))
    stab = [0.5 * a + 0.5 * b for a, b in zip(norm(g("loss_share"), True), norm(g("margin_p10")))]
    soil = [0.4 * a + 0.3 * b + 0.3 * c for a, b, c in
            zip(norm(g("erosion"), True), norm(g("organic_matter")), norm(g("n_balance")))]
    water = norm(g("drought_share"), True)
    pest = norm(g("pest_risk"), True)
    tot = sum(weights.values()) or 1
    for i, s in enumerate(strats):
        sub = {"income": income[i], "stability": stab[i], "soil": soil[i], "water": water[i], "pests": pest[i]}
        s["subscores"] = {k: round(v * 100) for k, v in sub.items()}
        s["score"] = round(100 * sum(weights.get(k, 0) * v for k, v in sub.items()) / tot)
        s["excluded"] = [c for c in s["crops"] if c in excluded]
    order = sorted(strats, key=lambda s: (bool(s["excluded"]), -s["score"]))
    for r, s in enumerate(order, 1):
        s["rank"] = r


def _pct(x):
    return f"{round(x * 100)} %"


def card(s: dict, base: dict, lang: str) -> dict:
    st = STRATEGIES[s["id"]]
    I, B = s["indicators"], base["indicators"]
    es = lang == "es"
    ev, ben, risk = [], [], []

    def add_ev(text, basis):
        ev.append({"text": text, "basis": basis})

    add_ev((f"Ganancia media {I['margin']['value']} USD/ha/año; en el 10 % de peores años {I['margin_p10']['value']} USD/ha."
            if es else f"Mean margin {I['margin']['value']} USD/ha/yr; worst 10 % of years {I['margin_p10']['value']} USD/ha."),
           "data+input")
    add_ev((f"Soya/maíz de verano con mala campaña en {_pct(I['bad_summer_share']['value'])} de {s['n_campaigns']} campañas simuladas con clima NASA POWER desde 1981."
            if es else f"Poor summer crop in {_pct(I['bad_summer_share']['value'])} of {s['n_campaigns']} campaigns simulated with NASA POWER climate since 1981."),
           "data")
    add_ev((f"Suelo desnudo {I['bare_days']['value']} días al año (cobertura < 30 %)." if es
            else f"Bare soil {I['bare_days']['value']} days per year (cover < 30 %)."), "data")
    add_ev((f"Rastrojo aportado ≈ {I['organic_matter']['value']} t/ha/año; balance de nitrógeno ≈ {I['n_balance']['value']} kg N/ha/año."
            if es else f"Residue ≈ {I['organic_matter']['value']} t/ha/yr; nitrogen balance ≈ {I['n_balance']['value']} kg N/ha/yr."), "rule")

    if s["id"] != base["id"]:
        d_bare = B["bare_days"]["value"] - I["bare_days"]["value"]
        if d_bare > 20:
            ben.append(f"{d_bare} días menos de suelo desnudo que tu rotación actual." if es
                       else f"{d_bare} fewer bare-soil days than your current rotation.")
        d_er = (B["erosion"]["value"] - I["erosion"]["value"]) / max(1, B["erosion"]["value"])
        if d_er > 0.1:
            ben.append(f"Exposición a erosión {round(d_er * 100)} % menor." if es else f"Erosion exposure {round(d_er * 100)} % lower.")
        d_m = I["margin"]["value"] - B["margin"]["value"]
        if d_m > 20:
            ben.append(f"+{d_m} USD/ha/año de ingreso extra en promedio." if es else f"+{d_m} USD/ha/yr extra income on average.")
        elif d_m < -20:
            risk.append(f"{d_m} USD/ha/año menos de ingreso que la rotación actual." if es else f"{d_m} USD/ha/yr less income than the current rotation.")
        if I["pest_risk"]["value"] < B["pest_risk"]["value"]:
            ben.append("Corta el ciclo de plagas y enfermedades (no repite la misma familia)." if es
                       else "Breaks pest and disease cycles (no back-to-back same family).")
        if I["n_balance"]["value"] > B["n_balance"]["value"] + 10:
            ben.append("Mejor balance de nitrógeno para el cultivo siguiente." if es else "Better nitrogen balance for the next crop.")
        if I["loss_share"]["value"] > B["loss_share"]["value"] + 0.05:
            risk.append(f"Más años con pérdida económica ({_pct(I['loss_share']['value'])})." if es
                        else f"More years with an economic loss ({_pct(I['loss_share']['value'])}).")
    for c in s["crops"]:
        for t in CROPS[c].get("traits", []):
            txt = f"{_crop_name(c, lang)}: {TRAIT_TEXT[t][lang]}."
            if txt not in ben:
                ben.append(txt)
    crop_risks = {
        "trigo": ("El trigo de invierno depende del agua guardada; vigilar brusone y heladas tardías.",
                  "Winter wheat relies on stored water; watch for blast disease and late frosts."),
        "girasol": ("Girasol: daño por aves y precio variable.", "Sunflower: bird damage and volatile prices."),
        "cobertura": ("La cobertura no genera ingreso directo y requiere semilla y manejo para terminarla.",
                      "The cover crop gives no direct income and needs seed and termination management."),
        "maiz": ("El maíz exige más nitrógeno y es sensible a sequía en floración.",
                 "Maize needs more nitrogen and is sensitive to drought at flowering."),
        "sorgo": ("Sorgo: mercado local más chico; consulta si hay comprador.", "Sorghum: smaller local market; check for buyers."),
    }
    for c in s["crops"]:
        if c in crop_risks:
            risk.append(crop_risks[c][0 if es else 1])
    if s["id"] == "A":
        risk.append("Soya todos los años mantiene roya, nematodos y chinches; suelo desnudo en la época seca y ventosa."
                    if es else "Soybean every year sustains rust, nematodes and stink bugs; bare soil in the dry, windy season.")
    return {"why": st["why_es" if es else "why_en"], "evidence": ev, "benefits": ben, "risks": risk, "gaps": GAPS[lang]}


def explain(strats: list[dict], current_id: str, outlook: dict, sat: dict | None, lang: str) -> list[str]:
    es = lang == "es"
    by = {s["id"]: s for s in strats}
    ranked = sorted([s for s in strats if not s["excluded"]], key=lambda s: s["rank"])
    best, cur = ranked[0], by[current_id]
    name = lambda s: STRATEGIES[s["id"]][lang]
    out = []
    if best["id"] == cur["id"]:
        out.append(f"Con tus prioridades, tu rotación actual ({name(cur)}) sigue siendo la mejor opción." if es
                   else f"With your priorities, your current rotation ({name(cur)}) remains the best option.")
        alt = ranked[1] if len(ranked) > 1 else None
    else:
        out.append(f"Con tus prioridades, la opción más conveniente es **{name(best)}** ({best['score']} puntos frente a {cur['score']} de tu rotación actual)."
                   if es else f"With your priorities, the best option is **{name(best)}** ({best['score']} points vs {cur['score']} for your current rotation).")
        alt = best
    if alt:
        I, C = alt["indicators"], cur["indicators"]
        out.append((f"Frente a {name(cur)}: suelo desnudo {C['bare_days']['value']} → {I['bare_days']['value']} días/año, "
                    f"ganancia media {C['margin']['value']} → {I['margin']['value']} USD/ha/año, "
                    f"años con pérdida {_pct(C['loss_share']['value'])} → {_pct(I['loss_share']['value'])}.")
                   if es else
                   (f"Compared with {name(cur)}: bare soil {C['bare_days']['value']} → {I['bare_days']['value']} days/yr, "
                    f"mean margin {C['margin']['value']} → {I['margin']['value']} USD/ha/yr, "
                    f"loss years {_pct(C['loss_share']['value'])} → {_pct(I['loss_share']['value'])}."))
    ph = outlook.get("phase")
    if ph in ("el_nino", "la_nina"):
        e = cur["by_enso"].get(ph)
        if e:
            label = {"el_nino": "El Niño", "la_nina": "La Niña"}[ph]
            out.append((f"NOAA reporta {label} (ONI {outlook['oni']:+.1f}). En las {e['n']} campañas pasadas con {label}, "
                        f"tu rotación actual tuvo mala campaña de verano en {_pct(e['bad_summer_share'])} de los años.")
                       if es else
                       (f"NOAA reports {label} (ONI {outlook['oni']:+.1f}). In the {e['n']} past {label} campaigns, "
                        f"your current rotation had a poor summer crop in {_pct(e['bad_summer_share'])} of the years."))
    if sat and sat.get("smap_anomaly") is not None:
        a = sat["smap_anomaly"]
        out.append((f"El satélite SMAP de la NASA ve el suelo {'más húmedo' if a > 0 else 'más seco'} que lo normal para esta época ({a:+.0%})."
                    if es else f"NASA's SMAP satellite sees the soil {'wetter' if a > 0 else 'drier'} than normal for this time of year ({a:+.0%})."))
    out.append("Esto es una guía basada en datos y reglas generales: confírmalo con tu técnico y tu experiencia en el campo."
               if es else "This is guidance from data and general rules: confirm it with your agronomist and your own field experience.")
    return out
