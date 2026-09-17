# Phase 11 — Critical Access Guardian Specification & Integration Guide

## 1. Overview & Core Objective

Phase 11 introduces the **Critical Access Guardian** layer for AQUORA (Urban Flood Intelligence & Response Platform).

Phase 11 answers the critical operational question:
> **"Can this critical facility still be reached as modeled flooding evolves?"**

### Core Architectural Hierarchy
```
Critical Facility
       ↓
Responder Origin
       ↓
Phase 10 RoutingProcessingService (REUSED)
       ↓
Candidate Route(s)
       ↓
Phase 10 Route Exposure / Travel Window (REUSED)
       ↓
Phase 11 Critical Access Policy Threshold (CRITICAL_ACCESS_SEVERITY)
       ↓
Accessibility Timeline (7 Canonical Slices: 0, 30, 60, 90, 120, 150, 180 min)
       ↓
Modeled Loss-of-Access & Time-to-Loss Calculation
       ↓
Alternate Access Corridor Selection & Evaluation
       ↓
Explainable Access Recommendation & Governance Warnings
```

---

## 2. Invariants & Scope Boundaries

1. **Reuses Phase 10 Services Exclusively**: Phase 11 does **NOT** contain a second routing provider or route-to-raster intersection engine. It consumes candidate routes and exposure timelines directly from `RoutingProcessingService`.
2. **Reuses Phase 9 Digital Twin Slices**: Slices are evaluated across the 7 canonical intervals ($0, 30, 60, 90, 120, 150, 180$ min).
3. **Loss-of-Access Definition**: Loss of access (`modeled_loss_of_access_min`) occurs **ONLY when NO acceptable candidate route remains** under the configured Phase 11 access policy.
4. **Primary vs. Alternate Route Rules**: If the primary route is compromised/hazard-impacted but an acceptable alternate candidate exists, the recommendation is `USE_ALTERNATE` and the facility access status remains `ACCESSIBLE` or `LIMITED` (it is **NOT** marked `ACCESS_COMPROMISED`).
5. **No Fabricated Data**: Facilities are retrieved from authoritative sources or explicit, deterministic synthetic fixtures tagged `SYNTHETIC` and `DEVELOPMENT_ONLY`.
6. **Operational Status Independence**: Facility operational status (`UNKNOWN`, `OPEN`, `CLOSED`) is maintained separately from physical route accessibility and is **NEVER** inferred from flood state.
7. **ML & Label Restrictions**: Phase 8 ML scores are strictly labeled `PROTOTYPE_ONLY`. Zero Phase 7 training labels are exposed.

---

## 3. Controlled Taxonomy & Facility Provenance Hierarchy

### Controlled Categories
- `HOSPITAL`
- `CLINIC`
- `FIRE_STATION`
- `POLICE_STATION`
- `AMBULANCE_BASE`
- `EMERGENCY_CONTROL_CENTER`
- `SHELTER`
- `OTHER_CRITICAL`

### Source Hierarchy
1. Authoritative municipal/government datasets
2. Official institutional registries
3. Verified open-government datasets
4. Verified OpenStreetMap features
5. Deterministic development/test fixtures (`TEST FACILITY — ...`)

---

## 4. Accessibility States & Policy Thresholds

### Accessibility States
- `ACCESSIBLE`: At least one acceptable route meets policy without material hazard exposure.
- `LIMITED`: Access is possible, but travel window or exposure margin is reduced.
- `AT_RISK`: Route degradation is imminent or candidate routes reach hazard threshold.
- `COMPROMISED`: No acceptable candidate route remains under configured access policy.
- `UNKNOWN`: Insufficient flood or routing data available.

### Severity Threshold Separation
- **Phase 10**: `ROUTE_IMPACT_SEVERITY` (evaluates route exposure & travel window)
- **Phase 11**: `CRITICAL_ACCESS_SEVERITY` (evaluates facility accessibility policy threshold, default `HIGH`)

---

## 5. Causal Explainability & Governance Disclaimer

Every access result supplies a human-readable, causal explanation detailing route durations, onset times, peak severities, and alternate corridor availability.

### Mandatory Operational Disclaimer
> *"Critical Access Guardian provides modeled accessibility intelligence. It is not an official emergency-access, evacuation, or facility-operational-status system."*
