"""
Pure Geospatial Drainage Network Engine.

Provides deterministic data structures, geometry validation, spatial snapping,
topology validation, directed graph construction, upstream/downstream graph traversals,
outfall reachability checks, connected component discovery, and Phase 4 catchment association.

PHYSICS/GIS FIRST PRINCIPLE:
- Phase 5 represents and analyzes drainage infrastructure topology & capacity metadata; it does NOT simulate hydraulic flooding.
- DEM-derived surface drainage proxies (Phase 4) are NOT municipal drainage pipe networks.
- Municipal drainage infrastructure MUST NEVER be fabricated. Missing attributes or capacities remain UNKNOWN.
- No flood simulation, no SCS-CN runoff, no ML, no routing.
"""

from collections import deque
from enum import Enum
from typing import Any

import numpy as np
import structlog
from app.geospatial.validation import ensure_valid_polygon
from pyproj import Transformer
from shapely.geometry import LineString, Point, Polygon, shape
from shapely.ops import transform as shapely_transform

logger = structlog.get_logger("aquora.geospatial.drainage")


class NodeType(str, Enum):
    INLET = "INLET"
    CATCH_BASIN = "CATCH_BASIN"
    MANHOLE = "MANHOLE"
    JUNCTION = "JUNCTION"
    OUTFALL = "OUTFALL"
    STORAGE = "STORAGE"
    PUMP_STATION = "PUMP_STATION"
    OTHER = "OTHER"


class LinkType(str, Enum):
    PIPE = "PIPE"
    CONDUIT = "CONDUIT"
    OPEN_CHANNEL = "OPEN_CHANNEL"
    CULVERT = "CULVERT"
    DITCH = "DITCH"
    OTHER = "OTHER"


class DataConfidence(str, Enum):
    AUTHORITATIVE = "AUTHORITATIVE"
    OFFICIAL_OPEN_DATA = "OFFICIAL_OPEN_DATA"
    VERIFIED_MAPPED = "VERIFIED_MAPPED"
    DERIVED = "DERIVED"
    SYNTHETIC = "SYNTHETIC"
    UNKNOWN = "UNKNOWN"


class QualityFlag(str, Enum):
    VALID = "VALID"
    DUPLICATE_ID = "DUPLICATE_ID"
    MISSING_ENDPOINT = "MISSING_ENDPOINT"
    ORPHAN = "ORPHAN"
    SELF_LOOP = "SELF_LOOP"
    DISCONNECTED = "DISCONNECTED"
    DANGLING = "DANGLING"
    INVALID_GEOMETRY = "INVALID_GEOMETRY"
    UNKNOWN_DIRECTION = "UNKNOWN_DIRECTION"
    UNKNOWN_CAPACITY = "UNKNOWN_CAPACITY"
    LOW_CONFIDENCE = "LOW_CONFIDENCE"


class ConnectivityStatus(str, Enum):
    CONNECTED = "CONNECTED"
    ORPHAN = "ORPHAN"
    DISCONNECTED = "DISCONNECTED"
    ISOLATED_COMPONENT = "ISOLATED_COMPONENT"
    UNKNOWN = "UNKNOWN"


class DirectionStatus(str, Enum):
    KNOWN = "KNOWN"
    UNKNOWN = "UNKNOWN"


def validate_node_geometry(geom: Point | dict[str, Any], crs_str: str = "EPSG:4326") -> dict[str, Any]:
    """Validate drainage node Point geometry and return coordinates."""
    if isinstance(geom, dict):
        shapely_geom = shape(geom)
    else:
        shapely_geom = geom
        
    if not isinstance(shapely_geom, Point) or shapely_geom.is_empty:
        raise ValueError("Drainage node geometry must be a valid non-empty Point")
        
    x, y = float(shapely_geom.x), float(shapely_geom.y)
    if not (np.isfinite(x) and np.isfinite(y)):
        raise ValueError(f"Non-finite node coordinates ({x}, {y})")
        
    return {
        "valid": True,
        "x": x,
        "y": y,
        "crs": crs_str,
        "geometry": shapely_geom
    }


def validate_link_geometry(geom: LineString | dict[str, Any], crs_str: str = "EPSG:4326") -> dict[str, Any]:
    """Validate drainage link LineString geometry and calculate metric length."""
    if isinstance(geom, dict):
        shapely_geom = shape(geom)
    else:
        shapely_geom = geom
        
    if not isinstance(shapely_geom, LineString) or shapely_geom.is_empty or len(shapely_geom.coords) < 2:
        raise ValueError("Drainage link geometry must be a valid LineString with at least 2 coordinates")
        
    coords = [(float(c[0]), float(c[1])) for c in shapely_geom.coords]
    for cx, cy in coords:
        if not (np.isfinite(cx) and np.isfinite(cy)):
            raise ValueError("Non-finite link coordinate found")
            
    return {
        "valid": True,
        "coords_count": len(coords),
        "start_coord": coords[0],
        "end_coord": coords[-1],
        "crs": crs_str,
        "geometry": shapely_geom
    }


def snap_node_to_link_endpoints(
    node_xy: tuple[float, float],
    link_coords: list[tuple[float, float]],
    snap_tolerance_m: float,
    analysis_crs_str: str = "EPSG:32633",
    source_crs_str: str = "EPSG:32633"
) -> tuple[tuple[float, float], bool, float]:
    """
    Controlled spatial snapping of node coordinate to link endpoint using projected metric Analysis CRS.
    
    Returns (snapped_xy, snapped_bool, distance_m).
    Never snaps across distances exceeding snap_tolerance_m.
    """
    if snap_tolerance_m <= 0:
        return node_xy, False, 0.0
        
    # Transform to Analysis CRS for metric distance calculation
    if source_crs_str != analysis_crs_str:
        transformer = Transformer.from_crs(source_crs_str, analysis_crs_str, always_xy=True)
        nx_m, ny_m = transformer.transform(node_xy[0], node_xy[1])
        link_coords_m = [transformer.transform(cx, cy) for cx, cy in link_coords]
    else:
        nx_m, ny_m = node_xy
        link_coords_m = link_coords
        
    node_p_m = Point(nx_m, ny_m)
    best_dist = float("inf")
    best_target_orig = node_xy
    
    # Check endpoints (start & end of link)
    for idx, (lx_m, ly_m) in enumerate([link_coords_m[0], link_coords_m[-1]]):
        dist = float(node_p_m.distance(Point(lx_m, ly_m)))
        if dist < best_dist:
            best_dist = dist
            best_target_orig = link_coords[0] if idx == 0 else link_coords[-1]
            
    if best_dist <= snap_tolerance_m:
        return best_target_orig, True, float(best_dist)
    return node_xy, False, 0.0


def validate_network_topology(
    nodes: list[dict[str, Any]],
    links: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Validate node-link network topology deterministically.
    
    Detects:
    - Duplicate node IDs
    - Duplicate link IDs
    - Missing endpoint node references (ORPHAN links)
    - Self-loops (from_node == to_node)
    - Disconnected nodes
    - Dangling links
    - Unknown directions / capacities
    """
    node_map = {}
    duplicate_nodes = set()
    for n in nodes:
        nid = str(n["node_id"])
        if nid in node_map:
            duplicate_nodes.add(nid)
        node_map[nid] = n
        
    link_map = {}
    duplicate_links = set()
    for l in links:
        lid = str(l["link_id"])
        if lid in link_map:
            duplicate_links.add(lid)
        link_map[lid] = l
        
    orphan_links = []
    self_loops = []
    connected_node_ids = set()
    unknown_direction_count = 0
    unknown_capacity_count = 0
    
    for l in links:
        lid = str(l["link_id"])
        fn = str(l.get("from_node_id", ""))
        tn = str(l.get("to_node_id", ""))
        
        if fn == tn and fn != "":
            self_loops.append(lid)
            
        fn_exists = fn in node_map
        tn_exists = tn in node_map
        
        if not (fn_exists and tn_exists):
            orphan_links.append(lid)
        else:
            connected_node_ids.add(fn)
            connected_node_ids.add(tn)
            
        if l.get("direction_status") == DirectionStatus.UNKNOWN or not fn or not tn:
            unknown_direction_count += 1
            
        if l.get("capacity_m3s") is None:
            unknown_capacity_count += 1
            
    all_node_ids = set(node_map.keys())
    disconnected_nodes = list(all_node_ids - connected_node_ids)
    
    is_valid_topology = (
        len(duplicate_nodes) == 0 and
        len(duplicate_links) == 0 and
        len(orphan_links) == 0 and
        len(self_loops) == 0
    )
    
    quality_flags = []
    if len(duplicate_nodes) > 0 or len(duplicate_links) > 0:
        quality_flags.append(QualityFlag.DUPLICATE_ID.value)
    if len(orphan_links) > 0:
        quality_flags.append(QualityFlag.MISSING_ENDPOINT.value)
        quality_flags.append(QualityFlag.ORPHAN.value)
    if len(self_loops) > 0:
        quality_flags.append(QualityFlag.SELF_LOOP.value)
    if len(disconnected_nodes) > 0:
        quality_flags.append(QualityFlag.DISCONNECTED.value)
    if unknown_direction_count > 0:
        quality_flags.append(QualityFlag.UNKNOWN_DIRECTION.value)
    if unknown_capacity_count > 0:
        quality_flags.append(QualityFlag.UNKNOWN_CAPACITY.value)
    if not quality_flags:
        quality_flags.append(QualityFlag.VALID.value)
        
    return {
        "valid_topology": is_valid_topology,
        "total_nodes": len(nodes),
        "total_links": len(links),
        "duplicate_node_ids": list(duplicate_nodes),
        "duplicate_link_ids": list(duplicate_links),
        "orphan_link_ids": orphan_links,
        "self_loop_link_ids": self_loops,
        "disconnected_node_ids": disconnected_nodes,
        "unknown_direction_links_count": unknown_direction_count,
        "unknown_capacity_links_count": unknown_capacity_count,
        "quality_flags": quality_flags
    }


def build_drainage_graph(
    nodes: list[dict[str, Any]],
    links: list[dict[str, Any]]
) -> dict[str, Any]:
    """
    Build directed drainage graph representation with adjacency and reverse adjacency lookups.
    """
    node_map = {str(n["node_id"]): n for n in nodes}
    link_map = {str(l["link_id"]): l for l in links}
    
    adj: dict[str, list[str]] = {nid: [] for nid in node_map}
    rev_adj: dict[str, list[str]] = {nid: [] for nid in node_map}
    outfalls = set()
    
    for nid, n in node_map.items():
        if str(n.get("node_type", "")).upper() == NodeType.OUTFALL.value:
            outfalls.add(nid)
            
    for l in link_map.values():
        fn = str(l.get("from_node_id", ""))
        tn = str(l.get("to_node_id", ""))
        dir_status = l.get("direction_status", DirectionStatus.KNOWN)
        
        if fn in node_map and tn in node_map:
            # Directed link if direction is known
            adj[fn].append(tn)
            rev_adj[tn].append(fn)
            if dir_status == DirectionStatus.UNKNOWN:
                # Undirected fallback representation if direction unknown
                adj[tn].append(fn)
                rev_adj[fn].append(tn)
                
    return {
        "nodes": node_map,
        "links": link_map,
        "adj": adj,
        "rev_adj": rev_adj,
        "outfalls": outfalls
    }


def get_downstream_nodes(graph: dict[str, Any], start_node_id: str) -> list[str]:
    """
    Traverse directed graph downstream from start_node_id (BFS).
    Returns ordered list of downstream reachable node IDs. Handles cycles deterministically.
    """
    adj = graph["adj"]
    start_id = str(start_node_id)
    if start_id not in adj:
        return []
        
    visited = {start_id}
    queue = deque([start_id])
    downstream = []
    
    while queue:
        curr = queue.popleft()
        for neighbor in adj.get(curr, []):
            if neighbor not in visited:
                visited.add(neighbor)
                downstream.append(neighbor)
                queue.append(neighbor)
                
    return downstream


def get_upstream_nodes(graph: dict[str, Any], start_node_id: str) -> list[str]:
    """
    Traverse directed graph upstream from start_node_id (BFS using reverse adjacency).
    Returns ordered list of upstream contributing node IDs. Handles cycles deterministically.
    """
    rev_adj = graph["rev_adj"]
    start_id = str(start_node_id)
    if start_id not in rev_adj:
        return []
        
    visited = {start_id}

    queue = deque([start_id])
    upstream = []
    
    while queue:
        curr = queue.popleft()
        for neighbor in rev_adj.get(curr, []):
            if neighbor not in visited:
                visited.add(neighbor)
                upstream.append(neighbor)
                queue.append(neighbor)
                
    return upstream


def can_reach_outfall(graph: dict[str, Any], start_node_id: str) -> bool:
    """
    Check whether start_node_id can reach an explicit OUTFALL node via directed links.
    """
    outfalls = graph["outfalls"]
    start_id = str(start_node_id)
    if start_id in outfalls:
        return True
        
    downstream_nodes = get_downstream_nodes(graph, start_id)
    return any(nid in outfalls for nid in downstream_nodes)


def find_connected_components(graph: dict[str, Any]) -> list[list[str]]:
    """
    Discover all connected components in the network (treating graph as undirected).
    Returns list of component node_id lists sorted deterministically.
    """
    nodes = list(graph["nodes"].keys())
    adj = graph["adj"]
    rev_adj = graph["rev_adj"]
    
    # Combined undirected adjacency map
    undirected_adj: dict[str, set[str]] = {nid: set() for nid in nodes}
    for nid in nodes:
        for neighbor in adj.get(nid, []):
            undirected_adj[nid].add(neighbor)
            undirected_adj[neighbor].add(nid)
        for neighbor in rev_adj.get(nid, []):
            undirected_adj[nid].add(neighbor)
            undirected_adj[neighbor].add(nid)
            
    visited = set()
    components = []
    
    for nid in sorted(nodes):
        if nid not in visited:
            comp = []
            queue = deque([nid])
            visited.add(nid)
            while queue:
                curr = queue.popleft()
                comp.append(curr)
                for neighbor in sorted(undirected_adj[curr]):
                    if neighbor not in visited:
                        visited.add(neighbor)
                        queue.append(neighbor)
            components.append(sorted(comp))
            
    return components


def associate_catchment_with_node(
    catchment_geom: Polygon | dict[str, Any],
    nodes: list[dict[str, Any]],
    max_tolerance_m: float = 200.0,
    analysis_crs_str: str = "EPSG:32633",
    source_crs_str: str = "EPSG:32633"
) -> dict[str, Any]:
    """
    Associate Phase 4 Catchment geometry with candidate drainage inlet/node.
    
    Spatial Rules:
    1. Containment: Node lies inside catchment polygon.
    2. Proximity: If no container, find nearest INLET / CATCH_BASIN within max_tolerance_m in projected Analysis CRS.
    3. Status: ASSOCIATED (single clear match), NO_ASSOCIATION (none within distance), AMBIGUOUS (multiple equidistant candidates).
    """
    if isinstance(catchment_geom, dict):
        poly_shape = shape(catchment_geom)
    else:
        poly_shape = catchment_geom
        
    valid_poly = ensure_valid_polygon(poly_shape)
    
    # Transform geometry and nodes to Analysis CRS for metric distance
    if source_crs_str != analysis_crs_str:
        transformer = Transformer.from_crs(source_crs_str, analysis_crs_str, always_xy=True)
        poly_m = shapely_transform(transformer.transform, valid_poly)
    else:
        transformer = None
        poly_m = valid_poly
        
    candidates_inside = []
    candidates_nearby = []
    
    for n in nodes:
        nid = str(n["node_id"])
        ntype = str(n.get("node_type", "")).upper()
        
        nx, ny = float(n["x"]), float(n["y"])
        if transformer:
            nx_m, ny_m = transformer.transform(nx, ny)
        else:
            nx_m, ny_m = nx, ny
            
        node_p_m = Point(nx_m, ny_m)
        
        if poly_m.contains(node_p_m):
            candidates_inside.append((nid, ntype, 0.0))
        else:
            dist = float(poly_m.distance(node_p_m))
            if dist <= max_tolerance_m:
                candidates_nearby.append((nid, ntype, dist))
                
    # Prioritize INLET / CATCH_BASIN types
    def is_inlet_type(t: str) -> bool:
        return t in (NodeType.INLET.value, NodeType.CATCH_BASIN.value)
        
    if candidates_inside:
        inlet_inside = [c for c in candidates_inside if is_inlet_type(c[1])]
        selected = inlet_inside[0] if inlet_inside else candidates_inside[0]
        status = "ASSOCIATED"
        if len(candidates_inside) > 1 and not inlet_inside:
            status = "AMBIGUOUS"
            
        return {
            "status": status,
            "associated_node_id": selected[0],
            "association_method": "POLYGON_CONTAINMENT",
            "distance_m": 0.0,
            "confidence": DataConfidence.VERIFIED_MAPPED.value,
            "candidates_count": len(candidates_inside)
        }
        
    if candidates_nearby:
        candidates_nearby.sort(key=lambda x: (0 if is_inlet_type(x[1]) else 1, x[2]))
        best_candidate = candidates_nearby[0]
        
        # Check for ambiguity (equidistant ties)
        near_ties = [c for c in candidates_nearby if abs(c[2] - best_candidate[2]) < 1e-3]
        status = "ASSOCIATED" if len(near_ties) == 1 else "AMBIGUOUS"
        
        return {
            "status": status,
            "associated_node_id": best_candidate[0],
            "association_method": "PROXIMITY_SNAP",
            "distance_m": float(best_candidate[2]),
            "confidence": DataConfidence.DERIVED.value,
            "candidates_count": len(candidates_nearby)
        }
        
    return {
        "status": "NO_ASSOCIATION",
        "associated_node_id": None,
        "association_method": "NONE",
        "distance_m": None,
        "confidence": DataConfidence.UNKNOWN.value,
        "candidates_count": 0
    }
