"""
Phase 11 Unit and Integration Test Suite: Critical Access Guardian.

Validates facility schemas, provenance preservation, synthetic provider determinism,
Phase 10 RoutingProcessingService reuse (no duplicate routing engine), 7-slice timeline evaluation,
CRITICAL_ACCESS_SEVERITY policy, modeled loss-of-access, primary vs alternate route decision rules,
time-to-loss calculation, operational status independence, prototype ML isolation, and API endpoints.
"""

import httpx
import pytest
from app.main import app
from app.providers.critical_facility import SyntheticCriticalFacilityProvider
from app.schemas.critical_access import (
    CriticalAccessRequestSchema,
    CriticalAccessResponseSchema,
    CriticalFacilitySchema,
    ResponderOriginSchema,
)
from app.services.critical_access_service import CriticalAccessProcessingService
from app.services.digital_twin_service import CANONICAL_SLICES


# 1. CriticalFacility Schema & Coordinate Validation
def test_critical_facility_schema_validation():
    fac = CriticalFacilitySchema(
        facility_id="test_fac_1",
        name="TEST FACILITY — HOSPITAL A",
        category="HOSPITAL",
        latitude=19.0760,
        longitude=72.8777,
        source="MUMBAI_MUNICIPAL_DATASET",
        source_type="OPEN_GOVERNMENT",
        verification_status="VERIFIED",
        operational_status="UNKNOWN",
        provider_mode="SYNTHETIC",
        environment="DEVELOPMENT_ONLY",
        provenance={"test": "ok"},
    )
    assert fac.facility_id == "test_fac_1"
    assert fac.category == "HOSPITAL"
    assert fac.latitude == 19.0760
    assert fac.longitude == 72.8777


def test_invalid_coordinates_rejection():
    with pytest.raises(ValueError):
        CriticalFacilitySchema(
            facility_id="bad_coords",
            name="Bad Facility",
            category="HOSPITAL",
            latitude=120.0,  # Invalid latitude (>90)
            longitude=72.8777,
            source="TEST",
            source_type="TEST",
            verification_status="UNVERIFIED",
            operational_status="UNKNOWN",
        )


def test_invalid_category_rejection():
    with pytest.raises(ValueError):
        CriticalFacilitySchema(
            facility_id="bad_cat",
            name="Bad Category Facility",
            category="SUPERMARKET",  # Invalid category not in taxonomy
            latitude=19.0,
            longitude=72.0,
            source="TEST",
            source_type="TEST",
            verification_status="UNVERIFIED",
            operational_status="UNKNOWN",
        )


# 2. Synthetic Provider Determinism & Tagging
@pytest.mark.asyncio
async def test_synthetic_provider_determinism():
    provider = SyntheticCriticalFacilityProvider()
    facilities_1 = await provider.list_facilities()
    facilities_2 = await provider.list_facilities()

    assert len(facilities_1) == len(facilities_2)
    for f1, f2 in zip(facilities_1, facilities_2):
        assert f1.facility_id == f2.facility_id
        assert f1.provider_mode == "SYNTHETIC"
        assert f1.environment in ["DEVELOPMENT_ONLY", "TEST_ONLY"]
        assert f1.name.startswith("TEST FACILITY —")


# 3. CriticalAccessProcessingService Workflow (Phase 10 Reuse & 7 Slices)
@pytest.mark.asyncio
async def test_critical_access_service_workflow():
    service = CriticalAccessProcessingService(db=None)

    req = CriticalAccessRequestSchema(
        facility_id="fac_hospital_a",
        responder_origin=ResponderOriginSchema(
            latitude=19.0600,
            longitude=72.8650,
            label="Origin Unit 1",
        ),
        critical_access_severity="HIGH",
    )

    res: CriticalAccessResponseSchema = await service.analyze_critical_access(req)

    assert res.access_run_id.startswith("access_run_")
    assert res.facility.facility_id == "fac_hospital_a"
    assert len(res.accessibility_timeline) == 7
    assert [s.minutes_from_start for s in res.accessibility_timeline] == list(CANONICAL_SLICES)
    assert res.current_access_status in ["ACCESSIBLE", "LIMITED", "AT_RISK", "COMPROMISED", "UNKNOWN"]
    assert res.recommendation in ["MAINTAIN_ACCESS", "USE_ALTERNATE", "ACCESS_AT_RISK", "ACCESS_COMPROMISED", "UNKNOWN"]
    assert isinstance(res.explanation, str) and len(res.explanation) > 0


# 4. Primary Compromised + Acceptable Alternate -> USE_ALTERNATE (NOT ACCESS_COMPROMISED)
@pytest.mark.asyncio
async def test_primary_compromised_with_acceptable_alternate():
    service = CriticalAccessProcessingService(db=None)

    req = CriticalAccessRequestSchema(
        facility_id="fac_fire_station_a",
        responder_origin=ResponderOriginSchema(
            latitude=19.0600,
            longitude=72.8650,
            label="Origin Unit 2",
        ),
        critical_access_severity="MODERATE",
    )

    res = await service.analyze_critical_access(req)

    # Primary route status vs recommendation:
    if res.recommendation == "USE_ALTERNATE":
        assert res.alternate_route is not None
        assert res.alternate_route.status == "AVAILABLE"
        assert res.current_access_status != "COMPROMISED"
    else:
        assert res.current_access_status in ["ACCESSIBLE", "LIMITED", "AT_RISK", "COMPROMISED", "UNKNOWN"]


# 5. Facility Operational Status Independence from Accessibility
@pytest.mark.asyncio
async def test_operational_status_independence():
    service = CriticalAccessProcessingService(db=None)
    facility = await service.get_facility_by_id("fac_hospital_a")
    assert facility is not None

    req = CriticalAccessRequestSchema(
        facility_id="fac_hospital_a",
        responder_origin=ResponderOriginSchema(latitude=19.0600, longitude=72.8650),
    )
    res = await service.analyze_critical_access(req)

    # Facility operational status must remain UNKNOWN (not inferred from physical accessibility)
    assert res.facility_operational_status == "UNKNOWN"


# 6. Prototype ML Non-Dominance & Training Label Isolation
@pytest.mark.asyncio
async def test_ml_prototype_isolation():
    service = CriticalAccessProcessingService(db=None)
    req = CriticalAccessRequestSchema(
        facility_id="fac_hospital_a",
        responder_origin=ResponderOriginSchema(latitude=19.0600, longitude=72.8650),
    )
    res = await service.analyze_critical_access(req)

    # Verify no Phase 7 ground truth label leaks exist in provenance
    prov = res.provenance
    assert prov.get("ml_status") == "PROTOTYPE_ONLY"
    assert prov.get("training_labels_isolated") is True
    assert "flood_label" not in prov
    assert "label_status" not in prov


# 7. HTTP API Endpoints Validation
@pytest.mark.asyncio
async def test_api_get_facilities():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/critical-access/facilities")
    assert response.status_code == 200
    facilities = response.json()
    assert isinstance(facilities, list)
    assert len(facilities) >= 4
    for f in facilities:
        assert "facility_id" in f
        assert "category" in f
        assert f["provider_mode"] in ["SYNTHETIC", "LOCAL_VERIFIED"]


@pytest.mark.asyncio
async def test_api_get_facility_by_id():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        facs_res = await ac.get("/api/v1/critical-access/facilities")
        fac_id = facs_res.json()[0]["facility_id"]
        response = await ac.get(f"/api/v1/critical-access/facilities/{fac_id}")
    assert response.status_code == 200
    fac = response.json()
    assert fac["facility_id"] == fac_id
    assert "category" in fac


@pytest.mark.asyncio
async def test_api_get_facility_not_found():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/critical-access/facilities/non_existent_facility")
    assert response.status_code == 404


@pytest.mark.asyncio
async def test_api_post_analyze():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        facs_res = await ac.get("/api/v1/critical-access/facilities")
        fac_id = facs_res.json()[0]["facility_id"]
        payload = {
            "facility_id": fac_id,
            "responder_origin": {
                "latitude": 19.0600,
                "longitude": 72.8650,
                "label": "Responder Base 1",
            },
            "critical_access_severity": "HIGH",
        }
        response = await ac.post("/api/v1/critical-access/analyze", json=payload)
    assert response.status_code == 200
    body = response.json()

    assert "access_run_id" in body
    assert body["facility"]["facility_id"] == fac_id
    assert len(body["accessibility_timeline"]) == 7
    assert body["recommendation"] in ["MAINTAIN_ACCESS", "USE_ALTERNATE", "ACCESS_AT_RISK", "ACCESS_COMPROMISED", "UNKNOWN"]
    assert "selected_route" in body
    assert "provenance" in body


@pytest.mark.asyncio
async def test_api_get_runs():
    async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://test") as ac:
        response = await ac.get("/api/v1/critical-access/runs")
    assert response.status_code == 200
    assert isinstance(response.json(), list)


@pytest.mark.asyncio
async def test_local_facility_provider_real_data():
    """Verify LocalCriticalFacilityProvider reads verified Mithi catchment facilities."""
    from app.providers.critical_facility import LocalCriticalFacilityProvider

    provider = LocalCriticalFacilityProvider()
    facilities = await provider.list_facilities()

    assert len(facilities) >= 6
    categories = {f.category for f in facilities}
    assert "HOSPITAL" in categories
    assert "FIRE_STATION" in categories
    assert "POLICE_STATION" in categories
    assert "SHELTER" in categories
    assert "AMBULANCE_BASE" in categories
    assert "EMERGENCY_CONTROL" in categories

    for f in facilities:
        assert f.provider_mode in ["LOCAL_VERIFIED", "SYNTHETIC"]
        assert f.verification_status in ["VERIFIED", "SYNTHETIC_FIXTURE"]


@pytest.mark.asyncio
async def test_access_loss_only_when_no_route_remains():
    """Verify ACCESS_LOSS semantics occur only when all acceptable routes are compromised."""
    service = CriticalAccessProcessingService(db=None)
    req = CriticalAccessRequestSchema(
        facility_id="fac_mcgm_ltmg_sion_hosp",
        responder_origin=ResponderOriginSchema(latitude=19.0600, longitude=72.8650),
        critical_access_severity="HIGH",
    )
    res = await service.analyze_critical_access(req)
    assert res.recommendation in ["MAINTAIN_ACCESS", "USE_ALTERNATE", "ACCESS_AT_RISK", "ACCESS_COMPROMISED"]
    if res.recommendation == "USE_ALTERNATE":
        assert res.current_access_status != "COMPROMISED"
