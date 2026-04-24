"""
CARVanta Neural Bridge — Graph Comparison Engine
==================================================
Compare two subgraphs or graph states to identify structural
differences, divergent centrality rankings, and emergent patterns.

Use cases:
  ▸ Compare disease-specific subgraphs (e.g., DLBCL vs AML)
  ▸ Before/after treatment response network changes
  ▸ Wild-type vs mutant pathway topology
  ▸ Cross-species comparative genomics graphs
  ▸ Identify unique edges/nodes in each subgraph
  ▸ Jaccard overlap at node and edge level
  ▸ Centrality rank correlation (Kendall's tau)
  ▸ Density / clustering comparison
"""

from __future__ import annotations

import math
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple


# ═══════════════════════════════════════════════════════════════════════════════
# Adjacency helper
# ═══════════════════════════════════════════════════════════════════════════════

def _adj(links: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
    a: Dict[str, Set[str]] = defaultdict(set)
    for lnk in links:
        s, t = lnk.get("source", ""), lnk.get("target", "")
        if s and t:
            a[s].add(t)
            a[t].add(s)
    return dict(a)


def _edge_set(links: List[Dict[str, Any]]) -> Set[Tuple[str, str]]:
    edges: Set[Tuple[str, str]] = set()
    for lnk in links:
        s, t = lnk.get("source", ""), lnk.get("target", "")
        if s and t:
            edges.add((min(s, t), max(s, t)))
    return edges


# ═══════════════════════════════════════════════════════════════════════════════
# Degree distribution
# ═══════════════════════════════════════════════════════════════════════════════

def _degree_stats(adj: Dict[str, Set[str]]) -> Dict[str, Any]:
    if not adj:
        return {"min": 0, "max": 0, "mean": 0, "median": 0}
    degrees = sorted(len(nb) for nb in adj.values())
    n = len(degrees)
    return {
        "min": degrees[0],
        "max": degrees[-1],
        "mean": round(sum(degrees) / n, 2),
        "median": degrees[n // 2],
    }


def _density(n_nodes: int, n_edges: int) -> float:
    if n_nodes < 2:
        return 0.0
    return round(2 * n_edges / (n_nodes * (n_nodes - 1)), 6)


def _clustering_coeff(adj: Dict[str, Set[str]]) -> float:
    total_cc = 0.0
    count = 0
    for v, nb in adj.items():
        deg = len(nb)
        if deg < 2:
            continue
        triangles = 0
        nb_list = list(nb)
        for i in range(len(nb_list)):
            for j in range(i + 1, min(len(nb_list), 30)):
                if nb_list[j] in adj.get(nb_list[i], set()):
                    triangles += 1
        cc = 2 * triangles / (deg * (deg - 1))
        total_cc += cc
        count += 1
    return round(total_cc / max(count, 1), 6)


# ═══════════════════════════════════════════════════════════════════════════════
# Subgraph Extraction
# ═══════════════════════════════════════════════════════════════════════════════

def extract_subgraph(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    filter_group: Optional[str] = None,
    filter_ids: Optional[List[str]] = None,
) -> Tuple[List[Dict[str, Any]], List[Dict[str, Any]]]:
    """Extract a subgraph by group or explicit node IDs."""
    if filter_ids:
        id_set = set(filter_ids)
    elif filter_group:
        id_set = {n["id"] for n in nodes if n.get("group") == filter_group}
    else:
        id_set = {n["id"] for n in nodes}

    sub_nodes = [n for n in nodes if n["id"] in id_set]
    sub_links = [
        l for l in links
        if l.get("source") in id_set and l.get("target") in id_set
    ]
    return sub_nodes, sub_links


# ═══════════════════════════════════════════════════════════════════════════════
# Graph Comparison
# ═══════════════════════════════════════════════════════════════════════════════

def compare_subgraphs(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    group_a: str,
    group_b: str,
) -> Dict[str, Any]:
    """
    Compare two group-based subgraphs side by side.
    Returns structural metrics + overlap analysis.
    """
    nodes_a, links_a = extract_subgraph(nodes, links, filter_group=group_a)
    nodes_b, links_b = extract_subgraph(nodes, links, filter_group=group_b)

    ids_a = {n["id"] for n in nodes_a}
    ids_b = {n["id"] for n in nodes_b}
    edges_a = _edge_set(links_a)
    edges_b = _edge_set(links_b)

    adj_a = _adj(links_a)
    adj_b = _adj(links_b)

    # Cross-group edges (connecting A and B)
    cross_edges = [
        l for l in links
        if (l.get("source") in ids_a and l.get("target") in ids_b) or
           (l.get("source") in ids_b and l.get("target") in ids_a)
    ]

    return {
        "group_a": {
            "name": group_a,
            "nodes": len(nodes_a),
            "edges": len(links_a),
            "density": _density(len(nodes_a), len(links_a)),
            "clustering": _clustering_coeff(adj_a),
            "degree_stats": _degree_stats(adj_a),
        },
        "group_b": {
            "name": group_b,
            "nodes": len(nodes_b),
            "edges": len(links_b),
            "density": _density(len(nodes_b), len(links_b)),
            "clustering": _clustering_coeff(adj_b),
            "degree_stats": _degree_stats(adj_b),
        },
        "cross_group_edges": len(cross_edges),
        "node_overlap": {
            "shared": len(ids_a & ids_b),
            "only_a": len(ids_a - ids_b),
            "only_b": len(ids_b - ids_a),
            "jaccard": round(
                len(ids_a & ids_b) / max(len(ids_a | ids_b), 1), 4
            ),
        },
        "edge_overlap": {
            "shared": len(edges_a & edges_b),
            "only_a": len(edges_a - edges_b),
            "only_b": len(edges_b - edges_a),
            "jaccard": round(
                len(edges_a & edges_b) / max(len(edges_a | edges_b), 1), 4
            ),
        },
    }


def centrality_comparison(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    group_a: str,
    group_b: str,
    top_n: int = 10,
) -> Dict[str, Any]:
    """
    Compare degree centrality rankings between two subgraphs.
    Identifies nodes that are central in one but peripheral in another.
    """
    nodes_a, links_a = extract_subgraph(nodes, links, filter_group=group_a)
    nodes_b, links_b = extract_subgraph(nodes, links, filter_group=group_b)

    adj_all = _adj(links)

    # Compute centrality in each context
    def _rank(node_list: List[Dict], adj: Dict) -> List[Dict]:
        ranked = []
        for n in node_list:
            nid = n["id"]
            deg = len(adj.get(nid, set()))
            ranked.append({"node": nid, "name": n.get("name", ""), "degree": deg})
        ranked.sort(key=lambda x: x["degree"], reverse=True)
        return ranked

    rank_a = _rank(nodes_a, _adj(links_a))
    rank_b = _rank(nodes_b, _adj(links_b))

    # Cross-compare: nodes in A with connections to B
    bridge_nodes = []
    ids_a = {n["id"] for n in nodes_a}
    ids_b = {n["id"] for n in nodes_b}

    for n in nodes:
        nid = n["id"]
        nb = adj_all.get(nid, set())
        conn_a = len(nb & ids_a)
        conn_b = len(nb & ids_b)
        if conn_a > 0 and conn_b > 0:
            bridge_nodes.append({
                "node": nid,
                "name": n.get("name", ""),
                "group": n.get("group", ""),
                "connections_to_a": conn_a,
                "connections_to_b": conn_b,
                "bridge_score": conn_a + conn_b,
            })

    bridge_nodes.sort(key=lambda x: x["bridge_score"], reverse=True)

    return {
        "top_in_a": rank_a[:top_n],
        "top_in_b": rank_b[:top_n],
        "bridge_nodes": bridge_nodes[:top_n],
    }


def group_interaction_matrix(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Compute the interaction density between every pair of groups.
    Returns a matrix showing how strongly each group connects to others.
    """
    nmap = {n["id"]: n.get("group", "Unknown") for n in nodes}
    groups = sorted(set(nmap.values()))

    matrix: Dict[str, Dict[str, int]] = {g: {g2: 0 for g2 in groups} for g in groups}

    for lnk in links:
        s, t = lnk.get("source", ""), lnk.get("target", "")
        gs = nmap.get(s, "Unknown")
        gt = nmap.get(t, "Unknown")
        matrix[gs][gt] += 1
        if gs != gt:
            matrix[gt][gs] += 1

    # Normalise by group sizes
    group_sizes = defaultdict(int)
    for g in nmap.values():
        group_sizes[g] += 1

    normalised: Dict[str, Dict[str, float]] = {}
    for g1 in groups:
        normalised[g1] = {}
        for g2 in groups:
            max_edges = group_sizes[g1] * group_sizes[g2]
            if g1 == g2:
                max_edges = group_sizes[g1] * (group_sizes[g1] - 1) // 2
            normalised[g1][g2] = round(
                matrix[g1][g2] / max(max_edges, 1), 4
            )

    return {
        "groups": groups,
        "raw_counts": matrix,
        "normalised_density": normalised,
        "strongest_inter_group": max(
            ((g1, g2, normalised[g1][g2])
             for g1 in groups for g2 in groups if g1 < g2),
            key=lambda x: x[2],
            default=("", "", 0),
        ),
    }
