"""
CARVanta Neural Bridge — Graph Motif & Sub-Structure Detection
===============================================================
Identifies recurring structural patterns (motifs) in the knowledge
graph that carry biological significance.

Motif types:
  ▸ Feed-forward loops (A→B→C, A→C)
  ▸ Bi-fan motifs (two regulators → two targets)
  ▸ Mutual regulation pairs
  ▸ Hub-spoke patterns
  ▸ Clique detection (k-cliques)
  ▸ Star subgraph identification
  ▸ Chain motifs (linear pathways)
  ▸ Diamond motifs (two shared intermediaries)

Network motifs serve as building blocks of complex biological
networks. Feed-forward loops represent coherent signalling;
bi-fans suggest co-regulation.
"""

from __future__ import annotations

import itertools
from collections import defaultdict
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple


# ═══════════════════════════════════════════════════════════════════════════════
# Adjacency helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _adj(links: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
    a: Dict[str, Set[str]] = defaultdict(set)
    for lnk in links:
        s, t = lnk.get("source", ""), lnk.get("target", "")
        if s and t:
            a[s].add(t)
            a[t].add(s)
    return dict(a)


def _directed_adj(links: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
    """Directed adjacency (source → targets only)."""
    a: Dict[str, Set[str]] = defaultdict(set)
    for lnk in links:
        s, t = lnk.get("source", ""), lnk.get("target", "")
        if s and t:
            a[s].add(t)
    return dict(a)


# ═══════════════════════════════════════════════════════════════════════════════
# Triangle / Clique Detection
# ═══════════════════════════════════════════════════════════════════════════════

def find_triangles(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    max_results: int = 50,
) -> Dict[str, Any]:
    """
    Find all triangles (3-cliques) in the graph.
    A triangle between A-B-C means all three are mutually connected,
    suggesting a tightly coupled functional module.
    """
    adj = _adj(links)
    triangles: List[Tuple[str, str, str]] = []
    seen: Set[FrozenSet[str]] = set()

    for u in adj:
        for v in adj[u]:
            if v <= u:
                continue
            for w in adj[u] & adj[v]:
                if w <= v:
                    continue
                tri = frozenset([u, v, w])
                if tri not in seen:
                    seen.add(tri)
                    triangles.append((u, v, w))
                    if len(triangles) >= max_results:
                        break
            if len(triangles) >= max_results:
                break
        if len(triangles) >= max_results:
            break

    nmap = {n["id"]: n for n in nodes}

    return {
        "total_triangles": len(triangles),
        "triangles": [
            {
                "nodes": [u, v, w],
                "names": [nmap.get(u, {}).get("name", ""), nmap.get(v, {}).get("name", ""), nmap.get(w, {}).get("name", "")],
                "groups": [nmap.get(u, {}).get("group", ""), nmap.get(v, {}).get("group", ""), nmap.get(w, {}).get("group", "")],
            }
            for u, v, w in triangles
        ],
    }


def find_cliques(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    min_size: int = 3,
    max_size: int = 6,
    max_results: int = 30,
) -> Dict[str, Any]:
    """
    Find cliques (fully connected subgraphs) of size k.
    Uses Bron–Kerbosch algorithm with pivot.
    """
    adj = _adj(links)
    all_cliques: List[List[str]] = []

    def _bron_kerbosch(R: Set[str], P: Set[str], X: Set[str]):
        if len(all_cliques) >= max_results:
            return
        if not P and not X:
            if min_size <= len(R) <= max_size:
                all_cliques.append(sorted(R))
            return

        # Choose pivot with max connections in P ∪ X
        pivot_candidates = P | X
        if not pivot_candidates:
            return
        pivot = max(pivot_candidates, key=lambda v: len(adj.get(v, set()) & P))

        for v in list(P - adj.get(pivot, set())):
            nb = adj.get(v, set())
            _bron_kerbosch(R | {v}, P & nb, X & nb)
            P.discard(v)
            X.add(v)

    vertices = set(adj.keys())
    _bron_kerbosch(set(), vertices, set())

    nmap = {n["id"]: n for n in nodes}
    return {
        "total_cliques": len(all_cliques),
        "cliques": [
            {
                "size": len(c),
                "nodes": c,
                "names": [nmap.get(v, {}).get("name", "") for v in c],
            }
            for c in sorted(all_cliques, key=len, reverse=True)
        ],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Feed-Forward Loop Detection
# ═══════════════════════════════════════════════════════════════════════════════

def find_feed_forward_loops(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    max_results: int = 40,
) -> Dict[str, Any]:
    """
    Find feed-forward loops: A→B, B→C, and A→C.
    In biology, FFLs filter noise and create delayed responses.
    """
    dadj = _directed_adj(links)
    nmap = {n["id"]: n for n in nodes}
    ffls: List[Dict[str, Any]] = []
    seen: Set[FrozenSet[str]] = set()

    for a in dadj:
        for b in dadj.get(a, set()):
            for c in dadj.get(b, set()):
                if c in dadj.get(a, set()):
                    key = frozenset([a, b, c])
                    if key not in seen:
                        seen.add(key)
                        ffls.append({
                            "regulator": a,
                            "intermediate": b,
                            "target": c,
                            "names": [
                                nmap.get(a, {}).get("name", ""),
                                nmap.get(b, {}).get("name", ""),
                                nmap.get(c, {}).get("name", ""),
                            ],
                        })
                        if len(ffls) >= max_results:
                            return {"total": len(ffls), "feed_forward_loops": ffls}

    return {"total": len(ffls), "feed_forward_loops": ffls}


# ═══════════════════════════════════════════════════════════════════════════════
# Hub-Spoke Pattern Detection
# ═══════════════════════════════════════════════════════════════════════════════

def find_hub_spokes(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    min_degree: int = 10,
    top_n: int = 20,
) -> Dict[str, Any]:
    """
    Find hub-spoke patterns: nodes with unusually high degree
    whose neighbours form a star topology.
    """
    adj = _adj(links)
    nmap = {n["id"]: n for n in nodes}

    hubs = []
    for nid in adj:
        nb = adj[nid]
        deg = len(nb)
        if deg < min_degree:
            continue

        # Check how sparsely the spokes are connected to each other
        spoke_edges = 0
        max_spoke_edges = deg * (deg - 1) / 2
        nb_list = list(nb)
        for i in range(min(len(nb_list), 30)):
            for j in range(i + 1, min(len(nb_list), 30)):
                if nb_list[j] in adj.get(nb_list[i], set()):
                    spoke_edges += 1

        spoke_density = spoke_edges / max(max_spoke_edges, 1)
        star_score = 1.0 - spoke_density  # Pure star has density 0

        info = nmap.get(nid, {})
        hubs.append({
            "hub_id": nid,
            "hub_name": info.get("name", ""),
            "group": info.get("group", ""),
            "degree": deg,
            "star_score": round(star_score, 3),
            "spoke_density": round(spoke_density, 3),
            "spoke_groups": _group_dist(nb, nmap),
        })

    hubs.sort(key=lambda x: x["degree"], reverse=True)
    return {"hub_spokes": hubs[:top_n]}


def _group_dist(nbs: Set[str], nmap: Dict) -> Dict[str, int]:
    d: Dict[str, int] = defaultdict(int)
    for n in nbs:
        d[nmap.get(n, {}).get("group", "Unknown")] += 1
    return dict(d)


# ═══════════════════════════════════════════════════════════════════════════════
# Diamond Motif Detection
# ═══════════════════════════════════════════════════════════════════════════════

def find_diamonds(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    max_results: int = 30,
) -> Dict[str, Any]:
    """
    Find diamond motifs: two nodes (A,B) connected via exactly
    two shared intermediaries (C,D).

    A — C — B
    A — D — B

    Diamonds indicate redundant pathways — biologically relevant
    for drug resistance.
    """
    adj = _adj(links)
    nmap = {n["id"]: n for n in nodes}
    diamonds: List[Dict[str, Any]] = []
    seen: Set[FrozenSet[str]] = set()

    id_list = list(adj.keys())

    for i in range(min(len(id_list), 200)):
        a = id_list[i]
        na = adj.get(a, set())
        for b in list(na)[:30]:
            nb = adj.get(b, set())
            # Shared neighbours (excluding a and b themselves)
            shared = (na & nb) - {a, b}
            if len(shared) >= 2:
                for c, d in itertools.combinations(list(shared)[:10], 2):
                    key = frozenset([a, b, c, d])
                    if key not in seen:
                        seen.add(key)
                        diamonds.append({
                            "endpoints": [a, b],
                            "intermediaries": [c, d],
                            "names": {
                                "endpoint_1": nmap.get(a, {}).get("name", ""),
                                "endpoint_2": nmap.get(b, {}).get("name", ""),
                                "intermediate_1": nmap.get(c, {}).get("name", ""),
                                "intermediate_2": nmap.get(d, {}).get("name", ""),
                            },
                        })
                        if len(diamonds) >= max_results:
                            return {"total": len(diamonds), "diamonds": diamonds}

    return {"total": len(diamonds), "diamonds": diamonds}


# ═══════════════════════════════════════════════════════════════════════════════
# Chain Motif (Linear Pathway) Detection
# ═══════════════════════════════════════════════════════════════════════════════

def find_chains(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    min_length: int = 4,
    max_length: int = 8,
    max_results: int = 20,
) -> Dict[str, Any]:
    """
    Find chain motifs: linear paths where each intermediate node
    has degree exactly 2 (forming a pipeline).

    Chains represent sequential signal cascades.
    """
    adj = _adj(links)
    nmap = {n["id"]: n for n in nodes}

    # Start from degree-2 nodes (chain interiors)
    chains: List[List[str]] = []
    visited_in_chains: Set[str] = set()

    for start in adj:
        if start in visited_in_chains:
            continue
        if len(adj[start]) != 2:
            continue

        # Walk both directions
        chain = [start]
        visited_in_chains.add(start)

        for direction in range(2):
            current = start
            nb = list(adj[start])
            next_node = nb[direction]

            while next_node not in visited_in_chains and len(chain) < max_length:
                chain.append(next_node) if direction == 1 else chain.insert(0, next_node)
                visited_in_chains.add(next_node)

                if len(adj.get(next_node, set())) != 2:
                    break

                neighbours = adj[next_node] - {current}
                if not neighbours:
                    break
                current = next_node
                next_node = list(neighbours)[0]

        if len(chain) >= min_length:
            chains.append(chain)
            if len(chains) >= max_results:
                break

    return {
        "total_chains": len(chains),
        "chains": [
            {
                "length": len(c),
                "path": c,
                "names": [nmap.get(v, {}).get("name", "") for v in c],
            }
            for c in chains
        ],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Full Motif Census
# ═══════════════════════════════════════════════════════════════════════════════

def motif_census(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
) -> Dict[str, Any]:
    """
    Run a full motif census across multiple pattern types.
    Returns counts and representative examples of each.
    """
    triangles = find_triangles(nodes, links, max_results=20)
    cliques = find_cliques(nodes, links, max_results=15)
    ffls = find_feed_forward_loops(nodes, links, max_results=15)
    hubs = find_hub_spokes(nodes, links, top_n=10)
    diamonds = find_diamonds(nodes, links, max_results=15)
    chains = find_chains(nodes, links, max_results=10)

    return {
        "summary": {
            "triangles": triangles["total_triangles"],
            "cliques": cliques["total_cliques"],
            "feed_forward_loops": ffls["total"],
            "hub_spokes": len(hubs["hub_spokes"]),
            "diamonds": diamonds["total"],
            "chains": chains["total_chains"],
        },
        "details": {
            "triangles": triangles,
            "cliques": cliques,
            "feed_forward_loops": ffls,
            "hub_spokes": hubs,
            "diamonds": diamonds,
            "chains": chains,
        },
    }
