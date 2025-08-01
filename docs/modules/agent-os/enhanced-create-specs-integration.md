# Enhanced Create-Specs Integration Guide

> **Module:** agent-os
> **Purpose:** Integration guide for enhanced create-specs workflow across repositories
> **AI Context:** Complete setup and usage instructions for enhanced spec creation system

This document provides comprehensive integration instructions for the enhanced create-specs workflow system.

## Overview

The enhanced create-specs system provides:
- **Module-based organization** for better scalability and maintainability
- **Cross-repository referencing** for shared sub-agents and utilities
- **Multi-level AI persistence* for context continuity
- **Enhanced documentation** with executive summaries and mermaid diagrams
- **Comprehensive task tracking** with implementation summaries

## Repository Setup

### 1. AssetUtilities Hub Configuration

The AssetUtilities repository serves as the central hub for shared components:

```bash
# Clone or navigate to assetutilities repository
git clone https://github.com/[user]/assetutilities.git
cd assetutilities

# Verify enhanced create-specs module exists
ls -la specs/modules/agent-os/enhanced-create-specs/
ls -la src/modules/agent-os/enhanced-create-specs/
```

### 2. Target Repository Setup

For each repository that will use the enhanced workflow:

```bash
# Create .agent-os directory structure
mkdir -p .agent-os/context
mkdir -p .agent-os/cache
mkdir -p .agent-os/templates

# Create cross-repository configuration
cat > .agent-os/cross-repo-config.yml << EOF
cross_repo:
  hub_repository: "https://github.com/[user]/assetutilities.git"
  sub_agents:
    - agent-os/enhanced-create-specs
  sync_interval: "daily"
  cache_location: ".agent-os/cache/"
  
shared_components:
  assetutilities:
    current_version: "main"
    last_sync: "$(date -Iseconds)"
    compatibility: ">=1.0.0"
EOF

# Create module-based directory structure
mkdir -p specs/modules
mkdir -p docs/modules
mkdir -p src/modules
mkdir -p tests/modules
```

### 3. AI Persistence Setup

#### System Level (One-time setup per system)
```bash
# Create system-level configuration
mkdir -p ~/.agent-os/system
cat > ~/.agent-os/system/config.yml << EOF
version: "1.0.0"
global_defaults:
  default_module: "product"
  spec_naming_convention: "kebab-case"
  date_format: "YYYY-MM-DD"

common_modules:
  - authentication
  - authorization
  - user-management
  - data-management
  - api
  - ui-ux
  - reporting
  - notifications
  - payment
  - admin
  - agent-os

cross_repo_settings:
  default_hub: "https://github.com/[user]/assetutilities.git"
  sync_frequency: "daily"
  cache_duration: "7d"
EOF
```

#### User Level (One-time setup per user)
```bash
# Create user-level preferences
mkdir -p ~/.agent-os/user
cat > ~/.agent-os/user/preferences.yml << EOF
user_info:
  name: "Your Name"
  email: "your.email@example.com"
  timezone: "UTC-05:00"

preferred_settings:
  default_modules:
    - authentication
    - user-management
    - api
  
  documentation_preferences:
    diagram_type: "mermaid"
    detail_level: "medium"
    include_examples: true

project_history: []
learning_patterns:
  successful_specs: []
  common_mistakes: []
  preferred_patterns: {}
EOF
```

## Usage Instructions

### 1. Basic Enhanced Spec Creation

Instead of the standard `/create-specs`, use the enhanced workflow:

```markdown
@github:assetutilities/src/modules/agent-os/enhanced-create-specs/enhanced_create_specs_workflow.md

Create a new user authentication system with the following requirements:
- Secure login and signup
- Password reset functionality  
- User profile management
- Integration with existing database
```

### 2. Module-Specific Spec Creation

For specs targeting specific modules:

```markdown
@github:assetutilities/src/modules/agent-os/enhanced-create-specs/enhanced_create_specs_workflow.md

Create API rate limiting system for the api module:
- Request throttling by user and IP
- Configurable rate limits
- Real-time monitoring dashboard
- Integration with existing API infrastructure
```

### 3. Cross-Repository Sub-Agent Usage

Reference shared utilities from other repositories:

```markdown
<!-- In any repository's CLAUDE.md -->
## Enhanced Spec Creation

For creating new specs, use the enhanced workflow:
- **Enhanced Spec Creation:** @github:assetutilities/src/modules/agent-os/enhanced-create-specs/enhanced_create_specs_workflow.md
- **Git Utilities:** @github:assetutilities/src/modules/git-utilities/
- **File Management:** @github:assetutilities/src/modules/file-management/
```

## Generated Structure

The enhanced workflow creates the following structure:

```
repository/
├── specs/modules/<module_name>/<spec_name>/
│   ├── spec.md                    # Enhanced with all new features
│   ├── task_summary.md           # Implementation tracking template
│   └── sub-specs/
│       ├── technical-spec.md     # Comprehensive technical details
│       ├── api-spec.md          # API specifications (conditional)
│       ├── database-schema.md   # Database changes (conditional)
│       ├── cross-repo-spec.md   # Cross-repo integration (conditional)
│       └── tests.md             # Complete test coverage plan
├── docs/modules/<module_name>/
│   ├── index.md                 # Module documentation index
│   └── [module-specific docs]
├── src/modules/<module_name>/
│   └── [implementation files]
├── tests/modules/<module_name>/<spec_name>/
│   ├── unit/
│   ├── integration/
│   └── e2e/
└── .agent-os/
    ├── context/
    │   ├── project_context.yml
    │   └── team_knowledge.yml
    ├── cross-repo-config.yml
    └── cache/
```

## Enhanced Features

### 1. Prompt Summary
Every spec includes a comprehensive prompt summary:
- Original user request (verbatim)
- Context provided during creation
- Clarifications made during the process
- Reuse notes for future iterations

### 2. Executive Summary
Business-focused summary including:
- High-level purpose and goals
- Business value and user benefits
- Technical advancement and impact
- Effort estimates and timeline
- Key outcomes and deliverables

### 3. Mermaid Diagrams
Visual representations including:
- System overview diagrams
- Data flow diagrams
- Module dependency maps
- Technical architecture diagrams
- Test coverage visualization

### 4. Task Summary System
Implementation tracking with:
- Executive summary of what was built
- Complete list of files changed
- Implementation logic and decisions
- References to existing work leveraged
- Way forward with conclusions and improvements

## Cross-Repository Integration

### Reference Patterns

1. **Direct Reference:**
   ```markdown
   @github:assetutilities/src/modules/agent-os/enhanced-create-specs/
   ```

2. **Template Reference:**
   ```yaml
   template_source: "@github:assetutilities/templates/enhanced-spec-template.md.j2"
   ```

3. **Utility Reference:**
   ```python
   from agent_os.cross_repo import load_shared_module
   create_specs = load_shared_module('assetutilities', 'agent-os.enhanced-create-specs')
   ```

### Synchronization

The system automatically synchronizes shared components:

```bash
# Manual sync (if needed)
cd .agent-os
git submodule update --remote --recursive
python validate_references.py
```

## AI Persistence Benefits

### Continuous Learning
- AI agents remember successful patterns across sessions
- Common mistakes are tracked and avoided
- User preferences are learned and applied
- Project context is maintained across development cycles

### Context Continuity
- System-level: Global defaults and common patterns
- User-level: Personal preferences and learning history
- Repository-level: Project context and team patterns
- Session-level: Current conversation and active variables

### Cross-System Consistency
- Same AI behavior across different machines
- Team members share consistent patterns
- Project knowledge accumulates over time
- Specifications improve through iteration

## Troubleshooting

### Common Issues

1. **Cross-Repository Access Issues:**
   ```bash
   # Verify git access to assetutilities
   git ls-remote https://github.com/[user]/assetutilities.git
   
   # Update submodule if needed
   git submodule update --init --recursive
   ```

2. **Module Identification Problems:**
   - Check ~/.agent-os/system/config.yml for common modules
   - Verify module naming follows kebab-case convention
   - Ensure module has fewer than 5 specs (or create subcategory)

3. **Template Not Found:**
   ```bash
   # Verify assetutilities templates exist
   ls -la .agent-os/shared/templates/
   
   # Re-sync if needed
   cd .agent-os && git submodule update --remote
   ```

4. **AI Persistence Not Working:**
   - Check file permissions on ~/.agent-os/ directories
   - Verify YAML syntax in configuration files
   - Ensure sufficient disk space for cache files

### Support and Updates

For issues or enhancement requests:
1. Check the AssetUtilities repository issues
2. Review the enhanced-create-specs specification
3. Consult the cross-repository integration documentation
4. Contact the development team through established channels

## Migration from Standard Workflow

### Existing Repositories

To migrate existing repositories to the enhanced workflow:

1. **Backup Current Specs:**
   ```bash
   cp -r .agent-os/specs .agent-os/specs.backup
   ```

2. **Setup Enhanced Structure:**
   ```bash
   # Run setup commands from "Repository Setup" section above
   ```

3. **Migrate Existing Specs (Optional):**
   ```bash
   # Create migration script or manually reorganize
   # Move specs from .agent-os/specs/YYYY-MM-DD-spec-name/
   # To specs/modules/<module-name>/<spec-name>/
   ```

4. **Update CLAUDE.md:**
   ```markdown
   ## Enhanced Spec Creation
   
   Use the enhanced workflow for all new specs:
   @github:assetutilities/src/modules/agent-os/enhanced-create-specs/enhanced_create_specs_workflow.md
   ```

### Team Onboarding

For new team members:
1. Complete "System Level" and "User Level" setup
2. Clone repositories with enhanced structure
3. Review generated example specs
4. Practice with simple spec creation
5. Gradually adopt advanced features

---

*This integration guide ensures consistent adoption of the enhanced create-specs workflow across all repositories and team members, providing improved organization, documentation quality, and development efficiency.*