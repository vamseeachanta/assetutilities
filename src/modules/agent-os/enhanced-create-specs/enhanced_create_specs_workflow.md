---
description: Enhanced Spec Creation Rules for Agent OS with Module-Based Organization
globs:
alwaysApply: false
version: 2.0
encoding: UTF-8
---

# Enhanced Spec Creation Rules

<ai_meta>
  <parsing_rules>
    - Process XML blocks first for structured data
    - Execute instructions in sequential order
    - Use templates as exact patterns
    - Request missing data rather than assuming
  </parsing_rules>
  <file_conventions>
    - encoding: UTF-8
    - line_endings: LF
    - indent: 2 spaces
    - markdown_headers: no indentation
  </file_conventions>
  <module_organization>
    - specs/modules/<module_name>/<spec_name>/
    - docs/modules/<module_name>/
    - src/modules/<module_name>/
    - tests/modules/<module_name>/<spec_name>/
    - default_module: "product" for unclassified specs
    - subcategories: when >5 specs in module
  </module_organization>
</ai_meta>

## Overview

<purpose>
  - Create detailed spec plans for specific features using module-based organization
  - Generate structured documentation for implementation with executive summaries
  - Ensure alignment with product roadmap and mission
  - Provide prompt reusability and mermaid diagrams for visual clarity
  - Organize specs by logical modules for better maintainability
  - Enable cross-repository sub-agent referencing and reuse
</purpose>

<context>
  - Part of Agent OS framework
  - Executed when implementing roadmap items
  - Creates spec-specific documentation in module-based structure
  - Supports cross-repository sub-agent referencing
  - Implements multi-level AI persistence
</context>

<prerequisites>
  - Product documentation exists in .agent-os/product/
  - Access to:
    - @.agent-os/product/mission.md,
    - @.agent-os/product/roadmap.md,
    - @.agent-os/product/tech-stack.md
  - User has spec idea or roadmap reference
  - Repository follows module-based organization
  - AssetUtilities repository available for cross-repo referencing
</prerequisites>

<process_flow>

<step number="1" name="spec_initiation_and_prompt_capture">

### Step 1: Spec Initiation and Prompt Capture

<step_metadata>
  <trigger_options>
    - option_a: user_asks_whats_next
    - option_b: user_provides_specific_spec
  </trigger_options>
  <captures>original_user_prompt</captures>
  <cross_repo_reference>@github:assetutilities/src/modules/agent-os/enhanced-create-specs/</cross_repo_reference>
</step_metadata>

<prompt_capture>
  <purpose>Enable future reuse and iteration based on updated prompts</purpose>
  <content>
    - original_request: exact user input
    - context_provided: any additional context given
    - refinements: any clarifications made during process
    - reuse_notes: guidance for future iterations
  </content>
</prompt_capture>

<instructions>
  ACTION: Identify spec initiation method and capture original prompt
  STORE: Original user request for future reference and iteration
  ROUTE: Follow appropriate flow based on trigger
  REFERENCE: Use assetutilities hub for shared templates and patterns
  WAIT: Ensure user agreement before proceeding
</instructions>

</step>

<step number="2" name="module_identification">

### Step 2: Module Identification

<step_metadata>
  <purpose>Determine appropriate module for spec organization</purpose>
  <creates>module classification</creates>
  <references>AssetUtilities module registry</references>
</step_metadata>

<module_categories>
  <common_modules>
    - authentication: login, signup, password management
    - authorization: permissions, roles, access control
    - user-management: profiles, settings, preferences
    - data-management: CRUD operations, data processing
    - api: external integrations, webhooks
    - ui-ux: interface components, user experience
    - reporting: analytics, dashboards, exports
    - notifications: emails, alerts, messaging
    - payment: billing, subscriptions, transactions
    - admin: administrative functions, system management
    - agent-os: AI workflow and automation enhancements
  </common_modules>
  <default_module>product</default_module>
  <subcategory_threshold>5 specs per module</subcategory_threshold>
</module_categories>

<instructions>
  ACTION: Analyze spec to determine appropriate module
  CHECK: Existing module structure and AssetUtilities registry
  ASSIGN: Spec to most logical module or "product" as default
  CONSIDER: Subcategories for modules with >5 specs
  REFERENCE: Cross-repository module patterns from AssetUtilities
</instructions>

</step>

<step number="3" name="enhanced_folder_creation">

### Step 3: Enhanced Module-Based Folder Creation

<step_metadata>
  <creates>
    - directory: specs/modules/<module_name>/<spec_name>/
    - directory: tests/modules/<module_name>/<spec_name>/
    - directory: docs/modules/<module_name>/ (if not exists)
    - directory: src/modules/<module_name>/ (if not exists)
  </creates>
  <ensures>module structure consistency</ensures>
  <cross_repo_templates>@github:assetutilities/templates/module-structure/</cross_repo_templates>
</step_metadata>

<folder_structure>
  <spec_location>specs/modules/<module_name>/<spec_name>/</spec_location>
  <test_location>tests/modules/<module_name>/<spec_name>/</test_location>
  <docs_location>docs/modules/<module_name>/</docs_location>
  <src_location>src/modules/<module_name>/</src_location>
  <naming_convention>
    - spec_name: descriptive, kebab-case, no date prefix
    - module_name: singular noun, kebab-case
    - max_words_spec: 4
    - descriptive: true
  </naming_convention>
</folder_structure>

<instructions>
  ACTION: Create complete module-based folder structure
  FORMAT: Use kebab-case for names, no date prefixes per research
  ENSURE: All four directory types created (specs/docs/src/tests)
  REFERENCE: Use AssetUtilities templates for consistent structure
  VERIFY: Module structure consistency across repository
</instructions>

</step>

<step number="4" name="enhanced_spec_generation">

### Step 4: Enhanced Spec Document Generation

<step_metadata>
  <creates>comprehensive spec with all enhanced features</creates>
  <includes>
    - prompt_summary
    - executive_summary
    - mermaid_diagrams
    - module_context
    - cross_repo_references
  </includes>
  <template_source>@github:assetutilities/templates/enhanced-spec-template.md.j2</template_source>
</step_metadata>

<enhanced_sections>
  <prompt_summary>
    - original_request: verbatim user input
    - context_provided: additional context
    - clarifications_made: refinements during process
    - reuse_notes: guidance for future iterations
  </prompt_summary>
  
  <executive_summary>
    - purpose: high-level goal (1-2 sentences)
    - impact: business value, user benefit, technical advancement
    - scope: effort estimate, timeline, dependencies
    - key_outcomes: primary deliverables
  </executive_summary>
  
  <system_overview>
    - mermaid_diagram: appropriate type for spec (graph, sequence, class, ER)
    - flow_description: step-by-step process
    - integration_points: system connections and dependencies
  </system_overview>
  
  <module_dependencies>
    - required_modules: dependencies with reasons
    - optional_integrations: beneficial connections
    - external_dependencies: outside systems
    - data_flow: visual representation of module interactions
  </module_dependencies>
</enhanced_sections>

<instructions>
  ACTION: Generate comprehensive spec document with all enhanced features
  INCLUDE: All required sections with mermaid diagrams
  REFERENCE: AssetUtilities templates and patterns
  ENSURE: Module context and cross-repo references are clear
  MAINTAIN: Business-focused language in executive summary
</instructions>

</step>

<step number="5" name="task_summary_template_creation">

### Step 5: Task Summary Template Creation

<step_metadata>
  <creates>task_summary.md template for implementation tracking</creates>
  <purpose>Enable comprehensive implementation documentation</purpose>
  <template_source>@github:assetutilities/templates/task-summary-template.md.j2</template_source>
</step_metadata>

<task_summary_sections>
  <executive_summary>
    - implementation_status: completion state
    - key_achievements: deliverables completed
    - business_impact: value delivered, UX improvement, performance impact
  </executive_summary>
  
  <files_changed>
    - new_files_created: complete list with paths
    - existing_files_modified: changes made to existing files
    - configuration_changes: system and project config updates
  </files_changed>
  
  <implementation_logic>
    - architectural_decisions: key choices and rationale
    - key_algorithms: important code patterns or pseudocode
    - integration_patterns: how modules connect and interact
  </implementation_logic>
  
  <existing_references>
    - reused_components: what was leveraged from existing code
    - module_interactions: how this spec integrates with other modules
    - established_patterns: which proven patterns were followed
  </existing_references>
  
  <way_forward>
    - conclusions: key learnings from implementation
    - performance_observations: metrics and improvements
    - suggested_improvements: specific enhancement recommendations
    - next_iteration_opportunities: future development possibilities
  </way_forward>
</task_summary_sections>

<instructions>
  ACTION: Create comprehensive task summary template
  PREPARE: All sections for completion during implementation
  REFERENCE: AssetUtilities patterns for consistency
  NOTE: Template will be filled by execute-tasks workflow
</instructions>

</step>

<step number="6" name="conditional_subspecs_creation">

### Step 6: Enhanced Conditional Sub-Specification Creation

<step_metadata>
  <creates>
    - file: sub-specs/technical-spec.md (always)
    - file: sub-specs/database-schema.md (conditional)
    - file: sub-specs/api-spec.md (conditional)
    - file: sub-specs/cross-repo-spec.md (conditional)
    - file: sub-specs/tests.md (always)
  </creates>
  <enhanced>with module context, mermaid diagrams, and cross-repo references</enhanced>
</step_metadata>

<technical_spec>
  <includes>
    - architecture_overview: class and sequence diagrams
    - implementation_approach: selected approach with rationale
    - module_integration: how spec integrates with other modules
    - cross_repo_dependencies: external system requirements
    - performance_considerations: optimization strategies
    - security_considerations: protection measures
  </includes>
</technical_spec>

<conditional_specs>
  <database_schema>
    - condition: spec requires database changes
    - includes: ER diagrams, schema changes, migration scripts
  </database_schema>
  
  <api_spec>
    - condition: spec requires API changes
    - includes: sequence diagrams, endpoint specifications, integration patterns
  </api_spec>
  
  <cross_repo_spec>
    - condition: spec requires cross-repository integration
    - includes: reference patterns, version management, synchronization
  </cross_repo_spec>
</conditional_specs>

<tests_spec>
  <includes>
    - test_coverage_strategy: visual test pyramid
    - unit_tests: component-level testing
    - integration_tests: module interaction testing
    - e2e_tests: complete workflow testing
    - performance_tests: benchmarking requirements
  </includes>
</tests_spec>

<instructions>
  ACTION: Create appropriate sub-specifications based on spec requirements
  INCLUDE: Module context and mermaid diagrams in all specs
  REFERENCE: AssetUtilities patterns for consistency
  ORGANIZE: Tests by module structure
  ENSURE: Cross-repo integration documented when applicable
</instructions>

</step>

<step number="7" name="cross_repo_reference_establishment">

### Step 7: Cross-Repository Reference Establishment

<step_metadata>
  <establishes>connections to AssetUtilities hub</establishes>
  <updates>local and remote reference registries</updates>
  <validates>cross-repository compatibility</validates>
</step_metadata>

<reference_establishment>
  <local_config>
    - update: .agent-os/cross-repo-config.yml
    - register: new spec in local registry
    - establish: connection to AssetUtilities hub
  </local_config>
  
  <remote_registration>
    - notify: AssetUtilities hub of new spec
    - update: shared module registry
    - validate: compatibility with existing patterns
  </remote_registration>
  
  <version_management>
    - establish: version compatibility requirements
    - create: dependency tracking
    - setup: automatic sync configuration
  </version_management>
</reference_establishment>

<instructions>
  ACTION: Establish comprehensive cross-repository references
  UPDATE: Both local and AssetUtilities registries
  VALIDATE: Compatibility and connection integrity
  SETUP: Automatic synchronization and versioning
</instructions>

</step>

<step number="8" name="ai_persistence_implementation">

### Step 8: AI Persistence Implementation

<step_metadata>
  <implements>multi-level persistence system</implements>
  <levels>system, user, repository, session</levels>
  <ensures>AI context continuity across sessions and systems</ensures>
</step_metadata>

<persistence_levels>
  <system_level>
    - location: ~/.agent-os/system/ or /etc/agent-os/
    - content: global defaults, common modules, template library
    - scope: all users and repositories on system
  </system_level>
  
  <user_level>
    - location: ~/.agent-os/user/
    - content: personal preferences, learning history, custom templates
    - scope: specific user across all repositories
  </user_level>
  
  <repository_level>
    - location: .agent-os/context/
    - content: project context, team patterns, spec history
    - scope: specific repository and team
  </repository_level>
  
  <session_level>
    - location: memory and temporary cache
    - content: current context, active variables, conversation state
    - scope: current AI session
  </session_level>
</persistence_levels>

<context_hierarchy>
  <loading_order>
    1. Load system-level defaults
    2. Override with user preferences
    3. Override with repository context
    4. Enhance with session variables
  </loading_order>
  
  <saving_strategy>
    - immediate: session-level changes
    - on_completion: repository-level updates
    - periodic: user-level learning updates
    - administrative: system-level changes
  </saving_strategy>
</context_hierarchy>

<instructions>
  ACTION: Implement comprehensive AI persistence system
  ESTABLISH: All four persistence levels with proper hierarchy
  ENSURE: Context continuity across sessions, branches, systems, users
  CONFIGURE: Automatic synchronization and conflict resolution
</instructions>

</step>

<step number="9" name="enhanced_user_review">

### Step 9: Enhanced User Review and Validation

<step_metadata>
  <presents>comprehensive spec package for review</presents>
  <includes>all enhanced features and cross-repo references</includes>
  <validates>completeness and accuracy</validates>
</step_metadata>

<review_package>
  <main_documents>
    - enhanced spec.md with all new features
    - task_summary.md template prepared
    - comprehensive sub-specifications
    - cross-repository reference configuration
  </main_documents>
  
  <validation_checklist>
    - prompt summary accuracy
    - executive summary business alignment
    - mermaid diagram correctness
    - module organization appropriateness
    - cross-repo reference validity
    - AI persistence configuration
  </validation_checklist>
</review_package>

<enhanced_features_summary>
  - ✓ Prompt summary for future reuse and iteration
  - ✓ Executive summary with business impact analysis
  - ✓ Multiple mermaid diagrams for visual clarity
  - ✓ Module-based organization with cross-references
  - ✓ Task summary template for implementation tracking
  - ✓ Cross-repository sub-agent referencing
  - ✓ Multi-level AI persistence system
  - ✓ Comprehensive test coverage planning
</enhanced_features_summary>

<instructions>
  ACTION: Present comprehensive review package to user
  HIGHLIGHT: All enhanced features and improvements
  VALIDATE: Completeness and accuracy of all components
  WAIT: For user approval or requested modifications
  REVISE: Make any requested changes before proceeding
</instructions>

</step>

<step number="10" name="enhanced_tasks_creation">

### Step 10: Enhanced Task Creation with Module Context

<step_metadata>
  <creates>comprehensive task breakdown</creates>
  <includes>module setup, implementation, cross-repo integration, completion</includes>
  <depends_on>user approval from step 9</depends_on>
</step_metadata>

<enhanced_task_structure>
  <module_setup_phase>
    - module structure verification
    - cross-repo configuration setup
    - AI persistence initialization
    - template and dependency preparation
  </module_setup_phase>
  
  <implementation_phase>
    - grouped by module components
    - cross-module integration tasks
    - testing at each development level
    - documentation updates throughout
  </implementation_phase>
  
  <integration_phase>
    - AssetUtilities hub integration
    - cross-repository synchronization
    - AI persistence testing and validation
    - performance and compatibility verification
  </integration_phase>
  
  <completion_phase>
    - task_summary.md completion with implementation details
    - comprehensive documentation updates
    - cross-reference validation and updates
    - final testing and user acceptance
  </completion_phase>
</enhanced_task_structure>

<instructions>
  ACTION: Create comprehensive task breakdown with enhanced module context
  STRUCTURE: Four distinct phases with clear dependencies
  INCLUDE: Task summary completion as integral final step
  ORDER: Consider module dependencies and cross-repo integrations
  ENSURE: Full coverage of all enhanced features and requirements
</instructions>

</step>

<step number="11" name="execution_readiness_check">

### Step 11: Enhanced Execution Readiness Check

<step_metadata>
  <evaluates>complete readiness for implementation</step_metadata>
  <includes>all enhanced features and cross-repo setup</includes>
  <prepares>handoff to execute-tasks workflow</prepares>
</step_metadata>

<readiness_validation>
  <spec_completeness>
    - all enhanced sections present and accurate
    - mermaid diagrams appropriate and correct
    - cross-repo references established and validated
    - AI persistence properly configured
  </spec_completeness>
  
  <implementation_preparation>
    - task breakdown comprehensive and ordered
    - dependencies identified and available
    - templates and patterns accessible
    - testing framework prepared
  </implementation_preparation>
  
  <cross_repo_readiness>
    - AssetUtilities hub connection verified
    - shared templates and patterns accessible
    - version compatibility confirmed
    - synchronization mechanisms operational
  </cross_repo_readiness>
</readiness_validation>

<execution_handoff>
  <summary_presentation>
    - module and spec identification
    - executive summary recap
    - enhanced features confirmation
    - first task details and context
    - cross-repo integration status
    - AI persistence readiness
  </summary_presentation>
  
  <handoff_preparation>
    - task_summary.md template ready for completion
    - cross-repo references validated and accessible
    - AI context properly saved and available
    - implementation workflow prepared
  </handoff_preparation>
</execution_handoff>

<instructions>
  ACTION: Validate complete readiness for enhanced implementation
  CONFIRM: All enhanced features properly configured and accessible
  PREPARE: Comprehensive handoff to execute-tasks workflow
  ENSURE: Task summary template and cross-repo references ready
  HIGHLIGHT: Enhanced capabilities and improved organization
</instructions>

</step>

</process_flow>

## Enhanced Execution Standards

<standards>
  <follow>
    - @.agent-os/product/code-style.md
    - @.agent-os/product/dev-best-practices.md
    - @.agent-os/product/tech-stack.md
    - Module-based organization principles
    - Cross-repository sub-agent referencing standards
    - Multi-level AI persistence requirements
  </follow>
  <maintain>
    - Consistency with product mission and roadmap
    - Alignment with established technical patterns
    - Module organization and naming standards
    - Cross-module dependency clarity and management
    - AI context continuity and learning progression
  </maintain>
  <create>
    - Comprehensive documentation with executive summaries and visual diagrams
    - Clear implementation paths with module context and cross-repo integration
    - Testable outcomes organized by module with performance benchmarks
    - Visual diagrams for system understanding and communication
    - Reusable prompt summaries for iteration and improvement
    - Implementation tracking via comprehensive task summaries
    - Cross-repository sharing and reuse capabilities
    - Multi-level AI persistence for continuous improvement
  </create>
</standards>

## Module Improvements Framework

<specs_category>
  1. **Automated Spec Generation:** Template-based spec creation from user prompts with AI pattern recognition
  2. **Dependency Visualization:** Interactive dependency graphs between modules with impact analysis
  3. **Spec Versioning:** Comprehensive version control for spec iterations with change tracking
  4. **Impact Analysis:** Automated analysis of spec changes on dependent modules with risk assessment
  5. **Spec Templates:** Module-specific templates for common patterns with customization options
</specs_category>

<docs_category>
  1. **Auto-Generated API Docs:** Automatic documentation generation from code annotations and OpenAPI specs
  2. **Interactive Diagrams:** Clickable mermaid diagrams with drill-down capability and live updates
  3. **Module Dependency Maps:** Visual representation of module relationships with health monitoring
  4. **Usage Examples:** Automatic generation of usage examples from tests with scenario coverage
  5. **Documentation Validation:** Automated checks for documentation completeness with quality scoring
</docs_category>

<src_category>
  1. **Module Scaffolding:** Automated module structure generation with best-practice templates
  2. **Interface Validation:** Compile-time checks for module interface compliance with standards
  3. **Performance Monitoring:** Built-in performance tracking per module with alerting capabilities
  4. **Code Generation:** Template-based code generation from specs with customization hooks
  5. **Dependency Injection:** Automated dependency management between modules with lifecycle control
</src_category>

<tests_category>
  1. **Test Generation:** Automatic test scaffolding from specs with coverage analysis
  2. **Cross-Module Testing:** Automated integration test discovery with dependency mapping
  3. **Test Coverage Tracking:** Module-level coverage reporting with trend analysis
  4. **Performance Benchmarks:** Automated performance regression testing with baseline management
  5. **Test Data Management:** Shared test data and fixtures across modules with versioning
</tests_category>

## Cross-Repository Integration

<assetutilities_hub>
  <location>https://github.com/[user]/assetutilities.git</location>
  <purpose>Central repository for shared sub-agents, templates, and utilities</purpose>
  <structure>
    - src/modules/agent-os/enhanced-create-specs/
    - templates/spec-templates/
    - templates/module-structure/
    - docs/cross-repo-integration/
    - scripts/setup-cross-repo.sh
  </structure>
</assetutilities_hub>

<reference_patterns>
  <sub_agent_reference>@github:assetutilities/src/modules/agent-os/enhanced-create-specs/</sub_agent_reference>
  <template_reference>@github:assetutilities/templates/enhanced-spec-template.md.j2</template_reference>
  <utility_reference>@github:assetutilities/src/modules/git-utilities/</utility_reference>
</reference_patterns>

<synchronization>
  <automatic_sync>Daily synchronization of shared components</automatic_sync>
  <version_management>Semantic versioning with compatibility checking</version_management>
  <conflict_resolution>Automated merging with manual override capability</conflict_resolution>
</synchronization>

## Final Enhanced Checklist

<verify>
  - [ ] Module identified and complete folder structure created (specs/docs/src/tests)
  - [ ] Original prompt captured verbatim with reuse notes for future iterations
  - [ ] Executive summary created with comprehensive business impact analysis
  - [ ] Multiple mermaid diagrams added for visual clarity and understanding
  - [ ] Enhanced spec.md contains all required sections with module context
  - [ ] All applicable sub-specs created with module context and cross-repo awareness
  - [ ] Task summary template prepared with comprehensive tracking sections
  - [ ] Cross-repository references established and validated with AssetUtilities
  - [ ] Multi-level AI persistence implemented (system/user/repo/session levels)
  - [ ] User reviewed and approved all enhanced documentation and features
  - [ ] Enhanced tasks.md created with module-aware, phased approach
  - [ ] Cross-references updated with comprehensive module and cross-repo paths
  - [ ] Module documentation index updated with new enhanced capabilities
  - [ ] AI context properly saved at all persistence levels for continuity
  - [ ] Enhanced execution readiness confirmed with complete feature validation
</verify>

---

*This enhanced workflow represents a significant evolution of the Agent OS spec creation system, incorporating module-based organization, comprehensive documentation, visual clarity, cross-repository integration, and multi-level AI persistence for improved development workflows across all projects.*