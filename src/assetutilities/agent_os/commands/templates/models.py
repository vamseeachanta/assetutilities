# ABOUTME: Data models for template management system.
# ABOUTME: Extracted from template_management.py dataclasses.
"""Data models for the template management system."""

import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field
from datetime import datetime

@dataclass
class ValidationResult:
    """Result of template validation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class OperationResult:
    """Result of template operation."""
    success: bool
    message: str = ""
    data: Any = None


@dataclass
class Capabilities:
    """Agent capabilities structure."""
    core: List[str] = field(default_factory=list)
    specialized: List[str] = field(default_factory=list)


@dataclass
class ContextSources:
    """Context sources for agent."""
    repositories: Dict[str, str] = field(default_factory=dict)
    external: List[str] = field(default_factory=list)


@dataclass
class Template:
    """Template data structure."""
    name: str
    version: str
    description: str
    category: str
    capabilities: Capabilities = field(default_factory=Capabilities)
    context_sources: ContextSources = field(default_factory=ContextSources)
    prompts: List[Dict[str, Any]] = field(default_factory=list)
    responses: List[Dict[str, Any]] = field(default_factory=list)
    workflow_hooks: List[Dict[str, Any]] = field(default_factory=list)

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'Template':
        """Create template from dictionary."""
        template = cls(
            name=data.get("name", ""),
            version=data.get("version", ""),
            description=data.get("description", ""),
            category=data.get("category", "")
        )
        
        # Parse capabilities
        if "capabilities" in data:
            cap_data = data["capabilities"]
            template.capabilities = Capabilities(
                core=cap_data.get("core", []),
                specialized=cap_data.get("specialized", [])
            )
        
        # Parse context sources
        if "context_sources" in data:
            ctx_data = data["context_sources"]
            template.context_sources = ContextSources(
                repositories=ctx_data.get("repositories", {}),
                external=ctx_data.get("external", [])
            )
        
        # Parse prompts, responses, and workflow hooks
        template.prompts = data.get("prompts", [])
        template.responses = data.get("responses", [])
        template.workflow_hooks = data.get("workflow_hooks", [])
        
        return template

    def to_dict(self) -> Dict[str, Any]:
        """Convert template to dictionary."""
        return {
            "name": self.name,
            "version": self.version,
            "description": self.description,
            "category": self.category,
            "capabilities": {
                "core": self.capabilities.core,
                "specialized": self.capabilities.specialized
            },
            "context_sources": {
                "repositories": self.context_sources.repositories,
                "external": self.context_sources.external
            },
            "prompts": self.prompts,
            "responses": self.responses,
            "workflow_hooks": self.workflow_hooks
        }

    def is_valid(self) -> bool:
        """Check if template has required fields."""
        return (
            bool(self.name) and
            bool(self.version) and
            bool(self.description) and
            bool(self.category)
        )


