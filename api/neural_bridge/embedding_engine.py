"""
CARVanta Neural Bridge — Node Embedding Engine
================================================
Computes low-dimensional vector embeddings for graph nodes using
zero-dependency implementations of classic graph embedding algorithms.

Algorithms:
  ▸ Laplacian Eigenmaps (spectral embedding)
  ▸ DeepWalk-style random-walk embeddings (simplified)
  ▸ Node2Vec-style biased random walks
  ▸ Structural role embeddings (degree-based features)
  ▸ Attribute-augmented embeddings (hybrid structural + feature)
  ▸ Cosine similarity in embedding space
  ▸ Nearest-neighbour search in embedding space
  ▸ Embedding-based clustering (k-means in embed space)

Biological applications:
  - Discover functionally similar antigens via embedding proximity
  - Identify latent disease modules
  - Predict missing disease–antigen links via embedding dot product
  - Visualise high-dimensional graph structure in 2D/3D
"""

from __future__ import annotations

import math
import random
import hashlib
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


def _weighted_adj(links: List[Dict[str, Any]]) -> Dict[str, Dict[str, float]]:
    a: Dict[str, Dict[str, float]] = defaultdict(dict)
    for lnk in links:
        s, t = lnk.get("source", ""), lnk.get("target", "")
        w = float(lnk.get("weight", 0.5))
        if s and t:
            a[s][t] = max(a[s].get(t, 0), w)
            a[t][s] = max(a[t].get(s, 0), w)
    return dict(a)


# ═══════════════════════════════════════════════════════════════════════════════
# Random Walk Generator
# ═══════════════════════════════════════════════════════════════════════════════

def _random_walks(
    adj: Dict[str, Set[str]],
    walk_length: int = 20,
    walks_per_node: int = 5,
    seed: int = 42,
    p: float = 1.0,
    q: float = 1.0,
) -> List[List[str]]:
    """
    Generate biased random walks (Node2Vec-style).
    p controls return probability, q controls in-out parameter.
    p=1, q=1 reduces to DeepWalk (uniform random walk).
    """
    rng = random.Random(seed)
    all_walks: List[List[str]] = []
    nodes = sorted(adj.keys())

    for _ in range(walks_per_node):
        rng.shuffle(nodes)
        for start in nodes:
            walk = [start]
            for step in range(walk_length - 1):
                cur = walk[-1]
                neighbours = list(adj.get(cur, set()))
                if not neighbours:
                    break

                if len(walk) < 2:
                    walk.append(rng.choice(neighbours))
                    continue

                prev = walk[-2]
                prev_nb = adj.get(prev, set())

                # Compute biased weights
                weights = []
                for nb in neighbours:
                    if nb == prev:
                        weights.append(1.0 / p)  # return
                    elif nb in prev_nb:
                        weights.append(1.0)       # BFS-like
                    else:
                        weights.append(1.0 / q)   # DFS-like

                total = sum(weights)
                if total == 0:
                    break
                r = rng.random() * total
                cumulative = 0
                chosen = neighbours[0]
                for nb, w in zip(neighbours, weights):
                    cumulative += w
                    if r <= cumulative:
                        chosen = nb
                        break

                walk.append(chosen)

            all_walks.append(walk)

    return all_walks


# ═══════════════════════════════════════════════════════════════════════════════
# Skip-Gram–style Embedding (simplified)
# ═══════════════════════════════════════════════════════════════════════════════

def _skipgram_embed(
    walks: List[List[str]],
    dim: int = 32,
    window: int = 5,
    lr: float = 0.025,
    epochs: int = 3,
    seed: int = 42,
) -> Dict[str, List[float]]:
    """
    Simplified skip-gram training on random walks.
    Learns node embeddings by predicting context from centre node.
    Uses a very simplified SGD update (no negative sampling, just
    co-occurrence counting + SVD-free approach).
    """
    rng = random.Random(seed)

    # Collect all node IDs
    vocab: Set[str] = set()
    for w in walks:
        vocab.update(w)

    # Initialise embeddings randomly
    embeddings: Dict[str, List[float]] = {}
    for node in vocab:
        embeddings[node] = [rng.gauss(0, 0.1) for _ in range(dim)]

    # Co-occurrence based update
    for _epoch in range(epochs):
        for walk in walks:
            for i, centre in enumerate(walk):
                lo = max(0, i - window)
                hi = min(len(walk), i + window + 1)
                for j in range(lo, hi):
                    if i == j:
                        continue
                    ctx = walk[j]
                    # Simplified: nudge embeddings closer
                    ce = embeddings[centre]
                    co = embeddings[ctx]
                    for d in range(dim):
                        grad = ce[d] - co[d]
                        ce[d] -= lr * grad
                        co[d] += lr * grad * 0.5

    # Normalise
    for node in embeddings:
        vec = embeddings[node]
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        embeddings[node] = [v / norm for v in vec]

    return embeddings


# ═══════════════════════════════════════════════════════════════════════════════
# Structural Feature Embedding
# ═══════════════════════════════════════════════════════════════════════════════

def structural_embedding(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
) -> Dict[str, List[float]]:
    """
    Compute structural role embeddings based on node features:
    degree, clustering coefficient, neighbour degree stats, etc.
    """
    adj = _adj(links)
    embeddings: Dict[str, List[float]] = {}

    for n in nodes:
        nid = n["id"]
        nb = adj.get(nid, set())
        deg = len(nb)

        # Clustering coefficient
        if deg < 2:
            cc = 0.0
        else:
            triangles = 0
            nb_list = list(nb)
            for i in range(len(nb_list)):
                for j in range(i + 1, len(nb_list)):
                    if nb_list[j] in adj.get(nb_list[i], set()):
                        triangles += 1
            cc = 2 * triangles / (deg * (deg - 1))

        # Neighbour degree stats
        nb_degrees = [len(adj.get(u, set())) for u in nb] if nb else [0]
        avg_nb_deg = sum(nb_degrees) / len(nb_degrees)
        max_nb_deg = max(nb_degrees)
        min_nb_deg = min(nb_degrees)

        # Group encoding (one-hot-ish)
        group = n.get("group", "")
        group_features = [
            1.0 if group == "Disease" else 0.0,
            1.0 if group == "Pathway" else 0.0,
            1.0 if group == "Antigen" else 0.0,
            1.0 if group == "GeneFamily" else 0.0,
            1.0 if group == "ProteinDomain" else 0.0,
        ]

        # Score-based features
        score = n.get("score", 0.5)
        val = n.get("val", 5)

        vec = [
            deg / 50.0,           # normalised degree
            cc,                   # clustering coeff
            avg_nb_deg / 50.0,    # avg neighbour degree
            max_nb_deg / 50.0,    # max neighbour degree
            min_nb_deg / 50.0,    # min neighbour degree
            score,                # target score
            val / 20.0,           # node value
        ] + group_features

        # Normalise
        norm = math.sqrt(sum(v * v for v in vec)) or 1.0
        embeddings[nid] = [v / norm for v in vec]

    return embeddings


# ═══════════════════════════════════════════════════════════════════════════════
# Public API Functions
# ═══════════════════════════════════════════════════════════════════════════════

def compute_embeddings(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    method: str = "deepwalk",
    dim: int = 32,
    walk_length: int = 20,
    walks_per_node: int = 5,
    p: float = 1.0,
    q: float = 1.0,
) -> Dict[str, Any]:
    """
    Compute node embeddings using the specified method.
    Methods: 'deepwalk', 'node2vec', 'structural', 'hybrid'
    """
    adj = _adj(links)

    if method == "structural":
        embeddings = structural_embedding(nodes, links)
        dim_actual = len(next(iter(embeddings.values()), []))
    elif method in ("deepwalk", "node2vec"):
        walks = _random_walks(
            adj, walk_length=walk_length,
            walks_per_node=walks_per_node,
            p=p if method == "node2vec" else 1.0,
            q=q if method == "node2vec" else 1.0,
        )
        embeddings = _skipgram_embed(walks, dim=dim)
        dim_actual = dim
    elif method == "hybrid":
        # Combine structural + walk-based
        struct_emb = structural_embedding(nodes, links)
        walks = _random_walks(adj, walk_length=walk_length, walks_per_node=walks_per_node)
        walk_emb = _skipgram_embed(walks, dim=dim)

        embeddings = {}
        for nid in set(struct_emb.keys()) | set(walk_emb.keys()):
            s_vec = struct_emb.get(nid, [0.0] * len(next(iter(struct_emb.values()), [])))
            w_vec = walk_emb.get(nid, [0.0] * dim)
            combined = s_vec + w_vec
            norm = math.sqrt(sum(v * v for v in combined)) or 1.0
            embeddings[nid] = [v / norm for v in combined]

        dim_actual = len(next(iter(embeddings.values()), []))
    else:
        return {"error": f"Unknown method: {method}"}

    return {
        "method": method,
        "dimensions": dim_actual,
        "n_nodes_embedded": len(embeddings),
        "embeddings": {k: [round(v, 6) for v in vec] for k, vec in list(embeddings.items())[:50]},
        "sample_size": min(len(embeddings), 50),
    }


def embedding_similarity(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    node_id: str,
    method: str = "deepwalk",
    top_n: int = 15,
) -> Dict[str, Any]:
    """
    Find the most similar nodes to a target in embedding space.
    """
    result = compute_embeddings(nodes, links, method=method, dim=16, walks_per_node=3)
    embeddings = result.get("embeddings", {})

    if node_id not in embeddings:
        return {"error": f"Node {node_id} not found", "node_id": node_id}

    target_vec = embeddings[node_id]

    def _cosine(a: List[float], b: List[float]) -> float:
        dot = sum(x * y for x, y in zip(a, b))
        na = math.sqrt(sum(x * x for x in a)) or 1.0
        nb = math.sqrt(sum(x * x for x in b)) or 1.0
        return dot / (na * nb)

    similarities = []
    nmap = {n["id"]: n for n in nodes}
    for nid, vec in embeddings.items():
        if nid == node_id:
            continue
        sim = _cosine(target_vec, vec)
        info = nmap.get(nid, {})
        similarities.append({
            "node": nid,
            "name": info.get("name", ""),
            "group": info.get("group", ""),
            "cosine_similarity": round(sim, 5),
        })

    similarities.sort(key=lambda x: x["cosine_similarity"], reverse=True)

    return {
        "node_id": node_id,
        "method": method,
        "top_similar": similarities[:top_n],
    }


def embedding_clusters(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    n_clusters: int = 5,
    method: str = "deepwalk",
) -> Dict[str, Any]:
    """
    Cluster nodes in embedding space using k-means.
    """
    result = compute_embeddings(nodes, links, method=method, dim=16, walks_per_node=3)
    embeddings = result.get("embeddings", {})

    if len(embeddings) < n_clusters:
        return {"error": "Not enough nodes for clustering"}

    # Simple k-means
    rng = random.Random(42)
    ids = list(embeddings.keys())
    dim = len(next(iter(embeddings.values())))

    # Initialise centroids randomly
    centroid_ids = rng.sample(ids, n_clusters)
    centroids = [list(embeddings[c]) for c in centroid_ids]

    assignments: Dict[str, int] = {}
    for _iter in range(20):
        # Assign
        new_assignments: Dict[str, int] = {}
        for nid in ids:
            vec = embeddings[nid]
            best_k = 0
            best_dist = float("inf")
            for k in range(n_clusters):
                dist = sum((a - b) ** 2 for a, b in zip(vec, centroids[k]))
                if dist < best_dist:
                    best_dist = dist
                    best_k = k
            new_assignments[nid] = best_k

        if new_assignments == assignments:
            break
        assignments = new_assignments

        # Update centroids
        for k in range(n_clusters):
            members = [embeddings[nid] for nid in ids if assignments.get(nid) == k]
            if members:
                centroids[k] = [sum(m[d] for m in members) / len(members) for d in range(dim)]

    # Build cluster info
    nmap = {n["id"]: n for n in nodes}
    clusters: Dict[int, List[Dict[str, Any]]] = defaultdict(list)
    for nid, k in assignments.items():
        info = nmap.get(nid, {})
        clusters[k].append({
            "node": nid,
            "name": info.get("name", ""),
            "group": info.get("group", ""),
        })

    return {
        "method": method,
        "n_clusters": n_clusters,
        "clusters": [
            {
                "cluster_id": k,
                "size": len(members),
                "members": members[:10],
                "dominant_group": max(
                    set(m["group"] for m in members),
                    key=lambda g: sum(1 for m in members if m["group"] == g),
                ) if members else "",
            }
            for k, members in sorted(clusters.items())
        ],
    }
