import React, { useEffect, useState } from 'react';
import {
  Bell,
  Info,
  Clock,
  RefreshCw
} from 'lucide-react';
import {
  Alert,
  AlertAuditEvent,
  AlertEvidence,
  AlertSeverity,
  AlertStatus,
  ExplainabilityStep,
  acknowledgeAlert,
  fetchAlerts,
  generateAlerts,
  getAlertAudit,
  getAlertEvidence,
  getAlertExplainability,
  resolveAlert,
  suppressAlert,
} from '@/api/alerts';
import { fetchLatestDigitalTwinRun } from '@/api/digitalTwin';
import { LeafletMap as _LeafletMap } from '@/map/LeafletMap';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';

export const AlertCenterFeature: React.FC = () => {
  const [alerts, setAlerts] = useState<Alert[]>([]);
  const [selectedAlert, setSelectedAlert] = useState<Alert | null>(null);
  const [evidences, setEvidences] = useState<AlertEvidence[]>([]);
  const [explainSteps, setExplainSteps] = useState<ExplainabilityStep[]>([]);
  const [auditEvents, setAuditEvents] = useState<AlertAuditEvent[]>([]);
  const [statusFilter, setStatusFilter] = useState<AlertStatus | 'ALL'>('ALL');
  const [severityFilter, setSeverityFilter] = useState<AlertSeverity | 'ALL'>('ALL');
  const [loading, setLoading] = useState<boolean>(false);
  const [generating, setGenerating] = useState<boolean>(false);
  const [noRunWarning, setNoRunWarning] = useState<string | null>(null);
  const [activeTab, setActiveTab] = useState<'OVERVIEW' | 'CAUSE_CHAIN' | 'EVIDENCE' | 'AUDIT'>('OVERVIEW');
  const [actionReason, setActionReason] = useState<string>('');

  const loadAlerts = async () => {
    setLoading(true);
    setNoRunWarning(null);
    try {
      let res = await fetchAlerts(
        statusFilter === 'ALL' ? undefined : statusFilter,
        severityFilter === 'ALL' ? undefined : severityFilter
      );
      if (!res.alerts || res.alerts.length === 0) {
        try {
          const dt = await fetchLatestDigitalTwinRun();
          if (dt && dt.run_id) {
            res = await generateAlerts({ digital_twin_run_id: dt.run_id });
          } else {
            setNoRunWarning('No source run available for alert evaluation.');
          }
        } catch {
          setNoRunWarning('No source run available for alert evaluation.');
        }
      }
      setAlerts(res.alerts || []);
      if (res.alerts && res.alerts.length > 0 && (!selectedAlert || !res.alerts.some(a => a.alert_id === selectedAlert.alert_id))) {
        selectAlert(res.alerts[0]);
      }
    } catch (err) {
      console.error('Failed to load alerts', err);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadAlerts();
  }, [statusFilter, severityFilter]);

  const selectAlert = async (alert: Alert) => {
    setSelectedAlert(alert);
    try {
      const [evd, exp, aud] = await Promise.all([
        getAlertEvidence(alert.alert_id),
        getAlertExplainability(alert.alert_id),
        getAlertAudit(alert.alert_id),
      ]);
      setEvidences(evd);
      setExplainSteps(exp);
      setAuditEvents(aud);
    } catch (err) {
      console.error('Failed to load alert details', err);
    }
  };

  const handleTriggerGenerate = async () => {
    setGenerating(true);
    try {
      let dtRunId: string | undefined = undefined;
      try {
        const dt = await fetchLatestDigitalTwinRun();
        if (dt && dt.run_id) {
          dtRunId = dt.run_id;
        }
      } catch (e) {
        console.warn('Could not fetch latest Digital Twin run', e);
      }
      if (!dtRunId) {
        setNoRunWarning('No active Digital Twin run available for alert evaluation. Run a simulation first.');
        return;
      }
      await generateAlerts({
        digital_twin_run_id: dtRunId,
      });
      await loadAlerts();
    } catch (err) {
      console.error('Failed to generate alerts', err);
    } finally {
      setGenerating(false);
    }
  };

  const handleAcknowledge = async () => {
    if (!selectedAlert) return;
    try {
      const updated = await acknowledgeAlert(selectedAlert.alert_id, 'OPERATOR_PRIMARY', actionReason || undefined);
      setSelectedAlert(updated);
      setActionReason('');
      await loadAlerts();
    } catch (err) {
      console.error('Failed to acknowledge alert', err);
    }
  };

  const handleResolve = async () => {
    if (!selectedAlert || !actionReason) return;
    try {
      const updated = await resolveAlert(selectedAlert.alert_id, actionReason, 'OPERATOR_PRIMARY');
      setSelectedAlert(updated);
      setActionReason('');
      await loadAlerts();
    } catch (err) {
      console.error('Failed to resolve alert', err);
    }
  };

  const handleSuppress = async () => {
    if (!selectedAlert || !actionReason) return;
    try {
      const updated = await suppressAlert(selectedAlert.alert_id, actionReason, 'OPERATOR_PRIMARY');
      setSelectedAlert(updated);
      setActionReason('');
      await loadAlerts();
    } catch (err) {
      console.error('Failed to suppress alert', err);
    }
  };

  const getSeverityBadgeVariant = (sev: AlertSeverity): 'danger' | 'warning' | 'info' | 'neutral' => {
    switch (sev) {
      case 'CRITICAL':
        return 'danger';
      case 'HIGH':
        return 'warning';
      case 'MEDIUM':
        return 'warning';
      case 'LOW':
      case 'INFO':
        return 'info';
      default:
        return 'neutral';
    }
  };

  const SEVERITY_COLORS: Record<string, string> = {
    CRITICAL: '#dc2626',
    HIGH: '#ea580c',
    MEDIUM: '#d97706',
    LOW: '#0891b2',
    INFO: '#94a3b8',
  };

  return (
    <div className="space-y-5 pb-10 font-sans max-w-[1240px] mx-auto">

      {/* ── Page header ─────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-3">
        <div>
          <h1
            className="text-[1.75rem] font-extrabold leading-none tracking-tight"
            style={{ color: 'var(--aq-navy)', letterSpacing: '-0.02em' }}
          >
            Alerts
          </h1>
          <p className="mt-1.5 text-[14px]" style={{ color: 'var(--aq-muted)' }}>
            Active conditions that need attention — reviewed, acknowledged, or resolved by your team.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={loadAlerts}
            isLoading={loading}
            icon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Refresh
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={handleTriggerGenerate}
            isLoading={generating}
          >
            Evaluate alerts
          </Button>
        </div>
      </div>

      {/* ── Warning banner ─────────────────────────────────── */}
      {noRunWarning && (
        <div className="px-4 py-3 rounded-xl text-[12px] font-medium" style={{ background: '#fffbeb', color: '#92400e', border: '1px solid #fde68a' }}>
          {noRunWarning}
        </div>
      )}

      {/* ── Filter row ─────────────────────────────────────── */}
      <div className="flex flex-wrap gap-2">
        {/* Status filters */}
        {(['ALL', 'ACTIVE', 'ACKNOWLEDGED', 'RESOLVED'] as const).map((s) => (
          <button
            key={s}
            onClick={() => setStatusFilter(s as AlertStatus | 'ALL')}
            className="px-3 py-1.5 rounded-xl text-[11px] font-semibold transition-all duration-150"
            style={statusFilter === s
              ? { background: 'var(--aq-blue)', color: '#fff' }
              : { background: '#f8fafc', color: 'var(--aq-muted)', border: '1px solid rgba(15,35,64,0.10)' }
            }
          >
            {s.charAt(0) + s.slice(1).toLowerCase()}
          </button>
        ))}
        <span className="w-px self-stretch bg-slate-200 mx-1" />
        {/* Severity filters */}
        {(['ALL', 'CRITICAL', 'HIGH', 'MEDIUM', 'LOW'] as const).map((sv) => (
          <button
            key={sv}
            onClick={() => setSeverityFilter(sv as AlertSeverity | 'ALL')}
            className="px-3 py-1.5 rounded-xl text-[11px] font-semibold flex items-center gap-1.5 transition-all duration-150"
            style={severityFilter === sv
              ? { background: SEVERITY_COLORS[sv] || 'var(--aq-blue)', color: '#fff' }
              : { background: '#f8fafc', color: 'var(--aq-muted)', border: '1px solid rgba(15,35,64,0.10)' }
            }
          >
            {sv !== 'ALL' && (
              <span className="w-1.5 h-1.5 rounded-full" style={{ background: SEVERITY_COLORS[sv] }} />
            )}
            {sv.charAt(0) + sv.slice(1).toLowerCase()}
          </button>
        ))}
      </div>

      {/* ── Main layout: alerts list + detail ──────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5">

        {/* Alert list — 1/3 */}
        <div className="flex flex-col gap-2">
          {loading ? (
            <div className="py-10 text-center text-[12px]" style={{ color: 'var(--aq-muted)' }}>Loading alerts…</div>
          ) : alerts.length === 0 ? (
            <Card padding="md">
              <div className="flex flex-col items-center py-8 text-center">
                <Bell className="w-8 h-8 mb-2" style={{ color: 'var(--aq-muted)' }} />
                <p className="text-[13px] font-semibold" style={{ color: 'var(--aq-text)' }}>No alerts at this time</p>
                <p className="text-[11px] mt-1" style={{ color: 'var(--aq-muted)' }}>
                  Tap "Evaluate alerts" to check current flood conditions.
                </p>
              </div>
            </Card>
          ) : (
            <div className="space-y-2 max-h-[720px] overflow-y-auto pr-1" style={{ scrollbarWidth: 'thin' }}>
              {alerts.map((alert) => {
                const isSelected = selectedAlert?.alert_id === alert.alert_id;
                const sevColor = SEVERITY_COLORS[alert.severity] || '#94a3b8';
                return (
                  <button
                    key={alert.alert_id}
                    onClick={() => selectAlert(alert)}
                    className="w-full text-left p-4 rounded-2xl transition-all duration-150 flex items-start gap-3"
                    style={{
                      background: isSelected ? '#eff6ff' : '#ffffff',
                      border: isSelected ? '1.5px solid #bfdbfe' : '1px solid rgba(15,35,64,0.07)',
                      boxShadow: isSelected ? '0 2px 8px rgba(26,86,219,0.12)' : '0 1px 3px rgba(15,35,64,0.06)',
                    }}
                  >
                    <span className="w-2 h-2 rounded-full shrink-0 mt-1.5" style={{ background: sevColor }} />
                    <div className="flex-1 min-w-0">
                      <div className="text-[13px] font-semibold leading-tight" style={{ color: 'var(--aq-navy)' }}>
                        {alert.title}
                      </div>
                      <div className="text-[10px] mt-1 truncate" style={{ color: 'var(--aq-muted)' }}>
                        {alert.alert_type.replace(/_/g, ' ')} · {alert.status}
                      </div>
                    </div>
                    <Badge
                      variant={getSeverityBadgeVariant(alert.severity)}
                      size="sm"
                    >
                      {alert.severity}
                    </Badge>
                  </button>
                );
              })}
            </div>
          )}
        </div>

        {/* Alert detail — 2/3 */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          {selectedAlert ? (
            <>
              {/* Detail header */}
              <Card padding="md" className="space-y-4">
                <div className="flex items-start justify-between gap-4">
                  <div className="flex-1">
                    <div className="flex items-center gap-2 flex-wrap mb-1">
                      <Badge variant={getSeverityBadgeVariant(selectedAlert.severity)} size="sm">
                        {selectedAlert.severity}
                      </Badge>
                      <Badge variant="neutral" size="sm">{selectedAlert.status}</Badge>
                    </div>
                    <h2 className="text-[17px] font-bold leading-snug" style={{ color: 'var(--aq-navy)' }}>
                      {selectedAlert.title}
                    </h2>
                    <p className="text-[12px] mt-1 leading-relaxed" style={{ color: 'var(--aq-muted)' }}>
                      {selectedAlert.summary}
                    </p>
                  </div>
                </div>

                {/* Recommended action */}
                {selectedAlert.recommended_action && (
                  <div className="px-3 py-2.5 rounded-xl text-[12px] font-medium" style={{ background: '#eff6ff', color: '#1e3a8a', border: '1px solid #bfdbfe' }}>
                    <div className="font-semibold mb-0.5 flex items-center gap-1.5">
                      <Info className="w-3.5 h-3.5" />
                      Recommended action
                    </div>
                    {selectedAlert.recommended_action}
                  </div>
                )}

                {/* Action controls */}
                {selectedAlert.status === 'ACTIVE' && (
                  <div className="space-y-2 pt-2 border-t" style={{ borderColor: 'rgba(15,35,64,0.06)' }}>
                    <div>
                      <label className="aq-label block mb-1">Reason / note (required for resolve or suppress)</label>
                      <input
                        type="text"
                        value={actionReason}
                        onChange={(e) => setActionReason(e.target.value)}
                        placeholder="e.g. Confirmed — routing team notified"
                        className="w-full rounded-xl px-3 py-2 text-[12px] font-medium focus:outline-none"
                        style={{ background: '#f8fafc', border: '1px solid rgba(15,35,64,0.12)', color: 'var(--aq-text)' }}
                      />
                    </div>
                    <div className="flex gap-2 flex-wrap">
                      <Button variant="outline" size="sm" onClick={handleAcknowledge}>Acknowledge</Button>
                      <Button
                        variant="primary"
                        size="sm"
                        onClick={handleResolve}
                        disabled={!actionReason.trim()}
                        style={{ background: '#15803d', borderColor: '#15803d' }}
                      >
                        Mark resolved
                      </Button>
                      <Button
                        variant="outline"
                        size="sm"
                        onClick={handleSuppress}
                        disabled={!actionReason.trim()}
                      >
                        Suppress
                      </Button>
                    </div>
                  </div>
                )}
              </Card>

              {/* Detail tabs */}
              <Card padding="sm">
                <div className="flex gap-1 mb-4 overflow-x-auto">
                  {(['OVERVIEW', 'CAUSE_CHAIN', 'EVIDENCE', 'AUDIT'] as const).map((tab) => (
                    <button
                      key={tab}
                      onClick={() => setActiveTab(tab)}
                      className="px-3 py-1.5 rounded-xl text-[11px] font-semibold whitespace-nowrap transition-all duration-150"
                      style={activeTab === tab
                        ? { background: 'var(--aq-blue)', color: '#fff' }
                        : { background: '#f8fafc', color: 'var(--aq-muted)', border: '1px solid rgba(15,35,64,0.08)' }
                      }
                    >
                      {tab === 'CAUSE_CHAIN' ? 'Why' : tab.charAt(0) + tab.slice(1).toLowerCase()}
                    </button>
                  ))}
                </div>

                <div className="p-1">
                  {activeTab === 'OVERVIEW' && (
                    <div className="space-y-2">
                      {[
                        { label: 'Affected area', val: `${selectedAlert.affected_entity_type}: ${selectedAlert.affected_entity_id}` },
                        { label: 'Evidence strength', val: selectedAlert.evidence_strength },
                        { label: 'Model confidence', val: selectedAlert.uncertainty_status },
                        { label: 'Generated', val: new Date(selectedAlert.generated_at).toLocaleString() },
                      ].map((row) => (
                        <div key={row.label} className="flex justify-between text-[12px] py-1.5 border-b" style={{ borderColor: 'rgba(15,35,64,0.05)' }}>
                          <span style={{ color: 'var(--aq-muted)' }}>{row.label}</span>
                          <span className="font-semibold" style={{ color: 'var(--aq-text)' }}>{row.val}</span>
                        </div>
                      ))}
                      {selectedAlert.governance_notice && (
                        <p className="text-[10px] pt-2" style={{ color: 'var(--aq-muted)' }}>
                          {selectedAlert.governance_notice}
                        </p>
                      )}
                    </div>
                  )}

                  {activeTab === 'CAUSE_CHAIN' && (
                    <div className="space-y-2">
                      {explainSteps.length === 0 ? (
                        <p className="text-[12px] py-4 text-center" style={{ color: 'var(--aq-muted)' }}>No explainability data available for this alert.</p>
                      ) : (
                        explainSteps.map((step) => (
                          <div key={step.step_id} className="flex gap-3 text-[12px]">
                            <div
                              className="w-6 h-6 rounded-full shrink-0 flex items-center justify-center text-[10px] font-bold text-white"
                              style={{ background: 'var(--aq-blue)' }}
                            >
                              {step.sequence}
                            </div>
                            <div>
                              <div className="font-semibold mb-0.5" style={{ color: 'var(--aq-navy)' }}>{step.category}</div>
                              <div style={{ color: 'var(--aq-muted)' }}>{step.statement}</div>
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  )}

                  {activeTab === 'EVIDENCE' && (
                    <div className="space-y-2">
                      {evidences.length === 0 ? (
                        <p className="text-[12px] py-4 text-center" style={{ color: 'var(--aq-muted)' }}>No evidence data available.</p>
                      ) : (
                        evidences.map((ev) => (
                          <div key={ev.evidence_id} className="p-3 rounded-xl" style={{ background: '#f8fafc', border: '1px solid rgba(15,35,64,0.06)' }}>
                            <div className="flex items-center justify-between text-[12px]">
                              <span className="font-semibold" style={{ color: 'var(--aq-text)' }}>{ev.metric}</span>
                              {ev.value !== undefined && (
                                <span className="font-bold" style={{ color: 'var(--aq-blue)' }}>
                                  {ev.value.toFixed(2)}{ev.units ? ` ${ev.units}` : ''}
                                </span>
                              )}
                            </div>
                            <div className="text-[10px] mt-0.5" style={{ color: 'var(--aq-muted)' }}>
                              {ev.evidence_type} · {ev.evidence_strength}
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  )}

                  {activeTab === 'AUDIT' && (
                    <div className="space-y-2">
                      {auditEvents.length === 0 ? (
                        <p className="text-[12px] py-4 text-center" style={{ color: 'var(--aq-muted)' }}>No audit history.</p>
                      ) : (
                        auditEvents.map((ev) => (
                          <div key={ev.event_id} className="flex items-start gap-3 text-[11px]">
                            <Clock className="w-3.5 h-3.5 shrink-0 mt-0.5" style={{ color: 'var(--aq-muted)' }} />
                            <div>
                              <div className="font-semibold" style={{ color: 'var(--aq-text)' }}>
                                {ev.event_type.replace(/_/g, ' ')}
                                {ev.previous_status && ` · ${ev.previous_status} → ${ev.new_status}`}
                              </div>
                              <div style={{ color: 'var(--aq-muted)' }}>
                                {ev.actor_reference} · {new Date(ev.timestamp).toLocaleString()}
                              </div>
                              {ev.reason && <div className="italic mt-0.5" style={{ color: 'var(--aq-muted)' }}>"{ev.reason}"</div>}
                            </div>
                          </div>
                        ))
                      )}
                    </div>
                  )}
                </div>
              </Card>
            </>
          ) : !loading ? (
            <Card padding="md">
              <div className="flex flex-col items-center py-12 text-center">
                <Bell className="w-8 h-8 mb-2" style={{ color: 'var(--aq-muted)' }} />
                <p className="text-[13px] font-semibold" style={{ color: 'var(--aq-text)' }}>
                  Select an alert to review details
                </p>
              </div>
            </Card>
          ) : null}
        </div>
      </div>
    </div>
  );
};

export default AlertCenterFeature;
