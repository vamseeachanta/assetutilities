#!/usr/bin/env python3
"""
Unified /create-spec command with enhanced features by default.
Includes mermaid diagrams, executive summaries, and variant support.

MANDATORY: All specs MUST be created in specs/modules/[module-name] structure.
This is enforced across all repositories.

Usage:
  create-spec <spec-name> <module-name> [options]
  
Options:
  --variant=TYPE    Spec variant: standard (default), minimal, research, api
  --no-diagrams     Skip mermaid diagram generation
  --no-summary      Skip executive summary generation
"""

import sys
import os
import argparse
from datetime import datetime
from pathlib import Path

def create_spec_directory(spec_name, module_name):
    """Create specification directory structure.
    
    MANDATORY: Module name is required. All specs must be in specs/modules/[module-name]/
    """
    today = datetime.now().strftime("%Y-%m-%d")
    spec_folder_name = f"{today}-{spec_name}"
    
    # MANDATORY: Module-based organization only
    specs_base = Path("specs/modules")
    module_dir = specs_base / module_name
    module_dir.mkdir(parents=True, exist_ok=True)
    
    spec_path = module_dir / spec_folder_name
    spec_path.mkdir(exist_ok=True)
    
    # Create sub-directories
    (spec_path / "sub-specs").mkdir(exist_ok=True)
    (spec_path / "diagrams").mkdir(exist_ok=True)
    (spec_path / "summaries").mkdir(exist_ok=True)
    
    return spec_path

def create_spec_file(spec_path, spec_name, variant="standard", include_diagrams=True):
    """Create spec.md file with appropriate content based on variant."""
    
    if variant == "minimal":
        spec_content = f"""# {spec_name.replace('-', ' ').title()} Specification

> Created: {datetime.now().strftime("%Y-%m-%d")}
> Variant: Minimal

## Goal
[One sentence describing what this spec achieves]

## User Story
As a [user type], I want [functionality] so that [benefit].

## Requirements
- [ ] [Core requirement]
- [ ] [Core requirement]
- [ ] [Core requirement]

## Tasks
- [ ] [Implementation task]
- [ ] [Testing task]
- [ ] [Documentation task]

## Definition of Done
- [ ] Code implemented and tested
- [ ] Documentation updated
- [ ] All tests passing
"""
    
    elif variant == "research":
        spec_content = f"""# Research Specification Document

> Spec: {spec_name}
> Created: {datetime.now().strftime("%Y-%m-%d")}
> Status: Research Planning
> Variant: Research

## Research Objective
[Clear statement of research question or hypothesis to be addressed]

## Background & Context
### Current State
[Summary of existing knowledge and practices]

### Knowledge Gaps
[Specific gaps this research will address]

### Research Questions
1. [Primary research question]
2. [Secondary research questions]

## Methodology
### Data Sources
- [Primary data sources and access methods]
- [Secondary data sources for validation]

### Analysis Approach
- [Statistical methods to be employed]
- [Modeling techniques and rationale]

### Validation Strategy
- [How results will be validated]
- [Peer review and reproducibility measures]

## Expected Outcomes
### Research Deliverables
1. [Research findings and insights]
2. [Methodology documentation]
3. [Reproducible analysis notebooks]

### Applications
- [How findings can be applied in practice]
- [Potential impact on decisions]

## Timeline & Milestones
### Phase 1: Data Collection (Weeks 1-2)
- [ ] [Specific milestone]

### Phase 2: Analysis (Weeks 3-4)
- [ ] [Specific milestone]

### Phase 3: Documentation (Weeks 5-6)
- [ ] [Specific milestone]
"""

    elif variant == "api":
        spec_content = f"""# API Specification Document

> Spec: {spec_name}
> Created: {datetime.now().strftime("%Y-%m-%d")}
> Status: Planning
> Variant: API-Focused

## API Overview
[High-level description of the API purpose and capabilities]

## Resource Model
### Primary Resources
- **[Resource Name]**: [Description and purpose]
- **[Resource Name]**: [Description and purpose]

### Resource Relationships
[How resources relate to each other]

## Endpoints

### GET /api/v1/[resource]
**Purpose:** [What this endpoint does]
**Authentication:** Required/Optional
**Parameters:**
- `param1` (required): [Description]
- `param2` (optional): [Description]

**Response:** 200 OK
```json
{{
  "data": [],
  "meta": {{}}
}}
```

### POST /api/v1/[resource]
**Purpose:** [What this endpoint does]
**Authentication:** Required
**Request Body:**
```json
{{
  "field1": "value",
  "field2": "value"
}}
```

**Response:** 201 Created
```json
{{
  "id": "uuid",
  "field1": "value",
  "field2": "value"
}}
```

## Authentication & Security
### Authentication Method
[JWT/OAuth/API Keys - specify approach]

### Rate Limiting
- Anonymous: X requests/minute
- Authenticated: Y requests/minute

### Security Headers
- `X-API-Version`: API version
- `X-Request-ID`: Unique request identifier

## Error Handling
### Error Response Format
```json
{{
  "error": {{
    "code": "ERROR_CODE",
    "message": "Human readable message",
    "details": {{}}
  }}
}}
```

### Standard Error Codes
- `400`: Bad Request
- `401`: Unauthorized
- `403`: Forbidden
- `404`: Not Found
- `429`: Too Many Requests
- `500`: Internal Server Error

## Testing Strategy
- Unit tests for each endpoint
- Integration tests for workflows
- Load testing for performance
- Security testing for vulnerabilities
"""
    
    else:  # standard (default)
        mermaid_section = ""
        if include_diagrams:
            mermaid_section = """
## System Architecture

### Data Flow
```mermaid
graph TD
    A[Input Source] --> B[Processing Layer]
    B --> C[Business Logic]
    C --> D[Data Storage]
    C --> E[Output Layer]
    E --> F[User Interface]
    E --> G[API Response]
```

### Component Interaction
```mermaid
sequenceDiagram
    participant User
    participant System
    participant Database
    participant External
    
    User->>System: Request
    System->>Database: Query data
    Database-->>System: Return data
    System->>External: Fetch additional data (if needed)
    External-->>System: Return data
    System->>System: Process & validate
    System-->>User: Response
```
"""
        
        spec_content = f"""# Spec Requirements Document

> Spec: {spec_name}
> Created: {datetime.now().strftime("%Y-%m-%d")}
> Status: Planning
> Variant: Standard (with enhanced features)

## Executive Summary

### Business Impact
[High-level business value and strategic alignment]

### Key Deliverables
- [Primary deliverable with business value]
- [Secondary deliverable with user impact]
- [Technical deliverable with system improvement]

### Success Metrics
- [Quantifiable success measure]
- [User adoption target]
- [Performance improvement goal]

## Overview
[Comprehensive description of what this spec accomplishes]

## User Stories

### Primary User Workflow
As a [user type], I want to [specific functionality], so that I can [business value].

**Acceptance Criteria:**
- [ ] [Specific testable condition]
- [ ] [User interface requirement]
- [ ] [Performance requirement]

### Secondary User Workflow
As a [user type], I want to [specific functionality], so that I can [value/benefit].

**Acceptance Criteria:**
- [ ] [Data quality requirement]
- [ ] [Analysis capability requirement]
- [ ] [Export/sharing requirement]
{mermaid_section}
## Spec Scope

### Phase 1: Core Implementation
1. **[Feature Name]** - [Implementation details and acceptance criteria]
2. **[Feature Name]** - [Implementation details and acceptance criteria]

### Phase 2: Enhanced Features
1. **[Advanced Feature]** - [Enhanced capability description]
2. **[Integration Feature]** - [Cross-system integration details]

## Out of Scope
- [Explicitly excluded functionality with rationale]
- [Future considerations for next iteration]

## Expected Deliverable

### Technical Deliverables
1. [Specific code module or function with test coverage]
2. [Documentation updates with examples]
3. [Performance benchmarks and optimization]

### User Deliverables
1. [User-facing feature with usage examples]
2. [Updated user documentation and tutorials]
3. [Migration guide if applicable]

## Risk Assessment

### Technical Risks
- **[Risk Category]:** [Description and mitigation strategy]

### Business Risks
- **[Risk Category]:** [Impact and contingency plan]

## Dependencies

### Internal Dependencies
- [Existing components required]
- [Agent OS framework components needed]

### External Dependencies
- [Third-party libraries or APIs required]
- [Data source availability requirements]

## Testing Strategy

### Unit Testing
- [Specific test requirements for core functions]
- [Data validation test requirements]

### Integration Testing
- [End-to-end workflow testing requirements]
- [Performance testing requirements]

### User Acceptance Testing
- [User scenario testing requirements]
- [Documentation and tutorial validation]

## Documentation

### Code Documentation
- [API documentation requirements]
- [Inline documentation standards]

### User Documentation
- [Tutorial creation requirements]
- [Example notebooks and use cases]

## Spec Documentation

- **Tasks:** @{spec_path.name}/tasks.md
- **Technical Specification:** @{spec_path.name}/sub-specs/technical-spec.md
- **API Specification:** @{spec_path.name}/sub-specs/api-spec.md
- **Tests Specification:** @{spec_path.name}/sub-specs/tests.md
- **Executive Summary:** @{spec_path.name}/summaries/executive-summary.md
- **System Architecture:** @{spec_path.name}/diagrams/architecture.mmd
"""
    
    with open(spec_path / "spec.md", "w") as f:
        f.write(spec_content)

def create_tasks_file(spec_path, spec_name, variant="standard"):
    """Create tasks.md with appropriate detail level."""
    
    if variant == "minimal":
        tasks_content = f"""# Tasks - {spec_name}

> Created: {datetime.now().strftime("%Y-%m-%d")}

## Implementation Tasks

- [ ] Core implementation
- [ ] Add tests
- [ ] Update documentation
- [ ] Code review
- [ ] Deploy

## Definition of Done
- [ ] All tests passing
- [ ] Documentation updated
- [ ] Code reviewed
"""
    else:
        tasks_content = f"""# Spec Tasks - {spec_name}

> Created: {datetime.now().strftime("%Y-%m-%d")}
> Status: Ready for Implementation

## Task Summary

**Total Estimated Effort:** [X weeks]
**Priority:** High/Medium/Low
**Dependencies:** [List any dependencies]

## Phase 1: Foundation

- [ ] **1. Project Setup** `M`
  - [ ] 1.1 Create module structure
  - [ ] 1.2 Set up testing infrastructure
  - [ ] 1.3 Configure dependencies
  - [ ] 1.4 Initialize documentation
  - [ ] 1.5 Verify foundation tests pass

- [ ] **2. Core Implementation** `L`
  - [ ] 2.1 Write unit tests for core functions
  - [ ] 2.2 Implement main logic
  - [ ] 2.3 Add error handling
  - [ ] 2.4 Implement logging
  - [ ] 2.5 Verify all core tests pass

## Phase 2: Integration

- [ ] **3. System Integration** `M`
  - [ ] 3.1 Write integration tests
  - [ ] 3.2 Implement integrations
  - [ ] 3.3 Test end-to-end workflows
  - [ ] 3.4 Verify integration tests pass

- [ ] **4. User Interface** `M`
  - [ ] 4.1 Write UI tests
  - [ ] 4.2 Implement user interface
  - [ ] 4.3 Add input validation
  - [ ] 4.4 Verify UI tests pass

## Phase 3: Quality & Documentation

- [ ] **5. Documentation** `S`
  - [ ] 5.1 Create API documentation
  - [ ] 5.2 Write user guides
  - [ ] 5.3 Add code documentation
  - [ ] 5.4 Create examples
  - [ ] 5.5 Verify documentation completeness

- [ ] **6. Quality Assurance** `M`
  - [ ] 6.1 Run complete test suite
  - [ ] 6.2 Code review and refactoring
  - [ ] 6.3 Performance testing
  - [ ] 6.4 Security review
  - [ ] 6.5 Final verification

## Definition of Done

- [ ] All code implemented following standards
- [ ] Test coverage >= 80%
- [ ] All tests passing
- [ ] Documentation complete
- [ ] Code review completed
- [ ] Performance benchmarks met

## Effort Estimates

- **XS:** 1-2 hours
- **S:** 1-2 days  
- **M:** 3-5 days
- **L:** 1-2 weeks
- **XL:** 3-4 weeks
"""
    
    with open(spec_path / "tasks.md", "w") as f:
        f.write(tasks_content)

def create_executive_summary(spec_path, spec_name):
    """Create executive summary for business stakeholders."""
    summary_content = f"""# Executive Summary - {spec_name}

> Created: {datetime.now().strftime("%Y-%m-%d")}
> Audience: Business Stakeholders

## Business Case

### Problem Statement
[Clear description of the business problem]

### Proposed Solution
[High-level solution overview]

### Expected Benefits
- **Cost Savings:** [Quantified cost reduction]
- **Time Savings:** [Quantified time reduction]
- **Capability Enhancement:** [New capabilities]

## Investment & Resources

### Development Effort
- **Timeline:** [X weeks/months]
- **Team Requirements:** [Roles needed]

### Success Metrics
- **User Adoption:** [Target metrics]
- **Performance:** [Performance goals]
- **Business Impact:** [Impact measures]

## Risk Assessment

### Key Risks
- **[Risk]:** [Mitigation strategy]

## Recommendation

[Clear recommendation with next steps]

### Go/No-Go Criteria
- [ ] [Critical success factor]
- [ ] [Resource availability]
- [ ] [Stakeholder alignment]
"""
    
    summary_path = spec_path / "summaries"
    summary_path.mkdir(exist_ok=True)
    
    with open(summary_path / "executive-summary.md", "w") as f:
        f.write(summary_content)

def create_mermaid_diagrams(spec_path, spec_name):
    """Create standalone mermaid diagram files."""
    
    architecture_diagram = f"""# System Architecture - {spec_name}

## High-Level Architecture

```mermaid
graph TB
    subgraph "Input Layer"
        A[Data Sources]
        B[User Input]
        C[External APIs]
    end
    
    subgraph "Processing Layer"
        D[Data Validation]
        E[Business Logic]
        F[Integration Layer]
    end
    
    subgraph "Storage Layer"
        G[Database]
        H[Cache]
        I[File Storage]
    end
    
    subgraph "Output Layer"
        J[User Interface]
        K[API Endpoints]
        L[Reports/Exports]
    end
    
    A --> D
    B --> D
    C --> D
    D --> E
    E --> F
    F --> G
    F --> H
    F --> I
    G --> J
    H --> J
    G --> K
    H --> K
    I --> L
```

## Data Flow Sequence

```mermaid
sequenceDiagram
    participant User
    participant UI as User Interface
    participant API as API Layer
    participant BL as Business Logic
    participant DB as Database
    participant Ext as External Service
    
    User->>UI: Initiate Request
    UI->>API: Send Request
    API->>API: Validate Input
    API->>BL: Process Request
    BL->>DB: Query Data
    DB-->>BL: Return Data
    BL->>Ext: Fetch Additional Data
    Ext-->>BL: Return Data
    BL->>BL: Apply Business Rules
    BL-->>API: Return Result
    API-->>UI: Send Response
    UI-->>User: Display Result
```

## Component Class Diagram

```mermaid
classDiagram
    class Controller {
        +handleRequest()
        +validateInput()
        +formatResponse()
    }
    
    class Service {
        +processData()
        +applyBusinessLogic()
        +handleErrors()
    }
    
    class Repository {
        +create()
        +read()
        +update()
        +delete()
    }
    
    class Model {
        +id: string
        +data: object
        +validate()
        +serialize()
    }
    
    Controller --> Service : uses
    Service --> Repository : uses
    Repository --> Model : manages
```

## State Diagram

```mermaid
stateDiagram-v2
    [*] --> Idle
    Idle --> Processing : Request Received
    Processing --> Validating : Start Validation
    Validating --> Processing : Validation Failed
    Validating --> Executing : Validation Passed
    Executing --> Success : Execution Complete
    Executing --> Error : Execution Failed
    Success --> Idle : Reset
    Error --> Idle : Reset
    Error --> Retry : Retry Requested
    Retry --> Processing : Retry Attempt
```
"""
    
    diagrams_path = spec_path / "diagrams"
    diagrams_path.mkdir(exist_ok=True)
    
    with open(diagrams_path / "architecture.mmd", "w") as f:
        f.write(architecture_diagram)

def create_sub_specs(spec_path, variant="standard"):
    """Create sub-specification templates."""
    
    # Technical spec
    tech_spec = f"""# Technical Specification

> Created: {datetime.now().strftime("%Y-%m-%d")}

## Technical Requirements
- [Specific technical requirement]
- [Performance requirement]
- [Scalability requirement]

## Implementation Approach
- [Technical approach details]
- [Architecture decisions]
- [Technology choices]

## Performance Requirements
- Response time: < X ms
- Throughput: Y requests/second
- Memory usage: < Z MB

## Security Considerations
- [Authentication requirements]
- [Authorization model]
- [Data encryption requirements]
- [Audit logging requirements]

## Database Design
- [Schema considerations]
- [Indexing strategy]
- [Data retention policy]

## Integration Points
- [Internal service integrations]
- [External API integrations]
- [Message queue integrations]
"""
    
    # API spec
    api_spec = f"""# API Specification

> Created: {datetime.now().strftime("%Y-%m-%d")}

## API Overview
[General API description and purpose]

## Base URL
- Development: `https://dev-api.example.com/v1`
- Production: `https://api.example.com/v1`

## Authentication
- Method: [Bearer Token / API Key / OAuth]
- Header: `Authorization: Bearer {{token}}`

## Endpoints

### GET /api/[resource]
- **Purpose:** [Description]
- **Parameters:** 
  - `limit` (optional): Number of results
  - `offset` (optional): Pagination offset
- **Response:** 
```json
{{
  "data": [],
  "meta": {{
    "total": 0,
    "limit": 10,
    "offset": 0
  }}
}}
```

### POST /api/[resource]
- **Purpose:** [Description]
- **Body:** 
```json
{{
  "field1": "required",
  "field2": "optional"
}}
```
- **Response:** HTTP 201 Created

## Error Handling
- Standard error format
- HTTP status codes
- Error recovery strategies

## Rate Limiting
- Limits per endpoint
- Rate limit headers
- Retry strategies
"""
    
    # Tests spec
    tests_spec = f"""# Tests Specification

> Created: {datetime.now().strftime("%Y-%m-%d")}

## Test Coverage Requirements
- Unit test coverage: >= 80%
- Integration test coverage: Core workflows
- E2E test coverage: Critical user paths

## Unit Tests
### Components to Test
- [Component/Function name]: [What to test]
- Input validation
- Business logic
- Error handling
- Edge cases

## Integration Tests
### Workflows to Test
- [Workflow name]: [Expected behavior]
- API endpoint integration
- Database operations
- External service mocking

## Performance Tests
### Scenarios
- Load test: [X concurrent users]
- Stress test: [Peak load scenario]
- Endurance test: [Duration and load]

## Security Tests
- Input sanitization
- SQL injection prevention
- XSS prevention
- Authentication/Authorization

## Test Data
### Requirements
- Test fixtures
- Mock data generation
- Database seeding

## Continuous Integration
- Test automation setup
- CI/CD pipeline integration
- Test reporting
"""
    
    sub_specs_path = spec_path / "sub-specs"
    sub_specs_path.mkdir(exist_ok=True)
    
    with open(sub_specs_path / "technical-spec.md", "w") as f:
        f.write(tech_spec)
    
    with open(sub_specs_path / "api-spec.md", "w") as f:
        f.write(api_spec)
    
    with open(sub_specs_path / "tests.md", "w") as f:
        f.write(tests_spec)

def main():
    """Main unified create-spec command."""
    parser = argparse.ArgumentParser(
        description="Create specification with enhanced features by default",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  create-spec user-auth security                    # Standard spec with all features
  create-spec user-auth security --variant=minimal  # Minimal spec
  create-spec user-auth security --no-diagrams      # Skip mermaid diagrams
  create-spec api-gateway core --variant=api        # API-focused spec
  create-spec ml-research data --variant=research   # Research spec
        """
    )
    
    parser.add_argument("spec_name", help="Name of the specification (kebab-case)")
    parser.add_argument("module_name", help="Module name for organization (required)")
    parser.add_argument(
        "--variant",
        choices=["standard", "minimal", "research", "api"],
        default="standard",
        help="Specification variant (default: standard with all enhanced features)"
    )
    parser.add_argument(
        "--no-diagrams",
        action="store_true",
        help="Skip mermaid diagram generation"
    )
    parser.add_argument(
        "--no-summary",
        action="store_true",
        help="Skip executive summary generation"
    )
    
    # Handle both command-line and slash command invocation
    if len(sys.argv) == 1:
        parser.print_help()
        return 1
    
    # Support legacy positional variant argument
    if len(sys.argv) == 4 and not sys.argv[3].startswith("--"):
        # Legacy: create-spec name module variant
        sys.argv[3] = f"--variant={sys.argv[3]}"
    
    args = parser.parse_args()
    
    try:
        variant_display = {
            "standard": "Standard (with enhanced features)",
            "minimal": "Minimal",
            "research": "Research",
            "api": "API-Focused"
        }
        
        print(f"🚀 Creating {variant_display[args.variant]} specification: {args.spec_name}")
        print(f"📦 Module: {args.module_name}")
        
        # Create directory structure
        spec_path = create_spec_directory(args.spec_name, args.module_name)
        print(f"📁 Created: {spec_path}")
        
        # Create main spec file
        include_diagrams = not args.no_diagrams and args.variant != "minimal"
        create_spec_file(spec_path, args.spec_name, args.variant, include_diagrams)
        print(f"📄 Created: {spec_path}/spec.md")
        
        # Create tasks file
        create_tasks_file(spec_path, args.spec_name, args.variant)
        print(f"📋 Created: {spec_path}/tasks.md")
        
        # Create sub-specs (except for minimal)
        if args.variant != "minimal":
            create_sub_specs(spec_path, args.variant)
            print(f"🔧 Created: {spec_path}/sub-specs/")
        
        # Create executive summary (except for minimal or if disabled)
        if not args.no_summary and args.variant != "minimal":
            create_executive_summary(spec_path, args.spec_name)
            print(f"📊 Created: {spec_path}/summaries/executive-summary.md")
        
        # Create mermaid diagrams (if not disabled and not minimal)
        if include_diagrams:
            create_mermaid_diagrams(spec_path, args.spec_name)
            print(f"🎨 Created: {spec_path}/diagrams/architecture.mmd")
        
        print(f"\n✅ Specification '{args.spec_name}' created successfully!")
        print(f"📍 Location: {spec_path}")
        
        # Feature summary
        print("\n📦 Features included:")
        features = []
        if args.variant == "standard":
            features = ["✓ Executive Summary", "✓ Mermaid Diagrams", "✓ Detailed Tasks", "✓ Sub-specs"]
        elif args.variant == "minimal":
            features = ["✓ Basic Spec", "✓ Simple Tasks"]
        elif args.variant == "research":
            features = ["✓ Research Framework", "✓ Methodology", "✓ Timeline"]
        elif args.variant == "api":
            features = ["✓ API Endpoints", "✓ Authentication", "✓ Error Handling"]
        
        if args.no_diagrams and args.variant != "minimal":
            features = [f for f in features if "Diagram" not in f]
        if args.no_summary and args.variant != "minimal":
            features = [f for f in features if "Summary" not in f]
        
        for feature in features:
            print(f"  {feature}")
        
        print("\n🚀 Next steps:")
        print("1. Review and customize the generated specification")
        print("2. Add specific details for your use case")
        print(f"3. Run: /execute-tasks @{spec_path}/tasks.md")
        
        return 0
        
    except Exception as e:
        print(f"❌ Error creating specification: {e}")
        import traceback
        traceback.print_exc()
        return 1

if __name__ == "__main__":
    sys.exit(main())