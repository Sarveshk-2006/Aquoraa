"""
Routing Provider Implementations for Phase 10 Flood-Aware Routing.

Defines abstract BaseRoutingProvider and implementations:
1. SyntheticRoutingProvider — Deterministic spatial route generator for development & testing.
2. OSRMRoutingProvider — HTTP client for Open Source Routing Machine (OSRM).
"""

import math
from abc import ABC, abstractmethod

from app.core.config import settings
from app.core.logging import logger


class RouteCandidateResult:
    """Container for candidate route geometry and duration metadata from routing provider."""

    def __init__(
        self,
        route_id: str,
        coordinates: list[list[float]],  # [[lon, lat], ...]
        distance_m: float,
        estimated_duration_s: float,
        provider: str,
        provider_mode: str,
        summary: str | None = None,
    ):
        self.route_id = route_id
        self.coordinates = coordinates
        self.distance_m = distance_m
        self.estimated_duration_s = estimated_duration_s
        self.provider = provider
        self.provider_mode = provider_mode
        self.summary = summary


class BaseRoutingProvider(ABC):
    """Abstract interface for routing engine connectors."""

    @abstractmethod
    async def compute_routes(
        self,
        origin: dict[str, float],
        destination: dict[str, float],
        max_alternatives: int = 3,
    ) -> list[RouteCandidateResult]:
        """Compute candidate routes between origin and destination."""


def _haversine_distance_m(lat1: float, lon1: float, lat2: float, lon2: float) -> float:
    """Compute approximate geodesic distance in meters using Haversine formula."""
    r = 6371000.0  # Earth radius in meters
    d_lat = math.radians(lat2 - lat1)
    d_lon = math.radians(lon2 - lon1)
    a = math.sin(d_lat / 2.0) ** 2 + math.cos(math.radians(lat1)) * math.cos(math.radians(lat2)) * math.sin(d_lon / 2.0) ** 2
    c = 2.0 * math.atan2(math.sqrt(a), math.sqrt(1.0 - a))
    return r * c


class SyntheticRoutingProvider(BaseRoutingProvider):
    """
    Deterministic synthetic routing provider for development and testing.
    Accepts arbitrary valid EPSG:4326 origin & destination coordinates.
    Never uses hard-coded city restrictions. Explicitly tags outputs as SYNTHETIC / DEVELOPMENT_ONLY.
    """

    def __init__(self):
        self.provider_id = "SYNTHETIC_ROUTER"
        self.provider_mode = "SYNTHETIC"
        self.environment = "DEVELOPMENT_ONLY"

    async def compute_routes(
        self,
        origin: dict[str, float],
        destination: dict[str, float],
        max_alternatives: int = 3,
    ) -> list[RouteCandidateResult]:
        lat1, lon1 = origin["lat"], origin["lon"]
        lat2, lon2 = destination["lat"], destination["lon"]

        direct_dist = _haversine_distance_m(lat1, lon1, lat2, lon2)
        # Average urban driving speed: 25 km/h = ~6.94 m/s
        direct_duration = direct_dist / 6.94

        candidates: list[RouteCandidateResult] = []

        # Candidate 1: Direct Spatial Waypoints Line (10 interpolated waypoints)
        coords_c1: list[list[float]] = []
        num_pts = 12
        for i in range(num_pts):
            t = i / (num_pts - 1)
            wpt_lat = lat1 + t * (lat2 - lat1)
            wpt_lon = lon1 + t * (lon2 - lon1)
            coords_c1.append([round(wpt_lon, 6), round(wpt_lat, 6)])

        candidates.append(
            RouteCandidateResult(
                route_id="route_primary_direct",
                coordinates=coords_c1,
                distance_m=round(direct_dist, 1),
                estimated_duration_s=round(direct_duration, 1),
                provider=self.provider_id,
                provider_mode=self.provider_mode,
                summary="Primary Direct Route (Synthetic)",
            )
        )

        # Candidate 2: Detour A (Northern Arc Waypoint offset)
        if max_alternatives >= 2:
            mid_lat = (lat1 + lat2) / 2.0 + 0.008
            mid_lon = (lon1 + lon2) / 2.0 - 0.004

            coords_c2: list[list[float]] = []
            for i in range(num_pts):
                t = i / (num_pts - 1)
                if t < 0.5:
                    sub_t = t * 2.0
                    wpt_lat = lat1 + sub_t * (mid_lat - lat1)
                    wpt_lon = lon1 + sub_t * (mid_lon - lon1)
                else:
                    sub_t = (t - 0.5) * 2.0
                    wpt_lat = mid_lat + sub_t * (lat2 - mid_lat)
                    wpt_lon = mid_lon + sub_t * (lon2 - mid_lon)
                coords_c2.append([round(wpt_lon, 6), round(wpt_lat, 6)])

            alt1_dist = direct_dist * 1.18
            alt1_duration = alt1_dist / 6.94

            candidates.append(
                RouteCandidateResult(
                    route_id="route_alt_northern_detour",
                    coordinates=coords_c2,
                    distance_m=round(alt1_dist, 1),
                    estimated_duration_s=round(alt1_duration, 1),
                    provider=self.provider_id,
                    provider_mode=self.provider_mode,
                    summary="Alternate Route via Northern Corridor (Synthetic)",
                )
            )

        # Candidate 3: Detour B (Southern Arc Waypoint offset)
        if max_alternatives >= 3:
            mid_lat = (lat1 + lat2) / 2.0 - 0.008
            mid_lon = (lon1 + lon2) / 2.0 + 0.005

            coords_c3: list[list[float]] = []
            for i in range(num_pts):
                t = i / (num_pts - 1)
                if t < 0.5:
                    sub_t = t * 2.0
                    wpt_lat = lat1 + sub_t * (mid_lat - lat1)
                    wpt_lon = lon1 + sub_t * (mid_lon - lon1)
                else:
                    sub_t = (t - 0.5) * 2.0
                    wpt_lat = mid_lat + sub_t * (lat2 - mid_lat)
                    wpt_lon = mid_lon + sub_t * (lon2 - mid_lon)
                coords_c3.append([round(wpt_lon, 6), round(wpt_lat, 6)])

            alt2_dist = direct_dist * 1.30
            alt2_duration = alt2_dist / 6.94

            candidates.append(
                RouteCandidateResult(
                    route_id="route_alt_southern_detour",
                    coordinates=coords_c3,
                    distance_m=round(alt2_dist, 1),
                    estimated_duration_s=round(alt2_duration, 1),
                    provider=self.provider_id,
                    provider_mode=self.provider_mode,
                    summary="Alternate Route via Southern Bypass (Synthetic)",
                )
            )

        logger.info(
            "Computed synthetic routes",
            provider=self.provider_id,
            num_candidates=len(candidates),
            direct_dist_m=direct_dist,
        )
        return candidates


class OSRMRoutingProvider(BaseRoutingProvider):
    """
    HTTP client provider for Open Source Routing Machine (OSRM).
    Connects to external OSRM service with bounded timeouts and graceful error handling.
    """

    def __init__(self, base_url: str | None = None, timeout_seconds: float | None = None):
        self.provider_id = "OSRM_ROUTER"
        self.provider_mode = "LIVE_OSRM"
        self.base_url = base_url or settings.ROUTING_BASE_URL
        self.timeout_seconds = timeout_seconds or settings.ROUTING_TIMEOUT_SECONDS

    async def compute_routes(
        self,
        origin: dict[str, float],
        destination: dict[str, float],
        max_alternatives: int = 3,
    ) -> list[RouteCandidateResult]:
        import httpx

        url = f"{self.base_url.rstrip('/')}/route/v1/driving/{origin['lon']},{origin['lat']};{destination['lon']},{destination['lat']}"
        params = {
            "overview": "full",
            "geometries": "geojson",
            "alternatives": "true" if max_alternatives > 1 else "false",
        }

        try:
            async with httpx.AsyncClient(timeout=self.timeout_seconds) as client:
                resp = await client.get(url, params=params)
                if resp.status_code != 200:
                    raise RuntimeError(f"OSRM HTTP error {resp.status_code}: {resp.text}")

                data = resp.json()
                if data.get("code") != "Ok" or not data.get("routes"):
                    raise RuntimeError(f"OSRM routing error: {data.get('message', 'No routes found')}")

                results: list[RouteCandidateResult] = []
                for idx, r in enumerate(data["routes"]):
                    route_id = f"osrm_route_{idx + 1}"
                    coords = r["geometry"]["coordinates"]
                    dist = float(r["distance"])
                    dur = float(r["duration"])

                    results.append(
                        RouteCandidateResult(
                            route_id=route_id,
                            coordinates=coords,
                            distance_m=dist,
                            estimated_duration_s=dur,
                            provider=self.provider_id,
                            provider_mode=self.provider_mode,
                            summary=f"OSRM Route #{idx + 1}",
                        )
                    )
                return results
        except Exception as err:
            logger.warning("OSRM provider request failed", error=str(err), base_url=self.base_url)
            raise RuntimeError(f"OSRM routing provider unavailable: {err}") from err
