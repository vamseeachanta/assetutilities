# assetutilities Module Structure

Generated: 2025-08-11 06:30

## Directory Structure

```
assetutilities/
├── src/
│   └── assetutilities/       # Main package
│       ├── __init__.py
│       ├── __main__.py           # Entry point
│       ├── cli/                  # Command-line interfaces
│       ├── core/                 # Core functionality
│       ├── utils/                # Utilities
│       ├── devtools/             # Development tools
│       └── modules/              # Feature modules
├── tests/                        # Test suite
│   ├── unit/                     # Unit tests
│   ├── integration/              # Integration tests
│   └── fixtures/                 # Test data
├── docs/                         # Documentation
│   ├── api/                      # API docs
│   ├── guides/                   # User guides
│   └── examples/                 # Examples
├── scripts/                      # Standalone scripts
│   ├── dev/                      # Development scripts
│   ├── deployment/               # Deployment scripts
│   └── maintenance/              # Maintenance scripts
├── .agent-os/                    # Agent OS config
│   ├── commands/                 # Slash commands
│   ├── specs/                    # Specifications
│   └── product/                  # Product docs
└── [root config files]           # Configuration files
```

## Module Guidelines

### Adding New Features
1. Create a new module in `src/assetutilities/modules/`
2. Include `__init__.py` with module documentation
3. Add tests in `tests/unit/test_<module>.py`
4. Document in `docs/api/<module>.md`

### File Placement Rules

| File Type | Location | Example |
|-----------|----------|---------|
| Python modules | `src/assetutilities/` | `core/processor.py` |
| CLI scripts | `src/assetutilities/cli/` | `cli/main.py` |
| Tests | `tests/unit/` | `test_processor.py` |
| Dev scripts | `scripts/dev/` | `setup_env.sh` |
| Documentation | `docs/` | `guides/quickstart.md` |
| Slash commands | `.agent-os/commands/` | `organize_structure.py` |

## Import Examples

```python
# Import from main package
from assetutilities.core import processor
from assetutilities.utils import helpers
from assetutilities.cli import main

# Import from modules
from assetutilities.modules.web import scraper
from assetutilities.devtools import modernize_deps
```

## Best Practices

1. **Keep root clean**: Only configuration files in root
2. **Module isolation**: Each module should be self-contained
3. **Clear imports**: Use absolute imports from package root
4. **Test coverage**: Each module needs corresponding tests
5. **Documentation**: Each module needs API documentation
