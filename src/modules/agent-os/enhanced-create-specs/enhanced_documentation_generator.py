#!/usr/bin/env python3
"""
Enhanced Documentation Generator for Agent OS Enhanced Create-Specs Workflow.

This module provides comprehensive template generation with:
- Enhanced spec.md templates with prompt summaries, executive summaries, and mermaid diagrams
- Conditional sub-spec generation (API, database, tests)
- Cross-reference system integration
- Template customization and validation
- Module-based organization support

Author: Enhanced Create-Specs Workflow
Created: 2025-08-05
Module: agent-os/enhanced-create-specs
"""

import os
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Any, Union
import re
from dataclasses import dataclass, field
from enum import Enum


class TemplateType(Enum):
    """Enumeration of available template types."""
    STANDARD = "standard"
    ENHANCED = "enhanced"
    MINIMAL = "minimal"
    CUSTOM = "custom"


class DiagramType(Enum):
    """Enumeration of mermaid diagram types."""
    SYSTEM_OVERVIEW = "system_overview"
    WORKFLOW = "workflow"
    ARCHITECTURE = "architecture"
    DATA_FLOW = "data_flow"
    SEQUENCE = "sequence"


@dataclass
class PromptSummary:
    """Data class for prompt summary information."""
    original_request: str
    context_provided: str
    clarifications_made: List[str] = field(default_factory=list)
    reuse_notes: str = ""
    prompt_evolution: str = ""


@dataclass
class ExecutiveSummary:
    """Data class for executive summary information."""
    purpose: str
    impact: Dict[str, str] = field(default_factory=dict)
    scope: Dict[str, Union[str, List[str]]] = field(default_factory=dict)
    key_outcomes: List[str] = field(default_factory=list)


@dataclass
class UserStory:
    """Data class for user story information."""
    title: str
    user_type: str
    want: str
    benefit: str
    acceptance_criteria: List[str] = field(default_factory=list)
    workflow: List[str] = field(default_factory=list)


@dataclass
class ModuleDependency:
    """Data class for module dependency information."""
    name: str
    description: str
    type: str = "required"  # required, optional, external


@dataclass
class SpecConfiguration:
    """Configuration class for spec generation."""
    module_name: str
    spec_name: str
    sub_agent_type: str = "workflow-automation"
    template_type: TemplateType = TemplateType.ENHANCED
    creation_date: str = ""
    status: str = "Planning"
    ai_context_description: str = ""
    
    # Content sections
    prompt_summary: Optional[PromptSummary] = None
    executive_summary: Optional[ExecutiveSummary] = None
    user_stories: List[UserStory] = field(default_factory=list)
    spec_scope: List[Dict[str, str]] = field(default_factory=list)
    out_of_scope: List[str] = field(default_factory=list)
    expected_deliverables: List[Dict[str, str]] = field(default_factory=list)
    
    # Dependencies and integration
    required_modules: List[ModuleDependency] = field(default_factory=list)
    optional_integrations: List[ModuleDependency] = field(default_factory=list)
    external_dependencies: List[ModuleDependency] = field(default_factory=list)
    integration_points: List[Dict[str, str]] = field(default_factory=list)
    
    # Diagrams and visualization
    mermaid_diagram: str = ""
    data_flow_diagram: str = ""
    flow_description: str = ""
    
    # Navigation and references
    navigation: Dict[str, Dict[str, str]] = field(default_factory=dict)
    cross_repo_references: List[Dict[str, str]] = field(default_factory=list)
    
    # Conditional sections
    has_module_dependencies: bool = True
    has_data_flow: bool = False
    has_sub_specs: bool = True
    
    def __post_init__(self):
        """Post-initialization processing."""
        if not self.creation_date:
            self.creation_date = datetime.now().strftime("%Y-%m-%d")


class MermaidDiagramGenerator:
    """Generator for mermaid diagrams based on spec requirements."""
    
    def __init__(self):
        self.diagram_templates = {
            DiagramType.SYSTEM_OVERVIEW: self._generate_system_overview,
            DiagramType.WORKFLOW: self._generate_workflow_diagram,
            DiagramType.ARCHITECTURE: self._generate_architecture_diagram,
            DiagramType.DATA_FLOW: self._generate_data_flow_diagram,
            DiagramType.SEQUENCE: self._generate_sequence_diagram
        }
    
    def generate_diagram(self, diagram_type: DiagramType, config: SpecConfiguration) -> str:
        """Generate mermaid diagram based on type and configuration."""
        if diagram_type in self.diagram_templates:
            return self.diagram_templates[diagram_type](config)
        else:
            return self._generate_default_diagram(config)
    
    def _generate_system_overview(self, config: SpecConfiguration) -> str:
        """Generate system overview diagram."""
        return f"""graph TD
    A[User Request] --> B[{config.spec_name} Workflow]
    B --> C{{Module Identification}}
    C --> D[{config.module_name} Module]
    D --> E[Implementation]
    
    subgraph "Enhanced Features"
        E --> F[Prompt Summary]
        E --> G[Executive Summary]
        E --> H[Mermaid Diagrams]
        E --> I[Task Summary]
    end
    
    subgraph "Integration Points"
        J[{config.module_name} Hub] --> K[Component A]
        J --> L[Component B]
        J --> M[Component N]
    end
    
    B --> J
    E --> J"""
    
    def _generate_workflow_diagram(self, config: SpecConfiguration) -> str:
        """Generate workflow diagram."""
        return f"""flowchart LR
    Start([Start: {config.spec_name}]) --> Analysis[Analyze Requirements]
    Analysis --> Design[Design Solution]
    Design --> Implementation[Implement Features]
    Implementation --> Testing[Run Tests]
    Testing --> Deployment[Deploy Changes]
    Deployment --> End([Complete])
    
    Testing -->|Issues Found| Design"""
    
    def _generate_architecture_diagram(self, config: SpecConfiguration) -> str:
        """Generate architecture diagram."""
        return f"""graph TB
    subgraph "Presentation Layer"
        UI[User Interface]
        API[REST API]
    end
    
    subgraph "Business Logic Layer"
        Service[{config.spec_name} Service]
        Workflow[Workflow Engine]
    end
    
    subgraph "Data Layer"
        DB[(Database)]
        Cache[(Cache)]
    end
    
    UI --> API
    API --> Service
    Service --> Workflow
    Workflow --> DB
    Service --> Cache"""
    
    def _generate_data_flow_diagram(self, config: SpecConfiguration) -> str:
        """Generate data flow diagram."""
        return f"""graph LR
    Input[Input Data] --> Processor[{config.spec_name} Processor]
    Processor --> Validator[Data Validator]
    Validator --> Transformer[Data Transformer]
    Transformer --> Storage[Data Storage]
    Storage --> Output[Output Data]
    
    Processor --> Logger[Audit Logger]
    Validator --> Logger
    Transformer --> Logger"""
    
    def _generate_sequence_diagram(self, config: SpecConfiguration) -> str:
        """Generate sequence diagram."""
        return f"""sequenceDiagram
    participant User
    participant System
    participant {config.module_name}
    participant Database
    
    User->>System: Initiate {config.spec_name}
    System->>{config.module_name}: Process Request
    {config.module_name}->>Database: Store Data
    Database-->>{config.module_name}: Confirm Storage
    {config.module_name}-->>System: Return Result
    System-->>User: Display Response"""
    
    def _generate_default_diagram(self, config: SpecConfiguration) -> str:
        """Generate default diagram when type is not specified."""
        return self._generate_system_overview(config)


class SubSpecGenerator:
    """Generator for conditional sub-specification documents."""
    
    def __init__(self):
        self.sub_spec_templates = {
            "technical-spec": self._generate_technical_spec,
            "api-spec": self._generate_api_spec,
            "database-schema": self._generate_database_spec,
            "tests": self._generate_tests_spec
        }
    
    def should_generate_sub_spec(self, spec_type: str, config: SpecConfiguration) -> bool:
        """Determine if a sub-spec should be generated based on requirements."""
        conditions = {
            "technical-spec": True,  # Always generate technical spec
            "api-spec": self._has_api_requirements(config),
            "database-schema": self._has_database_requirements(config),
            "tests": True  # Always generate tests spec
        }
        return conditions.get(spec_type, False)
    
    def generate_sub_spec(self, spec_type: str, config: SpecConfiguration) -> str:
        """Generate sub-specification content."""
        if spec_type in self.sub_spec_templates:
            return self.sub_spec_templates[spec_type](config)
        else:
            return self._generate_default_sub_spec(spec_type, config)
    
    def _has_api_requirements(self, config: SpecConfiguration) -> bool:
        """Check if spec has API requirements."""
        # Look for API-related keywords in scope and deliverables
        api_keywords = ["api", "endpoint", "rest", "graphql", "service", "controller"]
        
        text_to_check = []
        text_to_check.extend([item.get("description", "") for item in config.spec_scope])
        text_to_check.extend([item.get("description", "") for item in config.expected_deliverables])
        
        combined_text = " ".join(text_to_check).lower()
        return any(keyword in combined_text for keyword in api_keywords)
    
    def _has_database_requirements(self, config: SpecConfiguration) -> bool:
        """Check if spec has database requirements."""
        # Look for database-related keywords
        db_keywords = ["database", "table", "schema", "migration", "sql", "model", "entity"]
        
        text_to_check = []
        text_to_check.extend([item.get("description", "") for item in config.spec_scope])
        text_to_check.extend([item.get("description", "") for item in config.expected_deliverables])
        
        combined_text = " ".join(text_to_check).lower()
        return any(keyword in combined_text for keyword in db_keywords)
    
    def _generate_technical_spec(self, config: SpecConfiguration) -> str:
        """Generate technical specification content."""
        return f"""# Technical Specification

This is the technical specification for the spec detailed in @specs/modules/{config.module_name}/{config.spec_name}/spec.md

> Created: {config.creation_date}
> Version: 1.0.0

## Technical Requirements

- **Architecture Pattern**: {self._infer_architecture_pattern(config)}
- **Technology Stack**: {self._infer_technology_stack(config)}
- **Performance Requirements**: {self._infer_performance_requirements(config)}
- **Security Considerations**: Standard security practices for {config.module_name} module

## Implementation Approach

### Option A: {self._get_primary_approach(config)}
- Pros: Scalable, maintainable, follows established patterns
- Cons: Higher complexity, longer initial development time

### Option B: Simplified Implementation
- Pros: Faster development, lower complexity
- Cons: Limited scalability, potential technical debt

**Rationale:** Option A selected for long-term maintainability and alignment with module architecture.

## External Dependencies

{self._generate_dependency_list(config)}

## Quality Standards

- **Code Coverage**: Minimum 80% test coverage
- **Documentation**: Comprehensive inline documentation
- **Performance**: Response times under 200ms for typical operations
- **Security**: Input validation and sanitization for all user inputs"""
    
    def _generate_api_spec(self, config: SpecConfiguration) -> str:
        """Generate API specification content."""
        return f"""# API Specification

This is the API specification for the spec detailed in @specs/modules/{config.module_name}/{config.spec_name}/spec.md

> Created: {config.creation_date}
> Version: 1.0.0

## API Endpoints

### Core Endpoints

#### POST /{config.module_name}/{config.spec_name}
**Purpose:** Create new {config.spec_name} resource
**Parameters:** 
- `name` (string, required): Resource name
- `configuration` (object, optional): Resource configuration

**Response:**
```json
{{
  "id": "string",
  "name": "string", 
  "status": "created",
  "created_at": "2025-08-05T10:00:00Z"
}}
```

#### GET /{config.module_name}/{config.spec_name}/{{id}}
**Purpose:** Retrieve {config.spec_name} resource
**Parameters:**
- `id` (string, required): Resource identifier

**Response:**
```json
{{
  "id": "string",
  "name": "string",
  "configuration": {{}},
  "status": "active"
}}
```

## Error Handling

- **400 Bad Request**: Invalid input parameters
- **404 Not Found**: Resource not found
- **500 Internal Server Error**: Server processing error

## Rate Limiting

- Standard rate limiting: 100 requests per minute per client
- Burst limit: 10 requests per second"""
    
    def _generate_database_spec(self, config: SpecConfiguration) -> str:
        """Generate database specification content."""
        return f"""# Database Schema

This is the database schema implementation for the spec detailed in @specs/modules/{config.module_name}/{config.spec_name}/spec.md

> Created: {config.creation_date}
> Version: 1.0.0

## Schema Changes

### New Tables

#### {config.spec_name.replace('-', '_')}
```sql
CREATE TABLE {config.spec_name.replace('-', '_')} (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    name VARCHAR(255) NOT NULL,
    configuration JSONB,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

CREATE INDEX idx_{config.spec_name.replace('-', '_')}_name ON {config.spec_name.replace('-', '_')} (name);
CREATE INDEX idx_{config.spec_name.replace('-', '_')}_status ON {config.spec_name.replace('-', '_')} (status);
```

### Indexes

- Primary key index on `id` column
- Performance index on `name` for lookups
- Status index for filtering queries

### Constraints

- `name` field must be unique within active records
- `status` field restricted to predefined values
- `configuration` field must be valid JSON

## Migration Strategy

1. Create new table with proper indexes
2. Add foreign key constraints if applicable
3. Populate initial data if required
4. Update application code to use new schema
5. Monitor performance and optimize as needed"""
    
    def _generate_tests_spec(self, config: SpecConfiguration) -> str:
        """Generate tests specification content."""
        return f"""# Tests Specification

This is the tests coverage details for the spec detailed in @specs/modules/{config.module_name}/{config.spec_name}/spec.md

> Created: {config.creation_date}
> Version: 1.0.0

## Test Coverage

### Unit Tests

**{config.spec_name.title().replace('-', '')}Service**
- Test service initialization and configuration
- Test core business logic methods
- Test error handling and edge cases
- Test input validation and sanitization

**{config.spec_name.title().replace('-', '')}Model**
- Test model creation and validation
- Test model serialization and deserialization
- Test model relationships and constraints

### Integration Tests

**API Integration**
- Test all API endpoints with valid inputs
- Test API error responses and status codes
- Test API authentication and authorization
- Test API rate limiting behavior

**Database Integration**
- Test database connection and queries
- Test transaction handling and rollback
- Test data integrity and constraints
- Test performance with large datasets

### End-to-End Tests

**Complete Workflow**
- Test full user workflow from start to finish
- Test integration between all system components
- Test cross-module interactions and dependencies

### Performance Tests

**Load Testing**
- Test system performance under normal load
- Test system behavior under peak load
- Test resource utilization and memory usage

### Security Tests

**Input Validation**
- Test SQL injection prevention
- Test XSS prevention
- Test input sanitization effectiveness

## Mocking Requirements

- **External APIs**: Mock third-party service calls
- **File System**: Mock file operations for testing
- **Database**: Use in-memory database for unit tests
- **Time-based Operations**: Mock datetime for consistent test results

## Test Data Management

- Use factory pattern for test data creation
- Implement test data cleanup between tests
- Maintain separate test database for integration tests
- Use realistic but anonymized data for performance tests"""
    
    def _generate_default_sub_spec(self, spec_type: str, config: SpecConfiguration) -> str:
        """Generate default sub-spec content."""
        return f"""# {spec_type.title().replace('-', ' ')}

This is the {spec_type} for the spec detailed in @specs/modules/{config.module_name}/{config.spec_name}/spec.md

> Created: {config.creation_date}
> Version: 1.0.0

## Overview

[Content to be implemented based on specific requirements for {spec_type}]

## Implementation Details

[Detailed implementation information for {spec_type}]

## Quality Assurance

[Quality standards and validation criteria for {spec_type}]"""
    
    def _infer_architecture_pattern(self, config: SpecConfiguration) -> str:
        """Infer architecture pattern from configuration."""
        if any("api" in item.get("description", "").lower() for item in config.spec_scope):
            return "Layered Architecture (Presentation, Business, Data)"
        elif any("workflow" in item.get("description", "").lower() for item in config.spec_scope):
            return "Pipeline Architecture"
        else:
            return "Modular Architecture"
    
    def _infer_technology_stack(self, config: SpecConfiguration) -> str:
        """Infer technology stack from configuration."""
        return f"Python 3.8+, {config.module_name} module framework"
    
    def _infer_performance_requirements(self, config: SpecConfiguration) -> str:
        """Infer performance requirements from configuration."""
        return "Standard performance requirements for business applications"
    
    def _get_primary_approach(self, config: SpecConfiguration) -> str:
        """Get primary implementation approach."""
        return f"Modular Implementation with {config.module_name} Integration"
    
    def _generate_dependency_list(self, config: SpecConfiguration) -> str:
        """Generate dependency list."""
        deps = []
        for dep in config.external_dependencies:
            deps.append(f"- **{dep.name}:** {dep.description}")
        
        if not deps:
            deps.append("- No external dependencies identified")
        
        return "\n".join(deps)


class CrossReferenceSystem:
    """System for managing and validating cross-references."""
    
    def __init__(self):
        self.reference_patterns = {
            "internal": r"@(specs|src|docs|tests)/.*",
            "cross_repo": r"@\w+:.*",
            "external": r"https?://.*"
        }
    
    def validate_reference(self, reference: str) -> Dict[str, Any]:
        """Validate a reference and return validation results."""
        result = {
            "reference": reference,
            "type": self._get_reference_type(reference),
            "valid": False,
            "exists": False,
            "error": None
        }
        
        try:
            if result["type"] == "internal":
                result["valid"] = True
                result["exists"] = self._check_internal_reference(reference)
            elif result["type"] == "cross_repo":
                result["valid"] = True
                result["exists"] = self._check_cross_repo_reference(reference)
            elif result["type"] == "external":
                result["valid"] = True
                result["exists"] = self._check_external_reference(reference)
            else:
                result["error"] = "Unknown reference type"
        
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def generate_cross_references(self, config: SpecConfiguration) -> List[Dict[str, str]]:
        """Generate cross-references for a spec."""
        references = []
        
        # Add module documentation references
        references.append({
            "name": f"{config.module_name} Module Documentation",
            "reference": f"@docs/modules/{config.module_name}/README.md"
        })
        
        # Add related specs references
        references.append({
            "name": "Agent OS Framework",
            "reference": "@docs/modules/agent-os/README.md"
        })
        
        # Add cross-repository references
        if config.cross_repo_references:
            references.extend(config.cross_repo_references)
        
        return references
    
    def _get_reference_type(self, reference: str) -> str:
        """Determine the type of reference."""
        for ref_type, pattern in self.reference_patterns.items():
            if re.match(pattern, reference):
                return ref_type
        return "unknown"
    
    def _check_internal_reference(self, reference: str) -> bool:
        """Check if internal reference exists."""
        # Remove @ prefix and check if path exists
        path = reference[1:] if reference.startswith("@") else reference
        return os.path.exists(path)
    
    def _check_cross_repo_reference(self, reference: str) -> bool:
        """Check if cross-repository reference is valid."""
        # For now, assume cross-repo references are valid
        # In a real implementation, this would check repository accessibility
        return True
    
    def _check_external_reference(self, reference: str) -> bool:
        """Check if external reference is accessible."""
        # For now, assume external references are valid
        # In a real implementation, this would make HTTP requests to check
        return True


class SpecTemplate:
    """Main template class for spec document generation."""
    
    def __init__(self, template_type: TemplateType = TemplateType.ENHANCED):
        self.template_type = template_type
        self.template_path = self._get_template_path()
        self.mermaid_generator = MermaidDiagramGenerator()
        self.sub_spec_generator = SubSpecGenerator()
        self.cross_reference_system = CrossReferenceSystem()
    
    def _get_template_path(self) -> str:
        """Get the path to the template file."""
        template_files = {
            TemplateType.STANDARD: "standard-spec-template.md",
            TemplateType.ENHANCED: "enhanced-spec-template.md",
            TemplateType.MINIMAL: "minimal-spec-template.md",
            TemplateType.CUSTOM: "custom-spec-template.md"
        }
        
        base_dir = Path(__file__).parent / "templates"
        return str(base_dir / template_files[self.template_type])
    
    def render_template(self, config: SpecConfiguration) -> str:
        """Render the spec template with configuration data."""
        try:
            with open(self.template_path, 'r', encoding='utf-8') as f:
                template_content = f.read()
        except FileNotFoundError:
            template_content = self._get_fallback_template()
        
        # Generate mermaid diagram if not provided
        if not config.mermaid_diagram:
            config.mermaid_diagram = self.mermaid_generator.generate_diagram(
                DiagramType.SYSTEM_OVERVIEW, config
            )
        
        # Generate cross-references
        if not config.cross_repo_references:
            config.cross_repo_references = self.cross_reference_system.generate_cross_references(config)
        
        # Simple template substitution (in a real implementation, use a proper template engine)
        rendered_content = self._substitute_template_variables(template_content, config)
        
        return rendered_content
    
    def generate_sub_specs(self, config: SpecConfiguration) -> Dict[str, str]:
        """Generate all applicable sub-specifications."""
        sub_specs = {}
        
        sub_spec_types = ["technical-spec", "api-spec", "database-schema", "tests"]
        
        for spec_type in sub_spec_types:
            if self.sub_spec_generator.should_generate_sub_spec(spec_type, config):
                sub_specs[f"sub-specs/{spec_type}.md"] = self.sub_spec_generator.generate_sub_spec(
                    spec_type, config
                )
        
        return sub_specs
    
    def _substitute_template_variables(self, template: str, config: SpecConfiguration) -> str:
        """Substitute template variables with actual values."""
        # Simple substitution - in a real implementation, use a proper template engine like Jinja2
        substitutions = {
            "{{module_name}}": config.module_name,
            "{{spec_name}}": config.spec_name,
            "{{sub_agent_type}}": config.sub_agent_type,
            "{{creation_date}}": config.creation_date,
            "{{status}}": config.status,
            "{{ai_context_description}}": config.ai_context_description,
            "{{mermaid_diagram}}": config.mermaid_diagram,
            "{{flow_description}}": config.flow_description
        }
        
        # Handle prompt summary
        if config.prompt_summary:
            substitutions.update({
                "{{original_request}}": config.prompt_summary.original_request,
                "{{context_provided}}": config.prompt_summary.context_provided,
                "{{reuse_notes}}": config.prompt_summary.reuse_notes,
                "{{prompt_evolution}}": config.prompt_summary.prompt_evolution
            })
        
        # Handle executive summary
        if config.executive_summary:
            substitutions.update({
                "{{executive_summary.purpose}}": config.executive_summary.purpose,
            })
            
            # Handle impact and scope (simplified for this example)
            if config.executive_summary.impact:
                for key, value in config.executive_summary.impact.items():
                    substitutions[f"{{{{executive_summary.impact.{key}}}}}"] = value
        
        # Apply substitutions
        result = template
        for placeholder, value in substitutions.items():
            result = result.replace(placeholder, str(value))
        
        return result
    
    def _get_fallback_template(self) -> str:
        """Get fallback template if file is not found."""
        return """# Spec Requirements Document

> **Module:** {{module_name}}
> **Spec:** {{spec_name}}
> **Created:** {{creation_date}}
> **Status:** {{status}}

## Overview

{{ai_context_description}}

## System Overview

```mermaid
{{mermaid_diagram}}
```

## Spec Scope

[Spec scope to be defined]

## Expected Deliverable

[Expected deliverables to be defined]"""


class EnhancedDocumentationGenerator:
    """Main class for enhanced documentation generation."""
    
    def __init__(self, config: Optional[Dict[str, Any]] = None):
        self.config = config or {}
        self.template_system = SpecTemplate(TemplateType.ENHANCED)
        self.quality_validator = DocumentationQualityValidator()
    
    def generate_complete_specification(self, spec_config: SpecConfiguration) -> Dict[str, str]:
        """Generate complete specification with all documents."""
        documents = {}
        
        # Generate main spec document
        documents["spec.md"] = self.template_system.render_template(spec_config)
        
        # Generate sub-specifications
        sub_specs = self.template_system.generate_sub_specs(spec_config)
        documents.update(sub_specs)
        
        # Generate tasks.md placeholder
        documents["tasks.md"] = self._generate_tasks_template(spec_config)
        
        return documents
    
    def validate_documentation_quality(self, documents: Dict[str, str]) -> Dict[str, Any]:
        """Validate the quality of generated documentation."""
        return self.quality_validator.validate_documents(documents)
    
    def _generate_tasks_template(self, config: SpecConfiguration) -> str:
        """Generate tasks.md template."""
        return f"""# Spec Tasks

> **Module:** {config.module_name}
> **Spec:** {config.spec_name}
> **Sub-Agent:** {config.sub_agent_type}
> **AI Context:** Implementation tasks for {config.spec_name}

These are the tasks to be completed for the spec detailed in @specs/modules/{config.module_name}/{config.spec_name}/spec.md

> Created: {config.creation_date}
> Status: Ready for Implementation

## Implementation Tasks

- [ ] 1. **Core Implementation**
  - [ ] 1.1 Write tests for core functionality
  - [ ] 1.2 Implement main features according to technical specification
  - [ ] 1.3 Integrate with {config.module_name} module
  - [ ] 1.4 Verify all tests pass

- [ ] 2. **Quality Assurance**
  - [ ] 2.1 Run complete test suite
  - [ ] 2.2 Validate documentation completeness
  - [ ] 2.3 Check cross-reference validity
  - [ ] 2.4 Performance testing and optimization

- [ ] 3. **Integration and Deployment**
  - [ ] 3.1 Integration testing with related modules
  - [ ] 3.2 Documentation updates
  - [ ] 3.3 Deployment preparation
  - [ ] 3.4 User acceptance testing"""


class DocumentationQualityValidator:
    """Validator for documentation quality and completeness."""
    
    def __init__(self):
        self.required_sections = [
            "# Spec Requirements Document",
            "## Prompt Summary", 
            "## Executive Summary",
            "## System Overview",
            "## User Stories",
            "## Spec Scope",
            "## Expected Deliverable"
        ]
    
    def validate_documents(self, documents: Dict[str, str]) -> Dict[str, Any]:
        """Validate all documents and return quality metrics."""
        validation_results = {
            "overall_score": 0.0,
            "document_scores": {},
            "missing_sections": [],
            "quality_issues": [],
            "recommendations": []
        }
        
        total_score = 0
        document_count = 0
        
        for doc_name, content in documents.items():
            doc_score = self._validate_single_document(doc_name, content)
            validation_results["document_scores"][doc_name] = doc_score
            total_score += doc_score["overall_score"]
            document_count += 1
            
            if doc_score["missing_sections"]:
                validation_results["missing_sections"].extend(
                    [f"{doc_name}: {section}" for section in doc_score["missing_sections"]]
                )
        
        validation_results["overall_score"] = total_score / document_count if document_count > 0 else 0
        
        # Generate recommendations
        if validation_results["overall_score"] < 0.8:
            validation_results["recommendations"].append(
                "Documentation quality below recommended threshold. Review missing sections and content completeness."
            )
        
        return validation_results
    
    def _validate_single_document(self, doc_name: str, content: str) -> Dict[str, Any]:
        """Validate a single document."""
        result = {
            "overall_score": 0.0,
            "completeness_score": 0.0,
            "readability_score": 0.0,
            "structure_score": 0.0,
            "missing_sections": [],
            "issues": []
        }
        
        # Check completeness
        if doc_name == "spec.md":
            missing_sections = []
            for section in self.required_sections:
                if section not in content:
                    missing_sections.append(section)
            
            result["missing_sections"] = missing_sections
            result["completeness_score"] = 1.0 - (len(missing_sections) / len(self.required_sections))
        else:
            result["completeness_score"] = 1.0  # Assume other docs are complete
        
        # Check structure (basic)
        has_proper_headers = bool(re.search(r'^#\s+', content, re.MULTILINE))
        has_content = len(content.strip()) > 100
        
        result["structure_score"] = (int(has_proper_headers) + int(has_content)) / 2
        
        # Simple readability check
        word_count = len(content.split())
        sentence_count = content.count('.') + content.count('!') + content.count('?')
        avg_sentence_length = word_count / max(sentence_count, 1)
        
        # Readability score based on sentence length (simplified)
        if avg_sentence_length <= 20:
            result["readability_score"] = 1.0
        elif avg_sentence_length <= 30:
            result["readability_score"] = 0.8
        else:
            result["readability_score"] = 0.6
        
        # Calculate overall score
        result["overall_score"] = (
            result["completeness_score"] * 0.5 +
            result["structure_score"] * 0.3 +
            result["readability_score"] * 0.2
        )
        
        return result


# Example usage and configuration
if __name__ == "__main__":
    # Example configuration
    prompt_summary = PromptSummary(
        original_request="/create-specs for enhanced documentation system",
        context_provided="Agent OS framework enhancement requirements",
        clarifications_made=[
            "Module-based organization confirmed",
            "Cross-repository referencing required",
            "Enhanced visual documentation needed"
        ],
        reuse_notes="This configuration can be reused for similar documentation enhancement specs",
        prompt_evolution="Track iterative improvements based on user feedback and requirements refinement"
    )
    
    executive_summary = ExecutiveSummary(
        purpose="Enhance Agent OS spec creation with improved documentation, organization, and cross-repository capabilities",
        impact={
            "business_value": "Standardized development workflows across all repositories",
            "user_benefit": "Consistent, well-documented specs with visual clarity",
            "technical_advancement": "Module-based organization with AI persistence"
        },
        scope={
            "effort_estimate": "Large (L)",
            "timeline": "2-3 weeks",
            "dependencies": ["Agent OS framework", "AssetUtilities repository", "Git workflows"]
        },
        key_outcomes=[
            "Enhanced /create-specs workflow",
            "Cross-repository sub-agent system", 
            "Multi-level AI persistence"
        ]
    )
    
    # Create configuration
    config = SpecConfiguration(
        module_name="agent-os",
        spec_name="enhanced-create-specs",
        sub_agent_type="workflow-automation",
        ai_context_description="Enhanced Agent OS spec creation workflow with module organization and cross-repository capabilities",
        prompt_summary=prompt_summary,
        executive_summary=executive_summary,
        flow_description="User initiates enhanced spec creation, system identifies module, creates structured documentation with visual diagrams and cross-repository references",
        spec_scope=[
            {"name": "Enhanced Spec Creation Workflow", "description": "Upgrade existing workflow with module organization and enhanced documentation"},
            {"name": "Cross-Repository Sub-Agent System", "description": "Enable sharing of sub-agents across multiple repositories"},
            {"name": "Multi-Level AI Persistence", "description": "Implement persistence at system, user, and repository levels"}
        ],
        out_of_scope=[
            "Migration of existing specs to new structure",
            "Real-time collaborative editing",
            "Integration with external project management tools"
        ],
        expected_deliverables=[
            {"name": "Enhanced create-specs workflow", "description": "Fully functional enhanced spec creation with all requested features"},
            {"name": "Cross-repository referencing system", "description": "Working system for sharing sub-agents across repositories"},
            {"name": "Multi-level AI persistence", "description": "Implemented persistence at system, user, and repository levels"}
        ]
    )
    
    # Generate documentation
    generator = EnhancedDocumentationGenerator()
    documents = generator.generate_complete_specification(config)
    
    # Validate quality
    quality_results = generator.validate_documentation_quality(documents)
    
    # Print results
    print("Generated Documents:")
    for doc_name in documents.keys():
        print(f"  - {doc_name}")
    
    print(f"\nOverall Quality Score: {quality_results['overall_score']:.2f}")
    
    if quality_results['missing_sections']:
        print("\nMissing Sections:")
        for section in quality_results['missing_sections']:
            print(f"  - {section}")