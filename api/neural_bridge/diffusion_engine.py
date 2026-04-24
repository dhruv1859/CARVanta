"""
CARVanta Neural Bridge — Influence Propagation & Diffusion Engine
==================================================================
Models how signals (drug targets, mutations, expression changes)
propagate through the knowledge graph.

Algorithms:
  ▸ Heat diffusion (Laplacian kernel)
  ▸ Random walk with restart (personalised PageRank)
  ▸ Susceptible-Infected-Recovered (SIR) epidemic model
  ▸ Network influence maximization (greedy + CELF)
  ▸ Cascade simulation for biological signal flow
  ▸ Diffusion distance computation
  ▸ Spreading activation for multi-hop reasoning

Biological applications:
  - Given a mutated gene, which pathways/diseases are "closest"
    to the perturbation?
  - If Antigen X is lost (antigen escape), which backup targets
    are in the influence zone?
  - Model how resistance mutations propagate through a pathway
    network.
"""

from __future__ import annotations

import math
import random
from collections import defaultdict, deque
from typing import Any, Dict, List, Optional, Set, Tuple


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
# Heat Diffusion
# ═══════════════════════════════════════════════════════════════════════════════

def heat_diffusion(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    seed_nodes: List[str],
    time_steps: int = 10,
    diffusion_rate: float = 0.3,
) -> Dict[str, Any]:
    """
    Simulate heat diffusion from seed nodes through the network.

    Each timestep, a fraction (diffusion_rate) of each node's heat
    is transferred equally to its neighbours.  Converges to the
    stationary distribution of a lazy random walk.

    Returns heat values per node after ``time_steps`` iterations.
    """
    adj = _adj(links)
    ids = [n["id"] for n in nodes]

    # Initial heat: 1.0 on seed nodes, 0 elsewhere
    heat: Dict[str, float] = {v: 0.0 for v in ids}
    for s in seed_nodes:
        if s in heat:
            heat[s] = 1.0

    history: List[Dict[str, float]] = [dict(heat)]

    for _t in range(time_steps):
        new_heat: Dict[str, float] = {v: 0.0 for v in ids}
        for v in ids:
            neighbours = adj.get(v, set())
            n_nb = len(neighbours)
            if n_nb == 0:
                new_heat[v] += heat[v]
                continue

            # Keep fraction
            kept = heat[v] * (1 - diffusion_rate)
            distributed = heat[v] * diffusion_rate / n_nb

            new_heat[v] += kept
            for nb in neighbours:
                if nb in new_heat:
                    new_heat[nb] += distributed

        heat = new_heat
        history.append(dict(heat))

    # Rank by final heat
    ranked = sorted(heat.items(), key=lambda x: x[1], reverse=True)

    return {
        "seed_nodes": seed_nodes,
        "time_steps": time_steps,
        "diffusion_rate": diffusion_rate,
        "final_heat": {k: round(v, 6) for k, v in ranked[:50]},
        "top_heated_nodes": [
            {"node": k, "heat": round(v, 6)} for k, v in ranked[:20]
        ],
        "history_length": len(history),
        "total_heat": round(sum(heat.values()), 4),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Random Walk with Restart (Personalised PageRank)
# ═══════════════════════════════════════════════════════════════════════════════

def random_walk_restart(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    seed_node: str,
    restart_prob: float = 0.15,
    max_iter: int = 50,
    tol: float = 1e-6,
) -> Dict[str, Any]:
    """
    Personalised PageRank from a seed node.

    At each step, with probability ``restart_prob`` the walker
    returns to the seed; otherwise it follows a random edge.

    Nodes with high PPR score are "functionally close" to the seed
    even if topologically distant.
    """
    adj = _adj(links)
    ids = [n["id"] for n in nodes]
    n = len(ids)
    if n == 0:
        return {"error": "No nodes"}

    # Uniform start
    ppr = {v: 0.0 for v in ids}
    ppr[seed_node] = 1.0

    for _ in range(max_iter):
        new_ppr: Dict[str, float] = {v: 0.0 for v in ids}

        for v in ids:
            nb = adj.get(v, set())
            out_deg = len(nb)
            if out_deg == 0:
                # Dangling: distribute to seed
                new_ppr[seed_node] += ppr[v]
                continue
            share = ppr[v] * (1 - restart_prob) / out_deg
            for u in nb:
                if u in new_ppr:
                    new_ppr[u] += share

        # Restart teleportation
        for v in ids:
            new_ppr[v] += restart_prob * (1.0 if v == seed_node else 0.0)

        # Convergence
        diff = sum(abs(new_ppr[v] - ppr[v]) for v in ids)
        ppr = new_ppr
        if diff < tol:
            break

    ranked = sorted(ppr.items(), key=lambda x: x[1], reverse=True)

    return {
        "seed_node": seed_node,
        "restart_prob": restart_prob,
        "top_related_nodes": [
            {"node": k, "proximity": round(v, 6)} for k, v in ranked[:25]
        ],
        "seed_score": round(ppr.get(seed_node, 0), 6),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# SIR Epidemic Model (Signal Propagation)
# ═══════════════════════════════════════════════════════════════════════════════

def sir_simulation(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    initial_infected: List[str],
    infection_rate: float = 0.3,
    recovery_rate: float = 0.1,
    max_steps: int = 30,
    n_simulations: int = 20,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    SIR model on the knowledge graph.

    Biologically: models how a perturbation (e.g., antigen escape
    mutation) spreads through connected pathways and diseases.

    Runs ``n_simulations`` stochastic simulations and averages.
    """
    adj = _adj(links)
    rng = random.Random(seed)
    ids = [n["id"] for n in nodes]
    id_set = set(ids)

    # Aggregate across simulations
    infection_freq: Dict[str, int] = defaultdict(int)
    avg_sir: List[Dict[str, int]] = []

    for _sim in range(n_simulations):
        S = set(ids) - set(initial_infected)
        I: Set[str] = set(initial_infected) & id_set
        R: Set[str] = set()

        timeline: List[Dict[str, int]] = []

        for step in range(max_steps):
            timeline.append({"step": step, "S": len(S), "I": len(I), "R": len(R)})

            if not I:
                break

            new_infected: Set[str] = set()
            new_recovered: Set[str] = set()

            for v in list(I):
                # Try to infect neighbours
                for nb in adj.get(v, set()):
                    if nb in S and rng.random() < infection_rate:
                        new_infected.add(nb)
                # Try to recover
                if rng.random() < recovery_rate:
                    new_recovered.add(v)

            S -= new_infected
            I = (I | new_infected) - new_recovered
            R |= new_recovered

        # Record final infected/recovered
        for v in R | I:
            infection_freq[v] += 1

        if _sim == 0:
            avg_sir = timeline

    # Compute infection probability per node
    infection_prob = {
        v: round(count / n_simulations, 3)
        for v, count in sorted(infection_freq.items(), key=lambda x: -x[1])
    }

    return {
        "initial_infected": initial_infected,
        "infection_rate": infection_rate,
        "recovery_rate": recovery_rate,
        "n_simulations": n_simulations,
        "timeline_sample": avg_sir[:max_steps],
        "infection_probability": dict(list(infection_prob.items())[:30]),
        "total_ever_infected": len(infection_prob),
        "avg_final_recovered_pct": round(
            sum(1 for v in infection_prob.values() if v > 0.5) / max(len(ids), 1) * 100, 1
        ),
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Influence Maximization (Greedy + CELF)
# ═══════════════════════════════════════════════════════════════════════════════

def influence_maximization(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    k: int = 5,
    infection_rate: float = 0.3,
    n_simulations: int = 10,
    seed: int = 42,
) -> Dict[str, Any]:
    """
    Find the top-k most influential seed nodes via greedy algorithm.

    Applications:
      - Which k antigens, if targeted together, would maximize
        disruption to cancer signalling networks?
      - Optimal combination therapy targets.
    """
    adj = _adj(links)
    rng = random.Random(seed)
    ids = [n["id"] for n in nodes]

    def _spread(seeds: Set[str]) -> float:
        """Estimate average spread from a seed set."""
        total = 0
        for _ in range(n_simulations):
            activated: Set[str] = set(seeds)
            frontier = set(seeds)
            while frontier:
                next_frontier: Set[str] = set()
                for v in frontier:
                    for nb in adj.get(v, set()):
                        if nb not in activated and rng.random() < infection_rate:
                            activated.add(nb)
                            next_frontier.add(nb)
                frontier = next_frontier
            total += len(activated)
        return total / n_simulations

    selected: List[str] = []
    remaining = set(ids)

    for _i in range(k):
        best_node = ""
        best_marginal = -1

        for candidate in list(remaining)[:100]:  # limit search for speed
            current_spread = _spread(set(selected) | {candidate})
            marginal = current_spread - _spread(set(selected)) if selected else current_spread
            if marginal > best_marginal:
                best_marginal = marginal
                best_node = candidate

        if best_node:
            selected.append(best_node)
            remaining.discard(best_node)

    total_influence = _spread(set(selected))

    return {
        "k": k,
        "seed_set": selected,
        "estimated_spread": round(total_influence, 1),
        "spread_fraction": round(total_influence / max(len(ids), 1), 4),
        "method": "greedy",
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Spreading Activation (Multi-hop Reasoning)
# ═══════════════════════════════════════════════════════════════════════════════

def spreading_activation(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    seed_nodes: Dict[str, float],
    decay: float = 0.7,
    threshold: float = 0.01,
    max_hops: int = 5,
) -> Dict[str, Any]:
    """
    Spreading activation from weighted seed nodes.

    Each hop, activation decays by ``decay`` factor and propagates
    to neighbours via edge weights.

    Seed nodes can have different initial activation levels
    (e.g., one antigen is primary target at 1.0, backup at 0.5).
    """
    wadj = _weighted_adj(links)
    ids = [n["id"] for n in nodes]

    activation: Dict[str, float] = {v: 0.0 for v in ids}
    for s, val in seed_nodes.items():
        if s in activation:
            activation[s] = val

    history = [dict(activation)]

    for hop in range(max_hops):
        new_activation: Dict[str, float] = {v: 0.0 for v in ids}

        for v in ids:
            if activation[v] < threshold:
                continue
            neighbours = wadj.get(v, {})
            for nb, weight in neighbours.items():
                if nb in new_activation:
                    spread = activation[v] * decay * weight
                    new_activation[nb] = max(new_activation[nb], spread)

        # Merge: keep max of current and new
        changed = False
        for v in ids:
            if new_activation[v] > activation[v]:
                activation[v] = new_activation[v]
                changed = True

        history.append(dict(activation))
        if not changed:
            break

    ranked = sorted(
        ((k, v) for k, v in activation.items() if v > threshold),
        key=lambda x: x[1], reverse=True,
    )

    return {
        "seed_nodes": seed_nodes,
        "decay": decay,
        "hops_executed": len(history) - 1,
        "activated_nodes": len(ranked),
        "top_activated": [
            {"node": k, "activation": round(v, 5)} for k, v in ranked[:25]
        ],
    }


# ═══════════════════════════════════════════════════════════════════════════════
# Diffusion Distance
# ═══════════════════════════════════════════════════════════════════════════════

def diffusion_distance(
    nodes: List[Dict[str, Any]],
    links: List[Dict[str, Any]],
    source: str,
    targets: Optional[List[str]] = None,
    time_steps: int = 10,
    diffusion_rate: float = 0.3,
) -> Dict[str, Any]:
    """
    Compute diffusion-based distance from source to targets.

    Diffusion distance captures functional proximity better than
    shortest-path distance because it considers ALL paths, not
    just the shortest one.
    """
    result = heat_diffusion(
        nodes, links, [source],
        time_steps=time_steps,
        diffusion_rate=diffusion_rate,
    )

    heat_map = result["final_heat"]

    if targets is None:
        targets = [n["id"] for n in nodes if n["id"] != source][:30]

    distances = []
    for t in targets:
        t_heat = heat_map.get(t, 0)
        # Distance is inverse of heat (higher heat = closer)
        dist = 1.0 / max(t_heat, 1e-8) if t_heat > 1e-8 else float("inf")
        distances.append({
            "target": t,
            "heat": round(t_heat, 8),
            "diffusion_distance": round(dist, 4) if dist < 1e6 else "unreachable",
        })

    distances.sort(key=lambda x: x["heat"], reverse=True)

    return {
        "source": source,
        "distances": distances[:30],
        "closest_by_diffusion": distances[0]["target"] if distances else None,
    }
