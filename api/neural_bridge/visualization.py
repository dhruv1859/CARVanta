"""
CARVanta Neural Bridge — Graph Layout & Visualization Engine
==============================================================
Server-side layout computation and visualization configuration for
the knowledge graph.  Pre-computing layouts on the backend avoids
expensive browser-side force simulations on large graphs.

Layout algorithms:
  ▸ Force-directed (Fruchterman–Reingold)
  ▸ Circular / Radial layout
  ▸ Hierarchical (layered) layout
  ▸ Grid layout (grouped by attribute)
  ▸ Concentric layout (by centrality)

Visualization helpers:
  ▸ Node colour / size mapping by attribute
  ▸ Edge bundling preparation
  ▸ Level-of-detail (LOD) configuration
  ▸ Viewport culling (only return visible nodes)
  ▸ Animation keyframe generation
"""

from __future__ import annotations

import math
import random
from collections import defaultdict
from typing import Any, Dict, List, Optional, Set, Tuple


# ═══════════════════════════════════════════════════════════════════════════════
# Force-Directed Layout (Fruchterman–Reingold)
# ═══════════════════════════════════════════════════════════════════════════════

def force_directed_layout(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    width: float = 1000.0,
    height: float = 1000.0,
    iterations: int = 50,
    cooling_factor: float = 0.95,
    seed: int = 42,
) -> Dict[str, Dict[str, float]]:
    """
    Fruchterman–Reingold force-directed layout.

    Attractive forces pull connected nodes together;
    repulsive forces push all nodes apart.
    Converges via simulated annealing with temperature cooling.
    """
    rng = random.Random(seed)
    n = len(nodes)
    if n == 0:
        return {}

    area = width * height
    k = math.sqrt(area / n)  # optimal distance

    # Initial random positions
    pos: Dict[str, Dict[str, float]] = {}
    for node in nodes:
        nid = node["id"]
        pos[nid] = {
            "x": rng.uniform(0, width),
            "y": rng.uniform(0, height),
        }

    # Build adjacency
    adj: Dict[str, Set[str]] = defaultdict(set)
    for lnk in links:
        s, t = lnk.get("source", ""), lnk.get("target", "")
        if s and t:
            adj[s].add(t)
            adj[t].add(s)

    temp = width / 10  # initial temperature

    for _iteration in range(iterations):
        disp: Dict[str, Dict[str, float]] = {nid: {"x": 0, "y": 0} for nid in pos}

        node_ids = list(pos.keys())

        # Repulsive forces (all pairs — sampled for large graphs)
        if n > 300:
            # Sample pairs for O(n) instead of O(n²)
            sample_size = min(n * 10, n * n // 2)
            for _ in range(sample_size):
                u = rng.choice(node_ids)
                v = rng.choice(node_ids)
                if u == v:
                    continue
                dx = pos[u]["x"] - pos[v]["x"]
                dy = pos[u]["y"] - pos[v]["y"]
                dist = max(math.sqrt(dx * dx + dy * dy), 0.01)
                force = (k * k) / dist
                disp[u]["x"] += (dx / dist) * force
                disp[u]["y"] += (dy / dist) * force
                disp[v]["x"] -= (dx / dist) * force
                disp[v]["y"] -= (dy / dist) * force
        else:
            for i in range(len(node_ids)):
                for j in range(i + 1, len(node_ids)):
                    u, v = node_ids[i], node_ids[j]
                    dx = pos[u]["x"] - pos[v]["x"]
                    dy = pos[u]["y"] - pos[v]["y"]
                    dist = max(math.sqrt(dx * dx + dy * dy), 0.01)
                    force = (k * k) / dist
                    disp[u]["x"] += (dx / dist) * force
                    disp[u]["y"] += (dy / dist) * force
                    disp[v]["x"] -= (dx / dist) * force
                    disp[v]["y"] -= (dy / dist) * force

        # Attractive forces (connected pairs)
        for lnk in links:
            u, v = lnk.get("source", ""), lnk.get("target", "")
            if u not in pos or v not in pos:
                continue
            dx = pos[u]["x"] - pos[v]["x"]
            dy = pos[u]["y"] - pos[v]["y"]
            dist = max(math.sqrt(dx * dx + dy * dy), 0.01)
            force = (dist * dist) / k
            disp[u]["x"] -= (dx / dist) * force
            disp[u]["y"] -= (dy / dist) * force
            disp[v]["x"] += (dx / dist) * force
            disp[v]["y"] += (dy / dist) * force

        # Apply displacements (clamped by temperature)
        for nid in node_ids:
            dx = disp[nid]["x"]
            dy = disp[nid]["y"]
            dist = max(math.sqrt(dx * dx + dy * dy), 0.01)
            pos[nid]["x"] += (dx / dist) * min(abs(dx), temp)
            pos[nid]["y"] += (dy / dist) * min(abs(dy), temp)
            # Keep within bounds
            pos[nid]["x"] = max(0, min(width, pos[nid]["x"]))
            pos[nid]["y"] = max(0, min(height, pos[nid]["y"]))

        temp *= cooling_factor

    return pos


# ═══════════════════════════════════════════════════════════════════════════════
# Circular Layout
# ═══════════════════════════════════════════════════════════════════════════════

def circular_layout(
    nodes: List[Dict[str, Any]],
    center_x: float = 500.0,
    center_y: float = 500.0,
    radius: float = 400.0,
    group_by: Optional[str] = None,
) -> Dict[str, Dict[str, float]]:
    """
    Place nodes evenly on a circle, optionally grouped by an attribute
    so that nodes of the same group are adjacent on the ring.
    """
    if not nodes:
        return {}

    ordered = list(nodes)
    if group_by:
        ordered.sort(key=lambda n: n.get(group_by, ""))

    pos: Dict[str, Dict[str, float]] = {}
    n = len(ordered)

    for i, node in enumerate(ordered):
        angle = 2 * math.pi * i / n
        pos[node["id"]] = {
            "x": round(center_x + radius * math.cos(angle), 2),
            "y": round(center_y + radius * math.sin(angle), 2),
        }

    return pos


# ═══════════════════════════════════════════════════════════════════════════════
# Concentric Layout (by centrality)
# ═══════════════════════════════════════════════════════════════════════════════

def concentric_layout(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    center_x: float = 500.0,
    center_y: float = 500.0,
    max_radius: float = 450.0,
    n_rings: int = 5,
) -> Dict[str, Dict[str, float]]:
    """
    Place nodes on concentric rings by degree centrality.
    High-degree hubs at the centre, low-degree at the periphery.
    """
    adj: Dict[str, Set[str]] = defaultdict(set)
    for lnk in links:
        s, t = lnk.get("source", ""), lnk.get("target", "")
        adj[s].add(t)
        adj[t].add(s)

    # Sort by degree descending
    sorted_nodes = sorted(nodes, key=lambda n: len(adj.get(n["id"], set())), reverse=True)
    n = len(sorted_nodes)
    ring_size = max(1, n // n_rings)

    pos: Dict[str, Dict[str, float]] = {}
    for i, node in enumerate(sorted_nodes):
        ring = min(i // ring_size, n_rings - 1)
        pos_in_ring = i % ring_size
        ring_count = min(ring_size, n - ring * ring_size)
        radius = max_radius * (ring + 1) / n_rings

        angle = 2 * math.pi * pos_in_ring / max(ring_count, 1)
        pos[node["id"]] = {
            "x": round(center_x + radius * math.cos(angle), 2),
            "y": round(center_y + radius * math.sin(angle), 2),
        }

    return pos


# ═══════════════════════════════════════════════════════════════════════════════
# Hierarchical Layered Layout
# ═══════════════════════════════════════════════════════════════════════════════

def hierarchical_layout(
    nodes: List[Dict[str, Any]],
    width: float = 1000.0,
    height: float = 800.0,
    layer_attr: str = "layer",
    layer_order: Optional[List[str]] = None,
) -> Dict[str, Dict[str, float]]:
    """
    Place nodes in horizontal layers (swim lanes) based on an attribute.
    Default layers: clinical → biological → omics (top to bottom).
    """
    if layer_order is None:
        layer_order = ["clinical", "biological", "omics"]

    # Group by layer
    layers: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for node in nodes:
        lyr = node.get(layer_attr, "unknown")
        layers[lyr].append(node)

    # Ensure all layers are in the order
    ordered_layers = [l for l in layer_order if l in layers]
    for l in layers:
        if l not in ordered_layers:
            ordered_layers.append(l)

    n_layers = len(ordered_layers)
    layer_height = height / max(n_layers, 1)

    pos: Dict[str, Dict[str, float]] = {}
    for li, lyr in enumerate(ordered_layers):
        nodes_in_layer = layers[lyr]
        n_in_layer = len(nodes_in_layer)
        spacing = width / max(n_in_layer + 1, 1)

        for ni, node in enumerate(nodes_in_layer):
            pos[node["id"]] = {
                "x": round(spacing * (ni + 1), 2),
                "y": round(layer_height * (li + 0.5), 2),
            }

    return pos


# ═══════════════════════════════════════════════════════════════════════════════
# Grid Layout (grouped)
# ═══════════════════════════════════════════════════════════════════════════════

def grid_layout(
    nodes: List[Dict[str, Any]],
    group_by: str = "group",
    cell_size: float = 40.0,
    padding: float = 10.0,
) -> Dict[str, Dict[str, float]]:
    """
    Place nodes in a grid, clustered by group.
    Each group gets its own rectangular region.
    """
    groups: Dict[str, List[Dict[str, Any]]] = defaultdict(list)
    for n in nodes:
        groups[n.get(group_by, "Unknown")].append(n)

    pos: Dict[str, Dict[str, float]] = {}
    group_x_offset = 0.0

    for group_name, group_nodes in sorted(groups.items()):
        cols = max(1, int(math.ceil(math.sqrt(len(group_nodes)))))
        for i, node in enumerate(group_nodes):
            row = i // cols
            col = i % cols
            pos[node["id"]] = {
                "x": round(group_x_offset + col * cell_size, 2),
                "y": round(row * cell_size, 2),
            }
        group_x_offset += (cols + 2) * cell_size + padding

    return pos


# ═══════════════════════════════════════════════════════════════════════════════
# Node Style Mapper
# ═══════════════════════════════════════════════════════════════════════════════

_GROUP_COLOURS = {
    "Antigen": "#4ECDC4",
    "Disease": "#FF6B6B",
    "Pathway": "#45B7D1",
    "GeneFamily": "#96CEB4",
    "ProteinDomain": "#DDA0DD",
}

_LAYER_SHAPES = {
    "clinical": "diamond",
    "biological": "hexagon",
    "omics": "circle",
}


def compute_node_styles(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    size_by: str = "degree",
    color_by: str = "group",
    min_size: float = 4.0,
    max_size: float = 30.0,
) -> List[Dict[str, Any]]:
    """
    Compute visual styles for each node: colour, size, shape, opacity.
    """
    adj: Dict[str, Set[str]] = defaultdict(set)
    for lnk in links:
        adj[lnk.get("source", "")].add(lnk.get("target", ""))
        adj[lnk.get("target", "")].add(lnk.get("source", ""))

    # Compute sizes
    if size_by == "degree":
        degrees = {n["id"]: len(adj.get(n["id"], set())) for n in nodes}
        max_deg = max(degrees.values()) if degrees else 1
    elif size_by == "score":
        degrees = {n["id"]: float(n.get("score", 0.5)) for n in nodes}
        max_deg = max(degrees.values()) if degrees else 1
    else:
        degrees = {n["id"]: 1.0 for n in nodes}
        max_deg = 1

    styled = []
    for node in nodes:
        nid = node["id"]
        group = node.get("group", "Unknown")
        layer = node.get("layer", "unknown")

        # Size
        val = degrees.get(nid, 0)
        normalized = val / max(max_deg, 1)
        size = min_size + normalized * (max_size - min_size)

        # Colour
        if color_by == "group":
            colour = _GROUP_COLOURS.get(group, "#85929E")
        elif color_by == "layer":
            layer_colors = {"clinical": "#FF6B6B", "biological": "#4ECDC4", "omics": "#45B7D1"}
            colour = layer_colors.get(layer, "#85929E")
        else:
            # Gradient by score
            score = float(node.get("score", 0.5))
            r = int(255 * (1 - score))
            g = int(255 * score)
            colour = f"#{r:02x}{g:02x}80"

        styled.append({
            "id": nid,
            "size": round(size, 1),
            "color": colour,
            "shape": _LAYER_SHAPES.get(layer, "circle"),
            "opacity": round(0.6 + 0.4 * normalized, 2),
            "label_visible": normalized > 0.3,
        })

    return styled


# ═══════════════════════════════════════════════════════════════════════════════
# Viewport Culling
# ═══════════════════════════════════════════════════════════════════════════════

def viewport_cull(
    nodes: List[Dict[str, Any]],
    positions: Dict[str, Dict[str, float]],
    viewport_x: float,
    viewport_y: float,
    viewport_w: float,
    viewport_h: float,
    padding: float = 50.0,
) -> List[str]:
    """
    Return node IDs visible within the given viewport rectangle.
    Used for level-of-detail rendering on large graphs.
    """
    visible = []
    x1, y1 = viewport_x - padding, viewport_y - padding
    x2, y2 = viewport_x + viewport_w + padding, viewport_y + viewport_h + padding

    for nid, pos in positions.items():
        x, y = pos.get("x", 0), pos.get("y", 0)
        if x1 <= x <= x2 and y1 <= y <= y2:
            visible.append(nid)

    return visible


# ═══════════════════════════════════════════════════════════════════════════════
# Level-of-Detail Configuration
# ═══════════════════════════════════════════════════════════════════════════════

def lod_config(total_nodes: int) -> Dict[str, Any]:
    """
    Return recommended rendering configuration based on graph size.
    Larger graphs need simpler rendering to keep 60fps.
    """
    if total_nodes < 100:
        return {
            "render_labels": True,
            "render_arrows": True,
            "edge_opacity": 0.6,
            "particle_effects": True,
            "max_visible_labels": total_nodes,
            "edge_curvature": 0.2,
            "anti_aliasing": True,
            "bloom_effect": True,
        }
    elif total_nodes < 500:
        return {
            "render_labels": True,
            "render_arrows": False,
            "edge_opacity": 0.3,
            "particle_effects": False,
            "max_visible_labels": 50,
            "edge_curvature": 0,
            "anti_aliasing": True,
            "bloom_effect": False,
        }
    else:
        return {
            "render_labels": False,
            "render_arrows": False,
            "edge_opacity": 0.15,
            "particle_effects": False,
            "max_visible_labels": 20,
            "edge_curvature": 0,
            "anti_aliasing": False,
            "bloom_effect": False,
            "use_instanced_rendering": True,
        }


# ═══════════════════════════════════════════════════════════════════════════════
# Animation Keyframes
# ═══════════════════════════════════════════════════════════════════════════════

def generate_transition_keyframes(
    positions_from: Dict[str, Dict[str, float]],
    positions_to: Dict[str, Dict[str, float]],
    n_frames: int = 30,
    easing: str = "ease-in-out",
) -> List[Dict[str, Dict[str, float]]]:
    """
    Generate interpolated position keyframes for smooth layout transitions.
    Supports linear and ease-in-out easing.
    """
    all_ids = set(positions_from.keys()) | set(positions_to.keys())
    frames = []

    for frame in range(n_frames):
        t = frame / max(n_frames - 1, 1)

        if easing == "ease-in-out":
            t = t * t * (3 - 2 * t)  # smoothstep

        frame_pos: Dict[str, Dict[str, float]] = {}
        for nid in all_ids:
            p_from = positions_from.get(nid, {"x": 0, "y": 0})
            p_to = positions_to.get(nid, p_from)
            frame_pos[nid] = {
                "x": round(p_from["x"] + (p_to["x"] - p_from["x"]) * t, 2),
                "y": round(p_from["y"] + (p_to["y"] - p_from["y"]) * t, 2),
            }
        frames.append(frame_pos)

    return frames
