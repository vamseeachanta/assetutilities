# ABOUTME: Template instantiation engine for creating agents from templates.
# ABOUTME: Extracted from template_management.py TemplateInstantiator class.
"""Template instantiation for the template management system."""

import yaml
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from assetutilities.agent_os.commands.templates.models import OperationResult, Template

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


