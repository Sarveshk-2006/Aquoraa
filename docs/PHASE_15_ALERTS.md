# Phase 15 Specification — Alerts, Explainability, and Audit

## Executive Summary
Phase 15 defines the **Decision, Notification, Explainability, and Audit Layer** for AQUORA.
It consumes authoritative output signals from earlier phases (Phase 6 Flood Engine, Phase 9 Digital Twin, Phase 10 Travel Window, Phase 11 Critical Access Guardian, Phase 12 Protect City, Phase 13 Ground Truth, and Phase 14 Simulator) to generate, deduplicate, explain, and audit operational alerts without recreating flood physics, routing solvers, or risk scores.

---

## 1. Ownership & Non-Negotiable Boundaries
- **Phase 15 OWNS**:
  - Alert rule evaluation & generation from explicit source run IDs
  - Operational alert severity (`INFO`, `LOW`, `MEDIUM`, `HIGH`, `CRITICAL`)
  - Alert lifecycle (`ACTIVE`, `ACKNOWLEDGED`, `RESOLVED`, `EXPIRED`, `SUPPRESSED`, `FAILED`)
  - Fingerprint-based continuing-condition deduplication & escalation/de-escalation
  - Structured cause-chain explainability steps (`WHAT`, `WHY`, `WHEN`, `WHERE`, `HOW_CERTAIN`, `WHAT_SHOULD_I_DO`, `EVIDENCE`)
  - Compact evidence references & metrics storage
  - Audit trail logging and cryptographic provenance hashing
  - Configuration-driven operational thresholds

- **Phase 15 DOES NOT OWN**:
  - Flood physics, D8 routing, or mass balance solver (owned by Phase 6)
  - Future flood timeline canonical slices (owned by Phase 9)
  - Travel window & route sampling (owned by Phase 10)
  - Critical facility access calculation (owned by Phase 11)
  - Protect City intervention prioritization (owned by Phase 12)
  - Ground-truth corroboration or photo verification (owned by Phase 13)
  - What-if scenario simulation (owned by Phase 14)

---

## 2. Explicit Source-Run Contract
Alert generation endpoints accept explicit typed source references:
- `digital_twin_run_id`: Authoritative Phase 9 Digital Twin run reference
- `travel_window_run_id`: Authoritative Phase 10 Travel Window / Routing run reference
- `critical_access_run_id`: Authoritative Phase 11 Critical Access run reference
- `protect_city_run_id`: Authoritative Phase 12 Protect City run reference
- `ground_truth_run_id`: Authoritative Phase 13 Ground Truth verification run reference
- `simulator_run_id`: Authoritative Phase 14 Simulator scenario run reference

Clients cannot inject raw unverified flood values to forge alerts. At least one valid source run reference is required.

---

## 3. Alert Taxonomy & Deterministic Severity Mapping
- `FLOOD_ONSET`: Projected flood onset within lookahead window (`HIGH` / `CRITICAL`)
- `FLOOD_SEVERITY_ESCALATION`: Escalation in modeled flood severity (`HIGH`)
- `HIGH_SEVERE_FLOOD_RISK`: Significant near-term flood hazard (`HIGH` / `CRITICAL`)
- `TRAVEL_WINDOW_CLOSING`: Route travel window approaching warning threshold (`HIGH`)
- `ROUTE_AVOID`: Primary route unsafe due to modeled inundation (`CRITICAL`)
- `CRITICAL_ACCESS_THREAT`: Alternate facility route required (`HIGH`)
- `CRITICAL_ACCESS_LOSS`: Facility access unavailable (`CRITICAL`)
- `PROTECT_CITY_PRIORITY`: High-benefit intervention candidate identified (`HIGH` / `CRITICAL`)
- `GROUND_TRUTH_CONFLICT`: Material model vs corroboration discrepancy (`MEDIUM`)
- `MODEL_INPUT_DEGRADED`: Missing or incomplete input pipeline (`MEDIUM`)
- `MODEL_UNCERTAINTY`: Upstream model diagnostics indicate uncertainty (`LOW` / `MEDIUM`)
- `SIMULATOR_SCENARIO_RESULT`: What-if simulation outcome result (`INFO` / `MEDIUM`)
- `SYSTEM_DATA_QUALITY`: Upstream data pipeline quality notice (`INFO` / `LOW`)

---

## 4. Continuing-Condition Deduplication & Escalation
1. **Fingerprint**: Computed as `sha256(alert_type:affected_entity_type:affected_entity_id:condition_key)`.
2. **Deduplication Window**: Multiple runs evaluating the same active condition within `ALERT_DEDUPLICATION_WINDOW_MINUTES` update the existing active alert record rather than spawning duplicate rows.
3. **Escalation / De-escalation**: If upstream severity increases (e.g. `HIGH` -> `CRITICAL`), the alert is updated and an `ESCALATED` audit event is logged.

---

## 5. Language Semantics & Governance
All alert titles and summaries strictly distinguish between signal types:
- `MODELED`: Model-based Digital Twin / Flood engine outputs
- `OBSERVED`: Unverified community or sensor reports
- `CORROBORATED`: Verified multi-source field evidence
- `CONFIRMED`: Official authority confirmed events

Mandatory Governance Notice:
> *"Alerts are model-based decision-support signals and are not guarantees of real-world conditions."*

---

## 6. API Endpoints
- `GET /api/v1/alerts`: List operational alerts with status, severity, and type filters
- `GET /api/v1/alerts/{alert_id}`: Fetch complete alert detail
- `POST /api/v1/alerts/generate`: Idempotent alert generation from source run IDs
- `POST /api/v1/alerts/{alert_id}/acknowledge`: Acknowledge alert
- `POST /api/v1/alerts/{alert_id}/resolve`: Resolve alert with mandatory rationale
- `POST /api/v1/alerts/{alert_id}/suppress`: Suppress alert with mandatory rationale
- `GET /api/v1/alerts/{alert_id}/evidence`: List supporting evidence references
- `GET /api/v1/alerts/{alert_id}/explainability`: Fetch structured cause-chain steps
- `GET /api/v1/alerts/{alert_id}/audit`: Fetch lifecycle audit event history
- `GET /api/v1/alerts/{alert_id}/provenance`: Fetch provenance chain & cryptographic hash
- `GET /api/v1/alerts/configuration`: Read active operational threshold settings
- `POST /api/v1/alerts/configuration/validate`: Validate configuration settings payload
