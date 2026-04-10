# ABOUTME: Backward-compatible re-exports from decomposed context/ subpackage.
# ABOUTME: All classes moved to focused modules under commands/context/.
"""Backward-compatible re-exports from decomposed context/ subpackage.

All classes have been moved to focused modules under commands/context/.
Import from the new locations for new code.
"""

from assetutilities.agent_os.commands.context.chunking import (
    APISignature,
    Concept,
    DocumentChunk,
    DocumentChunker,
    Pattern,
)
from assetutilities.agent_os.commands.context.embedding import (
    FAISS_AVAILABLE,
    SENTENCE_TRANSFORMERS_AVAILABLE,
    ContextCache,
    EmbeddingGenerator,
    SemanticSearch,
)
from assetutilities.agent_os.commands.context.optimizer import OptimizedContext
from assetutilities.agent_os.commands.context.processor import ContextProcessor

# Re-export optional dependencies for test patching compatibility
try:
    from sentence_transformers import SentenceTransformer
except ImportError:
    SentenceTransformer = None  # type: ignore[assignment,misc]

try:
    import faiss
except ImportError:
    faiss = None  # type: ignore[assignment]

__all__ = [
    "APISignature",
    "Concept",
    "ContextCache",
    "ContextProcessor",
    "DocumentChunk",
    "DocumentChunker",
    "EmbeddingGenerator",
    "OptimizedContext",
    "Pattern",
    "SemanticSearch",
]
