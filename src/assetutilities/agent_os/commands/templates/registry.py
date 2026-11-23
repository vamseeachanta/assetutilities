# ABOUTME: Template registry for storing and retrieving template definitions.
# ABOUTME: Extracted from template_management.py TemplateRegistry class.
"""Template registry for the template management system."""

import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from assetutilities.agent_os.commands.templates.models import OperationResult, Template
from assetutilities.agent_os.commands.templates.validator import TemplateValidator

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


