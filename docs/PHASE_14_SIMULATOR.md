# AQUORA PHASE 14 — AQUORA SIMULATOR
## What-If Hydro-Simulation & Scenario Analysis Engine

> **Tagline**: "See the flood before it becomes a crisis."

---

### Governance & Operational Disclaimers

> [!IMPORTANT]
> **Mandatory Governance Statement**:
> "Simulator results are model-based what-if estimates and are not guarantees of real-world outcomes."

> [!NOTE]
> **Conditional Benefit Statement**:
> "Modeled benefit is conditional on the selected model assumptions, baseline inputs, and intervention representation."

---

## 1. Executive Summary & Purpose

Phase 14 introduces **AQUORA Simulator**, an orchestration, parameterization, and what-if comparison layer built directly on top of the deterministic **Phase 6 Flood Simulation Engine**.

It allows urban planners, flood risk managers, and emergency responders to evaluate hypothetical changes in environmental conditions, storm events, drainage network performance, and municipal interventions.

### Key Capabilities:
- **Baseline Immutability**: All scenario executions reference a completed, unmutated Phase 9 Digital Twin / Phase 6 simulation baseline. Scenarios never mutate underlying rainfall, terrain, or drainage database records.
- **Phase 6 Solver Authority**: Reuses `run_flood_simulation_loop` from `app.geospatial.flood` without creating a duplicate flood solver.
- **Scenario Taxonomy**: Supports `RAINFALL_MULTIPLIER`, `RAINFALL_ADDITION`, `DRAINAGE_CAPACITY_REDUCTION`, `DRAINAGE_CAPACITY_INCREASE`, `DRAINAGE_NODE_INTERVENTION`, `TEMPORARY_BARRIER`, `STORAGE_INTERVENTION`, `PUMP_OR_DEWATERING_SCENARIO`, and `COMBINED_SCENARIO`.
- **Baseline Equivalence**: Guarantees that `RAINFALL_MULTIPLIER = 1.0` reproduces baseline inundation metrics within documented numerical tolerance.
- **Outcome Classification**: Categorizes delta impacts into `IMPROVED`, `NO_SIGNIFICANT_CHANGE`, `WORSE`, and `INCONCLUSIVE` based on a configurable `SIMULATOR_NO_CHANGE_TOLERANCE` threshold.
- **Audit Provenance**: Stores complete parameter payloads, recorded assumptions, solver diagnostics (mass balance errors), and file-backed raster map artifacts.

---

## 2. Architectural Boundary & Non-Negotiable Rules

Phase 14 acts strictly as an **orchestration and delta-comparison layer**.

```
BASELINE DIGITAL TWIN RUN (Phase 9 / Phase 6)
                      ↓
          SCENARIO DEFINITION & VALIDATION
                      ↓
       PARAMETER OVERLAY (In-Memory Transformation)
                      ↓
       EXISTING PHASE 6 DETERMINISTIC ENGINE
                      ↓
      SCENARIO RASTER ARTIFACTS & DIAGNOSTICS
                      ↓
        BASELINE VS SCENARIO COMPARISON
                      ↓
          DECISION & OUTCOME INSIGHT
```

### Prohibited Actions:
1. **No Second Flood Solver**: Phase 6 remains the sole physical solver authority.
2. **No Second Digital Twin Generator**: Phase 9 remains the sole Digital Twin authority.
3. **No In-Place Data Mutation**: Scenarios create ephemeral overlay copies during Phase 6 solver execution. Baseline data in Postgres/PostGIS and raster files remain untouched.
4. **No Synthetic Fallback**: Real production baseline data is required; synthetic providers are labeled `TEST_ONLY`.
5. **No Arbitrary Code Execution**: Scenario inputs accept strictly structured, typed JSON payloads. Executable code, Python, SQL, or shell commands are rejected.

---

## 3. Scenario Taxonomy & Parameter Semantics

| Scenario Type | Canonical Parameter | Semantics & Transformation | Physical Solver Support |
| :--- | :--- | :--- | :--- |
| `RAINFALL_MULTIPLIER` | `rainfall_multiplier` (e.g. 1.25) | Multiplies each baseline rainfall timestep intensity by factor (bounded [0.0, 3.0]). | Supported via Phase 6 |
| `RAINFALL_ADDITION` | `rainfall_addition_mm` (e.g. +20mm) | Distributes added total event rainfall proportional to baseline temporal storm profile. | Supported via Phase 6 |
| `DRAINAGE_CAPACITY_REDUCTION` | `capacity_multiplier` (e.g. 0.80) | Scales link full capacities by factor. Unknown capacity remains UNKNOWN unless explicit policy provided. | Supported via Phase 6 |
| `DRAINAGE_CAPACITY_INCREASE` | `capacity_multiplier` (e.g. 1.50) | Scales link full capacities by factor. Does not mutate DB records. | Supported via Phase 6 |
| `DRAINAGE_NODE_INTERVENTION` | `intervention_candidate_ids` | Maps Phase 12 intervention candidates to target node capacity enhancements. | Supported via Phase 6 |
| `PUMP_OR_DEWATERING_SCENARIO` | `pump_capacity_m3_s` | Applies continuous bounded dewatering removal rate at outfall nodes. | Supported via Phase 6 |
| `COMBINED_SCENARIO` | Multi-parameter dictionary | Applies rainfall transformation followed by drainage capacity adjustments in deterministic order. | Supported via Phase 6 |
| `TEMPORARY_BARRIER` | Barrier parameters | Returns `UNSUPPORTED_SCENARIO` if Phase 6 engine cannot represent hydraulic effect faithfully. | Unsupported |
| `STORAGE_INTERVENTION` | Storage parameters | Returns `UNSUPPORTED_SCENARIO` if Phase 6 engine lacks reservoir solver. | Unsupported |

---

## 4. API Endpoints (`/api/v1/simulator`)

- `POST /api/v1/simulator/scenarios`: Create scenario definition.
- `GET /api/v1/simulator/scenarios`: List defined scenarios.
- `GET /api/v1/simulator/scenarios/{scenario_id}`: Retrieve scenario detail.
- `POST /api/v1/simulator/scenarios/{scenario_id}/validate`: Run scenario validation checks.
- `POST /api/v1/simulator/scenarios/{scenario_id}/run`: Execute simulation through Phase 6 engine.
- `GET /api/v1/simulator/runs`: List scenario execution runs.
- `GET /api/v1/simulator/runs/{run_id}`: Get run execution details.
- `GET /api/v1/simulator/runs/{run_id}/summary`: Get comprehensive summary.
- `GET /api/v1/simulator/runs/{run_id}/comparison`: Retrieve metric comparisons across 0-180m timesteps.
- `GET /api/v1/simulator/runs/{run_id}/map/{minutes}`: Retrieve map artifact metadata for time slice.
- `GET /api/v1/simulator/runs/{run_id}/diagnostics`: Get solver diagnostics (mass balance errors).
- `GET /api/v1/simulator/scenarios/{scenario_id}/provenance`: Retrieve complete audit provenance chain.

---

## 5. Verification & Audit Results

- **Baseline Equivalence Test (`RAINFALL_MULTIPLIER = 1.0`)**: PASS
- **Determinism Test**: PASS
- **Immutability Test**: PASS
- **Duplicate-Engine Audit**: PASS (0 duplicate solvers found)
- **Data Isolation Audit**: PASS
- **Full Backend Pytest Regression**: PASS (369 passed)
- **TypeScript `--noEmit`**: PASS
- **Vite Production Build**: PASS
- **Alembic Migration Verification**: PASS
