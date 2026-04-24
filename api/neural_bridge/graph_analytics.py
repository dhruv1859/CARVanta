"""
CARVanta Neural Bridge — Graph Analytics Engine
=================================================
Advanced network science metrics computed on the antigen–disease–pathway
knowledge graph.  Every metric is implemented from first-principles
(no ``networkx`` dependency) so the module remains zero-dep.

Metrics implemented:
  ▸ Degree centrality (normalised)
  ▸ Betweenness centrality (Brandes' algorithm)
  ▸ Closeness centrality (BFS-based)
  ▸ PageRank (power-iteration)
  ▸ Eigenvector centrality (power-iteration)
  ▸ Hub & Authority scores (HITS)
  ▸ Clustering coefficient (local + global)
  ▸ Connected-component analysis
  ▸ Assortativity coefficient (degree–degree correlation)
  ▸ Rich-club coefficient
  ▸ Network motif census (triads)
  ▸ Small-world-ness σ estimation

All public functions accept the standard ``(nodes, links)`` pair
produced by ``graph_builder.build_graph()``.
"""

from __future__ import annotations

import math
import random
import statistics
from collections import defaultdict, deque
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple


# ═══════════════════════════════════════════════════════════════════════════════
# Internal helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _adj(links: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
    """Build undirected adjacency from edge list."""
    a: Dict[str, Set[str]] = defaultdict(set)
    for lnk in links:
        s, t = lnk.get("source", ""), lnk.get("target", "")
        if s and t:
            a[s].add(t)
            a[t].add(s)
    return dict(a)


def _node_ids(nodes: List[Dict[str, Any]]) -> List[str]:
    return [n["id"] for n in nodes]


def _bfs_distances(adj: Dict[str, Set[str]], start: str) -> Dict[str, int]:
    """BFS shortest-path distances from ``start``."""
    dist: Dict[str, int] = {start: 0}
    queue = deque([start])
    while queue:
        u = queue.popleft()
        for v in adj.get(u, set()):
            if v not in dist:
                dist[v] = dist[u] + 1
                queue.append(v)
    return dist


# ═══════════════════════════════════════════════════════════════════════════════
# Degree centrality
# ═══════════════════════════════════════════════════════════════════════════════

def degree_centrality(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
) -> Dict[str, float]:
    """
    Normalised degree centrality  C_D(v) = deg(v) / (n - 1).
    """
    adj = _adj(links)
    n = len(nodes)
    denom = max(n - 1, 1)
    return {
        nid: len(adj.get(nid, set())) / denom
        for nid in _node_ids(nodes)
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Betweenness centrality  (Brandes 2001)
# ═══════════════════════════════════════════════════════════════════════════════

def betweenness_centrality(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    normalise: bool = True,
    sample_frac: float = 1.0,
    seed: int = 42,
) -> Dict[str, float]:
    """
    Brandes' O(VE) algorithm for betweenness centrality.

    For very large graphs set ``sample_frac < 1`` to estimate
    centrality from a random subset of source nodes.
    """
    adj = _adj(links)
    ids = _node_ids(nodes)
    n = len(ids)
    bc: Dict[str, float] = {v: 0.0 for v in ids}

    # Optional sampling
    rng = random.Random(seed)
    sources = ids
    if sample_frac < 1.0:
        k = max(1, int(n * sample_frac))
        sources = rng.sample(ids, k)

    for s in sources:
        # BFS from s
        stack: List[str] = []
        pred: Dict[str, List[str]] = {v: [] for v in ids}
        sigma: Dict[str, int] = {v: 0 for v in ids}
        sigma[s] = 1
        dist: Dict[str, int] = {v: -1 for v in ids}
        dist[s] = 0
        queue: deque = deque([s])

        while queue:
            v = queue.popleft()
            stack.append(v)
            for w in adj.get(v, set()):
                # First visit?
                if dist[w] < 0:
                    queue.append(w)
                    dist[w] = dist[v] + 1
                # Shortest path to w via v?
                if dist[w] == dist[v] + 1:
                    sigma[w] += sigma[v]
                    pred[w].append(v)

        # Back-propagation
        delta: Dict[str, float] = {v: 0.0 for v in ids}
        while stack:
            w = stack.pop()
            for v in pred[w]:
                delta[v] += (sigma[v] / max(sigma[w], 1)) * (1 + delta[w])
            if w != s:
                bc[w] += delta[w]

    # Normalise for undirected graph
    if normalise and n > 2:
        scale = 1.0 / ((n - 1) * (n - 2))
        if sample_frac < 1.0:
            scale *= n / len(sources)
        bc = {v: c * scale for v, c in bc.items()}

    return bc


# ═══════════════════════════════════════════════════════════════════════════════
# Closeness centrality
# ═══════════════════════════════════════════════════════════════════════════════

def closeness_centrality(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
) -> Dict[str, float]:
    """
    Closeness centrality  C_C(v) = (n - 1) / Σ d(v, u).
    Uses Wasserman–Faust normalisation for disconnected graphs.
    """
    adj = _adj(links)
    ids = _node_ids(nodes)
    n = len(ids)
    cc: Dict[str, float] = {}

    for v in ids:
        dists = _bfs_distances(adj, v)
        reachable = len(dists) - 1  # exclude self
        total_dist = sum(dists.values())
        if reachable > 0 and total_dist > 0:
            # Wasserman–Faust: scale by (reachable / (n-1))
            cc[v] = (reachable / max(n - 1, 1)) * (reachable / total_dist)
        else:
            cc[v] = 0.0

    return cc


# ═══════════════════════════════════════════════════════════════════════════════
# PageRank
# ═══════════════════════════════════════════════════════════════════════════════

def pagerank(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    damping: float = 0.85,
    max_iter: int = 100,
    tol: float = 1e-6,
) -> Dict[str, float]:
    """
    Power-iteration PageRank.
    Damping factor ``d = 0.85`` is typical; convergence is checked via
    L1-norm between successive iterations.
    """
    adj = _adj(links)
    ids = _node_ids(nodes)
    n = len(ids)
    if n == 0:
        return {}

    pr = {v: 1.0 / n for v in ids}

    for _ in range(max_iter):
        new_pr: Dict[str, float] = {}
        dangling_sum = sum(pr[v] for v in ids if not adj.get(v))

        for v in ids:
            rank = (1 - damping) / n + damping * dangling_sum / n
            for u in adj.get(v, set()):
                out_degree = len(adj.get(u, set()))
                if out_degree > 0:
                    rank += damping * pr[u] / out_degree
            new_pr[v] = rank

        # Convergence check
        diff = sum(abs(new_pr[v] - pr[v]) for v in ids)
        pr = new_pr
        if diff < tol:
            break

    return pr


# ═══════════════════════════════════════════════════════════════════════════════
# Eigenvector centrality
# ═══════════════════════════════════════════════════════════════════════════════

def eigenvector_centrality(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    max_iter: int = 100,
    tol: float = 1e-6,
) -> Dict[str, float]:
    """
    Power-iteration approximation of the leading eigenvector
    of the adjacency matrix.
    """
    adj = _adj(links)
    ids = _node_ids(nodes)
    n = len(ids)
    if n == 0:
        return {}

    x = {v: 1.0 / n for v in ids}

    for _ in range(max_iter):
        x_new: Dict[str, float] = {}
        for v in ids:
            s = sum(x.get(u, 0) for u in adj.get(v, set()))
            x_new[v] = s

        # Normalise
        norm = math.sqrt(sum(val ** 2 for val in x_new.values())) or 1.0
        x_new = {v: val / norm for v, val in x_new.items()}

        diff = sum(abs(x_new[v] - x[v]) for v in ids)
        x = x_new
        if diff < tol:
            break

    return x


# ═══════════════════════════════════════════════════════════════════════════════
# HITS (Hub & Authority scores)
# ═══════════════════════════════════════════════════════════════════════════════

def hits(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    max_iter: int = 100,
    tol: float = 1e-6,
) -> Dict[str, Dict[str, float]]:
    """
    Hyperlink-Induced Topic Search.
    Returns ``{"hubs": {...}, "authorities": {...}}``.
    For undirected graphs hubs ≈ authorities, but we keep
    both for API symmetry with directed-graph consumers.
    """
    adj = _adj(links)
    ids = _node_ids(nodes)
    n = len(ids)
    if n == 0:
        return {"hubs": {}, "authorities": {}}

    hub = {v: 1.0 for v in ids}
    auth = {v: 1.0 for v in ids}

    for _ in range(max_iter):
        # Authority update
        new_auth: Dict[str, float] = {}
        for v in ids:
            new_auth[v] = sum(hub.get(u, 0) for u in adj.get(v, set()))
        norm_a = math.sqrt(sum(val ** 2 for val in new_auth.values())) or 1.0
        new_auth = {v: val / norm_a for v, val in new_auth.items()}

        # Hub update
        new_hub: Dict[str, float] = {}
        for v in ids:
            new_hub[v] = sum(new_auth.get(u, 0) for u in adj.get(v, set()))
        norm_h = math.sqrt(sum(val ** 2 for val in new_hub.values())) or 1.0
        new_hub = {v: val / norm_h for v, val in new_hub.items()}

        # Convergence
        diff = sum(abs(new_hub[v] - hub[v]) for v in ids) + sum(abs(new_auth[v] - auth[v]) for v in ids)
        hub, auth = new_hub, new_auth
        if diff < tol:
            break

    return {"hubs": hub, "authorities": auth}


# ═══════════════════════════════════════════════════════════════════════════════
# Clustering coefficient
# ═══════════════════════════════════════════════════════════════════════════════

def local_clustering_coefficient(
    adj: Dict[str, Set[str]],
    node: str,
) -> float:
    """
    Local clustering coefficient of ``node``.
    C(v) = 2T(v) / (k_v * (k_v - 1))  where T(v) is the number
    of triangles through v and k_v is its degree.
    """
    neighbours = adj.get(node, set())
    k = len(neighbours)
    if k < 2:
        return 0.0

    triangles = 0
    nb_list = list(neighbours)
    for i in range(len(nb_list)):
        for j in range(i + 1, len(nb_list)):
            if nb_list[j] in adj.get(nb_list[i], set()):
                triangles += 1

    return (2 * triangles) / (k * (k - 1))


def clustering_coefficients(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Local clustering coefficient per node + global average.
    """
    adj = _adj(links)
    ids = _node_ids(nodes)

    local = {v: round(local_clustering_coefficient(adj, v), 4) for v in ids}
    values = list(local.values())
    avg = statistics.mean(values) if values else 0.0

    return {
        "local": local,
        "global_average": round(avg, 4),
        "transitivity": _transitivity(adj, ids),
    }


def _transitivity(adj: Dict[str, Set[str]], ids: List[str]) -> float:
    """
    Global transitivity (ratio of closed triplets to all triplets).
    """
    closed = 0
    total_triplets = 0
    for v in ids:
        nb = list(adj.get(v, set()))
        k = len(nb)
        if k < 2:
            continue
        total_triplets += k * (k - 1) // 2
        for i in range(len(nb)):
            for j in range(i + 1, len(nb)):
                if nb[j] in adj.get(nb[i], set()):
                    closed += 1
    return round(closed / max(total_triplets, 1), 4)


# ═══════════════════════════════════════════════════════════════════════════════
# Connected components
# ═══════════════════════════════════════════════════════════════════════════════

def connected_components(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Find all connected components via BFS.
    Returns component sizes, the largest component, and isolated nodes.
    """
    adj = _adj(links)
    ids = set(_node_ids(nodes))
    visited: Set[str] = set()
    components: List[List[str]] = []

    for start in ids:
        if start in visited:
            continue
        comp: List[str] = []
        queue = deque([start])
        visited.add(start)
        while queue:
            u = queue.popleft()
            comp.append(u)
            for v in adj.get(u, set()):
                if v not in visited and v in ids:
                    visited.add(v)
                    queue.append(v)
        components.append(comp)

    components.sort(key=len, reverse=True)
    sizes = [len(c) for c in components]

    return {
        "n_components": len(components),
        "component_sizes": sizes,
        "largest_component_size": sizes[0] if sizes else 0,
        "largest_component_fraction": round(sizes[0] / len(ids), 4) if sizes and ids else 0,
        "isolated_nodes": [c[0] for c in components if len(c) == 1],
        "n_isolated": sum(1 for c in components if len(c) == 1),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Assortativity (degree–degree correlation)
# ═══════════════════════════════════════════════════════════════════════════════

def degree_assortativity(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
) -> float:
    """
    Newman's degree assortativity coefficient r ∈ [-1, 1].
    Positive → high-degree nodes connect to high-degree nodes.
    Negative → hub-and-spoke topology.
    """
    adj = _adj(links)
    edges = []
    for lnk in links:
        s, t = lnk.get("source", ""), lnk.get("target", "")
        if s and t:
            edges.append((len(adj.get(s, set())), len(adj.get(t, set()))))

    if len(edges) < 2:
        return 0.0

    x = [e[0] for e in edges]
    y = [e[1] for e in edges]
    mean_x = statistics.mean(x)
    mean_y = statistics.mean(y)
    std_x = statistics.stdev(x) if len(x) > 1 else 1.0
    std_y = statistics.stdev(y) if len(y) > 1 else 1.0

    if std_x == 0 or std_y == 0:
        return 0.0

    numerator = sum((xi - mean_x) * (yi - mean_y) for xi, yi in zip(x, y))
    denominator = len(edges) * std_x * std_y
    return round(numerator / max(denominator, 1e-12), 4)


# ═══════════════════════════════════════════════════════════════════════════════
# Rich-club coefficient
# ═══════════════════════════════════════════════════════════════════════════════

def rich_club_coefficient(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    k_values: Optional[List[int]] = None,
) -> Dict[int, float]:
    """
    Rich-club coefficient φ(k) — the fraction of edges among nodes
    with degree > k relative to the maximum possible.

    A high φ means that high-degree nodes (hubs) are preferentially
    interconnected — common in biological signalling networks.
    """
    adj = _adj(links)
    deg = {v: len(adj.get(v, set())) for v in _node_ids(nodes)}
    max_deg = max(deg.values()) if deg else 0

    if k_values is None:
        step = max(1, max_deg // 10)
        k_values = list(range(1, max_deg, step))

    result: Dict[int, float] = {}
    for k in k_values:
        rich = {v for v, d in deg.items() if d > k}
        if len(rich) < 2:
            result[k] = 0.0
            continue

        # Count edges among rich-club members
        e_rich = 0
        for lnk in links:
            s, t = lnk.get("source", ""), lnk.get("target", "")
            if s in rich and t in rich:
                e_rich += 1

        n_rich = len(rich)
        max_edges = n_rich * (n_rich - 1) // 2
        result[k] = round(e_rich / max(max_edges, 1), 4)

    return result


# ═══════════════════════════════════════════════════════════════════════════════
# Small-world-ness estimation
# ═══════════════════════════════════════════════════════════════════════════════

def small_world_sigma(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    n_random: int = 5,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Estimate the small-world coefficient σ = (C / C_rand) / (L / L_rand).
    σ >> 1 indicates a small-world network.

    We approximate by comparing the graph's clustering and path length
    against Erdős–Rényi random graphs of the same density.
    """
    adj = _adj(links)
    ids = _node_ids(nodes)
    n = len(ids)
    m = len(links)

    if n < 10:
        return {"sigma": 0, "note": "Too few nodes for meaningful estimation."}

    # Actual clustering and avg path length
    cc_data = clustering_coefficients(nodes, links)
    c_actual = cc_data["global_average"]

    # Sample average path length (full BFS is expensive for large graphs)
    rng = random.Random(seed)
    sample = rng.sample(ids, min(50, n))
    path_lengths = []
    for s in sample:
        dists = _bfs_distances(adj, s)
        path_lengths.extend(d for d in dists.values() if d > 0)
    l_actual = statistics.mean(path_lengths) if path_lengths else float("inf")

    # Erdős–Rényi reference
    p = (2 * m) / max(n * (n - 1), 1)
    c_random = p  # E[C_ER] = p
    l_random = math.log(n) / math.log(max(n * p, 2)) if p > 0 else float("inf")

    if c_random == 0 or l_random == 0 or l_actual == 0:
        sigma = 0.0
    else:
        gamma = c_actual / max(c_random, 1e-9)
        lam = l_actual / max(l_random, 1e-9)
        sigma = gamma / max(lam, 1e-9)

    return {
        "sigma": round(sigma, 4),
        "clustering_actual": round(c_actual, 4),
        "clustering_random": round(c_random, 4),
        "avg_path_length_actual": round(l_actual, 4),
        "avg_path_length_random": round(l_random, 4),
        "is_small_world": sigma > 1.0,
        "interpretation": (
            "Network exhibits small-world properties (high clustering, short paths)"
            if sigma > 1.0
            else "Network does not exhibit strong small-world properties"
        ),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Triad census (network motifs)
# ═══════════════════════════════════════════════════════════════════════════════

def triad_census(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    sample_size: int = 500,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Count triangle types (open vs closed triads) and compute
    the triad significance profile.

    In biology, closed triads (triangles) represent stable
    regulatory motifs; open triads indicate potential missing links.
    """
    adj = _adj(links)
    ids = _node_ids(nodes)
    n = len(ids)

    rng = random.Random(seed)
    sample_nodes = rng.sample(ids, min(sample_size, n))

    open_triads = 0
    closed_triads = 0
    triangle_nodes: Set[FrozenSet[str]] = set()

    for v in sample_nodes:
        nb_v = list(adj.get(v, set()))
        for i in range(len(nb_v)):
            for j in range(i + 1, len(nb_v)):
                u, w = nb_v[i], nb_v[j]
                if w in adj.get(u, set()):
                    # Closed triad (triangle)
                    closed_triads += 1
                    triangle_nodes.add(frozenset([v, u, w]))
                else:
                    # Open triad
                    open_triads += 1

    total = open_triads + closed_triads
    closure_rate = closed_triads / max(total, 1)

    return {
        "open_triads": open_triads,
        "closed_triads": closed_triads,
        "unique_triangles": len(triangle_nodes),
        "closure_rate": round(closure_rate, 4),
        "sample_size": len(sample_nodes),
        "interpretation": (
            f"{round(closure_rate * 100, 1)}% triadic closure — "
            f"{'high' if closure_rate > 0.3 else 'moderate' if closure_rate > 0.1 else 'low'} "
            f"pathway cross-talk"
        ),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Comprehensive analytics bundle
# ═══════════════════════════════════════════════════════════════════════════════

def full_analytics(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    include_centralities: bool = True,
    sample_betweenness: float = 0.3,
) -> Dict[str, Any]:
    """
    Run the full analytics pipeline and return a comprehensive report.
    ``sample_betweenness`` controls what fraction of nodes to use as
    sources in betweenness computation (set lower for large graphs).
    """
    result: Dict[str, Any] = {
        "node_count": len(nodes),
        "edge_count": len(links),
    }

    # Components
    result["components"] = connected_components(nodes, links)

    # Clustering
    result["clustering"] = clustering_coefficients(nodes, links)

    # Assortativity
    result["assortativity"] = degree_assortativity(nodes, links)

    # Small-world
    result["small_world"] = small_world_sigma(nodes, links)

    # Triad census
    result["triads"] = triad_census(nodes, links)

    # Rich-club
    result["rich_club"] = rich_club_coefficient(nodes, links)

    if include_centralities:
        # Degree
        dc = degree_centrality(nodes, links)
        top_dc = sorted(dc.items(), key=lambda x: x[1], reverse=True)[:15]
        result["top_degree_centrality"] = [
            {"node": n, "centrality": round(c, 4)} for n, c in top_dc
        ]

        # PageRank
        pr = pagerank(nodes, links)
        top_pr = sorted(pr.items(), key=lambda x: x[1], reverse=True)[:15]
        result["top_pagerank"] = [
            {"node": n, "pagerank": round(c, 6)} for n, c in top_pr
        ]

        # Betweenness (sampled for speed)
        bc = betweenness_centrality(nodes, links, sample_frac=sample_betweenness)
        top_bc = sorted(bc.items(), key=lambda x: x[1], reverse=True)[:15]
        result["top_betweenness"] = [
            {"node": n, "betweenness": round(c, 6)} for n, c in top_bc
        ]

        # Closeness
        cc = closeness_centrality(nodes, links)
        top_cc = sorted(cc.items(), key=lambda x: x[1], reverse=True)[:15]
        result["top_closeness"] = [
            {"node": n, "closeness": round(c, 4)} for n, c in top_cc
        ]

        # HITS
        h = hits(nodes, links)
        top_hubs = sorted(h["hubs"].items(), key=lambda x: x[1], reverse=True)[:10]
        top_auth = sorted(h["authorities"].items(), key=lambda x: x[1], reverse=True)[:10]
        result["top_hubs"] = [{"node": n, "hub_score": round(s, 6)} for n, s in top_hubs]
        result["top_authorities"] = [{"node": n, "authority_score": round(s, 6)} for n, s in top_auth]

    return result
