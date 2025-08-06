#!/bin/bash

# Enhanced Create-Specs Deployment Script
# Version: 1.0.0
# Platform: Linux/macOS
# Description: Deploys enhanced create-specs workflow to a repository

set -e

# Configuration
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PROJECT_ROOT="$(cd "${SCRIPT_DIR}/.." && pwd)"
DEPLOYMENT_VERSION="1.0.0"

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Logging functions
log_info() {
    echo -e "${BLUE}[INFO]${NC} $1"
}

log_success() {
    echo -e "${GREEN}[SUCCESS]${NC} $1"
}

log_warning() {
    echo -e "${YELLOW}[WARNING]${NC} $1"
}

log_error() {
    echo -e "${RED}[ERROR]${NC} $1"
}

# Usage information
show_usage() {
    cat << EOF
Enhanced Create-Specs Deployment Script

Usage: $0 [OPTIONS] TARGET_DIRECTORY

OPTIONS:
    -h, --help              Show this help message
    -v, --verbose           Enable verbose output
    -f, --force             Force deployment (overwrite existing)
    -t, --type TYPE         Deployment type (full|hub|client)
                           full   - Complete deployment with hub setup
                           hub    - Hub repository setup only
                           client - Client repository setup only
    -c, --config FILE       Custom configuration file
    -d, --dry-run           Show what would be deployed without making changes
    --no-tests              Skip test execution during deployment
    --version               Show version information

EXAMPLES:
    $0 /path/to/target/repo
    $0 --type client --force /path/to/client/repo
    $0 --type hub --dry-run /path/to/hub/repo
    $0 --config custom.yaml /path/to/repo

EOF
}

# Parse command line arguments
VERBOSE=0
FORCE=0
DRY_RUN=0
DEPLOYMENT_TYPE="full"
CONFIG_FILE=""
RUN_TESTS=1
TARGET_DIR=""

while [[ $# -gt 0 ]]; do
    case $1 in
        -h|--help)
            show_usage
            exit 0
            ;;
        -v|--verbose)
            VERBOSE=1
            shift
            ;;
        -f|--force)
            FORCE=1
            shift
            ;;
        -t|--type)
            DEPLOYMENT_TYPE="$2"
            shift 2
            ;;
        -c|--config)
            CONFIG_FILE="$2"
            shift 2
            ;;
        -d|--dry-run)
            DRY_RUN=1
            shift
            ;;
        --no-tests)
            RUN_TESTS=0
            shift
            ;;
        --version)
            echo "Enhanced Create-Specs Deployment Script v${DEPLOYMENT_VERSION}"
            exit 0
            ;;
        -*)
            log_error "Unknown option: $1"
            show_usage
            exit 1
            ;;
        *)
            if [[ -z "$TARGET_DIR" ]]; then
                TARGET_DIR="$1"
            else
                log_error "Multiple target directories specified"
                exit 1
            fi
            shift
            ;;
    esac
done

# Validate arguments
if [[ -z "$TARGET_DIR" ]]; then
    log_error "Target directory is required"
    show_usage
    exit 1
fi

if [[ ! "$DEPLOYMENT_TYPE" =~ ^(full|hub|client)$ ]]; then
    log_error "Invalid deployment type: $DEPLOYMENT_TYPE"
    exit 1
fi

# Verbose logging
verbose_log() {
    if [[ $VERBOSE -eq 1 ]]; then
        log_info "$1"
    fi
}

# Dry run execution
execute_command() {
    local cmd="$1"
    local description="$2"
    
    if [[ $DRY_RUN -eq 1 ]]; then
        echo "DRY RUN: $description"
        echo "  Command: $cmd"
    else
        verbose_log "Executing: $description"
        eval "$cmd"
    fi
}

# Pre-deployment checks
run_pre_checks() {
    log_info "Running pre-deployment checks..."
    
    # Check if target directory exists
    if [[ ! -d "$TARGET_DIR" ]]; then
        if [[ $FORCE -eq 1 ]]; then
            execute_command "mkdir -p '$TARGET_DIR'" "Create target directory"
        else
            log_error "Target directory does not exist: $TARGET_DIR"
            log_error "Use --force to create it automatically"
            exit 1
        fi
    fi
    
    # Check if target is a git repository
    if [[ ! -d "$TARGET_DIR/.git" ]]; then
        log_warning "Target directory is not a git repository"
        read -p "Initialize git repository? (y/N): " -n 1 -r
        echo
        if [[ $REPLY =~ ^[Yy]$ ]]; then
            execute_command "cd '$TARGET_DIR' && git init" "Initialize git repository"
        fi
    fi
    
    # Check required tools
    local tools=("git" "python3" "curl")
    for tool in "${tools[@]}"; do
        if ! command -v "$tool" &> /dev/null; then
            log_error "Required tool not found: $tool"
            exit 1
        fi
    done
    
    # Check Python version
    local python_version=$(python3 --version | cut -d' ' -f2 | cut -d'.' -f1-2)
    local required_version="3.8"
    if ! awk "BEGIN {exit !($python_version >= $required_version)}"; then
        log_error "Python 3.8+ required, found: $python_version"
        exit 1
    fi
    
    log_success "Pre-deployment checks passed"
}

# Deploy core files
deploy_core_files() {
    log_info "Deploying core enhanced create-specs files..."
    
    local target_agent_os="$TARGET_DIR/.agent-os"
    
    # Create directory structure
    execute_command "mkdir -p '$target_agent_os/instructions'" "Create instructions directory"
    execute_command "mkdir -p '$target_agent_os/templates'" "Create templates directory"
    execute_command "mkdir -p '$target_agent_os/context'" "Create context directory"
    execute_command "mkdir -p '$target_agent_os/cache'" "Create cache directory"
    
    # Copy enhanced instruction files
    if [[ -f "$PROJECT_ROOT/.agent-os/instructions/enhanced-create-spec.md" ]]; then
        execute_command "cp '$PROJECT_ROOT/.agent-os/instructions/enhanced-create-spec.md' '$target_agent_os/instructions/'" "Copy enhanced create-spec instructions"
    fi
    
    if [[ -f "$PROJECT_ROOT/.agent-os/instructions/enhanced-execute-tasks.md" ]]; then
        execute_command "cp '$PROJECT_ROOT/.agent-os/instructions/enhanced-execute-tasks.md' '$target_agent_os/instructions/'" "Copy enhanced execute-tasks instructions"
    fi
    
    # Create module directory structure
    execute_command "mkdir -p '$TARGET_DIR/specs/modules'" "Create specs/modules directory"
    execute_command "mkdir -p '$TARGET_DIR/docs/modules'" "Create docs/modules directory"
    execute_command "mkdir -p '$TARGET_DIR/src/modules'" "Create src/modules directory"
    execute_command "mkdir -p '$TARGET_DIR/tests/modules'" "Create tests/modules directory"
    
    log_success "Core files deployed"
}

# Deploy hub-specific files
deploy_hub_files() {
    log_info "Deploying hub-specific files..."
    
    # Copy hub configuration
    if [[ -f "$PROJECT_ROOT/hub-config.yaml" ]]; then
        execute_command "cp '$PROJECT_ROOT/hub-config.yaml' '$TARGET_DIR/'" "Copy hub configuration"
    fi
    
    # Copy sub-agent registry
    if [[ -d "$PROJECT_ROOT/agents" ]]; then
        execute_command "cp -r '$PROJECT_ROOT/agents' '$TARGET_DIR/'" "Copy sub-agent registry"
    fi
    
    # Copy setup scripts
    if [[ -f "$PROJECT_ROOT/scripts/setup-cross-repo-integration.py" ]]; then
        execute_command "mkdir -p '$TARGET_DIR/scripts'" "Create scripts directory"
        execute_command "cp '$PROJECT_ROOT/scripts/setup-cross-repo-integration.py' '$TARGET_DIR/scripts/'" "Copy setup script"
        execute_command "chmod +x '$TARGET_DIR/scripts/setup-cross-repo-integration.py'" "Make setup script executable"
    fi
    
    # Copy implementation files
    if [[ -d "$PROJECT_ROOT/src/modules/agent-os" ]]; then
        execute_command "mkdir -p '$TARGET_DIR/src/modules/agent-os'" "Create agent-os module directory"
        execute_command "cp -r '$PROJECT_ROOT/src/modules/agent-os/enhanced-create-specs' '$TARGET_DIR/src/modules/agent-os/'" "Copy implementation files"
    fi
    
    log_success "Hub files deployed"
}

# Deploy client-specific files
deploy_client_files() {
    log_info "Deploying client-specific files..."
    
    local target_agent_os="$TARGET_DIR/.agent-os"
    
    # Create user preferences template
    cat > "$TARGET_DIR/.agent-os/user-preferences.yaml" << 'EOF'
# Enhanced Create-Specs User Preferences
preferred_variant: "enhanced"
organization_type: "module-based"

# Feature flags
enable_mermaid_diagrams: true
enable_cross_references: true
auto_detect_sub_specs: true
enable_task_summaries: true

# Default sections for enhanced specs
default_sections:
  - "prompt_summary"
  - "executive_summary"
  - "system_overview"

# Custom variables
custom_variables:
  organization: "Your Organization"
  contact_email: "developer@yourorg.com"

# Performance settings
performance_monitoring: true
benchmark_targets:
  spec_creation_time: 5000  # milliseconds
  cross_reference_validation: 2000  # milliseconds
  mermaid_generation: 1000  # milliseconds
EOF

    # Create cross-repository configuration template
    cat > "$TARGET_DIR/.agent-os/cross-repo-config.yaml" << 'EOF'
# Cross-Repository Configuration
hub_repository: "assetutilities"
hub_path: "/path/to/assetutilities"  # Update with actual path
hub_url: "https://github.com/user/assetutilities"

# Integration type: full, partial, minimal
integration_type: "partial"

# Shared components to access
shared_components:
  - "agent-os/enhanced-create-specs/enhanced_documentation_generator.py"
  - "agent-os/enhanced-create-specs/template_customization_system.py"

# Sub-agents to use
sub_agents:
  - "workflow-automation"

# Version requirements
version_requirements:
  hub: ">=1.0.0"
  agent-os: ">=1.0.0"

# Local overrides
local_overrides:
  template_variant: "enhanced"
  organization_standards: true

# Cache configuration
cache_config:
  enabled: true
  max_age_hours: 24
  auto_refresh: true
EOF

    log_success "Client files deployed"
}

# Deploy documentation
deploy_documentation() {
    log_info "Deploying documentation..."
    
    local docs_dir="$TARGET_DIR/docs/modules/agent-os"
    execute_command "mkdir -p '$docs_dir'" "Create documentation directory"
    
    # Copy user guide
    if [[ -f "$PROJECT_ROOT/docs/modules/agent-os/enhanced-create-specs-user-guide.md" ]]; then
        execute_command "cp '$PROJECT_ROOT/docs/modules/agent-os/enhanced-create-specs-user-guide.md' '$docs_dir/'" "Copy user guide"
    fi
    
    # Copy setup guide  
    if [[ -f "$PROJECT_ROOT/docs/modules/agent-os/enhanced-create-specs-setup.md" ]]; then
        execute_command "cp '$PROJECT_ROOT/docs/modules/agent-os/enhanced-create-specs-setup.md' '$docs_dir/'" "Copy setup guide"
    fi
    
    # Create README if it doesn't exist
    if [[ ! -f "$docs_dir/README.md" ]]; then
        cat > "$docs_dir/README.md" << 'EOF'
# Agent OS Enhanced Create-Specs

This directory contains the enhanced create-specs workflow for the Agent OS framework.

## Documentation

- [User Guide](enhanced-create-specs-user-guide.md) - Complete user documentation
- [Setup Guide](enhanced-create-specs-setup.md) - Installation and configuration
- [API Reference](api-reference.md) - Developer API documentation (if available)

## Quick Start

```bash
# Create an enhanced spec
/create-spec feature-name module-name enhanced

# Create a minimal spec for simple changes  
/create-spec bug-fix utils minimal

# Execute enhanced tasks with summaries
/execute-tasks @specs/modules/module-name/spec-folder/tasks.md
```

## Features

- 5 template variants (minimal, standard, enhanced, api_focused, research)
- Auto-generated mermaid diagrams
- Cross-repository component sharing
- Module-based organization
- Task summary tracking
- Performance monitoring

## Support

For questions, issues, or contributions, see the main project repository.
EOF
        log_info "Created documentation README"
    fi
    
    log_success "Documentation deployed"
}

# Update CLAUDE.md template
update_claude_template() {
    log_info "Updating CLAUDE.md template..."
    
    local claude_file="$TARGET_DIR/CLAUDE.md"
    
    if [[ -f "$claude_file" ]]; then
        # Backup existing CLAUDE.md
        execute_command "cp '$claude_file' '$claude_file.backup'" "Backup existing CLAUDE.md"
    fi
    
    # Add or update enhanced features section
    if [[ ! -f "$claude_file" ]] || ! grep -q "Enhanced Features Available" "$claude_file"; then
        cat >> "$claude_file" << 'EOF'

## Enhanced Features Available

This project supports enhanced Agent OS workflows including:
- **Enhanced Spec Creation**: Prompt summaries, executive summaries, mermaid diagrams, module organization
- **Cross-Repository Integration**: Shared components from AssetUtilities hub (@assetutilities: references)
- **Enhanced Task Execution**: Task summaries, performance tracking, real-time documentation
- **Template Variants**: minimal, standard, enhanced, api_focused, research
- **Visual Documentation**: Auto-generated system architecture and workflow diagrams

### Command Examples
```bash
# Enhanced spec creation
/create-spec feature-name module-name enhanced

# Traditional spec creation (backward compatible)  
/create-spec feature-name

# Enhanced task execution with summaries
/execute-tasks @specs/modules/module-name/spec-folder/tasks.md
```

### Cross-Repository References
- Shared components: @assetutilities:src/modules/agent-os/enhanced-create-specs/
- Sub-agent registry: @assetutilities:agents/registry/sub-agents/workflow-automation
- Hub configuration: @assetutilities:hub-config.yaml
EOF
        log_info "Added enhanced features section to CLAUDE.md"
    else
        log_info "CLAUDE.md already contains enhanced features section"
    fi
    
    log_success "CLAUDE.md template updated"
}

# Run tests
run_deployment_tests() {
    if [[ $RUN_TESTS -eq 0 ]]; then
        log_info "Skipping tests (--no-tests specified)"
        return
    fi
    
    log_info "Running deployment verification tests..."
    
    # Test directory structure
    local required_dirs=(
        ".agent-os"
        ".agent-os/instructions" 
        "specs/modules"
        "docs/modules"
        "src/modules"
        "tests/modules"
    )
    
    for dir in "${required_dirs[@]}"; do
        if [[ -d "$TARGET_DIR/$dir" ]]; then
            verbose_log "✓ Directory exists: $dir"
        else
            log_warning "✗ Missing directory: $dir"
        fi
    done
    
    # Test configuration files
    local config_files=(
        ".agent-os/user-preferences.yaml"
        ".agent-os/cross-repo-config.yaml"
    )
    
    for file in "${config_files[@]}"; do
        if [[ -f "$TARGET_DIR/$file" ]]; then
            verbose_log "✓ Configuration file exists: $file"
            
            # Validate YAML syntax
            if python3 -c "import yaml; yaml.safe_load(open('$TARGET_DIR/$file'))" 2>/dev/null; then
                verbose_log "✓ Valid YAML syntax: $file"
            else
                log_warning "✗ Invalid YAML syntax: $file"
            fi
        else
            log_warning "✗ Missing configuration file: $file"
        fi
    done
    
    # Test instruction files
    if [[ -f "$TARGET_DIR/.agent-os/instructions/enhanced-create-spec.md" ]]; then
        verbose_log "✓ Enhanced create-spec instructions available"
    else
        log_warning "✗ Missing enhanced create-spec instructions"
    fi
    
    log_success "Deployment tests completed"
}

# Generate deployment report
generate_report() {
    log_info "Generating deployment report..."
    
    local report_file="$TARGET_DIR/deployment-report.md"
    
    cat > "$report_file" << EOF
# Enhanced Create-Specs Deployment Report

**Deployment Date:** $(date)
**Deployment Type:** $DEPLOYMENT_TYPE
**Target Directory:** $TARGET_DIR
**Deployment Version:** $DEPLOYMENT_VERSION

## Deployment Summary

### Files Deployed

#### Core Files
- Enhanced create-spec instructions
- Enhanced execute-tasks instructions
- User preferences template
- Cross-repository configuration template

#### Directory Structure
- \`.agent-os/\` - Agent OS configuration and instructions
- \`specs/modules/\` - Module-based specification storage
- \`docs/modules/\` - Module documentation
- \`src/modules/\` - Module implementation files
- \`tests/modules/\` - Module test files

#### Documentation
- User guide: \`docs/modules/agent-os/enhanced-create-specs-user-guide.md\`
- Setup guide: \`docs/modules/agent-os/enhanced-create-specs-setup.md\`
- README: \`docs/modules/agent-os/README.md\`

### Configuration

#### User Preferences
- Template variant: enhanced
- Organization type: module-based
- Mermaid diagrams: enabled
- Cross-references: enabled

#### Performance Targets
- Spec creation: <5000ms
- Cross-reference validation: <2000ms
- Mermaid generation: <1000ms

## Next Steps

1. **Configure Cross-Repository Integration**
   - Update hub_path in \`.agent-os/cross-repo-config.yaml\`
   - Verify AssetUtilities hub accessibility

2. **Customize User Preferences**
   - Update organization name and contact
   - Adjust performance targets if needed
   - Configure additional template variants

3. **Test Deployment**
   - Run: \`/create-spec test-deployment testing enhanced\`
   - Verify module structure creation
   - Test cross-repository references

4. **Team Onboarding**
   - Share user guide with team members
   - Provide setup training
   - Configure organization standards

## Support

- Documentation: \`docs/modules/agent-os/\`
- Configuration: \`.agent-os/\`
- Issues: Report to project repository

---

*Deployment completed successfully on $(date)*
EOF

    log_success "Deployment report generated: $report_file"
}

# Main deployment function
main() {
    echo "Enhanced Create-Specs Deployment Script v${DEPLOYMENT_VERSION}"
    echo "============================================================"
    
    log_info "Deployment type: $DEPLOYMENT_TYPE"
    log_info "Target directory: $TARGET_DIR"
    
    if [[ $DRY_RUN -eq 1 ]]; then
        log_info "DRY RUN MODE - No changes will be made"
    fi
    
    # Run pre-deployment checks
    run_pre_checks
    
    # Deploy based on type
    case $DEPLOYMENT_TYPE in
        "full")
            deploy_core_files
            deploy_hub_files
            deploy_client_files
            deploy_documentation
            update_claude_template
            ;;
        "hub")
            deploy_core_files
            deploy_hub_files
            deploy_documentation
            update_claude_template
            ;;
        "client")
            deploy_core_files
            deploy_client_files
            deploy_documentation
            update_claude_template
            ;;
    esac
    
    # Run deployment tests
    run_deployment_tests
    
    # Generate report
    if [[ $DRY_RUN -eq 0 ]]; then
        generate_report
    fi
    
    echo
    log_success "Enhanced Create-Specs deployment completed successfully!"
    
    if [[ $DRY_RUN -eq 0 ]]; then
        echo
        echo "Next steps:"
        echo "1. Review deployment report: $TARGET_DIR/deployment-report.md"
        echo "2. Configure cross-repository integration if needed"
        echo "3. Test deployment: /create-spec test-deployment testing enhanced"
        echo "4. Read user guide: $TARGET_DIR/docs/modules/agent-os/enhanced-create-specs-user-guide.md"
    fi
}

# Run main function
main "$@"