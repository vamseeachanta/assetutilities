"""Cross-Repository Integration for Agent OS.

This module provides functionality to distribute Agent OS commands
across multiple repositories in the ecosystem.
"""

from .distributor import CrossRepoDistributor
from .installer import CommandInstaller
from .updater import CommandUpdater

__all__ = ['CrossRepoDistributor', 'CommandInstaller', 'CommandUpdater']