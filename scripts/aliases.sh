#!/bin/bash

# AssetUtilities Development Aliases
# Project-specific command shortcuts and aliases

# Ensure we're in the AssetUtilities project
if [[ -z "$ASSETUTILITIES_ROOT" ]]; then
    return 1
fi

# Navigation aliases
alias auroot='cd "$ASSETUTILITIES_ROOT"'
alias ausrc='cd "$ASSETUTILITIES_ROOT/src"'
alias autest='cd "$ASSETUTILITIES_ROOT/tests"'
alias audoc='cd "$ASSETUTILITIES_ROOT/docs"'
alias auscript='cd "$ASSETUTILITIES_ROOT/scripts"'
alias auconfig='cd "$ASSETUTILITIES_ROOT/config"'

# Python development aliases
alias py='python'
alias py3='python3'
alias pip='python -m pip'
alias venv-create='python -m venv venv'
alias venv-activate='source venv/Scripts/activate'  # Windows Git Bash
alias venv-deactivate='deactivate'

# Testing aliases
alias test='python -m pytest'
alias test-v='python -m pytest -v'
alias test-vv='python -m pytest -vv'
alias test-fast='python -m pytest -x'  # Stop on first failure
alias test-cov='python -m pytest --cov=assetutilities'
alias test-html='python -m pytest --cov=assetutilities --cov-report=html'

# Code quality aliases
alias lint='ruff check src/'
alias lint-fix='ruff check --fix src/'
alias format='ruff format src/'
alias format-check='ruff format --check src/'
alias qa='lint && format-check && test'  # Full quality assurance

# Package management aliases
alias install='pip install -e .'  # Install in development mode
alias install-dev='pip install -e ".[dev]"'  # Install with dev dependencies
alias install-test='pip install -e ".[test]"'  # Install with test dependencies
alias requirements='pip freeze > requirements.txt'
alias deps='pip list'
alias outdated='pip list --outdated'

# Git workflow aliases
alias gs='git status'
alias ga='git add'
alias gc='git commit'
alias gp='git push'
alias gl='git log --oneline -10'
alias gb='git branch'
alias gco='git checkout'
alias gd='git diff'
alias gds='git diff --staged'

# Git workflow for AssetUtilities
alias commit-feat='git commit -m "feat: "'
alias commit-fix='git commit -m "fix: "'
alias commit-docs='git commit -m "docs: "'
alias commit-test='git commit -m "test: "'
alias commit-refactor='git commit -m "refactor: "'

# Package building and distribution
alias build='python -m build'
alias build-clean='rm -rf build/ dist/ *.egg-info/ && python -m build'
alias upload-test='python -m twine upload --repository testpypi dist/*'
alias upload='python -m twine upload dist/*'

# Documentation aliases
alias docs-build='python -m sphinx build docs docs/_build'
alias docs-serve='python -m http.server 8000 --directory docs/_build'
alias docs-clean='rm -rf docs/_build'

# Utility aliases
alias ll='ls -la'
alias la='ls -A'
alias l='ls -CF'
alias ..='cd ..'
alias ...='cd ../..'
alias ....='cd ../../..'

# Find files and content
alias ff='find . -name'  # Find files by name
alias fg='grep -r --include="*.py"'  # Find in Python files
alias fgl='grep -rl --include="*.py"'  # Find files containing pattern

# Process management
alias psg='ps aux | grep'
alias ports='netstat -tulpn'

# AssetUtilities specific shortcuts
alias au-clean='find . -name "*.pyc" -delete && find . -name "__pycache__" -delete'
alias au-reset='au-clean && rm -rf build/ dist/ *.egg-info/'
alias au-example='cd "$ASSETUTILITIES_ROOT/examples" && python'

# Quick file editing (assumes VS Code is available)
alias edit-config='code "$ASSETUTILITIES_ROOT/config"'
alias edit-setup='code "$ASSETUTILITIES_ROOT/setup.py"'
alias edit-pyproject='code "$ASSETUTILITIES_ROOT/pyproject.toml"'

# Environment information
alias au-env='echo "AssetUtilities Root: $ASSETUTILITIES_ROOT" && python --version && pip --version'
alias au-tree='tree -I "__pycache__|*.pyc|.git|venv|build|dist|*.egg-info" -L 3'

# Performance and profiling
alias profile='python -m cProfile -s cumulative'
alias memory='python -m memory_profiler'

# Package information
alias au-info='python -c "import assetutilities; print(assetutilities.__version__)"'
alias au-path='python -c "import assetutilities; print(assetutilities.__file__)"'

# Function aliases (these are more complex operations)

# Run a specific test file
autest-file() {
    if [[ -n "$1" ]]; then
        python -m pytest "tests/$1" -v
    else
        echo "Usage: autest-file <test_file_name>"
        echo "Example: autest-file test_excel.py"
    fi
}

# Quick commit with automatic message
aucommit() {
    if [[ -n "$1" ]]; then
        git add . && git commit -m "$1"
    else
        echo "Usage: aucommit <commit_message>"
    fi
}

# Create new feature branch
aubranch() {
    if [[ -n "$1" ]]; then
        git checkout -b "feature/$1"
    else
        echo "Usage: aubranch <feature_name>"
        echo "Example: aubranch new-excel-feature"
    fi
}

# Install package in development mode and run tests
audev() {
    echo "Installing AssetUtilities in development mode..."
    pip install -e . && echo "Running tests..." && python -m pytest tests/ -x
}

# Quick setup for new development environment
ausetup() {
    echo "Setting up AssetUtilities development environment..."
    python -m venv venv
    source venv/Scripts/activate
    pip install --upgrade pip
    pip install -e ".[dev,test]"
    echo "Development environment ready!"
}

echo "AssetUtilities aliases loaded. Type 'alias | grep au' to see all project aliases."