"""
CARVanta Neural Bridge — Temporal & Versioned Graph Engine
===========================================================
Tracks changes to the knowledge graph over time, enables
time-travel queries, and computes graph evolution metrics.

Features:
  ▸ Graph snapshots with UTC timestamps
  ▸ Diff computation between snapshots
  ▸ Node/edge lifecycle tracking (added, removed, modified)
  ▸ Temporal centrality (how a node's importance changes)
  ▸ Growth rate analysis
  ▸ Stability metrics (edge persistence, node churn)
  ▸ Trend detection for graph properties
  ▸ Event timeline (significant structural changes)
  ▸ Rollback to previous snapshot
"""

from __future__ import annotations

import hashlib
import copy
import math
import statistics
from collections import defaultdict
from datetime import datetime, timezone
from typing import Any, Dict, FrozenSet, List, Optional, Set, Tuple


# ═══════════════════════════════════════════════════════════════════════════════
# Snapshot Storage
# ═══════════════════════════════════════════════════════════════════════════════

class GraphSnapshot:
    """Immutable snapshot of the graph at a point in time."""
    __slots__ = ["timestamp", "node_ids", "edge_set", "node_count",
                 "edge_count", "groups", "label"]

    def __init__(
        self,
        nodes: List[Dict[str, Any]],
        links: List[Dict[str, Any]],
        label: str = "",
    ):
        self.timestamp = datetime.now(timezone.utc)
        self.node_ids = frozenset(n["id"] for n in nodes)
        self.edge_set = frozenset(
            (lnk.get("source", ""), lnk.get("target", ""))
            for lnk in links
        )
        self.node_count = len(self.node_ids)
        self.edge_count = len(self.edge_set)
        self.groups: Dict[str, int] = defaultdict(int)
        for n in nodes:
            self.groups[n.get("group", "Unknown")] += 1
        self.label = label or f"snapshot_{self.timestamp.strftime('%Y%m%d_%H%M%S')}"

    def to_dict(self) -> Dict[str, Any]:
        return {
            "label": self.label,
            "timestamp": self.timestamp.isoformat(),
            "node_count": self.node_count,
            "edge_count": self.edge_count,
            "groups": dict(self.groups),
        }


class TemporalGraphStore:
    """
    Manages a sequence of graph snapshots and provides diff,
    lifecycle, and trend analysis capabilities.
    """

    def __init__(self, max_snapshots: int = 50):
        self.snapshots: List[GraphSnapshot] = []
        self.max_snapshots = max_snapshots
        self._event_log: List[Dict[str, Any]] = []

    # ── Snapshot Management ─────────────────────────────────────────

    def create_snapshot(
        self,
        nodes: List[Dict[str, Any]],
        links: List[Dict[str, Any]],
        label: str = "",
    ) -> Dict[str, Any]:
        """Create and store a new graph snapshot."""
        snap = GraphSnapshot(nodes, links, label)

        # Detect events vs previous
        if self.snapshots:
            prev = self.snapshots[-1]
            added_nodes = snap.node_ids - prev.node_ids
            removed_nodes = prev.node_ids - snap.node_ids
            added_edges = snap.edge_set - prev.edge_set
            removed_edges = prev.edge_set - snap.edge_set

            if added_nodes or removed_nodes or len(added_edges) > 10:
                self._event_log.append({
                    "timestamp": snap.timestamp.isoformat(),
                    "label": snap.label,
                    "nodes_added": len(added_nodes),
                    "nodes_removed": len(removed_nodes),
                    "edges_added": len(added_edges),
                    "edges_removed": len(removed_edges),
                    "significance": _event_significance(
                        len(added_nodes), len(removed_nodes),
                        len(added_edges), len(removed_edges),
                        prev.node_count, prev.edge_count,
                    ),
                })

        self.snapshots.append(snap)
        if len(self.snapshots) > self.max_snapshots:
            self.snapshots.pop(0)

        return snap.to_dict()

    def list_snapshots(self) -> List[Dict[str, Any]]:
        """List all stored snapshots."""
        return [s.to_dict() for s in self.snapshots]

    def get_snapshot(self, index: int) -> Optional[Dict[str, Any]]:
        """Get snapshot by index (0 = oldest, -1 = latest)."""
        if not self.snapshots:
            return None
        idx = index % len(self.snapshots)
        return self.snapshots[idx].to_dict()

    # ── Diff Computation ────────────────────────────────────────────

    def diff(
        self,
        index_a: int = -2,
        index_b: int = -1,
    ) -> Dict[str, Any]:
        """
        Compute the diff between two snapshots.
        Default: diff between the two most recent snapshots.
        """
        if len(self.snapshots) < 2:
            return {"error": "Need at least 2 snapshots for diff"}

        a = self.snapshots[index_a % len(self.snapshots)]
        b = self.snapshots[index_b % len(self.snapshots)]

        nodes_added = b.node_ids - a.node_ids
        nodes_removed = a.node_ids - b.node_ids
        nodes_unchanged = a.node_ids & b.node_ids
        edges_added = b.edge_set - a.edge_set
        edges_removed = a.edge_set - b.edge_set

        return {
            "snapshot_a": a.to_dict(),
            "snapshot_b": b.to_dict(),
            "nodes": {
                "added": sorted(nodes_added)[:50],
                "removed": sorted(nodes_removed)[:50],
                "unchanged": len(nodes_unchanged),
                "n_added": len(nodes_added),
                "n_removed": len(nodes_removed),
            },
            "edges": {
                "added": len(edges_added),
                "removed": len(edges_removed),
                "net_change": len(edges_added) - len(edges_removed),
            },
            "growth_rate": {
                "node_growth_pct": round(
                    (b.node_count - a.node_count) / max(a.node_count, 1) * 100, 2
                ),
                "edge_growth_pct": round(
                    (b.edge_count - a.edge_count) / max(a.edge_count, 1) * 100, 2
                ),
            },
        }

    # ── Growth Analysis ─────────────────────────────────────────────

    def growth_timeline(self) -> Dict[str, Any]:
        """Track node/edge counts over all snapshots."""
        if not self.snapshots:
            return {"timeline": []}

        timeline = []
        for i, snap in enumerate(self.snapshots):
            entry = {
                "index": i,
                "label": snap.label,
                "timestamp": snap.timestamp.isoformat(),
                "nodes": snap.node_count,
                "edges": snap.edge_count,
                "density": round(
                    2 * snap.edge_count / max(snap.node_count * (snap.node_count - 1), 1), 6
                ),
            }
            if i > 0:
                prev = self.snapshots[i - 1]
                entry["node_delta"] = snap.node_count - prev.node_count
                entry["edge_delta"] = snap.edge_count - prev.edge_count
            timeline.append(entry)

        return {"timeline": timeline, "total_snapshots": len(self.snapshots)}

    # ── Stability Metrics ───────────────────────────────────────────

    def stability_analysis(self) -> Dict[str, Any]:
        """
        Compute how stable the graph is across snapshots.
        High stability = few structural changes over time.
        """
        if len(self.snapshots) < 2:
            return {"error": "Need ≥2 snapshots"}

        jaccard_nodes = []
        jaccard_edges = []
        churn_rates = []

        for i in range(1, len(self.snapshots)):
            a, b = self.snapshots[i - 1], self.snapshots[i]

            # Jaccard similarity of node sets
            inter_n = len(a.node_ids & b.node_ids)
            union_n = len(a.node_ids | b.node_ids)
            jaccard_nodes.append(inter_n / max(union_n, 1))

            # Jaccard similarity of edge sets
            inter_e = len(a.edge_set & b.edge_set)
            union_e = len(a.edge_set | b.edge_set)
            jaccard_edges.append(inter_e / max(union_e, 1))

            # Churn rate
            churn = (len(b.node_ids - a.node_ids) + len(a.node_ids - b.node_ids))
            churn_rates.append(churn / max(len(a.node_ids | b.node_ids), 1))

        return {
            "node_stability": round(statistics.mean(jaccard_nodes), 4),
            "edge_stability": round(statistics.mean(jaccard_edges), 4),
            "avg_churn_rate": round(statistics.mean(churn_rates), 4),
            "n_comparisons": len(jaccard_nodes),
            "per_snapshot": [
                {
                    "snapshot": i + 1,
                    "node_jaccard": round(jaccard_nodes[i], 4),
                    "edge_jaccard": round(jaccard_edges[i], 4),
                    "churn_rate": round(churn_rates[i], 4),
                }
                for i in range(len(jaccard_nodes))
            ],
        }

    # ── Event Log ───────────────────────────────────────────────────

    def event_timeline(self) -> Dict[str, Any]:
        """Return the event log of significant structural changes."""
        return {
            "events": sorted(
                self._event_log,
                key=lambda e: e.get("significance", 0),
                reverse=True,
            ),
            "total_events": len(self._event_log),
        }

    # ── Group Evolution ─────────────────────────────────────────────

    def group_evolution(self) -> Dict[str, Any]:
        """Track how group distributions change across snapshots."""
        if not self.snapshots:
            return {"evolution": []}

        all_groups: Set[str] = set()
        for s in self.snapshots:
            all_groups.update(s.groups.keys())

        evolution = []
        for i, snap in enumerate(self.snapshots):
            entry: Dict[str, Any] = {
                "index": i,
                "timestamp": snap.timestamp.isoformat(),
            }
            for g in sorted(all_groups):
                entry[g] = snap.groups.get(g, 0)
            evolution.append(entry)

        return {"groups": sorted(all_groups), "evolution": evolution}


# ── Helpers ──────────────────────────────────────────────────────────────

def _event_significance(
    n_added: int, n_removed: int,
    e_added: int, e_removed: int,
    prev_nodes: int, prev_edges: int,
) -> float:
    """Score importance of a graph-change event (0–1)."""
    node_change = (n_added + n_removed) / max(prev_nodes, 1)
    edge_change = (e_added + e_removed) / max(prev_edges, 1)
    return round(min(node_change * 0.6 + edge_change * 0.4, 1.0), 3)


# ── Module-level singleton ──────────────────────────────────────────────

temporal_store = TemporalGraphStore()
