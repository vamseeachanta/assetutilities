# Deployment Agent Configuration

> Repository: AssetUtilities
> Created: 2025-07-31
> Version: 1.0.0

## Agent Purpose

This deployment agent provides build and release automation specifically optimized for AssetUtilities Python package deployment, focusing on PyPI publishing, version management, and distribution automation that adapts to the setuptools-based build system.

## Build System Integration

### Package Build Configuration
- **Build System**: setuptools>=61.0.0 with pyproject.toml configuration
- **Distribution Format**: wheel format for efficient distribution
- **Version Management**: bumpver tool for semantic versioning (MAJOR.MINOR.PATCH)
- **Publishing Tool**: twine for secure PyPI publishing

### Build Process
```bash
#!/bin/bash
# Clean previous builds
rm -rf dist/ build/ src/*.egg-info/

# Build package distributions
python -m build --sdist --wheel

# Verify package contents
twine check dist/*

# Upload to PyPI (production)
twine upload dist/*
```

## Version Management

### Semantic Versioning Strategy
- **Current Version**: 0.0.8 (development phase)
- **Version Pattern**: MAJOR.MINOR.PATCH
- **Increment Rules**:
  - MAJOR: Breaking API changes
  - MINOR: New features, backwards compatible
  - PATCH: Bug fixes, backwards compatible

### Version Automation
```bash
#!/bin/bash
# Patch version increment
bumpver update --patch

# Minor version increment  
bumpver update --minor

# Major version increment
bumpver update --major

# Custom version
bumpver update --set-version 1.0.0
```

## Deployment Environments

### Development Environment
- **Installation**: Local pip install -e . (editable install)
- **Testing**: pytest test suite execution
- **Dependencies**: Development dependencies via poetry/uv
- **Code Quality**: ruff linting and formatting checks

### Production Environment
- **Platform**: PyPI (Python Package Index)
- **Distribution**: Global CDN distribution
- **Installation**: pip install assetutilities
- **Monitoring**: Download statistics and usage metrics

## Release Automation

### Pre-Release Checks
1. **Code Quality**: Run ruff checks and formatting
2. **Test Suite**: Execute complete pytest test suite
3. **Documentation**: Verify documentation is up-to-date
4. **Version**: Confirm version increment is appropriate
5. **Dependencies**: Validate dependency compatibility

### Release Process
```bash
#!/bin/bash
# Pre-release validation
python -m ruff check src/
python -m ruff format --check src/
pytest tests/ --cov=src/assetutilities --cov-fail-under=90

# Version increment
bumpver update --patch

# Build package
python -m build --sdist --wheel

# Security check
twine check dist/*

# Upload to PyPI
twine upload dist/*

# Git tagging
git tag v$(python -c "import tomli; print(tomli.load(open('pyproject.toml', 'rb'))['project']['version'])")
git push origin --tags
```

## Continuous Integration

### GitHub Actions Integration
```yaml
# .github/workflows/release.yml
name: Release Package
on:
  push:
    tags:
      - 'v*'

jobs:
  release:
    runs-on: ubuntu-latest
    steps:
    - uses: actions/checkout@v3
    - name: Set up Python
      uses: actions/setup-python@v4
      with:
        python-version: '3.9'
    - name: Install dependencies
      run: |
        pip install build twine
    - name: Build package
      run: python -m build
    - name: Publish to PyPI
      env:
        TWINE_USERNAME: __token__
        TWINE_PASSWORD: ${{ secrets.PYPI_API_TOKEN }}
      run: twine upload dist/*
```

### Quality Gates
- **Test Coverage**: Minimum 90% test coverage required
- **Code Quality**: All ruff checks must pass
- **Security**: No known security vulnerabilities
- **Documentation**: All public APIs documented

## Distribution Management

### Package Metadata
```toml
# pyproject.toml excerpt
[project]
name = "assetutilities"
description = "Comprehensive Python library for business automation utilities"
authors = [{name = "AssetUtilities Team", email = "team@assetutilities.com"}]
license = {text = "MIT"}
requires-python = ">=3.8"
keywords = ["business", "automation", "utilities", "excel", "visualization"]
```

### Dependency Management
- **Core Dependencies**: numpy, pandas, plotly, matplotlib, PyYAML
- **Optional Dependencies**: Group related optional dependencies
- **Version Constraints**: Specify minimum versions for stability
- **Security Updates**: Regular dependency security updates

## Monitoring and Analytics

### Distribution Metrics
- **Download Statistics**: Track PyPI download counts
- **Version Adoption**: Monitor version distribution usage
- **Geographic Distribution**: Track usage by region
- **Installation Methods**: Monitor pip vs conda installations

### Performance Monitoring
- **Package Size**: Monitor distribution package size
- **Installation Time**: Track installation performance
- **Import Performance**: Monitor module import speed
- **Memory Usage**: Track runtime memory consumption

## Rollback Procedures

### Emergency Rollback
```bash
#!/bin/bash
# Remove problematic version from PyPI (if possible)
# Note: PyPI generally doesn't allow deletion of releases

# Create hotfix release
bumpver update --patch
# Fix critical issue
git commit -m "Hotfix: Critical issue resolution"

# Emergency release
python -m build --sdist --wheel
twine upload dist/*
```

### Version Deprecation
- **Deprecation Warnings**: Add warnings to deprecated versions
- **Migration Guide**: Provide clear migration documentation
- **Support Timeline**: Define support timeline for older versions
- **Communication**: Notify users of deprecation through appropriate channels

## Security Considerations

### Secure Publishing
- **API Tokens**: Use PyPI API tokens instead of username/password
- **Token Scope**: Limit token scope to specific packages
- **Secret Management**: Store tokens securely in CI/CD systems
- **Two-Factor Authentication**: Enable 2FA on PyPI account

### Package Security
- **Dependency Scanning**: Regular security scanning of dependencies
- **Code Signing**: Consider package signing for integrity verification
- **Vulnerability Monitoring**: Monitor for reported vulnerabilities
- **Security Updates**: Rapid response to security issues

## Team Coordination

### Release Management
- **Release Calendar**: Coordinate release schedule with team
- **Release Notes**: Maintain comprehensive release notes
- **Communication**: Notify stakeholders of releases
- **Documentation**: Update documentation with each release

### Deployment Standards
- **Consistent Versioning**: Follow semantic versioning strictly
- **Quality Standards**: Maintain consistent quality standards
- **Testing Requirements**: Comprehensive testing before releases
- **Documentation**: Keep deployment documentation current

## Environment Configuration

### Local Deployment Setup
```bash
#!/bin/bash
# Install development dependencies
pip install build twine bumpver ruff pytest

# Set up PyPI credentials
# Create ~/.pypirc with credentials

# Configure git for tagging
git config user.name "AssetUtilities Team"
git config user.email "team@assetutilities.com"
```

### CI/CD Environment
- **Python Versions**: Test against Python 3.8, 3.9, 3.10, 3.11, 3.12
- **Operating Systems**: Test on Linux, Windows, macOS
- **Dependencies**: Test with minimum and latest dependency versions
- **Package Installation**: Verify package installs correctly from PyPI