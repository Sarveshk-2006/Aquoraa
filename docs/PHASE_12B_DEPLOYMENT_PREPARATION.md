# AQUORA — PHASE 12B PRODUCTION DEPLOYMENT PREPARATION GUIDE

> **Target Architecture**: Vercel Frontend SPA + Render Backend (FastAPI + Managed PostgreSQL/PostGIS + Managed Redis)

---

## 1. Final Vercel Frontend Architecture
- **Framework**: React 18 + Vite Single Page Application (SPA).
- **Deployment Platform**: Vercel.
- **Root Directory**: `frontend/`
- **Build Command**: `npm run build`
- **Output Directory**: `dist`
- **Client-Side Routing**: SPA fallback configured via `frontend/vercel.json` (`rewrites: [{"source": "/(.*)", "destination": "/index.html"}]`).
- **Environment Configuration**: API base URL injected at build time via `VITE_API_BASE_URL`.

---

## 2. Final Render Backend Architecture
- **Framework**: FastAPI Async Monolith running Python 3.11.
- **Deployment Platform**: Render Web Service.
- **Root Directory**: `backend/`
- **Build Command**: `pip install -r requirements.txt`
- **Start Command**: `uvicorn app.main:app --host 0.0.0.0 --port $PORT`
- **Health Check Path**: `/api/v1/health/live`
- **Blueprint File**: `render.yaml` at project root.

---

## 3. PostgreSQL / PostGIS Setup Sequence
1. Provision Managed PostgreSQL 15 instance on Render (`aquora-db`).
2. Enable PostGIS 3.4 spatial extension:
   ```sql
   CREATE EXTENSION IF NOT EXISTS postgis;
   ```
3. Run Alembic database migrations:
   ```bash
   alembic upgrade head
   ```
4. Verify PostGIS spatial table structures for `critical_facilities`, `ground_truth_observations`, `digital_twin_runs`, and `audit_events`.

---

## 4. Redis Setup Sequence
1. Provision Managed Redis Key-Value instance on Render (`aquora-redis`).
2. Bind `REDIS_URL` connection string to backend environment (`redis://red-xxx:6379`).
3. Verify connection via `/api/v1/health/ready`.

---

## 5. Environment Variable Matrix

| Variable Name | Scope | Deployment Location | Safe Default / Format |
| :--- | :--- | :--- | :--- |
| `ENVIRONMENT` | Backend | Render Dashboard | `production` |
| `VITE_API_BASE_URL` | Frontend | Vercel Environment | `https://aquora-backend.onrender.com` |
| `API_BASE_URL` | Backend | Render Environment | `https://aquora-backend.onrender.com` |
| `CORS_ORIGINS` | Backend | Render Environment | `["https://aquoraa.vercel.app","https://aquora.example.com"]` |
| `DATABASE_URL` | Backend | Render Secret (Auto-wired) | `postgresql+asyncpg://user:pass@host/db` |
| `REDIS_URL` | Backend | Render Secret (Auto-wired) | `redis://red-xxx:6379/0` |
| `ROUTING_PROVIDER` | Backend | Render Environment | `OSRM` |
| `RAINFALL_PROVIDER` | Backend | Render Environment | `IMERG` |
| `FACILITY_PROVIDER` | Backend | Render Environment | `LOCAL` |
| `GROUND_TRUTH_PROVIDER` | Backend | Render Environment | `LOCAL_VERIFIED` |

---

## 6. CORS Configuration
Backend CORS middleware (`app/main.py`) parses environment-driven origins via `Settings.CORS_ORIGINS`:
- Supports JSON strings (e.g. `["https://aquoraa.vercel.app"]`) and comma-separated strings (`https://aquoraa.vercel.app, http://localhost:5175`).
- Preserves `allow_credentials=True` without using wildcard (`*`) origins.

---

## 7. Health & Readiness Endpoints
- **Liveness Endpoint**: `GET /api/v1/health/live` -> Returns HTTP 200 OK process check. Used by Render health checker.
- **Readiness Endpoint**: `GET /api/v1/health/ready` -> Verifies active PostgreSQL/PostGIS and Redis TCP connections.

---

## 8. Runtime Data Requirements
Lightweight runtime assets bundled inside repository (Total ~1.6 MB):
- `data/raw/facilities/osm_critical_facilities.json` (359 OSM facilities)
- `data/raw/facilities/mithi_critical_facilities.json` (7 MCGM facilities)
- `data/raw/phase7/dem/Copernicus_DSM_COG_10_N19_00_E072_00.tif` (0.71 MB DEM elevation tile)
- `backend/data/models/aquora_xgboost_prototype.joblib` (0.64 MB model)
- `backend/data/models/aquora_xgboost_metadata.json` (0.01 MB metadata)

---

## 9. Large-Data External Storage Requirements
Multi-GB raw satellite archives remain stored in cloud object storage (AWS S3 / GCS):
- Sentinel-1 GRD archives (11.6 GB)
- ESA WorldCover Landcover map (119.9 MB)
- NASA IMERG HDF5 precipitation files (53.8 MB)
- Referenced via SHA256 checksums in `PHASE_7_MASTER_DATASET_MANIFEST.yaml` and re-downloadable via `scripts/acquire_real_*.py`.

---

## 10. Migration Procedure
Execute Alembic migrations automatically or via Render build command:
```bash
cd backend && alembic upgrade head
```

---

## 11. Facility Initialization Procedure
`LocalCriticalFacilityProvider` automatically parses `data/raw/facilities/*.json` on startup and populates the 366 verified facilities without requiring manual database seeding scripts.

---

## 12. Deployment Order
1. **Step 1**: Provision Render PostgreSQL (`aquora-db`) and enable PostGIS extension.
2. **Step 2**: Provision Render Redis (`aquora-redis`).
3. **Step 3**: Deploy Render Backend Web Service (`aquora-backend`) and retrieve assigned backend URL.
4. **Step 4**: Deploy Vercel Frontend SPA (`frontend/`) and set `VITE_API_BASE_URL` to the Render backend URL.
5. **Step 5**: Update `CORS_ORIGINS` in Render environment to include the live Vercel frontend URL.

---

## 13. Rollback Procedure
If a deployment issue occurs:
1. **Frontend**: Roll back Vercel deployment instantly via Vercel Dashboard -> Deployments -> Promote Previous Deployment.
2. **Backend**: Roll back Render web service to previous image build in Render Dashboard.

---

## 14. Known Limitations
1. Render free-tier web services spin down after 15 minutes of inactivity; initial cold-start latency may take ~30 seconds.
2. XGBoost prototype remains `PROTOTYPE_ONLY` & `NOT_CALIBRATED`. The Phase 6 physical hydraulic solver remains authoritative.

---

## 15. Exact Manual Actions Required Before Live Deployment (Phase 12C)

| Action | Status | Location |
| :--- | :--- | :--- |
| **Commit Blueprint Configs** | `READY AUTOMATICALLY` | `render.yaml` & `frontend/vercel.json` created |
| **Connect GitHub Repo to Render** | `REQUIRES MANUAL DASHBOARD ACTION` | Render Dashboard -> New Blueprint Instance -> Select `Sarveshk-2006/Aquoraa` |
| **Connect GitHub Repo to Vercel** | `REQUIRES MANUAL DASHBOARD ACTION` | Vercel Dashboard -> Add New Project -> Import `Sarveshk-2006/Aquoraa` (`frontend/`) |
| **Configure VITE_API_BASE_URL** | `REQUIRES MANUAL DASHBOARD ACTION` | Vercel Project Settings -> Environment Variables |
| **Configure CORS_ORIGINS** | `REQUIRES MANUAL DASHBOARD ACTION` | Render Service Settings -> Environment Variables |
