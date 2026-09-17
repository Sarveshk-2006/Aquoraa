# Aquora Audit & Lineage Architecture Design

## Overview

Aquora requires complete scientific, operational, and data lineage traceability. Every automated run, manual configuration override, dataset ingestion, and simulation run must leave an immutable record in PostGIS.

---

## Data Model Lineage Flow

```text
Prediction / Inundation Grid
           │
           ▼
     Model Run (`model_runs` table)
           │
           ├──> Model Version & Code Git Hash
           ├──> Feature Version ID
           ├──> Input Dataset Versions (Rainfall, DEM, Soil, Drainage)
           └──> Execution Metrics Reference
           │
           ▼
    Audit Event (`audit_events` table)
           │
           ├──> Timestamp & Actor
           ├──> Action & Entity Type
           ├──> State Diff (Old Value / New Value)
           └──> System Metadata
```

---

## Phase 0 Database Schemas

### `audit_events` Table
- `id` (UUID / BigInt, Primary Key)
- `timestamp` (TIMESTAMPTZ, default NOW())
- `actor` (VARCHAR(128)) - User ID, System Service, or Worker Process
- `action` (VARCHAR(128)) - e.g., `DATASET_INGESTED`, `MODEL_EXECUTED`, `PARAM_UPDATED`
- `entity_type` (VARCHAR(128)) - Target table or entity
- `entity_id` (VARCHAR(128)) - Reference identifier
- `old_value` (JSONB) - Previous state
- `new_value` (JSONB) - Updated state
- `model_version` (VARCHAR(64)) - Active model build
- `data_version` (VARCHAR(64)) - Version hash of input spatial/temporal data
- `reason` (TEXT) - Justification for change
- `metadata` (JSONB) - Additional execution context

### `model_runs` Table
- `id` (UUID / BigInt, Primary Key)
- `model_version` (VARCHAR(64))
- `dataset_version` (VARCHAR(64))
- `feature_version` (VARCHAR(64))
- `input_timestamp` (TIMESTAMPTZ)
- `forecast_horizon` (VARCHAR(32)) - e.g., `0-3h`, `15m`
- `created_at` (TIMESTAMPTZ, default NOW())
- `status` (VARCHAR(32)) - e.g., `PENDING`, `RUNNING`, `COMPLETED`, `FAILED`
- `metrics_reference` (JSONB) - Storage pointer or loss metrics metadata
