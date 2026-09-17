import React, { useState, useEffect } from 'react';
import {
  Building2,
  AlertTriangle,
  RefreshCw,
  MapPin,
  ShieldCheck,
} from 'lucide-react';
import { LeafletMap } from '@/map/LeafletMap';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import {
  analyzeProtectCity,
  fetchLatestProtectCityRun,
  ProtectCityResponse,
  ProtectCityRequest,
} from '@/api/protectCity';

const PRIORITY_BADGES: Record<string, { badge: 'danger' | 'warning' | 'info' | 'neutral'; colorHex: string }> = {
  CRITICAL: { badge: 'danger', colorHex: '#e11d48' },
  HIGH: { badge: 'warning', colorHex: '#ea580c' },
  MEDIUM: { badge: 'warning', colorHex: '#d97706' },
  LOW: { badge: 'info', colorHex: '#0284c7' },
  UNKNOWN: { badge: 'neutral', colorHex: '#64748b' },
};


export const ProtectCityFeature: React.FC = () => {
  const [analysisData, setAnalysisData] = useState<ProtectCityResponse | null>(null);
  const [selectedCandidateId, setSelectedCandidateId] = useState<string | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Filters & sorting
  const [timeFilterMin, setTimeFilterMin] = useState<number | null>(180);
  const [minPriority] = useState<string>('LOW');
  const [sortBy, setSortBy] = useState<'priority' | 'threat_time' | 'expected_benefit'>('priority');

  const runAnalysis = async () => {
    setIsAnalyzing(true);
    setErrorMsg(null);
    try {
      const payload: ProtectCityRequest = {
        minimum_priority: minPriority,
        priority_limit: 30,
        time_horizon_minutes: timeFilterMin,
      };
      const res = await analyzeProtectCity(payload);
      setAnalysisData(res);
      if (res.recommendations.length > 0 && !selectedCandidateId) {
        setSelectedCandidateId(res.recommendations[0].candidate.candidate_id);
      }
    } catch (err: any) {
      console.error('Protect the City analysis error:', err);
      try {
        const latest = await fetchLatestProtectCityRun();
        setAnalysisData(latest);
        if (latest.recommendations.length > 0) {
          setSelectedCandidateId(latest.recommendations[0].candidate.candidate_id);
        }
      } catch (fallbackErr: any) {
        setErrorMsg(err.message || 'Failed to complete Protect the City analysis');
      }
    } finally {
      setIsAnalyzing(false);
    }
  };

  useEffect(() => {
    runAnalysis();
  }, []);

  const filteredRecommendations = (analysisData?.recommendations || []).filter((rec) => {
    if (timeFilterMin !== null && rec.first_threat_minutes !== undefined && rec.first_threat_minutes !== null && rec.first_threat_minutes > timeFilterMin) {
      return false;
    }
    return true;
  }).sort((a, b) => {
    if (sortBy === 'priority') {
      return b.priority_score - a.priority_score;
    }
    if (sortBy === 'threat_time') {
      const timeA = a.first_threat_minutes ?? 999;
      const timeB = b.first_threat_minutes ?? 999;
      return timeA - timeB;
    }
    if (sortBy === 'expected_benefit') {
      const benefitOrder: Record<string, number> = { HIGH: 4, MEDIUM: 3, LOW: 2, UNKNOWN: 1 };
      return (benefitOrder[b.expected_benefit] || 0) - (benefitOrder[a.expected_benefit] || 0);
    }
    return 0;
  });

  const selectedRecommendation = filteredRecommendations.find(
    (r) => r.candidate.candidate_id === selectedCandidateId
  ) || filteredRecommendations[0] || null;

  const mapMarkers = filteredRecommendations.map((rec) => {
    const { candidate, priority } = rec;
    const badge = PRIORITY_BADGES[priority] || PRIORITY_BADGES.UNKNOWN;

    return {
      id: candidate.candidate_id,
      position: [candidate.latitude, candidate.longitude] as [number, number],
      color: badge.colorHex,
      popupContent: `<strong>${candidate.name}</strong><br/>Priority: ${priority}<br/>Action: ${rec.intervention_type}`,
    };
  });

  return (
    <div className="space-y-5 pb-10 font-sans max-w-[1240px] mx-auto">

      {/* ── Page header ─────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-3">
        <div>
          <h1
            className="text-[1.75rem] font-extrabold leading-none tracking-tight"
            style={{ color: 'var(--aq-navy)', letterSpacing: '-0.02em' }}
          >
            Protect the City
          </h1>
          <p className="mt-1.5 text-[14px]" style={{ color: 'var(--aq-muted)' }}>
            Where could an intervention help most? Priority locations for dewatering, clearing, or barriers.
          </p>
        </div>
        <Button
          variant="primary"
          size="sm"
          onClick={runAnalysis}
          isLoading={isAnalyzing}
          icon={<RefreshCw className="w-3.5 h-3.5" />}
        >
          Re-analyse
        </Button>
      </div>

      {/* ── Error state ─────────────────────────────────────── */}
      {errorMsg && (
        <Card padding="md">
          <div className="flex items-start gap-3">
            <AlertTriangle className="w-5 h-5 shrink-0 mt-0.5" style={{ color: '#d97706' }} />
            <div>
              <p className="text-[13px] font-semibold" style={{ color: 'var(--aq-text)' }}>Couldn't complete analysis</p>
              <p className="text-[11px] mt-0.5" style={{ color: 'var(--aq-muted)' }}>{errorMsg}</p>
            </div>
          </div>
        </Card>
      )}

      {/* ── Controls ─────────────────────────────────────────── */}
      <Card padding="sm">
        <div className="flex flex-wrap items-center gap-3">
          <span className="aq-label shrink-0">Sort by</span>
          {([
            ['priority', 'Priority'],
            ['threat_time', 'Soonest threat'],
            ['expected_benefit', 'Expected benefit'],
          ] as const).map(([key, label]) => (
            <button
              key={key}
              onClick={() => setSortBy(key as 'priority' | 'threat_time' | 'expected_benefit')}
              className="px-3 py-1.5 rounded-xl text-[11px] font-semibold transition-all duration-150"
              style={sortBy === key
                ? { background: 'var(--aq-blue)', color: '#fff' }
                : { background: '#f8fafc', color: 'var(--aq-muted)', border: '1px solid rgba(15,35,64,0.10)' }
              }
            >
              {label}
            </button>
          ))}
          <span className="w-px self-stretch bg-slate-200 mx-1" />
          <span className="aq-label shrink-0">Horizon</span>
          {([30, 60, 90, 180, null] as const).map((t) => (
            <button
              key={t ?? 'all'}
              onClick={() => setTimeFilterMin(t)}
              className="px-3 py-1.5 rounded-xl text-[11px] font-semibold transition-all duration-150"
              style={timeFilterMin === t
                ? { background: 'var(--aq-navy)', color: '#fff' }
                : { background: '#f8fafc', color: 'var(--aq-muted)', border: '1px solid rgba(15,35,64,0.10)' }
              }
            >
              {t === null ? 'All' : `${t} min`}
            </button>
          ))}
        </div>
      </Card>

      {/* ── Main layout ─────────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-3 gap-5 min-h-[500px]">

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

          {/* Intervention list */}
          <Card padding="sm" className="flex-1">
            <div className="flex items-center gap-2 px-1 pb-3 border-b mb-3" style={{ borderColor: 'rgba(15,35,64,0.06)' }}>
              <Building2 className="w-4 h-4" style={{ color: 'var(--aq-aqua)' }} />
              <span className="aq-section-title">Priority sites</span>
              <span className="ml-auto text-[11px] font-semibold px-2 py-0.5 rounded-full" style={{ background: '#eff6ff', color: 'var(--aq-blue)' }}>
                {filteredRecommendations.length}
              </span>
            </div>

            {isAnalyzing ? (
              <div className="py-8 text-center text-[12px]" style={{ color: 'var(--aq-muted)' }}>Analysing priority sites…</div>
            ) : filteredRecommendations.length === 0 ? (
              <div className="py-8 text-center">
                <ShieldCheck className="w-8 h-8 mx-auto mb-2" style={{ color: 'var(--aq-muted)' }} />
                <p className="text-[13px] font-semibold" style={{ color: 'var(--aq-text)' }}>No sites match this filter</p>
              </div>
            ) : (
              <div className="space-y-1.5 max-h-[320px] overflow-y-auto pr-1" style={{ scrollbarWidth: 'thin' }}>
                {filteredRecommendations.map((rec) => {
                  const pb = PRIORITY_BADGES[rec.priority] || PRIORITY_BADGES.UNKNOWN;
                  const isSelected = selectedCandidateId === rec.candidate.candidate_id;
                  return (
                    <button
                      key={rec.candidate.candidate_id}
                      onClick={() => setSelectedCandidateId(rec.candidate.candidate_id)}
                      className="w-full text-left p-3 rounded-xl flex items-start gap-3 transition-all duration-150"
                      style={{
                        background: isSelected ? '#eff6ff' : '#f8fafc',
                        border: isSelected ? '1.5px solid #bfdbfe' : '1px solid rgba(15,35,64,0.06)',
                      }}
                    >
                      <span className="w-1.5 h-1.5 rounded-full shrink-0 mt-1.5" style={{ background: pb.colorHex }} />
                      <div className="flex-1 min-w-0">
                        <div className="text-[12px] font-semibold truncate" style={{ color: 'var(--aq-text)' }}>
                          {rec.candidate.name}
                        </div>
                        <div className="text-[10px] mt-0.5" style={{ color: 'var(--aq-muted)' }}>
                          {rec.intervention_type.replace(/_/g, ' ')}
                          {rec.first_threat_minutes != null ? ` · threat in ${rec.first_threat_minutes}m` : ''}
                        </div>
                      </div>
                      <Badge variant={pb.badge} size="sm">{rec.priority}</Badge>
                    </button>
                  );
                })}
              </div>
            )}
          </Card>

          {/* Selected site detail */}
          {selectedRecommendation && (
            <Card padding="md" className="space-y-3">
              <div className="flex items-center justify-between pb-2 border-b" style={{ borderColor: 'rgba(15,35,64,0.06)' }}>
                <span className="aq-section-title">Site detail</span>
                <Badge variant={PRIORITY_BADGES[selectedRecommendation.priority]?.badge || 'neutral'} size="sm">
                  {selectedRecommendation.priority}
                </Badge>
              </div>

              <div className="flex items-start gap-2">
                <MapPin className="w-4 h-4 shrink-0 mt-0.5" style={{ color: 'var(--aq-blue)' }} />
                <div>
                  <div className="text-[13px] font-semibold" style={{ color: 'var(--aq-navy)' }}>
                    {selectedRecommendation.candidate.name}
                  </div>
                  <div className="text-[11px]" style={{ color: 'var(--aq-muted)' }}>
                    {selectedRecommendation.candidate.candidate_type.replace(/_/g, ' ')}
                  </div>
                </div>
              </div>

              {[
                { label: 'Intervention', val: selectedRecommendation.intervention_type.replace(/_/g, ' ') },
                { label: 'Threat onset', val: selectedRecommendation.first_threat_minutes != null ? `+${selectedRecommendation.first_threat_minutes} min` : 'No modelled threat' },
                { label: 'Expected benefit', val: selectedRecommendation.expected_benefit },
                { label: 'Urgency', val: selectedRecommendation.priority_component_breakdown?.ranking_category || selectedRecommendation.priority },
              ].map((row) => (
                <div key={row.label} className="flex justify-between text-[12px] py-1.5 border-b" style={{ borderColor: 'rgba(15,35,64,0.05)' }}>
                  <span style={{ color: 'var(--aq-muted)' }}>{row.label}</span>
                  <span className="font-semibold" style={{ color: 'var(--aq-text)' }}>{row.val}</span>
                </div>
              ))}

              {selectedRecommendation.explanation && (
                <div className="px-3 py-2.5 rounded-xl text-[11px] leading-relaxed" style={{ background: '#eff6ff', color: '#1e3a8a', border: '1px solid #bfdbfe' }}>
                  <div className="font-semibold mb-1">Why this site matters</div>
                  {selectedRecommendation.explanation}
                </div>
              )}
            </Card>
          )}
        </div>
      </div>
    </div>
  );
};

export default ProtectCityFeature;
