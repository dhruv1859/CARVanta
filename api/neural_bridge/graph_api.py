"""
CARVanta Neural Bridge — REST API
====================================
Serves the antigen–disease–pathway knowledge graph with:
  - Full graph data (nodes + edges) for force-directed visualisation
  - Community detection (Louvain, Label Propagation)
  - Full-text search with BM25 ranking and fuzzy matching
  - Node neighbourhood expansion
  - Graph statistics and analytics
  - Export in JSON, CSV, GraphML, Cytoscape formats
  - Subgraph extraction around seed nodes
  - Bridging-node identification
"""

from __future__ import annotations

from typing import Any, Dict, List, Optional
from fastapi import APIRouter, HTTPException, Query
from pydantic import BaseModel, Field

from api.neural_bridge.graph_builder import graph_builder
from api.neural_bridge.cluster_engine import cluster_engine, ClusterResult
from api.neural_bridge.search_engine import search_engine
from api.neural_bridge import export as graph_export
from api.neural_bridge import graph_analytics
from api.neural_bridge import path_finder
from api.neural_bridge import similarity_engine
from api.neural_bridge import visualization as viz_engine
from api.neural_bridge import diffusion_engine
from api.neural_bridge import motif_detection
from api.neural_bridge.graph_temporal import temporal_store
from api.neural_bridge import embedding_engine
from api.neural_bridge import graph_comparison

router = APIRouter(
    prefix="/api/v5/bridge",
    tags=["Neural Network Bridge"],
)

# ─── Lazy initialisation helper ──────────────────────────────────────────────

_graph_data: Dict[str, Any] = {}


def _ensure_graph() -> Dict[str, Any]:
    """Build (or return cached) graph and ensure search index is ready."""
    global _graph_data
    if not _graph_data or not _graph_data.get("nodes"):
        _graph_data = graph_builder.build_graph()
        if _graph_data.get("nodes"):
            search_engine.build_index(_graph_data["nodes"])
    return _graph_data


# ═══════════════════════════════════════════════════════════════════════════════
# Graph Data Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/graph", summary="Get full knowledge graph")
async def get_knowledge_graph(
    max_nodes: Optional[int] = Query(None, ge=10, le=5000, description="Limit node count"),
    group: Optional[str] = Query(None, description="Filter by group: Antigen, Disease, Pathway"),
    layer: Optional[str] = Query(None, description="Filter by layer: clinical, biological, omics"),
    min_score: Optional[float] = Query(None, ge=0, le=1, description="Minimum node score"),
):
    """
    Returns the knowledge graph for the interactive force-directed visualisation.
    Supports filtering by group, layer, score, and node limit.
    """
    data = _ensure_graph()
    nodes = data.get("nodes", [])
    links = data.get("links", [])

    if not nodes:
        raise HTTPException(status_code=404, detail="Graph data not available or empty.")

    # Apply filters
    if group or layer or min_score is not None or max_nodes:
        nodes, links = graph_export.filter_graph(
            nodes, links,
            group=group, layer=layer,
            min_score=min_score, max_nodes=max_nodes,
        )

    return {
        "status": "success",
        "metadata": {
            "nodes_count": len(nodes),
            "edges_count": len(links),
            "layers": ["clinical", "biological", "omics"],
            "groups": list({n.get("group", "") for n in nodes}),
        },
        "data": {"nodes": nodes, "links": links},
    }


@router.get("/graph/stats", summary="Graph statistics")
async def graph_statistics():
    """Comprehensive network statistics: degree distribution, density, breakdowns."""
    data = _ensure_graph()
    nodes = data.get("nodes", [])
    links = data.get("links", [])

    if not nodes:
        raise HTTPException(status_code=404, detail="No graph data available.")

    stats = graph_export.compute_graph_statistics(nodes, links)
    return {"status": "success", "statistics": stats}


@router.get("/node/{node_id}", summary="Get node details and neighbours")
async def get_node(
    node_id: str,
    depth: int = Query(1, ge=1, le=3, description="Neighbourhood depth"),
):
    """Return a node's metadata and its neighbours up to `depth` hops."""
    data = _ensure_graph()
    nodes = data.get("nodes", [])
    links = data.get("links", [])

    # Find the node
    node_info = None
    for n in nodes:
        if n.get("id") == node_id:
            node_info = n
            break

    if not node_info:
        raise HTTPException(status_code=404, detail=f"Node '{node_id}' not found.")

    # Build adjacency for neighbour lookup
    from collections import defaultdict
    adj: Dict[str, set] = defaultdict(set)
    for lnk in links:
        adj[lnk.get("source", "")].add(lnk.get("target", ""))
        adj[lnk.get("target", "")].add(lnk.get("source", ""))

    neighbours = search_engine.get_neighbours(node_id, adj, depth=depth)

    return {
        "node": node_info,
        "neighbours": neighbours,
        "neighbour_count": len(neighbours),
        "depth": depth,
    }


@router.get("/subgraph/{seed_node_id}", summary="Extract subgraph")
async def extract_subgraph(
    seed_node_id: str,
    depth: int = Query(2, ge=1, le=4, description="BFS depth from seed"),
):
    """Extract a subgraph centred on a seed node."""
    data = _ensure_graph()
    result = graph_export.extract_subgraph(
        data.get("nodes", []),
        data.get("links", []),
        seed_node_id,
        depth=depth,
    )
    if not result["nodes"]:
        raise HTTPException(status_code=404, detail=f"Seed node '{seed_node_id}' not found.")
    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Search Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/search", summary="Search the knowledge graph")
async def search_graph(
    query: str = Query(..., min_length=1, description="Search query"),
    group: Optional[str] = Query(None, description="Filter: Antigen, Disease, Pathway"),
    layer: Optional[str] = Query(None, description="Filter: clinical, biological, omics"),
    min_score: Optional[float] = Query(None, ge=0, le=1),
    limit: int = Query(20, ge=1, le=100),
    fuzzy: bool = Query(True, description="Enable fuzzy matching"),
):
    """
    Full-text search with BM25 ranking, fuzzy matching, and faceted filtering.
    """
    _ensure_graph()
    result = search_engine.search(
        query,
        group_filter=group,
        layer_filter=layer,
        min_score=min_score,
        limit=limit,
        fuzzy=fuzzy,
    )
    return result.to_dict()


@router.get("/suggest", summary="Auto-complete suggestions")
async def suggest(
    prefix: str = Query(..., min_length=1, description="Prefix to complete"),
    limit: int = Query(10, ge=1, le=30),
):
    """Auto-complete node names for the search bar."""
    _ensure_graph()
    suggestions = search_engine.suggest(prefix, limit=limit)
    return {"prefix": prefix, "suggestions": suggestions}


@router.get("/search/analytics", summary="Search usage analytics")
async def search_analytics():
    """Return search usage metrics: top terms, zero-result queries, etc."""
    return search_engine.search_analytics()


# ═══════════════════════════════════════════════════════════════════════════════
# Cluster / Community Detection Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/clusters", summary="Detect communities in the graph")
async def detect_clusters(
    method: str = Query("louvain", description="Algorithm: louvain or label_propagation"),
    resolution: float = Query(1.0, ge=0.1, le=5.0, description="Louvain resolution"),
):
    """
    Run community detection and return cluster assignments,
    quality metrics, and per-cluster summaries.
    """
    data = _ensure_graph()
    nodes = data.get("nodes", [])
    links = data.get("links", [])

    if not nodes:
        raise HTTPException(status_code=404, detail="No graph data.")

    result = cluster_engine.detect_communities(
        nodes, links, method=method, resolution=resolution,
    )
    return result.to_dict()


@router.get("/clusters/stats", summary="Cluster statistics")
async def cluster_stats():
    """Global statistics about the current clustering."""
    stats = cluster_engine.cluster_statistics()
    if "error" in stats:
        raise HTTPException(status_code=404, detail="Run /clusters first.")
    return stats


@router.get("/clusters/{cluster_id}", summary="Get cluster details")
async def get_cluster(cluster_id: int):
    """Detailed information about a specific cluster."""
    info = cluster_engine.get_cluster_members(cluster_id)
    if not info:
        raise HTTPException(status_code=404, detail=f"Cluster {cluster_id} not found.")
    return info


@router.get("/clusters/bridging-nodes", summary="Find bridging nodes")
async def bridging_nodes(
    top_n: int = Query(20, ge=1, le=100),
):
    """
    Identify nodes that connect multiple clusters — biologically
    interesting boundary-spanning genes.
    """
    data = _ensure_graph()
    nodes = data.get("nodes", [])
    links = data.get("links", [])

    # Ensure clusters exist
    if not cluster_engine._cache:
        cluster_engine.detect_communities(nodes, links)

    from collections import defaultdict
    adj: Dict[str, set] = defaultdict(set)
    for lnk in links:
        adj[lnk.get("source", "")].add(lnk.get("target", ""))
        adj[lnk.get("target", "")].add(lnk.get("source", ""))

    bridges = cluster_engine.find_bridging_nodes(
        adj, cluster_engine._cache.node_to_cluster, top_n=top_n,
    )
    return {"bridging_nodes": bridges, "total": len(bridges)}


@router.get("/clusters/hierarchy", summary="Cluster hierarchy")
async def cluster_hierarchy():
    """
    Hierarchical summary (layer → group → cluster → hubs) for
    tree-map or sunburst visualisation.
    """
    data = _ensure_graph()
    return cluster_engine.hierarchical_summary(
        data.get("nodes", []), data.get("links", []),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Export Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/export/json", summary="Export graph as JSON")
async def export_json():
    """Full graph export in JSON format with metadata."""
    data = _ensure_graph()
    clusters = cluster_engine._cache.node_to_cluster if cluster_engine._cache else None
    return graph_export.export_json(
        data.get("nodes", []), data.get("links", []), clusters=clusters,
    )


@router.get("/export/csv", summary="Export graph as CSV")
async def export_csv_endpoint():
    """Export graph as two CSVs: nodes and edges."""
    data = _ensure_graph()
    clusters = cluster_engine._cache.node_to_cluster if cluster_engine._cache else None
    return graph_export.export_csv(
        data.get("nodes", []), data.get("links", []), clusters=clusters,
    )


@router.get("/export/graphml", summary="Export graph as GraphML")
async def export_graphml():
    """Export in GraphML format (compatible with Gephi, Cytoscape Desktop)."""
    from fastapi.responses import Response
    data = _ensure_graph()
    xml_str = graph_export.export_graphml(
        data.get("nodes", []), data.get("links", []),
    )
    return Response(
        content=xml_str,
        media_type="application/xml",
        headers={"Content-Disposition": "attachment; filename=CARVanta_KnowledgeGraph.graphml"},
    )


@router.get("/export/cytoscape", summary="Export as Cytoscape JSON")
async def export_cytoscape():
    """Export in Cytoscape.js JSON format."""
    data = _ensure_graph()
    clusters = cluster_engine._cache.node_to_cluster if cluster_engine._cache else None
    return graph_export.export_cytoscape(
        data.get("nodes", []), data.get("links", []), clusters=clusters,
    )


@router.get("/export/report", summary="Export summary report")
async def export_report():
    """Human-readable Markdown summary report."""
    data = _ensure_graph()
    stats = graph_export.compute_graph_statistics(
        data.get("nodes", []), data.get("links", []),
    )
    report = graph_export.export_summary_report(
        data.get("nodes", []), data.get("links", []), stats=stats,
    )
    return {"report": report, "statistics": stats}


# ═══════════════════════════════════════════════════════════════════════════════
# Path-Finding Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/path/{source}/{target}", summary="Shortest path between two nodes")
async def shortest_path(
    source: str,
    target: str,
    algorithm: str = Query("bfs", description="bfs or dijkstra"),
):
    """Find the shortest path between two nodes."""
    data = _ensure_graph()
    links = data.get("links", [])

    if algorithm == "dijkstra":
        result = path_finder.dijkstra_shortest_path(links, source, target)
    else:
        result = path_finder.bfs_shortest_path(links, source, target)

    if not result.get("found"):
        raise HTTPException(status_code=404, detail=result.get("message", "No path found."))
    return result


@router.get("/path/{source}/{target}/all", summary="All shortest paths")
async def all_paths(
    source: str,
    target: str,
    max_paths: int = Query(10, ge=1, le=50),
):
    """Find all shortest paths between two nodes."""
    data = _ensure_graph()
    result = path_finder.all_shortest_paths(
        data.get("links", []), source, target, max_paths=max_paths,
    )
    return result


@router.get("/path/{source}/{target}/k-shortest", summary="K shortest paths")
async def k_paths(
    source: str,
    target: str,
    k: int = Query(5, ge=1, le=20),
):
    """Yen's K-shortest loopless paths — reveals alternative biological routing."""
    data = _ensure_graph()
    result = path_finder.k_shortest_paths(
        data.get("links", []), source, target, k=k,
    )
    return result


@router.get("/topology", summary="Graph topology metrics")
async def topology():
    """Eccentricity, radius, diameter, centre and periphery nodes."""
    data = _ensure_graph()
    return path_finder.eccentricity(
        data.get("nodes", []), data.get("links", []),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Network Analytics Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/analytics/full", summary="Full network analytics report")
async def full_analytics_report(
    include_centralities: bool = Query(True),
):
    """
    Comprehensive analytics: centralities, clustering coefficient,
    components, assortativity, small-world-ness, triads, rich-club.
    """
    data = _ensure_graph()
    return graph_analytics.full_analytics(
        data.get("nodes", []), data.get("links", []),
        include_centralities=include_centralities,
    )


@router.get("/analytics/centrality/{metric}", summary="Centrality metric")
async def centrality_metric(
    metric: str,
    top_n: int = Query(20, ge=1, le=100),
):
    """
    Individual centrality metric.
    Supported: degree, betweenness, closeness, pagerank, eigenvector.
    """
    data = _ensure_graph()
    nodes = data.get("nodes", [])
    links = data.get("links", [])

    funcs = {
        "degree": graph_analytics.degree_centrality,
        "betweenness": graph_analytics.betweenness_centrality,
        "closeness": graph_analytics.closeness_centrality,
        "pagerank": graph_analytics.pagerank,
        "eigenvector": graph_analytics.eigenvector_centrality,
    }
    fn = funcs.get(metric)
    if not fn:
        raise HTTPException(status_code=400, detail=f"Unknown metric '{metric}'. Options: {list(funcs.keys())}")

    scores = fn(nodes, links)
    ranked = sorted(scores.items(), key=lambda x: x[1], reverse=True)[:top_n]
    return {
        "metric": metric,
        "top_nodes": [{"node": n, "score": round(s, 6)} for n, s in ranked],
    }


@router.get("/analytics/hits", summary="HITS hub & authority scores")
async def hits_scores(top_n: int = Query(15, ge=1, le=50)):
    """Hub and Authority scores (HITS algorithm)."""
    data = _ensure_graph()
    result = graph_analytics.hits(data.get("nodes", []), data.get("links", []))
    top_hubs = sorted(result["hubs"].items(), key=lambda x: x[1], reverse=True)[:top_n]
    top_auth = sorted(result["authorities"].items(), key=lambda x: x[1], reverse=True)[:top_n]
    return {
        "top_hubs": [{"node": n, "score": round(s, 6)} for n, s in top_hubs],
        "top_authorities": [{"node": n, "score": round(s, 6)} for n, s in top_auth],
    }


@router.get("/analytics/clustering", summary="Clustering coefficients")
async def clustering_coefficients():
    """Local and global clustering coefficients + transitivity."""
    data = _ensure_graph()
    result = graph_analytics.clustering_coefficients(
        data.get("nodes", []), data.get("links", []),
    )
    # Return top-20 highest local CC instead of all
    top_local = sorted(result["local"].items(), key=lambda x: x[1], reverse=True)[:20]
    return {
        "global_average": result["global_average"],
        "transitivity": result["transitivity"],
        "top_clustered_nodes": [{"node": n, "cc": c} for n, c in top_local],
    }


@router.get("/analytics/components", summary="Connected components")
async def components():
    """Connected component analysis."""
    data = _ensure_graph()
    return graph_analytics.connected_components(
        data.get("nodes", []), data.get("links", []),
    )


@router.get("/analytics/small-world", summary="Small-world analysis")
async def small_world():
    """Small-world-ness estimation (σ coefficient)."""
    data = _ensure_graph()
    return graph_analytics.small_world_sigma(
        data.get("nodes", []), data.get("links", []),
    )


@router.get("/analytics/rich-club", summary="Rich-club coefficient")
async def rich_club():
    """Rich-club coefficient φ(k) — hub interconnectedness."""
    data = _ensure_graph()
    result = graph_analytics.rich_club_coefficient(
        data.get("nodes", []), data.get("links", []),
    )
    return {"rich_club": result}


@router.get("/analytics/triads", summary="Triad census")
async def triads():
    """Open vs closed triad counts and closure rate."""
    data = _ensure_graph()
    return graph_analytics.triad_census(
        data.get("nodes", []), data.get("links", []),
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Link Prediction Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/predict-links", summary="Predict missing links")
async def predict_links(
    top_n: int = Query(30, ge=1, le=100),
    group: Optional[str] = Query(None, description="Filter by group"),
):
    """
    Ensemble link prediction using 5 heuristics.
    High scores suggest undiscovered antigen-disease or antigen-pathway associations.
    """
    data = _ensure_graph()
    return path_finder.predict_links(
        data.get("nodes", []), data.get("links", []),
        top_n=top_n, group_filter=group,
    )


@router.get("/summary", summary="Graph builder summary")
async def graph_summary():
    """Quick summary: node/edge counts, groups, layers, edge types."""
    return graph_builder.get_summary()


# ═══════════════════════════════════════════════════════════════════════════════
# Similarity & Recommendation Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/similar/{node_id}", summary="Find similar nodes")
async def similar_nodes(
    node_id: str,
    top_n: int = Query(15, ge=1, le=50),
):
    """Ensemble recommendation of nodes similar to the given node."""
    data = _ensure_graph()
    return similarity_engine.recommend_similar(
        data.get("nodes", []), data.get("links", []),
        target_id=node_id, top_n=top_n,
    )


@router.get("/similar/{node_id}/by-attribute", summary="Attribute-similar nodes")
async def attribute_similar(
    node_id: str,
    top_n: int = Query(20, ge=1, le=50),
):
    """Find nodes with similar attributes (score, group, druggability)."""
    data = _ensure_graph()
    return similarity_engine.attribute_similarity_batch(
        data.get("nodes", []), target_id=node_id, top_n=top_n,
    )


@router.get("/similar/{node_id}/by-role", summary="Role-similar nodes")
async def role_similar(
    node_id: str,
    top_n: int = Query(20, ge=1, le=50),
):
    """Find nodes in analogous structural positions."""
    data = _ensure_graph()
    return similarity_engine.role_similarity(
        data.get("nodes", []), data.get("links", []),
        target_id=node_id, top_n=top_n,
    )


@router.get("/indication-expansion/{antigen_id}", summary="Indication expansion")
async def indication_expansion(
    antigen_id: str,
    top_n: int = Query(10, ge=1, le=30),
):
    """Suggest diseases an antigen could be repurposed for."""
    data = _ensure_graph()
    return similarity_engine.suggest_indication_expansion(
        data.get("nodes", []), data.get("links", []),
        antigen_id=antigen_id, top_n=top_n,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Layout & Visualization Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/layout/{algorithm}", summary="Compute graph layout")
async def compute_layout(
    algorithm: str,
    width: float = Query(1000, ge=100, le=5000),
    height: float = Query(1000, ge=100, le=5000),
    group_by: Optional[str] = Query(None),
):
    """
    Compute node positions using a layout algorithm.
    Algorithms: force, circular, concentric, hierarchical, grid.
    """
    data = _ensure_graph()
    nodes = data.get("nodes", [])
    links = data.get("links", [])

    layouts = {
        "force": lambda: viz_engine.force_directed_layout(nodes, links, width, height),
        "circular": lambda: viz_engine.circular_layout(nodes, group_by=group_by),
        "concentric": lambda: viz_engine.concentric_layout(nodes, links),
        "hierarchical": lambda: viz_engine.hierarchical_layout(nodes, width, height),
        "grid": lambda: viz_engine.grid_layout(nodes, group_by=group_by or "group"),
    }

    fn = layouts.get(algorithm)
    if not fn:
        raise HTTPException(status_code=400, detail=f"Unknown layout '{algorithm}'. Options: {list(layouts.keys())}")

    positions = fn()
    return {
        "algorithm": algorithm,
        "positions": positions,
        "node_count": len(positions),
    }


@router.get("/styles", summary="Node visual styles")
async def node_styles(
    size_by: str = Query("degree", description="degree or score"),
    color_by: str = Query("group", description="group, layer, or score"),
):
    """Compute visual styles (color, size, shape, opacity) for all nodes."""
    data = _ensure_graph()
    styles = viz_engine.compute_node_styles(
        data.get("nodes", []), data.get("links", []),
        size_by=size_by, color_by=color_by,
    )
    return {"styles": styles, "size_by": size_by, "color_by": color_by}


@router.get("/lod-config", summary="Level-of-detail configuration")
async def lod_configuration():
    """Recommended rendering settings based on graph size."""
    data = _ensure_graph()
    n_nodes = len(data.get("nodes", []))
    return viz_engine.lod_config(n_nodes)


# ═══════════════════════════════════════════════════════════════════════════════
# Diffusion & Influence Propagation Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/diffusion/heat", summary="Heat diffusion from seed nodes")
async def heat_diffusion_endpoint(
    seeds: str = Query(..., description="Comma-separated seed node IDs"),
    steps: int = Query(10, ge=1, le=50),
    rate: float = Query(0.3, ge=0.01, le=1.0),
):
    """Simulate heat diffusion through the graph from seed nodes."""
    data = _ensure_graph()
    seed_list = [s.strip() for s in seeds.split(",") if s.strip()]
    return diffusion_engine.heat_diffusion(
        data.get("nodes", []), data.get("links", []),
        seed_nodes=seed_list, time_steps=steps, diffusion_rate=rate,
    )


@router.get("/diffusion/rwr/{seed_node}", summary="Random walk with restart")
async def rwr_endpoint(
    seed_node: str,
    restart_prob: float = Query(0.15, ge=0.01, le=0.5),
):
    """Personalised PageRank from a seed node."""
    data = _ensure_graph()
    return diffusion_engine.random_walk_restart(
        data.get("nodes", []), data.get("links", []),
        seed_node=seed_node, restart_prob=restart_prob,
    )


@router.get("/diffusion/sir", summary="SIR epidemic simulation")
async def sir_endpoint(
    infected: str = Query(..., description="Comma-separated initially infected IDs"),
    infection_rate: float = Query(0.3, ge=0.01, le=1.0),
    recovery_rate: float = Query(0.1, ge=0.01, le=1.0),
):
    """SIR model for mutation/resistance propagation simulation."""
    data = _ensure_graph()
    inf_list = [s.strip() for s in infected.split(",") if s.strip()]
    return diffusion_engine.sir_simulation(
        data.get("nodes", []), data.get("links", []),
        initial_infected=inf_list,
        infection_rate=infection_rate,
        recovery_rate=recovery_rate,
    )


@router.get("/diffusion/influence-max", summary="Top-k influence maximization")
async def influence_max_endpoint(
    k: int = Query(5, ge=1, le=15),
):
    """Find the k most influential seed nodes."""
    data = _ensure_graph()
    return diffusion_engine.influence_maximization(
        data.get("nodes", []), data.get("links", []), k=k,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Motif Detection Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/motifs/census", summary="Full motif census")
async def motif_census_endpoint():
    """Run a complete motif census across all pattern types."""
    data = _ensure_graph()
    return motif_detection.motif_census(
        data.get("nodes", []), data.get("links", []),
    )


@router.get("/motifs/triangles", summary="Find triangles")
async def triangles_endpoint():
    """Find tightly coupled 3-node functional modules."""
    data = _ensure_graph()
    return motif_detection.find_triangles(
        data.get("nodes", []), data.get("links", []),
    )


@router.get("/motifs/cliques", summary="Find cliques")
async def cliques_endpoint(
    min_size: int = Query(3, ge=3, le=8),
    max_size: int = Query(6, ge=3, le=10),
):
    """Find fully connected subgraphs (cliques)."""
    data = _ensure_graph()
    return motif_detection.find_cliques(
        data.get("nodes", []), data.get("links", []),
        min_size=min_size, max_size=max_size,
    )


@router.get("/motifs/hubs", summary="Hub-spoke patterns")
async def hubs_endpoint(
    min_degree: int = Query(10, ge=3),
):
    """Find hub-spoke star topologies."""
    data = _ensure_graph()
    return motif_detection.find_hub_spokes(
        data.get("nodes", []), data.get("links", []),
        min_degree=min_degree,
    )


@router.get("/motifs/diamonds", summary="Diamond motifs")
async def diamonds_endpoint():
    """Find redundant pathway diamonds (drug resistance indicators)."""
    data = _ensure_graph()
    return motif_detection.find_diamonds(
        data.get("nodes", []), data.get("links", []),
    )


@router.get("/motifs/chains", summary="Chain motifs")
async def chains_endpoint(
    min_length: int = Query(4, ge=3, le=10),
):
    """Find linear signal cascade chains."""
    data = _ensure_graph()
    return motif_detection.find_chains(
        data.get("nodes", []), data.get("links", []),
        min_length=min_length,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Temporal / Versioning Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.post("/snapshot", summary="Create graph snapshot")
async def create_snapshot(
    label: str = Query("", description="Optional snapshot label"),
):
    """Snapshot the current graph state for temporal analysis."""
    data = _ensure_graph()
    return temporal_store.create_snapshot(
        data.get("nodes", []), data.get("links", []), label=label,
    )


@router.get("/snapshots", summary="List all snapshots")
async def list_snapshots():
    """List all stored graph snapshots."""
    return {"snapshots": temporal_store.list_snapshots()}


@router.get("/snapshots/diff", summary="Diff two snapshots")
async def snapshot_diff(
    index_a: int = Query(-2),
    index_b: int = Query(-1),
):
    """Compute structural diff between two snapshots."""
    return temporal_store.diff(index_a, index_b)


@router.get("/snapshots/growth", summary="Growth timeline")
async def growth_timeline():
    """Node/edge count evolution across snapshots."""
    return temporal_store.growth_timeline()


@router.get("/snapshots/stability", summary="Stability analysis")
async def stability_analysis():
    """Graph stability metrics across snapshots."""
    return temporal_store.stability_analysis()


@router.get("/snapshots/events", summary="Event timeline")
async def event_timeline():
    """Significant structural change events."""
    return temporal_store.event_timeline()


@router.get("/snapshots/group-evolution", summary="Group evolution")
async def group_evolution():
    """Track group distribution changes over time."""
    return temporal_store.group_evolution()


# ═══════════════════════════════════════════════════════════════════════════════
# Node Embedding Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/embeddings", summary="Compute node embeddings")
async def compute_embeddings_endpoint(
    method: str = Query("deepwalk", description="deepwalk|node2vec|structural|hybrid"),
    dim: int = Query(32, ge=4, le=128),
):
    """Compute vector embeddings for all graph nodes."""
    data = _ensure_graph()
    return embedding_engine.compute_embeddings(
        data.get("nodes", []), data.get("links", []),
        method=method, dim=dim,
    )


@router.get("/embeddings/similar/{node_id}", summary="Embedding similarity")
async def embedding_similar_endpoint(
    node_id: str,
    method: str = Query("deepwalk"),
    top_n: int = Query(15, ge=1, le=50),
):
    """Find most similar nodes in embedding space."""
    data = _ensure_graph()
    return embedding_engine.embedding_similarity(
        data.get("nodes", []), data.get("links", []),
        node_id=node_id, method=method, top_n=top_n,
    )


@router.get("/embeddings/clusters", summary="Embedding clusters")
async def embedding_clusters_endpoint(
    n_clusters: int = Query(5, ge=2, le=20),
    method: str = Query("deepwalk"),
):
    """Cluster nodes in embedding space via k-means."""
    data = _ensure_graph()
    return embedding_engine.embedding_clusters(
        data.get("nodes", []), data.get("links", []),
        n_clusters=n_clusters, method=method,
    )


# ═══════════════════════════════════════════════════════════════════════════════
# Graph Comparison Endpoints
# ═══════════════════════════════════════════════════════════════════════════════

@router.get("/compare-groups", summary="Compare two node groups")
async def compare_groups_endpoint(
    group_a: str = Query(..., description="First group (e.g., Disease)"),
    group_b: str = Query(..., description="Second group (e.g., Antigen)"),
):
    """Compare structural properties of two node-group subgraphs."""
    data = _ensure_graph()
    return graph_comparison.compare_subgraphs(
        data.get("nodes", []), data.get("links", []),
        group_a=group_a, group_b=group_b,
    )


@router.get("/compare-centrality", summary="Cross-group centrality")
async def compare_centrality_endpoint(
    group_a: str = Query(...),
    group_b: str = Query(...),
    top_n: int = Query(10, ge=1, le=30),
):
    """Compare centrality rankings between groups and find bridges."""
    data = _ensure_graph()
    return graph_comparison.centrality_comparison(
        data.get("nodes", []), data.get("links", []),
        group_a=group_a, group_b=group_b, top_n=top_n,
    )


@router.get("/group-interaction-matrix", summary="Group interaction matrix")
async def group_interaction_matrix_endpoint():
    """Compute interaction density between all node groups."""
    data = _ensure_graph()
    return graph_comparison.group_interaction_matrix(
        data.get("nodes", []), data.get("links", []),
    )
