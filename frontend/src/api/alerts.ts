import { apiFetch } from './client';

export type AlertType =
  | 'FLOOD_ONSET'
  | 'FLOOD_SEVERITY_ESCALATION'
  | 'HIGH_SEVERE_FLOOD_RISK'
  | 'TRAVEL_WINDOW_CLOSING'
  | 'ROUTE_AVOID'
  | 'CRITICAL_ACCESS_THREAT'
  | 'CRITICAL_ACCESS_LOSS'
  | 'PROTECT_CITY_PRIORITY'
  | 'GROUND_TRUTH_CONFLICT'
  | 'MODEL_INPUT_DEGRADED'
  | 'MODEL_UNCERTAINTY'
  | 'SIMULATOR_SCENARIO_RESULT'
  | 'SYSTEM_DATA_QUALITY';

export type AlertSeverity = 'INFO' | 'LOW' | 'MEDIUM' | 'HIGH' | 'CRITICAL';

export type AlertStatus =
  | 'ACTIVE'
  | 'ACKNOWLEDGED'
  | 'RESOLVED'
  | 'EXPIRED'
  | 'SUPPRESSED'
  | 'FAILED';

export type EvidenceStrength = 'UNVERIFIED' | 'CORROBORATED' | 'CONFIRMED';

export interface AlertGeneratePayload {
  digital_twin_run_id?: string;
  travel_window_run_id?: string;
  critical_access_run_id?: string;
  protect_city_run_id?: string;
  ground_truth_run_id?: string;
  simulator_run_id?: string;
}

export interface Alert {
  alert_id: string;
  alert_type: AlertType;
  severity: AlertSeverity;
  status: AlertStatus;
  title: string;
  summary: string;
  affected_entity_type: string;
  affected_entity_id: string;
  condition_key: string;
  fingerprint: string;
  source_phase: string;
  source_run_id: string;
  sources: Record<string, string>;
  input_completeness: number;
  model_status: string;
  evidence_strength: EvidenceStrength;
  uncertainty_status: string;
  recommended_action: string;
  governance_notice: string;
  configuration_version: string;
  generated_at: string;
  updated_at: string;
  acknowledged_at?: string;
  acknowledged_by?: string;
  resolved_at?: string;
  resolved_by?: string;
  resolution_reason?: string;
  suppressed_at?: string;
  suppressed_by?: string;
  suppression_reason?: string;
  expires_at?: string;
}

export interface AlertListResponse {
  total_count: number;
  alerts: Alert[];
}

export interface AlertEvidence {
  evidence_id: string;
  alert_id: string;
  source_phase: string;
  source_run_id: string;
  source_artifact_id?: string;
  evidence_type: string;
  metric: string;
  value?: number;
  units?: string;
  timestamp?: string;
  evidence_strength: EvidenceStrength;
  details: Record<string, any>;
}

export interface ExplainabilityStep {
  step_id: string;
  alert_id: string;
  sequence: number;
  category: string; // WHAT, WHY, WHEN, WHERE, HOW_CERTAIN, WHAT_SHOULD_I_DO, EVIDENCE
  statement: string;
  source_phase: string;
  source_run_id: string;
  source_metric?: string;
  source_value?: number;
  units?: string;
  slice_minutes?: number;
}

export interface AlertAuditEvent {
  event_id: string;
  alert_id: string;
  event_type: string;
  previous_status?: AlertStatus;
  new_status: AlertStatus;
  timestamp: string;
  actor_type: string;
  actor_reference: string;
  reason?: string;
  source_run_id?: string;
  event_metadata: Record<string, any>;
}

export interface AlertProvenance {
  alert_id: string;
  fingerprint: string;
  source_phase: string;
  source_run_id: string;
  sources: Record<string, string>;
  configuration_version: string;
  generated_at: string;
  provenance_hash: string;
  details: Record<string, any>;
}

export async function fetchAlerts(
  statusFilter?: AlertStatus,
  severityFilter?: AlertSeverity,
  typeFilter?: AlertType
): Promise<AlertListResponse> {
  const params = new URLSearchParams();
  if (statusFilter) params.append('status', statusFilter);
  if (severityFilter) params.append('severity', severityFilter);
  if (typeFilter) params.append('alert_type', typeFilter);

  const queryStr = params.toString() ? `?${params.toString()}` : '';
  return apiFetch<AlertListResponse>(`/api/v1/alerts${queryStr}`);
}

export async function generateAlerts(payload: AlertGeneratePayload): Promise<AlertListResponse> {
  return apiFetch<AlertListResponse>('/api/v1/alerts/generate', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function getAlertDetail(alertId: string): Promise<Alert> {
  return apiFetch<Alert>(`/api/v1/alerts/${alertId}`);
}

export async function acknowledgeAlert(alertId: string, actorRef: string = 'OPERATOR_PRIMARY', reason?: string): Promise<Alert> {
  return apiFetch<Alert>(`/api/v1/alerts/${alertId}/acknowledge`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ actor_reference: actorRef, reason }),
  });
}

export async function resolveAlert(alertId: string, resolutionReason: string, actorRef: string = 'OPERATOR_PRIMARY'): Promise<Alert> {
  return apiFetch<Alert>(`/api/v1/alerts/${alertId}/resolve`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ actor_reference: actorRef, resolution_reason: resolutionReason }),
  });
}

export async function suppressAlert(alertId: string, suppressionReason: string, actorRef: string = 'OPERATOR_PRIMARY'): Promise<Alert> {
  return apiFetch<Alert>(`/api/v1/alerts/${alertId}/suppress`, {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify({ actor_reference: actorRef, suppression_reason: suppressionReason }),
  });
}

export async function getAlertEvidence(alertId: string): Promise<AlertEvidence[]> {
  return apiFetch<AlertEvidence[]>(`/api/v1/alerts/${alertId}/evidence`);
}

export async function getAlertExplainability(alertId: string): Promise<ExplainabilityStep[]> {
  return apiFetch<ExplainabilityStep[]>(`/api/v1/alerts/${alertId}/explainability`);
}

export async function getAlertAudit(alertId: string): Promise<AlertAuditEvent[]> {
  return apiFetch<AlertAuditEvent[]>(`/api/v1/alerts/${alertId}/audit`);
}

export async function getAlertProvenance(alertId: string): Promise<AlertProvenance> {
  return apiFetch<AlertProvenance>(`/api/v1/alerts/${alertId}/provenance`);
}

export async function getAlertConfiguration(): Promise<Record<string, any>> {
  return apiFetch<Record<string, any>>('/api/v1/alerts/configuration');
}
