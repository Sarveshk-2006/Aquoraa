# AQUORA — Urban Flood Intelligence & Emergency Response Platform

> **See the flood before it becomes a crisis.**

Aquora is an end-to-end urban flood intelligence platform engineered for high-resolution hydraulic forecasting, flood-aware critical access routing, satellite evidence corroboration, and real-time emergency responder decision support.

---

## 🌊 What Aquora Does

Aquora integrates physical hydrology, remote sensing, spatial analytics, and machine learning to give municipal response teams early visibility into urban flood dynamics. It converts raw satellite imagery, elevation models, meteorological feeds, and terrain topography into actionable exposure timelines, route safety windows, and prioritized asset protection strategies.

---

## 🎯 Core Capabilities (Eight User-Facing Views)

1. **Overview (`/`)**: Executive situational dashboard displaying city-wide flood risk index, active alerts, operational facility status, live rainfall telemetry, and key performance indicators.
2. **Future Flood Map (`/flood-map`)**: 0 to +180 minute dynamic inundation forecast powered by the Phase 6 deterministic physical flood engine with time-step playback controls (+30m, +60m, +90m, +120m, +150m, +180m).
3. **Travel Window (`/travel-window`)**: Safe departure and arrival time window analysis for emergency transport corridors based on cell-level flood arrival timing and water depth thresholds.
4. **Critical Access (`/critical-access`)**: Monitoring status for 366 verified Mumbai hospitals, fire stations, and substations, identifying primary access road submergence and routing to alternate functional facilities.
5. **Protect the City (`/protect-city`)**: Priority intervention site optimization tool recommending structural drainage interventions, mobile pump deployments, and barrier placements.
6. **Ground Truth (`/ground-truth`)**: Community and field responder evidence submission portal matching photo/field observations against Digital Twin spatial slices with automated corroboration logic.
7. **Simulator (`/simulator`)**: Scenario planning engine for stress-testing urban catchments under synthetic or historical extreme rainfall hydrographs and tide level combinations.
8. **Alert Center (`/alerts`)**: Multi-tiered operational alert management hub tracking physical simulation warnings, statistical risk signals, and SAR evidence corroboration.

---

## 🔬 Scientific Architecture & Authority Hierarchy

Aquora enforces a strict multi-tier authority hierarchy for scientific computations:

```text
┌─────────────────────────────────────────────────────────────────────────┐
│                    AUTHORITATIVE HYDRAULIC SOURCE                       │
│             Phase 6 Deterministic Physical Flood Engine                │
│       (Copernicus DEM 30m + Slope/Aspect + Drainage Loss Solver)        │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    SECONDARY STATISTICAL SIGNAL                         │
│                    XGBoost Risk Classifier                              │
│         (PROTOTYPE_ONLY | NOT_CALIBRATED — Evaluated on E07)            │
└────────────────────────────────────┬────────────────────────────────────┘
                                     │
                                     ▼
┌─────────────────────────────────────────────────────────────────────────┐
│                    CORROBORATING SATELLITE EVIDENCE                      │
│                  Sentinel-1 GRD VV+VH SAR Bitemporal Pair               │
│                (Historical Flood Event Evidence E02–E07)                 │
└─────────────────────────────────────────────────────────────────────────┘
```

---

## 🤖 Model Status & Governance

- **XGBoost Classifier Status**: `PROTOTYPE_ONLY` & `NOT_CALIBRATED`.
- **Feature Policy**: Trained using strictly pre-event static and meteorological predictors (`elevation_m`, `slope_deg`, `aspect_deg`, `flow_accumulation_cells`, `drainage_proxy_score`, `landcover_class`, `built_up_fraction`, `distance_to_road_m`, `distance_to_waterway_m`, `rainfall_30min_mm`, `rainfall_intensity_mm_hr`, `tide_level_m`).
- **Operational Boundary**: The XGBoost model provides statistical risk signals only. It does **not** override the Phase 6 physical solver for hydraulic depth or extent predictions.

---

## 🛰️ Real Data Sources & Provenance

Aquora is built exclusively on real acquired global and regional datasets:

- **Copernicus DEM GLO-30**: 30 m resolution digital elevation model (`Copernicus_DSM_COG_10_N19_00_E072_00.tif`).
- **NASA GPM IMERG Final V07B**: 30-minute half-hourly precipitation records for historical Mumbai flood events (E01–E07).
- **ESA WorldCover 2021 v200**: 10 m resolution global land cover classification map (`N18E072`).
- **OpenStreetMap & MCGM Facilities**: 359 verified OSM critical infrastructure facilities + 7 Municipal Corporation of Greater Mumbai (MCGM) healthcare nodes.
- **Sentinel-1 SAR Evidence**: Official Sentinel-1 GRD dual-polarization VV+VH bitemporal radar acquisitions for historical events E02–E07.
- **UHSLC Tide Gauge Observations**: High-resolution sea level observations from Mumbai Port (Station h846a).

---

## 📁 Repository Structure

```text
Aquora/
├── backend/                  # FastAPI async monolith API service & test suite
│   ├── app/                  # Router, controllers, services, providers, models, schemas
│   ├── data/models/          # Trained XGBoost model artifact (.joblib) & metadata (.json)
│   └── tests/                # 476 pytest unit, integration, and E2E test suites
├── frontend/                 # React 18 + TypeScript + Vite + Leaflet web application
│   ├── src/                  # App components, layout, features, map overlays, stores
│   └── public/               # Static web assets & icons
├── engines/                  # Pure hydrologic, physical solver, and drainage computation modules
├── geospatial/               # Spatial reference system & raster handling utilities
├── ml/                       # Machine learning feature pipelines and calibration modules
├── data/                     # Data documentation, manifests, and verified facility datasets
│   ├── manifests/            # Data provenance manifests and dataset specifications
│   └── raw/facilities/       # 366 verified Mumbai critical infrastructure facilities
├── scripts/                  # Data acquisition, dataset building, training & audit scripts
├── docs/                     # Comprehensive architecture and scientific phase documentation
├── .env.example              # Safe environment variable configuration template
├── .gitignore                # Production-hardened Git ignore rules
├── .dockerignore              # Container image build exclusion rules
├── docker-compose.yml        # Docker orchestration setup (PostGIS, Redis, Backend, Frontend)
└── README.md                 # Project root documentation
```

---

## 💻 Local Development Setup

### 1. Prerequisites
- Python 3.11+
- Node.js 18+ / npm 9+
- PostgreSQL 15+ with PostGIS 3.4+ extension
- Redis 7+

### 2. Backend Installation
```bash
# Navigate to backend directory
cd backend

# Create & activate virtual environment
python -m venv .venv
source .venv/bin/activate  # Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run backend development server
python -m uvicorn app.main:app --host 127.0.0.1 --port 8000 --reload
```

### 3. Frontend Installation
```bash
# Navigate to frontend directory
cd frontend

# Install Node dependencies
npm install

# Start Vite development server
npm run dev
```

App runs at: [http://127.0.0.1:5175](http://127.0.0.1:5175)

---

## 🧪 Testing & Verification

Run the full suite of automated tests to verify backend integrity:

```bash
# Execute complete backend pytest regression suite (476 tests)
python -m pytest backend/tests/ -v

# Execute Ground Truth regression suite (20 tests)
python -m pytest backend/tests/test_phase13_ground_truth.py -v

# Execute Step 9 E2E integration suite (7 tests)
python -m pytest backend/tests/test_phase9_step9_end_to_end.py -v

# Run frontend TypeScript type checking
cd frontend && npx tsc --noEmit

# Run frontend production build test
npm run build
```

---

## 🐳 Docker Quickstart

To build and run the complete Aquora platform in containers:

```bash
# Copy example environment configuration
cp .env.example .env

# Build and start all services (PostGIS, Redis, Backend, Frontend)
docker compose up --build -d
```

Service Endpoints:
- **Frontend SPA**: [http://localhost:5173](http://localhost:5173)
- **Backend API**: [http://localhost:8000](http://localhost:8000)
- **API Liveness**: [http://localhost:8000/api/v1/health/live](http://localhost:8000/api/v1/health/live)
- **API Readiness**: [http://localhost:8000/api/v1/health/ready](http://localhost:8000/api/v1/health/ready)
- **OpenAPI Interactive Documentation**: [http://localhost:8000/docs](http://localhost:8000/docs)

---

## ⚠️ Known Limitations & Scope

1. **Hydraulic Simplifications**: The Phase 6 physical solver uses 2D kinematic wave routing with uniform loss parameters; local storm sewer pipe pressure transients are approximated via proxy drainage loss terms.
2. **Model Calibration**: The prototype XGBoost model is uncalibrated (`NOT_CALIBRATED`). Probability outputs should be treated as relative risk rankings rather than absolute frequentist probabilities.
3. **Regional Scope**: Operational datasets are centered on the Mithi River Catchment and Greater Mumbai Metropolitan Region (UTM Zone 43N / EPSG:32643).
