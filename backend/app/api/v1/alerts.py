"""
Phase 15 Alerts, Explainability, and Audit API Endpoints for Aquora.
"""

from typing import Any

from fastapi import APIRouter, Depends, HTTPException, Query, status
from sqlalchemy.ext.asyncio import AsyncSession

from app.db.session import get_db
from app.schemas.alerts import (
    AlertAcknowledgeSchema,
    AlertAuditEventResponseSchema,
    AlertEvidenceResponseSchema,
    AlertGenerateRequestSchema,
    AlertListResponseSchema,
    AlertProvenanceResponseSchema,
    AlertResolveSchema,
    AlertResponseSchema,
    AlertSeverity,
    AlertStatus,
    AlertSuppressSchema,
    AlertType,
    ExplainabilityStepResponseSchema,
)
from app.services.alerts_service import AlertsService

router = APIRouter(prefix="/alerts", tags=["Alerts & Explainability"])


@router.get("", response_model=AlertListResponseSchema, summary="List Active & Historical Operational Alerts")
async def list_alerts(
    status_filter: AlertStatus | None = Query(None, alias="status", description="Filter by alert status"),  # noqa: B008
    severity_filter: AlertSeverity | None = Query(None, alias="severity", description="Filter by operational severity"),  # noqa: B008
    type_filter: AlertType | None = Query(None, alias="alert_type", description="Filter by alert type taxonomy"),  # noqa: B008
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> AlertListResponseSchema:
    """Fetch operational alerts with optional status, severity, and type filters."""
    service = AlertsService(db=db)
    return await service.list_alerts(
        status=status_filter, severity=severity_filter, alert_type=type_filter
    )


@router.get("/configuration", response_model=dict[str, Any], summary="Read Active Operational Alert Configuration")
async def get_configuration(db: AsyncSession = Depends(get_db)) -> dict[str, Any]:  # noqa: B008
    """Fetch active operational alert thresholds and lookahead configuration."""
    service = AlertsService(db=db)
    return await service.get_configuration()


@router.post("/configuration/validate", response_model=dict[str, Any], summary="Validate Operational Alert Configuration Payload")
async def validate_configuration(
    payload: dict[str, Any],
) -> dict[str, Any]:
    """Validate alert configuration thresholds for numeric finitude, positivity, and safe bounds."""
    thresholds = payload.get("thresholds", {})
    warnings: list[str] = []

    for k, v in thresholds.items():
        if isinstance(v, (int, float)) and v < 0:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST,
                detail=f"Configuration threshold '{k}' must be non-negative, got {v}"
            )

    return {
        "is_valid": True,
        "configuration_version": payload.get("configuration_version", "v1"),
        "warnings": warnings,
    }


@router.post("/generate", response_model=AlertListResponseSchema, status_code=status.HTTP_201_CREATED, summary="Idempotent Alert Generation from Authoritative Run IDs")
async def generate_alerts(
    payload: AlertGenerateRequestSchema,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> AlertListResponseSchema:
    """Generate or update continuing operational alerts from authoritative Phase 9-14 run IDs."""
    service = AlertsService(db=db)
    try:
        return await service.generate_alerts(payload)
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err


@router.get("/{alert_id}", response_model=AlertResponseSchema, summary="Get Operational Alert Detail")
async def get_alert(
    alert_id: str,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> AlertResponseSchema:
    """Fetch complete detail record for a specific alert."""
    service = AlertsService(db=db)
    try:
        return await service.get_alert(alert_id)
    except KeyError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


@router.post("/{alert_id}/acknowledge", response_model=AlertResponseSchema, summary="Acknowledge Operational Alert")
async def acknowledge_alert(
    alert_id: str,
    payload: AlertAcknowledgeSchema,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> AlertResponseSchema:
    """Transition alert to ACKNOWLEDGED status with audit trail event."""
    service = AlertsService(db=db)
    try:
        return await service.acknowledge_alert(alert_id, payload)
    except KeyError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
    except ValueError as err:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail=str(err)) from err


@router.post("/{alert_id}/resolve", response_model=AlertResponseSchema, summary="Resolve Operational Alert")
async def resolve_alert(
    alert_id: str,
    payload: AlertResolveSchema,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> AlertResponseSchema:
    """Transition alert to RESOLVED status with mandatory resolution rationale and audit trail event."""
    service = AlertsService(db=db)
    try:
        return await service.resolve_alert(alert_id, payload)
    except KeyError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


@router.post("/{alert_id}/suppress", response_model=AlertResponseSchema, summary="Suppress Operational Alert")
async def suppress_alert(
    alert_id: str,
    payload: AlertSuppressSchema,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> AlertResponseSchema:
    """Transition alert to SUPPRESSED status with mandatory rationale and audit trail event."""
    service = AlertsService(db=db)
    try:
        return await service.suppress_alert(alert_id, payload)
    except KeyError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


@router.get("/{alert_id}/evidence", response_model=list[AlertEvidenceResponseSchema], summary="Get Alert Evidence References")
async def get_alert_evidence(
    alert_id: str,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> list[AlertEvidenceResponseSchema]:
    """Fetch compact evidence references and metrics supporting an alert."""
    service = AlertsService(db=db)
    try:
        return await service.get_evidence(alert_id)
    except KeyError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


@router.get("/{alert_id}/explainability", response_model=list[ExplainabilityStepResponseSchema], summary="Get Alert Cause-Chain Explainability Steps")
async def get_alert_explainability(
    alert_id: str,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> list[ExplainabilityStepResponseSchema]:
    """Fetch structured cause-chain explainability steps (WHAT, WHY, WHEN, WHERE, HOW_CERTAIN, WHAT_SHOULD_I_DO, EVIDENCE)."""
    service = AlertsService(db=db)
    try:
        return await service.get_explainability(alert_id)
    except KeyError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


@router.get("/{alert_id}/audit", response_model=list[AlertAuditEventResponseSchema], summary="Get Alert Lifecycle Audit Trail")
async def get_alert_audit(
    alert_id: str,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> list[AlertAuditEventResponseSchema]:
    """Fetch immutable lifecycle audit event history for an alert."""
    service = AlertsService(db=db)
    try:
        return await service.get_audit_trail(alert_id)
    except KeyError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err


@router.get("/{alert_id}/provenance", response_model=AlertProvenanceResponseSchema, summary="Get Alert Provenance Chain")
async def get_alert_provenance(
    alert_id: str,
    db: AsyncSession = Depends(get_db),  # noqa: B008
) -> AlertProvenanceResponseSchema:
    """Fetch cryptographic provenance hash and source configuration chain for an alert."""
    service = AlertsService(db=db)
    try:
        return await service.get_provenance(alert_id)
    except KeyError as err:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail=str(err)) from err
