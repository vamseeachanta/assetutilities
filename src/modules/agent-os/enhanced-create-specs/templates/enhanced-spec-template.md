# Spec Requirements Document

> **Module:** {{module_name}}
> **Spec:** {{spec_name}}
> **Sub-Agent:** {{sub_agent_type}}
> **Created:** {{creation_date}}
> **Status:** {{status}}
> **AI Context:** {{ai_context_description}}

## Prompt Summary

**Original Request:** {{original_request}}

**Context Provided:** {{context_provided}}

**Clarifications Made:** 
{{#clarifications_made}}
- {{.}}
{{/clarifications_made}}

**Reuse Notes:** {{reuse_notes}}

**Prompt Evolution:** {{prompt_evolution}}

## Executive Summary

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
{{/executive_summary.key_outcomes}}

## System Overview

```mermaid
{{mermaid_diagram}}
```

### Flow Description
{{flow_description}}

### Integration Points
{{#integration_points}}
- **{{name}}:** {{description}}
{{/integration_points}}

## User Stories

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

{{/user_stories}}

## Spec Scope

{{#spec_scope}}
{{@index}}. **{{name}}** - {{description}}
{{/spec_scope}}

## Out of Scope

{{#out_of_scope}}
- {{.}}
{{/out_of_scope}}

{{#conditional_sections}}
{{#has_module_dependencies}}
## Module Dependencies

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
{{/has_data_flow}}

{{/has_module_dependencies}}
{{/conditional_sections}}

## Expected Deliverable

{{#expected_deliverables}}
{{@index}}. **{{name}}** - {{description}}
{{/expected_deliverables}}

{{#conditional_sections}}
{{#has_sub_specs}}
## Spec Documentation

{{#sub_spec_references}}
- {{name}}: @{{path}}
{{/sub_spec_references}}

{{/has_sub_specs}}
{{/conditional_sections}}

---

**Navigation:**
{{#navigation}}
- [← Previous: {{previous.name}}]({{previous.path}})
- [Next: {{next.name}} →]({{next.path}})
{{/navigation}}

**Cross-Repository References:**
{{#cross_repo_references}}
- [{{name}}]({{reference}})
{{/cross_repo_references}}