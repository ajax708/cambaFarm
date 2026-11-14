# CambaFarm

**Earn money in winter.** CambaFarm shows soybean farmers in Santa Cruz, Bolivia, what would have happened on their own field over the last 45 winters if they had planted a winter crop instead of leaving the land bare (fallow), using NASA Earth observation data.

> Built for the NASA Space Apps Challenge 2026: *Field Shift: Adapting Farms with NASA Data*.

---

## The problem

After the summer soybean harvest, most fields in the Santa Cruz lowlands stay bare for months. That fallow period:

- earns nothing,
- leaves the soil exposed to erosion and losing organic matter,
- keeps pests and diseases cycling on a single crop.

Farmers know winter crops exist (wheat, sorghum, sunflower, cover crops), but they lack a simple way to see **how often each one would have worked on their own field** and **how much it would have paid**.

## What CambaFarm does

1. **Mark your field** on a satellite map (a pin or a drawn polygon).
2. **Tell us what you do in winter today** (rest, wheat, sorghum, sunflower or cover crop).
3. **See 45 winters replayed.** The engine runs every season since 1981 with the field's real daily climate for each rotation and compares it to what the farmer does today.

The answer is given in plain words:

- the best winter option and the extra income per hectare per year (and for the whole field, if a polygon was drawn);
- how many of the 45 winters it worked;
- how many months a year the soil stays bare, before and after;
- what happened in past years with the same El Niño / La Niña phase as the coming season;
- other options with a short label (*Recommended*, *Pays the most*, *The safest*, *Cares for your soil*);
- a priority switch: *A bit of everything*, *Earn more*, *Less risk* or *Care for the soil*.

A **Data** page shows every source behind the answer, with charts, tables and CSV / JSON downloads.

## Data sources

| Source | Provider | Used for |
|---|---|---|
| **NASA POWER** (daily, AG community) | NASA | 45 years of daily rain, temperature, wind, humidity and solar radiation that drive the crop simulation |
| **GPM IMERG** monthly (`NASA/GPM_L3/IMERG_MONTHLY_V07`) | NASA / JAXA | Satellite rainfall on the field |
| **SMAP L4** (`NASA/SMAP/SPL4SMGP/008`) | NASA | Current surface soil moisture vs. normal |
| **Landsat 8/9** C2 L2 | NASA / USGS | Field greenness (NDVI) and months with bare soil |
| **SRTM** 30 m | NASA | Elevation and slope |
| **SoilGrids 2.0** | ISRIC | Soil texture and organic carbon (0–30 cm) |
| **Oceanic Niño Index** | NOAA CPC | El Niño / La Niña phase |
| FAO-56 / FAO-33 | FAO | Crop water use and yield response coefficients |

GPM, SMAP, Landsat and SRTM slope are read through Google Earth Engine.

## How the engine works

For each rotation and each season since 1981, the engine runs these steps:

1. **Reference evapotranspiration:** the Hargreaves equation, using the daily NASA POWER weather corrected to the field's elevation.
2. **Soil water:** a two-layer bucket model, with water-holding capacity and infiltration set by the soil texture.
3. **Crop growth:** sowing happens when the topsoil is moist enough, and crop stages follow growing degree days.
4. **Yield:** water stress uses FAO-56 Ks and FAO-33 Ky. Heat and frost at flowering reduce it further.
5. **Soil cover and erosion:** canopy and residue cover are tracked day by day to count bare-soil days and estimate erosion exposure.
6. **Margin:** yield is multiplied by price, minus cost. Prices and costs are reference values the user can change.

The six rotations compared are:

| Code | Rotation |
|---|---|
| A | soy → fallow (typical today) |
| B | soy → wheat |
| C | soy → sorghum |
| D | soy → sunflower |
| E | soy → cover crop |
| F | soy → wheat / maize → cover crop (2 years) |

## Running it locally

**Requirements:** Python 3.11+ and Node.js 18+.

### Backend (FastAPI)

```bash
cd backend
python -m venv .venv
.venv/Scripts/activate          # Windows
# source .venv/bin/activate     # macOS / Linux
pip install -r requirements.txt
```

Create `backend/.env`:

```
EE_PROJECT=your-google-cloud-project-id
```

Authorize Earth Engine once. This is optional: without it the app still works, but the satellite cards show as offline.

```bash
earthengine authenticate
```

### Frontend (React + Vite)

```bash
cd frontend
npm install
npm run build        # builds into frontend/dist, served by the backend
```

### Start

```bash
cd backend
python -m uvicorn app.main:app --host 127.0.0.1 --port 8010
```

Open <http://127.0.0.1:8010>.

For frontend development with hot reload, run `npm run dev` inside `frontend/`. API calls go through `/api` and are proxied to port 8010.

## API

| Method | Path | Description |
|---|---|---|
| `GET` | `/health` | Service and Earth Engine status |
| `GET` | `/options?lang=es\|en` | Crops, rotations and soil types |
| `POST` | `/simulate` | Runs the 45-season comparison for a point or polygon. Returns rankings, per-season results, El Niño outlook and a `data` block with the raw inputs used |
| `POST` | `/satellite` | GPM, SMAP, Landsat and SRTM summaries for the field (each block fails independently) |

Example:

```bash
curl -X POST http://127.0.0.1:8010/simulate \
  -H "Content-Type: application/json" \
  -d '{"lat": -17.40, "lon": -63.20, "current": "A", "lang": "en"}'
```

No database is used. API responses are cached as JSON files in `backend/cache/`.

## Project structure

```
backend/
  app/
    main.py       API endpoints
    sources.py    NASA POWER, NOAA ONI, SoilGrids, elevation connectors
    gee.py        Earth Engine: GPM IMERG, SMAP, Landsat NDVI, SRTM
    engine.py     Daily crop and soil water simulation
    crops.py      Crop, soil and rotation parameters
    analysis.py   Indicators, scoring and explanations
frontend/
  src/
    App.jsx       Screens: home, field, loading, result
    DataPage.jsx  Data sources page with charts and downloads
    logic.js      Turns engine output into plain-language facts
    i18n.jsx      Spanish / English copy
docs/             Screen spec and design mockups
```

## Branches

| Branch | Content |
|---|---|
| `main` / `web` | Current version (desktop-first web layout + Data page) |
| `v1-movil` | First version with a phone-style layout |

## Limitations

- Crop, price and cost parameters are **provisional reference values** and still need calibration with local agronomic data. Winter crops currently look optimistic.
- NASA POWER climate represents a ~50 km cell, so a specific field can be wetter or drier.
- Nitrogen, pests and organic matter are estimated with agronomic rules, not field measurements.
- CambaFarm is a decision-support tool. It does not replace the farmer's judgment or local agronomists.

## Languages

The interface is available in **Spanish** (default) and **English**.
