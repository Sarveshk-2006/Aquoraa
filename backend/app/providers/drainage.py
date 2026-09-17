"""
Drainage Network Data Providers.

Implements BaseDrainageProvider for:
- SyntheticDrainageProvider: Deterministic synthetic drainage fixture generator explicitly labeled TEST FIXTURE ONLY.
- LocalDrainageProvider: Vendor-neutral vector file reader (GeoPackage / GeoJSON / Shapefile) for local drainage datasets.
"""

import os
from datetime import datetime, timezone
from typing import Any

import structlog

from app.geospatial.drainage import DirectionStatus, LinkType, NodeType
from app.providers.spatial import BoundingBox, SpatialMetadata

logger = structlog.get_logger("aquora.providers.drainage")


class BaseDrainageProvider:
    """
    Abstract Base Class for drainage network data acquisition providers.
    """

    async def get_metadata(self, dataset_id: str) -> SpatialMetadata:
        raise NotImplementedError

    async def check_coverage(self, bbox: BoundingBox, crs: str = "EPSG:4326") -> bool:
        raise NotImplementedError


class SyntheticDrainageProvider(BaseDrainageProvider):
    """
    Synthetic Drainage Provider for deterministic unit testing and algorithm verification.
    
    CRITICAL MANDATE: Every dataset returned by this provider is explicitly labeled:
    'TEST FIXTURE ONLY'. It must NEVER be represented as real operational municipal infrastructure.
    """

    def __init__(self, default_crs: str = "EPSG:32633"):
        self.default_crs = default_crs
        self.provider_label = "TEST FIXTURE ONLY — Synthetic Drainage Network Generator"

    async def get_metadata(self, dataset_id: str) -> SpatialMetadata:
        """Fetch spatial metadata for synthetic test fixture network."""
        return SpatialMetadata(
            source=self.provider_label,
            acquisition_time=datetime.now(timezone.utc),
            ingestion_time=datetime.now(timezone.utc),
            crs=self.default_crs,
            resolution=(1.0, 1.0),
            bounding_box=BoundingBox(minx=500000.0, miny=4500000.0, maxx=501000.0, maxy=4501000.0),
            units="meters",
            nodata=None,
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

    def generate_synthetic_network(
        self,
        fixture_type: str = "simple_chain",
        crs: str = "EPSG:32633"
    ) -> tuple[list[dict[str, Any]], list[dict[str, Any]], dict[str, Any]]:
        """
        Generate deterministic synthetic drainage nodes, links, and dataset metadata.
        
        Supported fixture types:
        - 'simple_chain': Linear N1 -> N2 -> N3 -> OUT
        - 'branching_network': Converging network N1 -> N2 -> N4, N3 -> N2
        - 'disconnected_component': N1 -> N2 -> OUT and disconnected X1 -> X2
        - 'missing_endpoint': Link referencing non-existent node (ORPHAN)
        - 'loop_topology': Self-loop or cyclic loop
        - 'unknown_direction': Network with UNKNOWN direction status
        """
        nodes = []
        links = []
        
        if fixture_type == "simple_chain":
            nodes = [
                {"node_id": "N1", "node_type": NodeType.INLET.value, "x": 500000.0, "y": 4501000.0, "elevation_m": 100.0, "invert_elevation_m": 98.0},
                {"node_id": "N2", "node_type": NodeType.MANHOLE.value, "x": 500100.0, "y": 4501000.0, "elevation_m": 95.0, "invert_elevation_m": 93.0},
                {"node_id": "N3", "node_type": NodeType.JUNCTION.value, "x": 500200.0, "y": 4501000.0, "elevation_m": 90.0, "invert_elevation_m": 88.0},
                {"node_id": "OUT1", "node_type": NodeType.OUTFALL.value, "x": 500300.0, "y": 4501000.0, "elevation_m": 85.0, "invert_elevation_m": 83.0},
            ]
            links = [
                {"link_id": "L1", "from_node_id": "N1", "to_node_id": "N2", "link_type": LinkType.PIPE.value, "length_m": 100.0, "diameter_m": 0.6, "capacity_m3s": 1.5, "coords": [(500000.0, 4501000.0), (500100.0, 4501000.0)], "direction_status": DirectionStatus.KNOWN.value},
                {"link_id": "L2", "from_node_id": "N2", "to_node_id": "N3", "link_type": LinkType.PIPE.value, "length_m": 100.0, "diameter_m": 0.8, "capacity_m3s": 2.5, "coords": [(500100.0, 4501000.0), (500200.0, 4501000.0)], "direction_status": DirectionStatus.KNOWN.value},
                {"link_id": "L3", "from_node_id": "N3", "to_node_id": "OUT1", "link_type": LinkType.CONDUIT.value, "length_m": 100.0, "diameter_m": 1.0, "capacity_m3s": 4.0, "coords": [(500200.0, 4501000.0), (500300.0, 4501000.0)], "direction_status": DirectionStatus.KNOWN.value},
            ]
        elif fixture_type == "branching_network":
            nodes = [
                {"node_id": "N1", "node_type": NodeType.INLET.value, "x": 500000.0, "y": 4501100.0, "elevation_m": 100.0},
                {"node_id": "N2", "node_type": NodeType.INLET.value, "x": 500000.0, "y": 4500900.0, "elevation_m": 100.0},
                {"node_id": "N3", "node_type": NodeType.JUNCTION.value, "x": 500200.0, "y": 4501000.0, "elevation_m": 90.0},
                {"node_id": "OUT1", "node_type": NodeType.OUTFALL.value, "x": 500400.0, "y": 4501000.0, "elevation_m": 80.0},
            ]
            links = [
                {"link_id": "L1", "from_node_id": "N1", "to_node_id": "N3", "link_type": LinkType.PIPE.value, "length_m": 223.6, "coords": [(500000.0, 4501100.0), (500200.0, 4501000.0)], "direction_status": DirectionStatus.KNOWN.value},
                {"link_id": "L2", "from_node_id": "N2", "to_node_id": "N3", "link_type": LinkType.PIPE.value, "length_m": 223.6, "coords": [(500000.0, 4500900.0), (500200.0, 4501000.0)], "direction_status": DirectionStatus.KNOWN.value},
                {"link_id": "L3", "from_node_id": "N3", "to_node_id": "OUT1", "link_type": LinkType.OPEN_CHANNEL.value, "length_m": 200.0, "coords": [(500200.0, 4501000.0), (500400.0, 4501000.0)], "direction_status": DirectionStatus.KNOWN.value},
            ]
        elif fixture_type == "disconnected_component":
            nodes = [
                {"node_id": "N1", "node_type": NodeType.INLET.value, "x": 500000.0, "y": 4501000.0},
                {"node_id": "OUT1", "node_type": NodeType.OUTFALL.value, "x": 500100.0, "y": 4501000.0},
                {"node_id": "X1", "node_type": NodeType.MANHOLE.value, "x": 505000.0, "y": 4505000.0},
                {"node_id": "X2", "node_type": NodeType.MANHOLE.value, "x": 505100.0, "y": 4505000.0},
            ]
            links = [
                {"link_id": "L1", "from_node_id": "N1", "to_node_id": "OUT1", "link_type": LinkType.PIPE.value, "length_m": 100.0, "coords": [(500000.0, 4501000.0), (500100.0, 4501000.0)], "direction_status": DirectionStatus.KNOWN.value},
                {"link_id": "LX", "from_node_id": "X1", "to_node_id": "X2", "link_type": LinkType.PIPE.value, "length_m": 100.0, "coords": [(505000.0, 4505000.0), (505100.0, 4505000.0)], "direction_status": DirectionStatus.KNOWN.value},
            ]
        elif fixture_type == "missing_endpoint":
            nodes = [
                {"node_id": "N1", "node_type": NodeType.INLET.value, "x": 500000.0, "y": 4501000.0},
            ]
            links = [
                {"link_id": "L_ORPHAN", "from_node_id": "N1", "to_node_id": "MISSING_N2", "link_type": LinkType.PIPE.value, "length_m": 100.0, "coords": [(500000.0, 4501000.0), (500100.0, 4501000.0)], "direction_status": DirectionStatus.KNOWN.value},
            ]
        elif fixture_type == "loop_topology":
            nodes = [
                {"node_id": "N1", "node_type": NodeType.MANHOLE.value, "x": 500000.0, "y": 4501000.0},
                {"node_id": "N2", "node_type": NodeType.MANHOLE.value, "x": 500100.0, "y": 4501000.0},
            ]
            links = [
                {"link_id": "L1", "from_node_id": "N1", "to_node_id": "N2", "link_type": LinkType.PIPE.value, "length_m": 100.0, "coords": [(500000.0, 4501000.0), (500100.0, 4501000.0)], "direction_status": DirectionStatus.KNOWN.value},
                {"link_id": "L2_LOOP", "from_node_id": "N2", "to_node_id": "N1", "link_type": LinkType.PIPE.value, "length_m": 100.0, "coords": [(500100.0, 4501000.0), (500000.0, 4501000.0)], "direction_status": DirectionStatus.KNOWN.value},
            ]
        elif fixture_type == "unknown_direction":
            nodes = [
                {"node_id": "N1", "node_type": NodeType.MANHOLE.value, "x": 500000.0, "y": 4501000.0},
                {"node_id": "N2", "node_type": NodeType.MANHOLE.value, "x": 500100.0, "y": 4501000.0},
            ]
            links = [
                {"link_id": "L1", "from_node_id": "N1", "to_node_id": "N2", "link_type": LinkType.PIPE.value, "length_m": 100.0, "coords": [(500000.0, 4501000.0), (500100.0, 4501000.0)], "direction_status": DirectionStatus.UNKNOWN.value},
            ]
        else:
            raise ValueError(f"Unknown synthetic drainage fixture type '{fixture_type}'")

        metadata = {
            "dataset_id": f"synthetic_{fixture_type}",
            "source": self.provider_label,
            "crs": crs,
            "is_test_fixture": True,
            "confidence": "SYNTHETIC",
            "provenance": {
                "fixture_type": fixture_type,
                "label": "TEST FIXTURE ONLY",
            }
        }

        return nodes, links, metadata


class LocalDrainageProvider(BaseDrainageProvider):
    """
    Local File-backed Drainage Network Provider for vector datasets (GeoPackage / GeoJSON / Shapefile).
    """

    def __init__(self, drainage_base_path: str = "data/raw/drainage"):
        self.drainage_base_path = drainage_base_path

    async def get_metadata(self, dataset_id: str) -> SpatialMetadata:
        """Extract metadata from local vector dataset file."""
        file_path = os.path.join(self.drainage_base_path, dataset_id)
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Local drainage dataset '{dataset_id}' not found at {file_path}")

        return SpatialMetadata(
            source=f"LocalDrainageFile:{os.path.basename(file_path)}",
            acquisition_time=datetime.now(timezone.utc),
            ingestion_time=datetime.now(timezone.utc),
            crs="EPSG:4326",
            resolution=(1.0, 1.0),
            bounding_box=BoundingBox(minx=0.0, miny=0.0, maxx=0.0, maxy=0.0),
            units="meters",
            version="1.0-local",
            provenance={"file_path": file_path}
        )

    async def check_coverage(self, bbox: BoundingBox, crs: str = "EPSG:4326") -> bool:
        """Check if local drainage directory exists and contains vector datasets."""
        if not os.path.exists(self.drainage_base_path):
            return False
        files = [f for f in os.listdir(self.drainage_base_path) if f.endswith((".gpkg", ".geojson", ".shp", ".json"))]
        return len(files) > 0
