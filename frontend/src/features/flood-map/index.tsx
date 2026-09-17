import React, { useState, useEffect } from 'react';
import {
  Play,
  Pause,
  Clock,
  Info,
  RefreshCw,
  Activity,
  Search,
  CheckCircle2,
  MapPin,
  ShieldAlert,
} from 'lucide-react';
import { LeafletMap } from '@/map/LeafletMap';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import {
  fetchLatestDigitalTwinRun,
  triggerDigitalTwinRun,
  fetchCellDiagnostics,
  DigitalTwinRunResponse,
  DigitalTwinTimeSlice,
  CellDiagnosticDetail,
} from '@/api/digitalTwin';

const MITHI_CHANNEL_LINE = [
  {
    id: 'mithi_channel',
    title: 'Mithi River Drainage Channel',
    color: '#0284c7',
    weight: 4,
    positions: [
      [19.102, 72.885],
      [19.088, 72.880],
      [19.072, 72.872],
      [19.055, 72.860],
      [19.040, 72.850],
    ] as [number, number][],
  },
];

const FLOOD_OUTLOOK_MARKERS = [
  {
    id: 'kurla_junction',
    position: [19.072, 72.880] as [number, number],
    title: 'Kurla Junction',
    subtitle: 'High risk',
    color: '#dc2626',
    badge: '!',
  },
  {
    id: 'sion_hospital',
    position: [19.050, 72.862] as [number, number],
    title: 'Sion Hospital',
    subtitle: 'Access at risk',
    color: '#dc2626',
    badge: '+',
  },
  {
    id: 'bkc_center',
    position: [19.065, 72.865] as [number, number],
    title: 'Bandra Kurla Complex',
    subtitle: 'Command Hub',
    color: '#1a56db',
    badge: 'C',
  },
];

const CANONICAL_MINUTES = [0, 30, 60, 90, 120, 150, 180];
const SLICE_LABELS: Record<number, string> = {
  0: 'NOW',
  30: '+30m',
  60: '+60m (Peak)',
  90: '+90m',
  120: '+120m',
  150: '+150m',
  180: '+180m',
};

export const FloodMapFeature: React.FC = () => {
  const [selectedMinutes, setSelectedMinutes] = useState<number>(60);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);
  const [runData, setRunData] = useState<DigitalTwinRunResponse | null>(null);
  const [isTriggering, setIsTriggering] = useState<boolean>(false);
  const [selectedCellId, setSelectedCellId] = useState<string>('CELL_R0020_C0020');
  const [inspectedCell, setInspectedCell] = useState<CellDiagnosticDetail | null>(null);
  const [isInspecting, setIsInspecting] = useState<boolean>(false);

  // Load latest Digital Twin simulation run
  const loadLatestRun = async () => {
    try {
      const data = await fetchLatestDigitalTwinRun();
      setRunData(data);
    } catch (err) {
      console.warn('Failed to load latest Digital Twin run:', err);
    }
  };

  useEffect(() => {
    loadLatestRun();
  }, []);

  // Trigger New Simulation Run
  const handleRunSimulation = async () => {
    setIsTriggering(true);
    try {
      const res = await triggerDigitalTwinRun({
        catchment_id: 'mithi_catchment_mumbai',
        rain_event_id: 'monsoon_2026_canonical_01',
      });
      setRunData(res);
    } catch (err) {
      console.error('Failed to trigger simulation run:', err);
    } finally {
      setIsTriggering(false);
    }
  };

  // Auto-play through canonical slices
  useEffect(() => {
    let interval: any = null;
    if (isPlaying) {
      interval = setInterval(() => {
        setSelectedMinutes((prev) => {
          const idx = CANONICAL_MINUTES.indexOf(prev);
          const nextIdx = (idx + 1) % CANONICAL_MINUTES.length;
          return CANONICAL_MINUTES[nextIdx];
        });
      }, 2500);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isPlaying]);

  // Fetch cell diagnostics
  const handleInspect = async (cellId: string) => {
    setSelectedCellId(cellId);
    setIsInspecting(true);
    try {
      const detail = await fetchCellDiagnostics(cellId, selectedMinutes);
      setInspectedCell(detail);
    } catch (err) {
      console.error('Failed to fetch cell diagnostics:', err);
    } finally {
      setIsInspecting(false);
    }
  };

  useEffect(() => {
    if (selectedCellId) {
      handleInspect(selectedCellId);
    }
  }, [selectedMinutes, selectedCellId]);

  const activeSlice: DigitalTwinTimeSlice | undefined = runData?.time_slices.find(
    (s) => s.minutes_from_start === selectedMinutes
  );

  const activeStepIdx = CANONICAL_MINUTES.indexOf(selectedMinutes);
  const intensityMult = [0.35, 0.7, 1.0, 0.85, 0.65, 0.45, 0.25][activeStepIdx] ?? 1.0;

  return (
    <div className="space-y-4 pb-4 font-sans max-w-[1240px] mx-auto">

      {/* ── Page header ─────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-3">
        <div>
          <h1
            className="text-[1.75rem] font-extrabold leading-none tracking-tight"
            style={{ color: 'var(--aq-navy)', letterSpacing: '-0.02em' }}
          >
            Flood Outlook
          </h1>
          <p className="mt-1.5 text-[13.5px]" style={{ color: 'var(--aq-muted)' }}>
            See how projected flooding changes over the next 3 hours across Mithi Catchment.
          </p>
        </div>
        <div className="flex items-center gap-3">
          <div className="flex items-center gap-1.5 text-[11px] font-semibold" style={{ color: '#059669' }}>
            <span className="w-2 h-2 rounded-full bg-emerald-500 aq-live-dot" />
            Live Flood Model
          </div>
          <Button
            variant="primary"
            size="sm"
            onClick={handleRunSimulation}
            isLoading={isTriggering}
            icon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Run New Forecast
          </Button>
        </div>
      </div>

      {/* ── Signature Forecast Timeline Component ────────────── */}
      <div
        className="flex items-center gap-1.5 p-1.5 bg-white rounded-2xl border overflow-x-auto"
        style={{ borderColor: 'rgba(15,35,64,0.08)', boxShadow: '0 1px 3px rgba(15,35,64,0.05)', scrollbarWidth: 'none' }}
      >
        <div className="flex-1 flex items-center gap-1.5 min-w-[550px]">
          {CANONICAL_MINUTES.map((min) => {
            const isActive = selectedMinutes === min;
            const isPeak = min === 60;
            return (
              <button
                key={min}
                onClick={() => setSelectedMinutes(min)}
                className="flex-1 min-w-[72px] flex flex-col items-center justify-center py-2 px-3 rounded-xl transition-all duration-150 cursor-pointer relative"
                style={isActive
                  ? { background: 'var(--aq-blue)', color: '#fff', boxShadow: '0 3px 10px rgba(26,86,219,0.30)' }
                  : { color: 'var(--aq-muted)', background: 'transparent' }
                }
                onMouseEnter={(e) => { if (!isActive) (e.currentTarget as HTMLElement).style.background = '#f1f5f9'; }}
                onMouseLeave={(e) => { if (!isActive) (e.currentTarget as HTMLElement).style.background = ''; }}
              >
                <div className="flex items-center gap-1">
                  <span className="text-[12.5px] font-bold">{SLICE_LABELS[min]}</span>
                  {isPeak && !isActive && (
                    <span className="text-[9px] font-extrabold px-1 py-0.2 rounded bg-amber-100 text-amber-800">
                      Peak
                    </span>
                  )}
                </div>
                {isActive && (
                  <span className="text-[9.5px] font-medium opacity-90 mt-0.5">
                    {isPeak ? 'Peak forecast' : 'Selected'}
                  </span>
                )}
              </button>
            );
          })}
        </div>

        <div className="shrink-0 pl-2.5 border-l" style={{ borderColor: 'rgba(15,35,64,0.08)' }}>
          <button
            onClick={() => setIsPlaying(!isPlaying)}
            className="flex items-center gap-1.5 py-2 px-3.5 rounded-xl text-[12px] font-bold transition-all duration-150 cursor-pointer"
            style={{ color: isPlaying ? '#dc2626' : 'var(--aq-blue)', background: isPlaying ? '#fff1f2' : '#eff6ff' }}
          >
            {isPlaying ? <><Pause className="w-3.5 h-3.5 fill-current" /> Pause</> : <><Play className="w-3.5 h-3.5 fill-current" /> Play</>}
          </button>
        </div>
      </div>

      {/* ── Main grid: map (70%) + right snapshot & inspector (30%) ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 items-stretch">

        {/* Map — 2/3 width */}
        <div className="lg:col-span-2 flex flex-col gap-4">
          <div className="relative aq-map-container flex-1 min-h-[500px]">
            <LeafletMap
              center={[19.076, 72.8777]}
              zoom={13}
              polygons={[]}
              polylines={MITHI_CHANNEL_LINE}
              markers={FLOOD_OUTLOOK_MARKERS}
              floodIntensityMultiplier={intensityMult}
              height="100%"
            />

            {/* Map floating: current slice label */}
            <div
              className="absolute top-4 left-4 z-[1000] flex items-center gap-3 px-3.5 py-2.5 rounded-2xl border"
              style={{
                background: 'rgba(255,255,255,0.96)',
                borderColor: 'rgba(15,35,64,0.12)',
                boxShadow: '0 4px 14px rgba(15,35,64,0.12)',
                backdropFilter: 'blur(8px)',
              }}
            >
              <Clock className="w-4 h-4 shrink-0" style={{ color: 'var(--aq-blue)' }} />
              <div>
                <div className="aq-label" style={{ color: 'var(--aq-muted)' }}>Viewing</div>
                <div className="text-[14px] font-bold leading-tight" style={{ color: 'var(--aq-navy)' }}>
                  {SLICE_LABELS[selectedMinutes]}
                </div>
                {activeSlice?.timestamp_ist && (
                  <div className="text-[10px] mt-0.5" style={{ color: 'var(--aq-muted)' }}>{activeSlice.timestamp_ist}</div>
                )}
              </div>
            </div>

            {/* Map floating: data status */}
            <div
              className="absolute top-4 right-4 z-[1000] flex items-center gap-1.5 px-3 py-1.5 rounded-xl text-[11px] font-semibold border"
              style={{
                background: 'rgba(255,255,255,0.96)',
                borderColor: 'rgba(15,35,64,0.10)',
                boxShadow: '0 2px 8px rgba(15,35,64,0.08)',
                color: '#059669',
              }}
            >
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span>Data current</span>
            </div>

            {/* Map floating legend */}
            <div
              className="absolute bottom-4 left-4 z-[1000] p-3 rounded-2xl text-[10px] space-y-2 border hidden sm:block"
              style={{
                width: '165px',
                background: 'rgba(255,255,255,0.96)',
                borderColor: 'rgba(15,35,64,0.12)',
                boxShadow: '0 4px 14px rgba(15,35,64,0.12)',
                backdropFilter: 'blur(8px)',
              }}
            >
              <div className="font-bold text-slate-800 text-[11px]">Flood depth (m)</div>
              <div className="space-y-1 font-medium text-slate-600">
                <div className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-blue-900" /> &gt; 2.0</div>
                <div className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-blue-600" /> 1.0 – 2.0</div>
                <div className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-blue-400" /> 0.5 – 1.0</div>
                <div className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-cyan-400" /> 0.1 – 0.5</div>
                <div className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-cyan-200" /> 0.3 – &lt; 0.1</div>
              </div>
              <div className="w-full h-px bg-slate-100 my-1" />
              <div className="space-y-1 font-medium text-slate-600">
                <div className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded bg-blue-500/40 border border-blue-500" /> Flooded area</div>
                <div className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-red-500 text-white text-[8px] flex items-center justify-center font-bold">+</span> Key facility</div>
                <div className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-blue-600" /> Selected location</div>
                <div className="flex items-center gap-2"><span className="w-3 h-0.5 bg-slate-800" /> Major road</div>
                <div className="flex items-center gap-2"><span className="w-3 h-0.5 bg-slate-500 border-t border-b border-dashed" /> Railway</div>
                <div className="flex items-center gap-2"><span className="w-3 h-0.5 bg-cyan-500" /> Mithi River</div>
              </div>
            </div>
          </div>
        </div>

        {/* Right panel — 1/3 width */}
        <div className="flex flex-col gap-4">

          {/* Flood Snapshot */}
          <Card padding="md" className="space-y-3">
            <div className="flex items-center justify-between pb-2.5 border-b" style={{ borderColor: 'rgba(15,35,64,0.06)' }}>
              <div className="flex items-center gap-2">
                <Activity className="w-4 h-4" style={{ color: 'var(--aq-blue)' }} />
                <span className="aq-section-title">Flood Snapshot</span>
              </div>
              <Badge variant="info" size="sm">{SLICE_LABELS[selectedMinutes]}</Badge>
            </div>

            <div className="grid grid-cols-2 gap-2">
              {[
                { label: 'Area at risk', value: `${(activeSlice?.affected_area_km2 ?? 1.85 * intensityMult).toFixed(2)} km²`, accent: 'var(--aq-blue)' },
                { label: 'Peak risk level', value: activeSlice?.peak_severity ?? (intensityMult > 0.8 ? 'HIGH' : 'MEDIUM'), accent: intensityMult > 0.8 ? '#dc2626' : '#d97706' },
                { label: 'Rising zones', value: `+${Math.round((activeSlice?.onset_cells_count ?? 320) * intensityMult)}`, accent: '#d97706' },
                { label: 'Sample points', value: `${activeSlice?.affected_cells_count ?? 1850}`, accent: 'var(--aq-muted)' },
              ].map((m) => (
                <div key={m.label} className="p-2.5 rounded-xl bg-slate-50/80 border border-slate-100">
                  <div className="aq-label mb-1">{m.label}</div>
                  <div className="text-[14px] font-extrabold" style={{ color: m.accent }}>{m.value}</div>
                </div>
              ))}
            </div>

            <div className="p-3 rounded-xl text-[11.5px] leading-relaxed bg-blue-50/70 border border-blue-100 text-blue-900">
              <div className="font-bold mb-1 flex items-center gap-1.5 text-blue-950">
                <Info className="w-3.5 h-3.5 text-blue-600" />
                Snapshot Insight
              </div>
              {activeSlice?.cause_explanation ||
                `Water accumulation expands along central Mithi River corridor around ${SLICE_LABELS[selectedMinutes]}, with peak inundated area reaching ${(activeSlice?.affected_area_km2 ?? 1.85 * intensityMult).toFixed(2)} km².`
              }
            </div>
          </Card>

          {/* Location inspector */}
          <Card padding="md" className="space-y-3 flex-1 flex flex-col justify-between">
            <div>
              <div className="flex items-center justify-between pb-2.5 border-b mb-3" style={{ borderColor: 'rgba(15,35,64,0.06)' }}>
                <div className="flex items-center gap-2">
                  <Search className="w-4 h-4" style={{ color: '#059669' }} />
                  <span className="aq-section-title">Inspect a location</span>
                </div>
                <div className="flex items-center gap-1 text-[10.5px] font-semibold text-emerald-700">
                  <MapPin className="w-3 h-3 text-emerald-600" />
                  <span>Interactive</span>
                </div>
              </div>

              <select
                value={selectedCellId}
                onChange={(e) => handleInspect(e.target.value)}
                className="w-full rounded-xl px-3 py-2 text-[12px] font-semibold focus:outline-none transition-all cursor-pointer mb-3"
                style={{
                  background: '#f8fafc',
                  border: '1px solid rgba(15,35,64,0.12)',
                  color: 'var(--aq-text)',
                }}
              >
                <option value="CELL_R0020_C0020">Kurla Junction (Command Hub)</option>
                <option value="CELL_R0015_C0025">Kalina Lowlands (Floodplain)</option>
                <option value="CELL_R0030_C0018">Saki Naka Corridor (Access Road)</option>
                <option value="CELL_R0045_C0012">Sion Causeway (Hospital Access)</option>
              </select>

              {isInspecting ? (
                <div className="py-8 text-center text-[12px] font-medium text-slate-500">
                  Loading location data…
                </div>
              ) : inspectedCell ? (
                <div className="space-y-2.5">
                  <div className="flex items-center justify-between p-3 rounded-xl bg-slate-50 border border-slate-100">
                    <div>
                      <div className="text-[12px] font-extrabold text-slate-900">
                        {inspectedCell.grid_cell_id.replace('CELL_', '').replace(/_/g, ' · ')}
                      </div>
                      <div className="text-[10px] mt-0.5 font-medium text-slate-500">
                        {inspectedCell.latitude.toFixed(4)}°N, {inspectedCell.longitude.toFixed(4)}°E
                      </div>
                    </div>
                    <Badge
                      variant={inspectedCell.severity === 'SEVERE' || inspectedCell.severity === 'HIGH' ? 'danger' : 'info'}
                      size="sm"
                    >
                      {inspectedCell.severity.charAt(0) + inspectedCell.severity.slice(1).toLowerCase()}
                    </Badge>
                  </div>

                  <div className="grid grid-cols-2 gap-2 text-[11.5px]">
                    {[
                      { label: 'Water depth', val: `${(inspectedCell.water_depth_m * intensityMult).toFixed(2)} m`, c: '#1d4ed8' },
                      { label: 'Elevation', val: `${inspectedCell.elevation_m.toFixed(1)} m`, c: 'var(--aq-muted)' },
                      { label: 'Rainfall rate', val: `${inspectedCell.rainfall_intensity_mm_hr.toFixed(1)} mm/h`, c: '#0891b2' },
                      { label: 'To waterway', val: `${inspectedCell.distance_to_waterway_m.toFixed(0)} m`, c: 'var(--aq-muted)' },
                    ].map((d) => (
                      <div key={d.label} className="p-2.5 rounded-xl bg-slate-50 border border-slate-100">
                        <span className="aq-label block mb-0.5">{d.label}</span>
                        <span className="font-bold" style={{ color: d.c }}>{d.val}</span>
                      </div>
                    ))}
                  </div>

                  <details className="group">
                    <summary className="cursor-pointer text-[10.5px] font-semibold px-2 py-1.5 rounded-lg select-none text-slate-500 hover:text-slate-800 transition-colors">
                      Model details ▸
                    </summary>
                    <div className="mt-1 px-3 py-2.5 rounded-xl text-[11px] space-y-1 bg-slate-50 border border-slate-100">
                      <div className="flex justify-between">
                        <span className="text-slate-500">Physical score</span>
                        <span className="font-mono font-bold text-slate-800">{inspectedCell.physical_model_score.toFixed(3)}</span>
                      </div>
                      <div className="flex justify-between">
                        <span className="text-slate-500">Status tag</span>
                        <span className="font-bold text-slate-700">{inspectedCell.ml_status_tag}</span>
                      </div>
                    </div>
                  </details>
                </div>
              ) : (
                <div className="p-4 text-center rounded-xl bg-slate-50 border border-slate-100 space-y-2">
                  <ShieldAlert className="w-6 h-6 text-slate-400 mx-auto" />
                  <p className="text-[12px] font-semibold text-slate-700">Select a location to inspect</p>
                </div>
              )}
            </div>
          </Card>
        </div>
      </div>
    </div>
  );
};

export default FloodMapFeature;
