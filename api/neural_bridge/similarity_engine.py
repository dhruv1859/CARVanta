"""
CARVanta Neural Bridge — Node Similarity & Recommendation Engine
=================================================================
Computes pairwise node similarity for the knowledge graph using
structural and attribute-based metrics, then produces ranked
recommendations of similar/related entities.

Similarity metrics:
  ▸ Cosine similarity on neighbourhood vectors
  ▸ Jaccard similarity on neighbour sets
  ▸ SimRank (iterative structural similarity)
  ▸ Role-based similarity (nodes in analogous positions)
  ▸ Attribute similarity (score, group, layer matching)
  ▸ Hybrid ensemble combining multiple signals

Use-cases:
  ▸ "Find antigens similar to CD19" — for backup-target discovery
  ▸ "Which diseases share targetable surface profiles?" — for
    indication expansion
  ▸ antigen-to-pathway recommendation for research prioritisation
"""

from __future__ import annotations

import math
import random
import statistics
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple


# ═══════════════════════════════════════════════════════════════════════════════
# Helpers
# ═══════════════════════════════════════════════════════════════════════════════

def _adj(links: List[Dict[str, Any]]) -> Dict[str, Set[str]]:
    a: Dict[str, Set[str]] = defaultdict(set)
    for lnk in links:
        s, t = lnk.get("source", ""), lnk.get("target", "")
        if s and t:
            a[s].add(t)
            a[t].add(s)
    return dict(a)


def _degree(adj: Dict[str, Set[str]], node: str) -> int:
    return len(adj.get(node, set()))


# ═══════════════════════════════════════════════════════════════════════════════
# Jaccard Neighbourhood Similarity
# ═══════════════════════════════════════════════════════════════════════════════

def jaccard_similarity(
    adj: Dict[str, Set[str]], u: str, v: str,
) -> float:
    """Jaccard index of the neighbour sets of u and v."""
    nu, nv = adj.get(u, set()), adj.get(v, set())
    if not nu and not nv:
        return 0.0
    inter = len(nu & nv)
    union = len(nu | nv)
    return inter / union if union else 0.0


def jaccard_similarity_matrix(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    node_ids: Optional[List[str]] = None,
) -> Dict[str, Dict[str, float]]:
    """
    Compute the pairwise Jaccard similarity for a set of nodes.
    Returns {u: {v: sim, ...}, ...}.
    """
    adj = _adj(links)
    ids = node_ids or [n["id"] for n in nodes]
    matrix: Dict[str, Dict[str, float]] = {}

    for i, u in enumerate(ids):
        matrix[u] = {}
        for j in range(i + 1, len(ids)):
            v = ids[j]
            sim = jaccard_similarity(adj, u, v)
            if sim > 0:
                matrix[u][v] = round(sim, 4)

    return matrix


# ═══════════════════════════════════════════════════════════════════════════════
# Cosine Neighbourhood Similarity
# ═══════════════════════════════════════════════════════════════════════════════

def cosine_similarity(
    adj: Dict[str, Set[str]],
    u: str,
    v: str,
    all_nodes: Set[str],
) -> float:
    """
    Cosine similarity of binary neighbourhood vectors.
    Each node is a dimension; 1 if neighbour, 0 otherwise.
    """
    nu = adj.get(u, set())
    nv = adj.get(v, set())
    dot = len(nu & nv)
    mag_u = math.sqrt(len(nu))
    mag_v = math.sqrt(len(nv))
    if mag_u == 0 or mag_v == 0:
        return 0.0
    return dot / (mag_u * mag_v)


# ═══════════════════════════════════════════════════════════════════════════════
# SimRank (Structural Similarity)
# ═══════════════════════════════════════════════════════════════════════════════

def simrank(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    decay: float = 0.8,
    max_iter: int = 5,
    threshold: float = 0.01,
) -> Dict[str, Dict[str, float]]:
    """
    SimRank: two nodes are similar if their neighbours are similar.

    S(a,b) = C / (|N(a)| * |N(b)|) * ΣΣ S(N_i(a), N_j(b))

    For scalability we only track pairs with sim > threshold.
    """
    adj = _adj(links)
    ids = [n["id"] for n in nodes]
    n = len(ids)

    # Initialise: S(a,a) = 1, S(a,b) = 0
    sim: Dict[Tuple[str, str], float] = {}
    for v in ids:
        sim[(v, v)] = 1.0

    for _it in range(max_iter):
        new_sim: Dict[Tuple[str, str], float] = {}
        for v in ids:
            new_sim[(v, v)] = 1.0

        for i in range(n):
            for j in range(i + 1, min(n, i + 200)):  # limit pairwise for speed
                a, b = ids[i], ids[j]
                na = list(adj.get(a, set()))
                nb = list(adj.get(b, set()))
                if not na or not nb:
                    continue

                total = 0.0
                for ni in na:
                    for nj in nb:
                        key = (ni, nj) if ni <= nj else (nj, ni)
                        total += sim.get(key, 0.0)

                s = (decay / (len(na) * len(nb))) * total
                if s > threshold:
                    key = (a, b) if a <= b else (b, a)
                    new_sim[key] = round(s, 4)

        sim = new_sim

    # Convert to nested dict
    result: Dict[str, Dict[str, float]] = defaultdict(dict)
    for (a, b), s in sim.items():
        if a != b and s > threshold:
            result[a][b] = s
            result[b][a] = s

    return dict(result)


# ═══════════════════════════════════════════════════════════════════════════════
# Attribute-Based Similarity
# ═══════════════════════════════════════════════════════════════════════════════

def attribute_similarity(
    node_a: Dict[str, Any],
    node_b: Dict[str, Any],
) -> float:
    """
    Attribute-based similarity combining:
      - Group match (0 or 0.3)
      - Layer match (0 or 0.2)
      - Score proximity (|s_a - s_b| inverted, 0–0.3)
      - Druggability match (0 or 0.1)
      - Gene family match (0 or 0.1)
    """
    score = 0.0

    if node_a.get("group") == node_b.get("group"):
        score += 0.3
    if node_a.get("layer") == node_b.get("layer"):
        score += 0.2

    sa = float(node_a.get("score", 0.5))
    sb = float(node_b.get("score", 0.5))
    score += 0.3 * (1.0 - abs(sa - sb))

    if node_a.get("druggability") == node_b.get("druggability"):
        score += 0.1
    if node_a.get("gene_family") == node_b.get("gene_family"):
        score += 0.1

    return round(min(score, 1.0), 4)


def attribute_similarity_batch(
    nodes: List[Dict[str, Any]],
    target_id: str,
    top_n: int = 20,
) -> List[Dict[str, Any]]:
    """Find the most attribute-similar nodes to a target."""
    nmap = {n["id"]: n for n in nodes}
    target = nmap.get(target_id)
    if not target:
        return []

    scored = []
    for n in nodes:
        if n["id"] == target_id:
            continue
        sim = attribute_similarity(target, n)
        if sim > 0.3:
            scored.append({
                "node_id": n["id"],
                "name": n.get("name", ""),
                "group": n.get("group", ""),
                "similarity": sim,
            })

    scored.sort(key=lambda x: x["similarity"], reverse=True)
    return scored[:top_n]


# ═══════════════════════════════════════════════════════════════════════════════
# Role-Based Similarity (Structural Equivalence)
# ═══════════════════════════════════════════════════════════════════════════════

def role_similarity(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    target_id: str,
    top_n: int = 20,
) -> List[Dict[str, Any]]:
    """
    Find nodes in analogous structural positions (similar degree,
    betweenness-like profile, and neighbour-group distribution).

    Two antigens that both connect to exactly 3 diseases and 2 pathways
    occupy the same "role" even if they share no direct neighbours.
    """
    adj = _adj(links)
    ids = [n["id"] for n in nodes]
    nmap = {n["id"]: n for n in nodes}

    target = nmap.get(target_id)
    if not target:
        return []

    def _role_vector(nid: str) -> Tuple[int, Dict[str, int], Dict[str, int]]:
        nb = adj.get(nid, set())
        deg = len(nb)
        group_dist: Dict[str, int] = defaultdict(int)
        layer_dist: Dict[str, int] = defaultdict(int)
        for n in nb:
            info = nmap.get(n, {})
            group_dist[info.get("group", "U")] += 1
            layer_dist[info.get("layer", "u")] += 1
        return deg, dict(group_dist), dict(layer_dist)

    target_deg, target_gd, target_ld = _role_vector(target_id)

    def _role_distance(nid: str) -> float:
        d, gd, ld = _role_vector(nid)
        deg_diff = abs(d - target_deg) / max(target_deg, 1)
        # Group distribution cosine
        all_groups = set(target_gd) | set(gd)
        dot = sum(target_gd.get(g, 0) * gd.get(g, 0) for g in all_groups)
        mag_a = math.sqrt(sum(v ** 2 for v in target_gd.values())) or 1
        mag_b = math.sqrt(sum(v ** 2 for v in gd.values())) or 1
        cos_g = dot / (mag_a * mag_b) if mag_a and mag_b else 0
        return deg_diff * 0.3 + (1 - cos_g) * 0.7

    scored = []
    for nid in ids:
        if nid == target_id:
            continue
        dist = _role_distance(nid)
        sim = max(0, 1.0 - dist)
        if sim > 0.2:
            scored.append({
                "node_id": nid,
                "name": nmap.get(nid, {}).get("name", ""),
                "group": nmap.get(nid, {}).get("group", ""),
                "role_similarity": round(sim, 4),
            })

    scored.sort(key=lambda x: x["role_similarity"], reverse=True)
    return scored[:top_n]


# ═══════════════════════════════════════════════════════════════════════════════
# Hybrid Ensemble Recommendation
# ═══════════════════════════════════════════════════════════════════════════════

def recommend_similar(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    target_id: str,
    top_n: int = 15,
    weights: Optional[Dict[str, float]] = None,
) -> Dict[str, Any]:
    """
    Ensemble recommendation combining:
      - Jaccard neighbourhood similarity (structural)
      - Attribute similarity (feature-based)
      - Role similarity (positional)

    Returns a ranked list of recommended nodes with per-signal scores.
    """
    if weights is None:
        weights = {"jaccard": 0.4, "attribute": 0.35, "role": 0.25}

    adj = _adj(links)
    nmap = {n["id"]: n for n in nodes}
    target = nmap.get(target_id)
    if not target:
        return {"error": f"Node '{target_id}' not found", "recommendations": []}

    ids = [n["id"] for n in nodes if n["id"] != target_id]

    # Compute signals
    all_nodes_set = set(nmap.keys())
    scores: Dict[str, Dict[str, float]] = {}

    for nid in ids:
        j = jaccard_similarity(adj, target_id, nid)
        a = attribute_similarity(target, nmap[nid])
        c = cosine_similarity(adj, target_id, nid, all_nodes_set)

        ensemble = (
            weights["jaccard"] * j +
            weights["attribute"] * a +
            weights.get("role", 0.25) * c  # use cosine as proxy for role
        )

        if ensemble > 0.05:
            scores[nid] = {
                "jaccard": round(j, 4),
                "attribute": round(a, 4),
                "cosine": round(c, 4),
                "ensemble": round(ensemble, 4),
            }

    # Rank by ensemble
    ranked = sorted(scores.items(), key=lambda x: x[1]["ensemble"], reverse=True)[:top_n]

    recommendations = []
    for nid, sigs in ranked:
        info = nmap.get(nid, {})
        recommendations.append({
            "node_id": nid,
            "name": info.get("name", ""),
            "group": info.get("group", ""),
            "layer": info.get("layer", ""),
            "score": info.get("score"),
            "signals": sigs,
        })

    return {
        "target": {
            "node_id": target_id,
            "name": target.get("name", ""),
            "group": target.get("group", ""),
        },
        "recommendations": recommendations,
        "method": "ensemble (Jaccard + Attribute + Cosine)",
        "weights": weights,
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Indication Expansion
# ═══════════════════════════════════════════════════════════════════════════════

def suggest_indication_expansion(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    antigen_id: str,
    top_n: int = 10,
) -> Dict[str, Any]:
    """
    Given an antigen, suggest diseases it might be repurposed for
    based on structural similarity to antigens already targeting
    those diseases.

    This is the graph-based version of "indication expansion" —
    a key drug-discovery concept.
    """
    adj = _adj(links)
    nmap = {n["id"]: n for n in nodes}

    if antigen_id not in nmap:
        return {"error": f"Antigen '{antigen_id}' not found"}

    # Find diseases already connected to this antigen
    current_diseases = {
        nb for nb in adj.get(antigen_id, set())
        if nmap.get(nb, {}).get("group") == "Disease"
    }

    # For each unconnected disease, compute a "repurposing score"
    all_diseases = [
        n["id"] for n in nodes
        if n.get("group") == "Disease" and n["id"] not in current_diseases
    ]

    suggestions = []
    for did in all_diseases:
        # How many antigens targeting this disease are similar to ours?
        disease_antigens = {
            nb for nb in adj.get(did, set())
            if nmap.get(nb, {}).get("group") == "Antigen"
        }

        if not disease_antigens:
            continue

        # Average Jaccard similarity to those disease-antigens
        sims = [jaccard_similarity(adj, antigen_id, da) for da in disease_antigens]
        avg_sim = statistics.mean(sims) if sims else 0
        max_sim = max(sims) if sims else 0
        n_similar = sum(1 for s in sims if s > 0.1)

        repurpose_score = (
            0.4 * avg_sim +
            0.3 * max_sim +
            0.3 * min(n_similar / 5, 1.0)
        )

        if repurpose_score > 0.05:
            suggestions.append({
                "disease_id": did,
                "disease_name": nmap.get(did, {}).get("name", ""),
                "repurpose_score": round(repurpose_score, 4),
                "avg_similarity": round(avg_sim, 4),
                "max_similarity": round(max_sim, 4),
                "n_similar_antigens": n_similar,
                "total_disease_antigens": len(disease_antigens),
            })

    suggestions.sort(key=lambda x: x["repurpose_score"], reverse=True)

    return {
        "antigen_id": antigen_id,
        "antigen_name": nmap.get(antigen_id, {}).get("name", ""),
        "current_diseases": [
            {"id": d, "name": nmap.get(d, {}).get("name", "")}
            for d in current_diseases
        ],
        "expansion_suggestions": suggestions[:top_n],
    }
