"""
AssetUtilities DevTools - Repository Management and Automation Tools

This module provides command-line tools for managing repositories:
- modernize_deps: Consolidate and modernize dependency management
- propagate_commands: Distribute slash commands across repositories
- organize_structure: Enforce module-based project organization
"""

from .modernize_deps import DependencyModernizer, modernize_repository, find_python_repositories
from .propagate_commands import CommandPropagator, find_repositories
from .organize_structure import ProjectOrganizer, organize_repository
from .cli import main

__version__ = "1.0.0"
__all__ = [
    "DependencyModernizer",
    "CommandPropagator",
    "ProjectOrganizer",
    "modernize_repository",
    "find_python_repositories",
    "find_repositories",
    "organize_repository",
    "main"
]