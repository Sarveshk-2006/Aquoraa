import React, { useState, useEffect } from 'react';
import {
  Clock,
  AlertTriangle,
  RefreshCw,
  Building2,
  ArrowRightLeft,
  Compass,
  Navigation
} from 'lucide-react';
import { LeafletMap } from '@/map/LeafletMap';
import { Card } from '@/components/ui/Card';
import { Badge } from '@/components/ui/Badge';
import { Button } from '@/components/ui/Button';
import {
  analyzeCriticalAccess,
  fetchCriticalFacilities,
  CriticalFacility,
  CriticalAccessResponse,
} from '@/api/criticalAccess';

const DEFAULT_ORIGIN = {
  lat: 19.0600,
  lon: 72.8650,
  label: 'Bandra-Kurla Responder Unit 1',
};

const STATUS_BADGES: Record<string, { badge: 'success' | 'info' | 'warning' | 'danger' | 'neutral'; text: string; bg: string; color: string }> = {
  ACCESSIBLE: { badge: 'success', text: 'Accessible', bg: '#f0fdf4', color: '#166534' },
  LIMITED: { badge: 'info', text: 'Limited Access', bg: '#eff6ff', color: '#1e40af' },
  AT_RISK: { badge: 'warning', text: 'Access At Risk', bg: '#fffbeb', color: '#92400e' },
  COMPROMISED: { badge: 'danger', text: 'Access Compromised', bg: '#fef2f2', color: '#991b1b' },
  UNAVAILABLE: { badge: 'danger', text: 'Unavailable', bg: '#fef2f2', color: '#991b1b' },
  UNKNOWN: { badge: 'neutral', text: 'Status Unknown', bg: '#f8fafc', color: '#475569' },
};

export const CriticalAccessFeature: React.FC = () => {
  const [facilities, setFacilities] = useState<CriticalFacility[]>([]);
  const [isLoadingFacilities, setIsLoadingFacilities] = useState<boolean>(true);
  const [facilityError, setFacilityError] = useState<string | null>(null);
  const [selectedFacilityId, setSelectedFacilityId] = useState<string>('');

  // String state for coordinate inputs to prevent NaN flashes while typing
  const [originLatInput, setOriginLatInput] = useState<string>(DEFAULT_ORIGIN.lat.toString());
  const [originLonInput, setOriginLonInput] = useState<string>(DEFAULT_ORIGIN.lon.toString());
  const [originLabel] = useState<string>(DEFAULT_ORIGIN.label);

  const [accessData, setAccessData] = useState<CriticalAccessResponse | null>(null);
  const [isAnalyzing, setIsAnalyzing] = useState<boolean>(false);
  const [errorMsg, setErrorMsg] = useState<string | null>(null);

  // Load facilities from real backend API on mount
  const loadFacilities = async () => {
    setIsLoadingFacilities(true);
    setFacilityError(null);
    try {
      const data = await fetchCriticalFacilities();
      if (data && data.length > 0) {
        setFacilities(data);
        setSelectedFacilityId(data[0].facility_id);
      } else {
        setFacilities([]);
        setFacilityError('No facilities returned by backend.');
      }
    } catch (err: any) {
      console.error('Failed to fetch facilities:', err);
      setFacilities([]);
      setFacilityError(err.message || 'Failed to fetch facility list.');
    } finally {
      setIsLoadingFacilities(false);
    }
  };

  useEffect(() => {
    loadFacilities();
  }, []);

  // Defensive coordinate validation
  const getValidLat = (val: string): number | null => {
    const p = parseFloat(val.trim());
    if (!isNaN(p) && isFinite(p) && p >= -90 && p <= 90) return p;
    return null;
  };

  const getValidLon = (val: string): number | null => {
    const p = parseFloat(val.trim());
    if (!isNaN(p) && isFinite(p) && p >= -180 && p <= 180) return p;
    return null;
  };

  const validLat = getValidLat(originLatInput);
  const validLon = getValidLon(originLonInput);
  const isCoordinatesValid = validLat !== null && validLon !== null;

  // Execute Analysis via real API
  const handleAnalyze = async () => {
    if (!selectedFacilityId) return;
    if (!isCoordinatesValid || validLat === null || validLon === null) {
      setErrorMsg('Please enter valid responder coordinates (Lat: -90 to 90, Lon: -180 to 180).');
      return;
    }

    setIsAnalyzing(true);
    setErrorMsg(null);

    try {
      const res = await analyzeCriticalAccess({
        facility_id: selectedFacilityId,
        responder_origin: {
          latitude: validLat,
          longitude: validLon,
          label: originLabel,
        },
        critical_access_severity: 'HIGH',
      });
      setAccessData(res);
    } catch (err: any) {
      console.error('Critical Access analysis failed:', err);
      setAccessData(null);
      setErrorMsg(err.message || 'Network Error: Failed to fetch');
    } finally {
      setIsAnalyzing(false);
    }
  };

  const selectedFacility = facilities.find((f) => f.facility_id === selectedFacilityId);

  // Prepare map markers & polylines defensively
  const mapMarkers: any[] = [];
  const mapPolylines: any[] = [];
  const boundsPoints: [number, number][] = [];

  // Responder marker
  if (isCoordinatesValid && validLat !== null && validLon !== null) {
    mapMarkers.push({
      id: 'responder-origin',
      position: [validLat, validLon] as [number, number],
      color: '#16a34a', // Green responder pin
      title: 'Responder Unit',
      subtitle: originLabel,
      badge: 'R',
      popupContent: `<strong>${originLabel}</strong><br/>Lat: ${validLat.toFixed(4)}, Lon: ${validLon.toFixed(4)}`,
    });
    boundsPoints.push([validLat, validLon]);
  }

  // Facility marker
  if (selectedFacility) {
    mapMarkers.push({
      id: 'facility-target',
      position: [selectedFacility.latitude, selectedFacility.longitude] as [number, number],
      color: '#0284c7', // Aquora blue facility pin
      title: selectedFacility.name,
      subtitle: selectedFacility.category,
      badge: 'H',
      popupContent: `<strong>${selectedFacility.name}</strong><br/>Category: ${selectedFacility.category}<br/>Status: Operational`,
    });
    boundsPoints.push([selectedFacility.latitude, selectedFacility.longitude]);
  }

  // Route geometry overlays when assessment data exists
  if (accessData) {
    if (accessData.selected_route?.geometry_geojson?.coordinates) {
      const positions = accessData.selected_route.geometry_geojson.coordinates
        .filter(([lon, lat]: [number, number]) => !isNaN(lat) && !isNaN(lon))
        .map(([lon, lat]: [number, number]) => [lat, lon] as [number, number]);

      if (positions.length >= 2) {
        mapPolylines.push({
          id: 'primary-route',
          positions,
          color: accessData.current_access_status === 'COMPROMISED' ? '#dc2626' : '#0284c7',
          weight: 5,
          title: `Primary Route (${(accessData.selected_route.distance_m / 1000).toFixed(2)} km)`,
        });
        positions.forEach((p) => boundsPoints.push(p));
      }
    }

    if (accessData.alternate_route?.geometry_geojson?.coordinates) {
      const positions = accessData.alternate_route.geometry_geojson.coordinates
        .filter(([lon, lat]: [number, number]) => !isNaN(lat) && !isNaN(lon))
        .map(([lon, lat]: [number, number]) => [lat, lon] as [number, number]);

      if (positions.length >= 2) {
        mapPolylines.push({
          id: 'alternate-route',
          positions,
          color: '#d97706',
          weight: 4,
          dashArray: '6, 6',
          title: `Alternate Route (${(accessData.alternate_route.distance_m / 1000).toFixed(2)} km)`,
        });
        positions.forEach((p) => boundsPoints.push(p));
      }
    }
  }

  const mapCenter: [number, number] = selectedFacility
    ? [selectedFacility.latitude, selectedFacility.longitude]
    : [19.076, 72.8777];

  const currentBadge = accessData
    ? STATUS_BADGES[accessData.current_access_status] || STATUS_BADGES.UNKNOWN
    : STATUS_BADGES.UNKNOWN;

  return (
    <div className="space-y-6 pb-12 font-sans max-w-[1280px] mx-auto">

      {/* ── Page Header ─────────────────────────────────────── */}
      <div className="flex flex-col md:flex-row md:items-end justify-between gap-4">
        <div>
          <div className="flex items-center gap-3">
            <h1
              className="text-[1.75rem] font-extrabold leading-none tracking-tight"
              style={{ color: 'var(--aq-navy)', letterSpacing: '-0.02em' }}
            >
              CRITICAL ACCESS
            </h1>
            <div className="flex items-center gap-1.5 px-2.5 py-1 rounded-full bg-slate-100 text-[11px] font-semibold text-slate-600 border border-slate-200">
              <span className="w-2 h-2 rounded-full bg-emerald-500 animate-pulse" />
              <span>Live flood model</span>
            </div>
          </div>
          <p className="mt-1.5 text-[14px]" style={{ color: 'var(--aq-muted)' }}>
            Can responders reach essential facilities as flooding develops?
          </p>
        </div>

        <Button
          variant="primary"
          size="md"
          onClick={handleAnalyze}
          isLoading={isAnalyzing}
          disabled={!selectedFacilityId || !isCoordinatesValid}
          icon={<RefreshCw className="w-4 h-4" />}
          className="shadow-sm"
        >
          Analyse Access
        </Button>
      </div>

      {/* ── Facility + Responder Control Bar ────────────────── */}
      <Card padding="md" className="border shadow-xs">
        <div className="space-y-3">
          <div className="text-[12px] font-bold uppercase tracking-wider text-slate-400">
            Access Assessment
          </div>

          <div className="grid grid-cols-1 lg:grid-cols-12 gap-4 items-end">
            {/* Facility Selector */}
            <div className="lg:col-span-6">
              <label className="aq-label flex items-center gap-1.5 mb-1.5">
                <Building2 className="w-3.5 h-3.5 text-sky-600" />
                Target facility
              </label>

              {isLoadingFacilities ? (
                <div className="h-[38px] rounded-xl bg-slate-100 animate-pulse flex items-center px-3 text-[12px] text-slate-400">
                  Loading essential facilities...
                </div>
              ) : facilityError || facilities.length === 0 ? (
                <div className="flex items-center justify-between p-2 rounded-xl bg-amber-50 border border-amber-200 text-[12px] text-amber-800">
                  <span className="font-semibold">No facilities available</span>
                  <button
                    onClick={loadFacilities}
                    className="px-2 py-0.5 rounded bg-amber-200 hover:bg-amber-300 font-bold text-[11px] transition-colors"
                  >
                    Try again
                  </button>
                </div>
              ) : (
                <select
                  value={selectedFacilityId}
                  onChange={(e) => {
                    setSelectedFacilityId(e.target.value);
                    setAccessData(null);
                    setErrorMsg(null);
                  }}
                  className="w-full rounded-xl px-3 py-2 text-[13px] font-semibold focus:outline-none transition-all cursor-pointer"
                  style={{
                    background: '#f8fafc',
                    border: '1px solid rgba(15,35,64,0.14)',
                    color: 'var(--aq-text)',
                  }}
                >
                  {facilities.map((f) => (
                    <option key={f.facility_id} value={f.facility_id}>
                      {f.name} ({f.category})
                    </option>
                  ))}
                </select>
              )}
            </div>

            {/* Responder Starting Point Coordinates */}
            <div className="lg:col-span-4 grid grid-cols-2 gap-2">
              <div>
                <label className="aq-label block mb-1">Latitude</label>
                <input
                  type="text"
                  value={originLatInput}
                  onChange={(e) => setOriginLatInput(e.target.value)}
                  placeholder="19.0600"
                  className={`w-full rounded-xl px-3 py-1.5 text-[13px] font-semibold focus:outline-none transition-all ${
                    getValidLat(originLatInput) === null
                      ? 'border-red-400 bg-red-50 text-red-900'
                      : 'border-slate-200 bg-slate-50 text-slate-800'
                  }`}
                  style={{ border: '1px solid rgba(15,35,64,0.14)' }}
                />
              </div>

              <div>
                <label className="aq-label block mb-1">Longitude</label>
                <input
                  type="text"
                  value={originLonInput}
                  onChange={(e) => setOriginLonInput(e.target.value)}
                  placeholder="72.8650"
                  className={`w-full rounded-xl px-3 py-1.5 text-[13px] font-semibold focus:outline-none transition-all ${
                    getValidLon(originLonInput) === null
                      ? 'border-red-400 bg-red-50 text-red-900'
                      : 'border-slate-200 bg-slate-50 text-slate-800'
                  }`}
                  style={{ border: '1px solid rgba(15,35,64,0.14)' }}
                />
              </div>
            </div>

            {/* Analyse Action */}
            <div className="lg:col-span-2">
              <Button
                variant="primary"
                size="md"
                onClick={handleAnalyze}
                isLoading={isAnalyzing}
                disabled={!selectedFacilityId || !isCoordinatesValid}
                className="w-full"
              >
                Analyse access
              </Button>
            </div>
          </div>
        </div>
      </Card>

      {/* ── Main Access Workspace (Map + Assessment Result) ── */}
      <div className="grid grid-cols-1 lg:grid-cols-12 gap-6 items-start">

        {/* ── Left 7 Cols: Map Feature ────────────────────── */}
        <div className="lg:col-span-7 space-y-3">
          <div className="relative aq-map-container min-h-[480px] h-[520px] rounded-2xl border overflow-hidden shadow-sm">
            <LeafletMap
              center={mapCenter}
              zoom={13}
              bounds={boundsPoints.length >= 2 ? boundsPoints : undefined}
              markers={mapMarkers}
              polylines={mapPolylines}
              showFullscreenControl={true}
              height="100%"
            />

            {/* Floating Map Legend Overlay */}
            <div
              className="absolute bottom-4 left-4 z-[1000] bg-white/95 backdrop-blur-md p-3 rounded-xl border text-[11px] font-sans space-y-2 shadow-md max-w-[220px]"
              style={{ borderColor: 'rgba(15,35,64,0.12)' }}
            >
              <div className="font-bold text-slate-800 uppercase tracking-wider text-[10px] border-b pb-1">
                Map Legend
              </div>

              <div className="space-y-1">
                <div className="text-[10px] font-semibold text-slate-500">FLOOD CONDITIONS</div>
                <div className="flex items-center gap-2">
                  <div className="w-3 h-3 rounded bg-sky-500/60" />
                  <span className="text-slate-700">Active Flood Extent</span>
                </div>
              </div>

              <div className="space-y-1">
                <div className="text-[10px] font-semibold text-slate-500">ROUTE</div>
                <div className="flex items-center gap-2">
                  <div className="w-4 h-1 bg-sky-600 rounded" />
                  <span className="text-slate-700">Primary Route</span>
                </div>
                {accessData?.alternate_route && (
                  <div className="flex items-center gap-2">
                    <div className="w-4 h-0 border-t-2 border-dashed border-amber-600" />
                    <span className="text-slate-700">Alternate Route</span>
                  </div>
                )}
              </div>

              <div className="space-y-1">
                <div className="text-[10px] font-semibold text-slate-500">LOCATIONS</div>
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-emerald-600 border border-white" />
                  <span className="text-slate-700">Responder Origin</span>
                </div>
                <div className="flex items-center gap-2">
                  <div className="w-2.5 h-2.5 rounded-full bg-sky-600 border border-white" />
                  <span className="text-slate-700">Target Facility</span>
                </div>
              </div>
            </div>
          </div>
        </div>

        {/* ── Right 5 Cols: Key Decision Card ─────────────── */}
        <div className="lg:col-span-5 space-y-5">

          {/* 1. ERROR STATE (Honest error handling, NO fake fallback) */}
          {errorMsg ? (
            <Card padding="lg" className="border border-amber-200 bg-amber-50/50">
              <div className="flex flex-col items-center py-6 text-center space-y-3">
                <div className="w-12 h-12 rounded-full bg-amber-100 flex items-center justify-center text-amber-700">
                  <AlertTriangle className="w-6 h-6" />
                </div>
                <div className="space-y-1">
                  <h3 className="text-[15px] font-bold text-slate-900">
                    Couldn’t load the latest facility assessment.
                  </h3>
                  <p className="text-[12px] text-slate-600 font-mono">
                    {errorMsg}
                  </p>
                </div>
                <Button
                  variant="outline"
                  size="sm"
                  onClick={handleAnalyze}
                  isLoading={isAnalyzing}
                  className="mt-2 bg-white"
                >
                  Try again
                </Button>
              </div>
            </Card>

          ) : isAnalyzing ? (
            /* 2. LOADING STATE */
            <Card padding="lg">
              <div className="flex flex-col items-center py-10 text-center space-y-4">
                <RefreshCw className="w-8 h-8 text-sky-600 animate-spin" />
                <div className="space-y-1">
                  <h3 className="text-[14px] font-bold text-slate-900">Analysing access…</h3>
                  <p className="text-[12px] text-slate-500">
                    Computing OSRM route geometry and digital twin flood risk...
                  </p>
                </div>
              </div>
            </Card>

          ) : !accessData ? (
            /* 3. BEFORE ANALYSIS / IDLE STATE */
            <Card padding="lg" className="border border-slate-200">
              <div className="flex flex-col items-center py-8 text-center space-y-4">
                <div className="w-12 h-12 rounded-2xl bg-sky-50 flex items-center justify-center text-sky-600">
                  <Compass className="w-6 h-6" />
                </div>
                <div className="space-y-1.5 max-w-sm">
                  <h3 className="text-[15px] font-bold text-slate-900 uppercase tracking-wide">
                    ACCESS ASSESSMENT
                  </h3>
                  <p className="text-[13px] text-slate-600 leading-relaxed">
                    Select a facility and responder starting point, then analyse access through the current flood outlook.
                  </p>
                </div>
                {selectedFacility && (
                  <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 text-left w-full text-[12px]">
                    <div className="text-[10px] font-bold text-slate-400 uppercase">Selected Facility</div>
                    <div className="font-bold text-slate-800 mt-0.5">{selectedFacility.name}</div>
                    <div className="text-slate-500">{selectedFacility.category}</div>
                  </div>
                )}
                <Button
                  variant="primary"
                  size="md"
                  onClick={handleAnalyze}
                  className="w-full"
                >
                  Analyse access
                </Button>
              </div>
            </Card>

          ) : (
            /* 4. SUCCESS ASSESSMENT RESULT PANEL */
            <div className="space-y-4">

              {/* Access Status Card */}
              <Card padding="lg" className="space-y-5 border shadow-sm">
                <div className="flex items-center justify-between pb-3 border-b border-slate-100">
                  <div>
                    <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400">
                      Access Assessment
                    </div>
                    <div className="text-[15px] font-bold text-slate-900 mt-0.5">
                      {accessData.facility.name}
                    </div>
                  </div>
                  <Badge variant={currentBadge.badge} size="md">
                    {currentBadge.text}
                  </Badge>
                </div>

                {/* Primary Answer & Explanation */}
                <div
                  className="p-4 rounded-xl border space-y-2"
                  style={{ background: currentBadge.bg, borderColor: `${currentBadge.color}30` }}
                >
                  <div className="text-[11px] font-bold uppercase tracking-wider" style={{ color: currentBadge.color }}>
                    ACCESS STATUS
                  </div>
                  <div className="text-[16px] font-extrabold" style={{ color: currentBadge.color }}>
                    {currentBadge.text}
                  </div>
                  {accessData.explanation && (
                    <p className="text-[12.5px] leading-relaxed font-medium text-slate-800 pt-1">
                      {accessData.explanation}
                    </p>
                  )}
                </div>

                {/* Onset / Window Timing */}
                {(accessData.modeled_loss_of_access_min != null || accessData.time_to_loss_of_access_min != null) && (
                  <div className="p-3.5 rounded-xl bg-slate-50 border border-slate-200/80 flex items-center justify-between">
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4 text-sky-600" />
                      <div>
                        <div className="text-[11px] font-bold text-slate-500 uppercase">Access Window</div>
                        <div className="text-[13px] font-bold text-slate-800">
                          {accessData.modeled_loss_of_access_min != null
                            ? `Expected loss of access: +${accessData.modeled_loss_of_access_min} min`
                            : accessData.time_to_loss_of_access_min != null
                            ? `Access risk onset: +${accessData.time_to_loss_of_access_min} min`
                            : 'No disruption detected within forecast horizon'}
                        </div>
                      </div>
                    </div>
                  </div>
                )}

                {/* Route Information */}
                <div className="space-y-3 pt-1">
                  <div className="text-[12px] font-bold uppercase tracking-wider text-slate-400">
                    Route Information
                  </div>

                  {/* Primary Route */}
                  {accessData.selected_route ? (
                    <div className="p-3 rounded-xl bg-slate-50 border border-slate-200/80 space-y-2 text-[12px]">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-slate-800 flex items-center gap-1.5">
                          <Navigation className="w-3.5 h-3.5 text-sky-600" />
                          PRIMARY ROUTE
                        </span>
                        <span className="px-2 py-0.5 rounded bg-sky-100 text-sky-800 text-[10px] font-bold">
                          {accessData.selected_route.provider || 'OSRM'}
                        </span>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
                        <div>
                          <span className="text-slate-500">Distance:</span>{' '}
                          <strong className="text-slate-800">
                            {(accessData.selected_route.distance_m / 1000).toFixed(2)} km
                          </strong>
                        </div>
                        <div>
                          <span className="text-slate-500">Travel time:</span>{' '}
                          <strong className="text-slate-800">
                            {(accessData.selected_route.estimated_duration_s / 60).toFixed(1)} min
                          </strong>
                        </div>
                        {accessData.selected_route.travel_window && (
                          <>
                            <div>
                              <span className="text-slate-500">Route status:</span>{' '}
                              <strong className="text-slate-800">
                                {accessData.selected_route.travel_window.status || 'Active'}
                              </strong>
                            </div>
                            <div>
                              <span className="text-slate-500">Usable window:</span>{' '}
                              <strong className="text-slate-800">
                                {accessData.selected_route.travel_window.usable_travel_window_min != null
                                  ? `${accessData.selected_route.travel_window.usable_travel_window_min} min`
                                  : 'Full horizon'}
                              </strong>
                            </div>
                          </>
                        )}
                      </div>
                    </div>
                  ) : (
                    <div className="text-[12px] text-slate-500 italic p-3 bg-slate-50 rounded-xl">
                      No primary route calculated.
                    </div>
                  )}

                  {/* Alternate Route */}
                  {accessData.alternate_route ? (
                    <div className="p-3 rounded-xl bg-amber-50/50 border border-amber-200 space-y-2 text-[12px]">
                      <div className="flex items-center justify-between">
                        <span className="font-bold text-amber-900 flex items-center gap-1.5">
                          <ArrowRightLeft className="w-3.5 h-3.5 text-amber-600" />
                          ALTERNATE ROUTE
                        </span>
                        <span className="px-2 py-0.5 rounded bg-amber-100 text-amber-800 text-[10px] font-bold">
                          Available
                        </span>
                      </div>
                      <div className="grid grid-cols-2 gap-2 text-[11px] pt-1">
                        <div>
                          <span className="text-slate-500">Distance:</span>{' '}
                          <strong className="text-slate-800">
                            {(accessData.alternate_route.distance_m / 1000).toFixed(2)} km
                          </strong>
                        </div>
                        <div>
                          <span className="text-slate-500">Travel time:</span>{' '}
                          <strong className="text-slate-800">
                            {(accessData.alternate_route.estimated_duration_s / 60).toFixed(1)} min
                          </strong>
                        </div>
                      </div>
                      {accessData.alternate_route.summary && (
                        <div className="text-[11px] text-amber-800 italic pt-1 border-t border-amber-200/60">
                          {accessData.alternate_route.summary}
                        </div>
                      )}
                    </div>
                  ) : (
                    <div className="text-[11px] text-slate-500 italic px-1">
                      No alternate route returned.
                    </div>
                  )}
                </div>

                {/* Structured Risk Reasons (Only rendered if backend provides recommendation) */}
                {accessData.recommendation && (
                  <div className="pt-2 border-t border-slate-100">
                    <div className="text-[10px] font-bold uppercase tracking-wider text-slate-400 mb-1.5">
                      Recommendation
                    </div>
                    <div className="text-[12px] font-semibold text-slate-700 bg-slate-50 p-2.5 rounded-lg border border-slate-200/60">
                      {accessData.recommendation.replace(/_/g, ' ')}
                    </div>
                  </div>
                )}
              </Card>

              {/* Access Timeline Card */}
              {accessData.accessibility_timeline && accessData.accessibility_timeline.length > 0 && (
                <Card padding="md" className="space-y-3">
                  <div className="flex items-center justify-between pb-2 border-b border-slate-100">
                    <div className="flex items-center gap-2">
                      <Clock className="w-4 h-4 text-sky-600" />
                      <span className="text-[12px] font-bold text-slate-800 uppercase tracking-wider">
                        Access Timeline
                      </span>
                    </div>
                    <span className="text-[10px] font-semibold text-slate-400">
                      Forecast Horizon
                    </span>
                  </div>

                  <div className="space-y-1.5 pt-1">
                    {accessData.accessibility_timeline.map((entry) => {
                      const stBadge = STATUS_BADGES[entry.accessibility_status] || STATUS_BADGES.UNKNOWN;
                      return (
                        <div
                          key={entry.minutes_from_start}
                          className="flex items-center justify-between text-[12px] p-2 rounded-lg bg-slate-50 hover:bg-slate-100 transition-colors"
                        >
                          <span className="font-mono font-bold text-slate-600 w-14">
                            {entry.minutes_from_start === 0 ? 'NOW' : `+${entry.minutes_from_start}m`}
                          </span>
                          <Badge variant={stBadge.badge} size="sm">
                            {stBadge.text}
                          </Badge>
                        </div>
                      );
                    })}
                  </div>
                </Card>
              )}
            </div>
          )}
        </div>
      </div>
    </div>
  );
};

export default CriticalAccessFeature;
