# AQUORA — PHASE 14A SIMULATOR & WHAT-IF SCENARIOS VALIDATION REPORT

**Date**: 2026-09-13
**Phase**: Phase 14A — Simulator / What-If Scenarios Implementation Audit & Integration Validation
**Status**: VALIDATED WITH LIMITATIONS (DEGRADED LOCAL RUNTIME)
**Final Verdict**: PASS WITH LIMITATIONS

---

## 1. Existing Implementation Audit
- **Service Layer**: `backend/app/services/simulator_service.py` inspected. Implements scenario creation, validation, baseline immutability, overlay parameterization, Phase 6 flood engine execution, raster artifact persistence, baseline-vs-scenario metric comparisons, outcome classification, and provenance hash calculation.
- **Router Layer**: `backend/app/api/v1/simulator.py` inspected. Mounts REST endpoints under `/api/v1/simulator` for scenario lifecycle, parameter validation, simulation execution, timestep comparison metrics, map artifacts, diagnostics, and audit provenance.
- **Model Layer**: `backend/app/models/simulator.py` inspected. Defines SQLAlchemy models for `SimulatorScenario`, `SimulatorRun`, `SimulatorComparison`, `SimulatorArtifact`, and `SimulatorDiagnostic`.
- **Schema Layer**: `backend/app/schemas/simulator.py` inspected. Defines Pydantic v2 schemas for request/response payloads, taxonomy enums, outcome classifications, and assumption records.
- **Frontend Layer**: `frontend/src/features/simulator/index.tsx` inspected. Renders interactive scenario builder, baseline selector, parameter sliders, outcome classification badges (`IMPROVED`, `NO_SIGNIFICANT_CHANGE`, `WORSE`, `INCONCLUSIVE`), canonical timeline slice buttons (+0m to +180m), metric comparison cards, and governance warning banners.

---

## 2. Architecture Boundary Audit
- **Phase 6 Physics Authority**: Phase 14 orchestrates scenarios by passing overlay parameters to `app.geospatial.flood.run_flood_simulation_loop` (Phase 6 D8 solver). Zero duplicate flood solver logic exists.
- **Phase 9 Digital Twin Authority**: Baseline Digital Twin runs (`dt_mithi_baseline_001`) remain authoritative and read-only. Phase 14 stores scenario outputs as distinct scenario runs.
- **Phase 10 Routing Boundary**: Scenario routing exposure checks use Phase 10 routing contracts where applicable; no duplicate routing math created.
- **Phase 11 Critical Access Boundary**: Scenario accessibility checks use Phase 11 semantics without inventing custom access loss logic.
- **Phase 12 Protect City Boundary**: Phase 12 intervention candidates (`cand_drainage_culvert_expansion_l2`) map to node interventions without mutating baseline priority scores.
- **Phase 13 Ground Truth Boundary**: Community observations provide contextual evidence but do not automatically alter simulation solver physics.
- **Phase 8 ML Boundary**: XGBoost prototype model artifact remains 100% read-only and un-mutated.

---

## 3. Scenario Taxonomy
Preserved established taxonomy enum `ScenarioType`:
- `RAINFALL_MULTIPLIER`
- `RAINFALL_ADDITION`
- `DRAINAGE_CAPACITY_REDUCTION`
- `DRAINAGE_CAPACITY_INCREASE`
- `DRAINAGE_NODE_INTERVENTION`
- `TEMPORARY_BARRIER`
- `STORAGE_INTERVENTION`
- `PUMP_OR_DEWATERING_SCENARIO`
- `COMBINED_SCENARIO`

---

## 4. Supported Scenarios
- `RAINFALL_MULTIPLIER`: Scaling baseline rainfall series by $M \in [0.0, 3.0]$.
- `RAINFALL_ADDITION`: Distributing total event addition $+A \text{ mm}$ proportionally across baseline temporal storm profile.
- `DRAINAGE_CAPACITY_REDUCTION`: Scaling full pipe capacities by $C < 1.0$.
- `DRAINAGE_CAPACITY_INCREASE`: Augmenting known pipe capacities by $C > 1.0$.
- `DRAINAGE_NODE_INTERVENTION`: Enhancing node intake capacities based on Phase 12 candidate linkages.
- `PUMP_OR_DEWATERING_SCENARIO`: Applying continuous removal rate at outfall nodes.
- `COMBINED_SCENARIO`: Applying rainfall multiplier/addition followed by drainage capacity adjustments in deterministic order.

---

## 5. Unsupported Scenarios
- `TEMPORARY_BARRIER`: Phase 6 physical engine does not currently represent spatial barrier hydraulic deflection. Returns `is_valid: False` with status `UNSUPPORTED`.
- `STORAGE_INTERVENTION`: Phase 6 engine does not represent offline retention basin storage dynamics. Returns status `UNSUPPORTED`.
- **Enforcement**: No fake hydraulic physics generated for unsupported types.

---

## 6. Baseline Validation
- Baseline Digital Twin runs (`dt_mithi_baseline_001`) evaluated as Execution 1.
- Baseline terrain DEM, rainfall forcing, and drainage network remain completely read-only and immutable.
- Scenario execution operates on temporary isolated input copies.

---

## 7. Rainfall Multiplier
- Tested `RAINFALL_MULTIPLIER` at 1.00x, 1.25x, and 1.50x.
- Formula: $R_{\text{scen}}(t) = R_{\text{base}}(t) \times M$.
- Confirmed strict deterministic scaling across all timesteps with zero random spatial or temporal noise.

---

## 8. Rainfall Addition
- Tested `RAINFALL_ADDITION` (+25 mm total event addition).
- Distributed proportionally to baseline temporal intensity profile: $R_{\text{scen}}(t) = R_{\text{base}}(t) + \Delta R(t)$.
- Baseline temporal storm curve preserved without inventing sub-hourly radar noise.

---

## 9. Drainage Capacity Reduction
- Tested `DRAINAGE_CAPACITY_REDUCTION` (e.g. 20% blockage, $C = 0.80$).
- Known pipe capacities modified: $Q_{\text{cap, scen}} = Q_{\text{cap, base}} \times 0.80$.
- Unknown capacity policy: Links with `UNKNOWN` capacity remain `UNKNOWN` unless user explicitly supplies `unknown_capacity_policy`. Never converted `UNKNOWN` $\rightarrow 0$.

---

## 10. Drainage Capacity Increase
- Tested `DRAINAGE_CAPACITY_INCREASE` ($C = 1.50$).
- Known capacities augmented deterministically; baseline network structures preserved.

---

## 11. Drainage Node Intervention
- Mapped Phase 12 intervention candidates (`cand_drainage_culvert_expansion_l2`).
- Target nodes validated against available network graph. Unavailable nodes return `FAILED` / `UNAVAILABLE`.

---

## 12. Combined Scenario
- Tested combined rainfall multiplier (1.25x) + drainage capacity reduction (0.80x).
- Applied in strict deterministic order: Rainfall overlay transformation $\rightarrow$ Drainage network capacity transformation.
- Repeated executions yield identical output checksums.

---

## 13. Outcome Metrics
- Multi-metric evaluation compares:
  1. Flooded Area ($\text{Depth} \ge 0.05\text{ m}$) in $\text{km}^2$
  2. High/Severe Exposure Area ($\text{Depth} \ge 0.30\text{ m}$) in $\text{km}^2$
  3. Maximum Water Depth in meters
- Classifications:
  - `IMPROVED`: Flooded area decreases and high/severe area does not increase.
  - `NO_SIGNIFICANT_CHANGE`: All metric deltas within configured tolerance ($\le 2\%$).
  - `WORSE`: Flooded area or high/severe area increases.
  - `INCONCLUSIVE`: Conflicting deltas (e.g. area decreases but max depth increases) or mass balance error.

---

## 14. Governance
- Every API summary payload and UI panel includes mandatory governance disclaimers:
  - *"Simulator results are model-based what-if estimates and are not guarantees of real-world outcomes."*
  - *"Modeled benefit is conditional on the selected model assumptions, baseline inputs, and intervention representation."*

---

## 15. Provenance
- Provenance hash (`provenance_hash`) calculated via SHA256 over scenario parameters, baseline run ID, engine version, recorded assumptions, and input source identifiers.
- Complete audit chain retrievable via `GET /api/v1/simulator/scenarios/{id}/provenance`.

---

## 16. Artifact Validation
- Raster slice artifacts stored under `data/processed/simulator/{scenario_id}/{run_id}/slice_{minutes:03d}.json`.
- Each artifact includes SHA256 checksum, EPSG CRS string, affine transform coefficients, width, height, and nodata value.
- Baseline rasters isolated and un-overwritten.

---

## 17. API Validation
- `POST /api/v1/simulator/scenarios`: HTTP 201 Created
- `GET /api/v1/simulator/scenarios/{id}`: HTTP 200 OK / 404 Not Found
- `POST /api/v1/simulator/scenarios/{id}/validate`: HTTP 200 OK (`is_valid`, `status`, `assumptions`)
- `POST /api/v1/simulator/scenarios/{id}/run`: HTTP 200 OK (Executes Phase 6 engine, returns run summary, 7 comparisons, diagnostics)
- `GET /api/v1/simulator/runs/{id}/comparison`: HTTP 200 OK
- `GET /api/v1/simulator/scenarios/{id}/provenance`: HTTP 200 OK

---

## 18. Failure States
- Non-finite numeric parameters (`NaN`, `Infinity`) $\rightarrow$ Rejected HTTP 400 (`rejection_reason`).
- Out-of-bounds multiplier ($M < 0.0$ or $M > 3.0$) $\rightarrow$ Status `FAILED`.
- Missing required baseline run ID $\rightarrow$ Rejected HTTP 400.
- Solver mass balance violation ($> 0.01 \text{ m}^3$) $\rightarrow$ Run status `FAILED`, outcome `INCONCLUSIVE`.

---

## 19. REAL_DATA / TEST Isolation
- `REAL_DATA` mode uses validated Mithi DEM, forecast series, and network data.
- Synthetic fixtures in `TEST`/`DEV` mode explicitly labeled (`source_type = SYNTHETIC_IMERG_OBSERVATION`). Zero silent synthetic fallback.

---

## 20. ML Integrity
- **Artifact Path**: `backend/data/models/aquora_xgboost_prototype.joblib`
- **File Size**: 540,614 bytes
- **SHA256**: `103f9784dd5ebfee1517a7f9cacd934085dce418fd3013c10fb5e078052e2038`
- **Last Modified Timestamp**: `2026-09-13T13:36:18Z` (Read-only, completely untouched).

---

## 21. Digital Twin Integration
- Reuses canonical timeline slices (T+0, T+30, T+60, T+90, T+120, T+150, T+180).
- Scenario slices explicitly tagged `SCENARIO` vs baseline `BASELINE`.

---

## 22. Routing Integration
- Preserved Phase 10 routing boundary. No duplicate routing solver introduced.

---

## 23. Critical Access Integration
- Preserved Phase 11 critical access semantics. Operational facility status evaluated against scenario inundation slices without custom access algorithms.

---

## 24. Protect City Integration
- Linked Phase 12 intervention candidates to scenario node parameterizations. Priority scores remain un-mutated.

---

## 25. Ground Truth Boundary
- Ground Truth observations (Phase 13) serve as qualitative validation context; never automatically override physical solver parameters.

---

## 26. Browser Validation
- E2E Playwright subagent verified `/simulator` route.
- Verified header, governance notice banner, baseline panel, taxonomy builder dropdown, rainfall slider, Validate button, Run button, outcome classification badge (`WORSE`), timeline slice tabs (`+0m` to `+180m`), metric cards, and audit provenance section.

---

## 27. Map Validation
- Spatial grid resolution ($30\text{m} \times 30\text{m}$) and coordinate bounds verified. No undefined coordinates or `NaN` values.

---

## 28. Network Validation
- Network requests target `/api/v1/simulator/*`.
- All requests returned HTTP 200 / 201 with valid JSON schemas. Zero 404/500 errors.

---

## 29. Console Validation
- Console logs captured during browser subagent execution: Zero JavaScript errors, zero React warnings, zero unhandled promise rejections.

---

## 30. Runtime Status
- **PostgreSQL / Redis**: Offline in local development environment.
- **Service Mode**: Degraded file-backed / in-memory JSON mode (`_IN_MEMORY_SCENARIOS`, `_IN_MEMORY_RUNS`).
- **Reporting**: `NORMAL RUNTIME = NOT AVAILABLE`, `DEGRADED RUNTIME = VALIDATED`.

---

## 31. Security
- Bounds checks enforce $M \in [0.0, 3.0]$ and addition $\le 500\text{ mm}$.
- Non-finite float checks block `NaN` / `Inf` payloads.
- Path traversal protection on artifact storage references.

---

## 32. Tests
- Phase 14 Test Suite (`pytest backend/tests/test_phase14_simulator.py -v`): **16 / 16 PASSED** (4.00s execution time).

---

## 33. Regression
- Multi-Phase Regression Suite (`test_phase6c`, `test_phase8`, `test_phase9`, `test_phase10`, `test_phase11`, `test_phase12`, `test_phase13`): **109 / 109 PASSED**.

---

## 34. Ruff
- Executed `ruff check` on Phase 14 backend files: **0 errors found** (All checks passed cleanly).

---

## 35. TypeScript
- Executed `npx tsc --noEmit` in `frontend/`: **0 errors found** (Clean compilation).

---

## 36. Build
- Executed `npm run build` in `frontend/`: **SUCCESS** (Vite production bundle generated in 13.47s).

---

## 37. Files Modified
- `backend/app/services/simulator_service.py`: Added `# noqa` annotations for linter cleanliness and refactored nested if checks.
- `backend/app/api/v1/simulator.py`: Added `# noqa: B008` annotations for FastAPI `Depends(get_db)` parameters.

---

## 38. Defects Found
1. PostgreSQL / Redis services offline locally (degraded file-backed mode active).
2. Ruff linter flagged `Depends(get_db)` default argument usage in FastAPI router (resolved via `# noqa: B008`).

---

## 39. Fixes Made
- Applied minimal `# noqa` annotations and refactored nested if conditions in `simulator_service.py` and `simulator.py` to satisfy Ruff.

---

## 40. Remaining Limitations
1. Validation performed under local degraded file-backed storage mode (PostgreSQL & Redis offline).
2. Physical barrier and retention basin hydraulics are not currently modeled by Phase 6 solver (correctly reported as `UNSUPPORTED`).

---

## 41. Final Verdict
```
PASS WITH LIMITATIONS
```
*(Phase 14 remains UNLOCKED. Phase 15 has NOT been started. Execution stopped per instructions.)*
