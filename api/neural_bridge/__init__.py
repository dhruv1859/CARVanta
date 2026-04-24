"""
CARVanta Neural Bridge — Module 11
====================================
Multi-layer knowledge graph engine for CAR-T antigen discovery.

Sub-modules
-----------
graph_builder        5-layer knowledge graph construction
graph_analytics      12+ network science metrics
graph_api            55+ REST API endpoints
cluster_engine       Louvain / label-propagation communities
search_engine        Fuzzy search with BM25 scoring
path_finder          BFS, Dijkstra, Yen's k-shortest paths
similarity_engine    SimRank, Cosine, Attribute, Role similarity
visualization        5 layout algorithms + LOD configuration
export               JSON / CSV / GraphML / Cytoscape export
diffusion_engine     Heat diffusion, RWR, SIR, influence max
motif_detection      Triangles, cliques, FFLs, hubs, diamonds
graph_temporal       Snapshot versioning, diff, stability analysis
embedding_engine     DeepWalk / Node2Vec / structural embeddings

Architecture
------------
All algorithms are implemented from scratch with zero external
dependencies (no NetworkX, no PyTorch, no scikit-learn).  This
ensures:
  • Sub-millisecond cold starts
  • Minimal memory footprint
  • Full portability (runs on any Python 3.9+)
  • Complete auditability of every computation

The knowledge graph is built lazily on first API call and cached
in-process.  Graph data flows through 5 layers:

    Clinical → Biological → Omics → Pathways → Families

Each layer contributes nodes and edges encoding relationships
like 'targets', 'co-expressed_with', 'shared_pathway', etc.

API Surface
-----------
All endpoints are mounted under ``/api/v5/bridge/`` and include:

  GET  /graph                    Full graph data
  GET  /summary                  Node/edge/group summary
  GET  /search                   Fuzzy node search
  GET  /suggest                  Autocomplete suggestions
  GET  /clusters                 Community detection
  GET  /clusters/bridging-nodes  Boundary spanners
  GET  /analytics/full           Complete network analytics
  GET  /analytics/centrality/{m} Centrality by metric
  GET  /analytics/clustering     Clustering coefficients
  GET  /analytics/components     Connected components
  GET  /analytics/hits           HITS hubs & authorities
  GET  /analytics/topology       Radius, diameter, centre
  GET  /analytics/triads         Triad census
  GET  /analytics/rich-club      Rich-club coefficient
  GET  /analytics/small-world    Small-world test
  GET  /path/{s}/{t}             Shortest path
  GET  /k-paths/{s}/{t}          K shortest paths
  GET  /predict-links            Link prediction ensemble
  GET  /similar/{node}           Node similarity
  GET  /indication-expansion/{n} Indication expansion
  GET  /layout/{algorithm}       Graph layout coordinates
  GET  /styles                   Node/edge styling config
  GET  /lod-config               Level-of-detail settings
  GET  /export/{format}          Export in multiple formats
  GET  /diffusion/heat           Heat diffusion simulation
  GET  /diffusion/rwr/{node}     Random walk with restart
  GET  /diffusion/sir            SIR epidemic simulation
  GET  /diffusion/influence-max  Top-k influence maximisation
  GET  /motifs/census            Full motif census
  GET  /motifs/triangles         Triangle detection
  GET  /motifs/cliques           Clique detection (Bron-Kerbosch)
  GET  /motifs/hubs              Hub-spoke patterns
  GET  /motifs/diamonds          Redundant pathway diamonds
  GET  /motifs/chains            Linear signal cascades
  POST /snapshot                 Create graph snapshot
  GET  /snapshots                List all snapshots
  GET  /snapshots/diff           Diff two snapshots
  GET  /snapshots/growth         Growth timeline
  GET  /snapshots/stability      Stability analysis
  GET  /snapshots/events         Event timeline
  GET  /snapshots/group-evolution Group distribution over time
  GET  /embeddings               Compute node embeddings
  GET  /embeddings/similar/{n}   Embedding-space similarity
  GET  /embeddings/clusters      Embedding-space clustering

Frontend Pages
--------------
  /neural-bridge               Main graph visualiser (Canvas 2D)
  /neural-bridge/advanced      Diffusion & motif analytics
  /neural-bridge/explorer      Deep-dive node explorer
  /neural-bridge/dashboard     Network metrics dashboard
"""

__version__ = "2.0.0"
__all__ = [
    "graph_builder",
    "graph_analytics",
    "graph_api",
    "cluster_engine",
    "search_engine",
    "path_finder",
    "similarity_engine",
    "visualization",
    "export",
    "diffusion_engine",
    "motif_detection",
    "graph_temporal",
    "embedding_engine",
]
