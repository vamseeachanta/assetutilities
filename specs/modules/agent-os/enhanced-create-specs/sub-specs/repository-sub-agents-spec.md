# Repository-Specific Sub-Agents Specification

This is the sub-agent specification for repository-specific functionality detailed in @specs/modules/agent-os/enhanced-create-specs/spec.md

> Created: 2025-08-02
> Version: 1.0.0

## Overview

Create specialized sub-agents for each repository in the enhanced create-specs ecosystem, providing repository-specific functionality, domain expertise, and workflow automation tailored to each project's unique requirements.

## Repository Categories & Sub-Agents

### Engineering & Analysis Repositories (6)

#### 1. aceengineer-website
- **Sub-Agent:** `web-engineering-agent`
- **Module:** `web-engineering`
- **Expertise:** Flask web applications, client management systems, business development tools
- **Capabilities:**
  - Web application development and deployment workflows
  - Client project management and tracking
  - Business process automation
  - Contact form processing and customer relationship management

#### 2. aceengineercode  
- **Sub-Agent:** `engineering-analysis-agent`
- **Module:** `engineering-analysis`
- **Expertise:** Structural analysis, API579 implementation, OrcaFlex modeling, fatigue analysis
- **Capabilities:**
  - Engineering calculation workflows and validation
  - Stress analysis and fracture mechanics computations
  - Oil & gas industry standards implementation (API579, ASME, DNV)
  - FEA model generation and post-processing

#### 3. digitalmodel
- **Sub-Agent:** `digital-modeling-agent`
- **Module:** `digital-modeling`
- **Expertise:** Digital twins, computational modeling, simulation workflows
- **Capabilities:**
  - Digital model development and validation
  - Simulation parameter optimization
  - Model verification and benchmarking
  - Data-driven modeling approaches

#### 4. energy
- **Sub-Agent:** `energy-analysis-agent`
- **Module:** `energy-analysis`
- **Expertise:** Energy sector analysis, market research, renewable energy systems
- **Capabilities:**
  - Energy market analysis and forecasting
  - Renewable energy system design
  - Energy policy impact assessment
  - Carbon footprint analysis and sustainability metrics

#### 5. rock-oil-field
- **Sub-Agent:** `oil-field-operations-agent`
- **Module:** `oil-field-operations`
- **Expertise:** Oil field development, drilling operations, reservoir engineering
- **Capabilities:**
  - Drilling program optimization
  - Well completion design and analysis
  - Production forecasting and optimization
  - Field development planning and economics

#### 6. saipem
- **Sub-Agent:** `offshore-engineering-agent`
- **Module:** `offshore-engineering`
- **Expertise:** Offshore engineering, subsea systems, marine operations
- **Capabilities:**
  - Subsea system design and analysis
  - Marine vessel operations planning
  - Offshore installation procedures
  - Deepwater engineering solutions

### Project Management Repositories (4)

#### 7. acma-projects
- **Sub-Agent:** `project-coordination-agent`
- **Module:** `project-coordination`
- **Expertise:** Project management, activity planning, resource coordination
- **Capabilities:**
  - Project planning and milestone tracking
  - Resource allocation and scheduling
  - Activity coordination and progress monitoring
  - Project documentation and reporting

#### 8. client_projects
- **Sub-Agent:** `client-management-agent`
- **Module:** `client-management`
- **Expertise:** Client relationship management, project delivery, contract management
- **Capabilities:**
  - Client requirement analysis and specification
  - Project scope definition and change management
  - Deliverable tracking and quality assurance
  - Client communication and reporting workflows

#### 9. investments
- **Sub-Agent:** `investment-analysis-agent`
- **Module:** `investment-analysis`
- **Expertise:** Financial analysis, investment evaluation, portfolio management
- **Capabilities:**
  - Investment opportunity analysis and due diligence
  - Financial modeling and risk assessment
  - Portfolio optimization and diversification
  - Market trend analysis and forecasting

#### 10. teamresumes
- **Sub-Agent:** `talent-management-agent`
- **Module:** `talent-management`
- **Expertise:** Human resources, team coordination, skill assessment
- **Capabilities:**
  - Resume analysis and skill mapping
  - Team composition optimization
  - Talent acquisition and evaluation
  - Professional development planning

### Infrastructure & Utilities (4)

#### 11. assethold
- **Sub-Agent:** `asset-management-agent`
- **Module:** `asset-management`
- **Expertise:** Asset lifecycle management, maintenance planning, depreciation analysis
- **Capabilities:**
  - Asset tracking and inventory management
  - Maintenance scheduling and optimization
  - Asset performance analysis and reporting
  - Lifecycle cost analysis and budgeting

#### 12. assetutilities (Hub Repository)
- **Sub-Agent:** `utilities-hub-agent`
- **Module:** `utilities-hub`
- **Expertise:** Cross-repository coordination, shared utilities, system integration
- **Capabilities:**
  - Hub repository management and coordination
  - Cross-repository component sharing and versioning
  - System-wide utility development and maintenance
  - Integration testing and compatibility management

#### 13. pyproject-starter
- **Sub-Agent:** `project-template-agent`
- **Module:** `project-templates`
- **Expertise:** Project initialization, template management, development workflows
- **Capabilities:**
  - Python project template creation and customization
  - Development environment setup and configuration
  - Best practices implementation and enforcement
  - Project structure standardization

#### 14. worldenergydata
- **Sub-Agent:** `energy-data-agent`
- **Module:** `energy-data`
- **Expertise:** Energy data analysis, BSEE data processing, oil & gas analytics
- **Capabilities:**
  - Energy dataset processing and analysis
  - Regulatory data compliance and reporting
  - Statistical modeling and trend analysis
  - Data visualization and dashboard creation

### AI & Development (1)

#### 15. ai-native-traditional-eng
- **Sub-Agent:** `ai-engineering-integration-agent`
- **Module:** `ai-engineering-integration`
- **Expertise:** AI-traditional engineering integration, machine learning applications
- **Capabilities:**
  - AI model development for engineering applications
  - Traditional engineering process automation
  - ML pipeline development and deployment
  - Hybrid AI-traditional system design

### Documentation Repositories (2)

#### 16. frontierdeepwater
- **Sub-Agent:** `deepwater-documentation-agent`
- **Module:** `deepwater-documentation`
- **Expertise:** Deepwater project documentation, technical writing, knowledge management
- **Capabilities:**
  - Technical documentation creation and maintenance
  - Project knowledge capture and organization
  - Document version control and collaboration
  - Information architecture and searchability

#### 17. OGManufacturing
- **Sub-Agent:** `manufacturing-documentation-agent`
- **Module:** `manufacturing-documentation`
- **Expertise:** Manufacturing process documentation, quality management, compliance
- **Capabilities:**
  - Manufacturing process documentation and standardization
  - Quality control procedure development
  - Compliance documentation and audit support
  - Process improvement and optimization documentation

## Sub-Agent Architecture

### Standard Sub-Agent Structure

Each repository sub-agent follows this standardized structure:

```
agents/modules/<module_name>/
├── <repository_name>_agent.md              # Agent definition and capabilities
├── workflows/                               # Repository-specific workflows
│   ├── development_workflow.md
│   ├── testing_workflow.md
│   └── deployment_workflow.md
├── templates/                               # Repository-specific templates
│   ├── spec_template.md
│   ├── documentation_template.md
│   └── task_template.md
├── knowledge/                               # Domain-specific knowledge base
│   ├── best_practices.md
│   ├── common_patterns.md
│   └── troubleshooting.md
└── config/                                  # Agent configuration
    ├── agent_config.yml
    ├── tool_preferences.yml
    └── context_settings.yml
```

### Cross-Repository Integration

Sub-agents are designed to work together through:

1. **Shared Utilities Access:** All sub-agents can reference `@github:assetutilities/agents/modules/utilities-hub/`
2. **Cross-Agent Communication:** Agents can invoke other repository agents for collaborative workflows
3. **Knowledge Sharing:** Common patterns and solutions are shared through the hub repository
4. **Standardized Interfaces:** All agents follow the same API and communication protocols

### Agent Capabilities Matrix

| Repository | Sub-Agent | Domain Expertise | Primary Tools | Cross-Repo Dependencies |
|-----------|-----------|------------------|---------------|------------------------|
| aceengineer-website | web-engineering-agent | Web Development | Flask, HTML/CSS, Database | assetutilities, client_projects |
| aceengineercode | engineering-analysis-agent | Structural Analysis | Python, NumPy, SciPy | assetutilities, digitalmodel |
| digitalmodel | digital-modeling-agent | Digital Twins | Python, Simulation Tools | assetutilities, engineering repos |
| energy | energy-analysis-agent | Energy Markets | Python, Data Analysis | worldenergydata, investments |
| rock-oil-field | oil-field-operations-agent | Oil & Gas Operations | Industry Software, Python | aceengineercode, saipem |
| saipem | offshore-engineering-agent | Offshore Engineering | CAD, Analysis Tools | aceengineercode, rock-oil-field |
| acma-projects | project-coordination-agent | Project Management | Planning Tools, Documentation | client_projects, teamresumes |
| client_projects | client-management-agent | Client Relations | CRM, Communication Tools | acma-projects, aceengineer-website |
| investments | investment-analysis-agent | Financial Analysis | Financial Tools, Python | energy, assetutilities |
| teamresumes | talent-management-agent | HR Management | Resume Tools, Analysis | acma-projects, client_projects |
| assethold | asset-management-agent | Asset Lifecycle | Asset Tools, Database | assetutilities |
| assetutilities | utilities-hub-agent | System Integration | All Tools, Coordination | ALL repositories |
| pyproject-starter | project-template-agent | Project Templates | Python, Templates | assetutilities |
| worldenergydata | energy-data-agent | Energy Data | Data Tools, Analytics | energy, investments |
| ai-native-traditional-eng | ai-engineering-integration-agent | AI/ML Engineering | AI/ML Tools, Python | aceengineercode, digitalmodel |
| frontierdeepwater | deepwater-documentation-agent | Technical Documentation | Documentation Tools | saipem, rock-oil-field |
| OGManufacturing | manufacturing-documentation-agent | Manufacturing Docs | Documentation Tools | assetutilities |

## Implementation Strategy

### Phase 1: Core Sub-Agents (Week 1)
1. Create `utilities-hub-agent` in assetutilities (central coordination)
2. Implement `engineering-analysis-agent` and `web-engineering-agent` (primary engineering repos)
3. Set up basic cross-repository referencing infrastructure

### Phase 2: Domain-Specific Agents (Week 2)
1. Deploy all engineering & analysis sub-agents
2. Implement project management sub-agents
3. Create infrastructure & utilities sub-agents

### Phase 3: Specialized Agents (Week 3)
1. Deploy AI & development sub-agents
2. Implement documentation sub-agents
3. Create comprehensive cross-agent communication protocols

### Phase 4: Integration & Optimization (Week 4)
1. Test all cross-repository integrations
2. Optimize agent performance and capabilities
3. Create comprehensive documentation and training materials

## Expected Deliverables

1. **17 Repository-Specific Sub-Agents** - Fully functional sub-agents for each repository
2. **Cross-Repository Integration** - Working system for agent collaboration and communication
3. **Standardized Agent Framework** - Common structure and protocols for all sub-agents
4. **Domain Knowledge Bases** - Specialized knowledge repositories for each domain
5. **Agent Coordination System** - Central hub for managing cross-agent workflows

## Success Metrics

- **Coverage:** 100% of repositories have functional sub-agents
- **Integration:** All sub-agents can communicate and collaborate effectively
- **Performance:** Sub-agents reduce development time by 30-50%
- **Quality:** Enhanced consistency and standardization across all repositories
- **Adoption:** Teams actively use sub-agents for daily development workflows

This specification establishes a comprehensive sub-agent ecosystem that provides specialized expertise for each repository while maintaining seamless integration and collaboration across the entire development environment.