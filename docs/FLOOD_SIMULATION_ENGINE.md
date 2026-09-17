# AQUORA — Phase 6 Flood Simulation Engine

## Overview & Purpose

The **Flood Simulation Engine** (Phase 6) provides a deterministic, mass-conserving, physically defensible, simplified urban flood simulation for the **AQUORA — Urban Flood Intelligence & Response Platform**.

While Phase 3 answers *"What rainfall/forecast input is available?"*, Phase 4 answers *"Where does water naturally want to move over terrain?"*, and Phase 5 answers *"What drainage infrastructure exists and how is it connected?"*, Phase 6 answers:
> **"What happens over a 0–3 hour horizon when rainfall, runoff, terrain, surface flow, and municipal drainage interact?"**

### Important Scientific Disclaimer

> **IMPORTANT BOUNDARY STATEMENT**:
> - **Phase 6 is a simplified urban rainfall-runoff + surface storage + terrain-constrained routing + drainage-interaction model.**
> - **It is NOT a full 2D Saint-Venant / shallow-water hydrodynamic solver.**
> - **Missing physical attributes (pipe capacities, direction, parameters) remain UNKNOWN rather than being fabricated.**
> - **Input completeness indicators represent data quality and coverage; they are NOT ML model confidence.**

---

## Pipeline Architecture & Engine Location

The deterministic physical simulation engine is located in `engines/flood/` outside the web API layer to preserve architectural independence:

```text
External Inputs (Phase 3 Rainfall/Forecast, Phase 4 DEM, Phase 5 Drainage)
                       ↓
            backend/app/services/flood_service.py
                       ↓
            engines/flood/
            ├── models.py               (Domain enums & dataclasses)
            ├── validation.py           (Input array & spatial coverage checks)
            ├── runoff.py               (Rainfall excess & runoff volume calculation)
            ├── surface_storage.py      (Cell accumulation & depression storage)
            ├── surface_routing.py      (D8 terrain surface flow & Courant limiters)
            ├── drainage_coupling.py    (Inlet removal, capacity bounds & outfall check)
            ├── severity.py             (Depth severity & peak/onset state trackers)
            ├── diagnostics.py          (Mass balance accounting & completeness metrics)
            └── solver.py               (Main temporal timestep simulation loop)
                       ↓
            File-Backed Artifacts (data/processed/flood/<simulation_id>/)
                       ↓
            Developer HTTP APIs (/api/v1/flood/) & PostGIS Metadata
```

---

## Scientific Formulations & Hydrologic Rules

### 1. Rainfall-to-Runoff Generation (`runoff.py`)
Gross rainfall depth $P_{\text{gross}} = \text{intensity} \cdot (\Delta t / 60)$ ($mm$).
Rainfall excess depth:
$$P_{\text{excess}} = \max(0.0, P_{\text{gross}} - L_{\text{init}} - I_{\text{infil}} \cdot (\Delta t / 60))$$
Runoff depth $R_{\text{depth}} = P_{\text{excess}} \cdot C_{\text{runoff}}$ ($mm$).
Runoff volume for cell area $A$:
$$V_{\text{runoff}} = \left(\frac{R_{\text{depth}}}{1000.0}\right) \cdot A \quad (m^3)$$

### 2. Surface Storage & Depression Storage (`surface_storage.py`)
Accumulates $V_{\text{runoff}}$ into current cell storage $S(t)$.
$$S_{\text{total}} = S(t-1) + V_{\text{runoff}}$$
Mobile water available for routing:
$$V_{\text{mobile}} = \max(0.0, S_{\text{total}} - S_{\text{depression\_capacity}})$$

### 3. D8 Terrain Surface Routing (`surface_routing.py`)
Uses Phase 4 D8 flow directions ($1=\text{E}, 2=\text{SE}, 4=\text{S}, 8=\text{SW}, 16=\text{W}, 32=\text{NW}, 64=\text{N}, 128=\text{NE}$).
Transfers water downslope to valid neighbor cells.
Numerical stability constraint:
$$V_{\text{transfer}} \le V_{\text{mobile}} \cdot \text{max\_transfer\_ratio} \quad (\text{max\_transfer\_ratio} \le 0.5)$$
Prevents negative cell storage and numerical oscillation while ensuring water never moves uphill under D8 terrain flow rules.

### 4. Municipal Drainage Coupling (`drainage_coupling.py`)
- **Inlet Association**: Connects surface storage cells to valid Phase 5 inlets (`INLET`, `CATCH_BASIN`).
- **Known Capacity Bounds**: $V_{\text{drain\_out}} \le \min(V_{\text{available}}, \text{capacity\_m3s} \cdot \Delta t_{\text{sec}})$.
- **Unknown Capacity Policy**: Missing capacity remains `UNKNOWN`. Configured policy (`EXCLUDE`, `CONSERVATIVE_ASSUMPTION`, `SCENARIO`) is recorded. Missing capacity is **never** converted to $0$ or fabricated.
- **Unknown Direction Policy**: Missing link direction remains `UNKNOWN`. Links are excluded from directed hydraulic routing.
- **Outfall Reachability**: Drainage removal occurs **only** if the inlet node can reach an explicit `OUTFALL` node.
- **Hard Invariant**: Drainage coupling **never creates water** ($V_{\text{drain\_out}} \le V_{\text{available}}$).

---

## Mass Conservation & Diagnostics

### Mass Balance Equation
At every simulation timestep $t$:
$$S(t) = S(t-1) + V_{\text{gross\_rain}} - V_{\text{infil\_loss}} - V_{\text{drain\_out}}$$
Mass Balance Error:
$$\text{Error}(t) = \left| S(t) - \left(S(t-1) + V_{\text{gross\_rain}} - V_{\text{infil\_loss}} - V_{\text{drain\_out}}\right) \right|$$
Is Valid: $\text{Error}(t) \le \text{MASS\_BALANCE\_TOLERANCE}$ ($10^{-4}\,m^3$).

### Input Completeness & Uncertainty Warnings
Computes a transparent data coverage score ($0.0 - 1.0$) and level (`HIGH`, `MEDIUM`, `LOW`). Surfaces structured warnings for:
- `COARSE_RAINFALL_RESOLUTION`: ~10km NASA IMERG spatially distributed onto DEM grid.
- `SYNTHETIC_FORECAST_USED`: Simulation driven by `SyntheticForecastProvider`.
- `INCOMPLETE_DRAINAGE_CAPACITY`: Percentage of links with missing capacity.
- `INCOMPLETE_DRAINAGE_DIRECTION`: Percentage of links with unknown direction.

---

## Inundation Severity & Temporal Tracking

### Severity Classification (`severity.py`)
- **DRY**: Depth $< 0.05\,\text{m}$ ($< 5\,\text{cm}$)
- **LOW**: $0.05\,\text{m} \le \text{Depth} < 0.15\,\text{m}$ ($5-15\,\text{cm}$)
- **MODERATE**: $0.15\,\text{m} \le \text{Depth} < 0.30\,\text{m}$ ($15-30\,\text{cm}$)
- **HIGH**: $0.30\,\text{m} \le \text{Depth} < 0.60\,\text{m}$ ($30-60\,\text{cm}$)
- **SEVERE**: $\text{Depth} \ge 0.60\,\text{m}$ ($60+\,\text{cm}$)

### Temporal Tracking
- `first_flood_timestamp`: Timestamp when cell first exceeds $0.05\,\text{m}$ depth threshold (Flood Onset).
- `peak_water_depth_m`: Maximum water depth attained during simulation horizon.
- `peak_timestamp`: Timestamp when peak water depth occurred.
- `duration_grid_min`: Cumulative duration in minutes that cell remained flooded.

---

## Developer HTTP APIs (`/api/v1/flood/`)

- `POST /api/v1/flood/simulations` — Execute physical flood simulation run.
- `GET /api/v1/flood/simulations/{id}` — Get simulation run metadata summary.
- `GET /api/v1/flood/simulations/{id}/status` — Get execution status.
- `GET /api/v1/flood/simulations/{id}/diagnostics` — Get per-timestep mass balance diagnostics.
- `GET /api/v1/flood/simulations/{id}/artifacts` — Get list of file-backed raster/JSON output artifacts.
- `GET /api/v1/flood/simulations/latest` — Get latest simulation run.
- `POST /api/v1/flood/simulations/validate-inputs` — Validate simulation input parameters.

---

## Relationship to Future Phases

- **Phase 7 (Real Dataset Creation)**: Will generate historical storm events and real municipal vector/raster datasets.
- **Phase 8 (ML Calibration)**: Will train physics-guided ML models to calibrate systematic physical residual errors.
- **Phase 9 (Future Flood Map / City Twin)**: Will consume the temporal simulation outputs generated by Phase 6 to render 2D/3D flood inundation map scrubbing.
