import { useState, useEffect } from 'react';
import '../styles/pipeline.css';

interface PipelineStage {
    id: string;
    label: string;
    description: string;
    duration: number; // ms
}

const STAGES: PipelineStage[] = [
    { id: 'dna',      label: 'Gene Scanning',       description: 'Scanning expression databases (TCGA + GTEx)...', duration: 1800 },
    { id: 'protein',  label: 'Protein Analysis',     description: 'Validating surface accessibility & structure...', duration: 1500 },
    { id: 'safety',   label: 'Safety Screening',     description: 'Checking normal tissue expression & toxicity...', duration: 1400 },
    { id: 'features', label: 'Feature Engineering',  description: 'Computing 8 clinical viability features...',     duration: 1200 },
    { id: 'ml',       label: 'ML Inference',          description: 'Running RF + XGBoost ensemble model...',         duration: 1600 },
    { id: 'score',    label: 'Final Score',            description: 'Computing Clinical Viability Score...',          duration: 800  },
];

interface Props {
    isRunning: boolean;
    antigenName: string;
    onComplete?: () => void;
}

export default function PipelineVisualizer({ isRunning, antigenName, onComplete }: Props) {
    const [activeStage, setActiveStage] = useState(-1);
    const [completedStages, setCompletedStages] = useState<Set<number>>(new Set());
    const [stageTimes, setStageTimes] = useState<Record<number, number>>({});
    const [currentDesc, setCurrentDesc] = useState('Initializing scoring pipeline...');

    useEffect(() => {
        if (!isRunning) {
            setActiveStage(-1);
            setCompletedStages(new Set());
            setStageTimes({});
            return;
        }

        let cancelled = false;
        let stageIdx = 0;

        const runPipeline = async () => {
            for (let i = 0; i < STAGES.length; i++) {
                if (cancelled) return;
                stageIdx = i;
                setActiveStage(i);
                setCurrentDesc(STAGES[i]?.description || '');

                // Simulate processing time
                const dur = (STAGES[i]?.duration || 1000) + Math.random() * 400;
                await new Promise(r => setTimeout(r, dur));

                if (cancelled) return;
                setCompletedStages(prev => new Set([...prev, i]));
                setStageTimes(prev => ({ ...prev, [i]: Math.round(dur) }));
            }
            if (!cancelled) {
                setCurrentDesc('Pipeline complete — score ready!');
                onComplete?.();
            }
        };

        runPipeline();
        return () => { cancelled = true; };
    }, [isRunning]);

    if (!isRunning && completedStages.size === 0) return null;

    const progress = completedStages.size / STAGES.length * 100;

    const getStageStatus = (i: number) => {
        if (completedStages.has(i)) return 'complete';
        if (i === activeStage) return 'active';
        return 'pending';
    };

    return (
        <div className="pipeline-container">
            <div className="pipeline-header">
                <h3>⚡ Scoring Pipeline — {antigenName}</h3>
                <p>{currentDesc}</p>
            </div>

            <div className="pipeline-stages">
                {/* Connector bar */}
                <div className="pipeline-connector">
                    <div className="pipeline-connector-fill" style={{ width: `${progress}%` }} />
                </div>

                {STAGES.map((stage, i) => (
                    <div key={stage.id} className={`pipeline-stage ${getStageStatus(i)}`}>
                        <div className="pipeline-icon-box">
                            {getStageStatus(i) === 'complete' && (
                                <div className="pipeline-check">✓</div>
                            )}
                            {stage.id === 'dna' && <DNAHelix />}
                            {stage.id === 'protein' && <ProteinMolecule />}
                            {stage.id === 'safety' && <SafetyShield />}
                            {stage.id === 'features' && <FeatureBars />}
                            {stage.id === 'ml' && <NeuralNetwork />}
                            {stage.id === 'score' && <ScoreReveal />}
                        </div>
                        <span className="pipeline-stage-label">{stage.label}</span>
                        {stageTimes[i] && (
                            <span className="pipeline-stage-time">{stageTimes[i]}ms</span>
                        )}
                    </div>
                ))}
            </div>
        </div>
    );
}

/* ── SVG/CSS Animated Icons ──────────────────────────────── */

function DNAHelix() {
    return (
        <div className="dna-helix">
            <div className="dna-strand dna-strand-left" />
            <div className="dna-strand dna-strand-right" />
            <div className="dna-rung" />
            <div className="dna-rung" />
            <div className="dna-rung" />
            <div className="dna-rung" />
            <div className="dna-rung" />
            <div className="dna-rung" />
        </div>
    );
}

function ProteinMolecule() {
    return (
        <div className="protein-molecule">
            <div className="protein-core" />
            <div className="protein-orbit" />
            <div className="protein-orbit" />
            <div className="protein-electron" />
            <div className="protein-electron" />
            <div className="protein-electron" />
        </div>
    );
}

function SafetyShield() {
    return (
        <div className="safety-shield">
            <div className="shield-shape">🛡️</div>
            <div className="shield-scan" />
        </div>
    );
}

function FeatureBars() {
    return (
        <div className="feature-bars-anim">
            {Array.from({ length: 8 }).map((_, i) => (
                <div key={i} className="feature-bar-anim" />
            ))}
        </div>
    );
}

function NeuralNetwork() {
    return (
        <div className="neural-net">
            <div className="neuron" />
            <div className="neuron" />
            <div className="neuron" />
            <div className="neuron" />
            <div className="neuron" />
            <div className="neuron" />
        </div>
    );
}

function ScoreReveal() {
    return (
        <div className="score-reveal">
            <div className="score-ring">
                <span className="score-ring-inner">CVS</span>
            </div>
        </div>
    );
}
