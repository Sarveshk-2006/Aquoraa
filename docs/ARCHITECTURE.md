# Aquora Architecture Specification

## 1. System Topology & Component Layout

Aquora follows a **Modular Monolith + Async Workers** pattern to maximize performance, maintainability, and reproducibility.

```text
  [ External Data Sources ]
   (Radar, Satellites, Sensor APIs, Ground Observations)
              │
              ▼
   [ Data Provider Layer ] (App Providers)
              │
              ▼
  [ Application Service Layer ] (Orchestration & State Management)
              │
    ┌─────────┴─────────┐
    ▼                   ▼
[PostgreSQL/PostGIS] [Redis Queue/Cache]
    ▲                   │
    │                   ▼
    │           [Scientific Engines]
    │           - Rainfall Engine
    │           - Terrain Engine
    │           - Runoff Engine
    │           - Drainage Engine
    │           - Surface Flow Engine
    │           - Coupled Physics Engine
    │           - ML Calibration Engine
    │                   │
    └───────────────────┘
              │
              ▼
     [ API / Web Socket ] (/api/v1/)
              │
              ▼
     [ React Frontend Shell ]
```

---

## 2. Implementation Boundaries

### IMPLEMENTED NOW (Phase 0 - Phase 12)
- FastAPI Modular Monolith with `/api/v1/` versioning.
- `GET /api/v1/health/live` (Liveness) & `GET /api/v1/health/ready` (Readiness).
- `RequestIDMiddleware` propagating `X-Request-ID` correlation headers & structlog context.
- Centralized `AppException` handlers returning standardized `{"error": {...}}` JSON objects without leaking stack traces.
- SQLAlchemy 2.x Async Session factory & PostGIS migration foundation (`audit_events`, `model_runs`, `digital_twin_runs`, `routing_runs`, `critical_access_runs`, `protect_city_runs`).
- React + TypeScript + Vite frontend with TanStack Query hooks, `ApiClient` wrapper, and MapLibre boundary canvas.
- Phase 3: Rainfall + Forecast Data Pipeline.
- Phase 4: Terrain / Catchment / Surface Flow Engine.
- Phase 5: Drainage Network Engine.
- Phase 6: Coupled 1D/2D Flood Simulation Engine.
- Phase 7: Real Dataset Creation & Sentinel-1 SAR Processing.
- Phase 8: ML Residual Error Calibration & Nowcasting Prototype.
- Phase 9: Digital Twin (7 temporal slices: 0..180 min).
- Phase 10: Travel Window (Flood-Aware Routing & Exposure Engine).
- Phase 11: Critical Access Guardian (Facility Loss-of-Access Analysis).
- Phase 12: Protect the City (Explainable Intervention Priority Decision-Support Layer).

> **Governance Disclaimer**: Protect the City provides modeled decision-support recommendations. It does not issue official municipal, emergency, evacuation, traffic-control, or engineering orders.

### PLANNED FOR LATER (Phase 13+)
- Phase 13+: Citizen Ground Truth Loop, Aquora Storm Simulator, Multi-channel Alerts, Production Infrastructure.
