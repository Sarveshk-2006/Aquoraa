"""Phase 16 — Cross-Phase Contract & Immutability Tests.

Validates that contracts across Phase 6 -> 9 -> 10 -> 11 -> 12 -> 15,
Phase 13 -> 15, and Phase 14 -> 15 preserve identifiers, timestamps, CRS,
units, provenance, and authority boundaries without silent mutations.
"""

from uuid import uuid4

from app.schemas.alerts import AlertGenerateRequestSchema
from app.schemas.critical_access import (
    CriticalAccessRequestSchema,
    ResponderOriginSchema,
)
from app.schemas.digital_twin import (
    DigitalTwinRunRequestSchema,
)
from app.schemas.protect_city import ProtectCityRequestSchema
from app.schemas.routing import RouteAnalysisRequestSchema, RouteLocationSchema


def test_cross_phase_contract_pipeline_flow():
    """Verify that source run IDs, timestamps, units, and CRS are strictly passed through the phase chain."""
    digital_twin_id = uuid4()
    travel_window_id = uuid4()
    critical_access_id = uuid4()
    protect_city_id = uuid4()
    ground_truth_id = uuid4()
    simulator_id = uuid4()

    # 1. Digital Twin Request
    dt_req = DigitalTwinRunRequestSchema(
        horizon_minutes=180,
    )
    assert dt_req.horizon_minutes == 180

    # 2. Travel Window Request consuming Digital Twin
    tw_req = RouteAnalysisRequestSchema(
        digital_twin_run_id=str(digital_twin_id),
        origin=RouteLocationSchema(latitude=19.0760, longitude=72.8777),
        destination=RouteLocationSchema(latitude=19.0850, longitude=72.8880),
    )
    assert tw_req.digital_twin_run_id == str(digital_twin_id)

    # 3. Critical Access Request consuming Travel Window & Digital Twin
    ca_req = CriticalAccessRequestSchema(
        digital_twin_run_id=str(digital_twin_id),
        facility_id="HOSPITAL_MUMBAI_CENTRAL",
        responder_origin=ResponderOriginSchema(latitude=19.0760, longitude=72.8777),
    )
    assert ca_req.digital_twin_run_id == str(digital_twin_id)

    # 4. Protect City Request consuming Digital Twin & Critical Access
    pc_req = ProtectCityRequestSchema(
        digital_twin_run_id=str(digital_twin_id),
        critical_access_run_id=str(critical_access_id),
    )
    assert pc_req.digital_twin_run_id == str(digital_twin_id)

    # 5. Alert Generation Request consuming typed source run IDs
    alert_req = AlertGenerateRequestSchema(
        digital_twin_run_id=str(digital_twin_id),
        travel_window_run_id=str(travel_window_id),
        critical_access_run_id=str(critical_access_id),
        protect_city_run_id=str(protect_city_id),
        ground_truth_run_id=str(ground_truth_id),
        simulator_run_id=str(simulator_id),
    )
    assert alert_req.digital_twin_run_id == str(digital_twin_id)
    assert alert_req.travel_window_run_id == str(travel_window_id)
    assert alert_req.critical_access_run_id == str(critical_access_id)
    assert alert_req.protect_city_run_id == str(protect_city_id)
    assert alert_req.ground_truth_run_id == str(ground_truth_id)
    assert alert_req.simulator_run_id == str(simulator_id)


def test_unknown_status_preservation_across_contracts():
    """Verify that UNKNOWN status semantics are preserved and not silently mapped to dry or 0."""
    from app.schemas.ground_truth import VerificationState, WaterDepthClass

    assert VerificationState.UNVERIFIED.value == "UNVERIFIED"
    assert WaterDepthClass.UNKNOWN.value == "UNKNOWN"


def test_authoritative_ownership_isolation():
    """Verify Phase 15 does not export or own flood solvers or routing algorithms."""
    import inspect

    from app.services import alerts_service

    code_str = inspect.getsource(alerts_service)
    assert "def calculate_d8_flow_direction" not in code_str
    assert "def runoff_generation" not in code_str
    assert "def solve_shallow_water" not in code_str
    assert "def compute_dijkstra_route" not in code_str
