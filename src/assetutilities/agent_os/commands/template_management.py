"""Template Management System.

This module provides comprehensive template management for creating and
customizing AI agents with predefined patterns, prompts, and capabilities.
"""

import re
import yaml
import json
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field, asdict
from urllib.parse import urlparse
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


class TemplateValidator:
    """Validates template structure and content."""

    def __init__(self):
        """Initialize validator."""
        self.valid_categories = {
            "general", "engineering", "analysis", "infrastructure", 
            "documentation", "testing", "deployment", "monitoring"
        }
        
        self.valid_response_formats = {
            "markdown", "json", "yaml", "xml", "html", "text"
        }
        
        self.known_capabilities = {
            # Core capabilities
            "text_generation", "question_answering", "task_decomposition",
            "documentation_reading", "code_generation", "code_review",
            "debugging", "testing", "data_analysis", "visualization_generation",
            "report_creation", "deployment_automation", "monitoring_setup",
            "documentation_generation", "api_documentation",
            
            # Specialized capabilities
            "architecture_design", "performance_optimization", "security_analysis",
            "api_development", "predictive_modeling", "anomaly_detection",
            "trend_analysis", "data_cleaning", "kubernetes_management",
            "cloud_architecture", "security_hardening", "performance_tuning",
            "diagram_generation", "changelog_management", "knowledge_base_creation",
            "tutorial_creation"
        }

    def validate_schema(self, template_data: Dict[str, Any]) -> ValidationResult:
        """Validate template schema."""
        errors = []
        warnings = []
        
        # Required fields
        required_fields = ["name", "version", "description", "category"]
        for field in required_fields:
            if field not in template_data or not template_data[field]:
                errors.append(f"Missing required field: {field}")
        
        # Version format
        if "version" in template_data:
            version = template_data["version"]
            if not re.match(r'^\d+\.\d+\.\d+$', version):
                warnings.append(f"Version '{version}' should follow semantic versioning (x.y.z)")
        
        # Category validation
        if "category" in template_data:
            category = template_data["category"]
            if category not in self.valid_categories:
                warnings.append(f"Unknown category '{category}'. Known: {sorted(self.valid_categories)}")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    def validate_capabilities(self, template_data: Dict[str, Any]) -> ValidationResult:
        """Validate capabilities structure."""
        errors = []
        warnings = []
        
        capabilities = template_data.get("capabilities", {})
        
        if not isinstance(capabilities, dict):
            errors.append("Capabilities must be a dictionary")
            return ValidationResult(is_valid=False, errors=errors)
        
        # Check core and specialized capabilities
        for cap_type in ["core", "specialized"]:
            if cap_type in capabilities:
                cap_list = capabilities[cap_type]
                if not isinstance(cap_list, list):
                    errors.append(f"Capabilities.{cap_type} must be a list")
                else:
                    for capability in cap_list:
                        if not isinstance(capability, str):
                            errors.append(f"Capability must be string: {capability}")
                        elif capability not in self.known_capabilities:
                            warnings.append(f"Unknown capability: {capability}")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    def validate_prompts(self, template_data: Dict[str, Any]) -> ValidationResult:
        """Validate prompts structure."""
        errors = []
        warnings = []
        
        prompts = template_data.get("prompts", [])
        
        if not isinstance(prompts, list):
            errors.append("Prompts must be a list")
            return ValidationResult(is_valid=False, errors=errors)
        
        for i, prompt in enumerate(prompts):
            if not isinstance(prompt, dict):
                errors.append(f"Prompt {i} must be a dictionary")
                continue
            
            # Required fields
            if "name" not in prompt or not prompt["name"]:
                errors.append(f"Prompt {i} missing required 'name' field")
            
            if "content" not in prompt or not prompt["content"]:
                errors.append(f"Prompt {i} missing required 'content' field")
            
            # Check for template variables
            content = prompt.get("content", "")
            variables = re.findall(r'\{(\w+)\}', content)
            if variables:
                warnings.append(f"Prompt '{prompt.get('name', i)}' contains variables: {variables}")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    def validate_responses(self, template_data: Dict[str, Any]) -> ValidationResult:
        """Validate response templates."""
        errors = []
        warnings = []
        
        responses = template_data.get("responses", [])
        
        if not isinstance(responses, list):
            errors.append("Responses must be a list")
            return ValidationResult(is_valid=False, errors=errors)
        
        for i, response in enumerate(responses):
            if not isinstance(response, dict):
                errors.append(f"Response {i} must be a dictionary")
                continue
            
            # Required fields
            if "name" not in response or not response["name"]:
                errors.append(f"Response {i} missing required 'name' field")
            
            if "content" not in response or not response["content"]:
                errors.append(f"Response {i} missing required 'content' field")
            
            # Format validation
            response_format = response.get("format", "markdown")
            if response_format not in self.valid_response_formats:
                errors.append(f"Response {i} invalid format: {response_format}")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    def validate_context_sources(self, template_data: Dict[str, Any]) -> ValidationResult:
        """Validate context sources."""
        errors = []
        warnings = []
        
        context_sources = template_data.get("context_sources", {})
        
        if not isinstance(context_sources, dict):
            errors.append("Context sources must be a dictionary")
            return ValidationResult(is_valid=False, errors=errors)
        
        # Validate repositories
        repositories = context_sources.get("repositories", {})
        if repositories and not isinstance(repositories, dict):
            errors.append("Context sources repositories must be a dictionary")
        else:
            for repo_name, description in repositories.items():
                if not repo_name:
                    errors.append("Repository name cannot be empty")
                if not isinstance(description, str):
                    warnings.append(f"Repository '{repo_name}' description should be a string")
        
        # Validate external URLs
        external = context_sources.get("external", [])
        if external and not isinstance(external, list):
            errors.append("Context sources external must be a list")
        else:
            for url in external:
                if not url:
                    errors.append("External URL cannot be empty")
                elif not self._is_valid_url(url):
                    warnings.append(f"Invalid URL format: {url}")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    def validate_template(self, template_data: Dict[str, Any]) -> ValidationResult:
        """Validate complete template."""
        all_errors = []
        all_warnings = []
        
        # Run all validations
        validations = [
            self.validate_schema(template_data),
            self.validate_capabilities(template_data),
            self.validate_prompts(template_data),
            self.validate_responses(template_data),
            self.validate_context_sources(template_data)
        ]
        
        for result in validations:
            all_errors.extend(result.errors)
            all_warnings.extend(result.warnings)
        
        return ValidationResult(
            is_valid=len(all_errors) == 0,
            errors=all_errors,
            warnings=all_warnings
        )

    def _is_valid_url(self, url: str) -> bool:
        """Check if URL is valid."""
        try:
            result = urlparse(url)
            return all([result.scheme, result.netloc])
        except Exception:
            return False


class TemplateRegistry:
    """Manages template storage and retrieval."""

    def __init__(self, templates_dir: Path):
        """Initialize registry.
        
        Args:
            templates_dir: Directory containing template files
        """
        self.templates_dir = Path(templates_dir)
        self.templates_dir.mkdir(parents=True, exist_ok=True)
        self.validator = TemplateValidator()

    def register_template(self, template_path: Path) -> OperationResult:
        """Register a new template.
        
        Args:
            template_path: Path to template YAML file
            
        Returns:
            Operation result
        """
        try:
            # Load and validate template
            with open(template_path, 'r') as f:
                template_data = yaml.safe_load(f)
            
            validation = self.validator.validate_template(template_data)
            if not validation.is_valid:
                return OperationResult(
                    success=False,
                    message=f"Template validation failed: {'; '.join(validation.errors)}"
                )
            
            # Copy to templates directory
            template_name = template_data["name"]
            dest_path = self.templates_dir / f"{template_name}.yaml"
            
            with open(dest_path, 'w') as f:
                yaml.dump(template_data, f, default_flow_style=False, indent=2)
            
            return OperationResult(
                success=True,
                message=f"Template '{template_name}' registered successfully",
                data={"template_name": template_name, "path": str(dest_path)}
            )
            
        except Exception as e:
            return OperationResult(success=False, message=f"Failed to register template: {e}")

    def get_template(self, template_name: str) -> Optional[Template]:
        """Get template by name.
        
        Args:
            template_name: Name of template
            
        Returns:
            Template object or None if not found
        """
        template_path = self.templates_dir / f"{template_name}.yaml"
        
        if not template_path.exists():
            return None
        
        try:
            with open(template_path, 'r') as f:
                template_data = yaml.safe_load(f)
            
            return Template.from_dict(template_data)
        except Exception:
            return None

    def list_templates(self) -> List[str]:
        """List all available template names.
        
        Returns:
            List of template names
        """
        template_files = list(self.templates_dir.glob("*.yaml"))
        return [f.stem for f in template_files]

    def search_templates(self, category: Optional[str] = None, 
                        capability: Optional[str] = None) -> List[Template]:
        """Search templates by criteria.
        
        Args:
            category: Filter by category
            capability: Filter by capability
            
        Returns:
            List of matching templates
        """
        templates = []
        
        for template_name in self.list_templates():
            template = self.get_template(template_name)
            if template is None:
                continue
            
            # Filter by category
            if category and template.category != category:
                continue
            
            # Filter by capability
            if capability:
                all_capabilities = template.capabilities.core + template.capabilities.specialized
                if capability not in all_capabilities:
                    continue
            
            templates.append(template)
        
        return templates

    def update_template(self, template_name: str, new_template_path: Path) -> OperationResult:
        """Update existing template.
        
        Args:
            template_name: Name of template to update
            new_template_path: Path to new template file
            
        Returns:
            Operation result
        """
        existing_path = self.templates_dir / f"{template_name}.yaml"
        
        if not existing_path.exists():
            return OperationResult(
                success=False,
                message=f"Template '{template_name}' not found"
            )
        
        # Validate new template
        try:
            with open(new_template_path, 'r') as f:
                template_data = yaml.safe_load(f)
            
            validation = self.validator.validate_template(template_data)
            if not validation.is_valid:
                return OperationResult(
                    success=False,
                    message=f"Template validation failed: {'; '.join(validation.errors)}"
                )
            
            # Update template
            with open(existing_path, 'w') as f:
                yaml.dump(template_data, f, default_flow_style=False, indent=2)
            
            return OperationResult(
                success=True,
                message=f"Template '{template_name}' updated successfully"
            )
            
        except Exception as e:
            return OperationResult(success=False, message=f"Failed to update template: {e}")

    def delete_template(self, template_name: str) -> OperationResult:
        """Delete template.
        
        Args:
            template_name: Name of template to delete
            
        Returns:
            Operation result
        """
        template_path = self.templates_dir / f"{template_name}.yaml"
        
        if not template_path.exists():
            return OperationResult(
                success=False,
                message=f"Template '{template_name}' not found"
            )
        
        try:
            template_path.unlink()
            return OperationResult(
                success=True,
                message=f"Template '{template_name}' deleted successfully"
            )
        except Exception as e:
            return OperationResult(success=False, message=f"Failed to delete template: {e}")


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


class TemplateInstantiator:
    """Instantiates templates into agent structures."""

    def instantiate_template(self, template: Template, agent_dir: Path) -> OperationResult:
        """Instantiate template into agent directory.
        
        Args:
            template: Template to instantiate
            agent_dir: Target agent directory
            
        Returns:
            Operation result
        """
        try:
            # Setup directory structure
            self.setup_directory_structure(agent_dir)
            
            # Generate agent configuration
            agent_name = agent_dir.name
            config = self.generate_agent_config(template, agent_name)
            
            # Save agent.yaml
            with open(agent_dir / "agent.yaml", 'w') as f:
                yaml.dump(config, f, default_flow_style=False, indent=2)
            
            # Create prompt files
            self.create_prompt_files(template, agent_dir)
            
            # Create response templates
            self.create_response_templates(template, agent_dir)
            
            # Setup workflow hooks if any
            if template.workflow_hooks:
                self.setup_workflow_hooks(template, agent_dir)
            
            return OperationResult(
                success=True,
                message=f"Template '{template.name}' instantiated successfully",
                data={"agent_dir": str(agent_dir)}
            )
            
        except Exception as e:
            return OperationResult(success=False, message=f"Failed to instantiate template: {e}")

    def setup_directory_structure(self, agent_dir: Path) -> None:
        """Setup agent directory structure.
        
        Args:
            agent_dir: Agent directory path
        """
        directories = [
            agent_dir,
            agent_dir / "templates",
            agent_dir / "templates" / "prompts",
            agent_dir / "templates" / "responses",
            agent_dir / "context",
            agent_dir / "workflows"
        ]
        
        for directory in directories:
            directory.mkdir(parents=True, exist_ok=True)

    def generate_agent_config(self, template: Template, agent_name: str) -> Dict[str, Any]:
        """Generate agent configuration from template.
        
        Args:
            template: Template to use
            agent_name: Name of the agent
            
        Returns:
            Agent configuration dictionary
        """
        all_capabilities = template.capabilities.core + template.capabilities.specialized
        
        config = {
            "name": agent_name,
            "template": template.name,
            "version": template.version,
            "description": f"Agent created from {template.name} template",
            "capabilities": all_capabilities,
            "context": {
                "repositories": template.context_sources.repositories,
                "external_sources": template.context_sources.external
            },
            "created_at": datetime.now().isoformat(),
            "template_version": template.version
        }
        
        return config

    def create_prompt_files(self, template: Template, agent_dir: Path) -> None:
        """Create prompt files from template.
        
        Args:
            template: Template containing prompts
            agent_dir: Agent directory
        """
        prompts_dir = agent_dir / "templates" / "prompts"
        
        for prompt in template.prompts:
            prompt_name = prompt.get("name", "unnamed")
            prompt_content = prompt.get("content", "")
            
            prompt_file = prompts_dir / f"{prompt_name}.md"
            with open(prompt_file, 'w') as f:
                f.write(prompt_content)

    def create_response_templates(self, template: Template, agent_dir: Path) -> None:
        """Create response template files.
        
        Args:
            template: Template containing responses
            agent_dir: Agent directory
        """
        responses_dir = agent_dir / "templates" / "responses"
        
        for response in template.responses:
            response_name = response.get("name", "unnamed")
            response_content = response.get("content", "")
            
            response_file = responses_dir / f"{response_name}.md"
            with open(response_file, 'w') as f:
                f.write(response_content)

    def setup_workflow_hooks(self, template: Template, agent_dir: Path) -> None:
        """Setup workflow hooks from template.
        
        Args:
            template: Template containing workflow hooks
            agent_dir: Agent directory
        """
        workflows_dir = agent_dir / "workflows"
        
        hooks_config = {
            "hooks": template.workflow_hooks,
            "created_from_template": template.name,
            "created_at": datetime.now().isoformat()
        }
        
        with open(workflows_dir / "hooks.yaml", 'w') as f:
            yaml.dump(hooks_config, f, default_flow_style=False, indent=2)


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