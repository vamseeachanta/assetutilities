# ABOUTME: Data models for specs integration system.
# ABOUTME: Extracted from specs_integration.py dataclasses.
"""Data models for the enhanced specs integration system."""

import yaml
from pathlib import Path
from typing import List, Dict, Any
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class OperationResult:
    """Result of integration operation."""
    success: bool
    message: str = ""
    data: Any = None


@dataclass
class WorkflowHook:
    """Workflow hook configuration."""
    name: str
    trigger: str
    action: str
    config: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowHook':
        """Create hook from dictionary."""
        return cls(
            name=data.get("name", ""),
            trigger=data.get("trigger", ""),
            action=data.get("action", ""),
            config=data.get("config", {}),
            enabled=data.get("enabled", True)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert hook to dictionary."""
        return {
            "name": self.name,
            "trigger": self.trigger,
            "action": self.action,
            "config": self.config,
            "enabled": self.enabled
        }

    def is_valid(self) -> bool:
        """Check if hook configuration is valid."""
        return bool(self.name) and bool(self.trigger) and bool(self.action)


@dataclass
class EnhancedSpecsConfig:
    """Enhanced specs integration configuration."""
    agent_name: str
    integration_type: str = "enhanced_create_specs"
    workflow_hooks: List[WorkflowHook] = field(default_factory=list)
    cross_repo_references: List[str] = field(default_factory=list)
    prompt_evolution_enabled: bool = True
    auto_refresh_enabled: bool = True
    refresh_interval: int = 3600  # 1 hour in seconds

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnhancedSpecsConfig':
        """Create configuration from dictionary."""
        hooks = [WorkflowHook.from_dict(hook_data) for hook_data in data.get("workflow_hooks", [])]
        
        return cls(
            agent_name=data.get("agent_name", ""),
            integration_type=data.get("integration_type", "enhanced_create_specs"),
            workflow_hooks=hooks,
            cross_repo_references=data.get("cross_repo_references", []),
            prompt_evolution_enabled=data.get("prompt_evolution_enabled", True),
            auto_refresh_enabled=data.get("auto_refresh_enabled", True),
            refresh_interval=data.get("refresh_interval", 3600)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "agent_name": self.agent_name,
            "integration_type": self.integration_type,
            "workflow_hooks": [hook.to_dict() for hook in self.workflow_hooks],
            "cross_repo_references": self.cross_repo_references,
            "prompt_evolution_enabled": self.prompt_evolution_enabled,
            "auto_refresh_enabled": self.auto_refresh_enabled,
            "refresh_interval": self.refresh_interval,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }

    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return bool(self.agent_name) and self.refresh_interval > 0


