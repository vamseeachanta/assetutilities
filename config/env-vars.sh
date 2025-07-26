#!/bin/bash

# AssetUtilities Environment Variables
# Project-specific environment variable definitions

# Ensure we're in the AssetUtilities project
if [[ -z "$ASSETUTILITIES_ROOT" ]]; then
    return 1
fi

# Python development settings
export PYTHONDONTWRITEBYTECODE=1  # Prevent .pyc file creation
export PYTHONUNBUFFERED=1         # Force stdout/stderr to be unbuffered

# AssetUtilities package settings
export ASSETUTILITIES_LOG_LEVEL="INFO"
export ASSETUTILITIES_CONFIG_DIR="$ASSETUTILITIES_ROOT/config"
export ASSETUTILITIES_DATA_DIR="$ASSETUTILITIES_ROOT/data"
export ASSETUTILITIES_OUTPUT_DIR="$ASSETUTILITIES_ROOT/output"

# Testing environment
export PYTEST_ADDOPTS="--verbose --tb=short"
export ASSETUTILITIES_TEST_DATA="$ASSETUTILITIES_ROOT/tests/data"

# Development tools
export RUFF_CONFIG="$ASSETUTILITIES_ROOT/pyproject.toml"

# Git settings (project-specific)
export GIT_EDITOR="code --wait"  # Use VS Code as git editor

# Package building and distribution
export ASSETUTILITIES_BUILD_DIR="$ASSETUTILITIES_ROOT/build"
export ASSETUTILITIES_DIST_DIR="$ASSETUTILITIES_ROOT/dist"

# Documentation settings
export ASSETUTILITIES_DOCS_DIR="$ASSETUTILITIES_ROOT/docs"

# Create necessary directories if they don't exist
mkdir -p "$ASSETUTILITIES_DATA_DIR" 2>/dev/null || true
mkdir -p "$ASSETUTILITIES_OUTPUT_DIR" 2>/dev/null || true