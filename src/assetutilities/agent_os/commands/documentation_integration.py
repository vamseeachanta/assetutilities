# ABOUTME: Backward-compatible re-exports from decomposed docs/ subpackage.
# ABOUTME: All classes moved to focused modules under commands/docs/.
"""Backward-compatible re-exports from decomposed docs/ subpackage.

All classes have been moved to focused modules under commands/docs/.
Import from the new locations for new code.
"""

from assetutilities.agent_os.commands.docs.linker import ExternalDocumentationLinker
from assetutilities.agent_os.commands.docs.parser import MarkdownParser
from assetutilities.agent_os.commands.docs.processor import DocumentationProcessor
from assetutilities.agent_os.commands.docs.references import ReferenceManager
from assetutilities.agent_os.commands.docs.scanner import (
    DocumentReference,
    RepositoryDocumentationScanner,
)

__all__ = [
    "DocumentReference",
    "DocumentationProcessor",
    "ExternalDocumentationLinker",
    "MarkdownParser",
    "ReferenceManager",
    "RepositoryDocumentationScanner",
]
