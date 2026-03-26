# Git Trunk Flow - Enhanced with Hooks System

## 🎣 Hook System Overview

The enhanced `/git-trunk-flow` now includes a powerful hooks system that automatically executes code improvements, best practices, and integrates with other slash commands.

## Available Hooks

### 1. **Code Organization Hooks**

#### `/organize-structure` (External Command)
- Organizes project structure
- Moves files to proper directories
- Removes clutter and temporary files
- **Enabled by default**: Yes

#### `remove-duplicates` (Built-in)
- Detects duplicate code blocks
- Identifies repeated functions/classes
- Suggests refactoring opportunities
- **Configuration**:
  ```json
  {
    "min_lines": 10,
    "similarity_threshold": 0.9
  }
  ```

### 2. **Code Quality Hooks**

#### `fix-imports` (Built-in)
- Organizes Python imports (stdlib → third-party → local)
- Removes unused imports
- Sorts alphabetically
- Uses `isort` if available

#### `add-docstrings` (Built-in)
- Adds missing docstrings to functions
- Adds missing docstrings to classes
- Follows Google/NumPy style
- **Smart Detection**: Only adds where missing

### 3. **Security Hooks**

#### `security-fixes` (Built-in)
- Replaces hardcoded passwords with environment variables
- Adds Content-Security-Policy headers to HTML
- Removes exposed API keys
- Secures cookie settings

### 4. **Performance Hooks**

#### `performance-optimize` (Built-in)
- Converts list comprehensions to generators in loops
- Uses sets for membership testing
- Caches expensive operations
- Optimizes database queries

### 5. **Dependency Management**

#### `/modernize-deps` (External Command)
- Updates dependencies to latest stable versions
- Migrates to modern package managers (poetry, uv)
- Removes unused dependencies
- **Enabled by default**: Yes

### 6. **Testing Hooks**

#### `test-coverage` (Built-in)
- Identifies untested code
- Generates test stubs
- Adds missing test cases
- **Enabled by default**: No (opt-in)

## Configuration

### Creating Configuration File

Create `.git-trunk-flow.json` in your repository:

```json
{
  "hooks": {
    "organize-structure": {
      "enabled": true,
      "order": 1
    },
    "remove-duplicates": {
      "enabled": true,
      "order": 2,
      "config": {
        "min_lines": 10
      }
    },
    "fix-imports": {
      "enabled": true,
      "order": 3
    }
  },
  "auto_improvements": true,
  "interactive_mode": true
}
```

### Interactive Hook Selection

When running the enhanced flow:

```bash
$ ./slash_commands.py /git-trunk-flow-enhanced

🎣 Available Improvement Hooks:
----------------------------------------
✅ organize-structure: Organize project structure
✅ modernize-deps: Update dependencies
✅ remove-duplicates: Find duplicate code
✅ fix-imports: Fix and organize imports
✅ add-docstrings: Add missing docstrings
✅ security-fixes: Apply security best practices
✅ performance-optimize: Optimize performance
⭕ test-coverage: Add tests for uncovered code

Customize hooks? (y/n): y
Enter hook names to toggle, 'all', or 'none': test-coverage, lint-fix
```

## Execution Flow

### Standard Git Flow
```
1. Pre-flight checks
2. Cleanup redundant files
3. Apply best practices
4. Security scan
5. Run tests
6. Stage & Commit
7. Create PR
```

### Enhanced Flow with Hooks
```
1. Pre-flight checks
2. 🎣 EXECUTE IMPROVEMENT HOOKS
   ├── organize-structure (slash command)
   ├── modernize-deps (slash command)
   ├── remove-duplicates (built-in)
   ├── fix-imports (built-in)
   ├── add-docstrings (built-in)
   ├── security-fixes (built-in)
   └── performance-optimize (built-in)
3. Cleanup redundant files
4. Apply best practices
5. Security scan
6. Run tests
7. Stage & Commit (with improvements summary)
8. Create PR (with improvements report)
9. Show improvement report
```

## Integration with Other Commands

### Automatic Command Discovery

The enhanced flow can automatically discover and execute other slash commands:

```python
# In any repository with slash commands
available_commands = [
    "/organize-structure",
    "/modernize-deps",
    "/format-code",
    "/lint-fix",
    "/security-scan",
    "/update-deps"
]
```

### Custom Slash Command Integration

Add your own slash commands to the flow:

```json
{
  "hooks": {
    "custom-command": {
      "command": "/my-custom-command",
      "description": "My custom improvement",
      "enabled": true,
      "order": 15
    }
  }
}
```

## Improvement Report

### In Commit Message

```
feat: add user authentication system

Automated improvements applied:
- organize-structure: Moved 12 files to proper directories
- remove-duplicates: Found 3 duplicate functions
- fix-imports: Fixed imports in 8 files
- add-docstrings: Added 15 docstrings
- security-fixes: Applied 2 security fixes
- performance-optimize: Optimized 4 files

Best practices enforced:
- Code deduplication
- Import organization
- Security fixes
- Performance optimizations
```

### In Pull Request

```markdown
## Summary
Add user authentication system with automated improvements

## Automated Improvements
✅ **Code Organization**: Restructured project layout
✅ **Duplicates Removed**: 3 duplicate functions refactored
✅ **Imports Fixed**: 8 files with organized imports
✅ **Documentation**: Added 15 missing docstrings
✅ **Security**: Applied 2 security fixes
✅ **Performance**: 4 files optimized

## Changes Made
- Implemented JWT authentication
- Added user registration endpoints
- Created login/logout functionality
```

## Examples

### Example 1: Full Improvement Cycle

```bash
$ ./slash_commands.py /git-trunk-flow-enhanced

🔧 Executing Code Improvements...
========================================

▶️  Running: organize-structure
   Organize project structure and remove clutter
   ✅ Moved 8 files to src/
   ✅ Created proper module structure

▶️  Running: remove-duplicates
   Find and remove duplicate code
   🔍 Scanning for duplicate code...
   Duplicate found: calculate_total in utils.py
   Duplicate found: calculate_total in helpers.py
   ✅ Found 2 duplicate code blocks

▶️  Running: fix-imports
   Fix and organize imports
   🔧 Fixing Python imports...
   ✅ Fixed imports in 12 files

▶️  Running: add-docstrings
   Add missing docstrings
   📝 Adding missing docstrings...
   ✅ Added 23 docstrings

▶️  Running: security-fixes
   Apply security best practices
   🔒 Applying security fixes...
   ✅ Applied 3 security fixes

▶️  Running: performance-optimize
   Optimize performance bottlenecks
   ⚡ Optimizing performance...
   ✅ Optimized 5 files
```

### Example 2: Selective Hooks

```bash
# Only run specific improvements
$ ./slash_commands.py /git-trunk-flow-enhanced

Customize hooks? (y/n): y
Enter hook names to toggle: organize-structure, security-fixes

# Now only these hooks will run:
✅ organize-structure
⭕ modernize-deps (disabled)
⭕ remove-duplicates (disabled)
⭕ fix-imports (disabled)
⭕ add-docstrings (disabled)
✅ security-fixes
⭕ performance-optimize (disabled)
```

## Creating Custom Hooks

### Built-in Hook Template

```python
def my_custom_improvement(self) -> str:
    """Custom improvement logic."""
    print("   🔧 Running custom improvement...")
    
    improvements_made = 0
    
    # Your improvement logic here
    for file in Path(self.repo_path).rglob("*.py"):
        # Process file
        improvements_made += 1
    
    if improvements_made > 0:
        print(f"   ✅ Made {improvements_made} improvements")
        return f"Made {improvements_made} improvements"
    else:
        print("   ✅ No improvements needed")
        return "No improvements needed"
```

### External Command Hook

```python
# Create as slash command
# /my-improvement command

def main():
    """Execute my improvement."""
    # Improvement logic
    print("✅ My improvement completed")
    return 0
```

Then add to config:
```json
{
  "hooks": {
    "my-improvement": {
      "command": "/my-improvement",
      "enabled": true,
      "order": 20
    }
  }
}
```

## Benefits

### Without Hooks
- Manual code cleanup
- Separate commands for each improvement
- Inconsistent application of best practices
- Easy to forget important steps

### With Hooks
- ✅ Automatic code improvements
- ✅ Integrated workflow
- ✅ Consistent best practices
- ✅ All improvements in one commit
- ✅ Comprehensive improvement report
- ✅ Extensible with custom hooks
- ✅ Integration with slash command ecosystem

## Best Practices

1. **Start with defaults**: The default hooks cover most common improvements
2. **Customize per project**: Different projects need different hooks
3. **Add custom hooks**: Create project-specific improvements
4. **Review changes**: Always review automated improvements before committing
5. **Iterate**: Refine hook configuration based on results

## Troubleshooting

### Hooks not running
- Check `.git-trunk-flow.json` exists and is valid JSON
- Ensure slash commands are available (`./slash_commands.py --list`)
- Verify hook is enabled in configuration

### Improvements breaking code
- Use `--dry-run` mode first
- Disable problematic hooks
- Configure hook parameters in config file
- Review changes before committing

### Performance issues
- Disable expensive hooks for large codebases
- Run hooks selectively
- Use configuration to limit scope

## Future Enhancements

Planned improvements:
- AI-powered code review hooks
- Automatic refactoring suggestions
- Cross-repository improvement patterns
- Machine learning for duplicate detection
- Automatic test generation
- Documentation generation hooks

---

*The enhanced git-trunk-flow with hooks brings the power of multiple slash commands into a single, integrated workflow!* 🚀