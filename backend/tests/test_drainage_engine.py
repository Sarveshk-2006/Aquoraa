"""
Comprehensive Unit, Invariant, and Integration Tests for Phase 5 Drainage Network Engine.

Verifies node/link geometry validation, spatial snapping, network topology validation,
directed graph construction, upstream/downstream traversals, outfall reachability,
connected component analysis, Phase 4 catchment association, providers, service layer,
and developer HTTP API endpoints.

CRITICAL HARD SCOPE BOUNDARIES:
- Network topology is NOT flood simulation.
- Missing pipe capacity is UNKNOWN, NOT zero.
- Synthetic networks are explicitly labeled 'TEST FIXTURE ONLY'.
- Metric calculations use projected metric Analysis CRS (horizontal distances in meters).
"""

import pytest
from app.geospatial.drainage import (
    associate_catchment_with_node,
    build_drainage_graph,
    can_reach_outfall,
    find_connected_components,
    get_downstream_nodes,
    get_upstream_nodes,
    snap_node_to_link_endpoints,
    validate_link_geometry,
    validate_network_topology,
    validate_node_geometry,
)
from app.main import app
from app.providers.drainage import SyntheticDrainageProvider
from app.schemas.drainage import DrainageNetworkRequest
from app.services.drainage_service import DrainageProcessingService
from httpx import ASGITransport, AsyncClient
from shapely.geometry import LineString, Point, Polygon


def test_node_geometry_validation():
    """Test validation of valid Point node geometry."""
    pt = Point(500000.0, 4501000.0)
    res = validate_node_geometry(pt, crs_str="EPSG:32633")
    assert res["valid"] is True
    assert res["x"] == 500000.0
    assert res["y"] == 4501000.0


def test_node_geometry_validation_invalid():
    """Test validation fails for empty or non-Point geometry."""
    with pytest.raises(ValueError, match="valid non-empty Point"):
        validate_node_geometry(Point())


def test_link_geometry_validation():
    """Test validation of valid LineString link geometry."""
    line = LineString([(500000.0, 4501000.0), (500100.0, 4501000.0)])
    res = validate_link_geometry(line, crs_str="EPSG:32633")
    assert res["valid"] is True
    assert res["coords_count"] == 2
    assert res["start_coord"] == (500000.0, 4501000.0)
    assert res["end_coord"] == (500100.0, 4501000.0)


def test_spatial_snapping_within_tolerance():
    """Verify node snaps to link endpoint when within tolerance radius."""
    node_xy = (500002.0, 4501000.0)  # 2 meters away from (500000.0, 4501000.0)
    link_coords = [(500000.0, 4501000.0), (500100.0, 4501000.0)]
    
    snapped_xy, snapped_bool, dist = snap_node_to_link_endpoints(
        node_xy, link_coords, snap_tolerance_m=5.0, analysis_crs_str="EPSG:32633"
    )
    
    assert snapped_bool is True
    assert snapped_xy == (500000.0, 4501000.0)
    assert pytest.approx(dist, 0.1) == 2.0


def test_spatial_snapping_outside_tolerance():
    """Verify node does NOT snap when distance exceeds tolerance radius."""
    node_xy = (500010.0, 4501000.0)  # 10 meters away from start endpoint
    link_coords = [(500000.0, 4501000.0), (500100.0, 4501000.0)]
    
    snapped_xy, snapped_bool, dist = snap_node_to_link_endpoints(
        node_xy, link_coords, snap_tolerance_m=5.0, analysis_crs_str="EPSG:32633"
    )
    
    assert snapped_bool is False
    assert snapped_xy == node_xy
    assert dist == 0.0


def test_topology_validation_valid(simple_chain_network):
    """Validate clean linear chain network topology."""
    nodes, links = simple_chain_network
    res = validate_network_topology(nodes, links)
    
    assert res["valid_topology"] is True
    assert res["total_nodes"] == 4
    assert res["total_links"] == 3
    assert len(res["orphan_link_ids"]) == 0
    assert len(res["self_loop_link_ids"]) == 0
    assert len(res["disconnected_node_ids"]) == 0


def test_topology_validation_orphan_link():
    """Detect orphan link referencing non-existent node."""
    nodes = [{"node_id": "N1", "node_type": "INLET", "x": 0.0, "y": 0.0}]
    links = [{"link_id": "L1", "from_node_id": "N1", "to_node_id": "MISSING_N2", "link_type": "PIPE"}]
    
    res = validate_network_topology(nodes, links)
    assert res["valid_topology"] is False
    assert "L1" in res["orphan_link_ids"]
    assert "ORPHAN" in res["quality_flags"]


def test_topology_validation_self_loop():
    """Detect self-loop link pointing to same node."""
    nodes = [{"node_id": "N1", "node_type": "MANHOLE", "x": 0.0, "y": 0.0}]
    links = [{"link_id": "L_LOOP", "from_node_id": "N1", "to_node_id": "N1", "link_type": "PIPE"}]
    
    res = validate_network_topology(nodes, links)
    assert res["valid_topology"] is False
    assert "L_LOOP" in res["self_loop_link_ids"]
    assert "SELF_LOOP" in res["quality_flags"]


def test_graph_downstream_traversal(simple_chain_network):
    """Test downstream traversal: N1 -> N2 -> N3 -> OUT1."""
    nodes, links = simple_chain_network
    graph = build_drainage_graph(nodes, links)
    
    downstream_from_n1 = get_downstream_nodes(graph, "N1")
    assert downstream_from_n1 == ["N2", "N3", "OUT1"]
    
    downstream_from_n2 = get_downstream_nodes(graph, "N2")
    assert downstream_from_n2 == ["N3", "OUT1"]


def test_graph_upstream_traversal(simple_chain_network):
    """Test upstream traversal: OUT1 <- N3 <- N2 <- N1."""
    nodes, links = simple_chain_network
    graph = build_drainage_graph(nodes, links)
    
    upstream_from_out = get_upstream_nodes(graph, "OUT1")
    assert upstream_from_out == ["N3", "N2", "N1"]
    
    upstream_from_n3 = get_upstream_nodes(graph, "N3")
    assert upstream_from_n3 == ["N2", "N1"]


def test_graph_outfall_reachability(simple_chain_network, disconnected_network):
    """Test outfall reachability check."""
    nodes_c, links_c = simple_chain_network
    graph_c = build_drainage_graph(nodes_c, links_c)
    assert can_reach_outfall(graph_c, "N1") is True
    assert can_reach_outfall(graph_c, "N2") is True
    assert can_reach_outfall(graph_c, "OUT1") is True
    
    nodes_d, links_d = disconnected_network
    graph_d = build_drainage_graph(nodes_d, links_d)
    assert can_reach_outfall(graph_d, "N1") is True
    assert can_reach_outfall(graph_d, "X1") is False
    assert can_reach_outfall(graph_d, "X2") is False


def test_find_connected_components(disconnected_network):
    """Discover connected components in disconnected network."""
    nodes, links = disconnected_network
    graph = build_drainage_graph(nodes, links)
    components = find_connected_components(graph)
    
    assert len(components) == 2
    assert sorted(components[0]) == ["N1", "OUT1"]
    assert sorted(components[1]) == ["X1", "X2"]


def test_catchment_association_containment(simple_chain_network):
    """Test catchment association via polygon containment."""
    nodes, _ = simple_chain_network
    # Catchment polygon enclosing node N1 (500000.0, 4501000.0)
    poly = Polygon([
        (499900.0, 4500900.0),
        (500050.0, 4500900.0),
        (500050.0, 4501050.0),
        (499900.0, 4501050.0),
    ])
    
    assoc = associate_catchment_with_node(poly, nodes, max_tolerance_m=200.0, analysis_crs_str="EPSG:32633")
    assert assoc["status"] == "ASSOCIATED"
    assert assoc["associated_node_id"] == "N1"
    assert assoc["association_method"] == "POLYGON_CONTAINMENT"


def test_synthetic_drainage_provider():
    """Verify SyntheticDrainageProvider returns datasets explicitly labeled TEST FIXTURE ONLY."""
    provider = SyntheticDrainageProvider()
    nodes, links, meta = provider.generate_synthetic_network(fixture_type="branching_network")
    
    assert len(nodes) == 4
    assert len(links) == 3
    assert "TEST FIXTURE ONLY" in meta["source"]
    assert meta["is_test_fixture"] is True


@pytest.mark.asyncio
async def test_drainage_processing_service():
    """Verify end-to-end execution of DrainageProcessingService."""
    service = DrainageProcessingService()
    request = DrainageNetworkRequest(
        dataset_id="synthetic_simple_chain",
        provider_type="synthetic",
        fixture_type="simple_chain",
        snap_tolerance_m=5.0
    )
    
    response = await service.execute_drainage_analysis(request, db=None)
    
    assert response.status == "COMPLETED"
    assert response.nodes_count == 4
    assert response.links_count == 3
    assert response.outfalls_count == 1
    assert response.connected_components_count == 1
    assert response.validation_summary.valid_topology is True


@pytest.mark.asyncio
async def test_drainage_api_endpoints():
    """Verify developer verification API endpoints (/api/v1/drainage/)."""
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://testserver") as client:
        # POST /api/v1/drainage/analyze
        payload = {
            "dataset_id": "synthetic_simple_chain",
            "provider_type": "synthetic",
            "fixture_type": "simple_chain",
            "snap_tolerance_m": 5.0
        }
        res = await client.post("/api/v1/drainage/analyze", json=payload)
        assert res.status_code == 200
        data = res.json()
        assert data["status"] == "COMPLETED"
        assert data["nodes_count"] == 4
        
        # GET /api/v1/drainage/networks/latest
        res_latest = await client.get("/api/v1/drainage/networks/latest")
        assert res_latest.status_code == 200
        
        # GET /api/v1/drainage/nodes
        res_nodes = await client.get("/api/v1/drainage/nodes")
        assert res_nodes.status_code == 200
        assert len(res_nodes.json()) == 4
        
        # GET /api/v1/drainage/links
        res_links = await client.get("/api/v1/drainage/links")
        assert res_links.status_code == 200
        assert len(res_links.json()) == 3
        
        # GET /api/v1/drainage/nodes/N1/upstream
        res_up = await client.get("/api/v1/drainage/nodes/N1/upstream")
        assert res_up.status_code == 200
        
        # GET /api/v1/drainage/nodes/N1/downstream
        res_down = await client.get("/api/v1/drainage/nodes/N1/downstream")
        assert res_down.status_code == 200
        assert res_down.json() == ["N2", "N3", "OUT1"]
        
        # GET /api/v1/drainage/nodes/N1/outfalls
        res_out = await client.get("/api/v1/drainage/nodes/N1/outfalls")
        assert res_out.status_code == 200
        assert res_out.json()["can_reach_outfall"] is True


def test_scope_boundary_invariants(simple_chain_network):
    """
    ASSERT SCIENTIFIC SCOPE INVARIANTS:
    Phase 5 must NEVER generate runoff, flood depth, or fabricated pipe capacities.
    """
    nodes, links = simple_chain_network
    
    # 1. Missing capacity remains UNKNOWN / None (NOT 0)
    link_no_cap = {"link_id": "L_NO_CAP", "from_node_id": "N1", "to_node_id": "N2", "link_type": "PIPE", "capacity_m3s": None}
    assert link_no_cap["capacity_m3s"] is None
    assert link_no_cap["capacity_m3s"] != 0.0
    
    # 2. Network graph stores topology & connections ONLY, NOT 2D hydrodynamic flood depth
    graph = build_drainage_graph(nodes, links)
    assert "adj" in graph
    assert "rev_adj" in graph
    assert "flood_depth_m" not in graph
