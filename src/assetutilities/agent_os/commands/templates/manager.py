# ABOUTME: Top-level template manager coordinating all template operations.
# ABOUTME: Extracted from template_management.py TemplateManager class.
"""Manages the overall template management workflow."""

from pathlib import Path
from typing import List, Dict, Any, Optional

from assetutilities.agent_os.commands.templates.models import OperationResult, Template
from assetutilities.agent_os.commands.templates.validator import TemplateValidator
from assetutilities.agent_os.commands.templates.registry import TemplateRegistry
from assetutilities.agent_os.commands.templates.composer import TemplateComposer
from assetutilities.agent_os.commands.templates.instantiator import TemplateInstantiator

class TemplateManager:
    """Main template management interface."""

    def __init__(self, templates_dir: Path):
        """Initialize template manager.
        
        Args:
            templates_dir: Directory for template storage
        """
        self.registry = TemplateRegistry(templates_dir)
        self.composer = TemplateComposer(self.registry)
        self.instantiator = TemplateInstantiator()
        self.validator = TemplateValidator()

    def create_agent_from_template(self, template_name: str, agent_name: str, 
                                 agent_dir: Path) -> OperationResult:
        """Create agent from single template.
        
        Args:
            template_name: Name of template to use
            agent_name: Name for the new agent
            agent_dir: Directory for the agent
            
        Returns:
            Operation result
        """
        template = self.registry.get_template(template_name)
        if template is None:
            return OperationResult(
                success=False,
                message=f"Template '{template_name}' not found"
            )
        
        return self.instantiator.instantiate_template(template, agent_dir)

    def create_agent_with_composition(self, primary_template: str, mixin_templates: List[str],
                                    agent_name: str, agent_dir: Path) -> OperationResult:
        """Create agent with template composition.
        
        Args:
            primary_template: Primary template name
            mixin_templates: List of mixin template names
            agent_name: Name for the new agent
            agent_dir: Directory for the agent
            
        Returns:
            Operation result
        """
        try:
            composite_template = self.composer.compose_templates(primary_template, mixin_templates)
            return self.instantiator.instantiate_template(composite_template, agent_dir)
        except Exception as e:
            return OperationResult(success=False, message=str(e))

    def create_agent_auto(self, agent_name: str, agent_dir: Path, 
                         module_context: Dict[str, Any]) -> OperationResult:
        """Create agent with automatic template selection.
        
        Args:
            agent_name: Name for the new agent
            agent_dir: Directory for the agent
            module_context: Context information for template selection
            
        Returns:
            Operation result
        """
        template = self.composer.select_template("auto", module_context)
        return self.instantiator.instantiate_template(template, agent_dir)

    def customize_template(self, template: Template, 
                          options: Dict[str, Any]) -> Template:
        """Customize template with additional options.
        
        Args:
            template: Base template
            options: Customization options
            
        Returns:
            Customized template
        """
        # Add additional capabilities
        if "additional_capabilities" in options:
            template.capabilities.specialized.extend(options["additional_capabilities"])
        
        # Add custom prompts
        if "custom_prompts" in options:
            template.prompts.extend(options["custom_prompts"])
        
        # Add custom context repositories
        if "context_repositories" in options:
            template.context_sources.repositories.update(options["context_repositories"])
        
        return template

    def list_available_templates(self) -> List[Dict[str, Any]]:
        """List all available templates with details.
        
        Returns:
            List of template information dictionaries
        """
        templates_info = []
        
        for template_name in self.registry.list_templates():
            template = self.registry.get_template(template_name)
            if template:
                templates_info.append({
                    "name": template.name,
                    "version": template.version,
                    "description": template.description,
                    "category": template.category,
                    "capabilities": {
                        "core": template.capabilities.core,
                        "specialized": template.capabilities.specialized
                    }
                })
        
        return templates_info

    def get_template_info(self, template_name: str) -> Optional[Dict[str, Any]]:
        """Get detailed information about a template.
        
        Args:
            template_name: Name of template
            
        Returns:
            Template information dictionary or None
        """
        template = self.registry.get_template(template_name)
        if template is None:
            return None
        
        return {
            "name": template.name,
            "version": template.version,
            "description": template.description,
            "category": template.category,
            "capabilities": {
                "core": template.capabilities.core,
                "specialized": template.capabilities.specialized
            },
            "context_sources": {
                "repositories": template.context_sources.repositories,
                "external": template.context_sources.external
            },
            "prompts": [{"name": p.get("name", ""), "content": p.get("content", "")[:100] + "..."} 
                       for p in template.prompts],
            "responses": [{"name": r.get("name", ""), "format": r.get("format", "")} 
                         for r in template.responses]
        }

    def install_default_templates(self) -> OperationResult:
        """Install default templates.
        
        Returns:
            Operation result
        """
        default_templates = self._get_default_templates()
        
        installed = 0
        errors = []
        
        for template_data in default_templates:
            try:
                template_name = template_data["name"]
                template_path = self.registry.templates_dir / f"{template_name}.yaml"
                
                with open(template_path, 'w') as f:
                    yaml.dump(template_data, f, default_flow_style=False, indent=2)
                
                installed += 1
            except Exception as e:
                errors.append(f"Failed to install {template_data.get('name', 'unknown')}: {e}")
        
        if errors:
            return OperationResult(
                success=False,
                message=f"Installed {installed} templates with {len(errors)} errors: {'; '.join(errors)}"
            )
        
        return OperationResult(
            success=True,
            message=f"Successfully installed {installed} default templates"
        )

    def _get_default_templates(self) -> List[Dict[str, Any]]:
        """Get default template configurations."""
        return [
            {
                "name": "general-purpose",
                "version": "1.0.0",
                "description": "Basic agent with standard capabilities",
                "category": "general",
                "capabilities": {
                    "core": ["text_generation", "question_answering", "task_decomposition"],
                    "specialized": ["basic_code_understanding", "simple_data_analysis"]
                },
                "context_sources": {
                    "repositories": {"assetutilities": "Core utilities and patterns"},
                    "external": ["https://docs.python.org"]
                },
                "prompts": [
                    {
                        "name": "standard_task",
                        "content": "Given the task: {task_description}\n\nPlease:\n1. Analyze the requirements\n2. Break down into subtasks\n3. Execute systematically\n4. Provide clear output"
                    }
                ],
                "responses": [
                    {
                        "name": "task_completion",
                        "format": "markdown",
                        "content": "## Task Completed\n\n### Summary\n{summary}\n\n### Actions Taken\n{actions}\n\n### Results\n{results}"
                    }
                ]
            },
            {
                "name": "engineering",
                "version": "1.0.0",
                "description": "Engineering-focused agent with technical capabilities",
                "category": "engineering",
                "capabilities": {
                    "core": ["code_generation", "code_review", "debugging", "testing"],
                    "specialized": ["architecture_design", "performance_optimization", "security_analysis"]
                },
                "context_sources": {
                    "repositories": {"assetutilities": "Engineering patterns and utilities"},
                    "external": ["https://engineering.best-practices.com"]
                },
                "prompts": [
                    {
                        "name": "code_review",
                        "content": "Review the following code for:\n- Code quality and style\n- Performance implications\n- Security concerns\n- Best practices adherence\n\nCode: {code}"
                    }
                ],
                "responses": [
                    {
                        "name": "code_review_result",
                        "format": "markdown",
                        "content": "## Code Review Results\n\n### Quality Score: {score}/10\n\n### Issues Found\n{issues}\n\n### Recommendations\n{recommendations}"
                    }
                ]
            }
        ]