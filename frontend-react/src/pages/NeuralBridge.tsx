import React, { useEffect, useState, useRef, useCallback, useMemo } from 'react';
import ForceGraph3D from 'react-force-graph-3d';
import SpriteText from 'three-spritetext';
import api from '../api/client';

/* ─── Types ──────────────────────────────────────────────────────────── */
interface GraphNode {
  id: string; name: string; group: string; layer: string;
  val: number; score?: number; cluster_id?: number;
  druggability?: string; gene_family?: string;
  x?: number; y?: number; z?: number;
  __threeObj?: any;
}
interface GraphLink {
  source: string | any; target: string | any;
  relationship: string; weight: number;
}

/* ─── Colour palette ─────────────────────────────────────────────────── */
const GROUP_COLORS: Record<string, string> = {
  Disease: '#FF6B6B',
  Pathway: '#4ECDC4',
  Antigen: '#45B7D1',
  GeneFamily: '#96CEB4',
  ProteinDomain: '#DDA0DD',
};

const GLOW: Record<string, string> = {
  Disease: '#ff3a3a',
  Pathway: '#00f5e9',
  Antigen: '#00bfff',
  GeneFamily: '#5ddb8e',
  ProteinDomain: '#c97eff',
};

/* ─── Main Component ─────────────────────────────────────────────────── */
export default function NeuralBridge() {
  const fgRef = useRef<any>(null);
  const [graphData, setGraphData] = useState<{ nodes: GraphNode[]; links: GraphLink[] }>({ nodes: [], links: [] });
  const [loading, setLoading] = useState(true);
  const [selectedNode, setSelectedNode] = useState<GraphNode | null>(null);
  const [filterGroup, setFilterGroup] = useState('');
  const [searchQ, setSearchQ] = useState('');
  const [highlightIds, setHighlightIds] = useState<Set<string>>(new Set());
  const [neighborIds, setNeighborIds] = useState<Set<string>>(new Set());
  const [graphStats, setGraphStats] = useState<any>(null);
  const [similarNodes, setSimilarNodes] = useState<any[]>([]);
  const [panelTab, setPanelTab] = useState<'connections' | 'similar' | 'info'>('connections');

  /* ── Full replica of backend KnowledgeGraphBuilder schema ───────────── */
  const DEMO = useMemo(() => {
    // ── Constants (mirrors graph_builder.py exactly) ──────────────────
    const PATHWAYS = ['PI3K-AKT','MAPK','JAK-STAT','NF-kB','Wnt','Notch','Hedgehog','TGF-beta','RTK-RAS','TP53','Hippo','mTOR','VEGF','EGFR','HER2-neu','BCR-ABL','FLT3','PDGFR','MET','ALK'];
    const GENE_FAMILIES = ['Immunoglobulin Superfamily','Receptor Tyrosine Kinases','G-Protein Coupled Receptors','Tumour Necrosis Factor Receptors','Claudins','Mucins','Cadherins','Integrins','Tetraspanins','GPI-Anchored Proteins','Carcinoembryonic Antigen Family','Selectins','Protocadherins','Ephrins'];
    const PROTEIN_DOMAINS = ['Extracellular Domain','Transmembrane Domain','Intracellular Domain','Signal Peptide','EGF-like Domain','Fibronectin Type III','Leucine-Rich Repeat','C2-type Ig Domain','V-type Ig Domain','ITIM Motif','Scavenger Receptor Domain','Sushi Domain'];


    const CANCERS = [
      {id:'dlbcl',name:'DLBCL',approved:true},
      {id:'all',name:'Acute Lymphoblastic Leukemia',approved:true},
      {id:'multiple_myeloma',name:'Multiple Myeloma',approved:true},
      {id:'mantle_cell',name:'Mantle Cell Lymphoma',approved:true},
      {id:'aml',name:'Acute Myeloid Leukemia',approved:false},
      {id:'cll',name:'Chronic Lymphocytic Leukemia',approved:false},
      {id:'glioblastoma',name:'Glioblastoma',approved:false},
      {id:'lung_adenocarcinoma',name:'Lung Adenocarcinoma',approved:false},
      {id:'breast_cancer',name:'Breast Cancer',approved:false},
      {id:'ovarian_cancer',name:'Ovarian Cancer',approved:false},
      {id:'colorectal',name:'Colorectal Cancer',approved:false},
      {id:'melanoma',name:'Melanoma',approved:false},
      {id:'pancreatic',name:'Pancreatic Cancer',approved:false},
      {id:'prostate',name:'Prostate Cancer',approved:false},
      {id:'hepatocellular',name:'Hepatocellular Carcinoma',approved:false},
      {id:'gastric',name:'Gastric Cancer',approved:false},
      {id:'bladder',name:'Bladder Cancer',approved:false},
      {id:'cervical',name:'Cervical Cancer',approved:false},
      {id:'thyroid',name:'Thyroid Cancer',approved:false},
      {id:'renal_cell',name:'Renal Cell Carcinoma',approved:false},
    ];

    // 80 real CAR-T / oncology antigens covering all cancer types
    const ANTIGENS: {name:string; cancer:string; drug:string; score:number; tier:string}[] = [
      {name:'CD19',cancer:'dlbcl',drug:'CAR-T Target',score:0.97,tier:'validated'},
      {name:'CD22',cancer:'all',drug:'ADC Target',score:0.91,tier:'validated'},
      {name:'CD20',cancer:'dlbcl',drug:'Checkpoint Blockade',score:0.94,tier:'validated'},
      {name:'BCMA',cancer:'multiple_myeloma',drug:'CAR-T Target',score:0.96,tier:'validated'},
      {name:'CD38',cancer:'multiple_myeloma',drug:'CAR-T Target',score:0.89,tier:'validated'},
      {name:'SLAMF7',cancer:'multiple_myeloma',drug:'Checkpoint Blockade',score:0.84,tier:'clinical'},
      {name:'CD33',cancer:'aml',drug:'ADC Target',score:0.88,tier:'validated'},
      {name:'FLT3',cancer:'aml',drug:'CAR-T Target',score:0.82,tier:'clinical'},
      {name:'CD123',cancer:'aml',drug:'BiTE Target',score:0.79,tier:'clinical'},
      {name:'CLL-1',cancer:'aml',drug:'CAR-T Target',score:0.76,tier:'predicted'},
      {name:'CD5',cancer:'cll',drug:'BiTE Target',score:0.73,tier:'clinical'},
      {name:'ROR1',cancer:'cll',drug:'CAR-T Target',score:0.81,tier:'clinical'},
      {name:'CD37',cancer:'cll',drug:'ADC Target',score:0.69,tier:'predicted'},
      {name:'HER2',cancer:'breast_cancer',drug:'ADC Target',score:0.95,tier:'validated'},
      {name:'HER3',cancer:'breast_cancer',drug:'ADC Target',score:0.78,tier:'clinical'},
      {name:'TROP2',cancer:'breast_cancer',drug:'ADC Target',score:0.86,tier:'validated'},
      {name:'ROR2',cancer:'breast_cancer',drug:'CAR-T Target',score:0.67,tier:'predicted'},
      {name:'MSLN',cancer:'ovarian_cancer',drug:'CAR-T Target',score:0.85,tier:'clinical'},
      {name:'MUC16',cancer:'ovarian_cancer',drug:'ADC Target',score:0.77,tier:'clinical'},
      {name:'FRα',cancer:'ovarian_cancer',drug:'ADC Target',score:0.82,tier:'validated'},
      {name:'GD2',cancer:'melanoma',drug:'CAR-T Target',score:0.90,tier:'validated'},
      {name:'CSPG4',cancer:'melanoma',drug:'CAR-T Target',score:0.71,tier:'clinical'},
      {name:'gp100',cancer:'melanoma',drug:'Vaccine Antigen',score:0.68,tier:'clinical'},
      {name:'MAGE-A3',cancer:'melanoma',drug:'Vaccine Antigen',score:0.72,tier:'clinical'},
      {name:'EGFR',cancer:'lung_adenocarcinoma',drug:'Small Molecule',score:0.93,tier:'validated'},
      {name:'ALK',cancer:'lung_adenocarcinoma',drug:'Small Molecule',score:0.89,tier:'validated'},
      {name:'MET',cancer:'lung_adenocarcinoma',drug:'ADC Target',score:0.74,tier:'clinical'},
      {name:'ROS1',cancer:'lung_adenocarcinoma',drug:'Small Molecule',score:0.77,tier:'validated'},
      {name:'KRAS',cancer:'lung_adenocarcinoma',drug:'Small Molecule',score:0.71,tier:'validated'},
      {name:'EGFRvIII',cancer:'glioblastoma',drug:'CAR-T Target',score:0.79,tier:'clinical'},
      {name:'IL13Rα2',cancer:'glioblastoma',drug:'CAR-T Target',score:0.75,tier:'clinical'},
      {name:'GPC2',cancer:'glioblastoma',drug:'CAR-T Target',score:0.66,tier:'predicted'},
      {name:'B7-H3',cancer:'glioblastoma',drug:'Checkpoint Blockade',score:0.70,tier:'clinical'},
      {name:'CEA',cancer:'colorectal',drug:'ADC Target',score:0.83,tier:'validated'},
      {name:'GUCY2C',cancer:'colorectal',drug:'CAR-T Target',score:0.74,tier:'clinical'},
      {name:'EpCAM',cancer:'colorectal',drug:'BiTE Target',score:0.80,tier:'validated'},
      {name:'TAG-72',cancer:'colorectal',drug:'ADC Target',score:0.65,tier:'clinical'},
      {name:'GPC3',cancer:'hepatocellular',drug:'CAR-T Target',score:0.84,tier:'clinical'},
      {name:'AFP',cancer:'hepatocellular',drug:'Vaccine Antigen',score:0.71,tier:'predicted'},
      {name:'PSMA',cancer:'prostate',drug:'ADC Target',score:0.92,tier:'validated'},
      {name:'STEAP1',cancer:'prostate',drug:'ADC Target',score:0.76,tier:'clinical'},
      {name:'PSCMA',cancer:'prostate',drug:'CAR-T Target',score:0.69,tier:'predicted'},
      {name:'MUC1',cancer:'pancreatic',drug:'CAR-T Target',score:0.77,tier:'clinical'},
      {name:'MSLN',cancer:'pancreatic',drug:'ADC Target',score:0.81,tier:'clinical'},
      {name:'HER2',cancer:'gastric',drug:'ADC Target',score:0.88,tier:'validated'},
      {name:'CLDN18.2',cancer:'gastric',drug:'CAR-T Target',score:0.83,tier:'clinical'},
      {name:'FGFR2',cancer:'gastric',drug:'ADC Target',score:0.71,tier:'clinical'},
      {name:'CD70',cancer:'renal_cell',drug:'CAR-T Target',score:0.73,tier:'clinical'},
      {name:'CA9',cancer:'renal_cell',drug:'ADC Target',score:0.68,tier:'predicted'},
      {name:'NECTIN4',cancer:'bladder',drug:'ADC Target',score:0.86,tier:'validated'},
      {name:'CD155',cancer:'bladder',drug:'Checkpoint Blockade',score:0.69,tier:'predicted'},
      {name:'HER2',cancer:'cervical',drug:'ADC Target',score:0.77,tier:'predicted'},
      {name:'TROP2',cancer:'cervical',drug:'ADC Target',score:0.72,tier:'clinical'},
      {name:'TSHR',cancer:'thyroid',drug:'CAR-T Target',score:0.65,tier:'predicted'},
      {name:'CD30',cancer:'mantle_cell',drug:'ADC Target',score:0.87,tier:'validated'},
      {name:'CD79b',cancer:'dlbcl',drug:'ADC Target',score:0.84,tier:'validated'},
      {name:'CD47',cancer:'aml',drug:'Checkpoint Blockade',score:0.75,tier:'clinical'},
      {name:'TIM-3',cancer:'aml',drug:'Checkpoint Blockade',score:0.68,tier:'clinical'},
      {name:'PD-L1',cancer:'lung_adenocarcinoma',drug:'Checkpoint Blockade',score:0.91,tier:'validated'},
      {name:'CTLA-4',cancer:'melanoma',drug:'Checkpoint Blockade',score:0.87,tier:'validated'},
      {name:'LAG-3',cancer:'melanoma',drug:'Checkpoint Blockade',score:0.74,tier:'clinical'},
      {name:'TIGIT',cancer:'lung_adenocarcinoma',drug:'Checkpoint Blockade',score:0.70,tier:'clinical'},
      {name:'NKG2D-L',cancer:'aml',drug:'CAR-T Target',score:0.72,tier:'predicted'},
      {name:'CS1',cancer:'multiple_myeloma',drug:'CAR-T Target',score:0.83,tier:'clinical'},
      {name:'GPRC5D',cancer:'multiple_myeloma',drug:'BiTE Target',score:0.88,tier:'clinical'},
      {name:'FcRH5',cancer:'multiple_myeloma',drug:'BiTE Target',score:0.80,tier:'clinical'},
      {name:'DLL3',cancer:'glioblastoma',drug:'ADC Target',score:0.77,tier:'clinical'},
      {name:'ROBO1',cancer:'pancreatic',drug:'CAR-T Target',score:0.64,tier:'predicted'},
      {name:'Trop2',cancer:'bladder',drug:'ADC Target',score:0.81,tier:'validated'},
      {name:'AXL',cancer:'lung_adenocarcinoma',drug:'ADC Target',score:0.69,tier:'predicted'},
      {name:'Mucin-17',cancer:'gastric',drug:'CAR-T Target',score:0.62,tier:'predicted'},
      {name:'HER2',cancer:'lung_adenocarcinoma',drug:'ADC Target',score:0.79,tier:'clinical'},
      {name:'CD44v6',cancer:'aml',drug:'ADC Target',score:0.73,tier:'clinical'},
      {name:'LMP1',cancer:'dlbcl',drug:'CAR-T Target',score:0.68,tier:'predicted'},
      {name:'CD10',cancer:'all',drug:'BiTE Target',score:0.71,tier:'clinical'},
      {name:'CXCR4',cancer:'multiple_myeloma',drug:'CAR-T Target',score:0.66,tier:'predicted'},
      {name:'Ly6E',cancer:'breast_cancer',drug:'ADC Target',score:0.75,tier:'clinical'},
      {name:'PTK7',cancer:'breast_cancer',drug:'ADC Target',score:0.70,tier:'predicted'},
    ];

    // ── Deterministic hash (same as Python _stable_float) ──────────────
    const stableFloat = (key: string, lo=0, hi=1) => {
      let h = 0; for (let i=0;i<key.length;i++) h=(Math.imul(31,h)+key.charCodeAt(i))|0;
      return lo + (Math.abs(h) / 2147483647) * (hi - lo);
    };
    const stableIdx = (key: string, arr: any[]) => Math.abs(Array.from(key).reduce((h,c)=>(Math.imul(31,h)+c.charCodeAt(0))|0,0)) % arr.length;

    // ── Build nodes ────────────────────────────────────────────────────
    const nodes: GraphNode[] = [];

    // Disease nodes (layer: clinical)
    CANCERS.forEach(c => nodes.push({
      id: `disease_${c.id}`, name: c.name, group: 'Disease', layer: 'clinical',
      val: 14, score: stableFloat(c.id+'score', 0.6, 0.99),
      druggability: c.approved ? 'CAR-T Target' : undefined,
    }));

    // Pathway nodes (layer: biological)
    PATHWAYS.forEach(p => nodes.push({
      id: `pathway_${p}`, name: `${p} Signaling`, group: 'Pathway', layer: 'biological',
      val: 9, score: stableFloat(p+'pw', 0.45, 0.9),
    }));

    // Gene family nodes (layer: biological)
    GENE_FAMILIES.forEach(gf => nodes.push({
      id: `family_${gf.replace(/ /g,'_').toLowerCase()}`, name: gf, group: 'GeneFamily', layer: 'biological',
      val: 7, score: stableFloat(gf+'fam', 0.4, 0.85),
    }));

    // Protein domain nodes (layer: biological)
    PROTEIN_DOMAINS.forEach(dom => nodes.push({
      id: `domain_${dom.replace(/ /g,'_').toLowerCase()}`, name: dom, group: 'ProteinDomain', layer: 'structural',
      val: 6, score: stableFloat(dom+'dom', 0.3, 0.8),
    }));

    // Antigen nodes (layer: omics)
    ANTIGENS.forEach(ag => nodes.push({
      id: `antigen_${ag.name}_${ag.cancer}`, name: ag.name, group: 'Antigen', layer: 'omics',
      val: Math.max(4, Math.round(ag.score * 12)),
      score: ag.score,
      druggability: ag.drug,
      gene_family: GENE_FAMILIES[stableIdx(ag.name+'fam', GENE_FAMILIES)],
    }));

    // ── Build edges (mirrors 7 edge types from graph_builder.py) ───────
    const links: GraphLink[] = [];

    // 1. expressed_in: antigen ↔ disease
    ANTIGENS.forEach(ag => {
      links.push({ source:`antigen_${ag.name}_${ag.cancer}`, target:`disease_${ag.cancer}`, relationship:'expressed_in', weight:ag.score });
    });

    // 2. involved_in: antigen ↔ pathway (primary + sometimes secondary)
    ANTIGENS.forEach(ag => {
      const pw = PATHWAYS[stableIdx(ag.name+'pw', PATHWAYS)];
      links.push({ source:`antigen_${ag.name}_${ag.cancer}`, target:`pathway_${pw}`, relationship:'involved_in', weight:stableFloat(ag.name+'pw_w',0.3,0.95) });
      if (stableFloat(ag.name+'pw2',0,1) > 0.6) {
        const pw2 = PATHWAYS[stableIdx(ag.name+'pw2_sel', PATHWAYS)];
        if (pw2 !== pw) links.push({ source:`antigen_${ag.name}_${ag.cancer}`, target:`pathway_${pw2}`, relationship:'involved_in', weight:stableFloat(ag.name+'pw2_w',0.2,0.7) });
      }
    });

    // 3. belongs_to: antigen ↔ gene family
    ANTIGENS.forEach(ag => {
      const gf = GENE_FAMILIES[stableIdx(ag.name+'fam', GENE_FAMILIES)];
      links.push({ source:`antigen_${ag.name}_${ag.cancer}`, target:`family_${gf.replace(/ /g,'_').toLowerCase()}`, relationship:'belongs_to', weight:1.0 });
    });

    // 4. has_domain: antigen ↔ protein domain
    ANTIGENS.forEach(ag => {
      const dom = PROTEIN_DOMAINS[stableIdx(ag.name+'dom', PROTEIN_DOMAINS)];
      links.push({ source:`antigen_${ag.name}_${ag.cancer}`, target:`domain_${dom.replace(/ /g,'_').toLowerCase()}`, relationship:'has_domain', weight:1.0 });
    });

    // 5. co_expressed: antigen ↔ antigen (same cancer, top pairs)
    const byCancer: Record<string,string[]> = {};
    ANTIGENS.forEach(ag => { const k=ag.cancer; if(!byCancer[k]) byCancer[k]=[]; byCancer[k].push(`antigen_${ag.name}_${ag.cancer}`); });
    Object.values(byCancer).forEach(ags => {
      for(let i=0;i<Math.min(ags.length,6);i++) for(let j=i+1;j<Math.min(ags.length,6);j++)
        links.push({ source:ags[i], target:ags[j], relationship:'co_expressed', weight:stableFloat(ags[i]+ags[j]+'coex',0.3,0.9) });
    });

    // 6. pathway_crosstalk: pathway ↔ pathway (known oncology links)
    const CROSSTALKS:[string,string][] = [
      ['PI3K-AKT','MAPK'],['PI3K-AKT','mTOR'],['MAPK','RTK-RAS'],['JAK-STAT','PI3K-AKT'],
      ['NF-kB','JAK-STAT'],['Wnt','Notch'],['Wnt','Hedgehog'],['TGF-beta','MAPK'],
      ['VEGF','PI3K-AKT'],['EGFR','MAPK'],['EGFR','PI3K-AKT'],['HER2-neu','MAPK'],
      ['HER2-neu','PI3K-AKT'],['TP53','mTOR'],['MET','RTK-RAS'],['ALK','MAPK'],
      ['FLT3','JAK-STAT'],['PDGFR','PI3K-AKT'],['Hippo','Wnt'],['BCR-ABL','JAK-STAT'],
    ];
    CROSSTALKS.forEach(([p1,p2]) => links.push({ source:`pathway_${p1}`, target:`pathway_${p2}`, relationship:'pathway_crosstalk', weight:stableFloat(p1+p2+'xtalk',0.5,1.0) }));

    return { nodes, links };
  }, []);

  /* Load graph */
  const [isLiveData, setIsLiveData] = useState(false);
  useEffect(() => {
    api.get('/api/v5/bridge/graph')
      .then(r => {
        const d = r.data?.data;
        if (d && d.nodes?.length > 0) {
          setGraphData(d);
          if (r.data?.metadata) setGraphStats(r.data.metadata);
          setIsLiveData(true);
        } else {
          setGraphData(DEMO);
        }
      })
      .catch(() => setGraphData(DEMO))
      .finally(() => setLoading(false));
  }, [DEMO]);

  /* Local similar-node fallback (used when backend offline) */
  const getLocalSimilar = useCallback((node: GraphNode): any[] => {
    // Find nodes that share the same group, layer, or are connected via the same pathway/disease
    const sid = node.id;
    const connectedIds = new Set<string>();
    graphData.links.forEach(l => {
      const s = typeof l.source === 'object' ? l.source.id : l.source;
      const t = typeof l.target === 'object' ? l.target.id : l.target;
      if (s === sid) connectedIds.add(t);
      if (t === sid) connectedIds.add(s);
    });
    // Find nodes that share ≥1 common neighbour and same group
    const candidates: Record<string, { node: GraphNode; shared: number }> = {};
    graphData.nodes.forEach(n => {
      if (n.id === sid || n.group !== node.group) return;
      let shared = 0;
      graphData.links.forEach(l => {
        const s = typeof l.source === 'object' ? l.source.id : l.source;
        const t = typeof l.target === 'object' ? l.target.id : l.target;
        if ((s === n.id && connectedIds.has(t)) || (t === n.id && connectedIds.has(s))) shared++;
      });
      if (shared > 0) candidates[n.id] = { node: n, shared };
    });
    return Object.values(candidates)
      .sort((a, b) => b.shared - a.shared)
      .slice(0, 8)
      .map(({ node: n, shared }) => ({
        name: n.name, group: n.group,
        node_id: n.id,
        signals: { ensemble: Math.min(0.99, shared * 0.18 + (n.score || 0.5) * 0.4), jaccard: shared * 0.12 },
      }));
  }, [graphData]);

  /* Filtered graph */
  const filteredData = useMemo(() => {
    let nodes = graphData.nodes;
    if (filterGroup) nodes = nodes.filter(n => n.group === filterGroup);
    if (searchQ) {
      const q = searchQ.toLowerCase();
      nodes = nodes.filter(n => n.name?.toLowerCase().includes(q));
    }
    const ids = new Set(nodes.map(n => n.id));
    const links = graphData.links.filter(l => {
      const s = typeof l.source === 'object' ? l.source.id : l.source;
      const t = typeof l.target === 'object' ? l.target.id : l.target;
      return ids.has(s) && ids.has(t);
    });
    return { nodes, links };
  }, [graphData, filterGroup, searchQ]);

  /* Neighbours of selected node */
  const neighborData = useMemo(() => {
    if (!selectedNode) return { nodes: [], links: [] };
    const sid = selectedNode.id;
    const connLinks = graphData.links.filter(l => {
      const s = typeof l.source === 'object' ? l.source.id : l.source;
      const t = typeof l.target === 'object' ? l.target.id : l.target;
      return s === sid || t === sid;
    });
    const nids = new Set<string>();
    connLinks.forEach(l => {
      const s = typeof l.source === 'object' ? l.source.id : l.source;
      const t = typeof l.target === 'object' ? l.target.id : l.target;
      nids.add(s); nids.add(t);
    });
    const connNodes = graphData.nodes.filter(n => nids.has(n.id));
    return { nodes: connNodes, links: connLinks };
  }, [selectedNode, graphData]);

  /* Group connections of selected node for display */
  const groupedNeighbors = useMemo(() => {
    const groups: Record<string, GraphNode[]> = {};
    neighborData.nodes.forEach(n => {
      if (n.id === selectedNode?.id) return;
      if (!groups[n.group]) groups[n.group] = [];
      groups[n.group].push(n);
    });
    return groups;
  }, [neighborData, selectedNode]);

  /* Handle node click → zoom + highlight */
  const handleNodeClick = useCallback(async (node: GraphNode) => {
    setSelectedNode(node);
    setPanelTab('connections');

    // Collect neighbor IDs for highlight
    const sid = node.id;
    const nids = new Set<string>([sid]);
    graphData.links.forEach(l => {
      const s = typeof l.source === 'object' ? l.source.id : l.source;
      const t = typeof l.target === 'object' ? l.target.id : l.target;
      if (s === sid) nids.add(t);
      if (t === sid) nids.add(s);
    });
    setNeighborIds(nids);
    setHighlightIds(new Set([sid]));

    // Zoom camera to node
    if (fgRef.current && node.x !== undefined) {
      const dist = 120;
      const distRatio = 1 + dist / Math.hypot(node.x ?? 1, node.y ?? 1, node.z ?? 1);
      fgRef.current.cameraPosition(
        { x: (node.x ?? 0) * distRatio, y: (node.y ?? 0) * distRatio, z: (node.z ?? 0) * distRatio },
        { x: node.x ?? 0, y: node.y ?? 0, z: node.z ?? 0 },
        1200
      );
    }

    // Load similar nodes — fall back to local computation if API offline
    try {
      const r = await api.get(`/api/v5/bridge/similar/${sid}`);
      const recs = r.data?.recommendations || [];
      setSimilarNodes(recs.length > 0 ? recs : getLocalSimilar(node));
    } catch { setSimilarNodes(getLocalSimilar(node)); }
  }, [graphData, getLocalSimilar]);

  /* Node colour & size */
  const getNodeColor = useCallback((node: GraphNode) => {
    if (highlightIds.has(node.id)) return '#FFD700';
    if (neighborIds.size > 0 && !neighborIds.has(node.id)) return '#1a1a2e';
    return GROUP_COLORS[node.group] || '#85929E';
  }, [highlightIds, neighborIds]);

  const getNodeVal = useCallback((node: GraphNode) => {
    if (highlightIds.has(node.id)) return (node.val || 5) * 2.5;
    if (neighborIds.size > 0 && neighborIds.has(node.id)) return (node.val || 5) * 1.4;
    return node.val || 5;
  }, [highlightIds, neighborIds]);

  /* Link colour */
  const getLinkColor = useCallback((link: GraphLink) => {
    const s = typeof link.source === 'object' ? link.source.id : link.source;
    const t = typeof link.target === 'object' ? link.target.id : link.target;
    if (neighborIds.size > 0 && (neighborIds.has(s) && neighborIds.has(t))) return '#4ECDC4cc';
    return '#ffffff08';
  }, [neighborIds]);

  /* Close panel */
  const closePanel = () => {
    setSelectedNode(null);
    setHighlightIds(new Set());
    setNeighborIds(new Set());
    setSimilarNodes([]);
    if (fgRef.current) fgRef.current.cameraPosition({ x: 0, y: 0, z: 500 }, { x: 0, y: 0, z: 0 }, 1000);
  };

  /* Loading */
  if (loading) {
    return (
      <div style={{ display: 'flex', alignItems: 'center', justifyContent: 'center', height: '100vh', background: '#050510', color: '#fff', flexDirection: 'column', gap: 16 }}>
        <div style={{ width: 56, height: 56, border: '3px solid transparent', borderTop: '3px solid #4ECDC4', borderRight: '3px solid #6366f1', borderRadius: '50%', animation: 'spin 0.8s linear infinite' }} />
        <p style={{ color: '#4ECDC4', letterSpacing: 3, fontSize: 13, fontFamily: 'Inter, sans-serif' }}>INITIALIZING NEURAL BRIDGE</p>
        <style>{`@keyframes spin { to { transform: rotate(360deg); } }`}</style>
      </div>
    );
  }

  return (
    <div style={{ display: 'flex', flexDirection: 'column', height: '100vh', background: '#050510', color: '#fff', fontFamily: 'Inter, system-ui, sans-serif', overflow: 'hidden' }}>

      {/* ── Header ── */}
      <div style={{ padding: '12px 20px', borderBottom: '1px solid rgba(255,255,255,0.06)', display: 'flex', justifyContent: 'space-between', alignItems: 'center', background: 'rgba(5,5,16,0.9)', backdropFilter: 'blur(16px)', zIndex: 10, flexShrink: 0 }}>
        <div style={{ display: 'flex', alignItems: 'center', gap: 20 }}>
          <div>
            <div style={{ display: 'flex', alignItems: 'center', gap: 10 }}>
              <h1 style={{ margin: 0, fontSize: 18, fontWeight: 800, background: 'linear-gradient(135deg, #4ECDC4, #45B7D1, #6366f1)', WebkitBackgroundClip: 'text', WebkitTextFillColor: 'transparent' }}>
                Neural Network Bridge
              </h1>
              {isLiveData ? (
                <span style={{ background: 'rgba(78,205,196,0.15)', border: '1px solid rgba(78,205,196,0.35)', borderRadius: 20, padding: '2px 10px', fontSize: 10, color: '#4ECDC4', fontWeight: 700, letterSpacing: 0.5, display: 'flex', alignItems: 'center', gap: 4 }}>
                  <span style={{ width: 6, height: 6, borderRadius: '50%', background: '#4ECDC4', boxShadow: '0 0 6px #4ECDC4', display: 'inline-block', animation: 'pulse 2s infinite' }} />
                  LIVE
                </span>
              ) : (
                <span style={{ background: 'rgba(255,234,167,0.1)', border: '1px solid rgba(255,234,167,0.25)', borderRadius: 20, padding: '2px 10px', fontSize: 10, color: '#FFEAA7', fontWeight: 600, letterSpacing: 0.5 }}>
                  DEMO
                </span>
              )}
            </div>
            <p style={{ margin: 0, fontSize: 11, color: '#555', marginTop: 1 }}>
              {filteredData.nodes.length} nodes · {filteredData.links.length} edges
              {graphStats ? ` · ${graphStats.total_edges ?? ''} total in DB` : ' · 3D Interactive'}
            </p>
          </div>

          {/* Search */}
          <div style={{ position: 'relative' }}>
            <input
              value={searchQ}
              onChange={e => setSearchQ(e.target.value)}
              placeholder="🔍  Search nodes..."
              style={{ background: 'rgba(255,255,255,0.06)', color: '#fff', border: '1px solid rgba(255,255,255,0.12)', borderRadius: 10, padding: '7px 14px', fontSize: 13, outline: 'none', width: 220 }}
            />
            {searchQ && <button onClick={() => setSearchQ('')} style={{ position: 'absolute', right: 8, top: '50%', transform: 'translateY(-50%)', background: 'none', border: 'none', color: '#666', cursor: 'pointer', fontSize: 16 }}>×</button>}
          </div>
        </div>

        {/* Legend filters */}
        <div style={{ display: 'flex', gap: 8, alignItems: 'center' }}>
          {Object.entries(GROUP_COLORS).map(([g, c]) => (
            <button key={g} onClick={() => setFilterGroup(filterGroup === g ? '' : g)}
              style={{ background: filterGroup === g ? `${c}22` : 'transparent', border: `1px solid ${filterGroup === g ? c : 'rgba(255,255,255,0.1)'}`, borderRadius: 20, padding: '5px 12px', cursor: 'pointer', display: 'flex', alignItems: 'center', gap: 6, fontSize: 11, color: filterGroup === g ? c : '#666', transition: 'all 0.2s', opacity: filterGroup && filterGroup !== g ? 0.4 : 1 }}>
              <span style={{ width: 8, height: 8, borderRadius: '50%', background: c, boxShadow: `0 0 6px ${c}` }} />
              {g}
            </button>
          ))}
          {filterGroup && <button onClick={() => setFilterGroup('')} style={{ background: 'rgba(255,255,255,0.05)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 20, padding: '5px 12px', cursor: 'pointer', color: '#888', fontSize: 11 }}>Clear</button>}
        </div>
      </div>

      {/* ── Main area ── */}
      <div style={{ flex: 1, display: 'flex', overflow: 'hidden', position: 'relative' }}>

        {/* 3D Graph */}
        <div style={{ flex: 1, position: 'relative' }}>
          <ForceGraph3D
            ref={fgRef}
            graphData={filteredData}
            nodeLabel={(node: any) => `<div style="background:rgba(0,0,0,0.85);border:1px solid ${GROUP_COLORS[node.group] || '#888'};border-radius:8px;padding:8px 12px;font-family:Inter,sans-serif;font-size:12px;color:#fff;"><b>${node.name}</b><br/><span style="color:${GROUP_COLORS[node.group] || '#888'};font-size:10px;">${node.group}</span>${node.score ? `<br/><span style="color:#FFEAA7;font-size:10px;">Score: ${node.score.toFixed(3)}</span>` : ''}</div>`}
            nodeColor={getNodeColor as any}
            nodeVal={getNodeVal as any}
            nodeOpacity={0.92}
            nodeResolution={16}
            linkColor={getLinkColor as any}
            linkWidth={(link: any) => {
              const s = typeof link.source === 'object' ? link.source.id : link.source;
              const t = typeof link.target === 'object' ? link.target.id : link.target;
              return neighborIds.size > 0 && neighborIds.has(s) && neighborIds.has(t) ? 1.5 : 0.3;
            }}
            linkOpacity={0.6}
            linkDirectionalParticles={(link: any) => {
              const s = typeof link.source === 'object' ? link.source.id : link.source;
              const t = typeof link.target === 'object' ? link.target.id : link.target;
              return neighborIds.size > 0 && neighborIds.has(s) && neighborIds.has(t) ? 4 : 0;
            }}
            linkDirectionalParticleWidth={2}
            linkDirectionalParticleColor={() => '#4ECDC4'}
            onNodeClick={handleNodeClick as any}
            backgroundColor="#050510"
            showNavInfo={false}
            enableNodeDrag={true}
            enableNavigationControls={true}
            nodeThreeObject={(node: any) => {
              const color = highlightIds.has(node.id) ? '#FFD700' : (GROUP_COLORS[node.group] || '#888');
              const size = Math.max(3, (node.val || 5) * (highlightIds.has(node.id) ? 1.8 : 0.9));
              if ((node.val || 5) >= 7 || highlightIds.has(node.id) || (neighborIds.size > 0 && neighborIds.has(node.id))) {
                const sprite = new SpriteText(node.name?.substring(0, 18) || node.id);
                sprite.color = color;
                sprite.textHeight = highlightIds.has(node.id) ? 5 : 3.5;
                sprite.backgroundColor = 'rgba(0,0,0,0.6)';
                sprite.borderRadius = 3;
                sprite.padding = 2;
                (sprite as any).position.y = size + 6;
                return sprite;
              }
              return null as any;
            }}
            nodeThreeObjectExtend={true}
          />

          {/* Hint overlay */}
          {!selectedNode && (
            <div style={{ position: 'absolute', bottom: 20, left: '50%', transform: 'translateX(-50%)', background: 'rgba(0,0,0,0.6)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 20, padding: '8px 18px', fontSize: 12, color: '#666', backdropFilter: 'blur(8px)', pointerEvents: 'none' }}>
              🖱️ Drag to rotate · Scroll to zoom · <span style={{ color: '#4ECDC4' }}>Click a node</span> to explore its connections
            </div>
          )}
        </div>

        {/* ── Side Panel ── */}
        {selectedNode && (
          <div style={{ width: 360, background: 'rgba(5,5,20,0.96)', borderLeft: `1px solid ${GROUP_COLORS[selectedNode.group] || '#333'}44`, backdropFilter: 'blur(20px)', display: 'flex', flexDirection: 'column', overflow: 'hidden', animation: 'slideIn 0.3s ease', flexShrink: 0 }}>
            <style>{`
              @keyframes slideIn { from { transform: translateX(100%); opacity: 0; } to { transform: translateX(0); opacity: 1; } }
              @keyframes spin { to { transform: rotate(360deg); } }
              @keyframes pulse { 0%,100% { opacity:1; } 50% { opacity:0.4; } }
              .nb-neighbor:hover { background: rgba(78,205,196,0.08) !important; border-color: rgba(78,205,196,0.3) !important; cursor: pointer; }
            `}</style>

            {/* Panel header */}
            <div style={{ padding: '16px 18px', borderBottom: `1px solid ${GROUP_COLORS[selectedNode.group] || '#333'}33`, background: `${GROUP_COLORS[selectedNode.group] || '#333'}08` }}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start' }}>
                <div style={{ flex: 1 }}>
                  <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 4 }}>
                    <div style={{ width: 12, height: 12, borderRadius: '50%', background: GROUP_COLORS[selectedNode.group] || '#888', boxShadow: `0 0 10px ${GLOW[selectedNode.group] || '#888'}` }} />
                    <span style={{ fontSize: 10, color: GROUP_COLORS[selectedNode.group] || '#888', textTransform: 'uppercase', letterSpacing: 1.5, fontWeight: 700 }}>{selectedNode.group}</span>
                  </div>
                  <h2 style={{ margin: 0, fontSize: 17, fontWeight: 800, color: '#fff', lineHeight: 1.3 }}>{selectedNode.name}</h2>
                  <p style={{ margin: '4px 0 0', fontSize: 11, color: '#555' }}>ID: {selectedNode.id}</p>
                </div>
                <button onClick={closePanel} style={{ background: 'rgba(255,255,255,0.06)', border: '1px solid rgba(255,255,255,0.1)', borderRadius: 8, color: '#666', cursor: 'pointer', fontSize: 18, width: 32, height: 32, display: 'flex', alignItems: 'center', justifyContent: 'center', flexShrink: 0 }}>×</button>
              </div>

              {/* Score chips */}
              <div style={{ display: 'flex', gap: 8, marginTop: 12, flexWrap: 'wrap' }}>
                {selectedNode.score !== undefined && (
                  <div style={{ background: 'rgba(255,234,167,0.1)', border: '1px solid rgba(255,234,167,0.2)', borderRadius: 8, padding: '4px 10px', fontSize: 11 }}>
                    <span style={{ color: '#888' }}>Score </span><span style={{ color: '#FFEAA7', fontWeight: 700, fontFamily: 'monospace' }}>{selectedNode.score.toFixed(3)}</span>
                  </div>
                )}
                <div style={{ background: 'rgba(78,205,196,0.1)', border: '1px solid rgba(78,205,196,0.2)', borderRadius: 8, padding: '4px 10px', fontSize: 11 }}>
                  <span style={{ color: '#888' }}>Connections </span><span style={{ color: '#4ECDC4', fontWeight: 700 }}>{neighborData.nodes.length - 1}</span>
                </div>
                {selectedNode.layer && (
                  <div style={{ background: 'rgba(99,102,241,0.1)', border: '1px solid rgba(99,102,241,0.2)', borderRadius: 8, padding: '4px 10px', fontSize: 11 }}>
                    <span style={{ color: '#888' }}>Layer </span><span style={{ color: '#6366f1', fontWeight: 700 }}>{selectedNode.layer}</span>
                  </div>
                )}
              </div>
            </div>

            {/* Panel tabs */}
            <div style={{ display: 'flex', borderBottom: '1px solid rgba(255,255,255,0.06)', flexShrink: 0 }}>
              {(['connections', 'similar', 'info'] as const).map(tab => (
                <button key={tab} onClick={() => setPanelTab(tab)}
                  style={{ flex: 1, padding: '10px 0', background: 'transparent', border: 'none', borderBottom: panelTab === tab ? '2px solid #4ECDC4' : '2px solid transparent', color: panelTab === tab ? '#4ECDC4' : '#555', fontSize: 12, cursor: 'pointer', fontWeight: panelTab === tab ? 700 : 400, textTransform: 'capitalize', transition: 'all 0.2s' }}>
                  {tab === 'connections' ? `🕸️ Links (${neighborData.nodes.length - 1})` : tab === 'similar' ? `🔗 Similar` : `ℹ️ Info`}
                </button>
              ))}
            </div>

            {/* Panel content */}
            <div style={{ flex: 1, overflowY: 'auto', padding: 16 }}>

              {/* CONNECTIONS TAB */}
              {panelTab === 'connections' && (
                <div>
                  {Object.keys(groupedNeighbors).length === 0 ? (
                    <p style={{ color: '#444', fontSize: 13, textAlign: 'center', marginTop: 40 }}>No connections found</p>
                  ) : (
                    Object.entries(groupedNeighbors).map(([group, nodes]) => (
                      <div key={group} style={{ marginBottom: 20 }}>
                        <div style={{ display: 'flex', alignItems: 'center', gap: 8, marginBottom: 10 }}>
                          <div style={{ width: 8, height: 8, borderRadius: '50%', background: GROUP_COLORS[group] || '#888' }} />
                          <span style={{ fontSize: 11, color: GROUP_COLORS[group] || '#888', fontWeight: 700, textTransform: 'uppercase', letterSpacing: 1 }}>{group}</span>
                          <span style={{ fontSize: 10, color: '#444', marginLeft: 'auto' }}>{nodes.length}</span>
                        </div>
                        <div style={{ display: 'flex', flexDirection: 'column', gap: 6 }}>
                          {nodes.map(n => {
                            const link = neighborData.links.find(l => {
                              const s = typeof l.source === 'object' ? l.source.id : l.source;
                              const t = typeof l.target === 'object' ? l.target.id : l.target;
                              return (s === n.id || t === n.id);
                            });
                            return (
                              <div key={n.id} className="nb-neighbor"
                                onClick={() => handleNodeClick(n)}
                                style={{ background: 'rgba(255,255,255,0.03)', border: '1px solid rgba(255,255,255,0.07)', borderRadius: 10, padding: '9px 12px', transition: 'all 0.2s' }}>
                                <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                                  <span style={{ color: '#e2e8f0', fontSize: 13, fontWeight: 500 }}>{n.name}</span>
                                  {n.score !== undefined && <span style={{ color: '#FFEAA7', fontSize: 10, fontFamily: 'monospace' }}>{n.score.toFixed(2)}</span>}
                                </div>
                                {link?.relationship && (
                                  <div style={{ fontSize: 10, color: '#4ECDC4', marginTop: 3, opacity: 0.7 }}>
                                    ↔ {link.relationship}
                                  </div>
                                )}
                              </div>
                            );
                          })}
                        </div>
                      </div>
                    ))
                  )}
                </div>
              )}

              {/* SIMILAR TAB */}
              {panelTab === 'similar' && (
                <div>
                  {!isLiveData && similarNodes.length > 0 && (
                    <div style={{ background: 'rgba(255,234,167,0.06)', border: '1px solid rgba(255,234,167,0.15)', borderRadius: 8, padding: '6px 12px', marginBottom: 12, fontSize: 11, color: '#FFEAA7' }}>
                      ⚡ Local similarity (shared neighbours). Start backend for AI-powered results.
                    </div>
                  )}
                  {similarNodes.length === 0 ? (
                    <p style={{ color: '#444', fontSize: 13, textAlign: 'center', marginTop: 40 }}>No similar nodes found</p>
                  ) : (
                    <div style={{ display: 'flex', flexDirection: 'column', gap: 8 }}>
                      {similarNodes.map((s: any, i: number) => (
                        <div key={i} className="nb-neighbor"
                          onClick={() => { const n = graphData.nodes.find(nd => nd.id === s.node_id || nd.name === s.name); if (n) handleNodeClick(n); }}
                          style={{ background: 'rgba(187,143,206,0.05)', border: '1px solid rgba(187,143,206,0.12)', borderRadius: 10, padding: '10px 12px', transition: 'all 0.2s' }}>
                          <div style={{ display: 'flex', justifyContent: 'space-between' }}>
                            <span style={{ color: '#fff', fontWeight: 600, fontSize: 13 }}>{s.name}</span>
                            <span style={{ background: `${GROUP_COLORS[s.group] || '#888'}22`, color: GROUP_COLORS[s.group] || '#888', padding: '2px 7px', borderRadius: 5, fontSize: 10, fontWeight: 600 }}>{s.group}</span>
                          </div>
                          {s.signals && (
                            <div style={{ display: 'flex', gap: 12, marginTop: 6, fontSize: 10, color: '#666' }}>
                              <span>Ensemble: <span style={{ color: '#DDA0DD' }}>{s.signals.ensemble?.toFixed(3)}</span></span>
                              <span>Jaccard: {s.signals.jaccard?.toFixed(3)}</span>
                            </div>
                          )}
                        </div>
                      ))}
                    </div>
                  )}
                </div>
              )}

              {/* INFO TAB */}
              {panelTab === 'info' && (
                <div style={{ display: 'flex', flexDirection: 'column', gap: 10 }}>
                  {[
                    { label: 'Node ID', value: selectedNode.id },
                    { label: 'Group', value: selectedNode.group },
                    { label: 'Layer', value: selectedNode.layer },
                    { label: 'Score', value: selectedNode.score?.toFixed(4) },
                    { label: 'Cluster ID', value: selectedNode.cluster_id },
                    { label: 'Druggability', value: selectedNode.druggability },
                    { label: 'Gene Family', value: selectedNode.gene_family },
                    { label: 'Connections', value: neighborData.nodes.length - 1 },
                  ].filter(f => f.value !== undefined && f.value !== null && f.value !== '').map(f => (
                    <div key={f.label} style={{ display: 'flex', justifyContent: 'space-between', padding: '8px 12px', background: 'rgba(255,255,255,0.03)', borderRadius: 8, fontSize: 12 }}>
                      <span style={{ color: '#666' }}>{f.label}</span>
                      <span style={{ color: '#e2e8f0', fontWeight: 600, fontFamily: 'monospace', fontSize: 11 }}>{String(f.value)}</span>
                    </div>
                  ))}
                </div>
              )}
            </div>
          </div>
        )}
      </div>
    </div>
  );
}
