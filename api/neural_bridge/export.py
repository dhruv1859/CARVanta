"""
CARVanta Neural Bridge — Graph Export Engine
==============================================
Export knowledge-graph data and snapshots in multiple formats
for downstream analysis, publication, and integration.

Supported formats:
  - JSON  — full graph with metadata
  - CSV   — node list + edge list (two files, returned as dict)
  - GraphML — XML-based graph interchange format
  - Cytoscape JSON — for Cytoscape.js compatibility
  - Summary  — human-readable Markdown report
  - Statistics — node/edge/cluster metrics bundle

Features:
  - Filtered exports (by group, layer, score threshold)
  - Subgraph extraction (neighbourhood of a seed node)
  - Snapshot versioning with SHA-256 fingerprint
  - Export metadata (timestamp, parameters, data lineage)
"""

from __future__ import annotations

import csv
import hashlib
import io
import json
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Set, Tuple
from xml.etree.ElementTree import Element, SubElement, tostring


# ─── Snapshot Fingerprint ────────────────────────────────────────────────────

def _fingerprint(data: str) -> str:
    """SHA-256 fingerprint of export content for versioning."""
    return hashlib.sha256(data.encode("utf-8")).hexdigest()[:16]


# ─── Export Metadata ─────────────────────────────────────────────────────────

def _build_metadata(
    format_name: str,
    n_nodes: int,
    n_edges: int,
    filters: Optional[Dict[str, Any]] = None,
) -> Dict[str, Any]:
    return {
        "platform": "CARVanta",
        "module": "Neural Network Bridge",
        "format": format_name,
        "exported_at": datetime.now(timezone.utc).isoformat(),
        "node_count": n_nodes,
        "edge_count": n_edges,
        "filters_applied": filters or {},
        "version": "2.0",
    }


# ─── JSON Export ─────────────────────────────────────────────────────────────

def export_json(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    clusters: Optional[Dict[str, int]] = None,
    include_metadata: bool = True,
) -> Dict[str, Any]:
    """
    Export graph as a comprehensive JSON object.
    Optionally includes cluster assignments per node.
    """
    enriched_nodes = []
    for n in nodes:
        node = {**n}
        if clusters and n.get("id") in clusters:
            node["cluster_id"] = clusters[n["id"]]
        enriched_nodes.append(node)

    result: Dict[str, Any] = {
        "nodes": enriched_nodes,
        "links": links,
    }
    if include_metadata:
        result["metadata"] = _build_metadata("json", len(nodes), len(links))
        content = json.dumps(result, default=str)
        result["metadata"]["fingerprint"] = _fingerprint(content)

    return result


# ─── CSV Export ──────────────────────────────────────────────────────────────

def export_csv(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    clusters: Optional[Dict[str, int]] = None,
) -> Dict[str, str]:
    """
    Export graph as two CSV strings: one for nodes, one for edges.
    Returns {"nodes_csv": "...", "edges_csv": "...", "metadata": {...}}.
    """
    # Nodes CSV
    node_buf = io.StringIO()
    node_fields = ["id", "name", "group", "layer", "val", "score", "cluster_id"]
    writer = csv.DictWriter(node_buf, fieldnames=node_fields, extrasaction="ignore")
    writer.writeheader()
    for n in nodes:
        row = {**n}
        if clusters and n.get("id") in clusters:
            row["cluster_id"] = clusters[n["id"]]
        else:
            row["cluster_id"] = ""
        writer.writerow(row)

    # Edges CSV
    edge_buf = io.StringIO()
    edge_fields = ["source", "target", "relationship", "weight"]
    writer = csv.DictWriter(edge_buf, fieldnames=edge_fields, extrasaction="ignore")
    writer.writeheader()
    for lnk in links:
        writer.writerow(lnk)

    return {
        "nodes_csv": node_buf.getvalue(),
        "edges_csv": edge_buf.getvalue(),
        "metadata": _build_metadata("csv", len(nodes), len(links)),
    }


# ─── GraphML Export ──────────────────────────────────────────────────────────

def export_graphml(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
) -> str:
    """
    Export graph in GraphML (XML) format — compatible with Gephi,
    yEd, Cytoscape Desktop, and most network analysis tools.
    """
    root = Element("graphml")
    root.set("xmlns", "http://graphml.graphstruct.org/xmlns")

    # Declare attribute keys
    key_defs = [
        ("name", "string", "node"),
        ("group", "string", "node"),
        ("layer", "string", "node"),
        ("val", "int", "node"),
        ("score", "float", "node"),
        ("relationship", "string", "edge"),
        ("weight", "float", "edge"),
    ]
    for attr_name, attr_type, for_type in key_defs:
        key_el = SubElement(root, "key")
        key_el.set("id", attr_name)
        key_el.set("for", for_type)
        key_el.set("attr.name", attr_name)
        key_el.set("attr.type", attr_type)

    graph = SubElement(root, "graph")
    graph.set("id", "CARVanta_KnowledgeGraph")
    graph.set("edgedefault", "undirected")

    # Nodes
    for n in nodes:
        node_el = SubElement(graph, "node")
        node_el.set("id", n.get("id", ""))
        for attr in ["name", "group", "layer"]:
            data = SubElement(node_el, "data")
            data.set("key", attr)
            data.text = str(n.get(attr, ""))
        for attr in ["val"]:
            data = SubElement(node_el, "data")
            data.set("key", attr)
            data.text = str(n.get(attr, 5))
        for attr in ["score"]:
            data = SubElement(node_el, "data")
            data.set("key", attr)
            data.text = str(n.get(attr, 0.5))

    # Edges
    for i, lnk in enumerate(links):
        edge_el = SubElement(graph, "edge")
        edge_el.set("id", f"e{i}")
        edge_el.set("source", str(lnk.get("source", "")))
        edge_el.set("target", str(lnk.get("target", "")))
        for attr in ["relationship"]:
            data = SubElement(edge_el, "data")
            data.set("key", attr)
            data.text = str(lnk.get(attr, ""))
        for attr in ["weight"]:
            data = SubElement(edge_el, "data")
            data.set("key", attr)
            data.text = str(lnk.get(attr, 1.0))

    xml_bytes = tostring(root, encoding="unicode")
    return f'<?xml version="1.0" encoding="UTF-8"?>\n{xml_bytes}'


# ─── Cytoscape JSON Export ───────────────────────────────────────────────────

def export_cytoscape(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    clusters: Optional[Dict[str, int]] = None,
) -> Dict[str, Any]:
    """
    Export in Cytoscape.js JSON format — used by many bioinformatics
    visualisation tools and web frameworks.
    """
    elements = {"nodes": [], "edges": []}

    for n in nodes:
        data = {
            "id": n.get("id", ""),
            "label": n.get("name", ""),
            "group": n.get("group", ""),
            "layer": n.get("layer", ""),
            "score": n.get("score", 0.5),
        }
        if clusters and n.get("id") in clusters:
            data["cluster"] = clusters[n["id"]]
        elements["nodes"].append({"data": data})

    for i, lnk in enumerate(links):
        elements["edges"].append({
            "data": {
                "id": f"e{i}",
                "source": lnk.get("source", ""),
                "target": lnk.get("target", ""),
                "relationship": lnk.get("relationship", "related"),
                "weight": lnk.get("weight", 1.0),
            }
        })

    return {
        "format_version": "1.0",
        "generated_by": "CARVanta Neural Bridge",
        "target_cytoscapejs_version": "~3.0",
        "data": {"name": "CARVanta Knowledge Graph"},
        "elements": elements,
    }


# ─── Subgraph Extraction ────────────────────────────────────────────────────

def extract_subgraph(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    seed_node_id: str,
    depth: int = 2,
) -> Dict[str, Any]:
    """
    Extract a subgraph centred on a seed node up to ``depth`` hops.
    Returns filtered node and link lists suitable for any export format.
    """
    # Build adjacency
    adj: Dict[str, set] = defaultdict(set)
    for lnk in links:
        src, tgt = lnk.get("source", ""), lnk.get("target", "")
        adj[src].add(tgt)
        adj[tgt].add(src)

    # BFS
    visited: Set[str] = {seed_node_id}
    frontier: Set[str] = {seed_node_id}
    for _ in range(depth):
        next_frontier: Set[str] = set()
        for nid in frontier:
            for nb in adj.get(nid, set()):
                if nb not in visited:
                    visited.add(nb)
                    next_frontier.add(nb)
        frontier = next_frontier

    sub_nodes = [n for n in nodes if n.get("id") in visited]
    sub_links = [
        lnk for lnk in links
        if lnk.get("source") in visited and lnk.get("target") in visited
    ]

    return {
        "seed": seed_node_id,
        "depth": depth,
        "nodes": sub_nodes,
        "links": sub_links,
        "metadata": _build_metadata(
            "subgraph",
            len(sub_nodes),
            len(sub_links),
            filters={"seed": seed_node_id, "depth": depth},
        ),
    }


# ─── Filtered Export ─────────────────────────────────────────────────────────

def filter_graph(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    group: Optional[str] = None,
    layer: Optional[str] = None,
    min_score: Optional[float] = None,
    max_nodes: Optional[int] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """
    Filter nodes/links by group, layer, score, and limit count.
    """
    filtered_nodes = nodes
    if group:
        filtered_nodes = [n for n in filtered_nodes if n.get("group", "").lower() == group.lower()]
    if layer:
        filtered_nodes = [n for n in filtered_nodes if n.get("layer", "").lower() == layer.lower()]
    if min_score is not None:
        filtered_nodes = [n for n in filtered_nodes if n.get("score", 0) >= min_score]
    if max_nodes:
        filtered_nodes = filtered_nodes[:max_nodes]

    valid_ids = {n["id"] for n in filtered_nodes}
    filtered_links = [
        lnk for lnk in links
        if lnk.get("source") in valid_ids and lnk.get("target") in valid_ids
    ]

    return filtered_nodes, filtered_links


# ─── Graph Statistics ────────────────────────────────────────────────────────

def compute_graph_statistics(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Compute comprehensive statistics about the knowledge graph.
    """
    # Degree distribution
    degree: Dict[str, int] = defaultdict(int)
    for lnk in links:
        degree[lnk.get("source", "")] += 1
        degree[lnk.get("target", "")] += 1

    degrees = list(degree.values()) if degree else [0]

    # Group / Layer breakdown
    group_counts: Dict[str, int] = defaultdict(int)
    layer_counts: Dict[str, int] = defaultdict(int)
    scores: List[float] = []
    for n in nodes:
        group_counts[n.get("group", "Unknown")] += 1
        layer_counts[n.get("layer", "unknown")] += 1
        s = n.get("score")
        if s is not None:
            scores.append(float(s))

    # Relationship breakdown
    rel_counts: Dict[str, int] = defaultdict(int)
    weights: List[float] = []
    for lnk in links:
        rel_counts[lnk.get("relationship", "unknown")] += 1
        w = lnk.get("weight")
        if w is not None:
            weights.append(float(w))

    # Network density
    n = len(nodes)
    max_edges = n * (n - 1) // 2
    density = len(links) / max(max_edges, 1)

    return {
        "node_count": len(nodes),
        "edge_count": len(links),
        "network_density": round(density, 6),
        "group_breakdown": dict(group_counts),
        "layer_breakdown": dict(layer_counts),
        "relationship_breakdown": dict(rel_counts),
        "degree_stats": {
            "mean": round(statistics.mean(degrees), 2),
            "median": round(statistics.median(degrees), 2),
            "max": max(degrees),
            "min": min(degrees),
            "stdev": round(statistics.stdev(degrees), 2) if len(degrees) > 1 else 0,
        },
        "score_stats": {
            "mean": round(statistics.mean(scores), 4) if scores else 0,
            "median": round(statistics.median(scores), 4) if scores else 0,
            "max": round(max(scores), 4) if scores else 0,
            "min": round(min(scores), 4) if scores else 0,
        } if scores else {},
        "weight_stats": {
            "mean": round(statistics.mean(weights), 4) if weights else 0,
            "median": round(statistics.median(weights), 4) if weights else 0,
        } if weights else {},
        "top_degree_nodes": sorted(
            degree.items(), key=lambda x: x[1], reverse=True
        )[:10],
    }


# ─── Markdown Summary Report ────────────────────────────────────────────────

def export_summary_report(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    stats: Optional[Dict[str, Any]] = None,
) -> str:
    """
    Generate a human-readable Markdown summary suitable for
    publications, slide decks, or regulatory submissions.
    """
    if stats is None:
        stats = compute_graph_statistics(nodes, links)

    lines = [
        "# CARVanta Knowledge Graph — Summary Report",
        "",
        f"**Generated:** {datetime.now(timezone.utc).strftime('%Y-%m-%d %H:%M UTC')}",
        "",
        "## Overview",
        "",
        f"| Metric | Value |",
        f"|--------|-------|",
        f"| Total Nodes | {stats['node_count']:,} |",
        f"| Total Edges | {stats['edge_count']:,} |",
        f"| Network Density | {stats['network_density']:.6f} |",
        f"| Avg Degree | {stats['degree_stats']['mean']:.1f} |",
        f"| Max Degree | {stats['degree_stats']['max']} |",
        "",
        "## Node Groups",
        "",
        "| Group | Count |",
        "|-------|-------|",
    ]
    for grp, cnt in sorted(stats["group_breakdown"].items(), key=lambda x: -x[1]):
        lines.append(f"| {grp} | {cnt:,} |")

    lines.extend([
        "",
        "## Layer Distribution",
        "",
        "| Layer | Count |",
        "|-------|-------|",
    ])
    for lyr, cnt in sorted(stats["layer_breakdown"].items(), key=lambda x: -x[1]):
        lines.append(f"| {lyr} | {cnt:,} |")

    lines.extend([
        "",
        "## Top Connected Nodes (Hub Genes)",
        "",
        "| Node | Degree |",
        "|------|--------|",
    ])
    for nid, deg in stats.get("top_degree_nodes", [])[:10]:
        lines.append(f"| {nid} | {deg} |")

    lines.extend([
        "",
        "## Relationship Types",
        "",
        "| Relationship | Count |",
        "|-------------|-------|",
    ])
    for rel, cnt in sorted(stats.get("relationship_breakdown", {}).items(), key=lambda x: -x[1]):
        lines.append(f"| {rel} | {cnt:,} |")

    lines.extend([
        "",
        "---",
        "*Report generated by CARVanta Neural Network Bridge v2.0*",
    ])

    return "\n".join(lines)
