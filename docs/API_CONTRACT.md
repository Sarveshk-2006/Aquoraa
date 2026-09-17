# Aquora API Contract Specification

> **Phase 1 Status**: Versioned API (`/api/v1/`), Liveness (`GET /api/v1/health/live`), Readiness (`GET /api/v1/health/ready`), `X-Request-ID` correlation middleware, and standardized error response payloads are fully implemented.

---

## 1. Health & Infrastructure APIs (Implemented in Phase 1)

### `GET /api/v1/health/live`
Determines if the FastAPI application process is running. Performs no external database or cache checks.

#### Response (200 OK)
```json
{
  "status": "ok"
}
```

---

### `GET /api/v1/health/ready`
Verifies PostgreSQL/PostGIS and Redis dependency connectivity.

#### Response (200 OK - Healthy)
```json
{
  "status": "ok",
  "services": {
    "database": "ok",
    "redis": "ok"
  }
}
```

#### Response (503 Service Unavailable - Degraded)
```json
{
  "status": "degraded",
  "services": {
    "database": "error",
    "redis": "ok"
  }
}
```

---

## 2. Request Correlation ID (`X-Request-ID`)

- All API requests accept an optional `X-Request-ID` header.
- If omitted, the backend generates a UUID4 request correlation ID.
- Every API response includes `X-Request-ID` in the response header and attaches it to server logs.

---

## 3. Standardized Error Response Contract

All application exceptions, HTTP errors, and validation errors return a uniform JSON format hiding internal stack traces:

```json
{
  "error": {
    "code": "ERROR_CODE",
    "message": "Human-readable description of the error.",
    "request_id": "a1b2c3d4-e5f6-7890-abcd-1234567890ab"
  }
}
```

Common Error Codes:
- `VALIDATION_ERROR` (HTTP 422)
- `NOT_FOUND` (HTTP 404)
- `BAD_REQUEST` (HTTP 400)
- `INTERNAL_SERVER_ERROR` (HTTP 500)

---

## 5. Protect the City APIs (Implemented in Phase 12)

> **Governance Disclaimer**: Protect the City provides modeled decision-support recommendations. It does not issue official municipal, emergency, evacuation, traffic-control, or engineering orders.

### `POST /api/v1/protect-city/analyze`
Executes spatial-temporal threat analysis on a Digital Twin run across 7 slices (0..180 min), scoring candidate priorities, temporal threat metrics, qualitative expected benefits, uncertainty, and cause-chain explanations.

#### Request Payload
```json
{
  "digital_twin_run_id": "dt_run_001",
  "routing_run_id": "rt_run_001",
  "critical_access_run_id": "ca_run_001",
  "minimum_priority": "LOW",
  "priority_limit": 30,
  "time_horizon_minutes": 180
}
```

#### Response (200 OK)
```json
{
  "run_id": "ptc_run_12345",
  "digital_twin_run_id": "dt_run_001",
  "total_candidates": 4,
  "recommendations": [
    {
      "candidate": {
        "candidate_id": "cand_mumbai_001",
        "name": "TEST INTERVENTION CANDIDATE A - DRAINAGE CLEARANCE",
        "candidate_type": "DRAINAGE_CLEARANCE",
        "verification_status": "SYNTHETIC"
      },
      "priority": "CRITICAL",
      "priority_score": 85.0,
      "priority_component_breakdown": {
        "flood_severity_score": 30.0,
        "time_to_threat_score": 25.0,
        "critical_access_score": 20.0,
        "route_impact_score": 10.0,
        "terrain_drainage_score": 5.0,
        "completeness_adjustment": -5.0
      },
      "intervention_type": "DRAINAGE_CLEARANCE",
      "first_threat_minutes": 30,
      "first_high_severity_minutes": 60,
      "peak_severity": "HIGH",
      "peak_severity_minutes": 90,
      "expected_benefit": "HIGH",
      "feasibility_status": "UNKNOWN",
      "uncertainty_status": "MEDIUM",
      "explanation": "PREDICTION: Modeled flood severity reaches HIGH (+60 min)...",
      "governance_disclaimer": "Protect the City provides modeled decision-support recommendations. It does not issue official municipal, emergency, evacuation, traffic-control, or engineering orders."
    }
  ]
}
```

### `GET /api/v1/protect-city/runs`
Lists historical Protect the City decision support analysis runs.

### `GET /api/v1/protect-city/runs/latest`
Retrieves the latest completed Protect the City decision support analysis run.

### `GET /api/v1/protect-city/runs/{run_id}`
Retrieves detailed audit metadata for a specific run.

### `GET /api/v1/protect-city/runs/{run_id}/recommendations`
Retrieves all recommendation records associated with a run.

### `GET /api/v1/protect-city/runs/{run_id}/recommendations/{candidate_id}`
Retrieves specific recommendation detail for a candidate within a run (validates candidate-run ownership).

### `GET /api/v1/protect-city/candidates`
Lists available intervention candidates from local GeoJSON or synthetic providers.

---

## 6. Planned Endpoint Groups (Phase 13+)

- `POST /api/v1/ground-truth/report` - Citizen ground observation submission.
- `POST /api/v1/simulator/runs` - Storm scenario execution.

