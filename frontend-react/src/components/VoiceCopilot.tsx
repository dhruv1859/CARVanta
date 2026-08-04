import React, { useState, useRef } from 'react';
import axios from 'axios';

export default function VoiceCopilot() {
  const [isListening, setIsListening] = useState(false);
  const [responseMsg, setResponseMsg] = useState<{status: string, insight: string, protocol: string} | null>(null);
  
  // Use speech recognition safely
  const recognitionRef = useRef<any>(null);

  const initSpeech = () => {
    if (typeof window !== 'undefined') {
      const SpeechRecognition = (window as any).SpeechRecognition || (window as any).webkitSpeechRecognition;
      if (!SpeechRecognition) return null;
      const recognition = new SpeechRecognition();
      recognition.continuous = false;
      recognition.interimResults = false;
      recognition.lang = 'en-US';

      recognition.onresult = async (event: any) => {
        const transcript = event.results[0][0].transcript;
        console.log("Transcribed:", transcript);
        await processVoiceCommand(transcript);
        setIsListening(false);
      };

      recognition.onerror = (event: any) => {
        console.error("Speech Error:", event.error);
        setIsListening(false);
      };

      recognition.onend = () => {
        setIsListening(false);
      };

      return recognition;
    }
    return null;
  };

  const processVoiceCommand = async (transcript: string) => {
    try {
      // Note: we're using the standard copilot backend
      const res = await axios.post('http://localhost:8001/api/v5/copilot/voice-query', { transcript });
      const data = res.data;
      
      setResponseMsg({
        status: data.status,
        insight: data.clinical_insight,
        protocol: data.protocol
      });

      // Speak response aloud
      const utterance = new SpeechSynthesisUtterance(data.protocol);
      utterance.rate = 1.0;
      utterance.pitch = 1.0;
      window.speechSynthesis.speak(utterance);

    } catch (e) {
      console.error("Error processing voice command:", e);
      // Fallback if backend is down
      const fallbackProtocol = transcript.toLowerCase().includes("fever") 
        ? "Grade 3 CRS detected. Administer 8mg/kg Tocilizumab."
        : "Vitals normal. Continue monitoring.";
      
      setResponseMsg({
        status: "emergency",
        insight: "Mock mode enabled (Backend unreachable).",
        protocol: fallbackProtocol
      });

      const utterance = new SpeechSynthesisUtterance(fallbackProtocol);
      window.speechSynthesis.speak(utterance);
    }
  };

  const toggleListen = () => {
    if (isListening) {
      recognitionRef.current?.stop();
      setIsListening(false);
    } else {
      if (!recognitionRef.current) {
        recognitionRef.current = initSpeech();
      }
      if (recognitionRef.current) {
        recognitionRef.current.start();
        setIsListening(true);
        setResponseMsg(null);
      } else {
        alert("Speech recognition not supported in this browser.");
      }
    }
  };

  return (
    <div className="fixed bottom-24 right-6 z-50 flex flex-col items-end">
      {responseMsg && (
        <div className={`mb-4 p-4 rounded-xl shadow-2xl border backdrop-blur-xl max-w-sm transition-all duration-300 transform origin-bottom-right scale-100 ${
          responseMsg.status === 'emergency' 
            ? 'bg-red-500/20 border-red-500/50 text-red-100' 
            : 'bg-indigo-500/20 border-indigo-500/50 text-indigo-100'
        }`}>
          <div className="text-xs uppercase tracking-wider mb-1 font-bold opacity-75">Clinical Copilot</div>
          <div className="text-sm font-medium mb-2">{responseMsg.insight}</div>
          <div className="text-sm p-2 rounded bg-black/30 font-semibold">{responseMsg.protocol}</div>
          <button 
            onClick={() => setResponseMsg(null)}
            className="absolute top-2 right-2 text-white/50 hover:text-white"
          >
            ✕
          </button>
        </div>
      )}

      <button
        onClick={toggleListen}
        className={`w-16 h-16 rounded-full flex items-center justify-center shadow-2xl transition-all duration-300 ${
          isListening 
            ? 'bg-red-600 animate-pulse ring-4 ring-red-500/50' 
            : 'bg-indigo-600 hover:bg-indigo-500 hover:scale-105 ring-4 ring-indigo-500/20'
        }`}
        title="Activate Voice Copilot"
      >
        <svg xmlns="http://www.w3.org/2000/svg" className="h-8 w-8 text-white" fill="none" viewBox="0 0 24 24" stroke="currentColor">
          <path strokeLinecap="round" strokeLinejoin="round" strokeWidth={2} d="M19 11a7 7 0 01-7 7m0 0a7 7 0 01-7-7m7 7v4m0 0H8m4 0h4m-4-8a3 3 0 01-3-3V5a3 3 0 116 0v6a3 3 0 01-3 3z" />
        </svg>
      </button>
    </div>
  );
}
