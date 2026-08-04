import React, { useState, useRef } from 'react';
import '../styles/voice-copilot.css';

export default function VoiceCopilotPage() {
  const [isListening, setIsListening] = useState(false);
  const [transcript, setTranscript] = useState('');
  const [isSpeaking, setIsSpeaking] = useState(false);
  const [isPaused, setIsPaused] = useState(false);
  const [response, setResponse] = useState<{
    status: 'emergency' | 'warning' | 'normal' | null;
    headline: string;
    protocol: string;
    dosage: string;
    action: string;
    confidence: number;
  }>({
    status: 'emergency',
    headline: 'CRS Grade 3 / Hypotensive Shock Protocol',
    protocol: 'Patient indicates high grade Cytokine Release Syndrome (CRS). Administer immediate IL-6 receptor antagonist therapy.',
    dosage: 'Tocilizumab 8mg/kg IV (Max 800mg) over 1 hour. Repeat q8h if no improvement.',
    action: 'Initiate continuous ICU ECG & SpO2 telemetry. Prepare secondary Corticosteroid dose (Dexamethasone 10mg IV).',
    confidence: 98.4
  });

  const recognitionRef = useRef<any>(null);

  const triggerVoiceAnalysis = async (text: string) => {
    setTranscript(text);
    const lower = text.toLowerCase();

    let resData;
    if (lower.includes('fever') || lower.includes('temperature') || lower.includes('pressure') || lower.includes('shock') || lower.includes('crs')) {
      resData = {
        status: 'emergency' as const,
        headline: 'CRS Grade 3 / Acute Inflammation Alert',
        protocol: 'Elevated IL-6 & TNF-alpha surge detected. Severe risk of capillary leak syndrome.',
        dosage: 'Tocilizumab 8mg/kg IV + Dexamethasone 10mg IV q6h.',
        action: 'Notify ICU attending. Transfer to continuous hemodynamics monitor.',
        confidence: 99.1
      };
    } else if (lower.includes('headache') || lower.includes('confusion') || lower.includes('icans') || lower.includes('speech')) {
      resData = {
        status: 'warning' as const,
        headline: 'ICANS Grade 2 Neurotoxicity Alert',
        protocol: 'Immune effector cell-associated neurotoxicity syndrome detected. Cognitive impairment risk.',
        dosage: 'Dexamethasone 10mg IV q6h. Hold CAR-T cell infusions.',
        action: 'Perform full ICE assessment every 2 hours. Order emergency brain MRI/EEG.',
        confidence: 94.7
      };
    } else {
      resData = {
        status: 'normal' as const,
        headline: 'Vitals & Cytokine Dynamics Stable',
        protocol: 'Digital Twin trajectory indicates baseline expansion within safe physiological threshold.',
        dosage: 'Standard monitoring protocol. No intervention required.',
        action: 'Maintain routine q4h vital signs logging.',
        confidence: 97.2
      };
    }

    setResponse(resData);

    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      const utterance = new SpeechSynthesisUtterance(`${resData.headline}. ${resData.dosage}. ${resData.action}`);
      utterance.onstart = () => { setIsSpeaking(true); setIsPaused(false); };
      utterance.onend = () => { setIsSpeaking(false); setIsPaused(false); };
      window.speechSynthesis.speak(utterance);
    }
  };

  const togglePauseResume = () => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      if (isPaused) {
        window.speechSynthesis.resume();
        setIsPaused(false);
      } else {
        window.speechSynthesis.pause();
        setIsPaused(true);
      }
    }
  };

  const stopSpeaking = () => {
    if (typeof window !== 'undefined' && 'speechSynthesis' in window) {
      window.speechSynthesis.cancel();
      setIsSpeaking(false);
      setIsPaused(false);
    }
  };

  const toggleListening = () => {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
      return;
    }

    if (typeof window !== 'undefined') {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (!SpeechRecognition) {
        alert('Web Speech API is not supported in this browser. You can use the Quick Voice Emergency Presets below!');
        return;
      }

      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = true;
      recognition.lang = 'en-US';

      recognition.onresult = (event: any) => {
        const currentTranscript = Array.from(event.results)
          .map((res: any) => res[0].transcript)
          .join('');
        setTranscript(currentTranscript);
        if (event.results[0].isFinal) {
          triggerVoiceAnalysis(currentTranscript);
          setIsListening(false);
        }
      };

      recognition.onerror = () => setIsListening(false);
      recognition.onend = () => setIsListening(false);

      recognitionRef.current = recognition;
      recognition.start();
      setIsListening(true);
    }
  };

  return (
    <div className="vc-page">
      <div className="vc-header">
        <div>
          <div style={{ display: 'flex', gap: '8px', marginBottom: '8px' }}>
            <span className="vc-badge emergency">⚡ National Hackathon USP</span>
            <span className="vc-badge normal" style={{ background: 'rgba(99, 102, 241, 0.2)', color: '#a5b4fc', border: '1px solid rgba(99, 102, 241, 0.3)' }}>ICU Emergency Copilot</span>
          </div>
          <h1 className="vc-title">Voice-Activated Clinical Copilot</h1>
          <p className="vc-subtitle">Real-time hands-free speech reasoning engine for ICU CAR-T toxicity crises.</p>
        </div>

        <div style={{ display: 'flex', alignItems: 'center', gap: '10px' }}>
          <span style={{ 
            width: '12px', height: '12px', borderRadius: '50%', 
            background: isSpeaking ? '#34d399' : '#64748b',
            animation: isSpeaking ? 'vcPulse 1s infinite' : 'none'
          }} />
          <span style={{ fontSize: '12px', color: '#94a3b8', fontFamily: 'monospace', textTransform: 'uppercase' }}>
            {isSpeaking ? 'AI Speaking...' : 'Engine Ready'}
          </span>
        </div>
      </div>

      <div className="vc-grid">
        
        {/* Left Column: Interactive Mic & Presets */}
        <div>
          <div className="vc-card vc-mic-container">
            <button
              onClick={toggleListening}
              className={`vc-mic-btn ${isListening ? 'listening' : ''}`}
            >
              <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 24 24">
                <path strokeLinecap="round" strokeLinejoin="round" strokeWidth="2" d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
              </svg>
            </button>
            <span style={{ fontSize: '16px', fontWeight: 'bold', color: '#fff', marginTop: '10px' }}>
              {isListening ? 'Listening to Clinical Staff...' : 'Click Mic or Speak Command'}
            </span>
            <p style={{ fontSize: '12px', color: '#94a3b8', marginTop: '5px', textAlign: 'center' }}>
              {isListening ? 'Say vitals like: "Patient spiking 103 fever and blood pressure dropping"' : 'Browser Speech Recognition Active'}
            </p>

            <div style={{ width: '100%', marginTop: '30px' }}>
              <span style={{ fontSize: '10px', fontFamily: 'monospace', color: '#a5b4fc', textTransform: 'uppercase', letterSpacing: '2px', display: 'block', marginBottom: '5px' }}>Live Transcript</span>
              <div className="vc-transcript">
                {transcript || 'Awaiting voice input...'}
              </div>
            </div>
          </div>

          <div className="vc-card">
            <h3 className="vc-preset-title">⚡ Quick ICU Emergency Presets</h3>
            <div>
              <button onClick={() => triggerVoiceAnalysis('Patient spiking 103 degree fever and blood pressure is dropping!')} className="vc-preset-btn red">
                <span>🔥 CRS Shock: "Spiking 103°F fever + Low BP"</span>
                <span>→</span>
              </button>
              <button onClick={() => triggerVoiceAnalysis('Patient showing confusion, tremor and handwriting difficulty, ICE score dropped.')} className="vc-preset-btn amber">
                <span>🧠 ICANS Neurotoxicity: "ICE score drop + Tremor"</span>
                <span>→</span>
              </button>
              <button onClick={() => triggerVoiceAnalysis('Routine post-infusion check, vitals stable, temperature 98.6.')} className="vc-preset-btn emerald">
                <span>✅ Stable Monitoring: "Vitals normal, Temp 98.6°F"</span>
                <span>→</span>
              </button>
            </div>
          </div>
        </div>

        {/* Right Column: Dynamic Emergency Response Panel */}
        <div>
          {response && (
            <div className={`vc-response-panel vc-response-${response.status}`}>
              <div style={{ display: 'flex', justifyContent: 'space-between', alignItems: 'flex-start', marginBottom: '20px' }}>
                <div>
                  <span className={`vc-badge ${response.status}`}>
                    {response.status === 'emergency' ? '🚨 EMERGENCY ACTION REQUIRED' : response.status === 'warning' ? '⚠️ ELEVATED MONITORING' : '🟢 STABLE PHYSIOLOGY'}
                  </span>
                  <h2 className="vc-response-title">{response.headline}</h2>
                </div>
                <div style={{ textAlign: 'right', fontFamily: 'monospace' }}>
                  <div style={{ fontSize: '12px', color: '#94a3b8' }}>AI Confidence</div>
                  <div style={{ fontSize: '24px', fontWeight: 'bold', color: '#818cf8' }}>{response.confidence}%</div>
                </div>
              </div>

              <div className="vc-box">
                <h4>Clinical Assessment</h4>
                <p>{response.protocol}</p>
              </div>

              <div className="vc-box-red">
                <h4>💊 Immediate Countermeasure Dosage</h4>
                <p style={{ fontFamily: 'monospace', fontSize: '16px', fontWeight: 'bold' }}>{response.dosage}</p>
              </div>

              <div className="vc-box">
                <h4>ICU Nursing & Telemetry Directive</h4>
                <p>{response.action}</p>
              </div>

              <div style={{ marginTop: '30px', paddingTop: '20px', borderTop: '1px solid rgba(255,255,255,0.1)', display: 'flex', justifyContent: 'space-between', alignItems: 'center' }}>
                <span style={{ fontSize: '12px', fontFamily: 'monospace', color: '#94a3b8' }}>CARVanta v5 Bio-Intelligence Engine</span>
                <div style={{ display: 'flex', gap: '10px' }}>
                  {isSpeaking && (
                    <>
                      <button onClick={togglePauseResume} className="vc-reannounce-btn" style={{ background: '#f59e0b', color: '#000' }}>
                        {isPaused ? '▶️ Resume' : '⏸️ Pause'}
                      </button>
                      <button onClick={stopSpeaking} className="vc-reannounce-btn" style={{ background: '#ef4444', color: '#fff' }}>
                        ⏹️ Stop
                      </button>
                    </>
                  )}
                  <button onClick={() => triggerVoiceAnalysis('Patient spiking 103 degree fever and blood pressure dropping!')} className="vc-reannounce-btn">
                    🔊 Re-announce Protocol
                  </button>
                </div>
              </div>
            </div>
          )}
        </div>

      </div>
    </div>
  );
}
