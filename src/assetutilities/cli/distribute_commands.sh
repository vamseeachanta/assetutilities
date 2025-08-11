#!/bin/bash
# Distribute AssetUtilities slash commands to all repositories
# This script can be run from any directory

# Configuration
ASSETUTILITIES_DIR="/mnt/github/github/assetutilities"
TARGET_DIR="${1:-/mnt/github/github}"
PARALLEL="${2:-5}"

echo "🚀 Distributing AssetUtilities Slash Commands"
echo "============================================="
echo "📦 Source: $ASSETUTILITIES_DIR"
echo "🎯 Target: $TARGET_DIR"
echo "⚡ Parallel: $PARALLEL workers"
echo ""

# Check if AssetUtilities exists
if [ ! -d "$ASSETUTILITIES_DIR" ]; then
    echo "❌ AssetUtilities not found at: $ASSETUTILITIES_DIR"
    exit 1
fi

# Check if target directory exists
if [ ! -d "$TARGET_DIR" ]; then
    echo "❌ Target directory not found: $TARGET_DIR"
    exit 1
fi

# Change to AssetUtilities directory
cd "$ASSETUTILITIES_DIR" || exit 1

# Run the propagate command
if [ -f "./slash_commands.py" ]; then
    echo "🔄 Running propagate-commands..."
    python3 ./slash_commands.py /propagate-commands \
        --target-dir "$TARGET_DIR" \
        --parallel "$PARALLEL" \
        --force
else
    echo "❌ slash_commands.py not found in AssetUtilities"
    exit 1
fi

echo ""
echo "✨ Distribution complete!"
echo ""
echo "To use the commands in other repositories:"
echo "  cd /path/to/repo"
echo "  ./slash_commands.py --list"
echo "  ./slash_commands.py /modernize-deps"