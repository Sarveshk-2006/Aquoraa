import React, { useState, useEffect } from 'react';
import {
  Sliders,
  Play,
  AlertTriangle,
  ArrowRight,
} from 'lucide-react';
import { LeafletMap } from '@/map/LeafletMap';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import { fetchLatestDigitalTwinRun } from '@/api/digitalTwin';

import {
  createScenario,
  runScenarioSimulation,
  validateScenario,
  ScenarioType,
  OutcomeClassification,
  SimulatorRunSummary,
  SimulatorScenario,
} from '@/api/simulator';

export const SimulatorFeature: React.FC = () => {
  const [baselineRunId, setBaselineRunId] = useState<string>('dt_mithi_baseline_001');

  useEffect(() => {
    fetchLatestDigitalTwinRun()
      .then((run) => {
        if (run?.run_id) {
          setBaselineRunId(run.run_id);
        }
      })
      .catch((err) => console.warn('Could not load latest Digital Twin run for Simulator:', err));
  }, []);
  const [scenarioType, setScenarioType] = useState<ScenarioType>('RAINFALL_MULTIPLIER');

  // Controlled Parameter Inputs
  const [rainfallMultiplier, setRainfallMultiplier] = useState<number>(1.25);
  const [rainfallAdditionMm, setRainfallAdditionMm] = useState<number>(25.0);
  const [capacityMultiplier, setCapacityMultiplier] = useState<number>(0.80);
  const [interventionCandidateId] = useState<string>('cand_drainage_culvert_expansion_l2');
  const [pumpCapacityM3s] = useState<number>(5.0);
  const [modifiesUnknownCapacity] = useState<boolean>(false);
  const [unknownCapacityPolicy] = useState<string>('PRESERVE_UNKNOWN');

  // Execution State
  const [currentScenario, setCurrentScenario] = useState<SimulatorScenario | null>(null);
  const [executionSummary, setExecutionSummary] = useState<SimulatorRunSummary | null>(null);
  // statusState tracks internal sim flow — used in logic, not exposed to render
  const [, setStatusState] = useState<string>('DRAFT');
  const [loading, setLoading] = useState<boolean>(false);
  const [validationError, setValidationError] = useState<string | null>(null);

  const handleValidateScenario = async () => {
    setLoading(true);
    setValidationError(null);

    let params: Record<string, any> = {};
    if (scenarioType === 'RAINFALL_MULTIPLIER') {
      params = { rainfall_multiplier: rainfallMultiplier };
    } else if (scenarioType === 'RAINFALL_ADDITION') {
      params = { rainfall_addition_mm: rainfallAdditionMm };
    } else if (scenarioType === 'DRAINAGE_CAPACITY_REDUCTION' || scenarioType === 'DRAINAGE_CAPACITY_INCREASE') {
      params = { capacity_multiplier: capacityMultiplier, modifies_unknown_capacity: modifiesUnknownCapacity };
    } else if (scenarioType === 'DRAINAGE_NODE_INTERVENTION') {
      params = { intervention_candidate_ids: [interventionCandidateId] };
    } else if (scenarioType === 'PUMP_OR_DEWATERING_SCENARIO') {
      params = { pump_capacity_m3_s: pumpCapacityM3s };
    } else if (scenarioType === 'TEMPORARY_BARRIER' || scenarioType === 'STORAGE_INTERVENTION') {
      params = { is_supported_parameterization: false };
    } else if (scenarioType === 'COMBINED_SCENARIO') {
      params = { rainfall_multiplier: rainfallMultiplier, capacity_multiplier: capacityMultiplier };
    }

    try {
      const scen = await createScenario({
        baseline_run_id: baselineRunId,
        scenario_type: scenarioType,
        parameters: params,
        unknown_capacity_policy: modifiesUnknownCapacity ? unknownCapacityPolicy : undefined,
      });

      setCurrentScenario(scen);
      setStatusState(scen.status);

      const valRes = await validateScenario(scen.scenario_id);
      setStatusState(valRes.status);
      if (!valRes.is_valid) {
        setValidationError(valRes.rejection_reason || 'Scenario validation failed');
      }
    } catch (err: any) {
      setValidationError(err.message || 'Error initializing scenario');
      setStatusState('FAILED');
    } finally {
      setLoading(false);
    }
  };

  const handleRunSimulation = async () => {
    if (!currentScenario) {
      await handleValidateScenario();
    }
    setLoading(true);
    setStatusState('RUNNING');
    try {
      let scenId = currentScenario?.scenario_id;
      if (!scenId) {
        let params: Record<string, any> = { rainfall_multiplier: rainfallMultiplier };
        if (scenarioType === 'RAINFALL_ADDITION') params = { rainfall_addition_mm: rainfallAdditionMm };
        if (scenarioType === 'DRAINAGE_CAPACITY_REDUCTION') params = { capacity_multiplier: capacityMultiplier };
        const scen = await createScenario({
          baseline_run_id: baselineRunId,
          scenario_type: scenarioType,
          parameters: params,
        });
        scenId = scen.scenario_id;
        setCurrentScenario(scen);
      }

      const summary = await runScenarioSimulation(scenId);
      setExecutionSummary(summary);
      setStatusState(summary.run.status);
    } catch (err: any) {
      setValidationError(err.message || 'Simulation execution failed');
      setStatusState('FAILED');
    } finally {
      setLoading(false);
    }
  };

  // OUTCOME_STYLES derived from outcomeBadge
  const OUTCOME_STYLES: Record<OutcomeClassification, { badge: 'success' | 'neutral' | 'danger' | 'warning'; text: string }> = {
    IMPROVED: { badge: 'success', text: 'Outcome improved' },
    NO_SIGNIFICANT_CHANGE: { badge: 'neutral', text: 'No significant change' },
    WORSE: { badge: 'danger', text: 'Conditions worsened' },
    INCONCLUSIVE: { badge: 'warning', text: 'Inconclusive' },
  };

  // Peak comparison slice (choose +60m or first available)
  const peakComparison = executionSummary?.comparisons.find(c => c.slice_minutes === 60) || executionSummary?.comparisons[0];
  const peakOutcome = peakComparison?.outcome || 'INCONCLUSIVE';

  return (
    <div className="space-y-5 pb-10 font-sans max-w-[1240px] mx-auto">

      {/* ── Page header ──────────────────────────────────────── */}
      <div>
        <h1
          className="text-[1.75rem] font-extrabold leading-none tracking-tight"
          style={{ color: 'var(--aq-navy)', letterSpacing: '-0.02em' }}
        >
          Simulator
        </h1>
        <p className="mt-1.5 text-[14px]" style={{ color: 'var(--aq-muted)' }}>
          What happens if conditions change? Explore how adjustments affect the flood outlook.
        </p>
      </div>

      {/* ── Main 3-col layout ────────────────────────────────── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-5">

        {/* Left controls — 4 cols */}
        <div className="lg:col-span-4 flex flex-col gap-4">

          {/* Starting conditions */}
          <Card padding="md" className="space-y-3">
            <div className="aq-section-title pb-2 border-b" style={{ borderColor: 'rgba(15,35,64,0.06)' }}>
              Starting situation
            </div>
            <div>
              <label className="aq-label block mb-1.5">Current flood baseline</label>
              <select
                value={baselineRunId}
                onChange={(e) => setBaselineRunId(e.target.value)}
                className="w-full rounded-xl px-3 py-2 text-[12px] font-medium focus:outline-none"
                style={{ background: '#f8fafc', border: '1px solid rgba(15,35,64,0.12)', color: 'var(--aq-text)' }}
              >
                <option value="dt_mithi_baseline_001">Mithi River — Current season baseline</option>
                <option value="sim_v_valley_baseline">Model validation grid</option>
              </select>
            </div>
          </Card>

          {/* What would you like to change? */}
          <Card padding="md" className="space-y-4">
            <div className="aq-section-title pb-2 border-b" style={{ borderColor: 'rgba(15,35,64,0.06)' }}>
              What would you like to change?
            </div>

            {/* Scenario type tabs */}
            <div className="grid grid-cols-2 gap-2">
              {([
                ['RAINFALL_MULTIPLIER', 'Heavier rain'],
                ['RAINFALL_ADDITION', 'Extra rainfall'],
                ['DRAINAGE_CAPACITY_REDUCTION', 'Less drainage'],
                ['COMBINED_SCENARIO', 'Combined'],
              ] as [ScenarioType, string][]).map(([type, label]) => (
                <button
                  key={type}
                  onClick={() => setScenarioType(type)}
                  className="py-2 px-3 rounded-xl text-[12px] font-semibold transition-all duration-150 text-center"
                  style={scenarioType === type
                    ? { background: 'var(--aq-blue)', color: '#fff', boxShadow: '0 2px 6px rgba(26,86,219,0.25)' }
                    : { background: '#f8fafc', color: 'var(--aq-muted)', border: '1px solid rgba(15,35,64,0.10)' }
                  }
                >
                  {label}
                </button>
              ))}
            </div>

            {/* Scenario-specific control */}
            {scenarioType === 'RAINFALL_MULTIPLIER' && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="aq-label">Rainfall intensity</label>
                  <span
                    className="text-[18px] font-extrabold"
                    style={{ color: 'var(--aq-blue)', letterSpacing: '-0.02em' }}
                  >
                    {rainfallMultiplier.toFixed(2)}×
                  </span>
                </div>
                <input
                  type="range"
                  min="0.5"
                  max="3.0"
                  step="0.05"
                  value={rainfallMultiplier}
                  onChange={(e) => setRainfallMultiplier(parseFloat(e.target.value))}
                  className="w-full"
                />
                <p className="text-[11px]" style={{ color: 'var(--aq-muted)' }}>
                  {rainfallMultiplier >= 2.0
                    ? 'Extreme rainfall — significantly increases flood extent.'
                    : rainfallMultiplier >= 1.3
                    ? 'Heavy rainfall — moderate increase in flood risk.'
                    : 'Near-normal conditions.'}
                </p>
              </div>
            )}

            {scenarioType === 'RAINFALL_ADDITION' && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="aq-label">Additional rainfall</label>
                  <span className="text-[18px] font-extrabold" style={{ color: 'var(--aq-blue)', letterSpacing: '-0.02em' }}>
                    +{rainfallAdditionMm.toFixed(0)} mm
                  </span>
                </div>
                <input
                  type="range" min="0" max="150" step="5"
                  value={rainfallAdditionMm}
                  onChange={(e) => setRainfallAdditionMm(parseFloat(e.target.value))}
                  className="w-full"
                />
              </div>
            )}

            {(scenarioType === 'DRAINAGE_CAPACITY_REDUCTION' || scenarioType === 'DRAINAGE_CAPACITY_INCREASE') && (
              <div className="space-y-2">
                <div className="flex items-center justify-between">
                  <label className="aq-label">Drainage capacity</label>
                  <span className="text-[18px] font-extrabold" style={{ color: 'var(--aq-blue)', letterSpacing: '-0.02em' }}>
                    {(capacityMultiplier * 100).toFixed(0)}%
                  </span>
                </div>
                <input
                  type="range" min="0.1" max="1.5" step="0.05"
                  value={capacityMultiplier}
                  onChange={(e) => setCapacityMultiplier(parseFloat(e.target.value))}
                  className="w-full"
                />
              </div>
            )}

            {scenarioType === 'COMBINED_SCENARIO' && (
              <div className="space-y-3">
                <div className="space-y-1">
                  <div className="flex justify-between">
                    <label className="aq-label">Rainfall</label>
                    <span className="text-[13px] font-bold" style={{ color: 'var(--aq-blue)' }}>{rainfallMultiplier.toFixed(2)}×</span>
                  </div>
                  <input type="range" min="0.5" max="3.0" step="0.05" value={rainfallMultiplier} onChange={(e) => setRainfallMultiplier(parseFloat(e.target.value))} className="w-full" />
                </div>
                <div className="space-y-1">
                  <div className="flex justify-between">
                    <label className="aq-label">Drainage</label>
                    <span className="text-[13px] font-bold" style={{ color: 'var(--aq-blue)' }}>{(capacityMultiplier * 100).toFixed(0)}%</span>
                  </div>
                  <input type="range" min="0.1" max="1.5" step="0.05" value={capacityMultiplier} onChange={(e) => setCapacityMultiplier(parseFloat(e.target.value))} className="w-full" />
                </div>
              </div>
            )}

            {validationError && (
              <div className="px-3 py-2 rounded-xl text-[11px] font-medium" style={{ background: '#fff1f2', color: '#be123c', border: '1px solid #fecdd3' }}>
                {validationError}
              </div>
            )}

            <Button
              variant="primary"
              size="md"
              onClick={handleRunSimulation}
              isLoading={loading}
              icon={<Play className="w-3.5 h-3.5" />}
              className="w-full"
            >
              Run scenario
            </Button>
          </Card>

          {/* Model details (discoverable, secondary) */}
          <Card padding="sm">
            <details>
              <summary className="cursor-pointer text-[12px] font-semibold select-none py-1" style={{ color: 'var(--aq-muted)' }}>
                Model details ▸
              </summary>
              <div className="mt-3 space-y-1.5 text-[11px]" style={{ color: 'var(--aq-muted)' }}>
                {[
                  ['Engine', 'Digital Twin · D8 Flow Solver'],
                  ['Grid resolution', '30m × 30m'],
                  ['Surface model', 'Physical flow model'],
                  ['Scenario type', scenarioType],
                ].map(([k, v]) => (
                  <div key={k} className="flex justify-between">
                    <span>{k}</span>
                    <span className="font-semibold" style={{ color: 'var(--aq-text)' }}>{v}</span>
                  </div>
                ))}
              </div>
            </details>
          </Card>
        </div>

        {/* Right area — 8 cols: map + results */}
        <div className="lg:col-span-8 flex flex-col gap-4">

          {/* Map */}
          <div className="aq-map-container" style={{ height: '340px' }}>
            <LeafletMap
              center={[19.076, 72.8777]}
              zoom={13}
              height="100%"
            />
          </div>

          {/* Results */}
          {executionSummary && peakComparison ? (
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              {/* Before → After */}
              <Card padding="md" className="space-y-3">
                <div className="flex items-center gap-2 pb-2 border-b" style={{ borderColor: 'rgba(15,35,64,0.06)' }}>
                  <Sliders className="w-4 h-4" style={{ color: 'var(--aq-aqua)' }} />
                  <span className="aq-section-title">Scenario result</span>
                  {(() => {
                    const s = OUTCOME_STYLES[peakOutcome] || OUTCOME_STYLES.INCONCLUSIVE;
                    return <Badge variant={s.badge} size="sm">{s.text}</Badge>;
                  })()}
                </div>

                <div className="grid grid-cols-2 gap-3">
                  <div className="space-y-1">
                    <div className="aq-label">Baseline area</div>
                    <div className="text-[17px] font-extrabold" style={{ color: 'var(--aq-navy)', letterSpacing: '-0.02em' }}>
                      {peakComparison.baseline_metrics.flooded_area_km2.toFixed(2)} km²
                    </div>
                  </div>
                  <div className="space-y-1">
                    <div className="aq-label">Scenario area</div>
                    <div className="text-[17px] font-extrabold" style={{ color: '#dc2626', letterSpacing: '-0.02em' }}>
                      {peakComparison.scenario_metrics.flooded_area_km2.toFixed(2)} km²
                    </div>
                  </div>
                  <div className="space-y-1">
                    <div className="aq-label">Change in area</div>
                    <div className="text-[15px] font-bold" style={{ color: peakComparison.deltas.flooded_area_delta_km2 > 0 ? '#dc2626' : '#059669' }}>
                      {peakComparison.deltas.flooded_area_delta_km2 > 0 ? '+' : ''}{peakComparison.deltas.flooded_area_delta_km2.toFixed(2)} km²
                    </div>
                  </div>
                  <div className="space-y-1">
                    <div className="aq-label">High-risk area</div>
                    <div className="text-[15px] font-bold" style={{ color: 'var(--aq-muted)' }}>
                      {peakComparison.scenario_metrics.high_severe_area_km2.toFixed(2)} km²
                    </div>
                  </div>
                </div>
              </Card>

              {/* Explanation */}
              <Card padding="md">
                <div className="aq-section-title mb-3 pb-2 border-b" style={{ borderColor: 'rgba(15,35,64,0.06)' }}>
                  What this means
                </div>
                <p className="text-[12px] leading-relaxed" style={{ color: 'var(--aq-muted)' }}>
                  {executionSummary.governance_notice || executionSummary.conditional_benefit_notice ||
                    'The scenario was simulated using the Digital Twin physical engine. Review the area change above for flood impact.'}
                </p>
                {executionSummary.run.warnings && executionSummary.run.warnings.length > 0 && (
                  <div className="mt-3 flex items-start gap-2 text-[11px] px-3 py-2 rounded-xl" style={{ background: '#fffbeb', color: '#92400e', border: '1px solid #fde68a' }}>
                    <AlertTriangle className="w-3.5 h-3.5 shrink-0 mt-0.5" />
                    <span>{executionSummary.run.warnings[0]}</span>
                  </div>
                )}
              </Card>
            </div>
          ) : !loading ? (
            <div className="flex flex-col items-center justify-center py-12 rounded-2xl" style={{ background: '#f8fafc', border: '1px solid rgba(15,35,64,0.06)' }}>
              <ArrowRight className="w-8 h-8 mb-3" style={{ color: 'var(--aq-muted)' }} />
              <p className="text-[13px] font-semibold" style={{ color: 'var(--aq-text)' }}>Configure and run a scenario</p>
              <p className="text-[11px] mt-1" style={{ color: 'var(--aq-muted)' }}>
                Choose conditions on the left, then tap "Run scenario" to see the projected impact.
              </p>
            </div>
          ) : (
            <div className="flex items-center justify-center py-12 rounded-2xl" style={{ background: '#f8fafc', border: '1px solid rgba(15,35,64,0.06)' }}>
              <p className="text-[12px]" style={{ color: 'var(--aq-muted)' }}>Running scenario simulation…</p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default SimulatorFeature;
