# Phase 12: Protect the City — Decision Support & Intervention Prioritization

## Executive Summary

**Phase 12: Protect the City** serves as the decision-support layer of AQUORA.

Tagline: *"See the flood before it becomes a crisis."*

It addresses the fundamental question:
> *"Given the modeled flood evolution, where should the city consider intervening or protecting assets first, and why?"*

Protect the City consumes intelligence from previous phases (Phase 4 Terrain, Phase 5 Drainage, Phase 9 Digital Twin, Phase 10 Routing, and Phase 11 Critical Access) to produce transparent, explainable, and deterministic intervention recommendations.

---

## Product Philosophy & Governance

1. **Decision Support, Not Automated Commands**: Protect the City provides modeled recommendations for review. It does NOT issue official municipal, emergency, evacuation, traffic-control, or engineering orders.
2. **Explainable Cause-Chains**: Avoids opaque single-number "risk scores". Recommendations follow a traceable cause chain:
   $$\text{PREDICTION} \rightarrow \text{IMPACT} \rightarrow \text{CRITICALITY} \rightarrow \text{DECISION} \rightarrow \text{ACTION OPPORTUNITY}$$
3. **Qualitative Benefits & Feasibility**: Qualitative expected benefit (`HIGH`, `MEDIUM`, `LOW`, `UNKNOWN`) is used rather than fabricated depth-reduction percentages. Feasibility remains separate from physical threat.
4. **Mandatory Disclaimer**:
   > *"Protect the City provides modeled decision-support recommendations. It does not issue official municipal, emergency, evacuation, traffic-control, or engineering orders."*

---

## Architectural Boundary & Data Flow

```
                    PHASE 9
                Digital Twin
                     │
                     ▼
              Flood Evolution
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
       PHASE 4    PHASE 10    PHASE 11
       Terrain     Routing    Critical Access
          │          │          │
          └──────────┼──────────┘
                     ▼
                PHASE 12
             Protect the City
                     │
                     ▼
          Intervention Candidates
                     │
                     ▼
          Deterministic Prioritizer
                     │
          ┌──────────┼──────────┐
          ▼          ▼          ▼
        WHERE       WHY        WHEN
          │          │          │
          └──────────┼──────────┘
                     ▼
          Priority + Recommendation
                     │
                     ▼
              Explanation
```

Phase 12 owns candidate ingestion, taxonomy, priority component calculation, expected benefit assignment, feasibility tagging, uncertainty representation, cause-chain generation, audit logging, and the Protect the City UI. It does NOT own flood physics (Phase 6), raster Digital Twin generation (Phase 9), routing (Phase 10), or critical access calculations (Phase 11).

---

## Controlled Intervention Taxonomy

- `DRAINAGE_CLEARANCE`
- `DRAINAGE_CAPACITY_REVIEW`
- `PUMP_OR_DEWATERING_REVIEW`
- `TEMPORARY_BARRIER_REVIEW`
- `ROAD_ACCESS_PROTECTION`
- `CRITICAL_FACILITY_ACCESS_PROTECTION`
- `TRAFFIC_CONTROL_REVIEW`
- `OUTFALL_CAPACITY_REVIEW`
- `STORAGE_REVIEW`
- `SITE_INSPECTION`
- `OTHER_REVIEW`

---

## Provider Hierarchy & Fixture Policy

1. Authoritative municipal/utility sources
2. Official open government sources
3. Verified mapped infrastructure
4. OpenStreetMap / community sources
5. Deterministic analytical candidates
6. Synthetic development/test fixtures (`DEVELOPMENT_ONLY`, tagged `provider_mode = "SYNTHETIC"`, names prefixed with `TEST INTERVENTION CANDIDATE`)

---

## Priority Model & Component Breakdown

Priority is deterministic, explainable, bounded, and decomposable ($0 \le \text{final\_priority\_score} \le 125$):

### Raw vs. Final Score Clamping
- **`raw_priority_score`**: Theoretical sum of all component weights (Range: **-10.0 to 125.0**).
- **`final_priority_score`**: Operational score clamped to **0.0 to 125.0** using:
  $$\text{final\_priority\_score} = \max(0.0, \min(125.0, \text{raw\_priority\_score}))$$

### Semantic Priority Categories
Numeric scores serve as supporting signals; semantic rules remain authoritative:

| Priority Category | Semantic Criteria | Clamped Score Threshold |
| :--- | :--- | :--- |
| **CRITICAL** | Strong near-term ($\le 60\text{ min}$) HIGH/SEVERE flood threat **AND** critical facility access materially threatened (or major corridor impact). *Numeric score alone ($\ge 90$) does NOT grant CRITICAL.* | Semantic Rule Authoritative |
| **HIGH** | Significant modeled flood impact AND meaningful route/facility disruption. | $\text{final\_score} \ge 65.0$ |
| **MEDIUM** | Meaningful flood impact but lower consequence or later onset. | $\text{final\_score} \ge 40.0$ |
| **LOW** | Limited modeled impact and limited access consequence. | $\text{final\_score} < 40.0$ |
| **UNKNOWN** | Insufficient data available for responsible prioritization. | Data Incomplete |

### Component Breakdown
- **Flood Severity**: Up to 30 pts (based on peak flood severity slice)
- **Time-to-Threat**: Up to 25 pts (earlier onset receives higher priority)
- **Critical Access Impact**: Up to 25 pts (Phase 11 facility accessibility disruption)
- **Route Exposure**: Up to 20 pts (Phase 10 route disruption; double-counting control excludes duplicate facility route overlap)
- **Terrain & Drainage Context**: Up to 15 pts (Phase 4 flow accumulation & Phase 5 network context)
- **Evidence Completeness**: -10 to +10 pts adjustment based on source verification status (unverified/synthetic penalty down to -10, verified bonus up to +10)

---

## Temporal Semantics

Evaluated across the 7 canonical Digital Twin time slices: **0, 30, 60, 90, 120, 150, 180 minutes**.
Provides metrics:
- `first_threat_minutes`
- `first_high_severity_minutes`
- `peak_severity`
- `peak_severity_minutes`

---

## API Endpoints

- `POST /api/v1/protect-city/analyze`
- `GET /api/v1/protect-city/runs`
- `GET /api/v1/protect-city/runs/latest`
- `GET /api/v1/protect-city/runs/{run_id}`
- `GET /api/v1/protect-city/runs/{run_id}/recommendations`
- `GET /api/v1/protect-city/runs/{run_id}/recommendations/{candidate_id}`
- `GET /api/v1/protect-city/candidates`
- `GET /api/v1/protect-city/candidates/{candidate_id}`

---

## Verification & Isolation

- **Phase 7 Labels**: Zero raw training labels exposed.
- **Phase 8 ML**: Tagged `PROTOTYPE_ONLY`.
- **Database**: Migration `0010_phase12_protect_city.py` linked to `0009_phase11_critical_access`.
