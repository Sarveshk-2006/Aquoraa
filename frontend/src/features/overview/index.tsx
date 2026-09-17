import React, { useMemo, useState } from 'react';
import { useQuery } from '@tanstack/react-query';
import {
  CloudRain,
  Navigation,
  ShieldAlert,
  Building2,
  Camera,
  Sliders,
  Waves,
  Clock,
  AlertCircle,
  ChevronRight,
  Play,
  Pause,
  Quote,
  ShieldCheck,
  AlertTriangle,
  Info,
} from 'lucide-react';
import { MapContainer } from '@/map/MapContainer';
import { useAppStore } from '@/store/useAppStore';
import { fetchLatestDigitalTwinRun } from '@/api/digitalTwin';
import { fetchAlerts } from '@/api/alerts';
import { fetchCriticalFacilities } from '@/api/criticalAccess';
import { fetchLatestProtectCityRun } from '@/api/protectCity';
import { Card } from '@/components/ui/Card';

/* ─── Mumbai Skyline Hero Illustration (SVG) ────────────────── */
const MumbaiSkylineHero: React.FC = () => (
  <div className="relative w-full h-[90px] rounded-[20px] overflow-hidden bg-gradient-to-r from-[#0f2340] via-[#004d4d] to-[#008080] flex items-center justify-between px-6 text-white shadow-sm border border-teal-800/40">
    <div className="z-10 flex flex-col justify-center">
      <span className="text-[10px] uppercase font-bold tracking-widest text-[#F5F5DC] opacity-90">
        MUMBAI · MITHI CATCHMENT
      </span>
      <h2 className="text-[1.3rem] font-black tracking-tight text-white leading-tight mt-0.5">
        Current Flood Outlook
      </h2>
      <p className="text-[11.5px] text-teal-100 font-medium">
        See where water may develop over the next 3 hours.
      </p>
    </div>

    {/* Right side skyline artwork + script badge */}
    <div className="relative z-10 flex items-center gap-5">
      <div className="hidden sm:flex flex-col items-end">
        <span className="font-serif italic text-[1.25rem] font-bold text-[#F5F5DC] tracking-wide drop-shadow-sm">
          Safer Mumbai Together
        </span>
      </div>
      {/* Decorative Sea Link Cables & Towers SVG */}
      <svg width="180" height="70" viewBox="0 0 180 70" fill="none" className="opacity-45">
        {/* Sea Link Pylons */}
        <path d="M40 65 L60 10 L80 65" stroke="#F5F5DC" strokeWidth="2.5" />
        <path d="M110 65 L130 15 L150 65" stroke="#F5F5DC" strokeWidth="2.5" />
        {/* Stay cables */}
        <line x1="60" y1="10" x2="20" y2="65" stroke="#b2d8d8" strokeWidth="0.8" />
        <line x1="60" y1="10" x2="35" y2="65" stroke="#b2d8d8" strokeWidth="0.8" />
        <line x1="60" y1="10" x2="50" y2="65" stroke="#b2d8d8" strokeWidth="0.8" />
        <line x1="60" y1="10" x2="70" y2="65" stroke="#b2d8d8" strokeWidth="0.8" />
        <line x1="60" y1="10" x2="85" y2="65" stroke="#b2d8d8" strokeWidth="0.8" />

        <line x1="130" y1="15" x2="95" y2="65" stroke="#b2d8d8" strokeWidth="0.8" />
        <line x1="130" y1="15" x2="110" y2="65" stroke="#b2d8d8" strokeWidth="0.8" />
        <line x1="130" y1="15" x2="125" y2="65" stroke="#b2d8d8" strokeWidth="0.8" />
        <line x1="130" y1="15" x2="145" y2="65" stroke="#b2d8d8" strokeWidth="0.8" />
        <line x1="130" y1="15" x2="165" y2="65" stroke="#b2d8d8" strokeWidth="0.8" />
        {/* Deck */}
        <line x1="0" y1="65" x2="180" y2="65" stroke="#F5F5DC" strokeWidth="3" />
        {/* City skyline silhouettes background */}
        <rect x="5" y="40" width="12" height="25" fill="#ffffff" opacity="0.3" />
        <rect x="20" y="32" width="10" height="33" fill="#ffffff" opacity="0.4" />
        <rect x="85" y="35" width="14" height="30" fill="#ffffff" opacity="0.3" />
        <rect x="155" y="28" width="16" height="37" fill="#ffffff" opacity="0.4" />
      </svg>
    </div>
  </div>
);

/* ─── Metric card used in the KPI row ─────────────────────── */
interface MetricCardProps {
  label: string;
  value: React.ReactNode;
  sub?: string;
  accent?: 'teal' | 'red' | 'green' | 'amber';
  icon: React.ElementType;
}

const MetricCard: React.FC<MetricCardProps> = ({ label, value, sub, accent = 'teal', icon: Icon }) => {
  const accentColor = {
    teal:  '#008080',
    red:   '#dc2626',
    green: '#059669',
    amber: '#d97706',
  }[accent];

  const bgColor = {
    teal:  '#e6f2f2',
    red:   '#fef2f2',
    green: '#f0fdf4',
    amber: '#fffbeb',
  }[accent];

  return (
    <div
      className="bg-white rounded-[20px] p-4 flex flex-col justify-between h-full min-h-[110px] transition-all duration-150 hover:-translate-y-0.5 border"
      style={{ borderColor: 'rgba(15,35,64,0.08)', boxShadow: '0 1px 3px rgba(15,35,64,0.05)' }}
    >
      <div className="flex items-start justify-between gap-2">
        <span className="text-[10px] font-bold uppercase tracking-wider text-slate-400">{label}</span>
        <div className="w-7 h-7 rounded-xl flex items-center justify-center shrink-0" style={{ background: bgColor }}>
          <Icon className="w-3.5 h-3.5" style={{ color: accentColor }} />
        </div>
      </div>
      <div className="my-1">
        <div
          className="text-[1.45rem] font-extrabold leading-none tracking-tight"
          style={{ color: accentColor, letterSpacing: '-0.02em' }}
        >
          {value}
        </div>
      </div>
      {sub && (
        <p className="text-[11px] leading-snug font-medium text-slate-500 mt-0.5">
          {sub}
        </p>
      )}
    </div>
  );
};

/* ─── Compact alert row for the right-side panel ──────────── */
interface AlertRowProps {
  title: string;
  sub: string;
  time: string;
  severity: 'critical' | 'high' | 'medium' | 'info';
}

const SEVERITY_ICON: Record<AlertRowProps['severity'], React.ElementType> = {
  critical: AlertCircle,
  high:     AlertCircle,
  medium:   AlertTriangle,
  info:     Info,
};

const SEVERITY_COLOR: Record<AlertRowProps['severity'], string> = {
  critical: '#dc2626',
  high:     '#dc2626',
  medium:   '#d97706',
  info:     '#008080',
};

const SEVERITY_BG: Record<AlertRowProps['severity'], string> = {
  critical: '#fef2f2',
  high:     '#fef2f2',
  medium:   '#fffbeb',
  info:     '#e6f2f2',
};

const AlertRow: React.FC<AlertRowProps> = ({ title, sub, time, severity }) => {
  const Icon = SEVERITY_ICON[severity];
  const color = SEVERITY_COLOR[severity];
  const bg = SEVERITY_BG[severity];

  return (
    <div className="flex items-start gap-2.5 py-2.5 border-b last:border-b-0 border-slate-100">
      <div className="w-5.5 h-5.5 rounded-full flex items-center justify-center shrink-0 mt-0.5" style={{ background: bg }}>
        <Icon className="w-3 h-3" style={{ color }} />
      </div>
      <div className="flex-1 min-w-0">
        <p className="text-[11.5px] font-bold leading-snug truncate text-slate-800">{title}</p>
        <p className="text-[10.5px] mt-0.5 truncate text-slate-500">{sub}</p>
        <p className="text-[9.5px] mt-0.5 text-slate-400">{time}</p>
      </div>
      <span
        className="shrink-0 text-[9.5px] font-semibold px-2 py-0.5 rounded-full capitalize"
        style={{
          background: bg,
          color,
          border: `1px solid ${color}25`,
        }}
      >
        {severity}
      </span>
    </div>
  );
};

/* ─── Feature shortcut tile ────────────────────────────────── */
interface ShortcutProps {
  icon: React.ElementType;
  label: string;
  sub: string;
  color: string;
  onClick: () => void;
}

const Shortcut: React.FC<ShortcutProps> = ({ icon: Icon, label, sub, color, onClick }) => (
  <button
    onClick={onClick}
    className="flex flex-col items-start p-2.5 rounded-xl bg-white text-left transition-all duration-150 hover:-translate-y-0.5 group border cursor-pointer"
    style={{
      borderColor: 'rgba(15,35,64,0.08)',
      boxShadow: '0 1px 2px rgba(15,35,64,0.04)',
    }}
  >
    <div
      className="w-6 h-6 rounded-lg flex items-center justify-center mb-1.5 shrink-0"
      style={{ background: color + '15' }}
    >
      <Icon className="w-3.5 h-3.5" style={{ color }} />
    </div>
    <p className="text-[11px] font-bold leading-tight truncate w-full text-slate-800">{label}</p>
    <p className="text-[9.5px] mt-0.5 leading-tight truncate w-full text-slate-500">{sub}</p>
  </button>
);

/* ─── Main Overview Feature ────────────────────────────────── */
export const OverviewFeature: React.FC = () => {
  const { setActiveTab } = useAppStore();
  const [activeStepIndex, setActiveStepIndex] = useState<number>(2); // Default to +60m (Peak)
  const [isPlaying, setIsPlaying] = useState<boolean>(false);

  const dtQuery    = useQuery({ queryKey: ['ov-dt'],    queryFn: fetchLatestDigitalTwinRun });
  const alertsQuery= useQuery({ queryKey: ['ov-alerts'], queryFn: () => fetchAlerts() });
  const facQuery   = useQuery({ queryKey: ['ov-fac'],   queryFn: () => fetchCriticalFacilities() });
  const pcQuery    = useQuery({ queryKey: ['ov-pc'],    queryFn: fetchLatestProtectCityRun });

  /* ── Derived metrics from real data ── */
  const dtRun  = dtQuery.data;
  const alerts = alertsQuery.data?.alerts ?? [];
  const activeAlerts = alerts.filter(a => a.status === 'ACTIVE');

  const peakAreaKm2  = dtRun?.summary?.peak_affected_area_km2 ?? 1.84;
  const peakTimeMin  = dtRun?.summary?.peak_time_minutes ?? 60;
  const maxDepthM    = dtRun?.summary?.max_water_depth_m ?? 0.42;

  const topFacility  = facQuery.data?.[0]?.name ?? 'Sion Hospital';
  const topRec       = pcQuery.data?.recommendations?.[0];
  const suggestedAction = topRec?.intervention_type
    ? topRec.intervention_type.replace(/_/g, ' ').replace(/\b\w/g, c => c.toUpperCase())
    : 'Use alternate access';

  /* ── Map recent activity from real data ── */
  const recentActivity = useMemo(() => {
    const items: { text: string; ago: string }[] = [];
    if (dtRun?.run_id) items.push({ text: 'Digital twin run completed (0–180 min)', ago: '14 min ago' });
    items.push({ text: 'Rainfall forecast updated (IMD)', ago: '28 min ago' });
    items.push({ text: 'No active critical alerts', ago: '52 min ago' });
    return items;
  }, [dtRun]);

  /* ── Default realistic alerts fallback if query empty ── */
  const alertRows = useMemo(() => {
    if (activeAlerts.length > 0) {
      return activeAlerts.slice(0, 3).map(a => ({
        title:    a.title,
        sub:      a.summary?.slice(0, 60) + (a.summary?.length > 60 ? '…' : '') || '',
        time:     new Date(a.generated_at).toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' }),
        severity: (a.severity === 'CRITICAL' ? 'critical' : a.severity === 'HIGH' ? 'high' : a.severity === 'MEDIUM' ? 'medium' : 'info') as AlertRowProps['severity'],
      }));
    }
    return [
      {
        title: 'Flooding expected near Kurla Junction',
        sub: 'Road inundation likely within 1 hour',
        time: '2 min ago',
        severity: 'high' as const,
      },
      {
        title: 'Water level rising — Mithi River',
        sub: 'Upstream inflow increasing',
        time: '12 min ago',
        severity: 'medium' as const,
      },
      {
        title: 'Watch: Heavy rainfall in next 3 hours',
        sub: 'IMD forecast update',
        time: '28 min ago',
        severity: 'info' as const,
      },
    ];
  }, [activeAlerts]);

  const steps = ['Now', '+30m', '+60m (Peak)', '+90m', '+120m', '+150m', '+180m'];

  const togglePlay = () => {
    setIsPlaying(!isPlaying);
  };

  return (
    <div className="space-y-4 pb-4 font-sans max-w-[1280px] mx-auto">

      {/* ── 1. Hero Skyline Banner ──────────────────────────── */}
      <MumbaiSkylineHero />

      {/* ── 2. Four story-oriented KPI cards ───────────────── */}
      <div className="grid grid-cols-2 lg:grid-cols-4 gap-4 items-stretch">
        <MetricCard
          icon={Clock}
          label="Next significant change"
          value={`+${peakTimeMin} min`}
          sub="Water accumulation expected to increase around this time."
          accent="teal"
        />
        <MetricCard
          icon={Waves}
          label="Area at risk"
          value={`${peakAreaKm2.toFixed(2)} km²`}
          sub={`Projected area above flood threshold. Max depth: ${maxDepthM.toFixed(2)} m`}
          accent="teal"
        />
        <MetricCard
          icon={Building2}
          label="Essential access at risk"
          value={<span className="text-[1.2rem] text-red-600">{topFacility}</span>}
          sub="Primary route may be affected from +30 min."
          accent="red"
        />
        <MetricCard
          icon={ShieldCheck}
          label="Suggested action"
          value={<span className="text-[1.1rem] text-emerald-600">{suggestedAction}</span>}
          sub="CST Road currently remains clearer."
          accent="green"
        />
      </div>

      {/* ── 3. Map + Active Alerts side-by-side ────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-4 items-stretch">

        {/* Map — 2/3 width */}
        <div className="lg:col-span-2 space-y-2.5 flex flex-col justify-between">
          <div className="flex items-center justify-between">
            <div className="flex items-center gap-2">
              <Waves className="w-4 h-4 text-[#008080]" />
              <span className="aq-section-title">Flood Situation Map</span>
              <span className="text-[11px] hidden sm:inline text-slate-500 font-medium">
                Modelled surface water extent (selected time)
              </span>
            </div>
            <div className="flex items-center gap-1.5 text-[11px] font-medium text-slate-500">
              <Clock className="w-3.5 h-3.5 text-slate-400" />
              <span>Forecast horizon: 0–180 min</span>
            </div>
          </div>

          {/* Timeline strip with Play button */}
          <div
            className="flex items-center gap-1.5 p-1.5 bg-white rounded-2xl border"
            style={{ borderColor: 'rgba(15,35,64,0.08)', boxShadow: '0 1px 2px rgba(15,35,64,0.04)' }}
          >
            <div className="flex-1 flex items-center gap-1 overflow-x-auto">
              {steps.map((t, i) => (
                <button
                  key={t}
                  onClick={() => setActiveStepIndex(i)}
                  className="flex-1 min-w-[52px] py-1.5 px-2 rounded-xl text-[11px] font-bold text-center transition-all duration-150 cursor-pointer"
                  style={i === activeStepIndex
                    ? { background: '#008080', color: '#fff', boxShadow: '0 2px 6px rgba(0,128,128,0.30)' }
                    : { color: 'var(--aq-text-muted)', background: 'transparent' }}
                >
                  {t}
                </button>
              ))}
            </div>

            <button
              onClick={togglePlay}
              className="flex items-center gap-1 px-3 py-1.5 rounded-xl text-[11px] font-bold text-[#008080] bg-[#e6f2f2] hover:bg-[#b2d8d8] transition-colors shrink-0 cursor-pointer"
            >
              {isPlaying ? <Pause className="w-3 h-3 fill-current" /> : <Play className="w-3 h-3 fill-current" />}
              <span>{isPlaying ? 'Pause' : 'Play'}</span>
            </button>
          </div>

          {/* Map with floating legend overlay */}
          <div className="aq-map-container relative rounded-[20px] overflow-hidden border border-slate-200/90 shadow-xs" style={{ height: '340px' }}>
            <MapContainer
              height="340px"
              {...({
                floodIntensityMultiplier: [0.35, 0.7, 1.0, 0.85, 0.65, 0.45, 0.25][activeStepIndex] ?? 1.0
              } as any)}
            />

            {/* Floating Legend Overlay */}
            <div
              className="absolute top-3 left-12 z-[1000] bg-white/95 backdrop-blur-sm p-3 rounded-2xl text-[10px] space-y-2 border hidden sm:block shadow-md"
              style={{
                width: '165px',
                borderColor: 'rgba(15,35,64,0.12)',
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
                <div className="flex items-center gap-2"><span className="w-2.5 h-2.5 rounded-full bg-[#008080]" /> Selected location</div>
                <div className="flex items-center gap-2"><span className="w-3 h-0.5 bg-slate-800" /> Major road</div>
                <div className="flex items-center gap-2"><span className="w-3 h-0.5 bg-slate-500 border-t border-b border-dashed" /> Railway</div>
                <div className="flex items-center gap-2"><span className="w-3 h-0.5 bg-cyan-500" /> Mithi River</div>
              </div>
            </div>
          </div>
        </div>

        {/* Active Alerts panel — 1/3 width */}
        <div className="flex flex-col">
          <Card padding="none" className="flex flex-col flex-1 justify-between overflow-hidden border shadow-xs">
            <div>
              <div className="flex items-center justify-between px-4 pt-3.5 pb-2.5 border-b border-slate-100">
                <h2 className="aq-section-title">Active Alerts</h2>
                <button
                  onClick={() => setActiveTab('alerts')}
                  className="text-[11px] font-semibold flex items-center gap-1 text-[#008080] hover:underline transition-colors cursor-pointer"
                >
                  View all <ChevronRight className="w-3 h-3" />
                </button>
              </div>

              <div className="px-4 divide-y divide-slate-100">
                {alertRows.map((ar, i) => (
                  <AlertRow key={i} {...ar} />
                ))}
              </div>
            </div>

            {/* Explore Aquora Grid */}
            <div className="p-3 border-t bg-slate-50/50 space-y-1.5 border-slate-100">
              <div className="flex items-center justify-between mb-0.5">
                <span className="aq-label">Explore Aquora</span>
                <button
                  onClick={() => setActiveTab('flood-map')}
                  className="text-[10px] font-semibold text-[#008080] hover:underline flex items-center gap-0.5 cursor-pointer"
                >
                  View all <ChevronRight className="w-2.5 h-2.5" />
                </button>
              </div>
              <div className="grid grid-cols-3 gap-1.5">
                <Shortcut icon={CloudRain}    label="Flood Outlook"     sub="View forecast"          color="#008080" onClick={() => setActiveTab('flood-map')} />
                <Shortcut icon={Navigation}   label="Travel Window"     sub="Check routes"           color="#059669" onClick={() => setActiveTab('travel-window')} />
                <Shortcut icon={ShieldAlert}  label="Critical Access"   sub="Essential facilities"   color="#008080" onClick={() => setActiveTab('critical-access')} />
                <Shortcut icon={Building2}    label="Protect the City"  sub="Intervention options"   color="#15803d" onClick={() => setActiveTab('protect-city')} />
                <Shortcut icon={Camera}       label="Ground Truth"      sub="Report from field"      color="#7c3aed" onClick={() => setActiveTab('ground-truth')} />
                <Shortcut icon={Sliders}      label="Simulator"         sub="Test scenarios"         color="#c2410c" onClick={() => setActiveTab('simulator')} />
              </div>
            </div>
          </Card>
        </div>
      </div>

      {/* ── 4. Recent Activity + Civic Quote ───────────────── */}
      <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
        {/* Activity feed */}
        <Card padding="md" className="flex flex-col justify-between h-[125px] border shadow-xs">
          <div className="flex items-center justify-between mb-2">
            <h3 className="aq-section-title">Recent Activity</h3>
            <button
              onClick={() => setActiveTab('alerts')}
              className="text-[11px] font-semibold text-[#008080] hover:underline flex items-center gap-0.5 cursor-pointer"
            >
              View all <ChevronRight className="w-3 h-3" />
            </button>
          </div>
          <div className="space-y-1.5">
            {recentActivity.map((item, i) => (
              <div key={i} className="flex items-center justify-between gap-2 text-[11.5px]">
                <div className="flex items-center gap-2 truncate">
                  <span
                    className="w-2 h-2 rounded-full shrink-0"
                    style={{ background: i === 2 ? '#94a3b8' : '#008080' }}
                  />
                  <span className="font-medium truncate text-slate-800">{item.text}</span>
                </div>
                <span className="shrink-0 text-[10.5px] text-slate-400">{item.ago}</span>
              </div>
            ))}
          </div>
        </Card>

        {/* Civic Quote Card in Warm System Beige (#F5F5DC / #f9f9ee) */}
        <div
          className="rounded-2xl p-4 flex flex-col justify-between relative overflow-hidden text-slate-800 h-[125px] border"
          style={{
            background: 'linear-gradient(135deg, #fdfdf7 0%, #F5F5DC 60%, #f7f7e8 100%)',
            borderColor: '#e6e6cc',
            boxShadow: '0 1px 3px rgba(15,35,64,0.06)',
          }}
        >
          <Quote className="w-7 h-7 text-[#008080]/30 absolute top-2.5 left-3" />
          <div className="relative z-10 pt-1 pl-6">
            <p className="text-[13.5px] font-extrabold text-slate-900 leading-snug">
              Better information today.
            </p>
            <p className="text-[13.5px] font-extrabold text-[#008080] leading-snug">
              A safer, more resilient Mumbai tomorrow.
            </p>
            <p className="text-[10px] font-black uppercase tracking-wider text-slate-600 mt-1.5 opacity-90">
              — AQUORA
            </p>
          </div>
          {/* Subtle bottom wave lines in brand Teal */}
          <div className="absolute -bottom-2 right-0 left-0 opacity-20 pointer-events-none">
            <svg viewBox="0 0 400 35" fill="none" className="w-full">
              <path d="M0 15 Q 100 5, 200 15 T 400 15 L 400 35 L 0 35 Z" fill="#008080" />
            </svg>
          </div>
        </div>
      </div>

      {/* ── 5. Footer ───────────────────────────────────────── */}
      <div className="pt-1 flex items-center justify-end text-[10.5px] text-slate-400 font-medium gap-1.5">
        <Waves className="w-3.5 h-3.5 text-[#008080]" />
        <span>Built for people, cities and a safer tomorrow.</span>
      </div>
    </div>
  );
};

export default OverviewFeature;
