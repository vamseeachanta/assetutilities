# ABOUTME: Re-export hub for template management subpackage.
# ABOUTME: Extracted from template_management.py for focused module organization.
"""Template management system -- extracted from template_management.py."""

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
