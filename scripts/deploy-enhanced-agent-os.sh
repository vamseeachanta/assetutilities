#!/bin/bash

# Enhanced Agent OS Deployment Script
# Deploys enhanced Agent OS features to all repositories in the github folder
# Version: 1.0.0
# Date: 2025-08-06

set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ASSETUTILITIES_DIR="$(dirname "$SCRIPT_DIR")"
GITHUB_DIR="/mnt/github/github"

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

# Check if AssetUtilities has enhanced features
check_source_files() {
    log_info "Checking source files in AssetUtilities..."
    
    local required_files=(
        ".agent-os/instructions/enhanced-create-spec.md"
        ".agent-os/instructions/enhanced-execute-tasks.md"
        "docs/modules/agent-os/enhanced-create-specs-user-guide.md"
        "docs/modules/agent-os/enhanced-create-specs-setup.md"
        "docs/modules/agent-os/enhanced-create-specs-migration-guide.md"
        "docs/modules/agent-os/enhanced-create-specs-troubleshooting.md"
    )
    
    for file in "${required_files[@]}"; do
        if [[ ! -f "$ASSETUTILITIES_DIR/$file" ]]; then
            log_error "Required file not found: $file"
            return 1
        fi
    done
    
    log_success "All source files found in AssetUtilities"
    return 0
}

# Get list of target repositories
get_target_repositories() {
    local repos=()
    
    for repo_path in "$GITHUB_DIR"/*; do
        if [[ -d "$repo_path" ]] && [[ "$repo_path" != "$ASSETUTILITIES_DIR" ]]; then
            local repo_name=$(basename "$repo_path")
            # Skip system directories
            if [[ "$repo_name" != "."* ]] && [[ "$repo_name" != ".agent-os" ]]; then
                repos+=("$repo_path")
            fi
        fi
    done
    
    printf '%s\n' "${repos[@]}"
}

# Check if repository has Agent OS setup
has_agent_os() {
    local repo_path="$1"
    [[ -d "$repo_path/.agent-os" ]] || [[ -f "$repo_path/CLAUDE.md" ]]
}

# Check if repository has enhanced features
has_enhanced_features() {
    local repo_path="$1"
    [[ -f "$repo_path/.agent-os/instructions/enhanced-create-spec.md" ]]
}

# Deploy enhanced features to a repository
deploy_to_repository() {
    local repo_path="$1"
    local repo_name=$(basename "$repo_path")
    
    log_info "Deploying enhanced Agent OS to $repo_name..."
    
    # Create .agent-os directory if it doesn't exist
    if [[ ! -d "$repo_path/.agent-os" ]]; then
        mkdir -p "$repo_path/.agent-os/instructions"
        log_info "Created .agent-os directory structure"
    fi
    
    # Create instructions directory if it doesn't exist
    mkdir -p "$repo_path/.agent-os/instructions"
    
    # Copy enhanced instruction files
    local instruction_files=(
        "enhanced-create-spec.md"
        "enhanced-execute-tasks.md"
    )
    
    for file in "${instruction_files[@]}"; do
        if cp "$ASSETUTILITIES_DIR/.agent-os/instructions/$file" "$repo_path/.agent-os/instructions/$file"; then
            log_success "Copied $file"
        else
            log_error "Failed to copy $file"
            return 1
        fi
    done
    
    # Create docs directory structure if it doesn't exist
    mkdir -p "$repo_path/docs/modules/agent-os"
    
    # Copy documentation files
    local doc_files=(
        "enhanced-create-specs-user-guide.md"
        "enhanced-create-specs-setup.md"
        "enhanced-create-specs-migration-guide.md"
        "enhanced-create-specs-troubleshooting.md"
    )
    
    for file in "${doc_files[@]}"; do
        if cp "$ASSETUTILITIES_DIR/docs/modules/agent-os/$file" "$repo_path/docs/modules/agent-os/$file"; then
            log_success "Copied $file"
        else
            log_warning "Could not copy documentation file: $file"
        fi
    done
    
    # Update or create CLAUDE.md with enhanced features
    update_claude_md "$repo_path"
    
    log_success "Enhanced Agent OS deployed to $repo_name"
    return 0
}

# Update CLAUDE.md with enhanced features
update_claude_md() {
    local repo_path="$1"
    local claude_file="$repo_path/CLAUDE.md"
    
    # Check if CLAUDE.md exists
    if [[ ! -f "$claude_file" ]]; then
        log_info "Creating new CLAUDE.md file..."
        create_basic_claude_md "$repo_path"
        return 0
    fi
    
    # Check if enhanced features are already documented
    if grep -q "Enhanced Features Available" "$claude_file"; then
        log_info "CLAUDE.md already has enhanced features section"
        return 0
    fi
    
    # Add enhanced features section
    log_info "Adding enhanced features section to existing CLAUDE.md..."
    
    # Create backup
    cp "$claude_file" "$claude_file.backup.$(date +%Y%m%d-%H%M%S)"
    
    # Add enhanced features section before "Important Notes" if it exists
    if grep -q "## Important Notes" "$claude_file"; then
        sed -i '/## Important Notes/i\
## Enhanced Features Available\
\
This project supports enhanced Agent OS workflows including:\
- **Enhanced Spec Creation**: Prompt summaries, executive summaries, mermaid diagrams, module organization\
- **Cross-Repository Integration**: Shared components from AssetUtilities hub (@assetutilities: references)\
- **Enhanced Task Execution**: Task summaries, performance tracking, real-time documentation\
- **Template Variants**: minimal, standard, enhanced, api_focused, research\
- **Visual Documentation**: Auto-generated system architecture and workflow diagrams\
\
### Command Examples\
```bash\
# Enhanced spec creation\
/create-spec feature-name module-name enhanced\
\
# Traditional spec creation (backward compatible)  \
/create-spec feature-name\
\
# Enhanced task execution with summaries\
/execute-tasks @specs/modules/module-name/spec-folder/tasks.md\
```\
\
### Cross-Repository References\
- Shared components: @assetutilities:src/modules/agent-os/enhanced-create-specs/\
- Sub-agent registry: @assetutilities:agents/registry/sub-agents/workflow-automation\
- Hub configuration: @assetutilities:hub-config.yaml\
\
' "$claude_file"
    else
        # Add at the end of the file
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
    fi
    
    log_success "Updated CLAUDE.md with enhanced features"
}

# Create basic CLAUDE.md file
create_basic_claude_md() {
    local repo_path="$1"
    local repo_name=$(basename "$repo_path")
    local claude_file="$repo_path/CLAUDE.md"
    
    cat > "$claude_file" << EOF
# $repo_name Project Instructions

## Enhanced Features Available

This project supports enhanced Agent OS workflows including:
- **Enhanced Spec Creation**: Prompt summaries, executive summaries, mermaid diagrams, module organization
- **Cross-Repository Integration**: Shared components from AssetUtilities hub (@assetutilities: references)
- **Enhanced Task Execution**: Task summaries, performance tracking, real-time documentation
- **Template Variants**: minimal, standard, enhanced, api_focused, research
- **Visual Documentation**: Auto-generated system architecture and workflow diagrams

## Workflow Instructions

When asked to work on this codebase:

1. **First**, check available specs and documentation
2. **Then**, follow the appropriate instruction file:
   - For new features: @.agent-os/instructions/enhanced-create-spec.md (enhanced) or traditional create-spec workflow
   - For tasks execution: @.agent-os/instructions/enhanced-execute-tasks.md (enhanced) or traditional execute-tasks workflow
3. **Always**, adhere to established patterns, code style, and best practices

### Command Examples
\`\`\`bash
# Enhanced spec creation
/create-spec feature-name module-name enhanced

# Traditional spec creation (backward compatible)  
/create-spec feature-name

# Enhanced task execution with summaries
/execute-tasks @specs/modules/module-name/spec-folder/tasks.md
\`\`\`

### Cross-Repository References
- Shared components: @assetutilities:src/modules/agent-os/enhanced-create-specs/
- Sub-agent registry: @assetutilities:agents/registry/sub-agents/workflow-automation
- Hub configuration: @assetutilities:hub-config.yaml

## Important Notes

- Enhanced features are optional and backward compatible
- Traditional Agent OS workflows continue to work unchanged
- Always adhere to established patterns, code style, and best practices documented above
EOF
    
    log_success "Created new CLAUDE.md with enhanced features"
}

# Generate deployment report
generate_report() {
    local total_repos="$1"
    local deployed_repos="$2"
    local skipped_repos="$3"
    local failed_repos="$4"
    
    cat << EOF

=================================================
Enhanced Agent OS Deployment Report
=================================================
Date: $(date)
Total Repositories: $total_repos
Successfully Deployed: $deployed_repos
Skipped (Already Enhanced): $skipped_repos  
Failed Deployments: $failed_repos

Deployment Status: $([[ $failed_repos -eq 0 ]] && echo "SUCCESS" || echo "PARTIAL")

Next Steps:
1. Test enhanced features in deployed repositories
2. Update team documentation about enhanced features availability
3. Train team members on enhanced Agent OS commands
4. Monitor usage and gather feedback

For troubleshooting and user guides, see:
- docs/modules/agent-os/enhanced-create-specs-migration-guide.md
- docs/modules/agent-os/enhanced-create-specs-troubleshooting.md
=================================================
EOF
}

# Main deployment function
main() {
    log_info "Enhanced Agent OS Deployment Script v1.0.0"
    log_info "Deploying to all repositories in $GITHUB_DIR"
    echo
    
    # Check source files
    if ! check_source_files; then
        log_error "Source files validation failed. Aborting deployment."
        exit 1
    fi
    
    # Get target repositories
    local repositories
    mapfile -t repositories < <(get_target_repositories)
    
    if [[ ${#repositories[@]} -eq 0 ]]; then
        log_warning "No target repositories found"
        exit 0
    fi
    
    log_info "Found ${#repositories[@]} target repositories"
    echo
    
    # Deployment statistics
    local total_repos=0
    local deployed_repos=0
    local skipped_repos=0
    local failed_repos=0
    
    # Deploy to each repository
    for repo_path in "${repositories[@]}"; do
        local repo_name=$(basename "$repo_path")
        total_repos=$((total_repos + 1))
        
        echo "----------------------------------------"
        log_info "Processing repository: $repo_name"
        
        # Check if repository already has enhanced features
        if has_enhanced_features "$repo_path"; then
            log_warning "$repo_name already has enhanced features - skipping"
            skipped_repos=$((skipped_repos + 1))
            continue
        fi
        
        # Deploy enhanced features
        if deploy_to_repository "$repo_path"; then
            deployed_repos=$((deployed_repos + 1))
        else
            log_error "Failed to deploy to $repo_name"
            failed_repos=$((failed_repos + 1))
        fi
        echo
    done
    
    # Generate and display report
    generate_report $total_repos $deployed_repos $skipped_repos $failed_repos
    
    # Exit with appropriate code
    if [[ $failed_repos -eq 0 ]]; then
        log_success "Deployment completed successfully!"
        exit 0
    else
        log_error "Deployment completed with $failed_repos failures"
        exit 1
    fi
}

# Run main function if script is executed directly
if [[ "${BASH_SOURCE[0]}" == "${0}" ]]; then
    main "$@"
fi