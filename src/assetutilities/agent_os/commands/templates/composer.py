# ABOUTME: Template composition engine for building agent configurations.
# ABOUTME: Extracted from template_management.py TemplateComposer class.
"""Template composition for the template management system."""

from __future__ import annotations

import yaml
from pathlib import Path
from typing import TYPE_CHECKING, List, Dict, Any, Optional
from datetime import datetime

from assetutilities.agent_os.commands.templates.models import Template, OperationResult

if TYPE_CHECKING:
    from assetutilities.agent_os.commands.templates.registry import TemplateRegistry

class TemplateComposer:
    """Composes templates and handles automatic selection."""

    def __init__(self, registry: TemplateRegistry):
        """Initialize composer.
        
        Args:
            registry: Template registry
        """
        self.registry = registry

    def compose_templates(self, primary: str, mixins: List[str]) -> Template:
        """Compose multiple templates.
        
        Args:
            primary: Primary template name
            mixins: List of mixin template names
            
        Returns:
            Composed template
        """
        # Get primary template
        composite = self.registry.get_template(primary)
        if composite is None:
            raise ValueError(f"Primary template '{primary}' not found")
        
        # Merge mixin templates
        for mixin_name in mixins:
            mixin = self.registry.get_template(mixin_name)
            if mixin is None:
                continue
            
            # Merge capabilities
            composite.capabilities.core.extend(mixin.capabilities.core)
            composite.capabilities.specialized.extend(mixin.capabilities.specialized)
            
            # Merge context sources
            composite.context_sources.repositories.update(mixin.context_sources.repositories)
            composite.context_sources.external.extend(mixin.context_sources.external)
            
            # Merge prompts and responses
            composite.prompts.extend(mixin.prompts)
            composite.responses.extend(mixin.responses)
            composite.workflow_hooks.extend(mixin.workflow_hooks)
        
        # Remove duplicates
        composite = self._deduplicate_template(composite)
        
        return composite

    def select_template(self, agent_type: str, module_context: Dict[str, Any]) -> Template:
        """Select appropriate template based on context.
        
        Args:
            agent_type: Type of agent or 'auto' for automatic selection
            module_context: Context information about the module
            
        Returns:
            Selected template
        """
        if agent_type == "auto":
            agent_type = self.infer_agent_type(module_context)
        
        template = self.registry.get_template(agent_type)
        if template is None:
            # Fallback to general purpose template
            template = self.registry.get_template("general-purpose")
            if template is None:
                # Create basic template if none exists
                template = self._create_basic_template()
        
        return template

    def infer_agent_type(self, module_context: Dict[str, Any]) -> str:
        """Infer agent type from module context.
        
        Args:
            module_context: Context information
            
        Returns:
            Inferred agent type
        """
        # Check for engineering indicators
        engineering_indicators = [
            "has_code_files", "has_tests", "has_api", "language",
            "framework", "database", "deployment"
        ]
        
        analysis_indicators = [
            "has_data_files", "visualization", "statistics", "machine_learning",
            "data_processing", "jupyter_notebooks"
        ]
        
        documentation_indicators = [
            "has_docs", "markdown_files", "api_documentation", "user_guides",
            "tutorials", "wiki"
        ]
        
        infrastructure_indicators = [
            "docker", "kubernetes", "ci_cd", "deployment", "monitoring",
            "infrastructure_as_code", "cloud_provider"
        ]
        
        # Score each category
        scores = {
            "engineering": sum(1 for indicator in engineering_indicators if module_context.get(indicator)),
            "analysis": sum(1 for indicator in analysis_indicators if module_context.get(indicator)),
            "documentation": sum(1 for indicator in documentation_indicators if module_context.get(indicator)),
            "infrastructure": sum(1 for indicator in infrastructure_indicators if module_context.get(indicator))
        }
        
        # Return category with highest score, or general if tied
        if max(scores.values()) == 0:
            return "general-purpose"
        
        return max(scores.items(), key=lambda x: x[1])[0]

    def _deduplicate_template(self, template: Template) -> Template:
        """Remove duplicates from template."""
        # Deduplicate capabilities
        template.capabilities.core = list(dict.fromkeys(template.capabilities.core))
        template.capabilities.specialized = list(dict.fromkeys(template.capabilities.specialized))
        
        # Deduplicate external sources
        template.context_sources.external = list(dict.fromkeys(template.context_sources.external))
        
        # Deduplicate prompts and responses by name
        seen_prompts = set()
        unique_prompts = []
        for prompt in template.prompts:
            name = prompt.get("name", "")
            if name not in seen_prompts:
                seen_prompts.add(name)
                unique_prompts.append(prompt)
        template.prompts = unique_prompts
        
        seen_responses = set()
        unique_responses = []
        for response in template.responses:
            name = response.get("name", "")
            if name not in seen_responses:
                seen_responses.add(name)
                unique_responses.append(response)
        template.responses = unique_responses
        
        return template

    def _create_basic_template(self) -> Template:
        """Create a basic fallback template."""
        template = Template(
            name="basic",
            version="1.0.0",
            description="Basic template for general purpose agents",
            category="general"
        )
        
        template.capabilities.core = ["text_generation", "question_answering"]
        template.prompts = [{
            "name": "standard_task",
            "content": "Please help with the following task: {task_description}"
        }]
        template.responses = [{
            "name": "task_completion",
            "format": "markdown",
            "content": "## Task Completed\n\n{result}"
        }]
        
        return template


