# ABOUTME: Backward-compatible re-exports from decomposed templates/ subpackage.
# ABOUTME: All classes moved to focused modules under commands/templates/.
"""Backward-compatible re-exports from decomposed templates/ subpackage.

All classes have been moved to focused modules under commands/templates/.
Import from the new locations for new code.
"""

from assetutilities.agent_os.commands.templates.models import (
    Capabilities,
    ContextSources,
    OperationResult,
    Template,
    ValidationResult,
)
from assetutilities.agent_os.commands.templates.composer import TemplateComposer
from assetutilities.agent_os.commands.templates.instantiator import TemplateInstantiator
from assetutilities.agent_os.commands.templates.manager import TemplateManager
from assetutilities.agent_os.commands.templates.registry import TemplateRegistry
from assetutilities.agent_os.commands.templates.validator import TemplateValidator

__all__ = [
    "Capabilities",
    "ContextSources",
    "OperationResult",
    "Template",
    "TemplateComposer",
    "TemplateInstantiator",
    "TemplateManager",
    "TemplateRegistry",
    "TemplateValidator",
    "ValidationResult",
]
