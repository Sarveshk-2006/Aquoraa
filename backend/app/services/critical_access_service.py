"""
Critical Access Guardian Service for Phase 11.

Evaluates critical facility accessibility as modeled flood hazard evolves across 7 canonical
Digital Twin time slices (0, 30, 60, 90, 120, 150, 180 min).

Integrates directly with Phase 10 RoutingProcessingService to analyze route candidate exposure,
determines facility accessibility timeline, calculates modeled loss-of-access, evaluates alternate
access routes, and provides explainable access recommendations.
"""

import uuid
from datetime import datetime, timezone
from typing import Any

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.core.config import settings
from app.core.logging import logger
from app.models.critical_access import (
    CriticalAccessResult,
    CriticalAccessRun,
    CriticalFacility,
)
from app.providers.critical_facility import (
    BaseCriticalFacilityProvider,
    get_critical_facility_provider,
)
from app.schemas.critical_access import (
    AlternateRouteSummarySchema,
    CriticalAccessRequestSchema,
    CriticalAccessResponseSchema,
    CriticalFacilitySchema,
    SliceAccessibilitySchema,
)
from app.schemas.routing import RouteAnalysisRequestSchema
from app.services.digital_twin_service import (
    CANONICAL_SLICES,
    DigitalTwinProcessingService,
)
from app.services.routing_service import SEVERITY_RANK, RoutingProcessingService


class CriticalAccessProcessingService:
    """
    Core Application Service for Phase 11 Critical Access Guardian.

    Evaluates whether responders can reach a target critical facility given
    evolving modeled flood hazards from Phase 9 Digital Twin rasters via Phase 10 routing contracts.
    """

    def __init__(self, db: AsyncSession | None = None) -> None:
        self.db = db
        self.facility_provider: BaseCriticalFacilityProvider = get_critical_facility_provider()

    async def get_facility_by_id(self, facility_id: str) -> CriticalFacilitySchema | None:
        """Fetch facility by ID from DB or provider."""
        # 1. Try DB first if available
        if self.db:
            try:
                stmt = select(CriticalFacility).where(CriticalFacility.facility_id == facility_id)
                res = await self.db.execute(stmt)
                facility_db = res.scalar_one_or_none()
                if facility_db:
                    return CriticalFacilitySchema(
                        facility_id=facility_db.facility_id,
                        name=facility_db.name,
                        category=facility_db.category,
                        latitude=facility_db.latitude,
                        longitude=facility_db.longitude,
                        source=facility_db.source,
                        source_id=facility_db.source_id,
                        source_type=facility_db.source_type,
                        verification_status=facility_db.verification_status,
                        operational_status=facility_db.operational_status,
                        provider_mode=facility_db.provider_mode,
                        environment=facility_db.environment,
                        provenance=facility_db.provenance or {},
                    )
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Database query for facility '{facility_id}' failed (offline/fallback): {e}")

        # 2. Fall back to provider
        raw_res = await self.facility_provider.get_facility(facility_id)
        if not raw_res:
            from app.providers.critical_facility import SyntheticCriticalFacilityProvider
            synth_prov = SyntheticCriticalFacilityProvider()
            raw_res = await synth_prov.get_facility(facility_id)

        if not raw_res:
            return None

        return CriticalFacilitySchema(
            facility_id=raw_res.facility_id,
            name=raw_res.name,
            category=raw_res.category,
            latitude=raw_res.latitude,
            longitude=raw_res.longitude,
            source=raw_res.source,
            source_id=raw_res.source_id,
            source_type=raw_res.source_type,
            verification_status=raw_res.verification_status,
            operational_status=raw_res.operational_status,
            provider_mode=raw_res.provider_mode,
            environment=getattr(raw_res, "environment", "DEVELOPMENT_ONLY"),
            summary=raw_res.summary,
            provenance=raw_res.provenance or {},
        )

    async def list_facilities(
        self,
        category: str | None = None,
        verification_status: str | None = None,
        bbox: list[float] | None = None,
    ) -> list[CriticalFacilitySchema]:
        """List critical facilities filtered by category, verification status, or bounding box."""
        if self.db:
            try:
                stmt = select(CriticalFacility)
                if category:
                    stmt = stmt.where(CriticalFacility.category == category.upper())
                if verification_status:
                    stmt = stmt.where(CriticalFacility.verification_status == verification_status.upper())
                res = await self.db.execute(stmt)
                facilities_db = res.scalars().all()
                if facilities_db:
                    schemas = []
                    for f in facilities_db:
                        if bbox and len(bbox) == 4:
                            min_lon, min_lat, max_lon, max_lat = bbox
                            if not (min_lon <= f.longitude <= max_lon and min_lat <= f.latitude <= max_lat):
                                continue
                        schemas.append(
                            CriticalFacilitySchema(
                                facility_id=f.facility_id,
                                name=f.name,
                                category=f.category,
                                latitude=f.latitude,
                                longitude=f.longitude,
                                source=f.source,
                                source_id=f.source_id,
                                source_type=f.source_type,
                                verification_status=f.verification_status,
                                operational_status=f.operational_status,
                                provider_mode=f.provider_mode,
                                environment=f.environment,
                                provenance=f.provenance or {},
                            )
                        )
                    if schemas:
                        return schemas
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Database list_facilities failed (offline/fallback): {e}")

        # Provider fallback
        raw_list = await self.facility_provider.list_facilities(
            category=category,
            verification_status=verification_status,
        )
        schemas = []
        for raw_res in raw_list:
            if bbox and len(bbox) == 4:
                min_lon, min_lat, max_lon, max_lat = bbox
                if not (min_lon <= raw_res.longitude <= max_lon and min_lat <= raw_res.latitude <= max_lat):
                    continue
            schemas.append(
                CriticalFacilitySchema(
                    facility_id=raw_res.facility_id,
                    name=raw_res.name,
                    category=raw_res.category,
                    latitude=raw_res.latitude,
                    longitude=raw_res.longitude,
                    source=raw_res.source,
                    source_id=raw_res.source_id,
                    source_type=raw_res.source_type,
                    verification_status=raw_res.verification_status,
                    operational_status=raw_res.operational_status,
                    provider_mode=raw_res.provider_mode,
                    environment=getattr(raw_res, "environment", "DEVELOPMENT_ONLY"),
                    summary=raw_res.summary,
                    provenance=raw_res.provenance or {},
                )
            )
        return schemas

    async def analyze_critical_access(
        self,
        request: CriticalAccessRequestSchema,
    ) -> CriticalAccessResponseSchema:
        """
        Main access guardian workflow:
        1. Resolve target facility
        2. Resolve Digital Twin run
        3. Invoke Phase 10 RoutingProcessingService (REUSE Phase 10)
        4. Apply Phase 11 access policy across 7 canonical slices
        5. Evaluate primary vs alternate routes
        6. Compute modeled loss-of-access & time-to-loss
        7. Generate causal explainability & recommendations
        8. Audit database persistence
        """
        now_utc = datetime.now(timezone.utc)
        run_id = f"access_run_{uuid.uuid4().hex[:12]}"

        # 1. Resolve Target Facility
        facility = await self.get_facility_by_id(request.facility_id)
        if not facility:
            raise ValueError(f"Target critical facility '{request.facility_id}' not found.")

        # 2. Resolve Digital Twin Run
        dt_service = DigitalTwinProcessingService(db=self.db)
        if request.digital_twin_run_id:
            dt_run_id = request.digital_twin_run_id
        else:
            try:
                latest_run = await dt_service.get_latest_run()
                dt_run_id = latest_run.run_id
            except Exception:  # noqa: BLE001
                dt_run_id = "dt_run_mithi_pilot_001"

        # 3. Policy parameters
        access_threshold = request.critical_access_severity or settings.CRITICAL_ACCESS_SEVERITY
        access_threshold_rank = SEVERITY_RANK.get(access_threshold, 3)

        # 4. Invoke Phase 10 Routing Processing Service (STRICT REUSE OF PHASE 10)
        routing_service = RoutingProcessingService(db=self.db)
        route_req = RouteAnalysisRequestSchema(
            origin=request.responder_origin.to_route_location(),
            destination=facility.to_route_location(),
            digital_twin_run_id=dt_run_id,
            departure_time=request.departure_time,
            max_acceptable_severity=access_threshold,
            max_alternatives=3,
        )
        route_response = await routing_service.analyze_routes(route_req)

        candidates = route_response.candidates
        if not candidates:
            raise RuntimeError(f"Phase 10 routing service returned zero route candidates for facility '{facility.facility_id}'.")

        primary_cand = candidates[0]
        alternate_cands = candidates[1:] if len(candidates) > 1 else []

        # 5. Evaluate Accessibility Timeline across 7 canonical slices (0..180 min)
        slice_evaluations: list[SliceAccessibilitySchema] = []
        loss_of_access_min: int | None = None

        for slice_min in CANONICAL_SLICES:
            # Check exposure of candidates at slice_min
            cand_slice_states: list[dict[str, Any]] = []

            for cand in candidates:
                # Find slice exposure matching slice_min
                slice_exp = next(
                    (exp for exp in cand.time_slice_exposures if exp.minutes_from_start == slice_min),
                    None,
                )
                if not slice_exp:
                    cand_slice_states.append({
                        "route_id": cand.route_id,
                        "state": "UNKNOWN",
                        "peak_severity": "UNKNOWN",
                    })
                    continue

                sev = slice_exp.peak_severity
                sev_rank = SEVERITY_RANK.get(sev, -1)

                if sev == "UNKNOWN":
                    c_state = "UNKNOWN"
                elif sev_rank < access_threshold_rank:
                    c_state = "ACCESSIBLE" if sev in ["DRY", "LOW"] else "LIMITED"
                elif sev == access_threshold:
                    c_state = "AT_RISK"
                else:
                    c_state = "COMPROMISED"

                cand_slice_states.append({
                    "route_id": cand.route_id,
                    "state": c_state,
                    "peak_severity": sev,
                    "summary": cand.summary,
                    "travel_window_usable": cand.travel_window.usable_travel_window_min,
                })

            primary_state_info = cand_slice_states[0]
            primary_state = primary_state_info["state"]

            # Determine if any candidate route is acceptable (state in [ACCESSIBLE, LIMITED, AT_RISK])
            acceptable_cands = [
                cs for cs in cand_slice_states if cs["state"] in ["ACCESSIBLE", "LIMITED", "AT_RISK"]
            ]
            acceptable_alternates = [
                cs for cs in cand_slice_states[1:] if cs["state"] in ["ACCESSIBLE", "LIMITED", "AT_RISK"]
            ]

            if not cand_slice_states or all(cs["state"] == "UNKNOWN" for cs in cand_slice_states):
                overall_slice_state = "UNKNOWN"
                eval_notes = "Insufficient flood/exposure information for this time slice."
            elif primary_state in ["ACCESSIBLE", "LIMITED"]:
                overall_slice_state = primary_state
                eval_notes = f"Primary route '{primary_cand.summary}' remains usable (Peak hazard: {primary_state_info['peak_severity']})."
            elif acceptable_alternates:
                overall_slice_state = acceptable_alternates[0]["state"]
                eval_notes = f"Primary route degraded ({primary_state_info['peak_severity']}). Alternate route '{acceptable_alternates[0]['summary']}' provides usable access."
            elif acceptable_cands:
                overall_slice_state = "AT_RISK"
                eval_notes = f"Access is at risk. Candidate routes encounter threshold hazard ({primary_state_info['peak_severity']})."
            else:
                overall_slice_state = "COMPROMISED"
                eval_notes = f"No acceptable route remains under configured access policy ({access_threshold})."

            slice_evaluations.append(
                SliceAccessibilitySchema(
                    minutes_from_start=slice_min,
                    accessibility_status=overall_slice_state,
                    primary_route_state=primary_state,
                    primary_route_peak_severity=primary_state_info["peak_severity"],
                    acceptable_alternate_available=len(acceptable_alternates) > 0,
                    evaluation_notes=eval_notes,
                )
            )

            # Record earliest loss-of-access (when NO acceptable route remains)
            if overall_slice_state == "COMPROMISED" and loss_of_access_min is None:
                loss_of_access_min = slice_min

        # 6. Current Access Status (at 0 min slice)
        current_slice_eval = slice_evaluations[0]
        current_access_status = current_slice_eval.accessibility_status

        # 7. Time-to-Loss Calculation
        if loss_of_access_min is not None:
            time_to_loss_min: int | None = loss_of_access_min
            loss_of_access_str: str | None = f"+{loss_of_access_min} min"
        else:
            time_to_loss_min = None
            loss_of_access_str = "NO_MODELED_LOSS_WITHIN_HORIZON"

        # 8. Alternate Route Selection & Evaluation
        alternate_summary: AlternateRouteSummarySchema | None = None
        if alternate_cands:
            # Rank alternates by: avoid HIGH/SEVERE, maximize travel window, minimize duration
            best_alt = alternate_cands[0]
            alt_status = "AVAILABLE"
            alt_usable_window = best_alt.travel_window.usable_travel_window_min
            alt_onset = best_alt.travel_window.route_flood_onset_min

            if current_slice_eval.primary_route_state in ["COMPROMISED", "AT_RISK"] and best_alt.travel_window.usable_travel_window_min > 0:
                alt_recommendation = "RECOMMENDED_ALTERNATE"
            else:
                alt_recommendation = "AVAILABLE_SECONDARY"

            alternate_summary = AlternateRouteSummarySchema(
                route_id=best_alt.route_id,
                summary=best_alt.summary,
                distance_m=best_alt.distance_m,
                estimated_duration_s=best_alt.estimated_duration_s,
                status=alt_status,
                usable_travel_window_min=alt_usable_window,
                route_flood_onset_min=alt_onset,
                recommendation_note=alt_recommendation,
                geometry_geojson=best_alt.geometry_geojson,
            )
        else:
            alternate_summary = AlternateRouteSummarySchema(
                route_id="none",
                summary="No alternate candidate route evaluated",
                distance_m=0.0,
                estimated_duration_s=0.0,
                status="ALTERNATE_UNAVAILABLE",
                usable_travel_window_min=0,
                route_flood_onset_min=None,
                recommendation_note="Single candidate route evaluated by routing provider.",
                geometry_geojson=None,
            )

        # 9. Recommendation & Causal Explanation Policy
        has_acceptable_alternate = current_slice_eval.acceptable_alternate_available
        primary_compromised = current_slice_eval.primary_route_state in ["COMPROMISED", "AT_RISK"]

        if current_access_status == "UNKNOWN":
            rec_str = "UNKNOWN"
            explanation_str = "Facility accessibility cannot be determined due to missing routing or Digital Twin flood data."
        elif not primary_compromised:
            rec_str = "MAINTAIN_ACCESS"
            explanation_str = (
                f"Primary access route '{primary_cand.summary}' is clear/acceptable. "
                f"Estimated travel time is {primary_cand.estimated_duration_s / 60.0:.1f} min. "
                f"Usable travel window before modeled flood hazard is ~{primary_cand.travel_window.usable_travel_window_min} min."
            )
        elif primary_compromised and has_acceptable_alternate:
            rec_str = "USE_ALTERNATE"
            alt_name = alternate_summary.summary if alternate_summary else "alternate route"
            explanation_str = (
                f"Primary route '{primary_cand.summary}' encounters modeled flood hazard ({current_slice_eval.primary_route_peak_severity}). "
                f"Recommended alternate route '{alt_name}' remains usable, maintaining critical facility access."
            )
        elif primary_compromised and not has_acceptable_alternate:
            if loss_of_access_min is not None and loss_of_access_min > 0:
                rec_str = "ACCESS_AT_RISK"
                explanation_str = (
                    f"Primary route encounters modeled flood hazard around +{primary_cand.travel_window.route_flood_onset_min or 60} min. "
                    f"No acceptable alternate route is available. Modeled loss of access occurs around +{loss_of_access_min} min."
                )
            else:
                rec_str = "ACCESS_COMPROMISED"
                explanation_str = (
                    f"All evaluated access routes exceed configured critical access severity threshold ({access_threshold}). "
                    f"No acceptable modeled route remains available for responder origin."
                )
        else:
            rec_str = "MAINTAIN_ACCESS"
            explanation_str = f"Facility accessibility evaluated as {current_access_status}."

        # 10. Warnings & Provenance Assembly
        warnings: list[str] = []
        if facility.provider_mode == "SYNTHETIC":
            warnings.append(f"Target facility '{facility.name}' is a SYNTHETIC DEVELOPMENT FIXTURE. Do not use for real emergency operations.")
        if route_response.provenance.get("provider_mode") == "SYNTHETIC":
            warnings.append("Routing provider is operating in SYNTHETIC mode. Route geometries and travel times are estimated.")
        if facility.operational_status == "UNKNOWN":
            warnings.append("Facility operational status is UNKNOWN (accessibility reflects modeled physical route status only).")
        if loss_of_access_min is None:
            warnings.append("No modeled loss of access within 180 min horizon. Future access beyond 180 min is unmodeled.")
        if alternate_summary and alternate_summary.status == "ALTERNATE_UNAVAILABLE":
            warnings.append("No alternate route candidate available for evaluation.")

        provenance = {
            "platform": "AQUORA — Urban Flood Intelligence & Response Platform",
            "phase": "Phase 11 Critical Access Guardian v1.0",
            "facility_id": facility.facility_id,
            "facility_category": facility.category,
            "facility_verification_status": facility.verification_status,
            "facility_provider_mode": facility.provider_mode,
            "digital_twin_run_id": dt_run_id,
            "routing_run_id": route_response.run_id,
            "routing_provider": route_response.provenance.get("routing_provider", "SYNTHETIC_ROUTER"),
            "critical_access_severity_policy": access_threshold,
            "route_impact_severity_policy": route_response.provenance.get("max_acceptable_severity", access_threshold),
            "canonical_slices_evaluated": CANONICAL_SLICES,
            "crs_canonical": "EPSG:4326",
            "crs_analysis": settings.GEOSPATIAL_ANALYSIS_CRS,
            "ml_status": "PROTOTYPE_ONLY",
            "training_labels_isolated": True,
            "created_at": now_utc.isoformat(),
        }

        # 11. Formulate Response Schema
        response = CriticalAccessResponseSchema(
            access_run_id=run_id,
            facility=facility,
            origin=request.responder_origin,
            digital_twin_run_id=dt_run_id,
            routing_run_id=route_response.run_id,
            current_access_status=current_access_status,
            modeled_loss_of_access_min=loss_of_access_min,
            modeled_loss_of_access_label=loss_of_access_str,
            time_to_loss_of_access_min=time_to_loss_min,
            accessibility_timeline=slice_evaluations,
            selected_route=primary_cand,
            alternate_route=alternate_summary,
            recommendation=rec_str,
            explanation=explanation_str,
            warnings=warnings,
            provenance=provenance,
            facility_operational_status=facility.operational_status,
            facility_verification_status=facility.verification_status,
        )

        # 12. Audit Database Persistence
        if self.db:
            try:
                run_db = CriticalAccessRun(
                    run_identifier=run_id,
                    facility_id=facility.facility_id,
                    digital_twin_run_id=dt_run_id,
                    routing_run_id=route_response.run_id,
                    origin_lat=request.responder_origin.latitude,
                    origin_lon=request.responder_origin.longitude,
                    current_access_status=current_access_status,
                    modeled_loss_of_access_min=loss_of_access_min,
                    time_to_loss_of_access_min=time_to_loss_min,
                    recommendation=rec_str,
                    explanation=explanation_str,
                    provenance=provenance,
                    status="COMPLETED",
                )
                self.db.add(run_db)

                for s_eval in slice_evaluations:
                    res_db = CriticalAccessResult(
                        access_run_id=run_id,
                        facility_id=facility.facility_id,
                        minutes_from_start=s_eval.minutes_from_start,
                        access_status=s_eval.accessibility_status,
                        route_id=primary_cand.route_id,
                        peak_severity=s_eval.primary_route_peak_severity,
                        usable_travel_window_min=primary_cand.usable_travel_window_min,
                    )
                    self.db.add(res_db)
                await self.db.commit()
            except Exception as e:  # noqa: BLE001
                logger.warning(f"Database persistence for CriticalAccessRun failed (offline/sqlite fallback): {e}")
                if self.db:
                    await self.db.rollback()

        return response
