"""
CARVanta Copilot — AI Research Assistant Package
==================================================
RAG-powered research copilot for immunotherapy literature analysis,
experiment design, and conversational AI.

Sub-modules:
- paper_index: PubMed paper indexing and metadata extraction
- rag_engine: Vector search and retrieval-augmented generation
- chat_handler: Conversational AI controller
- lit_reviewer: Automated literature review generation
- experiment_designer: Protocol suggestion engine
- voice_handler: Speech-to-text / text-to-speech interface
"""

__version__ = "5.0.0"
__all__ = [
    "paper_index",
    "rag_engine",
    "chat_handler",
    "lit_reviewer",
    "experiment_designer",
    "voice_handler",
]
