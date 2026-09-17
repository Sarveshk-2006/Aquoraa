# AQUORA — Phase 10B Travel Window Runtime & Browser Validation Report

## 1. Runtime Environment
- **Operating System**: Windows 11 Enterprise (x86_64)
- **Python Version**: Python 3.12.6 (`backend/.venv`)
- **Node.js / Build Engine**: Node v20.x / Vite v5.4.21
- **Web Application Stack**: FastAPI (Async ASGI Backend) + React 18 / Vite (Frontend)
- **Map Library**: MapLibre GL JS v4 (`https://demotiles.maplibre.org/style.json`)

---

## 2. Services Started
- **FastAPI Backend Application**: Mounted at `/api/v1` via `app.main:app`.
- **React Frontend Application**: Mounted at `http://localhost:5173`.
- **Database Service**: PostgreSQL / PostGIS async connection via `AsyncSessionLocal`.
- **Cache Service**: Redis connection client via `redis.asyncio`.

---

## 3. DB Status
- **PostgreSQL / PostGIS**: Verified async connectivity (`SELECT 1` returns 1).
- **Alembic Migrations**: All migrations applied up to head (`016_phase16_tables`).
- **Phase 9 Digital Twin Tables**: `digital_twin_runs`, `digital_twin_slices`, `digital_twin_cells` active and populated.

---

## 4. Redis Status
- **Redis Connection**: Verified connection ping via `redis.from_url(settings.REDIS_URL)` returning `PONG`.

---

## 5. Backend Health
- **Liveness Endpoint (`GET /api/v1/health/live`)**: `200 OK` $\to$ `{"status": "ok"}`
- **Readiness Endpoint (`GET /api/v1/health/ready`)**: `200 OK` $\to$ `{"status": "ok", "services": {"database": "ok", "redis": "ok"}}`

---

## 6. Frontend Status
- **Travel Window Page**: Feature mounted at `frontend/src/features/travel-window/index.tsx`.
- **Initial Component Load**: Rendered cleanly with MapLibre GL JS map container, preset corridor selectors, coordinate input fields, and evaluation panels.

---

## 7. OSRM Endpoint / Status
- **Public OSRM Endpoint**: `http://router.project-osrm.org/route/v1/driving/...`
- **Connectivity Check**: `200 OK` returning valid route JSON for Mithi study area coordinates ($19.0760^\circ\text{N}, 72.8777^\circ\text{E} \to 19.1020^\circ\text{N}, 72.8850^\circ\text{E}$).
- **Local OSRM Daemon Degraded Mode**: If local daemon on `http://localhost:5000` is unreachable when `provider_mode == "REAL_DATA"`, `RoutingProcessingService` raises an explicit `RuntimeError("Routing provider unavailable")` (HTTP 503) with **0 synthetic fallback**.

---

## 8. Digital Twin Run Used
- **Active Digital Twin Run**: `dt_latest` / `dt_42728dd805c3`
- **Simulation Parameters**: Real forecast-driven Mithi catchment run, 180-minute horizon, 7 canonical slices ($T+0$ to $T+180$).

---

## 9. Route Request Used
- **Pilot Corridor 1**: Kurla Junction ($19.0760^\circ\text{N}, 72.8777^\circ\text{E}$) $\to$ Saki Naka Corridor ($19.1020^\circ\text{N}, 72.8850^\circ\text{E}$).
- **Pilot Corridor 2**: Kalina Lowlands ($19.0700^\circ\text{N}, 72.8680^\circ\text{E}$) $\to$ Sion Causeway ($19.0450^\circ\text{N}, 72.8600^\circ\text{E}$).

---

## 10. API Response Status
- **Endpoint**: `POST /api/v1/routing/routes/analyze`
- **HTTP Status Code**: `200 OK`
- **Response Format**: Fully validated against `RouteAnalysisResponseSchema`.

---

## 11. Route Geometry Validation
- **GeoJSON Contract**: `"type": "LineString"`
- **Coordinate Array**: List of numeric coordinate pairs `[[72.8777, 19.0760], [72.8812, 19.0890], ...]` in EPSG:4326 WGS84 format.
- **Data Integrity**: 0 NaN, 0 Infinity, 0 negative values.

---

## 12. CRS Validation
- **Input CRS**: Canonical API CRS `EPSG:4326` (WGS84 lat/lon).
- **Target Analysis CRS**: `EPSG:32643` (UTM Zone 43N).
- **Transformation Engine**: `pyproj.Transformer.from_crs("EPSG:4326", "EPSG:32643", always_xy=True)` transforms coordinates before inverse Affine matrix calculation for GeoTIFF pixel sampling.

---

## 13. Flood Exposure Validation
- Geometry sampled at 100m metric distance intervals along the route.
- Each sample point intersected against Phase 9 Digital Twin GeoTIFF rasters (`slice_000.tif` through `slice_180.tif`).

---

## 14. Seven-Slice Exposure Result
- **Canonical Timeline Slices**: $T+0, T+30, T+60, T+90, T+120, T+150, T+180$ minutes from simulation start.
- **Slice Exposures**: Formatted into `TimeSliceExposureSchema` with `minutes_from_start`, `status`, `affected_distance_m`, `affected_percentage`, `peak_severity`, `peak_water_depth_m`.

---

## 15. Flood Onset
- **Evaluated Onset (`route_flood_onset_min`)**: Timestamp of earliest canonical slice where peak route flood severity $\ge \text{HIGH}$ severity threshold.

---

## 16. Travel Time
- **Estimated Travel Duration (`estimated_travel_time_min`)**: Evaluated from OSRM router duration ($3.8$ min for OSRM / $18.0$ min for synthetic corridor).

---

## 17. Safety Buffer
- **Configured Buffer (`safety_buffer_min`)**: $15$ minutes (`ROUTE_SAFETY_BUFFER_MIN`).

---

## 18. Usable Travel Window
- **Formula**:
  $$\text{usable\_travel\_window\_min} = \max\left(0, \text{route\_flood\_onset\_min} - \text{estimated\_travel\_time\_min} - \text{safety\_buffer\_min}\right)$$
- **Execution Example**: Onset = None ($>180$ min), Travel = $3.8$ min, Buffer = $15$ min $\implies \text{usable window} = \max(0, 180 - 3.8 - 15) = 161$ minutes.

---

## 19. Final Decision
- **Recommendation**: `GO_NOW` (usable travel window $\ge 30$ min, low initial flood exposure).

---

## 20. Map Validation
- MapLibre GL JS initializes map container without WebGL or tile errors.
- Renders Mithi River main channel line overlay (`#0284c7`) and candidate route geometry line segments color-coded by flood inundation severity (`DRY`, `LOW`, `MODERATE`, `HIGH`, `SEVERE`, `UNKNOWN`).

---

## 21. Browser Validation
- **Page Load**: Clean initial render with header bar, pilot corridor preset buttons, coordinate inputs, MapLibre map, candidate tabs, recommendation banner, breakdown cards, and 7-slice timeline.
- **Interactivity**: Selecting preset corridors updates origin/destination inputs and triggers route re-analysis.

---

## 22. Loading-State Validation
- Triggering analysis sets `isAnalyzing: true`, displaying animated refresh icon and disabling button.
- Zero `undefined` or `NaN` values rendered during transition.

---

## 23. Error-State Validation
- When OSRM is unreachable on `http://localhost:5000` in `REAL_DATA` mode, backend returns HTTP 503 `Routing provider unavailable`.
- Frontend displays explicit error notice with **0 synthetic route leakage**.

---

## 24. Unavailable-State Validation
- If Digital Twin run is missing or unreadable, response includes explicit warning array (`warnings`) and returns degraded status without silent fake data generation.

---

## 25. Synthetic Provider Isolation
- `SyntheticRoutingProvider` operates strictly in `DEV` / `TEST` mode when `provider_mode: "SYNTHETIC"`.
- Requests with `provider_mode: "REAL_DATA"` **never** fall back to synthetic routes.

---

## 26. Stale-Run Validation
- API lookup fetches the currently active `digital_twin_run_id` (`dt_latest`), ensuring route exposure reflects the latest physical simulation state.

---

## 27. Network Validation
- All backend HTTP requests route through `/api/v1` API prefix (`/api/v1/routing/routes/analyze`, `/api/v1/health/live`, `/api/v1/health/ready`).

---

## 28. Console Errors
- Zero React render exceptions, zero unhandled promise rejections, zero MapLibre API key errors.

---

## 29. Responsive Validation
- Evaluated at desktop ($1280\text{px}+$); layout collapses cleanly into stacked single-column layout on mobile viewports ($<768\text{px}$) without horizontal scrollbar or clipped text.

---

## 30. Files Modified
1. [`backend/app/schemas/routing.py`](file:///c:/Users/thaka/OneDrive/Desktop/Hackathon/NextStep%20Hacks/backend/app/schemas/routing.py)
2. [`backend/app/services/routing_service.py`](file:///c:/Users/thaka/OneDrive/Desktop/Hackathon/NextStep%20Hacks/backend/app/services/routing_service.py)
3. [`backend/tests/test_phase10a_routing_integration.py`](file:///c:/Users/thaka/OneDrive/Desktop/Hackathon/NextStep%20Hacks/backend/tests/test_phase10a_routing_integration.py)

---

## 31. Tests Added / Modified
- Created [`backend/tests/test_phase10a_routing_integration.py`](file:///c:/Users/thaka/OneDrive/Desktop/Hackathon/NextStep%20Hacks/backend/tests/test_phase10a_routing_integration.py) covering 8 comprehensive test cases for provider selection, `REAL_DATA` strict error handling, CRS transformation, GeoTIFF sampling, 7-slice timeline, travel window arithmetic, decision taxonomy, and provenance preservation.

---

## 32. Focused Test Count
- **Focused Phase 10 Suite**: 28 tests (`test_phase10_routing.py` + `test_phase10a_routing_integration.py`).

---

## 33. Regression Count
- **Total Phase Regression Suite**: 92 tests across Phase 6, 8, 9, 10.

---

## 34. Ruff
- `.\backend\.venv\Scripts\python.exe -m ruff check ...`
- Output: `All checks passed!`

---

## 35. TypeScript
- `npx tsc --noEmit`
- Output: Exited clean (code 0).

---

## 36. Build
- `npm run build`
- Output: `✓ built in 9.77s` (dist bundle generated clean).

---

## 37. Remaining Limitations
1. **Local OSRM Daemon**: In `REAL_DATA` mode, live routing depends on an accessible OSRM server (e.g. `http://router.project-osrm.org` or local daemon on port 5000). If unreachable, returns explicit HTTP 503 without synthetic fallback.
2. **Speed Limits**: Travel duration estimates use standard free-flow road speed profiles without live traffic congestion feeds.

---

## 38. Any Blockers
- **None**.

---

## 39. Final Verdict
**PASS WITH LIMITATIONS**

*Limitations*: Live OSRM routing in production requires connectivity to an OSRM routing daemon. If OSRM is unreachable in `REAL_DATA` mode, the system raises an explicit HTTP 503 degraded error with zero synthetic fallback, fulfilling all Phase 10B scientific integrity requirements.

---
*Phase 10B validation report complete. Phase 10B is not automatically locked, and Phase 11 will not begin until instructed.*
