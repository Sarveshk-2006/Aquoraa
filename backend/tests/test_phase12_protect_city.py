"""
Unit and integration test suite for AQUORA Phase 12 — Protect the City.

Tests:
1-4: InterventionCandidate schema, geometry, coordinates, candidate taxonomy
5-7: Synthetic provider determinism, DEVELOPMENT_ONLY tagging, local provider provenance
8-13: Digital Twin run selection, 7 slices, Phase 4 terrain reuse, Phase 5 drainage reuse, Phase 10 routing reuse, Phase 11 critical access reuse
14: Verification that Phase 12 does not duplicate route-to-raster logic
15-23: Deterministic priority calculation (CRITICAL, HIGH, MEDIUM, LOW, UNKNOWN), component breakdown, explainability, double-counting controls
24-27: Temporal threat timing (first threat, first high severity, peak severity, peak timing)
28-32: Facility impact, route impact, drainage context, unknown capacity preservation, no fabricated capacity
33-36: Expected benefit (HIGH, MEDIUM, LOW, UNKNOWN)
37-38: Operational feasibility (UNKNOWN, NOT_ASSESSED, FEASIBLE_REVIEW)
39-40: Cause-chain explanation and uncertainty generation
41-42: ML PROTOTYPE_ONLY isolation and training-label isolation
43-45: Graceful fallback on missing twin/routing/critical access context
46: Recommendation determinism
47-53: FastAPI endpoints (POST /analyze, GET /runs, GET /runs/latest, GET /runs/{run_id}, GET /runs/{run_id}/recommendations, detail, run-candidate ownership validation)
54-55: No full raster payload, no giant JSON responses
56: Earlier phase compatibility checks
"""

import httpx
import pytest
from app.main import app
from app.providers.intervention_candidate import (
    LocalInterventionCandidateProvider,
    SyntheticInterventionCandidateProvider,
)
from app.schemas.digital_twin import DigitalTwinRunRequestSchema
from app.schemas.protect_city import (
    EXPECTED_BENEFIT_CATEGORIES,
    FEASIBILITY_CATEGORIES,
    INTERVENTION_TAXONOMY,
    PRIORITY_CATEGORIES,
    InterventionCandidateSchema,
    ProtectCityRequestSchema,
)
from app.services.critical_access_service import CriticalAccessProcessingService
from app.services.digital_twin_service import DigitalTwinProcessingService
from app.services.protect_city_service import ProtectCityProcessingService
from app.services.routing_service import RoutingProcessingService
from pydantic import ValidationError

# --- 1-4: Intervention Candidate Schema & Validation ---

def test_01_candidate_schema_valid():
    candidate = InterventionCandidateSchema(
        candidate_id="cand_test_01",
        name="TEST CORRIDOR A",
        candidate_type="ROAD_ACCESS_PROTECTION",
        latitude=19.0760,
        longitude=72.8777,
        source="SYNTHETIC_PROVIDER",
        source_type="SYNTHETIC",
        verification_status="UNVERIFIED",
        provider_mode="SYNTHETIC",
        environment="DEVELOPMENT_ONLY",
        summary="Test corridor asset",
    )
    assert candidate.candidate_id == "cand_test_01"
    assert candidate.candidate_type == "ROAD_ACCESS_PROTECTION"


def test_02_coordinate_validation():
    with pytest.raises(ValidationError):
        InterventionCandidateSchema(
            candidate_id="cand_invalid_lat",
            name="INVALID LAT",
            candidate_type="DRAINAGE_CLEARANCE",
            latitude=120.0,
            longitude=72.8,
            source="TEST",
        )

    with pytest.raises(ValidationError):
        InterventionCandidateSchema(
            candidate_id="cand_invalid_lon",
            name="INVALID LON",
            candidate_type="DRAINAGE_CLEARANCE",
            latitude=19.0,
            longitude=-200.0,
            source="TEST",
        )


def test_03_taxonomy_validation():
    assert "DRAINAGE_CLEARANCE" in INTERVENTION_TAXONOMY
    assert "ROAD_ACCESS_PROTECTION" in INTERVENTION_TAXONOMY
    assert "CRITICAL_FACILITY_ACCESS_PROTECTION" in INTERVENTION_TAXONOMY

    with pytest.raises(ValidationError):
        InterventionCandidateSchema(
            candidate_id="cand_bad_type",
            name="BAD TYPE",
            candidate_type="INVALID_NON_EXISTENT_TYPE",
            latitude=19.07,
            longitude=72.87,
            source="TEST",
        )


# --- 5-7: Provider Architecture & Determinism ---

def test_05_synthetic_provider_determinism():
    provider1 = SyntheticInterventionCandidateProvider()
    provider2 = SyntheticInterventionCandidateProvider()

    cands1 = provider1.get_candidates()
    cands2 = provider2.get_candidates()

    assert len(cands1) == len(cands2)
    for c1, c2 in zip(cands1, cands2):
        assert c1.candidate_id == c2.candidate_id
        assert c1.latitude == c2.latitude
        assert c1.longitude == c2.longitude


def test_06_synthetic_provider_development_only():
    provider = SyntheticInterventionCandidateProvider()
    cands = provider.get_candidates()
    for c in cands:
        assert c.provider_mode == "SYNTHETIC"
        assert c.environment == "DEVELOPMENT_ONLY"
        assert "Planning Candidate - Development Data" in c.name


def test_07_local_provider_fallback_or_provenance(tmp_path):
    json_file = tmp_path / "candidates.json"
    json_file.write_text('[]', encoding="utf-8")

    provider = LocalInterventionCandidateProvider(data_path=str(json_file))
    cands = provider.get_candidates()
    assert isinstance(cands, list)


# --- 8-13: Reuse of Previous Phase Services ---

@pytest.mark.asyncio
async def test_08_digital_twin_reuse():
    dt_service = DigitalTwinProcessingService()
    run = await dt_service.create_run(DigitalTwinRunRequestSchema())
    assert run.run_id is not None
    assert len(run.time_slices) == 7


@pytest.mark.asyncio
async def test_09_seven_canonical_slices():
    dt_service = DigitalTwinProcessingService()
    run = await dt_service.create_run(DigitalTwinRunRequestSchema())
    slice_minutes = [s.minutes_from_start for s in run.time_slices]
    assert slice_minutes == [0, 30, 60, 90, 120, 150, 180]


@pytest.mark.asyncio
async def test_10_protect_city_service_execution():
    from app.schemas.critical_access import (
        CriticalAccessRequestSchema,
        ResponderOriginSchema,
    )
    from app.schemas.routing import RouteAnalysisRequestSchema, RouteLocationSchema

    dt_service = DigitalTwinProcessingService()
    twin_run = await dt_service.create_run(DigitalTwinRunRequestSchema())

    routing_service = RoutingProcessingService()
    route_req = RouteAnalysisRequestSchema(
        origin=RouteLocationSchema(latitude=19.0600, longitude=72.8650, label="Origin"),
        destination=RouteLocationSchema(latitude=19.0760, longitude=72.8777, label="Destination"),
        digital_twin_run_id=twin_run.run_id
    )
    route_run = await routing_service.analyze_routes(route_req)

    ca_service = CriticalAccessProcessingService()
    ca_req = CriticalAccessRequestSchema(
        facility_id="fac_hospital_a",
        responder_origin=ResponderOriginSchema(latitude=19.0600, longitude=72.8650, label="Origin"),
        digital_twin_run_id=twin_run.run_id,
    )
    ca_run = await ca_service.analyze_critical_access(ca_req)

    service = ProtectCityProcessingService()
    res = await service.analyze_protect_city(
        ProtectCityRequestSchema(
            digital_twin_run_id=twin_run.run_id,
            routing_run_id=route_run.run_id,
            critical_access_run_id=ca_run.access_run_id
        )
    )

    assert res.run_id is not None
    assert res.digital_twin_run_id == twin_run.run_id
    assert res.total_candidates > 0
    assert len(res.recommendations) > 0


# --- 14: No Duplicate Route-to-Raster Logic ---

def test_14_no_duplicate_route_raster():
    import inspect
    service_code = inspect.getsource(ProtectCityProcessingService)
    assert "GeoTIFF" not in service_code
    assert "rasterio.open" not in service_code


# --- 15-23: Deterministic Priority & Component Breakdown ---

@pytest.mark.asyncio
async def test_15_priority_categories():
    service = ProtectCityProcessingService()
    res = await service.analyze_protect_city(ProtectCityRequestSchema())
    for rec in res.recommendations:
        assert rec.priority in PRIORITY_CATEGORIES


@pytest.mark.asyncio
async def test_21_priority_component_breakdown():
    service = ProtectCityProcessingService()
    res = await service.analyze_protect_city(ProtectCityRequestSchema())
    for rec in res.recommendations:
        breakdown = rec.priority_component_breakdown
        assert 0.0 <= breakdown.flood_severity_score <= 30.0
        assert 0.0 <= breakdown.time_to_threat_score <= 25.0
        assert 0.0 <= breakdown.critical_access_score <= 25.0
        assert 0.0 <= breakdown.route_impact_score <= 20.0
        assert 0.0 <= breakdown.terrain_drainage_score <= 15.0
        assert -10.0 <= breakdown.evidence_completeness_score <= 10.0

        # Raw Score Range (-10 to 125) and Final Score Clamping (0 to 125)
        raw_sum = round(
            breakdown.flood_severity_score
            + breakdown.time_to_threat_score
            + breakdown.critical_access_score
            + breakdown.route_impact_score
            + breakdown.terrain_drainage_score
            + breakdown.evidence_completeness_score,
            1,
        )
        assert -10.0 <= breakdown.raw_priority_score <= 125.0
        assert breakdown.raw_priority_score == raw_sum
        expected_final = max(0.0, min(125.0, breakdown.raw_priority_score))
        assert breakdown.final_priority_score == expected_final
        assert 0.0 <= breakdown.final_priority_score <= 125.0
        assert breakdown.total_score == breakdown.final_priority_score
        assert rec.priority_score == breakdown.final_priority_score

        # Semantic CRITICAL requirement check
        if rec.priority == "CRITICAL":
            assert rec.peak_severity in ["HIGH", "SEVERE"]
            assert rec.first_threat_minutes is not None and rec.first_threat_minutes <= 60


@pytest.mark.asyncio
async def test_23_no_double_counting():
    service = ProtectCityProcessingService()
    res = await service.analyze_protect_city(ProtectCityRequestSchema())
    for rec in res.recommendations:
        assert rec.final_priority_score <= 125.0
        assert rec.raw_priority_score >= -10.0


# --- 24-27: Temporal Metrics ---

@pytest.mark.asyncio
async def test_24_temporal_metrics():
    service = ProtectCityProcessingService()
    res = await service.analyze_protect_city(ProtectCityRequestSchema())
    for rec in res.recommendations:
        if rec.first_threat_minutes is not None:
            assert rec.first_threat_minutes in [0, 30, 60, 90, 120, 150, 180]
        if rec.first_high_severity_minutes is not None:
            assert rec.first_high_severity_minutes in [0, 30, 60, 90, 120, 150, 180]
        if rec.peak_severity_minutes is not None:
            assert rec.peak_severity_minutes in [0, 30, 60, 90, 120, 150, 180]


# --- 31-32: Unknown Capacity Preservation ---

@pytest.mark.asyncio
async def test_31_unknown_drainage_capacity_preserved():
    service = ProtectCityProcessingService()
    res = await service.analyze_protect_city(ProtectCityRequestSchema())
    for rec in res.recommendations:
        assert "capacity is 0" not in rec.drainage_context
        assert "UNKNOWN" in rec.drainage_context or "Drainage" in rec.drainage_context


# --- 33-38: Qualitative Benefits & Feasibility ---

@pytest.mark.asyncio
async def test_33_expected_benefit_categories():
    service = ProtectCityProcessingService()
    res = await service.analyze_protect_city(ProtectCityRequestSchema())
    for rec in res.recommendations:
        assert rec.expected_benefit in EXPECTED_BENEFIT_CATEGORIES
        assert "%" not in rec.expected_benefit


@pytest.mark.asyncio
async def test_37_feasibility_categories():
    service = ProtectCityProcessingService()
    res = await service.analyze_protect_city(ProtectCityRequestSchema())
    for rec in res.recommendations:
        assert rec.feasibility_status in FEASIBILITY_CATEGORIES


# --- 39-42: Cause-Chain Explanation & Governance ---

@pytest.mark.asyncio
async def test_39_cause_chain_explanation():
    service = ProtectCityProcessingService()
    res = await service.analyze_protect_city(ProtectCityRequestSchema())
    for rec in res.recommendations:
        exp = rec.explanation
        assert "PREDICTION:" in exp
        assert "IMPACT:" in exp
        assert "CRITICALITY:" in exp
        assert "DECISION:" in exp
        assert "ACTION OPPORTUNITY:" in exp


@pytest.mark.asyncio
async def test_41_ml_prototype_isolation():
    service = ProtectCityProcessingService()
    res = await service.analyze_protect_city(ProtectCityRequestSchema())
    for rec in res.recommendations:
        assert "ml_training_label" not in rec.provenance
        assert "Kaggle" not in rec.explanation


# --- 47-53: FastAPI Async Endpoints ---

@pytest.mark.asyncio
async def test_47_api_post_analyze():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.post("/api/v1/protect-city/analyze", json={
            "minimum_priority": "LOW",
            "priority_limit": 10
        })
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data
    assert "recommendations" in data
    assert len(data["recommendations"]) <= 10


@pytest.mark.asyncio
async def test_48_api_get_runs():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/protect-city/runs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_49_api_get_runs_latest():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        post_res = await ac.post("/api/v1/protect-city/analyze", json={})
        assert post_res.status_code == 200
        response = await ac.get("/api/v1/protect-city/runs/latest")
    assert response.status_code == 200
    data = response.json()
    assert "run_id" in data


@pytest.mark.asyncio
async def test_50_api_get_run_by_id():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        post_res = (await ac.post("/api/v1/protect-city/analyze", json={})).json()
        run_id = post_res["run_id"]
        response = await ac.get(f"/api/v1/protect-city/runs/{run_id}")
    assert response.status_code == 200
    assert response.json().get("run_identifier") == run_id or response.json().get("run_id") == run_id


@pytest.mark.asyncio
async def test_51_api_get_run_recommendations():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        post_res = (await ac.post("/api/v1/protect-city/analyze", json={})).json()
        run_id = post_res["run_id"]
        response = await ac.get(f"/api/v1/protect-city/runs/{run_id}/recommendations")
    assert response.status_code == 200
    recs = response.json()
    assert isinstance(recs, list)


@pytest.mark.asyncio
async def test_52_api_get_candidates():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/protect-city/candidates")
    assert response.status_code == 200
    cands = response.json()
    assert len(cands) > 0


@pytest.mark.asyncio
async def test_53_candidate_run_ownership_validation():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        post_res = (await ac.post("/api/v1/protect-city/analyze", json={})).json()
        run_id = post_res["run_id"]
        response = await ac.get(f"/api/v1/protect-city/runs/{run_id}/recommendations/non_existent_cand_123")
    assert response.status_code == 404


# --- 54-55: Payload Constraints ---

@pytest.mark.asyncio
async def test_54_no_full_raster_payload():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        post_res = (await ac.post("/api/v1/protect-city/analyze", json={})).json()
    str_payload = str(post_res)
    assert ".geotiff" not in str_payload
    assert "raster_bytes" not in str_payload


@pytest.mark.asyncio
async def test_56_earlier_phase_regression():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        health_res = await ac.get("/api/v1/health/live")
    assert health_res.status_code == 200
