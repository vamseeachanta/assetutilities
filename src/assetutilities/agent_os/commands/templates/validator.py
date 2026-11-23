# ABOUTME: Template validation engine for checking template structure and content.
# ABOUTME: Extracted from template_management.py TemplateValidator class.
"""Template validation for the template management system."""

import re
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from assetutilities.agent_os.commands.templates.models import ValidationResult

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


