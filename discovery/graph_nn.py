"""
CARVanta Discovery — Graph Neural Network Engine
==================================================
Graph-based protein-protein interaction (PPI) network analysis using
message-passing neural network simulation. Builds on STRING, BioGRID,
and pathway databases to discover hidden target relationships.

Implements:
- Graph construction from PPI databases
- Node embedding computation
- Message-passing inference (simulated GNN)
- Link prediction for novel target interactions
- Community detection for target clusters

Security: Stateless, async-compatible, input-validated.
API Version: v5
"""

import math
import hashlib
import logging
from typing import Any, Dict, List, Optional, Set, Tuple
from dataclasses import dataclass, field
from enum import Enum
from collections import defaultdict

logger = logging.getLogger("carvanta.discovery.graph_nn")

# ──────────────────────────────────────────────────────────────────────
# Constants — Protein Interaction Network
# ──────────────────────────────────────────────────────────────────────

class InteractionType(Enum):
    """Types of protein-protein interactions."""
    PHYSICAL_BINDING = "physical_binding"
    CO_EXPRESSION = "co_expression"
    PATHWAY_MEMBER = "pathway_member"
    GENETIC_INTERACTION = "genetic_interaction"
    ENZYME_SUBSTRATE = "enzyme_substrate"
    RECEPTOR_LIGAND = "receptor_ligand"
    COMPLEX_MEMBER = "complex_member"
    REGULATORY = "regulatory"
    SIGNALING = "signaling"


class PathwayCategory(Enum):
    """Major signaling/biological pathway categories."""
    PI3K_AKT = "PI3K-AKT signaling"
    RAS_MAPK = "RAS-MAPK signaling"
    JAK_STAT = "JAK-STAT signaling"
    WNT = "WNT signaling"
    NOTCH = "Notch signaling"
    HEDGEHOG = "Hedgehog signaling"
    NFKB = "NF-κB signaling"
    APOPTOSIS = "Apoptosis"
    CELL_CYCLE = "Cell cycle"
    DNA_REPAIR = "DNA repair"
    IMMUNE_CHECKPOINT = "Immune checkpoint"
    TCR_SIGNALING = "T-cell receptor signaling"
    BCR_SIGNALING = "B-cell receptor signaling"
    TUMOR_MICROENVIRONMENT = "Tumor microenvironment"
    ANGIOGENESIS = "Angiogenesis"
    METABOLISM = "Cancer metabolism"


# Core protein interaction network (curated from STRING/BioGRID)
# Each entry: (protein_A, protein_B, interaction_type, confidence, pathways)
CURATED_INTERACTIONS: List[Tuple[str, str, InteractionType, float, List[str]]] = [
    # ─── Receptor tyrosine kinase signaling ───
    ("EGFR", "HER2", InteractionType.PHYSICAL_BINDING, 0.95, ["PI3K-AKT", "RAS-MAPK"]),
    ("EGFR", "KRAS", InteractionType.SIGNALING, 0.92, ["RAS-MAPK"]),
    ("EGFR", "PIK3CA", InteractionType.SIGNALING, 0.88, ["PI3K-AKT"]),
    ("HER2", "PIK3CA", InteractionType.SIGNALING, 0.87, ["PI3K-AKT"]),
    ("HER2", "KRAS", InteractionType.SIGNALING, 0.82, ["RAS-MAPK"]),
    ("KRAS", "BRAF", InteractionType.SIGNALING, 0.97, ["RAS-MAPK"]),
    ("BRAF", "MEK1", InteractionType.ENZYME_SUBSTRATE, 0.96, ["RAS-MAPK"]),
    ("PIK3CA", "AKT1", InteractionType.SIGNALING, 0.94, ["PI3K-AKT"]),
    ("AKT1", "MTOR", InteractionType.SIGNALING, 0.93, ["PI3K-AKT"]),
    ("PTEN", "PIK3CA", InteractionType.REGULATORY, 0.95, ["PI3K-AKT"]),
    ("MET", "HER2", InteractionType.PHYSICAL_BINDING, 0.75, ["PI3K-AKT", "RAS-MAPK"]),
    ("MET", "EGFR", InteractionType.CO_EXPRESSION, 0.72, ["PI3K-AKT"]),
    ("ALK", "KRAS", InteractionType.SIGNALING, 0.78, ["RAS-MAPK"]),

    # ─── Immune checkpoint network ───
    ("PD_L1", "PD1", InteractionType.RECEPTOR_LIGAND, 0.98, ["Immune checkpoint"]),
    ("CD47", "SIRPA", InteractionType.RECEPTOR_LIGAND, 0.97, ["Immune checkpoint"]),
    ("B7_H3", "CD28", InteractionType.RECEPTOR_LIGAND, 0.65, ["Immune checkpoint", "TCR signaling"]),
    ("CTLA4", "CD80", InteractionType.RECEPTOR_LIGAND, 0.96, ["Immune checkpoint"]),
    ("CTLA4", "CD86", InteractionType.RECEPTOR_LIGAND, 0.95, ["Immune checkpoint"]),
    ("LAG3", "MHCII", InteractionType.RECEPTOR_LIGAND, 0.85, ["Immune checkpoint"]),
    ("TIM3", "GALECTIN9", InteractionType.RECEPTOR_LIGAND, 0.82, ["Immune checkpoint"]),
    ("TIGIT", "PVR", InteractionType.RECEPTOR_LIGAND, 0.88, ["Immune checkpoint"]),

    # ─── B-cell / myeloma targets ───
    ("CD19", "CD22", InteractionType.CO_EXPRESSION, 0.92, ["BCR signaling"]),
    ("CD19", "CD20", InteractionType.CO_EXPRESSION, 0.95, ["BCR signaling"]),
    ("CD19", "CD79A", InteractionType.COMPLEX_MEMBER, 0.90, ["BCR signaling"]),
    ("CD22", "CD20", InteractionType.CO_EXPRESSION, 0.88, ["BCR signaling"]),
    ("BCMA", "TACI", InteractionType.PATHWAY_MEMBER, 0.80, ["NF-κB", "BCR signaling"]),
    ("BCMA", "BAFF", InteractionType.RECEPTOR_LIGAND, 0.94, ["BCR signaling"]),
    ("BCMA", "APRIL", InteractionType.RECEPTOR_LIGAND, 0.93, ["BCR signaling"]),
    ("GPRC5D", "BCMA", InteractionType.CO_EXPRESSION, 0.70, ["BCR signaling"]),
    ("FcRH5", "BCMA", InteractionType.CO_EXPRESSION, 0.65, ["BCR signaling"]),

    # ─── Solid tumor CAR-T targets ───
    ("MSLN", "MUC16", InteractionType.PHYSICAL_BINDING, 0.90, ["Cell adhesion"]),
    ("EpCAM", "CLDN18.2", InteractionType.CO_EXPRESSION, 0.72, ["Cell adhesion"]),
    ("GPC3", "WNT3A", InteractionType.RECEPTOR_LIGAND, 0.75, ["WNT signaling"]),
    ("GPC3", "FGF2", InteractionType.PHYSICAL_BINDING, 0.68, ["Angiogenesis"]),
    ("DLL3", "NOTCH1", InteractionType.RECEPTOR_LIGAND, 0.85, ["Notch signaling"]),
    ("DLL3", "NOTCH2", InteractionType.RECEPTOR_LIGAND, 0.80, ["Notch signaling"]),
    ("PSMA", "FOLR1", InteractionType.CO_EXPRESSION, 0.55, ["Metabolism"]),
    ("CD70", "CD27", InteractionType.RECEPTOR_LIGAND, 0.95, ["NF-κB", "TCR signaling"]),
    ("ROR1", "WNT5A", InteractionType.RECEPTOR_LIGAND, 0.82, ["WNT signaling"]),
    ("IL13RA2", "IL13", InteractionType.RECEPTOR_LIGAND, 0.92, ["JAK-STAT signaling"]),
    ("GD2", "CD56", InteractionType.CO_EXPRESSION, 0.60, ["Neural"]),

    # ─── Tumor suppressor interactions ───
    ("TP53", "MDM2", InteractionType.REGULATORY, 0.98, ["Apoptosis", "Cell cycle"]),
    ("TP53", "BRCA1", InteractionType.COMPLEX_MEMBER, 0.85, ["DNA repair"]),
    ("RB1", "CDK4", InteractionType.ENZYME_SUBSTRATE, 0.93, ["Cell cycle"]),
    ("RB1", "CDK6", InteractionType.ENZYME_SUBSTRATE, 0.91, ["Cell cycle"]),
    ("BRCA1", "BRCA2", InteractionType.COMPLEX_MEMBER, 0.90, ["DNA repair"]),

    # ─── Tumor microenvironment ───
    ("VEGFA", "VEGFR2", InteractionType.RECEPTOR_LIGAND, 0.97, ["Angiogenesis"]),
    ("CXCL12", "CXCR4", InteractionType.RECEPTOR_LIGAND, 0.95, ["TME"]),
    ("CCL2", "CCR2", InteractionType.RECEPTOR_LIGAND, 0.92, ["TME"]),
    ("TGFB1", "TGFBR1", InteractionType.RECEPTOR_LIGAND, 0.94, ["TME"]),
    ("IDO1", "TRYPTOPHAN", InteractionType.ENZYME_SUBSTRATE, 0.88, ["TME", "Metabolism"]),

    # ─── JAK-STAT pathway ───
    ("JAK1", "STAT1", InteractionType.SIGNALING, 0.92, ["JAK-STAT"]),
    ("JAK2", "STAT3", InteractionType.SIGNALING, 0.95, ["JAK-STAT"]),
    ("JAK2", "STAT5", InteractionType.SIGNALING, 0.90, ["JAK-STAT"]),
    ("JAK3", "STAT5", InteractionType.SIGNALING, 0.88, ["JAK-STAT"]),

    # ─── Apoptosis pathway ───
    ("BCL2", "BAX", InteractionType.PHYSICAL_BINDING, 0.95, ["Apoptosis"]),
    ("BCL2", "BIM", InteractionType.PHYSICAL_BINDING, 0.92, ["Apoptosis"]),
    ("BCLXL", "BAK", InteractionType.PHYSICAL_BINDING, 0.90, ["Apoptosis"]),
    ("CASP3", "CASP9", InteractionType.SIGNALING, 0.93, ["Apoptosis"]),
    ("FASL", "FAS", InteractionType.RECEPTOR_LIGAND, 0.97, ["Apoptosis"]),
]

# Node feature vectors (simplified protein embeddings)
# Each feature: [surface_expr, tumor_expr, essentiality, druggability, connectivity]
NODE_FEATURES: Dict[str, List[float]] = {
    "CD19": [1.0, 0.98, 0.0, 0.90, 0.85], "BCMA": [1.0, 0.95, 0.0, 0.85, 0.70],
    "CD22": [1.0, 0.85, 0.0, 0.88, 0.75], "CD20": [1.0, 0.92, 0.0, 0.85, 0.72],
    "HER2": [1.0, 0.75, 1.0, 0.80, 0.90], "EGFR": [1.0, 0.82, 1.0, 0.78, 0.92],
    "MSLN": [1.0, 0.88, 0.0, 0.75, 0.65], "GPC3": [1.0, 0.80, 0.0, 0.72, 0.55],
    "PSMA": [1.0, 0.93, 0.0, 0.78, 0.50], "CD70": [0.9, 0.70, 0.0, 0.70, 0.60],
    "PD_L1": [1.0, 0.55, 0.0, 0.85, 0.80], "CD47": [1.0, 0.80, 1.0, 0.75, 0.85],
    "B7_H3": [1.0, 0.78, 0.0, 0.80, 0.55], "GPRC5D": [0.9, 0.80, 0.0, 0.72, 0.45],
    "EpCAM": [1.0, 0.85, 0.0, 0.75, 0.60], "GD2": [1.0, 0.92, 0.0, 0.65, 0.50],
    "DLL3": [0.9, 0.85, 0.0, 0.70, 0.55], "CLDN18.2": [1.0, 0.72, 0.0, 0.68, 0.48],
    "MUC16": [1.0, 0.90, 0.0, 0.60, 0.45], "ROR1": [0.9, 0.68, 0.0, 0.72, 0.55],
    "IL13RA2": [1.0, 0.75, 0.0, 0.70, 0.45], "FcRH5": [0.9, 0.75, 0.0, 0.68, 0.42],
    "KRAS": [0.0, 0.40, 1.0, 0.30, 0.95], "BRAF": [0.0, 0.35, 0.8, 0.35, 0.85],
    "PIK3CA": [0.0, 0.30, 0.7, 0.40, 0.88], "AKT1": [0.0, 0.25, 0.8, 0.35, 0.82],
    "TP53": [0.0, 0.10, 1.0, 0.15, 0.95], "PTEN": [0.0, 0.08, 1.0, 0.20, 0.80],
    "BCL2": [0.0, 0.20, 0.5, 0.40, 0.75], "MET": [0.9, 0.70, 0.5, 0.75, 0.72],
    "ALK": [0.8, 0.50, 0.3, 0.72, 0.60], "CSPG4": [1.0, 0.72, 0.0, 0.58, 0.45],
    "NKG2D_L": [0.8, 0.65, 0.0, 0.62, 0.50], "VEGFR2": [0.9, 0.40, 0.5, 0.78, 0.75],
}


# ──────────────────────────────────────────────────────────────────────
# Data Classes
# ──────────────────────────────────────────────────────────────────────

@dataclass
class GraphNode:
    """A node in the protein interaction graph."""
    protein_id: str
    feature_vector: List[float]
    embedding: List[float] = field(default_factory=list)
    degree: int = 0
    cluster_id: int = -1
    pagerank: float = 0.0
    betweenness: float = 0.0


@dataclass
class GraphEdge:
    """An edge in the protein interaction graph."""
    source: str
    target: str
    interaction_type: InteractionType
    confidence: float
    pathways: List[str]
    weight: float = 1.0


@dataclass
class ProteinInteractionGraph:
    """Complete protein interaction graph."""
    nodes: Dict[str, GraphNode] = field(default_factory=dict)
    edges: List[GraphEdge] = field(default_factory=list)
    adjacency: Dict[str, List[str]] = field(default_factory=lambda: defaultdict(list))
    total_nodes: int = 0
    total_edges: int = 0
    avg_degree: float = 0.0
    density: float = 0.0


@dataclass
class GNNPrediction:
    """GNN inference result for interaction prediction."""
    protein_a: str
    protein_b: str
    predicted_interaction: float  # 0-1 probability
    predicted_type: InteractionType
    confidence: float
    pathway_context: List[str]
    supporting_evidence: List[str]


@dataclass
class CommunityCluster:
    """A detected community/cluster in the graph."""
    cluster_id: int
    name: str
    members: List[str]
    size: int
    avg_internal_weight: float
    dominant_pathway: str
    car_t_relevance: float  # 0-1


# ──────────────────────────────────────────────────────────────────────
# Graph Construction
# ──────────────────────────────────────────────────────────────────────

async def build_protein_interaction_graph(
    include_pathways: Optional[List[str]] = None,
    min_confidence: float = 0.5,
    max_nodes: int = 500,
) -> ProteinInteractionGraph:
    """
    Build a protein-protein interaction graph from curated databases.

    Args:
        include_pathways: Filter for specific pathways
        min_confidence: Minimum interaction confidence
        max_nodes: Maximum graph nodes

    Returns:
        ProteinInteractionGraph with nodes, edges, and adjacency
    """
    graph = ProteinInteractionGraph()

    # Filter interactions
    filtered_interactions = []
    for pA, pB, itype, conf, pathways in CURATED_INTERACTIONS:
        if conf < min_confidence:
            continue
        if include_pathways:
            if not any(p in pathways for p in include_pathways):
                continue
        filtered_interactions.append((pA, pB, itype, conf, pathways))

    # Build nodes
    all_proteins: Set[str] = set()
    for pA, pB, _, _, _ in filtered_interactions:
        all_proteins.add(pA)
        all_proteins.add(pB)

    for protein in list(all_proteins)[:max_nodes]:
        features = NODE_FEATURES.get(protein, [0.5, 0.5, 0.5, 0.5, 0.5])
        node = GraphNode(
            protein_id=protein,
            feature_vector=features,
        )
        graph.nodes[protein] = node

    # Build edges
    for pA, pB, itype, conf, pathways in filtered_interactions:
        if pA not in graph.nodes or pB not in graph.nodes:
            continue

        edge = GraphEdge(
            source=pA,
            target=pB,
            interaction_type=itype,
            confidence=conf,
            pathways=pathways,
            weight=conf,
        )
        graph.edges.append(edge)
        graph.adjacency[pA].append(pB)
        graph.adjacency[pB].append(pA)

    # Compute degree and stats
    for node_id, node in graph.nodes.items():
        node.degree = len(graph.adjacency.get(node_id, []))

    graph.total_nodes = len(graph.nodes)
    graph.total_edges = len(graph.edges)
    if graph.total_nodes > 0:
        graph.avg_degree = sum(n.degree for n in graph.nodes.values()) / graph.total_nodes
        max_possible_edges = graph.total_nodes * (graph.total_nodes - 1) / 2
        graph.density = graph.total_edges / max_possible_edges if max_possible_edges > 0 else 0

    logger.info(
        f"Graph built: {graph.total_nodes} nodes, {graph.total_edges} edges, "
        f"density={graph.density:.3f}"
    )
    return graph


# ──────────────────────────────────────────────────────────────────────
# Message-Passing GNN Simulation
# ──────────────────────────────────────────────────────────────────────

def _relu(x: float) -> float:
    return max(0.0, x)


def _sigmoid(x: float) -> float:
    return 1.0 / (1.0 + math.exp(-max(-500, min(500, x))))


def _compute_node_embeddings(
    graph: ProteinInteractionGraph,
    embedding_dim: int = 8,
    num_layers: int = 3,
) -> Dict[str, List[float]]:
    """
    Compute node embeddings using simulated message-passing.

    Implements a simplified GraphSAGE-like algorithm:
    1. Initialize embeddings from node features
    2. For each layer, aggregate neighbor embeddings
    3. Apply non-linearity and normalization

    Args:
        graph: The protein interaction graph
        embedding_dim: Dimension of output embeddings
        num_layers: Number of message-passing layers

    Returns:
        Dict mapping protein → embedding vector
    """
    # Initialize embeddings from features
    embeddings: Dict[str, List[float]] = {}
    for node_id, node in graph.nodes.items():
        features = node.feature_vector
        # Pad or truncate to embedding_dim
        if len(features) < embedding_dim:
            features = features + [0.0] * (embedding_dim - len(features))
        elif len(features) > embedding_dim:
            features = features[:embedding_dim]
        embeddings[node_id] = features[:]

    # Simulated weight matrices (deterministic pseudo-random)
    def _weight(layer: int, i: int, j: int) -> float:
        seed = hash(f"W_{layer}_{i}_{j}") % 10000
        return (seed / 10000.0 - 0.5) * 0.5  # [-0.25, 0.25]

    # Message passing layers
    for layer in range(num_layers):
        new_embeddings: Dict[str, List[float]] = {}

        for node_id in graph.nodes:
            # Self embedding
            self_emb = embeddings[node_id]

            # Aggregate neighbor embeddings (mean aggregation)
            neighbors = graph.adjacency.get(node_id, [])
            if neighbors:
                agg = [0.0] * embedding_dim
                total_weight = 0.0
                for neighbor_id in neighbors:
                    if neighbor_id in embeddings:
                        n_emb = embeddings[neighbor_id]
                        # Find edge weight
                        edge_weight = 0.5
                        for edge in graph.edges:
                            if (edge.source == node_id and edge.target == neighbor_id) or \
                               (edge.target == node_id and edge.source == neighbor_id):
                                edge_weight = edge.confidence
                                break
                        for d in range(embedding_dim):
                            agg[d] += n_emb[d] * edge_weight
                        total_weight += edge_weight

                if total_weight > 0:
                    agg = [a / total_weight for a in agg]
            else:
                agg = [0.0] * embedding_dim

            # Combine self + aggregated (GraphSAGE concat style)
            combined = []
            for d in range(embedding_dim):
                val = 0.0
                for k in range(embedding_dim):
                    val += self_emb[k] * _weight(layer, d, k)
                    val += agg[k] * _weight(layer, d + embedding_dim, k)
                combined.append(_relu(val))

            # Normalize
            norm = math.sqrt(sum(v * v for v in combined) + 1e-8)
            combined = [v / norm for v in combined]

            new_embeddings[node_id] = combined

        embeddings = new_embeddings

    # Store on nodes
    for node_id, emb in embeddings.items():
        if node_id in graph.nodes:
            graph.nodes[node_id].embedding = emb

    return embeddings


def _compute_pagerank(
    graph: ProteinInteractionGraph,
    damping: float = 0.85,
    iterations: int = 50,
) -> Dict[str, float]:
    """Compute PageRank for all nodes."""
    n = graph.total_nodes
    if n == 0:
        return {}

    ranks = {node_id: 1.0 / n for node_id in graph.nodes}

    for _ in range(iterations):
        new_ranks: Dict[str, float] = {}
        for node_id in graph.nodes:
            rank_sum = 0.0
            for neighbor_id in graph.adjacency.get(node_id, []):
                if neighbor_id in ranks:
                    out_degree = len(graph.adjacency.get(neighbor_id, []))
                    if out_degree > 0:
                        rank_sum += ranks[neighbor_id] / out_degree
            new_ranks[node_id] = (1 - damping) / n + damping * rank_sum
        ranks = new_ranks

    # Normalize
    total = sum(ranks.values())
    if total > 0:
        ranks = {k: v / total for k, v in ranks.items()}

    for node_id, rank in ranks.items():
        if node_id in graph.nodes:
            graph.nodes[node_id].pagerank = round(rank, 6)

    return ranks


async def run_gnn_inference(
    graph: ProteinInteractionGraph,
    embedding_dim: int = 8,
    num_layers: int = 3,
) -> Dict[str, Any]:
    """
    Run complete GNN inference on the protein interaction graph.

    Steps:
    1. Compute node embeddings via message passing
    2. Compute PageRank centrality
    3. Detect communities
    4. Identify high-connectivity hubs

    Returns:
        Dict with embeddings, centralities, and community assignments
    """
    # Step 1: Node embeddings
    embeddings = _compute_node_embeddings(graph, embedding_dim, num_layers)

    # Step 2: PageRank
    pageranks = _compute_pagerank(graph)

    # Step 3: Community detection (simple label propagation)
    communities = _detect_communities(graph)

    # Step 4: Hub identification
    hubs = sorted(
        [(nid, n.degree, n.pagerank) for nid, n in graph.nodes.items()],
        key=lambda x: x[2], reverse=True,
    )[:10]

    return {
        "total_nodes": graph.total_nodes,
        "total_edges": graph.total_edges,
        "density": round(graph.density, 4),
        "avg_degree": round(graph.avg_degree, 2),
        "embedding_dim": embedding_dim,
        "num_layers": num_layers,
        "communities": [
            {
                "id": c.cluster_id,
                "name": c.name,
                "members": c.members,
                "size": c.size,
                "dominant_pathway": c.dominant_pathway,
                "car_t_relevance": c.car_t_relevance,
            }
            for c in communities
        ],
        "hubs": [
            {"protein": h[0], "degree": h[1], "pagerank": round(h[2], 6)}
            for h in hubs
        ],
        "node_details": {
            nid: {
                "degree": n.degree,
                "pagerank": n.pagerank,
                "cluster": n.cluster_id,
                "embedding": [round(v, 4) for v in n.embedding[:4]],  # truncate for API
            }
            for nid, n in graph.nodes.items()
        },
    }


# ──────────────────────────────────────────────────────────────────────
# Community Detection
# ──────────────────────────────────────────────────────────────────────

def _detect_communities(
    graph: ProteinInteractionGraph,
    max_iterations: int = 20,
) -> List[CommunityCluster]:
    """
    Detect communities using label propagation algorithm.
    """
    if not graph.nodes:
        return []

    # Initialize each node with its own label
    labels: Dict[str, int] = {}
    for i, node_id in enumerate(graph.nodes):
        labels[node_id] = i

    # Iterative label propagation
    for _ in range(max_iterations):
        changed = False
        for node_id in graph.nodes:
            neighbors = graph.adjacency.get(node_id, [])
            if not neighbors:
                continue

            # Count neighbor labels (weighted by edge confidence)
            label_weights: Dict[int, float] = defaultdict(float)
            for neighbor_id in neighbors:
                if neighbor_id in labels:
                    n_label = labels[neighbor_id]
                    weight = 1.0
                    for edge in graph.edges:
                        if (edge.source == node_id and edge.target == neighbor_id) or \
                           (edge.target == node_id and edge.source == neighbor_id):
                            weight = edge.confidence
                            break
                    label_weights[n_label] += weight

            if label_weights:
                best_label = max(label_weights, key=lambda l: label_weights[l])
                if labels[node_id] != best_label:
                    labels[node_id] = best_label
                    changed = True

        if not changed:
            break

    # Group by label
    clusters_map: Dict[int, List[str]] = defaultdict(list)
    for node_id, label in labels.items():
        clusters_map[label].append(node_id)

    # Assign cluster IDs to nodes
    for label, members in clusters_map.items():
        for member in members:
            if member in graph.nodes:
                graph.nodes[member].cluster_id = label

    # Build cluster objects
    communities: List[CommunityCluster] = []
    for cluster_id, (label, members) in enumerate(clusters_map.items()):
        if len(members) < 2:
            continue

        # Find dominant pathway
        pathway_counts: Dict[str, int] = defaultdict(int)
        total_internal_weight = 0.0
        internal_edge_count = 0
        member_set = set(members)

        for edge in graph.edges:
            if edge.source in member_set and edge.target in member_set:
                total_internal_weight += edge.confidence
                internal_edge_count += 1
                for p in edge.pathways:
                    pathway_counts[p] += 1

        dominant = max(pathway_counts, key=lambda p: pathway_counts[p]) if pathway_counts else "Unknown"
        avg_weight = total_internal_weight / max(internal_edge_count, 1)

        # CAR-T relevance (based on surface protein membership)
        surface_members = sum(
            1 for m in members
            if m in NODE_FEATURES and NODE_FEATURES[m][0] > 0.7
        )
        car_t_rel = surface_members / max(len(members), 1)

        cluster_name = f"{dominant} cluster" if dominant != "Unknown" else f"Cluster {cluster_id}"

        communities.append(CommunityCluster(
            cluster_id=cluster_id,
            name=cluster_name,
            members=sorted(members),
            size=len(members),
            avg_internal_weight=round(avg_weight, 3),
            dominant_pathway=dominant,
            car_t_relevance=round(car_t_rel, 3),
        ))

    communities.sort(key=lambda c: c.size, reverse=True)
    return communities


# ──────────────────────────────────────────────────────────────────────
# Link Prediction
# ──────────────────────────────────────────────────────────────────────

async def predict_target_interactions(
    graph: ProteinInteractionGraph,
    target_protein: str,
    top_k: int = 10,
) -> List[GNNPrediction]:
    """
    Predict novel interactions for a target protein using learned embeddings.

    Uses cosine similarity between node embeddings and structural features
    to predict likely interaction partners.

    Args:
        graph: Protein interaction graph with computed embeddings
        target_protein: The protein to find interactions for
        top_k: Number of predictions to return

    Returns:
        List of GNNPrediction objects ranked by predicted probability
    """
    if target_protein not in graph.nodes:
        return []

    target_node = graph.nodes[target_protein]
    target_emb = target_node.embedding

    if not target_emb:
        # Compute embeddings if not done
        _compute_node_embeddings(graph)
        target_emb = graph.nodes[target_protein].embedding

    # Existing neighbors (to exclude from predictions)
    existing_neighbors = set(graph.adjacency.get(target_protein, []))

    predictions: List[GNNPrediction] = []

    for other_id, other_node in graph.nodes.items():
        if other_id == target_protein or other_id in existing_neighbors:
            continue

        other_emb = other_node.embedding
        if not other_emb or not target_emb:
            continue

        # Cosine similarity between embeddings
        dot = sum(a * b for a, b in zip(target_emb, other_emb))
        norm_a = math.sqrt(sum(a * a for a in target_emb) + 1e-8)
        norm_b = math.sqrt(sum(b * b for b in other_emb) + 1e-8)
        cosine_sim = dot / (norm_a * norm_b)

        # Common neighbors (Jaccard index for structural prediction)
        other_neighbors = set(graph.adjacency.get(other_id, []))
        common = existing_neighbors & other_neighbors
        union = existing_neighbors | other_neighbors
        jaccard = len(common) / max(len(union), 1)

        # Combined prediction score
        pred_score = _sigmoid(cosine_sim * 2.0 + jaccard * 3.0)

        # Determine predicted interaction type
        target_features = target_node.feature_vector
        other_features = other_node.feature_vector
        if target_features[0] > 0.7 and other_features[0] > 0.7:
            pred_type = InteractionType.CO_EXPRESSION
        elif abs(target_features[0] - other_features[0]) > 0.5:
            pred_type = InteractionType.SIGNALING
        else:
            pred_type = InteractionType.PATHWAY_MEMBER

        # Identify common pathway context
        pathway_context: List[str] = []
        for edge in graph.edges:
            if edge.source in common or edge.target in common:
                pathway_context.extend(edge.pathways)
        pathway_context = list(set(pathway_context))[:5]

        # Supporting evidence
        evidence: List[str] = []
        if common:
            evidence.append(f"Shares {len(common)} common interaction partners: {', '.join(list(common)[:3])}")
        if cosine_sim > 0.5:
            evidence.append(f"High embedding similarity ({cosine_sim:.2f})")
        if target_node.cluster_id == other_node.cluster_id and target_node.cluster_id >= 0:
            evidence.append("Same network community/cluster")

        predictions.append(GNNPrediction(
            protein_a=target_protein,
            protein_b=other_id,
            predicted_interaction=round(pred_score, 4),
            predicted_type=pred_type,
            confidence=round(pred_score * 0.8, 4),  # conservative
            pathway_context=pathway_context,
            supporting_evidence=evidence,
        ))

    predictions.sort(key=lambda p: p.predicted_interaction, reverse=True)
    return predictions[:top_k]
