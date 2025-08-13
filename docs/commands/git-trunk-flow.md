# Git Trunk-Based Development Flow Command

## Overview

The `/git-trunk-flow` command implements industry best practices for trunk-based development, automating the entire git workflow from cleanup to PR creation and merge.

## Features

### 🧹 Step 1: Redundant File Cleanup
- Automatically removes temporary files (`*.tmp`, `*.bak`, `*.swp`)
- Cleans build artifacts (`__pycache__/`, `*.pyc`, `dist/`, `build/`)
- Removes IDE files not in `.gitignore`
- Eliminates duplicate and backup files

### 🔧 Step 2: Best Practices Application
- Creates/enhances `.gitignore` with comprehensive patterns
- Adds `.editorconfig` for consistent formatting
- Creates GitHub templates (PR template, CODEOWNERS)
- Sets up pre-commit hooks for security scanning
- Recommends branch protection rules

### 🔒 Step 3: Security Scanning
- Scans for API keys and tokens
- Detects AWS credentials
- Finds private keys
- Identifies database URLs with passwords
- Prevents JWT tokens from being committed

### 🧪 Step 4: Automated Testing
- Detects and runs available test suites
- Supports multiple test frameworks (pytest, npm, cargo, go, etc.)
- Ensures tests pass before commit

### 📦 Step 5: Smart Staging
- Stages all changes intelligently
- Shows commit statistics
- Warns if PR size exceeds best practices (>400 lines)

### ✍️ Step 6: Conventional Commits
- Interactive commit type selection
- Follows conventional commit standard
- Supports scopes and breaking changes
- Enforces 50-character title limit
- Wraps body at 72 characters

### 🔀 Step 7: PR Creation & Merge
- Creates short-lived feature branches (max 2-3 days)
- Pushes to remote repository
- Creates PR with comprehensive template
- Enables auto-merge with squash strategy
- Maintains clean linear history

### 🧹 Step 8: Branch Cleanup
- Deletes merged local branches
- Cleans up stale remote branches
- Returns to main branch
- Pulls latest changes

## Usage

### Basic Usage
```bash
cd /path/to/your/repo
python /mnt/github/github/assetutilities/.agent-os/commands/git_trunk_flow.py
```

### As Slash Command (from assetutilities)
```bash
cd /mnt/github/github/assetutilities
./slash_commands.py /git-trunk-flow
```

### From Any Repository (after propagation)
```bash
/git-trunk-flow
```

## Best Practices Implemented

### Trunk-Based Development
- **Short-lived branches**: Maximum 2-3 days lifespan
- **Continuous integration**: Merge to main frequently
- **Feature flags**: For incomplete features (recommended)
- **Small changes**: Optimal PR size 200-400 lines

### Commit Standards
- **Conventional Commits**: Standardized commit messages
- **Semantic Versioning**: Type indicates version impact
- **Clear history**: Squash merge for linear history
- **Co-authorship**: Attributes trunk flow automation

### Security
- **Pre-commit scanning**: Prevents secrets from being committed
- **Comprehensive patterns**: Detects various secret types
- **Manual override**: Available for false positives
- **Git hooks**: Automated security enforcement

### Code Quality
- **Automated testing**: Runs before every commit
- **Clean repository**: Removes redundant files
- **Consistent formatting**: Via .editorconfig
- **Code ownership**: Clear review responsibilities

## Configuration Files Created

### .gitignore
Comprehensive ignore patterns for:
- Environment variables
- IDE files
- OS artifacts
- Build outputs
- Temporary files
- Security files

### .editorconfig
Ensures consistent:
- Character encoding (UTF-8)
- Line endings (LF)
- Indentation (spaces)
- Trailing whitespace handling

### .github/CODEOWNERS
Defines:
- Default reviewers
- Team responsibilities
- Path-based ownership

### .github/pull_request_template.md
Includes:
- Change type checklist
- Testing confirmation
- Best practices reminder
- PR size indicator

### .git/hooks/pre-commit
Performs:
- Secret scanning
- Pattern matching
- Best practice reminders

## Workflow Example

```bash
$ /git-trunk-flow

🚀 Starting Git Trunk-Based Development Flow
============================================================

📋 Running pre-flight checks...
📝 Currently on main branch.
Enter feature name (e.g., 'user-auth', 'fix-bug'): enhance-security
✅ Created short-lived feature branch: enhance-security

🧹 Step 1: Cleaning up redundant files...
✅ Removed 15 redundant files

🔧 Step 2: Applying best practices to main context...
  Creating .github/CODEOWNERS...
  Creating .github/pull_request_template.md...
  Enhanced .gitignore

🔒 Step 3: Running security scan...
✅ No security issues detected

🧪 Step 4: Running tests...
✅ Tests passed: pytest

📦 Step 5: Staging changes...
Changes to be committed:
 15 files changed, 342 insertions(+), 28 deletions(-)

✍️ Step 6: Creating conventional commit...
Select commit type:
  1. feat: New feature (MINOR version)
  2. fix: Bug fix (PATCH version)
Enter choice (1-10): 1
Enter scope: security
Enter description: add comprehensive security scanning

✅ Commit created: feat(security): add comprehensive security scanning

🔀 Step 7: Creating Pull Request...
✅ Pull request created: https://github.com/user/repo/pull/123
✅ Auto-merge enabled (will squash merge after checks pass)

🧹 Step 8: Cleaning up branches...
  Deleted: old-feature-branch
  Deleted: stale-branch

✅ Trunk-based development flow completed successfully!
```

## Error Handling

### Security Issues
If secrets are detected:
1. Shows specific files and patterns
2. Asks for confirmation to continue
3. Suggests using `--no-verify` for false positives

### Test Failures
If tests fail:
1. Shows test output
2. Prevents commit creation
3. Suggests fixing tests first

### Git Conflicts
If rebase conflicts occur:
1. Provides conflict resolution guidance
2. Allows manual resolution
3. Continues after resolution

## Requirements

### System Requirements
- Git 2.0+
- Python 3.7+
- GitHub CLI (optional, for PR creation)

### Repository Requirements
- Initialized git repository
- Remote origin configured
- Main/master branch exists

## Integration with CI/CD

The command works seamlessly with CI/CD pipelines:
1. Pre-commit hooks run locally
2. PR creation triggers CI/CD
3. Auto-merge waits for checks
4. Squash merge maintains clean history

## Customization

### Modify Cleanup Patterns
Edit `cleanup_patterns` in the `GitTrunkFlow` class to add/remove file patterns.

### Add Security Patterns
Update `secrets_patterns` to detect additional secret types.

### Customize Templates
Modify generator methods to change created file contents:
- `generate_gitignore_content()`
- `generate_editorconfig_content()`
- `generate_codeowners_content()`
- `generate_pr_template()`

## Troubleshooting

### "Not in a git repository"
- Ensure you're in a directory with `.git` folder
- Run `git init` if needed

### "No changes detected"
- Make some changes before running the command
- Check `git status` to see current state

### "GitHub CLI not available"
- Install GitHub CLI: `brew install gh` (macOS)
- Or create PR manually using the provided information

### Pre-commit hook issues
- Check `.git/hooks/pre-commit` permissions
- Ensure it's executable: `chmod +x .git/hooks/pre-commit`

## Best Practices Summary

1. **Keep branches short-lived** - Maximum 2-3 days
2. **Make small commits** - Focused, single-purpose changes
3. **Write clear messages** - Use conventional commits
4. **Test before merge** - All tests must pass
5. **Squash on merge** - Maintain linear history
6. **Clean up regularly** - Remove merged branches
7. **Secure by default** - Never commit secrets
8. **Automate everything** - Use this command!

## Related Commands

- `/git-sync` - Sync with remote
- `/git-commit` - Create conventional commit
- `/git-pr` - Create pull request
- `/git-clean` - Clean merged branches

## Contributing

To improve this command:
1. Edit `/mnt/github/github/assetutilities/.agent-os/commands/git_trunk_flow.py`
2. Test changes locally
3. Use `/git-trunk-flow` to submit your improvements!

## References

- [Trunk-Based Development](https://trunkbaseddevelopment.com/)
- [Conventional Commits](https://www.conventionalcommits.org/)
- [GitHub Flow](https://guides.github.com/introduction/flow/)
- [Git Best Practices](https://git-scm.com/book/en/v2)

---

*Automating best practices for better code quality* 🚀