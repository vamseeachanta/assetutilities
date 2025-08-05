#!/bin/bash
# Global UV Environment Setup Script for Unix/Linux/macOS
# This script sets up the AssetUtilities environment globally for use across repositories

echo "================================"
echo "AssetUtilities Global UV Environment Setup"
echo "================================"

# Check if UV is installed
if ! command -v uv &> /dev/null; then
    echo "ERROR: UV is not installed or not in PATH"
    echo "Please install UV first: https://docs.astral.sh/uv/getting-started/installation/"
    exit 1
fi

echo "UV version detected:"
uv --version

# Get the current directory (AssetUtilities repo root)
ASSETUTILS_ROOT=$(pwd)

echo ""
echo "Setting up global environment from: $ASSETUTILS_ROOT"
echo ""

# Create a global environment using UV
echo "Creating global UV environment..."
uv venv --python 3.13 "$HOME/.uv/envs/assetutilities-global"

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to create global environment"
    exit 1
fi

# Activate the global environment and install dependencies
echo "Installing dependencies to global environment..."
source "$HOME/.uv/envs/assetutilities-global/bin/activate"

# Install using the current pyproject.toml
uv sync

if [ $? -ne 0 ]; then
    echo "ERROR: Failed to install dependencies"
    exit 1
fi

echo ""
echo "================================"
echo "SUCCESS: Global environment created!"
echo "================================"
echo ""
echo "Global environment location: $HOME/.uv/envs/assetutilities-global"
echo ""
echo "To use in other repositories:"
echo "1. Copy the activation script to your repo"
echo "2. Run: source activate-assetutils-global.sh"
echo "3. Or use: uv run --python $HOME/.uv/envs/assetutilities-global/bin/python your_script.py"
echo ""