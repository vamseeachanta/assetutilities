# UV Python Development Environment Setup

This document describes the recommended steps for setting up and managing your Python development environment using UV, as per project guidelines.

## 1. Install UV
```bash
curl -LsSf https://astral.sh/uv/install.sh | sh
```

## 2. Create a virtual environment
```bash
uv venv
```

## 3. Sync dependencies from pyproject.toml
```bash
uv sync
```

## 4. Add a package (never update pyproject.toml directly)
```bash
uv add requests
```

## 5. Add development dependencies
```bash
uv add --dev pytest ruff mypy
```

## 6. Remove a package
```bash
uv remove requests
```

## 7. Run commands in the environment
```bash
uv run python script.py
uv run pytest
uv run ruff check .
```

## 8. Install a specific Python version
```bash
uv python install 3.12
```

---

For more details, see [UV documentation](https://github.com/astral-sh/uv).
