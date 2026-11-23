# ABOUTME: Backward-compatible re-exports from decomposed cli_components/ subpackage.
# ABOUTME: All classes moved to focused modules under commands/cli_components/.
"""Backward-compatible re-exports from decomposed cli_components/ subpackage.

All classes have been moved to focused modules under commands/cli_components/.
Import from the new locations for new code.
"""

from assetutilities.agent_os.commands.cli_components.models import (
    ErrorResult,
    ParsedCommand,
    ValidationResult,
)
from assetutilities.agent_os.commands.cli_components.error_handler import ErrorHandler
from assetutilities.agent_os.commands.cli_components.help_system import HelpSystem
from assetutilities.agent_os.commands.cli_components.interactive import InteractiveMode
from assetutilities.agent_os.commands.cli_components.interface import CommandLineInterface, main
from assetutilities.agent_os.commands.cli_components.manager import CLIManager
from assetutilities.agent_os.commands.cli_components.progress import ProgressIndicator

__all__ = [
    "CLIManager",
    "CommandLineInterface",
    "ErrorHandler",
    "ErrorResult",
    "HelpSystem",
    "InteractiveMode",
    "ParsedCommand",
    "ProgressIndicator",
    "ValidationResult",
    "main",
]
