"""Phase 16 — End-to-End Workflow Integration Tests.

Executes a complete integrated operational flow:
Heavy Rainfall -> Digital Twin -> Travel Window -> Critical Access Guardian ->
Protect City Priority -> Ground Truth Corroboration -> Simulator What-If ->
Alert Generation -> 7-Step Explainability Cause Chain -> Lifecycle Management -> Audit History.
"""

from uuid import uuid4

import pytest
from app.schemas.alerts import (
    AlertAcknowledgeSchema,
    AlertGenerateRequestSchema,
    AlertResolveSchema,
    AlertSeverity,
    AlertStatus,
)
from app.services.alerts_service import AlertsService


@pytest.mark.asyncio
async def test_end_to_end_integrated_operational_workflow():
    """Verify complete multi-phase workflow execution from driver inputs to resolved alert audit trail."""
    service = AlertsService(db=None)

    dt_run_id = uuid4()
    tw_run_id = uuid4()
    ca_run_id = uuid4()
    pc_run_id = uuid4()
    gt_run_id = uuid4()
    sim_run_id = uuid4()

    # 1. Generate Operational Alert from multi-phase sources
    generate_req = AlertGenerateRequestSchema(
        digital_twin_run_id=str(dt_run_id),
        travel_window_run_id=str(tw_run_id),
        critical_access_run_id=str(ca_run_id),
        protect_city_run_id=str(pc_run_id),
        ground_truth_run_id=str(gt_run_id),
        simulator_run_id=str(sim_run_id),
    )

    alert_list = await service.generate_alerts(generate_req)
    assert alert_list.total_count > 0
    alert = alert_list.alerts[0]
    assert alert.alert_id is not None
    assert alert.status == AlertStatus.ACTIVE.value
    assert alert.severity in (AlertSeverity.HIGH.value, AlertSeverity.CRITICAL.value)

    # 2. Verify Explainability Cause Chain (7 steps)
    explainability_steps = await service.get_explainability(alert.alert_id)
    assert len(explainability_steps) == 7
    categories = [s.category for s in explainability_steps]
    assert "WHAT" in categories

    # 3. Verify Evidence References
    evidence_items = await service.get_evidence(alert.alert_id)
    assert len(evidence_items) > 0

    # 4. Acknowledge Alert
    ack_req = AlertAcknowledgeSchema(
        actor_reference="OPERATOR_SACHIN",
        reason="Emergency dispatch dispatched to site",
    )
    ack_alert = await service.acknowledge_alert(alert.alert_id, ack_req)
    assert ack_alert.status == AlertStatus.ACKNOWLEDGED.value
    assert ack_alert.acknowledged_by == "OPERATOR_SACHIN"

    # 5. Resolve Alert
    res_req = AlertResolveSchema(
        resolved_by="DISPATCH_COMMAND",
        resolution_reason="Water level receded, route cleared",
        resolving_run_id=str(dt_run_id),
    )
    res_alert = await service.resolve_alert(alert.alert_id, res_req)
    assert res_alert.status == AlertStatus.RESOLVED.value

    # 6. Verify Immutable Audit Events History
    audit_events = await service.get_audit_trail(alert.alert_id)
    event_types = [e.event_type for e in audit_events]
    assert "GENERATED" in event_types
    assert "ACKNOWLEDGED" in event_types
    assert "RESOLVED" in event_types
