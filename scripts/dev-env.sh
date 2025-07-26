#!/bin/bash

# AssetUtilities Development Environment Loader
# This script contains the core logic for detecting and loading the project environment
# It's designed to be lightweight and fast for automatic loading

# Core project detection function
detect_assetutilities_project() {
    local current_dir="$PWD"
    local max_depth=10  # Prevent infinite loops
    local depth=0
    
    # Traverse up the directory tree
    while [[ "$current_dir" != "/" ]] && [[ $depth -lt $max_depth ]]; do
        # Check for Git repository first (required)
        if [[ ! -d "$current_dir/.git" ]]; then
            current_dir="$(dirname "$current_dir")"
            ((depth++))
            continue
        fi
        
        # Check for AssetUtilities-specific markers
        local has_setup=false
        local has_pyproject=false
        local has_src_package=false
        local has_assetutilities_name=false
        
        # Check for setup.py
        if [[ -f "$current_dir/setup.py" ]]; then
            has_setup=true
            # Verify it's actually AssetUtilities by checking content
            if grep -q "assetutilities" "$current_dir/setup.py" 2>/dev/null; then
                has_assetutilities_name=true
            fi
        fi
        
        # Check for pyproject.toml
        if [[ -f "$current_dir/pyproject.toml" ]]; then
            has_pyproject=true
            # Verify it's AssetUtilities
            if grep -q "assetutilities" "$current_dir/pyproject.toml" 2>/dev/null; then
                has_assetutilities_name=true
            fi
        fi
        
        # Check for src/assetutilities package structure
        if [[ -d "$current_dir/src/assetutilities" ]]; then
            has_src_package=true
            has_assetutilities_name=true
        fi
        
        # Check directory name as additional hint
        local dir_name
        dir_name=$(basename "$current_dir")
        if [[ "$dir_name" == "assetutilities" ]] || [[ "$dir_name" == "AssetUtilities" ]]; then
            has_assetutilities_name=true
        fi
        
        # Must have at least one project file AND AssetUtilities identifier
        if ($has_setup || $has_pyproject || $has_src_package) && $has_assetutilities_name; then
            echo "$current_dir"
            return 0
        fi
        
        current_dir="$(dirname "$current_dir")"
        ((depth++))
    done
    
    return 1
}

# Fast project detection for prompt integration
is_in_assetutilities_project() {
    local project_root
    project_root=$(detect_assetutilities_project 2>/dev/null)
    [[ -n "$project_root" ]]
}

# Load project environment if detected
load_project_environment() {
    local project_root
    project_root=$(detect_assetutilities_project 2>/dev/null)
    
    if [[ -n "$project_root" ]]; then
        export ASSETUTILITIES_ROOT="$project_root"
        
        # Load main project configuration
        if [[ -f "$project_root/config/.project-bashrc" ]]; then
            source "$project_root/config/.project-bashrc"
            return 0
        fi
    fi
    
    return 1
}

# Clean up project environment
unload_project_environment() {
    if [[ -n "$ASSETUTILITIES_ROOT" ]] && command -v au_cleanup &> /dev/null; then
        au_cleanup
    fi
    
    unset ASSETUTILITIES_ROOT
}

# Validate project structure (for setup script)
validate_project_structure() {
    local project_root="$1"
    
    if [[ -z "$project_root" ]] || [[ ! -d "$project_root" ]]; then
        return 1
    fi
    
    # Check required directories and files
    local required_checks=(
        "$project_root/.git"
    )
    
    # At least one of these must exist
    local optional_checks=(
        "$project_root/setup.py"
        "$project_root/pyproject.toml" 
        "$project_root/src/assetutilities"
    )
    
    # Check required items
    for check in "${required_checks[@]}"; do
        if [[ ! -e "$check" ]]; then
            return 1
        fi
    done
    
    # Check at least one optional item exists
    local found_optional=false
    for check in "${optional_checks[@]}"; do
        if [[ -e "$check" ]]; then
            found_optional=true
            break
        fi
    done
    
    $found_optional
}

# Get project information
get_project_info() {
    local project_root
    project_root=$(detect_assetutilities_project 2>/dev/null)
    
    if [[ -z "$project_root" ]]; then
        echo "Not in AssetUtilities project"
        return 1
    fi
    
    echo "Project Root: $project_root"
    
    # Get Git information
    if [[ -d "$project_root/.git" ]]; then
        cd "$project_root" || return 1
        local branch
        branch=$(git rev-parse --abbrev-ref HEAD 2>/dev/null)
        echo "Git Branch: ${branch:-unknown}"
        
        local status
        status=$(git status --porcelain 2>/dev/null | wc -l)
        echo "Changed Files: $status"
    fi
    
    # Get Python information if available
    if command -v python &> /dev/null; then
        local python_version
        python_version=$(python --version 2>&1)
        echo "Python: $python_version"
    fi
    
    # Virtual environment status
    if [[ -n "$VIRTUAL_ENV" ]]; then
        echo "Virtual Env: $(basename "$VIRTUAL_ENV")"
    else
        echo "Virtual Env: None"
    fi
}

# Performance optimized detection for frequent calls
# Uses caching to avoid repeated file system checks
declare -g _AU_PROJECT_ROOT_CACHE=""
declare -g _AU_LAST_PWD=""

cached_detect_project() {
    # If we're in the same directory as last time, use cache
    if [[ "$PWD" == "$_AU_LAST_PWD" ]] && [[ -n "$_AU_PROJECT_ROOT_CACHE" ]]; then
        echo "$_AU_PROJECT_ROOT_CACHE"
        return 0
    fi
    
    # Clear cache if we changed directories
    if [[ "$PWD" != "$_AU_LAST_PWD" ]]; then
        _AU_PROJECT_ROOT_CACHE=""
        _AU_LAST_PWD="$PWD"
    fi
    
    # Detect project and cache result
    local project_root
    project_root=$(detect_assetutilities_project 2>/dev/null)
    
    if [[ -n "$project_root" ]]; then
        _AU_PROJECT_ROOT_CACHE="$project_root"
        echo "$project_root"
        return 0
    fi
    
    return 1
}

# Export functions for use in other scripts
export -f detect_assetutilities_project
export -f is_in_assetutilities_project
export -f load_project_environment
export -f unload_project_environment
export -f validate_project_structure
export -f get_project_info
export -f cached_detect_project