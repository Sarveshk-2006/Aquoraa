import { apiFetch } from './client';

export interface RouteLocation {
  latitude: number;
  longitude: number;
  label?: string;
}

export interface TravelWindow {
  estimated_travel_time_min: number;
  route_flood_onset_min?: number | null;
  safety_buffer_min: number;
  usable_travel_window_min?: number | null;
  status: string;
}

export interface TimeSliceExposure {
  minutes_from_start: number;
  status: string;
  affected_distance_m: number;
  affected_percentage: number;
  peak_severity: string;
  peak_water_depth_m: number;
  first_affected_km?: number | null;
  unknown_percentage: number;
}

export interface RouteSegment {
  segment_id: string;
  start_coordinates: [number, number];
  end_coordinates: [number, number];
  severity: string;
  water_depth_m: number;
  grid_cell_id: string;
  is_unknown: boolean;
}

export interface RouteCandidate {
  route_id: string;
  summary: string;
  provider: string;
  provider_mode: string;
  distance_m: number;
  estimated_duration_s: number;
  geometry_geojson: {
    type: string;
    coordinates: [number, number][];
  };
  travel_window: TravelWindow;
  recommendation: string;
  explanation: string;
  time_slice_exposures: TimeSliceExposure[];
  segments: RouteSegment[];
}

export interface RouteAnalysisResponse {
  run_id: string;
  digital_twin_run_id: string;
  recommended_route_id: string;
  recommendation: string;
  explanation: string;
  travel_window: TravelWindow;
  candidates: RouteCandidate[];
  warnings: string[];
  provenance: Record<string, any>;
}

export async function analyzeFloodAwareRoutes(payload: {
  origin: RouteLocation;
  destination: RouteLocation;
  digital_twin_run_id?: string;
  max_acceptable_severity?: string;
  max_alternatives?: number;
}): Promise<RouteAnalysisResponse> {
  return apiFetch<RouteAnalysisResponse>('/api/v1/routing/routes/analyze', {
    method: 'POST',
    headers: { 'Content-Type': 'application/json' },
    body: JSON.stringify(payload),
  });
}

export async function fetchLatestRoutingRun(): Promise<RouteAnalysisResponse> {
  return apiFetch<RouteAnalysisResponse>('/api/v1/routing/runs/latest');
}
