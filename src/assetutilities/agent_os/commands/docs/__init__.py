# ABOUTME: Re-export hub for documentation integration subpackage.
# ABOUTME: Extracted from documentation_integration.py for focused module organization.
"""Documentation integration system -- extracted from documentation_integration.py."""

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
