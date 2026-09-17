# AQUORA — RAINFALL + FORECAST DATA PIPELINE ARCHITECTURE (PHASE 3)

## 1. Executive Summary

Phase 3 establishes the normalized, provenance-aware **Rainfall + Forecast Data Pipeline** for **AQUORA — Urban Flood Intelligence & Response Platform**.

Following the core AQUORA engineering philosophy:

> **Physics/GIS first → ML calibration second → ground-truth feedback third.**

This pipeline provides normalized spatial-temporal precipitation inputs for future hydrological surface-flow and runoff calculation engines (Phase 4).

---

## 2. Core Architectural Separation

```
  +-------------------------------------+         +-------------------------------------+
  |      RAINFALL OBSERVATIONS          |         |         PRECIPITATION FORECASTS     |
  |     (e.g., NASA GPM IMERG V07B)     |         |     (0–3 Hour Horizon Nowcasts)     |
  +-------------------------------------+         +-------------------------------------+
                     |                                               |
                     v                                               v
        BaseRainfallProvider                            BaseForecastProvider
                     |                                               |
                     v                                               v
        RainfallIngestionService                        ForecastIngestionService
                     |                                               |
                     v                                               v
        RainfallObservationGrid                         RainfallForecastGrid
  (Accumulation mm / Intensity mm/h)                (Initialization T0, Valid T_valid, Lead Δt)
```

### Critical Scientific Principles
1. **Observation vs. Forecast Separation**: NASA GPM IMERG is a precipitation observation/estimation product — **NOT** a weather forecast. Rainfall observations and short-term forecast inputs are modeled as separate abstractions (`BaseRainfallProvider` vs. `BaseForecastProvider`).
2. **Resolution Realism**: IMERG spatial resolution is ~0.1° (~10km) and temporal resolution is 30 minutes. The architecture strictly forbids claiming street-level precision from ~0.1° satellite estimates.

---

## 3. Provider Architecture

### 3.1 `BaseRainfallProvider` & `IMERGRainfallProvider`
- **Adapter**: `IMERGRainfallProvider` implements vendor-neutral `BaseRainfallProvider`.
- **IMERG V07B Product Variants**:
  - `Final`: Research quality (latencies ~3.5 months).
  - `Late`: Operational monitoring (latencies ~14 hours).
  - `Early`: Near real-time monitoring (latencies ~4 hours).
- **Credentials**: Earthdata authentication (`NASA_EARTHDATA_USERNAME`, `NASA_EARTHDATA_PASSWORD`) is encapsulated within the adapter layer.

### 3.2 `BaseForecastProvider` & `SyntheticForecastProvider`
- **Lead Time Horizons**: Explicitly expresses $T_0$ (initialization time), $T_{valid}$ (valid time), and lead times $\Delta t \in [0, 30, 60, 90, 120, 150, 180]$ minutes.
- **Fixture**: `SyntheticForecastProvider` is provided strictly as a `TEST FIXTURE ONLY` for pipeline verification.

---

## 4. Quantity, Units & Quality Semantics

### 4.1 Quantities & Units
- **Accumulation**: $P_{accum}$ (mm over interval duration $\Delta t$).
- **Intensity Rate**: $i_{mm/h} = (P_{accum} / \Delta t_{min}) \times 60.0$.
- **Conversions**: `app.geospatial.units` provides explicit conversion routines.

### 4.2 Quality Status Flags (`QualityStatus`)
- `VALID`: Measured valid observation (including measured `0.0` zero rainfall).
- `MISSING`: Missing observation.
- `INVALID`: Failed validation (e.g. negative rainfall value).
- `SUSPECT`: Out of physical bounds.
- `NODATA`: Sentinel value (-9999.0).
- **Mandatory Rule**: `NODATA` (missing observation) is **NEVER** silently converted into `0.0` zero rainfall.

---

## 5. Persistence & Ingestion Schema

Defined in Alembic migration `0003_phase3_rainfall.py`:
- `rainfall_observation_grids`: Stores dataset metadata, spatial bounds (PostGIS GiST index), observation interval, duration, units, quality status, and JSONB provenance.
- `rainfall_forecast_grids`: Stores forecast metadata, spatial bounds (GiST index), initialization time, valid time, lead time minutes, units, quality status, and provenance.
- `ingestion_runs`: Execution audit log (`pipeline_type`, `provider`, `source_identifier`, `status`, `records_ingested`, `error_message`, timestamps).
- **Idempotency**: Unique constraint on `dataset_identifier` guarantees deterministic ingestion without duplicate record creation.

---

## 6. Hard Scope Boundary Confirmation

Phase 3 explicitly **EXCLUDES**:
- ML / XGBoost / scikit-learn / Kaggle / final ML training dataset (Belongs to Phase 7).
- SCS-CN runoff / infiltration / hydrology / slope / flow accumulation / catchment delineation (Belongs to Phase 4).
- Drainage network simulation (Belongs to Phase 5).
- 2D shallow-water flood simulation (Belongs to Phase 6).
- Routing / travel window / critical access guardian / citizen reports / alerts (Belongs to Phase 10-15).
