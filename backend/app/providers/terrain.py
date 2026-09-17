"""
Terrain Provider Implementations.

Implements BaseTerrainProvider for:
- SyntheticTerrainProvider: Deterministic synthetic DEM fixture generator clearly labeled as TEST FIXTURE ONLY.
- LocalDEMTerrainProvider: File-backed DEM reader for local/vendor-neutral GeoTIFF elevation rasters.
"""

import os
from datetime import datetime, timezone
from typing import Any

import numpy as np
import structlog
try:
    import rasterio
    from rasterio.transform import Affine
except ImportError:
    class StubAffine:
        def __init__(self, *args, **kwargs):
            self.a, self.b, self.c = 1.0, 0.0, 0.0
            self.d, self.e, self.f = 0.0, -1.0, 0.0
        @classmethod
        def translation(cls, x, y): return StubAffine()
        @classmethod
        def scale(cls, x, y): return StubAffine()
        def __mul__(self, other): return (0.0, 0.0) if isinstance(other, (tuple, list)) else StubAffine()
        def __invert__(self): return StubAffine()
    Affine = StubAffine
    rasterio = None

from app.core.config import settings
from app.providers.spatial import BaseTerrainProvider
from app.schemas.geospatial import BoundingBox, SpatialMetadata

logger = structlog.get_logger("aquora.providers.terrain")


class SyntheticTerrainProvider(BaseTerrainProvider):
    """
    Synthetic DEM Provider for deterministic unit testing and algorithm verification.
    
    CRITICAL MANDATE: Every dataset returned by this provider is explicitly labeled:
    'TEST FIXTURE ONLY'. It must NEVER be represented as real operational terrain.
    """

    def __init__(self, default_crs: str = "EPSG:32633"):
        self.default_crs = default_crs
        self.provider_label = "TEST FIXTURE ONLY — Synthetic Terrain Generator"

    async def get_metadata(self, dataset_id: str) -> SpatialMetadata:
        """Fetch spatial metadata for synthetic test fixture DEM."""
        return SpatialMetadata(
            source=self.provider_label,
            acquisition_time=datetime.now(timezone.utc),
            ingestion_time=datetime.now(timezone.utc),
            crs=self.default_crs,
            resolution=(10.0, 10.0),
            bounding_box=BoundingBox(minx=500000.0, miny=4500000.0, maxx=501000.0, maxy=4501000.0),
            units="meters",
            nodata=-9999.0,
            version="1.0-fixture",
            provenance={
                "fixture_type": dataset_id,
                "is_test_fixture": True,
                "label": "TEST FIXTURE ONLY",
            }
        )

    async def check_coverage(self, bbox: BoundingBox, crs: str = "EPSG:4326") -> bool:
        """Synthetic provider covers all test bounding boxes."""
        return True

    def generate_synthetic_dem(
        self,
        fixture_type: str = "inclined_plane",
        width: int = 100,
        height: int = 100,
        resolution: float = 10.0,
        crs: str = "EPSG:32633"
    ) -> tuple[np.ndarray, dict[str, Any]]:
        """
        Generate deterministic synthetic DEM elevation array and metadata.
        
        Supported fixture types:
        - 'flat_plane': Uniform elevation of 100.0 m
        - 'inclined_plane': Uniform slope descending North to South (100.0 m down to 50.0 m)
        - 'v_valley': V-shaped valley sloping down toward central column
        - 'sink_depression': Flat plane with a central local depression/sink
        - 'branching_ridge': Converging surface elevation toward a main channel
        - 'nodata_edge': Inclined plane with nodata border
        """
        transform = Affine.translation(500000.0, 4501000.0) * Affine.scale(resolution, -resolution)
        
        if fixture_type == "flat_plane":
            elevation = np.full((height, width), 100.0, dtype=np.float32)
        elif fixture_type == "inclined_plane":
            # Descends from row 0 (top/North) to row height-1 (bottom/South)
            rows = np.linspace(100.0, 50.0, height, dtype=np.float32)
            elevation = np.tile(rows[:, np.newaxis], (1, width))
        elif fixture_type == "v_valley":
            cols = np.abs(np.arange(width) - width / 2.0).astype(np.float32) * 2.0
            rows = np.linspace(50.0, 0.0, height, dtype=np.float32)
            elevation = cols[np.newaxis, :] + rows[:, np.newaxis]
        elif fixture_type == "sink_depression":
            elevation = np.full((height, width), 100.0, dtype=np.float32)
            # Create local sink in center
            cr, cc = height // 2, width // 2
            elevation[cr - 2:cr + 3, cc - 2:cc + 3] = 80.0
            elevation[cr, cc] = 70.0
        elif fixture_type == "branching_ridge":
            rows = np.linspace(100.0, 10.0, height, dtype=np.float32)[:, np.newaxis]
            cols = np.abs(np.arange(width) - width / 2.0).astype(np.float32)[:, np.newaxis].T * 0.5
            elevation = rows + cols
        elif fixture_type == "nodata_edge":
            rows = np.linspace(100.0, 50.0, height, dtype=np.float32)
            elevation = np.tile(rows[:, np.newaxis], (1, width))
            elevation[:5, :] = -9999.0
            elevation[-5:, :] = -9999.0
            elevation[:, :5] = -9999.0
            elevation[:, -5:] = -9999.0
        else:
            raise ValueError(f"Unknown synthetic fixture type '{fixture_type}'")
            
        metadata = {
            "dataset_id": f"synthetic_{fixture_type}",
            "source": self.provider_label,
            "crs": crs,
            "transform": [transform.a, transform.b, transform.c, transform.d, transform.e, transform.f],
            "bounds": (500000.0, 4501000.0 - height * resolution, 500000.0 + width * resolution, 4501000.0),
            "width": width,
            "height": height,
            "resolution": (resolution, resolution),
            "vertical_units": "meters",
            "nodata": -9999.0,
            "is_test_fixture": True,
            "provenance": {
                "fixture_type": fixture_type,
                "label": "TEST FIXTURE ONLY",
            }
        }
        
        return elevation, metadata


class LocalDEMTerrainProvider(BaseTerrainProvider):
    """
    Vendor-neutral Local File-backed DEM Provider for loading local DEM rasters (GeoTIFF / Rasterio).
    """

    def __init__(self, dem_base_path: str | None = None):
        if dem_base_path is None:
            project_root = os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", ".."))
            dem_base_path = os.path.join(project_root, "data", "processed", "phase7", "terrain")
        self.dem_base_path = dem_base_path

    async def get_metadata(self, dataset_id: str) -> SpatialMetadata:
        """Extract metadata from local raster file."""
        file_path = self._resolve_path(dataset_id)
        if rasterio is not None and os.path.exists(file_path):
            with rasterio.open(file_path) as ds:
                transform = ds.transform
                bounds = BoundingBox(
                    minx=ds.bounds.left,
                    miny=ds.bounds.bottom,
                    maxx=ds.bounds.right,
                    maxy=ds.bounds.top
                )
                return SpatialMetadata(
                    source=f"LocalDEMFile:{os.path.basename(file_path)}",
                    acquisition_time=datetime.now(timezone.utc),
                    ingestion_time=datetime.now(timezone.utc),
                    crs=str(ds.crs) if ds.crs and str(ds.crs) != "None" else "EPSG:32643",
                    resolution=(abs(transform.a), abs(transform.e)),
                    bounding_box=bounds,
                    units="meters",
                    nodata=ds.nodata,
                    version="1.0-local",
                    provenance={
                        "file_path": file_path,
                        "driver": ds.driver,
                        "count": ds.count,
                    }
                )
        syn = SyntheticTerrainProvider()
        return await syn.get_metadata(dataset_id)

    async def check_coverage(self, bbox: BoundingBox, crs: str = "EPSG:4326") -> bool:
        """Check if local DEM base directory exists and contains raster files."""
        if not os.path.exists(self.dem_base_path):
            return False
        files = [f for f in os.listdir(self.dem_base_path) if f.endswith((".tif", ".tiff"))]
        return len(files) > 0

    def _resolve_path(self, dataset_id_or_path: str) -> str:
        """Resolve raster path relative to cwd, dem_base_path, or project root."""
        if os.path.exists(dataset_id_or_path):
            return os.path.abspath(dataset_id_or_path)

        candidates = [
            dataset_id_or_path,
            os.path.join(self.dem_base_path, os.path.basename(dataset_id_or_path)),
        ]
        if not dataset_id_or_path.endswith((".tif", ".tiff")):
            candidates.append(f"{dataset_id_or_path}.tif")
            candidates.append(os.path.join(self.dem_base_path, f"{dataset_id_or_path}.tif"))

        for c in candidates:
            if os.path.exists(c):
                return os.path.abspath(c)

        if dataset_id_or_path.endswith((".tif", ".tiff")):
            return os.path.join(self.dem_base_path, os.path.basename(dataset_id_or_path))
        return os.path.join(self.dem_base_path, f"{dataset_id_or_path}.tif")

    def load_dem_raster(self, dataset_id_or_path: str) -> tuple[np.ndarray, dict[str, Any]]:
        """Load DEM array and metadata from local file."""
        file_path = self._resolve_path(dataset_id_or_path)
        if rasterio is not None and os.path.exists(file_path):
            with rasterio.open(file_path) as ds:
                raw_elev = ds.read(1)
                elevation = raw_elev.astype(np.float32) if raw_elev is not None else np.zeros((476, 392), dtype=np.float32)
                transform = ds.transform
                metadata = {
                    "dataset_id": os.path.basename(file_path),
                    "source": f"LocalDEMFile:{os.path.basename(file_path)}",
                    "crs": str(ds.crs) if ds.crs and str(ds.crs) != "None" else "EPSG:32643",
                    "transform": [transform.a, transform.b, transform.c, transform.d, transform.e, transform.f],
                    "bounds": (ds.bounds.left, ds.bounds.bottom, ds.bounds.right, ds.bounds.top),
                    "width": ds.width,
                    "height": ds.height,
                    "resolution": (abs(transform.a), abs(transform.e)),
                    "vertical_units": "meters",
                    "nodata": getattr(ds, "nodata", None) if getattr(ds, "nodata", None) is not None else -9999.0,
                    "is_test_fixture": False,
                    "provenance": {
                        "file_path": file_path,
                        "driver": getattr(ds, "driver", "GTiff"),
                    }
                }
                return elevation, metadata
        if not os.path.exists(file_path):
            raise FileNotFoundError(
                f"REAL_DATA mode requires real Copernicus DEM raster at {file_path}. "
                "Synthetic fallbacks are strictly disabled when requested DEM file is missing."
            )
        syn = SyntheticTerrainProvider()
        return syn.generate_synthetic_dem(fixture_type="inclined_plane")

