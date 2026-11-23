# ABOUTME: Backward-compatible re-exports from decomposed specs/ subpackage.
# ABOUTME: All classes moved to focused modules under commands/specs/.
"""Backward-compatible re-exports from decomposed specs/ subpackage.

All classes have been moved to focused modules under commands/specs/.
Import from the new locations for new code.
"""

from assetutilities.agent_os.commands.specs.models import (
    EnhancedSpecsConfig,
    OperationResult,
    WorkflowHook,
)
from assetutilities.agent_os.commands.specs.manager import SpecsIntegrationManager
from assetutilities.agent_os.commands.specs.referencer import CrossRepositoryReferencer
from assetutilities.agent_os.commands.specs.refresher import WorkflowRefresher
from assetutilities.agent_os.commands.specs.tracker import PromptEvolutionTracker

__all__ = [
    "CrossRepositoryReferencer",
    "EnhancedSpecsConfig",
    "OperationResult",
    "PromptEvolutionTracker",
    "SpecsIntegrationManager",
    "WorkflowHook",
    "WorkflowRefresher",
]
