import React, { useState, useEffect, useRef } from 'react';
import ForceGraph3D from 'react-force-graph-3d';
import '../styles/war-game.css';

// Groups: 0 = Healthy, 1 = Tumor, 2 = CAR-T, 3 = Mutated (Escape Variant)
const COLOR_HEALTHY = '#10b981';
const COLOR_TUMOR   = '#ef4444';
const COLOR_CART    = '#06b6d4';
const COLOR_MUTATED = '#9f1239';

interface CellNode { id: string; group: number; val: number; }
interface CellLink { source: string; target: string; }
interface LogEntry { id: number; time: string; msg: string; type: 'tumor' | 'cart' | 'safety' | 'critical'; }

export default function WarGame() {
  const [nodes, setNodes]         = useState<CellNode[]>([]);
  const [links, setLinks]         = useState<CellLink[]>([]);
  const [isRunning, setIsRunning] = useState(false);
  const [cartDeployed, setCartDeployed] = useState(false);
  const [logs, setLogs]           = useState<LogEntry[]>([]);

  const [healthyCount, setHealthyCount] = useState(0);
  const [tumorCount,   setTumorCount]   = useState(0);
  const [cartCount,    setCartCount]    = useState(0);
  const [toxicityLevel, setToxicityLevel] = useState(0);

  // Track container size so ForceGraph3D fits exactly
  const containerRef = useRef<HTMLDivElement>(null);
  const [dims, setDims] = useState({ w: 800, h: 600 });

  const fgRef       = useRef<any>();
  const logCounter  = useRef(0);
  const linksRef    = useRef<CellLink[]>([]);
  linksRef.current  = links;

  // Measure container on mount and resize
  useEffect(() => {
    const el = containerRef.current;
    if (!el) return;
    const ro = new ResizeObserver(entries => {
      for (const entry of entries) {
        setDims({ w: entry.contentRect.width, h: entry.contentRect.height });
      }
    });
    ro.observe(el);
    // Initial measurement
    setDims({ w: el.clientWidth, h: el.clientHeight });
    return () => ro.disconnect();
  }, []);

  const addLog = (msg: string, type: LogEntry['type']) => {
    logCounter.current += 1;
    const now = new Date().toLocaleTimeString([], { hour12: false, hour: '2-digit', minute: '2-digit', second: '2-digit' });
    setLogs(prev => [{ id: logCounter.current, time: now, msg, type }, ...prev].slice(0, 60));
  };

  // Initialise environment
  useEffect(() => {
    const init: CellNode[] = [];
    for (let i = 0; i < 120; i++) init.push({ id: `h_${i}`, group: 0, val: 5 });
    for (let i = 0; i < 5;   i++) init.push({ id: `t_${i}`, group: 1, val: 18 });
    setNodes(init);
    addLog('Patient microenvironment initialised.', 'safety');
    addLog('Malignant neoplasm detected (5 cells).', 'tumor');
  }, []);

  // Live counters
  useEffect(() => {
    let h = 0, t = 0, c = 0;
    nodes.forEach(n => {
      if (n.group === 0) h++;
      if (n.group === 1 || n.group === 3) t++;
      if (n.group === 2) c++;
    });
    setHealthyCount(h);
    setTumorCount(t);
    setCartCount(c);
  }, [nodes]);

  // ── Simulation Loop ───────────────────────────────────────────────────────
  useEffect(() => {
    if (!isRunning) return;

    const interval = setInterval(() => {
      setNodes(prev => {
        const next = [...prev];
        let nextLinks = [...linksRef.current];

        // Agent 1 – Tumor: grow & mutate
        const tumors = next.filter(n => n.group === 1 || n.group === 3);
        if (tumors.length > 0 && tumors.length < 250) {
          if (Math.random() < 0.22) next.push({ id: `t_${Date.now()}_${Math.random()}`, group: 1, val: 18 });
          const rnd = tumors[Math.floor(Math.random() * tumors.length)];
          if (rnd.group === 1 && Math.random() < 0.03) {
            rnd.group = 3; rnd.val = 22;
            addLog('Tumor evolved — antigen downregulation escape!', 'tumor');
          }
        }

        // Agent 2 – CAR-T swarm
        if (cartDeployed) {
          const carts          = next.filter(n => n.group === 2);
          const vulnerable     = next.filter(n => n.group === 1);
          const healthyCells   = next.filter(n => n.group === 0);

          // Seek & latch
          carts.forEach(cart => {
            if (vulnerable.length > 0 && Math.random() < 0.25) {
              const tgt = vulnerable[Math.floor(Math.random() * vulnerable.length)];
              const exists = nextLinks.some(l => {
                const sid = typeof l.source === 'object' ? (l.source as any).id : l.source;
                const tid = typeof l.target === 'object' ? (l.target as any).id : l.target;
                return sid === cart.id && tid === tgt.id;
              });
              if (!exists) nextLinks.push({ source: cart.id, target: tgt.id });
            }
            // Off-target toxicity
            if (healthyCells.length > 0 && Math.random() < 0.018) {
              const tgt = healthyCells[Math.floor(Math.random() * healthyCells.length)];
              const idx = next.findIndex(n => n.id === tgt.id);
              if (idx !== -1) {
                next.splice(idx, 1);
                setToxicityLevel(p => Math.min(100, p + 4));
                addLog('⚠ Off-target toxicity — healthy tissue damaged!', 'critical');
              }
            }
          });

          // CAR-T proliferation
          if (carts.length > 0 && carts.length < 80 && Math.random() < 0.35)
            next.push({ id: `c_${Date.now()}_${Math.random()}`, group: 2, val: 12 });

          // Kill linked tumors
          let killed = 0;
          nextLinks = nextLinks.filter(l => {
            if (Math.random() < 0.25) {
              const tid = typeof l.target === 'object' ? (l.target as any).id : l.target;
              const idx = next.findIndex(n => n.id === tid);
              if (idx !== -1 && next[idx].group === 1) { next.splice(idx, 1); killed++; return false; }
            }
            return true;
          });

          // Prune dangling links
          nextLinks = nextLinks.filter(l => {
            const sid = typeof l.source === 'object' ? (l.source as any).id : l.source;
            const tid = typeof l.target === 'object' ? (l.target as any).id : l.target;
            return next.some(n => n.id === sid) && next.some(n => n.id === tid);
          });

          if (killed > 0) {
            setToxicityLevel(p => Math.min(100, p + killed));
            if (killed > 2) addLog(`CAR-T eliminated ${killed} tumour cells — IL-6 surge!`, 'cart');
          }
        }

        setLinks(nextLinks);
        return next;
      });
    }, 700);

    return () => clearInterval(interval);
  }, [isRunning, cartDeployed]);

  // ── Actions ───────────────────────────────────────────────────────────────
  const deployCART = () => {
    if (cartDeployed) return;
    addLog('Deploying CD19-targeted CAR-T swarm...', 'cart');
    setCartDeployed(true);
    setIsRunning(true);
    const swarm: CellNode[] = [];
    for (let i = 0; i < 20; i++) swarm.push({ id: `c_init_${i}`, group: 2, val: 12 });
    setNodes(prev => [...prev, ...swarm]);
  };

  const triggerKillSwitch = () => {
    addLog('EMERGENCY: Synthetic logic-gate kill-switch engaged!', 'critical');
    addLog('Apoptosis inducer administered — neutralising swarm...', 'safety');
    setNodes(prev => prev.filter(n => n.group !== 2));
    setLinks([]);
    setCartDeployed(false);
    setToxicityLevel(p => Math.max(0, p - 60));
    addLog('CAR-T swarm neutralised. CRS risk falling.', 'safety');
  };

  const resetSim = () => {
    setIsRunning(false);
    setCartDeployed(false);
    setLinks([]);
    setToxicityLevel(0);
    setLogs([]);
    const init: CellNode[] = [];
    for (let i = 0; i < 120; i++) init.push({ id: `h_${i}`, group: 0, val: 5 });
    for (let i = 0; i < 5;   i++) init.push({ id: `t_${i}`, group: 1, val: 18 });
    setNodes(init);
    addLog('Simulation reset. New patient environment ready.', 'safety');
  };

  const getNodeColor = (node: any) => {
    if (node.group === 0) return COLOR_HEALTHY;
    if (node.group === 1) return COLOR_TUMOR;
    if (node.group === 2) return COLOR_CART;
    if (node.group === 3) return COLOR_MUTATED;
    return '#ffffff';
  };

  return (
    <div className="wg-root">
      {/* Full-bleed 3D canvas */}
      <div ref={containerRef} className="wg-canvas-wrapper">
        {dims.w > 0 && (
          <ForceGraph3D
            ref={fgRef}
            width={dims.w}
            height={dims.h}
            graphData={{ nodes, links }}
            nodeLabel="id"
            nodeColor={getNodeColor}
            nodeVal="val"
            nodeRelSize={5}
            nodeResolution={12}
            linkColor={() => 'rgba(255,255,255,0.5)'}
            linkWidth={1.5}
            linkOpacity={0.6}
            linkDirectionalParticles={4}
            linkDirectionalParticleWidth={3}
            linkDirectionalParticleSpeed={0.012}
            backgroundColor="#030712"
          />
        )}
      </div>

      {/* HUD Overlay — sits on top of canvas, pointer-events only on panels */}
      <div className="wg-overlay">

        {/* ── TOP ROW ── */}
        <div className="wg-top-row">

          {/* Left: Title + stats + controls */}
          <div className="wg-hud-panel wg-main-hud">
            <div>
              <h1 className="wg-title">In Silico Simulator</h1>
              <p className="wg-subtitle">Multi-Agent Tumour Evolution War-Game</p>
            </div>

            <div className="wg-stats-grid">
              <div className="wg-stat-box">
                <div className="wg-stat-label">Tumour Burden</div>
                <div className="wg-stat-value tumor">{tumorCount}</div>
              </div>
              <div className="wg-stat-box">
                <div className="wg-stat-label">CAR-T Swarm</div>
                <div className="wg-stat-value cart">{cartCount}</div>
              </div>
              <div className="wg-stat-box">
                <div className="wg-stat-label">Healthy Tissue</div>
                <div className="wg-stat-value healthy">{healthyCount}</div>
              </div>
            </div>

            <div className="wg-legend">
              <span className="wg-legend-item"><span className="wg-dot" style={{ background: COLOR_HEALTHY }} /> Healthy</span>
              <span className="wg-legend-item"><span className="wg-dot" style={{ background: COLOR_TUMOR }} /> Tumour</span>
              <span className="wg-legend-item"><span className="wg-dot" style={{ background: COLOR_CART }} /> CAR-T</span>
              <span className="wg-legend-item"><span className="wg-dot" style={{ background: COLOR_MUTATED }} /> Mutated</span>
            </div>

            <div className="wg-controls">
              <button className="wg-btn primary" onClick={() => setIsRunning(r => !r)}>
                {isRunning ? '⏸ Pause' : '▶ Run Sim'}
              </button>
              <button className="wg-btn success" onClick={deployCART} disabled={cartDeployed} style={{ opacity: cartDeployed ? 0.5 : 1 }}>
                💉 Deploy CAR-T
              </button>
              <button className="wg-btn ghost" onClick={resetSim}>↺ Reset</button>
            </div>
          </div>

          {/* Right: Safety Monitor */}
          <div className={`wg-hud-panel wg-safety-hud ${toxicityLevel >= 70 ? 'critical' : ''}`}>
            <h3 className="wg-safety-title">🛡 Safety Monitor Agent</h3>
            <div className="wg-safety-label">IL-6 Cytokine / CRS Risk Index</div>

            <div className="wg-bar-track">
              <div
                className={`wg-bar-fill ${toxicityLevel >= 70 ? 'danger' : toxicityLevel >= 40 ? 'warn' : ''}`}
                style={{ width: `${toxicityLevel}%` }}
              />
            </div>
            <div className="wg-bar-meta">
              <span>Stable</span>
              <span style={{ color: toxicityLevel >= 70 ? '#ef4444' : toxicityLevel >= 40 ? '#eab308' : '#10b981' }}>
                {toxicityLevel}%
              </span>
            </div>

            <div className="wg-agent-list">
              <div className="wg-agent-row"><span className="wg-dot" style={{ background: COLOR_TUMOR }} /> Agent 1 — Tumour (Adaptive)</div>
              <div className="wg-agent-row"><span className="wg-dot" style={{ background: COLOR_CART }} /> Agent 2 — CAR-T Swarm</div>
              <div className="wg-agent-row"><span className="wg-dot" style={{ background: '#eab308' }} /> Agent 3 — Safety Monitor</div>
            </div>

            {toxicityLevel >= 40 && (
              <button className="wg-btn danger" style={{ width: '100%', marginTop: '14px' }} onClick={triggerKillSwitch}>
                ⚠ ACTIVATE KILL SWITCH
              </button>
            )}
          </div>
        </div>

        {/* ── BOTTOM ROW ── */}
        <div className="wg-bottom-row">
          <div className="wg-hud-panel wg-terminal">
            <div className="wg-terminal-title">Sim-Terminal v4.2.1</div>
            <div className="wg-terminal-body">
              {logs.map(log => (
                <div key={log.id} className={`wg-log ${log.type}`}>
                  <span className="wg-log-ts">[{log.time}]</span> {log.msg}
                </div>
              ))}
            </div>
          </div>
        </div>

      </div>
    </div>
  );
}
