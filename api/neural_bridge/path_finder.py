"""
CARVanta Neural Bridge — Path Finder & Link Prediction
========================================================
Shortest-path algorithms and link-prediction heuristics for
the antigen–disease–pathway knowledge graph.

Path-finding algorithms:
  ▸ BFS shortest path (unweighted)
  ▸ Dijkstra shortest path (weighted)
  ▸ All shortest paths between two nodes
  ▸ K-shortest paths (Yen's algorithm)
  ▸ Path-based distance matrix
  ▸ Eccentricity, radius, diameter

Link-prediction heuristics:
  ▸ Common Neighbours
  ▸ Jaccard Coefficient
  ▸ Adamic-Adar Index
  ▸ Preferential Attachment
  ▸ Resource Allocation Index
  ▸ Combined scoring with ensemble ranking

These link-prediction scores are biologically meaningful:
a high score between two antigens suggests a shared regulatory
context or undiscovered co-expression signal.
"""

from __future__ import annotations

import heapq
import math
import statistics
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Set, Tuple


# ═══════════════════════════════════════════════════════════════════════════════
# Internal helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _adj_unweighted(links: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
    adj: Dict[str, Set[str]] = defaultdict(set)
    for lnk in links:
        s, t = lnk.get("source", ""), lnk.get("target", "")
        if s and t:
            adj[s].add(t)
            adj[t].add(s)
    return dict(adj)


def _adj_weighted(links: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    adj: Dict[str, Dict[str, float]] = defaultdict(dict)
    for lnk in links:
        s, t = lnk.get("source", ""), lnk.get("target", "")
        w = float(lnk.get("weight", 1.0))
        if s and t:
            # Lower weight → stronger connection → shorter distance
            dist = 1.0 / max(w, 0.01)
            adj[s][t] = min(adj[s].get(t, float("inf")), dist)
            adj[t][s] = min(adj[t].get(s, float("inf")), dist)
    return dict(adj)


# ═══════════════════════════════════════════════════════════════════════════════
# BFS Shortest Path (unweighted)
# ═══════════════════════════════════════════════════════════════════════════════

def bfs_shortest_path(
    links: List[Dict[str, Any]],
    source: str,
    target: str,
) -> Dict[str, Any]:
    """
    Find the shortest unweighted path between source and target.
    Returns the path, length, and intermediate nodes with their groups.
    """
    adj = _adj_unweighted(links)

    # BFS with parent tracking
    parent: Dict[str, Optional[str]] = {source: None}
    queue = deque([source])

    while queue:
        u = queue.popleft()
        if u == target:
            break
        for v in adj.get(u, set()):
            if v not in parent:
                parent[v] = u
                queue.append(v)

    if target not in parent:
        return {
            "found": False,
            "source": source,
            "target": target,
            "message": f"No path exists between '{source}' and '{target}'.",
        }

    # Reconstruct
    path = []
    current = target
    while current is not None:
        path.append(current)
        current = parent[current]
    path.reverse()

    return {
        "found": True,
        "source": source,
        "target": target,
        "path": path,
        "length": len(path) - 1,
        "hops": len(path) - 1,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Dijkstra Shortest Path (weighted)
# ═══════════════════════════════════════════════════════════════════════════════

def dijkstra_shortest_path(
    links: List[Dict[str, Any]],
    source: str,
    target: str,
) -> Dict[str, Any]:
    """
    Dijkstra's algorithm using edge weights (inverse of similarity).
    Lower total weight → biologically closer path.
    """
    adj = _adj_weighted(links)

    dist: Dict[str, float] = {source: 0.0}
    parent: Dict[str, Optional[str]] = {source: None}
    heap = [(0.0, source)]
    visited: Set[str] = set()

    while heap:
        d, u = heapq.heappop(heap)
        if u in visited:
            continue
        visited.add(u)

        if u == target:
            break

        for v, w in adj.get(u, {}).items():
            new_dist = d + w
            if new_dist < dist.get(v, float("inf")):
                dist[v] = new_dist
                parent[v] = u
                heapq.heappush(heap, (new_dist, v))

    if target not in parent:
        return {
            "found": False,
            "source": source,
            "target": target,
            "algorithm": "dijkstra",
            "message": f"No weighted path from '{source}' to '{target}'.",
        }

    # Reconstruct
    path = []
    current: Optional[str] = target
    while current is not None:
        path.append(current)
        current = parent[current]
    path.reverse()

    return {
        "found": True,
        "source": source,
        "target": target,
        "algorithm": "dijkstra",
        "path": path,
        "hops": len(path) - 1,
        "total_weight": round(dist[target], 4),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# All Shortest Paths
# ═══════════════════════════════════════════════════════════════════════════════

def all_shortest_paths(
    links: List[Dict[str, Any]],
    source: str,
    target: str,
    max_paths: int = 10,
) -> Dict[str, Any]:
    """
    Find ALL shortest paths (same minimum length) between source and target.
    Uses BFS with full predecessor tracking.
    """
    adj = _adj_unweighted(links)

    dist: Dict[str, int] = {source: 0}
    preds: Dict[str, List[str]] = defaultdict(list)
    queue = deque([source])

    while queue:
        u = queue.popleft()
        for v in adj.get(u, set()):
            if v not in dist:
                dist[v] = dist[u] + 1
                queue.append(v)
            if dist.get(v) == dist[u] + 1:
                preds[v].append(u)

    if target not in dist:
        return {"found": False, "paths": [], "count": 0}

    # Backtrack to enumerate all paths
    all_paths: List[List[str]] = []

    def _backtrack(node: str, path: List[str]):
        if node == source:
            all_paths.append(list(reversed(path)))
            return
        if len(all_paths) >= max_paths:
            return
        for p in preds.get(node, []):
            _backtrack(p, path + [p])

    _backtrack(target, [target])

    return {
        "found": True,
        "source": source,
        "target": target,
        "shortest_length": dist[target],
        "paths": all_paths[:max_paths],
        "count": len(all_paths),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# K-Shortest Paths (Yen's Algorithm)
# ═══════════════════════════════════════════════════════════════════════════════

def k_shortest_paths(
    links: List[Dict[str, Any]],
    source: str,
    target: str,
    k: int = 5,
) -> Dict[str, Any]:
    """
    Yen's algorithm for the K shortest loopless paths.
    More expensive than BFS but produces diverse alternative paths
    that may reveal alternative biological routing.
    """
    adj = _adj_unweighted(links)

    # Helper: BFS with excluded nodes/edges
    def _bfs_restricted(src: str, tgt: str, excluded_nodes: Set[str], excluded_edges: Set[Tuple[str, str]]):
        parent: Dict[str, Optional[str]] = {src: None}
        q = deque([src])
        while q:
            u = q.popleft()
            if u == tgt:
                path = []
                cur: Optional[str] = tgt
                while cur is not None:
                    path.append(cur)
                    cur = parent[cur]
                return list(reversed(path))
            for v in adj.get(u, set()):
                if v in excluded_nodes or v in parent:
                    continue
                if (u, v) in excluded_edges or (v, u) in excluded_edges:
                    continue
                parent[v] = u
                q.append(v)
        return None

    # First shortest path
    first = _bfs_restricted(source, target, set(), set())
    if not first:
        return {"found": False, "paths": [], "count": 0}

    A: List[List[str]] = [first]
    B: List[Tuple[int, List[str]]] = []  # (cost, path)

    for ki in range(1, k):
        prev_path = A[-1]
        for i in range(len(prev_path) - 1):
            spur_node = prev_path[i]
            root_path = prev_path[:i + 1]

            # Exclude edges used by existing shortest paths
            excluded_edges: Set[Tuple[str, str]] = set()
            for p in A:
                if p[:i + 1] == root_path:
                    if i + 1 < len(p):
                        excluded_edges.add((p[i], p[i + 1]))

            # Exclude root-path nodes (except spur)
            excluded_nodes = set(root_path[:-1])

            spur_path = _bfs_restricted(spur_node, target, excluded_nodes, excluded_edges)
            if spur_path:
                total = root_path[:-1] + spur_path
                cost = len(total) - 1
                if total not in A:
                    B.append((cost, total))

        if not B:
            break

        B.sort(key=lambda x: x[0])
        _, best = B.pop(0)
        A.append(best)

    return {
        "found": True,
        "source": source,
        "target": target,
        "paths": A,
        "count": len(A),
        "lengths": [len(p) - 1 for p in A],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Eccentricity / Radius / Diameter
# ═══════════════════════════════════════════════════════════════════════════════

def eccentricity(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    sample_size: int = 100,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Compute eccentricity (max BFS distance) for sampled nodes.
    Derives graph radius, diameter, and centre nodes.
    """
    import random as _rng
    rng = _rng.Random(seed)
    adj = _adj_unweighted(links)
    ids = [n["id"] for n in nodes]

    sample = rng.sample(ids, min(sample_size, len(ids)))
    ecc: Dict[str, int] = {}

    for v in sample:
        dists = {}
        visited_set: Set[str] = {v}
        q = deque([(v, 0)])
        while q:
            u, d = q.popleft()
            dists[u] = d
            for w in adj.get(u, set()):
                if w not in visited_set:
                    visited_set.add(w)
                    q.append((w, d + 1))
        ecc[v] = max(dists.values()) if dists else 0

    ecc_values = list(ecc.values())
    radius = min(ecc_values) if ecc_values else 0
    diameter = max(ecc_values) if ecc_values else 0
    centre = [v for v, e in ecc.items() if e == radius]
    periphery = [v for v, e in ecc.items() if e == diameter]

    return {
        "radius": radius,
        "diameter": diameter,
        "centre_nodes": centre[:10],
        "periphery_nodes": periphery[:10],
        "sample_size": len(sample),
        "eccentricity_distribution": {
            v: e for v, e in sorted(ecc.items(), key=lambda x: x[1])[:20]
        },
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Link Prediction
# ═══════════════════════════════════════════════════════════════════════════════

def common_neighbours_score(
    adj: Dict[str, Set[str]], u: str, v: str,
) -> int:
    """Number of shared neighbours: |N(u) ∩ N(v)|."""
    return len(adj.get(u, set()) & adj.get(v, set()))


def jaccard_coefficient(
    adj: Dict[str, Set[str]], u: str, v: str,
) -> float:
    """Jaccard: |N(u) ∩ N(v)| / |N(u) ∪ N(v)|."""
    nu, nv = adj.get(u, set()), adj.get(v, set())
    union = len(nu | nv)
    return len(nu & nv) / union if union else 0.0


def adamic_adar_index(
    adj: Dict[str, Set[str]], u: str, v: str,
) -> float:
    """Adamic-Adar: Σ 1/log(|N(w)|) for w ∈ N(u) ∩ N(v)."""
    common = adj.get(u, set()) & adj.get(v, set())
    score = 0.0
    for w in common:
        deg_w = len(adj.get(w, set()))
        if deg_w > 1:
            score += 1.0 / math.log(deg_w)
    return score


def preferential_attachment(
    adj: Dict[str, Set[str]], u: str, v: str,
) -> int:
    """Preferential attachment: |N(u)| × |N(v)|."""
    return len(adj.get(u, set())) * len(adj.get(v, set()))


def resource_allocation_index(
    adj: Dict[str, Set[str]], u: str, v: str,
) -> float:
    """Resource allocation: Σ 1/|N(w)| for w ∈ N(u) ∩ N(v)."""
    common = adj.get(u, set()) & adj.get(v, set())
    return sum(1.0 / max(len(adj.get(w, set())), 1) for w in common)


def predict_links(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    top_n: int = 50,
    group_filter: Optional[str] = None,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Predict missing links (undiscovered antigen–disease associations)
    using an ensemble of 5 heuristics.

    Returns ranked list of predicted (non-existing) edges sorted by
    ensemble score.

    ``group_filter`` restricts prediction to pairs where at least one
    node belongs to the specified group (e.g., "Antigen").
    """
    import random as _rng
    rng = _rng.Random(seed)
    adj = _adj_unweighted(links)
    id_list = [n["id"] for n in nodes]
    node_map = {n["id"]: n for n in nodes}

    # Existing edge set
    edges = set()
    for lnk in links:
        s, t = lnk.get("source", ""), lnk.get("target", "")
        edges.add((s, t))
        edges.add((t, s))

    # Sample non-adjacent pairs (for large graphs we can't check all)
    max_candidates = min(5000, len(id_list) * 10)
    candidates: List[Tuple[str, str]] = []
    attempts = 0
    while len(candidates) < max_candidates and attempts < max_candidates * 5:
        u = rng.choice(id_list)
        v = rng.choice(id_list)
        attempts += 1
        if u == v or (u, v) in edges:
            continue
        if group_filter:
            g_u = node_map.get(u, {}).get("group", "")
            g_v = node_map.get(v, {}).get("group", "")
            if group_filter not in (g_u, g_v):
                continue
        candidates.append((u, v))

    # Score each candidate
    scored: List[Dict[str, Any]] = []
    for u, v in candidates:
        cn = common_neighbours_score(adj, u, v)
        jc = jaccard_coefficient(adj, u, v)
        aa = adamic_adar_index(adj, u, v)
        pa = preferential_attachment(adj, u, v)
        ra = resource_allocation_index(adj, u, v)

        # Ensemble: normalised weighted sum
        ensemble = (
            0.25 * min(cn / 10, 1.0) +
            0.20 * jc +
            0.25 * min(aa / 3, 1.0) +
            0.10 * min(pa / 500, 1.0) +
            0.20 * min(ra / 2, 1.0)
        )

        if ensemble > 0.05:  # threshold
            scored.append({
                "source": u,
                "target": v,
                "source_name": node_map.get(u, {}).get("name", u),
                "target_name": node_map.get(v, {}).get("name", v),
                "ensemble_score": round(ensemble, 4),
                "common_neighbours": cn,
                "jaccard": round(jc, 4),
                "adamic_adar": round(aa, 4),
                "preferential_attachment": pa,
                "resource_allocation": round(ra, 4),
            })

    scored.sort(key=lambda x: x["ensemble_score"], reverse=True)

    return {
        "predictions": scored[:top_n],
        "total_candidates_evaluated": len(candidates),
        "predictions_above_threshold": len(scored),
        "method": "ensemble (CN + Jaccard + AA + PA + RA)",
    }
