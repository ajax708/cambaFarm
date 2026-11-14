"""Crop library, soils and rotation strategies for the Santa Cruz (Bolivia) pilot.

All agronomic values are PROVISIONAL defaults taken from FAO-56 (Kc), FAO-33 (Ky) and
general literature; the agronomy lead must review them. Prices/costs are rough
reference values the farmer can override."""

SOILS = {
    # available water (mm per m of soil), erodibility (relative), infiltration cap (mm/day, bare)
    "loamy_sand":      {"taw": 90,  "erod": 1.10, "infil": 60, "es": "Franco arenoso suelto", "en": "Loamy sand"},
    "sandy_loam":      {"taw": 120, "erod": 1.00, "infil": 45, "es": "Franco arenoso", "en": "Sandy loam"},
    "sandy_clay_loam": {"taw": 140, "erod": 0.85, "infil": 35, "es": "Franco arcillo arenoso", "en": "Sandy clay loam"},
    "loam":            {"taw": 160, "erod": 0.90, "infil": 35, "es": "Franco", "en": "Loam"},
    "clay_loam":       {"taw": 170, "erod": 0.70, "infil": 25, "es": "Franco arcilloso", "en": "Clay loam"},
    "clay":            {"taw": 180, "erod": 0.60, "infil": 20, "es": "Arcilloso", "en": "Clay"},
}
DEFAULT_SOIL = "sandy_clay_loam"
TOP_M, PROFILE_M = 1.0, 1.8   # two soil layers: 0-1.0 m and 1.0-1.8 m

# family: used by the pest-cycle rule; n_balance: kg N/ha/season (+ adds, - removes), rule-based;
# residue_t: dry residue left at full yield (t/ha) for the organic-matter rule.
CROPS = {
    "soya": {
        "es": "Soya", "en": "Soybean", "family": "legume", "season": "summer",
        "t_base": 10, "sow": ("11-01", "12-31"), "sow_frac": 0.45,
        "gdd": {"flower": 900, "flower_end": 1300, "maturity": 2000},
        "kc": (0.40, 1.15, 0.50), "ky": {"veg": 0.20, "flower": 0.80, "grain": 0.60},
        "root_m": 1.2, "p": 0.50, "heat": 36, "frost": None,
        "potential": 3200, "price": 0.38, "cost": 420,
        "max_cover": 0.95, "residue_cover": 0.30, "residue_t": 2.5, "n_balance": 10,
        "traits": ["n_fixing"],
    },
    "maiz": {
        "es": "Maíz", "en": "Maize", "family": "grass", "season": "summer",
        "t_base": 10, "sow": ("10-15", "12-15"), "sow_frac": 0.50,
        "gdd": {"flower": 1300, "flower_end": 1600, "maturity": 2600},
        "kc": (0.30, 1.20, 0.60), "ky": {"veg": 0.40, "flower": 1.50, "grain": 0.50},
        "root_m": 1.5, "p": 0.55, "heat": 35, "frost": None,
        "potential": 6500, "price": 0.19, "cost": 600,
        "max_cover": 0.95, "residue_cover": 0.70, "residue_t": 7.0, "n_balance": -60,
        "traits": ["high_residue"],
    },
    "trigo": {
        "es": "Trigo", "en": "Wheat", "family": "grass", "season": "winter",
        "t_base": 0, "sow": ("04-15", "05-31"), "sow_frac": 0.35,
        "gdd": {"flower": 1000, "flower_end": 1250, "maturity": 1900},
        "kc": (0.30, 1.15, 0.40), "ky": {"veg": 0.20, "flower": 0.65, "grain": 0.55},
        "root_m": 1.2, "p": 0.55, "heat": 32, "frost": -1.0,
        "potential": 2500, "price": 0.26, "cost": 380,
        "max_cover": 0.85, "residue_cover": 0.50, "residue_t": 3.5, "n_balance": -40,
        "traits": [],
    },
    "sorgo": {
        "es": "Sorgo", "en": "Sorghum", "family": "grass", "season": "winter",
        "t_base": 10, "sow": ("02-15", "04-15"), "sow_frac": 0.30,
        "gdd": {"flower": 900, "flower_end": 1150, "maturity": 1800},
        "kc": (0.30, 1.00, 0.55), "ky": {"veg": 0.20, "flower": 0.55, "grain": 0.45},
        "root_m": 1.6, "p": 0.60, "heat": 38, "frost": 0.0,
        "potential": 4000, "price": 0.15, "cost": 300,
        "max_cover": 0.85, "residue_cover": 0.70, "residue_t": 6.0, "n_balance": -40,
        "traits": ["drought_tolerant", "high_residue", "deep_roots"],
    },
    "girasol": {
        "es": "Girasol", "en": "Sunflower", "family": "composite", "season": "winter",
        "t_base": 6, "sow": ("03-01", "04-30"), "sow_frac": 0.30,
        "gdd": {"flower": 900, "flower_end": 1150, "maturity": 1700},
        "kc": (0.35, 1.10, 0.35), "ky": {"veg": 0.25, "flower": 0.70, "grain": 0.40},
        "root_m": 1.8, "p": 0.45, "heat": 36, "frost": -1.0,
        "potential": 1800, "price": 0.40, "cost": 330,
        "max_cover": 0.80, "residue_cover": 0.30, "residue_t": 3.0, "n_balance": -25,
        "traits": ["deep_roots"],
    },
    "cobertura": {
        "es": "Cultivo de cobertura (crotalaria + avena)", "en": "Cover crop (crotalaria + oats)",
        "family": "cover", "season": "winter",
        "t_base": 5, "sow": ("03-15", "05-15"), "sow_frac": 0.25,
        "gdd": {"flower": 9999, "flower_end": 9999, "maturity": 1500},
        "kc": (0.35, 0.90, 0.90), "ky": {"veg": 0.0, "flower": 0.0, "grain": 0.0},
        "root_m": 1.2, "p": 0.60, "heat": 99, "frost": None,
        "potential": 0, "price": 0.0, "cost": 70,
        "max_cover": 0.85, "residue_cover": 0.85, "residue_t": 4.0, "n_balance": 30,
        "traits": ["n_fixing", "cover", "high_residue"],
    },
    "barbecho": {
        "es": "Barbecho (suelo desnudo)", "en": "Fallow (bare soil)", "family": "fallow", "season": "winter",
        "cost": 25, "residue_t": 0.3, "n_balance": 0, "max_cover": 0.10, "traits": [],
        "potential": 0, "price": 0.0,
    },
}

# A rotation = list of campaigns; each campaign = (summer crop, winter crop). The cycle repeats.
STRATEGIES = {
    "A": {"cycle": [("soya", "barbecho")],
          "es": "Soya → barbecho de invierno", "en": "Soybean → winter fallow",
          "why_es": "Es la práctica más común: una soya por año y el campo queda sin cultivo en invierno.",
          "why_en": "The most common practice: one soybean crop per year, field left idle in winter."},
    "B": {"cycle": [("soya", "trigo")],
          "es": "Soya → trigo", "en": "Soybean → wheat",
          "why_es": "Aprovecha el invierno con un cereal que deja rastrojo y corta el ciclo de plagas de la soya.",
          "why_en": "Uses the winter with a cereal that leaves residue and breaks the soybean pest cycle."},
    "C": {"cycle": [("soya", "sorgo")],
          "es": "Soya → sorgo", "en": "Soybean → sorghum",
          "why_es": "El sorgo aguanta la sequía de invierno, tiene raíces profundas y deja mucho rastrojo.",
          "why_en": "Sorghum tolerates the dry winter, roots deeply and leaves a lot of residue."},
    "D": {"cycle": [("soya", "girasol")],
          "es": "Soya → girasol", "en": "Soybean → sunflower",
          "why_es": "El girasol usa agua profunda que la soya no alcanza y da un ingreso extra en invierno.",
          "why_en": "Sunflower uses deep water soybean cannot reach and adds winter income."},
    "E": {"cycle": [("soya", "cobertura")],
          "es": "Soya → cultivo de cobertura", "en": "Soybean → cover crop",
          "why_es": "No se cosecha, pero protege el suelo, aporta nitrógeno y materia orgánica.",
          "why_en": "Not harvested, but protects the soil and adds nitrogen and organic matter."},
    "F": {"cycle": [("soya", "trigo"), ("maiz", "cobertura")],
          "es": "Soya → trigo / maíz → cobertura (2 años)", "en": "Soybean → wheat / maize → cover (2 years)",
          "why_es": "Alterna soya y maíz en verano: corta plagas y enfermedades de la soya y diversifica.",
          "why_en": "Alternates soybean and maize in summer: breaks soybean pests and diversifies."},
}

TRAIT_TEXT = {
    "n_fixing": {"es": "fija nitrógeno del aire (leguminosa)", "en": "fixes nitrogen from the air (legume)"},
    "high_residue": {"es": "deja mucho rastrojo que protege el suelo y forma materia orgánica",
                     "en": "leaves lots of residue that protects soil and builds organic matter"},
    "deep_roots": {"es": "raíces profundas: usa agua de abajo y rompe la compactación",
                   "en": "deep roots: uses deep water and breaks compaction"},
    "drought_tolerant": {"es": "tolera la sequía", "en": "drought tolerant"},
    "cover": {"es": "cubre el suelo en la época seca y ventosa", "en": "covers the soil in the dry, windy season"},
}

GAPS = {
    "es": [
        "Precios y costos son valores de referencia: cámbialos por los tuyos.",
        "Nitrógeno, plagas y materia orgánica se estiman con reglas agronómicas, no con mediciones de tu campo.",
        "No modelamos enfermedades específicas, malezas resistentes ni anegamiento.",
        "El clima viene de una celda de ~50 km: tu campo puede ser más seco o más húmedo.",
    ],
    "en": [
        "Prices and costs are reference values: replace them with yours.",
        "Nitrogen, pests and organic matter are estimated with agronomic rules, not field measurements.",
        "We do not model specific diseases, resistant weeds or waterlogging.",
        "Climate comes from a ~50 km cell: your field may be drier or wetter.",
    ],
}
