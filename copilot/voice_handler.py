"""
CARVanta Copilot — Voice Handler
===================================
Speech-to-text and text-to-speech interface for hands-free
lab use of the AI Research Copilot.

Provides:
- Audio transcription (simulated — production uses Whisper API)
- Text-to-speech synthesis (simulated — production uses TTS API)
- Voice command parsing and intent routing
- Noise filtering and lab environment optimization
- Multi-language transcription support

Security: Stateless, async, no audio retention, PII-free.
"""

import logging
import re
import time
import uuid
import hashlib
from typing import Any, Dict, List, Optional
from dataclasses import dataclass, field
from enum import Enum

logger = logging.getLogger("carvanta.copilot.voice_handler")

# ──────────────────────────────────────────────────────────────────────
# Constants
# ──────────────────────────────────────────────────────────────────────

class VoiceLanguage(Enum):
    """Supported voice languages."""
    ENGLISH_US = "en-US"
    ENGLISH_UK = "en-GB"
    SPANISH = "es-ES"
    FRENCH = "fr-FR"
    GERMAN = "de-DE"
    CHINESE = "zh-CN"
    JAPANESE = "ja-JP"
    KOREAN = "ko-KR"
    PORTUGUESE = "pt-BR"
    ITALIAN = "it-IT"


class VoiceCommand(Enum):
    """Recognized voice commands."""
    SEARCH = "search"
    ANALYZE = "analyze"
    COMPARE = "compare"
    REVIEW = "review"
    PROTOCOL = "protocol"
    HELP = "help"
    STOP = "stop"
    REPEAT = "repeat"
    SLOWER = "slower"
    FASTER = "faster"


class AudioQuality(Enum):
    """Audio quality levels."""
    LOW = "low"
    MEDIUM = "medium"
    HIGH = "high"
    STUDIO = "studio"


# ──────────────────────────────────────────────────────────────────────
# Data Classes
# ──────────────────────────────────────────────────────────────────────

@dataclass
class TranscriptionResult:
    """Speech-to-text transcription result."""
    text: str
    language: str
    confidence: float
    duration_seconds: float
    word_count: int
    detected_command: Optional[str] = None
    alternatives: List[str] = field(default_factory=list)
    transcript_id: str = ""

    def __post_init__(self):
        if not self.transcript_id:
            self.transcript_id = str(uuid.uuid4())[:8]


@dataclass
class SynthesisResult:
    """Text-to-speech synthesis result."""
    text: str
    audio_format: str
    sample_rate: int
    duration_seconds: float
    language: str
    voice_id: str
    synthesis_id: str = ""

    def __post_init__(self):
        if not self.synthesis_id:
            self.synthesis_id = str(uuid.uuid4())[:8]


@dataclass
class VoiceSession:
    """Voice interaction session."""
    session_id: str
    language: str = "en-US"
    speech_rate: float = 1.0
    noise_filter: bool = True
    auto_punctuate: bool = True
    total_transcriptions: int = 0
    total_synthesis: int = 0
    created_at: float = 0.0
    last_active: float = 0.0

    def __post_init__(self):
        if not self.created_at:
            self.created_at = time.time()
            self.last_active = self.created_at


# ──────────────────────────────────────────────────────────────────────
# Voice Command Detection
# ──────────────────────────────────────────────────────────────────────

_COMMAND_PATTERNS: Dict[VoiceCommand, List[str]] = {
    VoiceCommand.SEARCH: ["search for", "find papers", "look up", "find me", "search pubmed"],
    VoiceCommand.ANALYZE: ["analyze", "score", "evaluate", "assess", "check"],
    VoiceCommand.COMPARE: ["compare", "versus", "difference between", "which is better"],
    VoiceCommand.REVIEW: ["review", "summarize", "give me an overview", "state of the art"],
    VoiceCommand.PROTOCOL: ["protocol for", "how do i test", "experiment design", "assay for"],
    VoiceCommand.HELP: ["help", "what can you do", "commands", "options"],
    VoiceCommand.STOP: ["stop", "cancel", "quit", "exit", "silence"],
    VoiceCommand.REPEAT: ["repeat", "say again", "what did you say", "pardon"],
    VoiceCommand.SLOWER: ["slower", "slow down", "speak slowly"],
    VoiceCommand.FASTER: ["faster", "speed up", "speak faster"],
}


def detect_voice_command(text: str) -> Optional[VoiceCommand]:
    """Detect voice command from transcribed text."""
    t = text.lower().strip()
    for cmd, patterns in _COMMAND_PATTERNS.items():
        if any(p in t for p in patterns):
            return cmd
    return None


# ──────────────────────────────────────────────────────────────────────
# Lab Noise Filter (Simulated)
# ──────────────────────────────────────────────────────────────────────

_LAB_NOISE_WORDS = [
    "um", "uh", "er", "ah", "hmm", "like", "you know", "basically",
    "so", "well", "ok so", "right so", "yeah so",
]


def _filter_noise(text: str) -> str:
    """Remove filler words and lab noise artifacts from transcription."""
    result = text
    for noise in _LAB_NOISE_WORDS:
        pattern = re.compile(r'\b' + re.escape(noise) + r'\b', re.IGNORECASE)
        result = pattern.sub('', result)
    result = re.sub(r'\s+', ' ', result).strip()
    return result


def _auto_punctuate(text: str) -> str:
    """Add basic punctuation to raw transcription."""
    text = text.strip()
    if not text:
        return text
    # Capitalize first letter
    text = text[0].upper() + text[1:]
    # Add period if missing
    if text[-1] not in '.?!':
        if any(text.lower().startswith(q) for q in ['what', 'how', 'why', 'when', 'where', 'which', 'can', 'do', 'is', 'are']):
            text += '?'
        else:
            text += '.'
    return text


# ──────────────────────────────────────────────────────────────────────
# Voice Session Management
# ──────────────────────────────────────────────────────────────────────

_VOICE_SESSIONS: Dict[str, VoiceSession] = {}
_MAX_VOICE_SESSIONS = 50


async def create_voice_session(
    language: str = "en-US",
    speech_rate: float = 1.0,
    noise_filter: bool = True,
) -> VoiceSession:
    """Create a new voice interaction session."""
    if len(_VOICE_SESSIONS) >= _MAX_VOICE_SESSIONS:
        oldest = min(_VOICE_SESSIONS, key=lambda k: _VOICE_SESSIONS[k].last_active)
        del _VOICE_SESSIONS[oldest]

    session = VoiceSession(
        session_id=str(uuid.uuid4())[:12],
        language=language,
        speech_rate=speech_rate,
        noise_filter=noise_filter,
    )
    _VOICE_SESSIONS[session.session_id] = session
    return session


async def get_voice_session(session_id: str) -> Optional[VoiceSession]:
    """Retrieve a voice session."""
    return _VOICE_SESSIONS.get(session_id)


# ──────────────────────────────────────────────────────────────────────
# Speech-to-Text (Simulated)
# ──────────────────────────────────────────────────────────────────────

async def transcribe_audio(
    audio_data: bytes,
    language: str = "en-US",
    noise_filter: bool = True,
    auto_punctuate: bool = True,
    session_id: Optional[str] = None,
) -> TranscriptionResult:
    """
    Transcribe audio to text.

    In production, this would use OpenAI Whisper, Google Speech-to-Text,
    or Azure Cognitive Services. Currently returns a simulated result.
    """
    # Validate audio data
    if not audio_data or len(audio_data) < 100:
        return TranscriptionResult(
            text="", language=language, confidence=0.0,
            duration_seconds=0.0, word_count=0,
        )

    # Simulated transcription based on audio hash
    audio_hash = hashlib.md5(audio_data).hexdigest()[:8]
    simulated_texts = [
        "What are the latest clinical results for CD19 CAR-T therapy",
        "Compare BCMA and GPRC5D as myeloma targets",
        "Search for papers on cytokine release syndrome management",
        "Design a protocol for testing HER2 CAR-T cytotoxicity",
        "Give me a review of armored CAR T cell approaches for solid tumors",
        "What is the mechanism of antigen loss resistance",
        "Analyze the safety profile of tisagenlecleucel",
        "How does 4-1BB co-stimulation compare to CD28",
    ]
    idx = int(audio_hash, 16) % len(simulated_texts)
    raw_text = simulated_texts[idx]

    # Apply filters
    if noise_filter:
        raw_text = _filter_noise(raw_text)
    if auto_punctuate:
        raw_text = _auto_punctuate(raw_text)

    # Detect command
    command = detect_voice_command(raw_text)

    # Estimate duration from audio size
    duration = len(audio_data) / 32000  # Assume 32kbps

    result = TranscriptionResult(
        text=raw_text,
        language=language,
        confidence=0.92,
        duration_seconds=round(duration, 2),
        word_count=len(raw_text.split()),
        detected_command=command.value if command else None,
        alternatives=[raw_text + " (alternative)"],
    )

    # Update session if exists
    if session_id:
        session = _VOICE_SESSIONS.get(session_id)
        if session:
            session.total_transcriptions += 1
            session.last_active = time.time()

    return result


# ──────────────────────────────────────────────────────────────────────
# Text-to-Speech (Simulated)
# ──────────────────────────────────────────────────────────────────────

_VOICE_PROFILES = {
    "en-US": {"voice_id": "cv_aria_en_us", "name": "Aria", "gender": "female", "style": "professional"},
    "en-GB": {"voice_id": "cv_james_en_gb", "name": "James", "gender": "male", "style": "formal"},
    "es-ES": {"voice_id": "cv_sofia_es", "name": "Sofia", "gender": "female", "style": "warm"},
    "fr-FR": {"voice_id": "cv_pierre_fr", "name": "Pierre", "gender": "male", "style": "clear"},
    "de-DE": {"voice_id": "cv_anna_de", "name": "Anna", "gender": "female", "style": "precise"},
    "zh-CN": {"voice_id": "cv_mei_zh", "name": "Mei", "gender": "female", "style": "natural"},
    "ja-JP": {"voice_id": "cv_yuki_ja", "name": "Yuki", "gender": "female", "style": "polite"},
}


async def synthesize_speech(
    text: str,
    language: str = "en-US",
    speech_rate: float = 1.0,
    audio_format: str = "wav",
    session_id: Optional[str] = None,
) -> SynthesisResult:
    """
    Synthesize text to speech audio.

    In production, this would use Google Cloud TTS, Azure Neural TTS,
    or ElevenLabs. Currently returns metadata only (no actual audio).
    """
    text = re.sub(r'[<>{}]', '', text.strip())[:5000]
    if not text:
        return SynthesisResult(text="", audio_format=audio_format, sample_rate=24000,
                              duration_seconds=0.0, language=language, voice_id="none")

    voice = _VOICE_PROFILES.get(language, _VOICE_PROFILES["en-US"])

    # Estimate duration: ~150 words/minute at 1.0 speed
    word_count = len(text.split())
    base_duration = (word_count / 150) * 60
    adjusted_duration = base_duration / speech_rate

    result = SynthesisResult(
        text=text[:200] + "..." if len(text) > 200 else text,
        audio_format=audio_format,
        sample_rate=24000,
        duration_seconds=round(adjusted_duration, 2),
        language=language,
        voice_id=voice["voice_id"],
    )

    if session_id:
        session = _VOICE_SESSIONS.get(session_id)
        if session:
            session.total_synthesis += 1
            session.last_active = time.time()

    return result


async def get_available_voices() -> List[Dict[str, str]]:
    """List all available voice profiles."""
    return [
        {
            "language": lang,
            "voice_id": profile["voice_id"],
            "name": profile["name"],
            "gender": profile["gender"],
            "style": profile["style"],
        }
        for lang, profile in _VOICE_PROFILES.items()
    ]


async def get_supported_languages() -> List[Dict[str, str]]:
    """List supported voice languages."""
    return [{"code": v.value, "name": v.name.replace("_", " ").title()} for v in VoiceLanguage]
