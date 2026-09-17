import React, { useState, useEffect } from 'react';
import {
  Eye,
  Camera,
  AlertTriangle,
  RefreshCw,
  Plus,
  Upload,
  FileText,
  X
} from 'lucide-react';
import { LeafletMap } from '@/map/LeafletMap';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import {
  fetchObservations,
  fetchIncidents as _fetchIncidents,
  createObservation,
  uploadObservationMedia,
  triggerGroundTruthRun,
  fetchObservationComparison,
  ObservationResponse,
  ComparisonResponse,
  ObservationPayload,
} from '@/api/groundTruth';

const VERIFICATION_BADGES: Record<string, { badge: 'success' | 'info' | 'warning' }> = {
  CONFIRMED: { badge: 'success' },
  CORROBORATED: { badge: 'info' },
  UNVERIFIED: { badge: 'warning' },
};

export const GroundTruthFeature: React.FC = () => {
  const [observations, setObservations] = useState<ObservationResponse[]>([]);
  const [selectedObs, setSelectedObs] = useState<ObservationResponse | null>(null);
  const [comparison, setComparison] = useState<ComparisonResponse | null>(null);
  const [loading, setLoading] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Form State
  const [showSubmitModal, setShowSubmitModal] = useState<boolean>(false);
  const [formLat, setFormLat] = useState<string>('19.076');
  const [formLon, setFormLon] = useState<string>('72.8777');
  const [formPresence, setFormPresence] = useState<string>('FLOOD_PRESENT');
  const [formDepth, setFormDepth] = useState<string>('10_TO_20CM');
  const [formPassability, setFormPassability] = useState<string>('DIFFICULT');
  const [formDesc, setFormDesc] = useState<string>('');
  const [selectedFile, setSelectedFile] = useState<File | null>(null);
  const [submitting, setSubmitting] = useState<boolean>(false);

  const loadData = async () => {
    setLoading(true);
    setErrorMsg(null);
    try {
      let obsData = await fetchObservations();

      if (!obsData || obsData.length === 0) {
        await triggerGroundTruthRun('SYNTHETIC');
        obsData = await fetchObservations();
      }

      setObservations(obsData);
      // Incidents stored for future use

      if (obsData.length > 0) {
        setSelectedObs(obsData[0]);
        const comp = await fetchObservationComparison(obsData[0].observation_id);
        setComparison(comp);
      }
    } catch (err: unknown) {
      const msg = err instanceof Error ? err.message : 'Failed to load ground truth observation data.';
      setErrorMsg(msg);
    } finally {
      setLoading(false);
    }
  };

  useEffect(() => {
    loadData();
  }, []);

  const mapMarkers = observations.map((obs) => {
    let colorHex = '#d97706';
    if (obs.verification_state === 'CONFIRMED') colorHex = '#059669';
    if (obs.verification_state === 'CORROBORATED') colorHex = '#0284c7';

    return {
      id: obs.observation_id,
      position: [obs.latitude, obs.longitude] as [number, number],
      color: colorHex,
      popupContent: `<strong>${obs.observation_type}</strong><br/>Status: ${obs.verification_state}<br/>Depth: ${obs.water_depth_class}`,
    };
  });

  const handleCreateObservation = async (e: React.FormEvent) => {
    e.preventDefault();
    setSubmitting(true);
    const lat = parseFloat(formLat) || 19.076;
    const lon = parseFloat(formLon) || 72.8777;

    try {
      const payload: ObservationPayload = {
        latitude: lat,
        longitude: lon,
        location_source: 'MANUAL',
        flood_presence: formPresence,
        water_depth_class: formDepth,
        road_passability: formPassability,
        description: formDesc,
        source: 'COMMUNITY',
        observer_type: 'COMMUNITY',
      };

      const newObs = await createObservation(payload);

      if (selectedFile) {
        await uploadObservationMedia(newObs.observation_id, selectedFile);
      }

      setShowSubmitModal(false);
      setSelectedFile(null);
      setFormDesc('');
      await loadData();
    } catch (err: unknown) {
      alert(err instanceof Error ? err.message : 'Submission failed');
    } finally {
      setSubmitting(false);
    }
  };

  const confirmedCount = observations.filter((o) => o.verification_state === 'CONFIRMED').length;
  const corroboratedCount = observations.filter((o) => o.verification_state === 'CORROBORATED').length;
  const contradictionCount = observations.filter((o) => o.model_comparison_status === 'MODEL_CONTRADICTS_OBSERVATION').length;

  return (
    <div className="space-y-5 pb-10 font-sans max-w-[1240px] mx-auto">

      {/* ── Page header ─────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-3">
        <div>
          <h1
            className="text-[1.75rem] font-extrabold leading-none tracking-tight"
            style={{ color: 'var(--aq-navy)', letterSpacing: '-0.02em' }}
          >
            Ground Truth
          </h1>
          <p className="mt-1.5 text-[14px]" style={{ color: 'var(--aq-muted)' }}>
            What people are seeing on the ground right now — field reports versus flood forecast.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <Button
            variant="outline"
            size="sm"
            onClick={loadData}
            isLoading={loading}
            icon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Refresh
          </Button>
          <Button
            variant="primary"
            size="sm"
            onClick={() => setShowSubmitModal(true)}
            icon={<Plus className="w-3.5 h-3.5" />}
          >
            Report what you see
          </Button>
        </div>
      </div>

      {/* ── Error state ─────────────────────────────────────── */}
      {errorMsg && (
        <Card padding="md">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" style={{ color: '#d97706' }} />
            <div>
              <p className="text-[13px] font-semibold" style={{ color: 'var(--aq-text)' }}>
                Couldn't load field reports
              </p>
              <p className="text-[11px] mt-0.5" style={{ color: 'var(--aq-muted)' }}>{errorMsg}</p>
            </div>
          </div>
        </Card>
      )}

      {/* ── KPI strip ───────────────────────────────────────── */}
      <div className="grid grid-cols-2 md:grid-cols-4 gap-3">
        {[
          { label: 'Total field reports', value: observations.length, color: 'var(--aq-navy)' },
          { label: 'Confirmed', value: confirmedCount, color: '#15803d' },
          { label: 'Corroborated', value: corroboratedCount, color: 'var(--aq-blue)' },
          { label: 'Contradict forecast', value: contradictionCount, color: '#dc2626' },
        ].map((kpi) => (
          <div
            key={kpi.label}
            className="p-4 rounded-2xl bg-white"
            style={{ boxShadow: '0 1px 3px rgba(15,35,64,0.07)', border: '1px solid rgba(15,35,64,0.06)' }}
          >
            <div className="aq-label mb-1">{kpi.label}</div>
            <div className="text-[24px] font-extrabold leading-none" style={{ color: kpi.color, letterSpacing: '-0.02em' }}>
              {kpi.value}
            </div>
          </div>
        ))}
      </div>

      {/* ── Main layout ─────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 min-h-[480px]">

        {/* Map — 2/3 */}
        <div className="lg:col-span-2 aq-map-container min-h-[440px]">
          <LeafletMap
            center={[19.076, 72.8777]}
            zoom={13}
            markers={mapMarkers}
            height="100%"
          />
        </div>

        {/* Right panel — 1/3 */}
        <div className="flex flex-col gap-4">

          {/* Observation list */}
          <Card padding="sm" className="flex-1">
            <div className="flex items-center gap-2 px-1 pb-3 border-b mb-3" style={{ borderColor: 'rgba(15,35,64,0.06)' }}>
              <Eye className="w-4 h-4" style={{ color: 'var(--aq-aqua)' }} />
              <span className="aq-section-title">Field reports</span>
              <span className="ml-auto text-[11px] font-semibold px-2 py-0.5 rounded-full" style={{ background: '#eff6ff', color: 'var(--aq-blue)' }}>
                {observations.length}
              </span>
            </div>

            {loading ? (
              <div className="py-8 text-center text-[12px]" style={{ color: 'var(--aq-muted)' }}>
                Loading field reports…
              </div>
            ) : observations.length === 0 ? (
              <div className="py-8 text-center">
                <Camera className="w-8 h-8 mx-auto mb-2" style={{ color: 'var(--aq-muted)' }} />
                <p className="text-[13px] font-semibold" style={{ color: 'var(--aq-text)' }}>No reports yet</p>
                <p className="text-[11px] mt-1" style={{ color: 'var(--aq-muted)' }}>
                  Be the first to report what you see.
                </p>
              </div>
            ) : (
              <div className="space-y-1.5 max-h-[340px] overflow-y-auto pr-1" style={{ scrollbarWidth: 'thin' }}>
                {observations.map((obs) => {
                  const vStyle = VERIFICATION_BADGES[obs.verification_state] || { badge: 'neutral' };
                  const isSelected = selectedObs?.observation_id === obs.observation_id;
                  return (
                    <button
                      key={obs.observation_id}
                      onClick={async () => {
                        setSelectedObs(obs);
                        const comp = await fetchObservationComparison(obs.observation_id);
                        setComparison(comp);
                      }}
                      className="w-full text-left p-3 rounded-xl transition-all duration-150 flex items-start gap-3"
                      style={{
                        background: isSelected ? '#eff6ff' : '#f8fafc',
                        border: isSelected ? '1.5px solid #bfdbfe' : '1px solid rgba(15,35,64,0.06)',
                      }}
                    >
                      <div className="shrink-0 w-1.5 h-1.5 rounded-full mt-1.5" style={{
                        background: obs.verification_state === 'CONFIRMED' ? '#059669'
                          : obs.verification_state === 'CORROBORATED' ? '#0284c7' : '#d97706',
                      }} />
                      <div className="flex-1 min-w-0">
                        <div className="text-[12px] font-semibold truncate" style={{ color: 'var(--aq-text)' }}>
                          {obs.observation_type.replace(/_/g, ' ')}
                        </div>
                        <div className="text-[10px] mt-0.5" style={{ color: 'var(--aq-muted)' }}>
                          {obs.latitude.toFixed(4)}°N · {obs.water_depth_class?.replace(/_/g, ' ')}
                        </div>
                      </div>
                      <Badge variant={vStyle.badge as 'success' | 'info' | 'warning' | 'neutral'} size="sm">
                        {obs.verification_state.charAt(0) + obs.verification_state.slice(1).toLowerCase()}
                      </Badge>
                    </button>
                  );
                })}
              </div>
            )}
          </Card>

          {/* Observation detail */}
          {selectedObs && (
            <Card padding="md" className="space-y-3">
              <div className="flex items-center justify-between pb-2 border-b" style={{ borderColor: 'rgba(15,35,64,0.06)' }}>
                <span className="aq-section-title">Report detail</span>
                <Badge
                  variant={(VERIFICATION_BADGES[selectedObs.verification_state]?.badge || 'neutral') as 'success' | 'info' | 'warning' | 'neutral'}
                  size="sm"
                >
                  {selectedObs.verification_state}
                </Badge>
              </div>

              {[
                { label: 'Type', val: selectedObs.observation_type.replace(/_/g, ' ') },
                { label: 'Water depth', val: selectedObs.water_depth_class?.replace(/_/g, ' ') || '—' },
                { label: 'Passability', val: selectedObs.road_passability?.replace(/_/g, ' ') || '—' },
                { label: 'Source', val: selectedObs.source || 'Community' },
              ].map((row) => (
                <div key={row.label} className="flex justify-between text-[12px] py-1 border-b" style={{ borderColor: 'rgba(15,35,64,0.04)' }}>
                  <span style={{ color: 'var(--aq-muted)' }}>{row.label}</span>
                  <span className="font-semibold" style={{ color: 'var(--aq-text)' }}>{row.val}</span>
                </div>
              ))}

              {comparison && (
                <div className="mt-1 px-3 py-2.5 rounded-xl text-[11px]" style={{
                  background: comparison.comparison_status === 'CONTRADICTION'
                    ? '#fff1f2' : '#f0fdf4',
                  border: comparison.comparison_status === 'CONTRADICTION'
                    ? '1px solid #fecdd3' : '1px solid #bbf7d0',
                  color: comparison.comparison_status === 'CONTRADICTION'
                    ? '#be123c' : '#15803d',
                }}>
                  <div className="font-semibold mb-1">
                    {comparison.comparison_status === 'CONTRADICTION'
                      ? '⚠ Model contradicts this report'
                      : '✓ Model agrees with this report'}
                  </div>
                  {comparison.explanation && (
                    <p style={{ opacity: 0.85 }}>{comparison.explanation}</p>
                  )}
                </div>
              )}
            </Card>
          )}
        </div>
      </div>

      {/* ── Submit modal ─────────────────────────────────────── */}
      {showSubmitModal && (
        <div className="fixed inset-0 z-50 flex items-center justify-center p-4" style={{ background: 'rgba(15,35,64,0.5)', backdropFilter: 'blur(4px)' }}>
          <div className="w-full max-w-lg bg-white rounded-2xl overflow-hidden" style={{ boxShadow: '0 20px 48px rgba(15,35,64,0.25)' }}>
            <div className="flex items-center justify-between px-6 py-4 border-b" style={{ borderColor: 'rgba(15,35,64,0.08)' }}>
              <h2 className="text-[16px] font-bold" style={{ color: 'var(--aq-navy)' }}>Report what you see</h2>
              <button onClick={() => setShowSubmitModal(false)} className="p-1 rounded-lg hover:bg-slate-100 transition-colors">
                <X className="w-5 h-5" style={{ color: 'var(--aq-muted)' }} />
              </button>
            </div>

            <form onSubmit={handleCreateObservation} className="p-6 space-y-4">
              {/* Location */}
              <div className="grid grid-cols-2 gap-3">
                {[
                  { label: 'Latitude', val: formLat, setter: setFormLat },
                  { label: 'Longitude', val: formLon, setter: setFormLon },
                ].map((f) => (
                  <div key={f.label}>
                    <label className="aq-label block mb-1">{f.label}</label>
                    <input
                      type="text" value={f.val}
                      onChange={(e) => f.setter(e.target.value)}
                      className="w-full rounded-xl px-3 py-2 text-[12px] font-medium focus:outline-none"
                      style={{ background: '#f8fafc', border: '1px solid rgba(15,35,64,0.12)', color: 'var(--aq-text)' }}
                    />
                  </div>
                ))}
              </div>

              {/* Flood presence */}
              <div>
                <label className="aq-label block mb-1.5">Is there flooding?</label>
                <select
                  value={formPresence}
                  onChange={(e) => setFormPresence(e.target.value)}
                  className="w-full rounded-xl px-3 py-2 text-[12px] font-medium focus:outline-none"
                  style={{ background: '#f8fafc', border: '1px solid rgba(15,35,64,0.12)', color: 'var(--aq-text)' }}
                >
                  <option value="FLOOD_PRESENT">Yes, flooding is present</option>
                  <option value="FLOOD_ABSENT">No flooding visible</option>
                  <option value="UNCERTAIN">I'm not sure</option>
                </select>
              </div>

              {/* Depth & passability */}
              <div className="grid grid-cols-2 gap-3">
                <div>
                  <label className="aq-label block mb-1">Water depth</label>
                  <select
                    value={formDepth}
                    onChange={(e) => setFormDepth(e.target.value)}
                    className="w-full rounded-xl px-3 py-2 text-[12px] font-medium focus:outline-none"
                    style={{ background: '#f8fafc', border: '1px solid rgba(15,35,64,0.12)', color: 'var(--aq-text)' }}
                  >
                    <option value="TRACE">Trace (&lt;2 cm)</option>
                    <option value="LESS_THAN_10CM">Under 10 cm</option>
                    <option value="10_TO_20CM">10–20 cm</option>
                    <option value="20_TO_50CM">20–50 cm</option>
                    <option value="ABOVE_50CM">Above 50 cm</option>
                  </select>
                </div>
                <div>
                  <label className="aq-label block mb-1">Road usable?</label>
                  <select
                    value={formPassability}
                    onChange={(e) => setFormPassability(e.target.value)}
                    className="w-full rounded-xl px-3 py-2 text-[12px] font-medium focus:outline-none"
                    style={{ background: '#f8fafc', border: '1px solid rgba(15,35,64,0.12)', color: 'var(--aq-text)' }}
                  >
                    <option value="PASSABLE">Yes, passable</option>
                    <option value="DIFFICULT">Difficult</option>
                    <option value="IMPASSABLE">Impassable</option>
                  </select>
                </div>
              </div>

              {/* Description */}
              <div>
                <label className="aq-label block mb-1">What else can you tell us? (optional)</label>
                <textarea
                  value={formDesc}
                  onChange={(e) => setFormDesc(e.target.value)}
                  rows={2}
                  placeholder="Describe what you're seeing…"
                  className="w-full rounded-xl px-3 py-2 text-[12px] font-medium focus:outline-none resize-none"
                  style={{ background: '#f8fafc', border: '1px solid rgba(15,35,64,0.12)', color: 'var(--aq-text)' }}
                />
              </div>

              {/* Photo */}
              <div>
                <label className="aq-label block mb-1.5 flex items-center gap-1.5">
                  <Upload className="w-3 h-3" />
                  Attach a photo (optional)
                </label>
                <input
                  type="file"
                  accept="image/*"
                  onChange={(e) => setSelectedFile(e.target.files?.[0] || null)}
                  className="text-[11px]"
                  style={{ color: 'var(--aq-muted)' }}
                />
              </div>

              <div className="flex gap-3 pt-2">
                <Button
                  type="button"
                  variant="outline"
                  size="sm"
                  onClick={() => setShowSubmitModal(false)}
                  className="flex-1"
                >
                  Cancel
                </Button>
                <Button
                  type="submit"
                  variant="primary"
                  size="sm"
                  isLoading={submitting}
                  icon={<FileText className="w-3.5 h-3.5" />}
                  className="flex-1"
                >
                  Submit report
                </Button>
              </div>
            </form>
          </div>
        </div>
      )}
    </div>
  );
};

export default GroundTruthFeature;
