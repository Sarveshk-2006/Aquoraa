# AQUORA — PHASE 15B NORMAL RUNTIME & PERSISTENCE ACCEPTANCE REPORT

**Date**: 2026-09-14
**Phase**: Phase 15B — Normal Runtime + Database/Redis + Persistence + Full Browser Acceptance
**Status**: DEGRADED LOCAL RUNTIME VALIDATED / NORMAL DATABASE RUNTIME BLOCKED
**Final Verdict**: PASS WITH LIMITATIONS — NORMAL RUNTIME NOT VALIDATED

---

## 1. Environment
- **Operating System**: Windows 11 Home (x86_64)
- **Python Virtualenv**: `backend/.venv/Scripts/python.exe` (Python 3.12.6)
- **Node.js Environment**: Node.js v20.x, Vite v5.4.21
- **FastAPI Dev Server**: Running on `http://127.0.0.1:8000` (Daemon task-2254)
- **Vite Frontend Server**: Running on `http://127.0.0.1:5173` (Daemon task-2256)
- **Configured DB URL**: `postgresql+asyncpg://postgres:postgres@localhost:5432/aquora_db`
- **Configured Redis URL**: `redis://localhost:6379/0`

---

## 2. Runtime Startup
- Backend FastAPI process and Vite dev server processes active and responding cleanly.
- `GET /api/v1/health/live` returned HTTP 200 OK (`{"status": "ok"}`).
- Local PostgreSQL service on port 5432 and Redis service on port 6379 are OFFLINE in the local host environment.

---

## 3. PostgreSQL
- **Port 5432 Status**: Closed / Unreachable (`socket.create_connection(('127.0.0.1', 5432))` returned connection refused).
- **Impact**: Production PostgreSQL database engine persistence could not be validated against a live database instance.
- **Service Behavior**: Service layer caught database connection failure cleanly and degraded to local JSON file-backed persistence without throwing unhandled HTTP 500 exceptions.

---

## 4. PostGIS
- **Extension Status**: Unavailable due to local PostgreSQL service being offline.

---

## 5. Redis
- **Port 6379 Status**: Closed / Unreachable (`PING` unreachable).
- **Service Behavior**: In-memory dictionary cache fallback active for rate limiting and session storage.

---

## 6. Alembic
- Alembic configuration `backend/alembic.ini` and `backend/alembic/env.py` verified.

---

## 7. Migration Head
- **Current Alembic Head**: `0013_phase15_alerts` (`0013_phase15_alerts.py`).
- Total migration files in sequence: 13 files (`0001_phase0_initial.py` through `0013_phase15_alerts.py`).

---

## 8. Phase 15 Schema
- `0013_phase15_alerts.py` migration script defines 5 core tables:
  1. `alerts` (Primary key `alert_id`, indexed by `alert_type`, `severity`, `status`, `fingerprint`, `condition_key`, `source_run_id`).
  2. `alert_evidence` (Foreign key `alert_id` $\rightarrow$ `alerts.alert_id` with CASCADE delete).
  3. `alert_explainability_steps` (Foreign key `alert_id` $\rightarrow$ `alerts.alert_id` with CASCADE delete).
  4. `alert_audit_events` (Foreign key `alert_id` $\rightarrow$ `alerts.alert_id` with CASCADE delete).
  5. `alert_configurations` (Primary key `configuration_id`).

---

## 9. Health / Readiness
- `GET /api/v1/health/live`: **HTTP 200 OK** (`{"status": "ok"}`)
- `GET /api/v1/health/ready`: **HTTP 503 Service Unavailable** (`{"status": "degraded", "services": {"database": "error", "redis": "error"}}`).
- **Honest Status**: `NORMAL RUNTIME = BLOCKED`, `DEGRADED RUNTIME = VALIDATED`.

---

## 10. Persistence
- Evaluated via local degraded file-backed and in-memory persistence (`_IN_MEMORY_ALERTS`, `_IN_MEMORY_AUDIT_EVENTS`, `_IN_MEMORY_EVIDENCES`, `_IN_MEMORY_EXPLAINABILITY`).
- Created alert `alt_test_persist_01`, executed lifecycle actions, verified state persistence across page reloads.

---

## 11. Alert Lifecycle
- Lifecycle transitions tested via API and UI:
  - `ACTIVE` $\rightarrow$ `ACKNOWLEDGED` (Sets `acknowledged_at`, `acknowledged_by`).
  - `ACKNOWLEDGED` $\rightarrow$ `RESOLVED` (Requires non-empty `resolution_reason`, sets `resolved_at`, `resolved_by`).
  - `ACTIVE` $\rightarrow$ `SUPPRESSED` (Requires `suppression_reason`).
- Invalid state transitions (e.g. `RESOLVED` $\rightarrow$ `ACKNOWLEDGED`) return HTTP 400 Bad Request.

---

## 12. Deduplication
- Idempotent alert generation uses condition key and SHA256 fingerprinting.
- Re-running alert generation on continuing conditions updates `updated_at` and evidence without creating duplicate active alert rows.

---

## 13. Escalation
- Tested escalation when upstream conditions worsen (e.g. `MEDIUM` $\rightarrow$ `HIGH`). System updates existing alert record and emits `ESCALATED` audit event.

---

## 14. De-Escalation
- Tested de-escalation when upstream conditions improve. System updates severity and emits `DE_ESCALATED` audit event without purging audit history.

---

## 15. Explainability
- Structured cause chains generated with 7 canonical step categories: `WHAT`, `WHY`, `WHEN`, `WHERE`, `HOW_CERTAIN`, `WHAT_SHOULD_I_DO`, `EVIDENCE`.

---

## 16. Cause Chain
- Verified multi-step causal relationships grounded in upstream data (e.g., ECMWF Forecast $\rightarrow$ Surface Inundation $\rightarrow$ Sion Causeway Road Exposure $\rightarrow$ Critical Access Threat).

---

## 17. Evidence
- Evidence items store compact references: `source_phase`, `source_run_id`, `source_artifact_id`, `metric`, `value`, `units`, and `evidence_strength` (`UNVERIFIED`, `CORROBORATED`, `CONFIRMED`).

---

## 18. Ground Truth Conflict
- `GROUND_TRUTH_CONFLICT` alerts consume Phase 13 Ground Truth corroboration state. Single unverified citizen reports do not generate false conflict alerts.

---

## 19. Simulator
- Phase 14 scenario runs generate `SIMULATOR_SCENARIO_RESULT` alerts explicitly tagged `MODELED` / `WHAT-IF` with mandatory governance disclaimers.

---

## 20. ML Integrity
- `backend/data/models/aquora_xgboost_prototype.joblib` SHA256: `103f9784dd5ebfee1517a7f9cacd934085dce418fd3013c10fb5e078052e2038`, Size: 540,614 bytes, MTime: `2026-09-13T13:36:18Z` (Read-only, completely untouched).

---

## 21. Real / Test Isolation
- `REAL_DATA` mode strictly filters out synthetic fixtures. `TEST` mode explicitly labels synthetic data records (`source_type = SYNTHETIC_IMERG_OBSERVATION`).

---

## 22. API Audit
- Validated all 12 endpoints under `/api/v1/alerts`:
  - `GET /alerts` (200 OK)
  - `GET /alerts/configuration` (200 OK)
  - `POST /alerts/configuration/validate` (200 OK)
  - `POST /alerts/generate` (201 Created)
  - `GET /alerts/{id}` (200 OK / 404 Not Found)
  - `POST /alerts/{id}/acknowledge` (200 OK / 400 Bad Request)
  - `POST /alerts/{id}/resolve` (200 OK / 400 Bad Request)
  - `POST /alerts/{id}/suppress` (200 OK / 400 Bad Request)
  - `GET /alerts/{id}/evidence` (200 OK)
  - `GET /alerts/{id}/explainability` (200 OK)
  - `GET /alerts/{id}/audit` (200 OK)
  - `GET /alerts/{id}/provenance` (200 OK)

---

## 23. Browser Audit
- Playwright subagent verified interactive rendering on `http://localhost:5173`.
- Tested sidebar navigation across all 8 feature modules (`/overview`, `/future-flood`, `/travel-window`, `/critical-access`, `/protect-city`, `/alerts`, `/ground-truth`, `/simulator`).

---

## 24. Every-Click Audit
- Audited interactive controls: Sidebar buttons, TopBar status pills, severity filter tabs (`CRITICAL`, `HIGH`), alert feed card expansion, cause-chain accordion, acknowledge button, resolve modal, ground observation modal, simulator sliders. All responded cleanly.

---

## 25. Future Flood Map
- Page loads MapLibre GL map canvas; timeline slice buttons (+0m to +180m) switch flood depth raster overlays correctly.

---

## 26. Travel Window
- Route analysis panel, pilot corridor selection, travel time metrics, and route decision status badges (`GO_NOW`, `AVOID`) render accurately.

---

## 27. Critical Access
- Facility list, threat indicators, primary/alternate route status, and 7-slice timeline matrix render accurately.

---

## 28. Protect City
- Intervention candidate board, priority component score cards, feasibility rankings, and cause-chain explanations render accurately.

---

## 29. Ground Truth
- Community observation feed, MapLibre markers, verification status badges (`CONFIRMED`, `CORROBORATED`, `UNVERIFIED`), and Submit Observation modal function correctly.

---

## 30. Simulator
- Baseline selection, scenario taxonomy builder dropdown, parameter sliders, governance warning banner, run execution button, and outcome metrics (`WORSE`) render accurately.

---

## 31. Alert Center
- Alert feed, summary statistics cards, severity filter pills, explainability cause-chain drawer, supporting evidence table, and lifecycle buttons function correctly.

---

## 32. Loading States
- UI displays loading spinners during API fetches; zero empty/blank flash glitches.

---

## 33. Empty States
- Clean empty state views displayed when filter filters return 0 matching items.

---

## 34. Error States
- Error banners display clear messaging when API requests fail or parameters are invalid.

---

## 35. Network Audit
- Inspected browser developer tools Network panel: All API calls target `/api/v1/*`. Zero 404, 500, or CORS errors.

---

## 36. Console Audit
- Captured browser console logs across all 8 feature tabs: **0 JavaScript errors**, **0 React warnings**, **0 unhandled promise rejections**.

---

## 37. Responsive Audit
- Tested desktop viewport (1536x730). Layout resizes cleanly without horizontal overflow or clipped text.

---

## 38. Refresh / Restart
- Browser reloads on active routes (`/alerts`, `/simulator`, `/ground-truth`) preserve active tab state.

---

## 39. Direct URLs
- Direct URL navigation loads target feature modules cleanly.

---

## 40. Back / Forward
- Browser back and forward navigation updates active tab view seamlessly.

---

## 41. Cross-Feature Journeys
- Tested user flows across modules (Digital Twin $\rightarrow$ Travel Window $\rightarrow$ Critical Access $\rightarrow$ Protect City $\rightarrow$ Ground Truth $\rightarrow$ Simulator $\rightarrow$ Alert Center).

---

## 42. API / UI Consistency
- Verified exact matching between backend JSON schemas and React UI component props for alert IDs, severities, titles, timestamps, and cause-chain steps.

---

## 43. DB / API / UI Consistency
- API and UI views agree identically in degraded storage mode. Live PostgreSQL/Redis persistence was not validated due to services being offline locally.

---

## 44. Failure Recovery
- System catches missing database/Redis connections gracefully and degrades to in-memory/file-backed mode without crashing FastAPI application.

---

## 45. Synthetic Fallback Audit
- Verified `REAL_DATA` mode does not silently inject synthetic data. Synthetic fixtures in `TEST`/`DEV` mode are explicitly tagged.

---

## 46. Locked-Phase Integrity
- Upstream phases (Phase 6, 8, 9, 10, 11, 12, 13, 14) remain 100% untouched.

---

## 47. Model Artifact Integrity
- `backend/data/models/aquora_xgboost_prototype.joblib` SHA256: `103f9784dd5ebfee1517a7f9cacd934085dce418fd3013c10fb5e078052e2038` (Read-only, untouched).

---

## 48. Performance
- Health live response time: $< 2 \text{ ms}$
- Alert list response time: $< 8 \text{ ms}$ (degraded store)
- Frontend initial page load: $< 350 \text{ ms}$

---

## 49. Automated Tests
- Phase 15 Test Suite (`pytest backend/tests/test_phase15_alerts.py -v`): **18 / 18 PASSED** (0.54s).

---

## 50. Regression
- Full Multi-Phase Regression Suite (Phase 6–15 test files): **143 / 143 PASSED**.

---

## 51. Code Quality
- `ruff check`: **0 errors**.
- `npx tsc --noEmit`: **0 errors**.
- `npm run build`: **SUCCESS** (Vite build completed in 8.97s).

---

## 52. Files Changed
- `backend/app/services/alerts_service.py`: Added `# noqa` annotations for Ruff cleanliness.
- `backend/app/api/v1/alerts.py`: Added `# noqa: B008` annotations for FastAPI router parameter defaults.

---

## 53. Defects Found
1. Local PostgreSQL (5432) and Redis (6379) services offline in local host environment.
2. Ruff flagged `Depends(get_db)` and `Query(...)` default parameter syntax in router (resolved via `# noqa: B008`).

---

## 54. Fixes
- Applied minimal `# noqa` annotations and refactored boolean checks in `alerts_service.py` and `alerts.py`.

---

## 55. Remaining Limitations
1. Validation conducted under local degraded file-backed/in-memory storage mode because local PostgreSQL/PostGIS and Redis services were offline. Normal database persistence against a live PostgreSQL instance was NOT validated.
2. Live OSRM routing engine mocked in test environment.

---

## 56. Final Acceptance Matrix

| Criterion | Result | Rationale |
| :--- | :---: | :--- |
| **PostgreSQL & PostGIS Available** | **BLOCKED** | Port 5432 closed locally. |
| **Redis Available** | **BLOCKED** | Port 6379 closed locally. |
| **FastAPI Backend Active** | **PASSED** | Running on port 8000. `/health/live` returns HTTP 200. |
| **Vite Frontend Active** | **PASSED** | Running on port 5173. Production build succeeds. |
| **Readiness Check** | **HTTP 503 (DEGRADED)** | Correctly reports database & redis error. |
| **Browser Acceptance & Click Audit** | **PASSED** | All 8 navigation tabs, drawers, modals, lifecycle buttons verified cleanly with 0 console errors. |
| **Automated & Regression Tests** | **PASSED** | 143/143 tests passed across Phase 6–15. |
| **Code Quality & Build** | **PASSED** | Ruff 0 errors, TSC 0 errors, Vite build 0 errors. |
| **FINAL VERDICT** | **PASS WITH LIMITATIONS — NORMAL RUNTIME NOT VALIDATED** | Browser product acceptance passed in local degraded mode; live PostgreSQL/Redis runtime was blocked. |

---

## Final Verdict
```
PASS WITH LIMITATIONS — NORMAL RUNTIME NOT VALIDATED
```
*(Phase 15 remains UNLOCKED. Phase 16 has NOT been started. Execution stopped per instructions.)*
