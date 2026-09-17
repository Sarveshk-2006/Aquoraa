import React, { useState, useEffect } from 'react';
import {
  Clock,
  AlertTriangle,
  RefreshCw,
  CheckCircle2,
  XCircle,
  HelpCircle,
  ShieldCheck,
  ArrowRight,
  Play,
  Pause,
  Compass,
  AlertCircle,
} from 'lucide-react';
import { LeafletMap, MapPolylineItem } from '@/map/LeafletMap';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import {
  analyzeFloodAwareRoutes,
  RouteAnalysisResponse,
  RouteCandidate,
} from '@/api/routing';

const PRESETS = [
  {
    name: 'Kurla Junction → Saki Naka Corridor',
    origin: { latitude: 19.0760, longitude: 72.8777, label: 'Kurla Junction' },
    destination: { latitude: 19.1020, longitude: 72.8850, label: 'Saki Naka Corridor' },
  },
  {
    name: 'Kalina Lowlands → Sion Causeway',
    origin: { latitude: 19.0700, longitude: 72.8680, label: 'Kalina Lowlands' },
    destination: { latitude: 19.0450, longitude: 72.8600, label: 'Sion Causeway' },
  },
];

const SEVERITY_COLORS: Record<string, string> = {
  DRY: '#059669',
  LOW: '#0284c7',
  MODERATE: '#d97706',
  HIGH: '#ea580c',
  SEVERE: '#dc2626',
  UNKNOWN: '#64748b',
};

const RECOMMENDATION_STYLES: Record<string, { badge: 'success' | 'warning' | 'danger' | 'neutral'; text: string; icon: any }> = {
  GO_NOW: {
    badge: 'success',
    text: 'Clear / Low Exposure',
    icon: CheckCircle2,
  },
  ALTERNATE_RECOMMENDED: {
    badge: 'warning',
    text: 'Alternate Route Recommended',
    icon: AlertTriangle,
  },
  AVOID: {
    badge: 'danger',
    text: 'High Exposure / Impassable',
    icon: XCircle,
  },
  UNKNOWN: {
    badge: 'neutral',
    text: 'Route Analysis Complete',
    icon: HelpCircle,
  },
};

export const TravelWindowFeature: React.FC = () => {
  const [selectedPresetIndex, setSelectedPresetIndex] = useState<number>(0);
  const [originLat, setOriginLat] = useState<number>(PRESETS[0].origin.latitude);
  const [originLon, setOriginLon] = useState<number>(PRESETS[0].origin.longitude);
  const [destLat, setDestLat] = useState<number>(PRESETS[0].destination.latitude);
  const [destLon, setDestLon] = useState<number>(PRESETS[0].destination.longitude);

  const [routingData, setRoutingData] = useState<RouteAnalysisResponse | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [hasError, setHasError] = useState<boolean>(false);
  const [selectedCandidateId, setSelectedCandidateId] = useState<string>('');
  const [selectedTimeSlice, setSelectedTimeSlice] = useState<number>(60);
  const [isPlaying, setIsPlaying] = useState<boolean>(false);

  // Real Backend Trigger Route Analysis
  const handleAnalyze = async () => {
    setIsAnalyzing(true);
    setHasError(false);
    try {
      const res = await analyzeFloodAwareRoutes({
        origin: { latitude: originLat, longitude: originLon, label: PRESETS[selectedPresetIndex]?.origin.label || 'Origin' },
        destination: { latitude: destLat, longitude: destLon, label: PRESETS[selectedPresetIndex]?.destination.label || 'Destination' },
        max_acceptable_severity: 'HIGH',
        max_alternatives: 3,
      });
      setRoutingData(res);
      if (res?.candidates && res.candidates.length > 0) {
        setSelectedCandidateId(res.recommended_route_id || res.candidates[0].route_id);
      }
    } catch (err) {
      console.error('Failed to analyze flood-aware routes from backend:', err);
      setRoutingData(null);
      setHasError(true);
    } finally {
      setIsAnalyzing(false);
    }
  };

  const handlePresetSelect = (idx: number) => {
    setSelectedPresetIndex(idx);
    const p = PRESETS[idx];
    setOriginLat(p.origin.latitude);
    setOriginLon(p.origin.longitude);
    setDestLat(p.destination.latitude);
    setDestLon(p.destination.longitude);
    // Reset previous analysis result so user explicitly triggers or sees clean state
    setRoutingData(null);
    setHasError(false);
  };

  // Playback timer for timeline slice
  const canonicalSlices = [0, 30, 60, 90, 120, 150, 180];
  useEffect(() => {
    let interval: any = null;
    if (isPlaying) {
      interval = setInterval(() => {
        setSelectedTimeSlice((prev) => {
          const idx = canonicalSlices.indexOf(prev);
          const nextIdx = (idx + 1) % canonicalSlices.length;
          return canonicalSlices[nextIdx];
        });
      }, 2500);
    }
    return () => {
      if (interval) clearInterval(interval);
    };
  }, [isPlaying]);

  const activeCandidate: RouteCandidate | undefined = routingData?.candidates?.find(
    (c) => c.route_id === selectedCandidateId
  ) || routingData?.candidates?.[0];

  const recStyle = routingData
    ? RECOMMENDATION_STYLES[routingData.recommendation] || RECOMMENDATION_STYLES.UNKNOWN
    : RECOMMENDATION_STYLES.UNKNOWN;
  const RecIcon = recStyle.icon;

  // Build Polylines ONLY from real backend data or river baseline
  const polylines: MapPolylineItem[] = [
    {
      id: 'mithi-river-corridor',
      positions: [
        [19.102, 72.885],
        [19.088, 72.880],
        [19.072, 72.872],
        [19.055, 72.860],
        [19.040, 72.850],
      ] as [number, number][],
      color: '#06b6d4',
      weight: 3,
      dashArray: '4, 4',
      opacity: 0.7,
      title: 'Mithi River Corridor',
    },
  ];

  // Render ONLY real candidate routes returned by the backend
  if (routingData?.candidates && routingData.candidates.length > 0) {
    routingData.candidates.forEach((cand, i) => {
      const isSelected = cand.route_id === selectedCandidateId;
      const rawCoords = cand.geometry_geojson?.coordinates;

      if (rawCoords && Array.isArray(rawCoords) && rawCoords.length > 0) {
        const coords: [number, number][] = rawCoords.map(([lon, lat]) => [lat, lon] as [number, number]);

        polylines.push({
          id: `route-cand-${cand.route_id}`,
          positions: coords,
          color: isSelected
            ? (cand.recommendation === 'AVOID' ? '#dc2626' : '#0284c7')
            : '#94a3b8',
          weight: isSelected ? 6 : 3,
          dashArray: isSelected ? undefined : '5, 5',
          opacity: isSelected ? 0.95 : 0.6,
          title: cand.summary || `Route Candidate ${i + 1}`,
        });
      }
    });
  }

  const mapMarkers = [
    {
      id: 'origin',
      position: [originLat, originLon] as [number, number],
      title: PRESETS[selectedPresetIndex]?.origin.label || 'Origin',
      subtitle: 'Origin A',
      color: '#059669',
      badge: 'A',
    },
    {
      id: 'dest',
      position: [destLat, destLon] as [number, number],
      title: PRESETS[selectedPresetIndex]?.destination.label || 'Destination',
      subtitle: 'Destination B',
      color: '#0f2340',
      badge: 'B',
    },
  ];

  const formatOnset = (onset: number | null | undefined): string => {
    if (typeof onset === 'number' && !isNaN(onset)) {
      return `+${onset} min`;
    }
    return 'No modeled threat';
  };

  const formatUsableWindow = (windowMin: number | null | undefined): string => {
    if (typeof windowMin === 'number' && !isNaN(windowMin)) {
      return `${windowMin} min`;
    }
    return 'No flood onset detected';
  };

  const intensityMult = [0.35, 0.7, 1.0, 0.85, 0.65, 0.45, 0.25][canonicalSlices.indexOf(selectedTimeSlice)] ?? 1.0;

  return (
    <div className="space-y-4 pb-4 font-sans max-w-[1240px] mx-auto">

      {/* ── Page Header ─────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-3">
        <div>
          <h1
            className="text-[1.75rem] font-extrabold leading-none tracking-tight"
            style={{ color: 'var(--aq-navy)', letterSpacing: '-0.02em' }}
          >
            Travel Window
          </h1>
          <p className="mt-1.5 text-[13.5px]" style={{ color: 'var(--aq-muted)' }}>
            How long can this route remain safely usable before flooding causes disruption?
          </p>
        </div>
        <div className="flex items-center gap-3">
          {routingData && (
            <div className="flex items-center gap-1.5 text-[11px] font-semibold text-emerald-700 bg-emerald-50 px-2.5 py-1 rounded-xl border border-emerald-200">
              <CheckCircle2 className="w-3.5 h-3.5 text-emerald-600" />
              <span>Backend Analysis Complete</span>
            </div>
          )}
          <Button
            variant="primary"
            size="sm"
            onClick={handleAnalyze}
            isLoading={isAnalyzing}
            icon={<RefreshCw className="w-3.5 h-3.5" />}
          >
            Analyse Routes
          </Button>
        </div>
      </div>

      {/* ── Route Selector Bar ───────────────────────────────── */}
      <Card padding="sm">
        <div className="flex flex-col lg:flex-row items-start lg:items-center justify-between gap-3">
          {/* Preset Corridor Selector */}
          <div className="flex items-center gap-2 flex-wrap">
            <span className="aq-label shrink-0 mr-1">Corridor</span>
            {PRESETS.map((p, idx) => (
              <button
                key={p.name}
                onClick={() => handlePresetSelect(idx)}
                className="px-3 py-1.5 text-[12px] font-bold rounded-xl transition-all duration-150 cursor-pointer flex items-center gap-1.5"
                style={selectedPresetIndex === idx
                  ? { background: 'var(--aq-blue)', color: '#fff', boxShadow: '0 2px 8px rgba(26,86,219,0.28)' }
                  : { background: '#f8fafc', color: 'var(--aq-muted)', border: '1px solid rgba(15,35,64,0.10)' }
                }
              >
                <span className="w-2 h-2 rounded-full" style={{ background: selectedPresetIndex === idx ? '#38bdf8' : '#94a3b8' }} />
                <span>{p.name}</span>
              </button>
            ))}
          </div>

          {/* Advanced coordinates (collapsed single-line) */}
          <details className="group">
            <summary
              className="cursor-pointer text-[11px] font-semibold select-none text-slate-500 hover:text-slate-800 transition-colors"
            >
              ▸ Advanced: custom coordinates
            </summary>
            <div className="mt-2.5 p-3 bg-slate-50 rounded-xl border border-slate-100 grid grid-cols-2 md:grid-cols-4 gap-2">
              {[
                { label: 'Origin Lat', val: originLat, setter: (v: number) => setOriginLat(v) },
                { label: 'Origin Lon', val: originLon, setter: (v: number) => setOriginLon(v) },
                { label: 'Dest. Lat',  val: destLat,   setter: (v: number) => setDestLat(v)   },
                { label: 'Dest. Lon',  val: destLon,   setter: (v: number) => setDestLon(v)   },
              ].map((f) => (
                <div key={f.label}>
                  <label className="aq-label block mb-1">{f.label}</label>
                  <input
                    type="number"
                    step="0.0001"
                    value={f.val}
                    onChange={(e) => f.setter(parseFloat(e.target.value) || 0)}
                    className="w-full rounded-lg px-2.5 py-1.5 text-[11.5px] font-semibold focus:outline-none bg-white border border-slate-200 text-slate-900"
                  />
                </div>
              ))}
            </div>
          </details>
        </div>
      </Card>

      {/* ── Main Grid: Map (~68%) + Route Status (~32%) ──────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 items-stretch">

        {/* Route Map — 2/3 width */}
        <div className="lg:col-span-2 flex flex-col gap-3">
          {/* Origin -> Destination Pill Header */}
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2 text-[12.5px] font-bold">
              <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-emerald-50 text-emerald-800 border border-emerald-200">
                <span className="w-2 h-2 rounded-full bg-emerald-500" />
                {PRESETS[selectedPresetIndex]?.origin.label || 'Origin'}
              </span>
              <ArrowRight className="w-3.5 h-3.5 text-slate-400" />
              <span className="flex items-center gap-1.5 px-3 py-1 rounded-full bg-slate-900 text-white shadow-xs">
                <span className="w-2 h-2 rounded-full bg-blue-400" />
                {PRESETS[selectedPresetIndex]?.destination.label || 'Destination'}
              </span>
            </div>
            <div className="text-[11px] font-medium text-slate-500 hidden sm:block">
              {routingData ? 'Displaying OSRM geometry & digital twin flood extent' : 'Ready to analyse corridor'}
            </div>
          </div>

          {/* Map Surface */}
          <div className="aq-map-container relative flex-1 min-h-[480px]">
            <LeafletMap
              center={[
                (originLat + destLat) / 2,
                (originLon + destLon) / 2,
              ]}
              zoom={13}
              polylines={polylines}
              markers={mapMarkers}
              floodIntensityMultiplier={intensityMult}
              height="100%"
            />

            {/* Floating legend overlay */}
            <div
              className="absolute bottom-4 left-4 z-[1000] p-3 rounded-2xl text-[10.5px] space-y-2 border hidden sm:block"
              style={{
                width: '175px',
                background: 'rgba(255,255,255,0.96)',
                borderColor: 'rgba(15,35,64,0.12)',
                boxShadow: '0 4px 14px rgba(15,35,64,0.12)',
                backdropFilter: 'blur(8px)',
              }}
            >
              <div className="font-bold text-slate-800 text-[11px]">Route & Risk Scale</div>
              <div className="space-y-1 font-semibold text-slate-700">
                <div className="flex items-center gap-2"><span className="w-4 h-1 rounded bg-blue-600" /> Primary route</div>
                <div className="flex items-center gap-2"><span className="w-4 h-0.5 rounded bg-slate-400 border-t border-b border-dashed" /> Alternate route</div>
                <div className="flex items-center gap-2"><span className="w-4 h-0.5 rounded bg-cyan-500" /> Mithi River</div>
              </div>
              <div className="w-full h-px bg-slate-100 my-1" />
              <div className="space-y-1 font-medium text-slate-600">
                <div className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-emerald-600" /> Clear / Low</div>
                <div className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-amber-500" /> Moderate</div>
                <div className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-red-600" /> High / Severe</div>
              </div>
            </div>
          </div>
        </div>

        {/* Right Panel: Route Status & Travel Window Card — 1/3 width */}
        <div className="flex flex-col gap-4">

          {/* Real Backend Route Card */}
          <Card padding="md" className="space-y-4 flex-1 flex flex-col justify-between">
            {isAnalyzing ? (
              <div className="py-12 flex flex-col items-center justify-center text-center space-y-3">
                <RefreshCw className="w-8 h-8 text-blue-600 animate-spin" />
                <div>
                  <h3 className="text-[14px] font-bold text-slate-900">Analysing route exposure…</h3>
                  <p className="text-[11.5px] text-slate-500 mt-1">Executing OSRM routing and Digital Twin flood analysis</p>
                </div>
              </div>
            ) : hasError ? (
              <div className="py-8 flex flex-col items-center justify-center text-center space-y-3">
                <AlertCircle className="w-8 h-8 text-red-500" />
                <div>
                  <h3 className="text-[14px] font-bold text-slate-900">Route analysis unavailable</h3>
                  <p className="text-[11.5px] text-slate-500 mt-1">Unable to connect to backend routing service.</p>
                </div>
                <Button variant="outline" size="sm" onClick={handleAnalyze}>
                  Try again
                </Button>
              </div>
            ) : routingData && activeCandidate ? (
              <div>
                {/* Status Header */}
                <div className="flex items-center justify-between pb-3 border-b border-slate-100 mb-3">
                  <div className="flex items-center gap-2">
                    <div className="w-8 h-8 rounded-xl bg-blue-50 flex items-center justify-center shrink-0">
                      <RecIcon className="w-4.5 h-4.5 text-blue-600" />
                    </div>
                    <div>
                      <div className="aq-label">Route Condition</div>
                      <div className="text-[14px] font-bold text-slate-900">{recStyle.text}</div>
                    </div>
                  </div>
                  {(routingData.recommended_route_id === activeCandidate.route_id || activeCandidate.recommendation === 'GO_NOW') && (
                    <Badge variant={recStyle.badge} size="sm">Recommended</Badge>
                  )}
                </div>

                {/* Real Travel Window Highlight Box */}
                <div
                  className="p-4 rounded-2xl text-center space-y-1 mb-4"
                  style={{
                    background: 'linear-gradient(135deg, #eff6ff 0%, #dbeafe 100%)',
                    border: '1px solid #bfdbfe',
                    boxShadow: '0 2px 8px rgba(26,86,219,0.08)',
                  }}
                >
                  <div className="text-[10px] uppercase font-bold tracking-wider text-blue-800">
                    TRAVEL WINDOW
                  </div>
                  <div className="text-[1.85rem] font-extrabold text-blue-900 leading-none tracking-tight">
                    {formatUsableWindow(activeCandidate.travel_window?.usable_travel_window_min)}
                  </div>
                  <p className="text-[11px] text-blue-700 font-medium">
                    {typeof activeCandidate.travel_window?.route_flood_onset_min === 'number'
                      ? `Model predicts flood onset along segment at +${activeCandidate.travel_window.route_flood_onset_min} min.`
                      : 'No flood onset predicted along this route geometry.'}
                  </p>
                </div>

                {/* Details Metrics */}
                <div className="space-y-2">
                  {[
                    { label: 'Route Distance', val: `${(activeCandidate.distance_m / 1000).toFixed(2)} km` },
                    { label: 'Est. Travel Time', val: `${(activeCandidate.travel_window?.estimated_travel_time_min ?? (activeCandidate.estimated_duration_s / 60)).toFixed(1)} min` },
                    { label: 'Flood Onset Time', val: formatOnset(activeCandidate.travel_window?.route_flood_onset_min) },
                    { label: 'Status Tag', val: activeCandidate.travel_window?.status || activeCandidate.recommendation || 'NORMAL' },
                  ].map((row) => (
                    <div key={row.label} className="flex items-center justify-between text-[12px] py-1.5 border-b border-slate-100 last:border-b-0">
                      <span className="text-slate-500 font-medium">{row.label}</span>
                      <span className="font-extrabold text-slate-800">{row.val}</span>
                    </div>
                  ))}
                </div>

                {/* Explanation Box - ONLY if backend provides explanation */}
                {(routingData.explanation || activeCandidate.explanation) && (
                  <div className="mt-4 p-3 rounded-xl bg-slate-50 border border-slate-100 text-[11.5px] leading-relaxed text-slate-700">
                    <div className="font-bold mb-1 flex items-center gap-1.5 text-slate-900">
                      <ShieldCheck className="w-3.5 h-3.5 text-blue-600" />
                      Backend Analysis Note
                    </div>
                    {routingData.explanation || activeCandidate.explanation}
                  </div>
                )}
              </div>
            ) : (
              /* Clean Ready / Empty State before analysis */
              <div className="py-10 flex flex-col items-center justify-center text-center space-y-3">
                <Compass className="w-10 h-10 text-slate-400" />
                <div>
                  <h3 className="text-[14px] font-bold text-slate-900">Ready to Analyse Route</h3>
                  <p className="text-[11.5px] text-slate-500 mt-1 max-w-[220px] mx-auto leading-relaxed">
                    Select a corridor above and tap <strong>Analyse Routes</strong> to evaluate real-time OSRM routing and flood exposure.
                  </p>
                </div>
                <Button variant="primary" size="sm" onClick={handleAnalyze}>
                  Analyse Routes
                </Button>
              </div>
            )}
          </Card>
        </div>
      </div>

      {/* ── Lower Section: Forecast Timeline & Route Options Comparison ── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4">

        {/* Exposure Timeline — 2/3 width */}
        <Card padding="md" className="lg:col-span-2 space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <div className="flex items-center gap-2">
              <Clock className="w-4 h-4 text-blue-600" />
              <span className="aq-section-title">Route Exposure Timeline</span>
              <span className="text-[11px] text-slate-500 hidden sm:inline">% route segment affected by timestep</span>
            </div>
            <button
              onClick={() => setIsPlaying(!isPlaying)}
              className="flex items-center gap-1 px-2.5 py-1 rounded-lg text-[11px] font-bold text-blue-600 bg-blue-50 hover:bg-blue-100 transition-colors cursor-pointer"
            >
              {isPlaying ? <><Pause className="w-3 h-3 fill-current" /> Pause</> : <><Play className="w-3 h-3 fill-current" /> Play</>}
            </button>
          </div>

          {activeCandidate?.time_slice_exposures && activeCandidate.time_slice_exposures.length > 0 ? (
            <div className="grid grid-cols-7 gap-2">
              {activeCandidate.time_slice_exposures.slice(0, 7).map((exposure) => {
                const pct = Math.min(exposure.affected_percentage || 0, 100);
                const sColor = SEVERITY_COLORS[exposure.peak_severity] || '#059669';
                const isSelectedTime = selectedTimeSlice === exposure.minutes_from_start;
                return (
                  <button
                    key={exposure.minutes_from_start}
                    onClick={() => setSelectedTimeSlice(exposure.minutes_from_start)}
                    className={`p-2 rounded-xl text-center flex flex-col items-center gap-1.5 transition-all cursor-pointer ${
                      isSelectedTime ? 'ring-2 ring-blue-600 bg-blue-50/50' : 'bg-slate-50 hover:bg-slate-100'
                    }`}
                  >
                    <span className="text-[10.5px] font-extrabold text-slate-700">
                      {exposure.minutes_from_start === 0 ? 'NOW' : `+${exposure.minutes_from_start}m`}
                    </span>
                    <div className="w-full h-1.5 rounded-full bg-slate-200 overflow-hidden">
                      <div className="h-full rounded-full transition-all duration-300" style={{ width: `${Math.max(pct, 4)}%`, background: sColor }} />
                    </div>
                    <span className="text-[10px] font-bold" style={{ color: sColor }}>
                      {pct > 0 ? `${pct.toFixed(0)}%` : 'Clear'}
                    </span>
                  </button>
                );
              })}
            </div>
          ) : (
            <div className="py-6 text-center text-[11.5px] text-slate-500 font-medium">
              Analyse routes to view forecast timestep segment exposure.
            </div>
          )}
        </Card>

        {/* Route Candidates Options — 1/3 width */}
        <Card padding="md" className="space-y-3">
          <div className="flex items-center justify-between pb-2 border-b border-slate-100">
            <span className="aq-section-title">Route Comparison</span>
            <span className="text-[10.5px] font-medium text-slate-500">
              {routingData?.candidates?.length || 0} candidate(s)
            </span>
          </div>

          <div className="space-y-2">
            {routingData?.candidates && routingData.candidates.length > 0 ? (
              routingData.candidates.map((cand, idx) => {
                const isSelected = selectedCandidateId === cand.route_id;
                const cStyle = RECOMMENDATION_STYLES[cand.recommendation] || RECOMMENDATION_STYLES.UNKNOWN;
                const isRec = cand.route_id === routingData.recommended_route_id;

                return (
                  <button
                    key={cand.route_id}
                    onClick={() => setSelectedCandidateId(cand.route_id)}
                    className={`w-full p-3 rounded-xl text-left transition-all flex flex-col gap-1.5 cursor-pointer border ${
                      isSelected
                        ? 'bg-blue-50/60 border-blue-300 shadow-xs'
                        : 'bg-white border-slate-200 hover:border-slate-300'
                    }`}
                  >
                    <div className="flex items-center justify-between">
                      <span className="text-[12px] font-bold text-slate-900 truncate max-w-[140px]">
                        {cand.summary || (idx === 0 ? 'Primary Route' : `Alternate ${idx}`)}
                      </span>
                      {isRec ? (
                        <Badge variant="success" size="sm">Recommended</Badge>
                      ) : (
                        <Badge variant={cStyle.badge} size="sm">{cStyle.text}</Badge>
                      )}
                    </div>
                    <div className="flex items-center justify-between text-[11px] text-slate-500">
                      <span>{(cand.distance_m / 1000).toFixed(2)} km</span>
                      <span className="font-bold text-blue-700">
                        {formatUsableWindow(cand.travel_window?.usable_travel_window_min)}
                      </span>
                    </div>
                  </button>
                );
              })
            ) : (
              <div className="py-4 text-center text-[11.5px] text-slate-500 font-medium">
                Analyse routes to compare available candidate paths.
              </div>
            )}
          </div>
        </Card>
      </div>
    </div>
  );
};

export default TravelWindowFeature;
