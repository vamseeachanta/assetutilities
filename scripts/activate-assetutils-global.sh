#!/bin/bash
# Global AssetUtilities Environment Activation Script
# Copy this file to any repository to activate the global AssetUtilities environment

echo "Activating AssetUtilities Global Environment..."

# Check if global environment exists
if [ ! -f "$HOME/.uv/envs/assetutilities-global/bin/activate" ]; then
    echo "ERROR: Global AssetUtilities environment not found!"
    echo "Please run setup-global-env.sh from the AssetUtilities repository first."
    echo ""
    echo "Expected location: $HOME/.uv/envs/assetutilities-global"
    exit 1
fi

# Activate the global environment
source "$HOME/.uv/envs/assetutilities-global/bin/activate"

echo ""
echo "================================"
echo "AssetUtilities Global Environment Active"
echo "================================"
echo "Python: $HOME/.uv/envs/assetutilities-global/bin/python"
echo ""
echo "Available utilities:"
echo "- All AssetUtilities modules (excel, visualization, file management, etc.)"
echo "- Development tools (pytest, ruff, build tools)"
echo "- Web scraping tools (scrapy, selenium, playwright)"
echo "- Data processing tools (pandas, numpy, plotly)"
echo ""
echo "Type 'deactivate' to exit this environment"
echo ""

# Start a new shell with the environment active
exec "$SHELL"