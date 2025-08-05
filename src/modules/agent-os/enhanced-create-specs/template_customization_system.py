#!/usr/bin/env python3
"""
Template Customization System for Enhanced Create-Specs Workflow.

This module provides comprehensive template customization with:
- Template variant selection and management
- Custom field configuration
- Template inheritance and override system
- Conditional section rendering
- User preferences and organization standards
- Template validation and quality checks

Author: Enhanced Create-Specs Workflow
Created: 2025-08-05
Module: agent-os/enhanced-create-specs
"""

import os
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any, Union, Callable
from dataclasses import dataclass, field, asdict
from enum import Enum
import re
from copy import deepcopy
import logging


class SectionType(Enum):
    """Enumeration of template section types."""
    REQUIRED = "required"
    OPTIONAL = "optional"
    CONDITIONAL = "conditional"
    CUSTOM = "custom"


class RenderCondition(Enum):
    """Enumeration of rendering conditions."""
    ALWAYS = "always"
    NEVER = "never"
    IF_EXISTS = "if_exists"
    IF_NOT_EXISTS = "if_not_exists"
    IF_TRUE = "if_true"
    IF_FALSE = "if_false"
    CUSTOM_FUNCTION = "custom_function"


@dataclass
class TemplateSection:
    """Data class for template section configuration."""
    name: str
    title: str
    content_template: str
    section_type: SectionType = SectionType.OPTIONAL
    render_condition: RenderCondition = RenderCondition.ALWAYS
    condition_field: str = ""
    condition_function: Optional[Callable] = None
    order: int = 100
    depends_on: List[str] = field(default_factory=list)
    excludes: List[str] = field(default_factory=list)
    variables: Dict[str, Any] = field(default_factory=dict)
    description: str = ""
    examples: List[str] = field(default_factory=list)


@dataclass
class TemplateVariant:
    """Data class for template variant configuration."""
    name: str
    display_name: str
    description: str
    sections: List[str] = field(default_factory=list)
    excluded_sections: List[str] = field(default_factory=list)
    default_variables: Dict[str, Any] = field(default_factory=dict)
    inherits_from: Optional[str] = None
    target_audience: List[str] = field(default_factory=list)
    use_cases: List[str] = field(default_factory=list)
    complexity_level: str = "medium"  # minimal, medium, comprehensive
    
    def __post_init__(self):
        """Post-initialization processing."""
        if not self.sections and not self.inherits_from:
            # Default sections for standalone variants
            self.sections = [
                "header",
                "overview", 
                "scope",
                "deliverables"
            ]


@dataclass
class UserPreferences:
    """Data class for user customization preferences."""
    preferred_variant: str = "enhanced"
    default_sections: List[str] = field(default_factory=list)
    custom_variables: Dict[str, Any] = field(default_factory=dict)
    organization_standards: Dict[str, Any] = field(default_factory=dict)
    section_preferences: Dict[str, Dict[str, Any]] = field(default_factory=dict)
    quality_requirements: Dict[str, Any] = field(default_factory=dict)


@dataclass
class OrganizationStandards:
    """Data class for organization-wide template standards."""
    required_sections: List[str] = field(default_factory=list)
    forbidden_sections: List[str] = field(default_factory=list)
    mandatory_variables: Dict[str, Any] = field(default_factory=dict)
    formatting_rules: Dict[str, Any] = field(default_factory=dict)
    quality_gates: Dict[str, Any] = field(default_factory=dict)
    approval_requirements: Dict[str, Any] = field(default_factory=dict)


class TemplateRegistry:
    """Registry for managing template sections and variants."""
    
    def __init__(self):
        self.sections: Dict[str, TemplateSection] = {}
        self.variants: Dict[str, TemplateVariant] = {}
        self.condition_functions: Dict[str, Callable] = {}
        self._initialize_default_sections()
        self._initialize_default_variants()
        self._initialize_default_conditions()
    
    def _initialize_default_sections(self):
        """Initialize default template sections."""
        # Header section
        self.sections["header"] = TemplateSection(
            name="header",
            title="Document Header",
            content_template="""# {{title}}

> **Module:** {{module_name}}
> **Spec:** {{spec_name}}
> **Sub-Agent:** {{sub_agent_type}}
> **Created:** {{creation_date}}
> **Status:** {{status}}
> **AI Context:** {{ai_context_description}}""",
            section_type=SectionType.REQUIRED,
            order=1,
            description="Document header with metadata"
        )
        
        # Prompt Summary section
        self.sections["prompt_summary"] = TemplateSection(
            name="prompt_summary",
            title="Prompt Summary",
            content_template="""## Prompt Summary

**Original Request:** {{original_request}}

**Context Provided:** {{context_provided}}

**Clarifications Made:** 
{{#clarifications_made}}
- {{.}}
{{/clarifications_made}}

**Reuse Notes:** {{reuse_notes}}

**Prompt Evolution:** {{prompt_evolution}}""",
            section_type=SectionType.OPTIONAL,
            render_condition=RenderCondition.IF_EXISTS,
            condition_field="prompt_summary",
            order=10,
            description="Summary of original prompt and clarifications for reuse"
        )
        
        # Executive Summary section
        self.sections["executive_summary"] = TemplateSection(
            name="executive_summary",
            title="Executive Summary",
            content_template="""## Executive Summary

### Purpose
{{executive_summary.purpose}}

### Impact
- **Business Value:** {{executive_summary.impact.business_value}}
- **User Benefit:** {{executive_summary.impact.user_benefit}}
- **Technical Advancement:** {{executive_summary.impact.technical_advancement}}

### Scope
- **Effort Estimate:** {{executive_summary.scope.effort_estimate}}
- **Timeline:** {{executive_summary.scope.timeline}}
- **Dependencies:** {{executive_summary.scope.dependencies}}

### Key Outcomes
{{#executive_summary.key_outcomes}}
{{@index}}. {{.}}
{{/executive_summary.key_outcomes}}""",
            section_type=SectionType.OPTIONAL,
            render_condition=RenderCondition.IF_EXISTS,
            condition_field="executive_summary",
            order=20,
            description="High-level summary for stakeholders and decision makers"
        )
        
        # System Overview section
        self.sections["system_overview"] = TemplateSection(
            name="system_overview",
            title="System Overview",
            content_template="""## System Overview

```mermaid
{{mermaid_diagram}}
```

### Flow Description
{{flow_description}}

### Integration Points
{{#integration_points}}
- **{{name}}:** {{description}}
{{/integration_points}}""",
            section_type=SectionType.OPTIONAL,
            render_condition=RenderCondition.IF_EXISTS,
            condition_field="mermaid_diagram",
            order=30,
            description="Visual system overview with mermaid diagrams"
        )
        
        # User Stories section
        self.sections["user_stories"] = TemplateSection(
            name="user_stories",
            title="User Stories",
            content_template="""## User Stories

{{#user_stories}}
### {{title}}

**As a** {{user_type}},  
**I want to** {{want}},  
**So that** {{benefit}}.

{{#acceptance_criteria}}
**Acceptance Criteria:**
{{#criteria}}
- [ ] {{.}}
{{/criteria}}
{{/acceptance_criteria}}

{{#workflow}}
**Workflow:**
{{#steps}}
{{@index}}. {{.}}
{{/steps}}
{{/workflow}}

{{/user_stories}}""",
            section_type=SectionType.OPTIONAL,
            render_condition=RenderCondition.IF_EXISTS,
            condition_field="user_stories",
            order=40,
            description="User-centered requirements and acceptance criteria"
        )
        
        # Basic Overview section (simplified alternative)
        self.sections["overview"] = TemplateSection(
            name="overview",
            title="Overview",
            content_template="""## Overview

{{overview_description}}""",
            section_type=SectionType.REQUIRED,
            order=15,
            description="Simple overview description"
        )
        
        # Spec Scope section
        self.sections["scope"] = TemplateSection(
            name="scope",
            title="Spec Scope",
            content_template="""## Spec Scope

{{#spec_scope}}
{{@index}}. **{{name}}** - {{description}}
{{/spec_scope}}""",
            section_type=SectionType.REQUIRED,
            order=50,
            description="Detailed specification scope and boundaries"
        )
        
        # Out of Scope section
        self.sections["out_of_scope"] = TemplateSection(
            name="out_of_scope",
            title="Out of Scope",
            content_template="""## Out of Scope

{{#out_of_scope}}
- {{.}}
{{/out_of_scope}}""",
            section_type=SectionType.OPTIONAL,
            render_condition=RenderCondition.IF_EXISTS,
            condition_field="out_of_scope",
            order=60,
            description="Explicitly excluded functionality and features"
        )
        
        # Module Dependencies section
        self.sections["module_dependencies"] = TemplateSection(
            name="module_dependencies",
            title="Module Dependencies",
            content_template="""## Module Dependencies

### Required Modules
{{#required_modules}}
- **{{name}}:** {{description}}
{{/required_modules}}

### Optional Integrations
{{#optional_integrations}}
- **{{name}}:** {{description}}
{{/optional_integrations}}

### External Dependencies
{{#external_dependencies}}
- **{{name}}:** {{description}}
{{/external_dependencies}}

{{#has_data_flow}}
### Data Flow
```mermaid
{{data_flow_diagram}}
```
{{/has_data_flow}}""",
            section_type=SectionType.CONDITIONAL,
            render_condition=RenderCondition.IF_TRUE,
            condition_field="has_module_dependencies",
            order=70,
            description="Module and dependency specifications"
        )
        
        # Expected Deliverable section
        self.sections["deliverables"] = TemplateSection(
            name="deliverables",
            title="Expected Deliverable",
            content_template="""## Expected Deliverable

{{#expected_deliverables}}
{{@index}}. **{{name}}** - {{description}}
{{/expected_deliverables}}""",
            section_type=SectionType.REQUIRED,
            order=80,
            description="Concrete deliverables and success criteria"
        )
        
        # Navigation section
        self.sections["navigation"] = TemplateSection(
            name="navigation",
            title="Navigation",
            content_template="""---

**Navigation:**
{{#navigation}}
- [← Previous: {{previous.name}}]({{previous.path}})
- [Next: {{next.name}} →]({{next.path}})
{{/navigation}}

**Cross-Repository References:**
{{#cross_repo_references}}
- [{{name}}]({{reference}})
{{/cross_repo_references}}""",
            section_type=SectionType.OPTIONAL,
            render_condition=RenderCondition.IF_EXISTS,
            condition_field="navigation",
            order=90,
            description="Navigation links and cross-references"
        )
    
    def _initialize_default_variants(self):
        """Initialize default template variants."""
        # Minimal variant
        self.variants["minimal"] = TemplateVariant(
            name="minimal",
            display_name="Minimal Spec",
            description="Basic specification with essential sections only",
            sections=["header", "overview", "scope", "deliverables"],
            complexity_level="minimal",
            target_audience=["developers", "technical_leads"],
            use_cases=["simple_features", "bug_fixes", "minor_enhancements"]
        )
        
        # Standard variant
        self.variants["standard"] = TemplateVariant(
            name="standard",
            display_name="Standard Spec",
            description="Comprehensive specification with all standard sections",
            sections=["header", "overview", "user_stories", "scope", "out_of_scope", "deliverables"],
            complexity_level="medium",
            target_audience=["developers", "product_managers", "qa_engineers"],
            use_cases=["new_features", "api_changes", "integrations"]
        )
        
        # Enhanced variant (default)
        self.variants["enhanced"] = TemplateVariant(
            name="enhanced",
            display_name="Enhanced Spec",
            description="Advanced specification with prompt summaries, executive summaries, and visual diagrams",
            sections=[
                "header", "prompt_summary", "executive_summary", "system_overview",
                "user_stories", "scope", "out_of_scope", "module_dependencies",
                "deliverables", "navigation"
            ],
            complexity_level="comprehensive",
            target_audience=["all_stakeholders", "executives", "cross_functional_teams"],
            use_cases=["major_features", "architecture_changes", "cross_team_initiatives"]
        )
        
        # API-focused variant
        self.variants["api_focused"] = TemplateVariant(
            name="api_focused", 
            display_name="API-Focused Spec",
            description="Specification optimized for API development and integration",
            inherits_from="standard",
            sections=["header", "overview", "user_stories", "scope", "deliverables"],
            default_variables={
                "has_api_changes": True,
                "requires_api_spec": True,
                "has_database_changes": False
            },
            target_audience=["api_developers", "integration_teams"],
            use_cases=["api_development", "service_integration", "microservices"]
        )
        
        # Research variant
        self.variants["research"] = TemplateVariant(
            name="research",
            display_name="Research Spec",
            description="Specification for research and analysis tasks",
            sections=["header", "overview", "scope", "deliverables"],
            default_variables={
                "is_research_task": True,
                "requires_documentation": True,
                "has_implementation": False
            },
            target_audience=["researchers", "architects", "technical_leads"],
            use_cases=["research_tasks", "technical_analysis", "feasibility_studies"]
        )
    
    def _initialize_default_conditions(self):
        """Initialize default condition functions."""
        self.condition_functions["has_api_requirements"] = lambda ctx: any(
            "api" in str(item).lower() for item in ctx.get("spec_scope", [])
        )
        
        self.condition_functions["has_database_requirements"] = lambda ctx: any(
            any(keyword in str(item).lower() for keyword in ["database", "table", "schema", "sql"])
            for item in ctx.get("spec_scope", [])
        )
        
        self.condition_functions["is_complex_feature"] = lambda ctx: (
            len(ctx.get("spec_scope", [])) > 5 or
            ctx.get("complexity_level") in ["high", "complex"]
        )
        
        self.condition_functions["requires_stakeholder_review"] = lambda ctx: (
            ctx.get("impact_level") in ["high", "organization"] or
            "executive" in str(ctx.get("target_audience", [])).lower()
        )
    
    def register_section(self, section: TemplateSection):
        """Register a new template section."""
        self.sections[section.name] = section
    
    def register_variant(self, variant: TemplateVariant):
        """Register a new template variant."""
        self.variants[variant.name] = variant
    
    def register_condition_function(self, name: str, func: Callable):
        """Register a custom condition function."""
        self.condition_functions[name] = func
    
    def get_section(self, name: str) -> Optional[TemplateSection]:
        """Get a template section by name."""
        return self.sections.get(name)
    
    def get_variant(self, name: str) -> Optional[TemplateVariant]:
        """Get a template variant by name."""
        return self.variants.get(name)
    
    def list_sections(self) -> List[str]:
        """List all available section names."""
        return list(self.sections.keys())
    
    def list_variants(self) -> List[str]:
        """List all available variant names."""
        return list(self.variants.keys())


class TemplateCustomizer:
    """Main class for template customization and rendering."""
    
    def __init__(self, registry: Optional[TemplateRegistry] = None):
        self.registry = registry or TemplateRegistry()
        self.user_preferences = UserPreferences()
        self.organization_standards = OrganizationStandards()
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the template customizer."""
        logger = logging.getLogger("template_customizer")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def load_user_preferences(self, preferences_file: str):
        """Load user preferences from file."""
        try:
            with open(preferences_file, 'r', encoding='utf-8') as f:
                if preferences_file.endswith('.json'):
                    prefs_data = json.load(f)
                else:
                    prefs_data = yaml.safe_load(f)
            
            self.user_preferences = UserPreferences(**prefs_data)
            self.logger.info(f"Loaded user preferences from {preferences_file}")
        
        except Exception as e:
            self.logger.error(f"Failed to load user preferences: {str(e)}")
    
    def load_organization_standards(self, standards_file: str):
        """Load organization standards from file."""
        try:
            with open(standards_file, 'r', encoding='utf-8') as f:
                if standards_file.endswith('.json'):
                    standards_data = json.load(f)
                else:
                    standards_data = yaml.safe_load(f)
            
            self.organization_standards = OrganizationStandards(**standards_data)
            self.logger.info(f"Loaded organization standards from {standards_file}")
        
        except Exception as e:
            self.logger.error(f"Failed to load organization standards: {str(e)}")
    
    def customize_template(self, 
                          variant_name: str,
                          context: Dict[str, Any],
                          custom_sections: Optional[List[str]] = None,
                          excluded_sections: Optional[List[str]] = None) -> Dict[str, Any]:
        """Customize template based on variant, context, and user preferences."""
        
        # Get base variant
        variant = self.registry.get_variant(variant_name)
        if not variant:
            raise ValueError(f"Unknown template variant: {variant_name}")
        
        # Apply inheritance if needed
        if variant.inherits_from:
            parent_variant = self.registry.get_variant(variant.inherits_from)
            if parent_variant:
                variant = self._apply_inheritance(variant, parent_variant)
        
        # Determine final section list
        final_sections = self._determine_final_sections(
            variant, custom_sections, excluded_sections, context
        )
        
        # Filter sections based on render conditions
        rendered_sections = self._filter_sections_by_conditions(final_sections, context)
        
        # Apply organization standards
        rendered_sections = self._apply_organization_standards(rendered_sections, context)
        
        # Generate customized template
        customized_template = {
            "variant": variant_name,
            "sections": rendered_sections,
            "context": context,
            "metadata": {
                "total_sections": len(rendered_sections),
                "required_sections": len([s for s in rendered_sections if self.registry.get_section(s).section_type == SectionType.REQUIRED]),
                "conditional_sections": len([s for s in rendered_sections if self.registry.get_section(s).section_type == SectionType.CONDITIONAL]),
                "customization_applied": True
            }
        }
        
        return customized_template
    
    def render_template(self, customized_template: Dict[str, Any]) -> str:
        """Render the customized template to final markdown content."""
        rendered_content = []
        context = customized_template["context"]
        
        # Sort sections by order
        sections = customized_template["sections"]
        sorted_sections = sorted(sections, key=lambda s: self.registry.get_section(s).order)
        
        # Render each section
        for section_name in sorted_sections:
            section = self.registry.get_section(section_name)
            if section:
                try:
                    rendered_section = self._render_section(section, context)
                    if rendered_section.strip():  # Only add non-empty sections
                        rendered_content.append(rendered_section)
                except Exception as e:
                    self.logger.error(f"Failed to render section {section_name}: {str(e)}")
                    # Add placeholder for failed sections
                    rendered_content.append(f"## {section.title}\n\n[Error rendering section: {str(e)}]\n")
        
        return "\n\n".join(rendered_content)
    
    def validate_template(self, customized_template: Dict[str, Any]) -> Dict[str, Any]:
        """Validate customized template against quality standards."""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "suggestions": [],
            "quality_score": 0.0,
            "completeness_score": 0.0,
            "compliance_score": 0.0
        }
        
        sections = customized_template["sections"]
        context = customized_template["context"]
        
        # Check required sections
        required_sections = [
            name for name, section in self.registry.sections.items()
            if section.section_type == SectionType.REQUIRED
        ]
        
        missing_required = [s for s in required_sections if s not in sections]
        if missing_required:
            validation_results["valid"] = False
            validation_results["errors"].extend([
                f"Missing required section: {section}" for section in missing_required
            ])
        
        # Check organization standards compliance
        if self.organization_standards.required_sections:
            missing_org_required = [
                s for s in self.organization_standards.required_sections 
                if s not in sections
            ]
            if missing_org_required:
                validation_results["warnings"].extend([
                    f"Missing organization-required section: {section}"
                    for section in missing_org_required
                ])
        
        # Check forbidden sections
        if self.organization_standards.forbidden_sections:
            forbidden_present = [
                s for s in self.organization_standards.forbidden_sections
                if s in sections
            ]
            if forbidden_present:
                validation_results["errors"].extend([
                    f"Forbidden section present: {section}"
                    for section in forbidden_present
                ])
                validation_results["valid"] = False
        
        # Calculate quality scores
        total_possible_sections = len(self.registry.sections)
        present_sections = len(sections)
        validation_results["completeness_score"] = min(1.0, present_sections / max(1, total_possible_sections))
        
        error_penalty = len(validation_results["errors"]) * 0.2
        warning_penalty = len(validation_results["warnings"]) * 0.1
        validation_results["quality_score"] = max(0.0, 1.0 - error_penalty - warning_penalty)
        
        compliance_issues = len(missing_org_required) + len(forbidden_present)
        validation_results["compliance_score"] = max(0.0, 1.0 - (compliance_issues * 0.15))
        
        # Generate suggestions
        if validation_results["completeness_score"] < 0.7:
            validation_results["suggestions"].append(
                "Consider adding more sections to improve documentation completeness"
            )
        
        if validation_results["quality_score"] < 0.8:
            validation_results["suggestions"].append(
                "Address validation errors and warnings to improve template quality"
            )
        
        return validation_results
    
    def _apply_inheritance(self, child_variant: TemplateVariant, parent_variant: TemplateVariant) -> TemplateVariant:
        """Apply template inheritance from parent to child variant."""
        inherited_variant = deepcopy(parent_variant)
        
        # Override with child properties
        inherited_variant.name = child_variant.name
        inherited_variant.display_name = child_variant.display_name
        inherited_variant.description = child_variant.description
        
        # Merge sections
        if child_variant.sections:
            inherited_variant.sections = child_variant.sections
        
        # Apply exclusions
        if child_variant.excluded_sections:
            inherited_variant.sections = [
                s for s in inherited_variant.sections
                if s not in child_variant.excluded_sections
            ]
        
        # Merge default variables
        inherited_variant.default_variables.update(child_variant.default_variables)
        
        # Use child's other properties
        if child_variant.target_audience:
            inherited_variant.target_audience = child_variant.target_audience
        if child_variant.use_cases:
            inherited_variant.use_cases = child_variant.use_cases
        if child_variant.complexity_level:
            inherited_variant.complexity_level = child_variant.complexity_level
        
        return inherited_variant
    
    def _determine_final_sections(self,
                                variant: TemplateVariant,
                                custom_sections: Optional[List[str]],
                                excluded_sections: Optional[List[str]],
                                context: Dict[str, Any]) -> List[str]:
        """Determine final list of sections to include."""
        
        # Start with variant sections
        sections = list(variant.sections)
        
        # Add custom sections if specified
        if custom_sections:
            sections.extend([s for s in custom_sections if s not in sections])
        
        # Add user preference sections
        if self.user_preferences.default_sections:
            sections.extend([s for s in self.user_preferences.default_sections if s not in sections])
        
        # Remove excluded sections
        excluded = set()
        if excluded_sections:
            excluded.update(excluded_sections)
        if variant.excluded_sections:
            excluded.update(variant.excluded_sections)
        
        sections = [s for s in sections if s not in excluded]
        
        # Ensure all sections exist in registry
        sections = [s for s in sections if s in self.registry.sections]
        
        return sections
    
    def _filter_sections_by_conditions(self, sections: List[str], context: Dict[str, Any]) -> List[str]:
        """Filter sections based on their render conditions."""
        filtered_sections = []
        
        for section_name in sections:
            section = self.registry.get_section(section_name)
            if not section:
                continue
            
            should_render = self._evaluate_render_condition(section, context)
            if should_render:
                filtered_sections.append(section_name)
        
        return filtered_sections
    
    def _evaluate_render_condition(self, section: TemplateSection, context: Dict[str, Any]) -> bool:
        """Evaluate whether a section should be rendered based on its condition."""
        condition = section.render_condition
        
        if condition == RenderCondition.ALWAYS:
            return True
        elif condition == RenderCondition.NEVER:
            return False
        elif condition == RenderCondition.IF_EXISTS:
            return bool(context.get(section.condition_field))
        elif condition == RenderCondition.IF_NOT_EXISTS:
            return not bool(context.get(section.condition_field))
        elif condition == RenderCondition.IF_TRUE:
            return context.get(section.condition_field, False) is True
        elif condition == RenderCondition.IF_FALSE:
            return context.get(section.condition_field, True) is False
        elif condition == RenderCondition.CUSTOM_FUNCTION:
            if section.condition_function:
                try:
                    return section.condition_function(context)
                except Exception as e:
                    self.logger.error(f"Error evaluating custom condition for section {section.name}: {str(e)}")
                    return False
            elif section.condition_field in self.registry.condition_functions:
                try:
                    return self.registry.condition_functions[section.condition_field](context)
                except Exception as e:
                    self.logger.error(f"Error evaluating condition function {section.condition_field}: {str(e)}")
                    return False
        
        # Default to True if condition evaluation fails
        return True
    
    def _apply_organization_standards(self, sections: List[str], context: Dict[str, Any]) -> List[str]:
        """Apply organization standards to section list."""
        # Add required sections if missing
        for required_section in self.organization_standards.required_sections:
            if required_section not in sections and required_section in self.registry.sections:
                sections.append(required_section)
        
        # Remove forbidden sections
        sections = [s for s in sections if s not in self.organization_standards.forbidden_sections]
        
        # Apply mandatory variables to context
        context.update(self.organization_standards.mandatory_variables)
        
        return sections
    
    def _render_section(self, section: TemplateSection, context: Dict[str, Any]) -> str:
        """Render a single section with the given context."""
        # Merge section variables with context
        render_context = {**context, **section.variables}
        
        # Apply user preference overrides for this section
        if section.name in self.user_preferences.section_preferences:
            section_prefs = self.user_preferences.section_preferences[section.name]
            render_context.update(section_prefs.get("variables", {}))
        
        # Simple template substitution (in a real implementation, use a proper template engine like Jinja2)
        rendered_content = section.content_template
        
        # Handle simple variable substitution
        for key, value in render_context.items():
            placeholder = f"{{{{{key}}}}}"
            if placeholder in rendered_content:
                rendered_content = rendered_content.replace(placeholder, str(value))
        
        # Handle nested variable substitution (simplified)
        if "." in rendered_content:
            for key, value in render_context.items():
                if isinstance(value, dict):
                    for subkey, subvalue in value.items():
                        placeholder = f"{{{{{key}.{subkey}}}}}"
                        if placeholder in rendered_content:
                            rendered_content = rendered_content.replace(placeholder, str(subvalue))
        
        return rendered_content


class TemplateManager:
    """High-level manager for template customization system."""
    
    def __init__(self, config_dir: str = ""):
        self.config_dir = Path(config_dir) if config_dir else Path.cwd() / "config"
        self.registry = TemplateRegistry()
        self.customizer = TemplateCustomizer(self.registry)
        self.logger = self._setup_logging()
        
        # Load configurations if they exist
        self._load_configurations()
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the template manager."""
        logger = logging.getLogger("template_manager")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _load_configurations(self):
        """Load user preferences and organization standards if they exist."""
        # Load user preferences
        user_prefs_file = self.config_dir / "user_preferences.yaml"
        if user_prefs_file.exists():
            self.customizer.load_user_preferences(str(user_prefs_file))
        
        # Load organization standards
        org_standards_file = self.config_dir / "organization_standards.yaml"
        if org_standards_file.exists():
            self.customizer.load_organization_standards(str(org_standards_file))
    
    def create_template(self,
                       variant_name: str,
                       context: Dict[str, Any],
                       output_file: Optional[str] = None) -> str:
        """Create a complete template with customization and validation."""
        
        self.logger.info(f"Creating template with variant: {variant_name}")
        
        # Customize template
        customized_template = self.customizer.customize_template(variant_name, context)
        
        # Validate template
        validation_results = self.customizer.validate_template(customized_template)
        
        if not validation_results["valid"]:
            self.logger.warning(f"Template validation failed: {validation_results['errors']}")
        
        # Render template
        rendered_content = self.customizer.render_template(customized_template)
        
        # Save to file if requested
        if output_file:
            with open(output_file, 'w', encoding='utf-8') as f:
                f.write(rendered_content)
            self.logger.info(f"Template saved to: {output_file}")
        
        return rendered_content
    
    def list_available_variants(self) -> Dict[str, Dict[str, Any]]:
        """List all available template variants with their details."""
        variants_info = {}
        
        for name, variant in self.registry.variants.items():
            variants_info[name] = {
                "display_name": variant.display_name,
                "description": variant.description,
                "complexity_level": variant.complexity_level,
                "target_audience": variant.target_audience,
                "use_cases": variant.use_cases,
                "sections_count": len(variant.sections),
                "inherits_from": variant.inherits_from
            }
        
        return variants_info
    
    def export_configuration(self, export_dir: str):
        """Export current configuration to files."""
        export_path = Path(export_dir)
        export_path.mkdir(exist_ok=True)
        
        # Export user preferences
        user_prefs_file = export_path / "user_preferences.yaml"
        with open(user_prefs_file, 'w', encoding='utf-8') as f:
            yaml.dump(asdict(self.customizer.user_preferences), f, default_flow_style=False)
        
        # Export organization standards
        org_standards_file = export_path / "organization_standards.yaml"
        with open(org_standards_file, 'w', encoding='utf-8') as f:
            yaml.dump(asdict(self.customizer.organization_standards), f, default_flow_style=False)
        
        # Export available variants
        variants_file = export_path / "available_variants.yaml"
        variants_data = {name: asdict(variant) for name, variant in self.registry.variants.items()}
        with open(variants_file, 'w', encoding='utf-8') as f:
            yaml.dump(variants_data, f, default_flow_style=False)
        
        self.logger.info(f"Configuration exported to: {export_dir}")


# Example usage and configuration
if __name__ == "__main__":
    # Initialize template manager
    manager = TemplateManager()
    
    # Example context for template generation
    context = {
        "module_name": "agent-os",
        "spec_name": "template-customization-example",
        "sub_agent_type": "workflow-automation",
        "creation_date": "2025-08-05",
        "status": "Planning",
        "ai_context_description": "Example of template customization system usage",
        "overview_description": "This is an example of how the template customization system works",
        "spec_scope": [
            {"name": "Template Customization", "description": "Implement flexible template system"},
            {"name": "User Preferences", "description": "Support user-specific customization"}
        ],
        "expected_deliverables": [
            {"name": "Customization System", "description": "Complete template customization implementation"},
            {"name": "Documentation", "description": "Comprehensive usage documentation"}
        ],
        "has_module_dependencies": False
    }
    
    # Create template with enhanced variant
    template_content = manager.create_template("enhanced", context)
    
    # List available variants
    variants = manager.list_available_variants()
    print("Available Template Variants:")
    for name, info in variants.items():
        print(f"  - {name}: {info['display_name']} ({info['complexity_level']})")
    
    # Export configuration
    manager.export_configuration("./template_config_export")
    
    print(f"\nGenerated template ({len(template_content)} characters)")
    print("First 500 characters:")
    print(template_content[:500] + "..." if len(template_content) > 500 else template_content)