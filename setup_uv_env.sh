#!/bin/bash
# Setup script for AssetUtilities with uv package manager

echo "Setting up AssetUtilities environment with uv..."

# Check if uv is installed
if ! command -v uv &> /dev/null; then
    echo "Installing uv..."
    curl -LsSf https://astral.sh/uv/install.sh | sh
    export PATH="$HOME/.cargo/bin:$PATH"
fi

# Create virtual environment with uv
echo "Creating virtual environment..."
uv venv

# Activate virtual environment
source .venv/bin/activate

# Install dependencies from pyproject.toml
echo "Installing dependencies..."
uv pip install -e .

# Install development dependencies
echo "Installing development dependencies..."
uv pip install -e ".[dev]"

# Verify installation
echo "Verifying installation..."
python -c "import assetutilities; print(f'AssetUtilities {assetutilities.__version__} installed successfully')"

echo "Setup complete! Activate the environment with: source .venv/bin/activate"