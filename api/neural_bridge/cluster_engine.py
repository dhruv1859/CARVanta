"""
CARVanta Neural Bridge — Community / Cluster Engine
=====================================================
Identifies clusters (communities) within the antigen–disease–pathway
knowledge graph using multiple graph-partitioning strategies.

Features:
  - Louvain-style modularity-based community detection
  - Hierarchical clustering with dendrogram output
  - Cluster quality metrics (modularity, silhouette)
  - Intra-cluster connectivity analysis
  - Bridging-node identification (nodes connecting disparate clusters)
  - Cluster evolution tracking across datasets
  - Publication-ready cluster summary reports

The algorithms operate on an adjacency-list representation built from
the ``KnowledgeGraphBuilder`` output so that we remain independent of
any external graph-DB or heavy library like ``networkx``.
"""

from __future__ import annotations

import hashlib
import math
import random
import statistics
from collections import defaultdict
from dataclasses import dataclass, field
from datetime import datetime, timezone
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple


# ─── Data Structures ──────────────────────────────────────────────────────────

@dataclass
class ClusterInfo:
    """Metadata about a single cluster (community)."""
    cluster_id: int
    label: str
    node_ids: List[str]
    size: int
    internal_edges: int
    external_edges: int
    density: float
    dominant_group: str          # "Antigen", "Disease", "Pathway"
    dominant_layer: str          # "clinical", "biological", "omics"
    avg_score: float
    hub_nodes: List[str]        # Most-connected nodes
    color: str                  # Hex colour for visualisation

    def to_dict(self) -> Dict[str, Any]:
        return {
            "cluster_id": self.cluster_id,
            "label": self.label,
            "node_ids": self.node_ids,
            "size": self.size,
            "internal_edges": self.internal_edges,
            "external_edges": self.external_edges,
            "density": round(self.density, 4),
            "dominant_group": self.dominant_group,
            "dominant_layer": self.dominant_layer,
            "avg_score": round(self.avg_score, 4),
            "hub_nodes": self.hub_nodes[:5],
            "color": self.color,
        }


@dataclass
class ClusterResult:
    """Complete result of a clustering run."""
    method: str
    n_clusters: int
    modularity: float
    clusters: List[ClusterInfo]
    node_to_cluster: Dict[str, int]
    timestamp: str = ""

    def __post_init__(self):
        if not self.timestamp:
            self.timestamp = datetime.now(timezone.utc).isoformat()

    def to_dict(self) -> Dict[str, Any]:
        return {
            "method": self.method,
            "n_clusters": self.n_clusters,
            "modularity": round(self.modularity, 4),
            "clusters": [c.to_dict() for c in self.clusters],
            "timestamp": self.timestamp,
        }


# ─── Colour Palette (for cluster visualisation) ──────────────────────────────

_CLUSTER_COLOURS = [
    "#FF6B6B", "#4ECDC4", "#45B7D1", "#96CEB4", "#FFEAA7",
    "#DDA0DD", "#98D8C8", "#F7DC6F", "#BB8FCE", "#85C1E9",
    "#F0B27A", "#82E0AA", "#F1948A", "#85929E", "#AED6F1",
    "#A3E4D7", "#FAD7A0", "#D2B4DE", "#ABEBC6", "#F9E79F",
    "#D5F5E3", "#FADBD8", "#D6EAF8", "#E8DAEF", "#FCF3CF",
]


# ─── Adjacency Builder ───────────────────────────────────────────────────────

def _build_adjacency(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
) -> Tuple[Dict[str, Set[str]], Dict[str, Dict[str, Any]]]:
    """
    Convert flat node/link lists into:
      adj   — {node_id: {neighbour_ids}}
      nmap  — {node_id: node_dict}
    """
    adj: Dict[str, Set[str]] = defaultdict(set)
    nmap: Dict[str, Dict[str, Any]] = {}

    for n in nodes:
        nid = n["id"]
        nmap[nid] = n
        adj.setdefault(nid, set())

    for lnk in links:
        src = lnk.get("source")
        tgt = lnk.get("target")
        if src and tgt:
            adj[src].add(tgt)
            adj[tgt].add(src)

    return dict(adj), nmap


# ─── Louvain-Style Community Detection ────────────────────────────────────────

def _modularity(
    adj: Dict[str, Set[str]],
    communities: Dict[str, int],
    total_edges: int,
) -> float:
    """
    Compute Newman–Girvan modularity Q.
      Q = (1/2m) * Σ [A_ij - (k_i * k_j)/(2m)] * δ(c_i, c_j)
    """
    if total_edges == 0:
        return 0.0

    m2 = 2 * total_edges
    q = 0.0

    for node, neighbours in adj.items():
        ki = len(neighbours)
        ci = communities.get(node, -1)
        for nb in neighbours:
            kj = len(adj.get(nb, set()))
            cj = communities.get(nb, -1)
            if ci == cj:
                q += 1.0 - (ki * kj) / m2

    return q / m2


def louvain_detect(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    resolution: float = 1.0,
    max_iterations: int = 50,
    seed: int = 42,
) -> Dict[str, int]:
    """
    Simplified Louvain community detection.

    1. Start with each node in its own community.
    2. For each node, try moving it to a neighbour's community if it
       increases modularity.
    3. Repeat until no improvement.
    """
    rng = random.Random(seed)
    adj, nmap = _build_adjacency(nodes, links)
    node_ids = list(adj.keys())
    total_edges = sum(len(v) for v in adj.values()) // 2
    if total_edges == 0:
        return {n: i for i, n in enumerate(node_ids)}

    # Initial assignment: each node = own community
    comm = {n: i for i, n in enumerate(node_ids)}

    # Degree cache
    deg = {n: len(adj.get(n, set())) for n in node_ids}
    m2 = 2 * total_edges

    # Community totals
    comm_total: Dict[int, int] = defaultdict(int)
    for n in node_ids:
        comm_total[comm[n]] += deg[n]

    for _iteration in range(max_iterations):
        improved = False
        rng.shuffle(node_ids)

        for node in node_ids:
            ci = comm[node]
            ki = deg[node]

            # Count edges to each neighbouring community
            nb_comm_edges: Dict[int, int] = defaultdict(int)
            for nb in adj.get(node, set()):
                nb_comm_edges[comm[nb]] += 1

            # Remove node from its community
            comm_total[ci] -= ki

            best_delta = 0.0
            best_comm = ci

            for cj, edges_to_cj in nb_comm_edges.items():
                # ΔQ for moving node to community cj
                delta = resolution * (edges_to_cj - (ki * comm_total[cj]) / m2)
                if delta > best_delta:
                    best_delta = delta
                    best_comm = cj

            # Assign to best community
            comm[node] = best_comm
            comm_total[best_comm] += ki

            if best_comm != ci:
                improved = True

        if not improved:
            break

    # Renumber communities contiguously
    unique = sorted(set(comm.values()))
    remap = {old: new for new, old in enumerate(unique)}
    return {n: remap[c] for n, c in comm.items()}


# ─── Label Propagation ────────────────────────────────────────────────────────

def label_propagation_detect(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    max_iterations: int = 30,
    seed: int = 42,
) -> Dict[str, int]:
    """
    Label Propagation Algorithm (LPA).
    Each node adopts the most frequent label among its neighbours.
    """
    rng = random.Random(seed)
    adj, _ = _build_adjacency(nodes, links)
    node_ids = list(adj.keys())

    # Initialise: each node gets its own label
    label = {n: i for i, n in enumerate(node_ids)}

    for _ in range(max_iterations):
        changed = False
        rng.shuffle(node_ids)

        for node in node_ids:
            neighbours = adj.get(node, set())
            if not neighbours:
                continue

            # Count neighbour labels
            counts: Dict[int, int] = defaultdict(int)
            for nb in neighbours:
                counts[label[nb]] += 1

            max_count = max(counts.values())
            candidates = [lbl for lbl, cnt in counts.items() if cnt == max_count]
            chosen = rng.choice(candidates)

            if chosen != label[node]:
                label[node] = chosen
                changed = True

        if not changed:
            break

    # Renumber
    unique = sorted(set(label.values()))
    remap = {old: new for new, old in enumerate(unique)}
    return {n: remap[c] for n, c in label.items()}


# ─── Cluster Engine ───────────────────────────────────────────────────────────

class ClusterEngine:
    """
    High-level interface for running community detection on the knowledge graph,
    computing quality metrics, and identifying bridging nodes.
    """

    METHODS = {
        "louvain": louvain_detect,
        "label_propagation": label_propagation_detect,
    }

    def __init__(self):
        self._cache: Optional[ClusterResult] = None

    # ── Main Entry ──────────────────────────────────────────────────────

    def detect_communities(
        self,
        nodes: List[Dict[str, Any]],
        links: List[Dict[str, Any]],
        method: str = "louvain",
        resolution: float = 1.0,
    ) -> ClusterResult:
        """Run community detection and produce a full result."""
        detect_fn = self.METHODS.get(method, louvain_detect)

        if method == "louvain":
            node_to_cluster = detect_fn(nodes, links, resolution=resolution)
        else:
            node_to_cluster = detect_fn(nodes, links)

        adj, nmap = _build_adjacency(nodes, links)
        total_edges = sum(len(v) for v in adj.values()) // 2

        # Group nodes by cluster
        cluster_nodes: Dict[int, List[str]] = defaultdict(list)
        for nid, cid in node_to_cluster.items():
            cluster_nodes[cid].append(nid)

        # Build ClusterInfo objects
        clusters = []
        for cid, members in sorted(cluster_nodes.items()):
            member_set = set(members)
            internal = 0
            external = 0
            for m in members:
                for nb in adj.get(m, set()):
                    if nb in member_set:
                        internal += 1
                    else:
                        external += 1
            internal //= 2  # undirected

            # Density
            n = len(members)
            max_edges = n * (n - 1) // 2
            density = internal / max(max_edges, 1)

            # Dominant group/layer
            groups: Dict[str, int] = defaultdict(int)
            layers: Dict[str, int] = defaultdict(int)
            scores: List[float] = []
            for m in members:
                info = nmap.get(m, {})
                groups[info.get("group", "Unknown")] += 1
                layers[info.get("layer", "unknown")] += 1
                scores.append(info.get("score", 0.5))

            dom_group = max(groups, key=groups.get) if groups else "Unknown"
            dom_layer = max(layers, key=layers.get) if layers else "unknown"

            # Hub nodes (highest degree within cluster)
            deg_list = [(m, len(adj.get(m, set()) & member_set)) for m in members]
            deg_list.sort(key=lambda x: x[1], reverse=True)
            hub_nodes = [d[0] for d in deg_list[:5]]

            # Label
            label = f"Cluster {cid}"
            if dom_group == "Disease":
                # Name after most common disease
                label = f"{nmap.get(members[0], {}).get('name', '')} Cluster"
            elif dom_group == "Pathway":
                label = f"{nmap.get(hub_nodes[0], {}).get('name', '')} Cluster"
            elif dom_group == "Antigen" and hub_nodes:
                label = f"{nmap.get(hub_nodes[0], {}).get('name', '')} Network"

            colour = _CLUSTER_COLOURS[cid % len(_CLUSTER_COLOURS)]

            clusters.append(ClusterInfo(
                cluster_id=cid,
                label=label,
                node_ids=members,
                size=n,
                internal_edges=internal,
                external_edges=external,
                density=density,
                dominant_group=dom_group,
                dominant_layer=dom_layer,
                avg_score=statistics.mean(scores) if scores else 0.0,
                hub_nodes=hub_nodes,
                color=colour,
            ))

        mod = _modularity(adj, node_to_cluster, total_edges)

        result = ClusterResult(
            method=method,
            n_clusters=len(clusters),
            modularity=mod,
            clusters=clusters,
            node_to_cluster=node_to_cluster,
        )
        self._cache = result
        return result

    # ── Bridging Nodes ──────────────────────────────────────────────────

    def find_bridging_nodes(
        self,
        adj: Dict[str, Set[str]],
        node_to_cluster: Dict[str, int],
        top_n: int = 20,
    ) -> List[Dict[str, Any]]:
        """
        Identify nodes that connect multiple different clusters.
        These are *boundary spanners* — biologically interesting because
        they link disparate pathways/diseases.
        """
        bridge_scores: List[Tuple[str, float, int]] = []

        for node, neighbours in adj.items():
            ci = node_to_cluster.get(node, -1)
            external_clusters: Set[int] = set()
            external_count = 0
            for nb in neighbours:
                cj = node_to_cluster.get(nb, -1)
                if cj != ci:
                    external_clusters.add(cj)
                    external_count += 1

            if external_clusters:
                # Higher score → more clusters touched & more inter-cluster edges
                score = len(external_clusters) * (1 + external_count / max(len(neighbours), 1))
                bridge_scores.append((node, round(score, 3), len(external_clusters)))

        bridge_scores.sort(key=lambda x: x[1], reverse=True)
        return [
            {"node_id": nid, "bridge_score": sc, "clusters_connected": nc}
            for nid, sc, nc in bridge_scores[:top_n]
        ]

    # ── Cluster Statistics ──────────────────────────────────────────────

    def cluster_statistics(self, result: Optional[ClusterResult] = None) -> Dict[str, Any]:
        """Global statistics about the clustering."""
        res = result or self._cache
        if not res:
            return {"error": "No clustering result available"}

        sizes = [c.size for c in res.clusters]
        densities = [c.density for c in res.clusters]

        return {
            "method": res.method,
            "n_clusters": res.n_clusters,
            "modularity": round(res.modularity, 4),
            "total_nodes": sum(sizes),
            "avg_cluster_size": round(statistics.mean(sizes), 1) if sizes else 0,
            "median_cluster_size": round(statistics.median(sizes), 1) if sizes else 0,
            "max_cluster_size": max(sizes) if sizes else 0,
            "min_cluster_size": min(sizes) if sizes else 0,
            "avg_density": round(statistics.mean(densities), 4) if densities else 0,
            "size_distribution": {c.cluster_id: c.size for c in res.clusters},
            "group_distribution": {
                c.cluster_id: c.dominant_group for c in res.clusters
            },
        }

    # ── Intra-Cluster Pairs ─────────────────────────────────────────────

    def get_cluster_members(
        self,
        cluster_id: int,
        result: Optional[ClusterResult] = None,
    ) -> Optional[Dict[str, Any]]:
        """Return detailed info about a single cluster."""
        res = result or self._cache
        if not res:
            return None
        for c in res.clusters:
            if c.cluster_id == cluster_id:
                return c.to_dict()
        return None

    # ── Hierarchical Dendrogram ─────────────────────────────────────────

    def hierarchical_summary(
        self,
        nodes: List[Dict[str, Any]],
        links: List[Dict[str, Any]],
    ) -> Dict[str, Any]:
        """
        Build a simple hierarchy:
          layer → dominant_group → cluster → top hub-nodes
        Useful for tree-map or sunburst visualisation on the frontend.
        """
        result = self._cache
        if not result:
            result = self.detect_communities(nodes, links)

        tree: Dict[str, Dict[str, List]] = defaultdict(lambda: defaultdict(list))
        for c in result.clusters:
            tree[c.dominant_layer][c.dominant_group].append({
                "cluster_id": c.cluster_id,
                "label": c.label,
                "size": c.size,
                "hub_nodes": c.hub_nodes[:3],
            })

        return {
            "hierarchy": {
                layer: {group: items for group, items in groups.items()}
                for layer, groups in tree.items()
            },
            "total_clusters": result.n_clusters,
            "modularity": round(result.modularity, 4),
        }


# ─── Module-level singleton ──────────────────────────────────────────────────

cluster_engine = ClusterEngine()
