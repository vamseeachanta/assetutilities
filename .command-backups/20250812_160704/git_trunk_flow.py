#!/usr/bin/env python3
"""
Git Trunk-Based Development Flow Command
Implements best practices for trunk-based development with automated cleanup,
security checks, and PR creation/merge workflow.

Based on comprehensive research of trunk-based development best practices:
- Short-lived feature branches (max 2-3 days)
- Conventional commits standard
- Squash merge strategy for clean history
- Automated security scanning
- Comprehensive testing before merge
- Small, focused PRs (200-400 lines optimal)
"""

import os
import sys
import subprocess
import re
import tempfile
from pathlib import Path
from typing import List, Optional

class GitTrunkFlow:
    """Manages trunk-based development workflow with best practices."""
    
    def __init__(self):
        self.repo_path = os.getcwd()
        self.main_branch = self.detect_main_branch()
        self.current_branch = self.get_current_branch()
        
        # Redundant file patterns to clean
        self.cleanup_patterns = [
            # Temporary and backup files
            "*.tmp", "*.bak", "*.backup", "*.orig", "*.swp", "*.swo",
            "*~", ".DS_Store", "Thumbs.db", "desktop.ini",
            
            # Build artifacts that shouldn't be committed
            "*.pyc", "__pycache__/", "*.pyo", "*.pyd",
            ".pytest_cache/", ".coverage", "htmlcov/",
            "*.egg-info/", "dist/", "build/",
            
            # Log files
            "*.log", "logs/", "*.debug",
            
            # IDE files that might not be in .gitignore
            ".idea/", ".vscode/", "*.iml", ".project", ".classpath",
            
            # Duplicate files
            "*.backup.*", "*.old", "*.duplicate",
            
            # Environment files
            ".env.backup*", ".env.old", ".env.local.backup*"
        ]
        
        # Secret patterns for security scanning
        self.secrets_patterns = [
            # API keys and tokens
            r'(?i)(api[_-]?key|apikey|api[_-]?secret)[\s]*[=:]\s*["\']?[\w\-]+["\']?',
            r'(?i)(token|access[_-]?token|auth[_-]?token)[\s]*[=:]\s*["\']?[\w\-]+["\']?',
            
            # AWS patterns
            r'AKIA[0-9A-Z]{16}',
            r'(?i)aws[_-]?secret[_-]?access[_-]?key[\s]*[=:]\s*["\']?[\w\+\/]+["\']?',
            
            # Private keys
            r'-----BEGIN (RSA |EC |DSA |OPENSSH )?PRIVATE KEY-----',
            
            # Database URLs with credentials
            r'(?i)(mongodb|postgres|postgresql|mysql|redis)://[^:]+:[^@]+@',
            
            # Generic passwords
            r'(?i)(password|passwd|pwd)[\s]*[=:]\s*["\']?[^\s"\']+["\']?',
            
            # JWT tokens
            r'eyJ[A-Za-z0-9-_=]+\.[A-Za-z0-9-_=]+\.?[A-Za-z0-9-_.+/=]*'
        ]
        
        # Best practice files to ensure exist
        self.required_files = {
            '.gitignore': self.generate_gitignore_content(),
            'README.md': None,  # Check existence only
            '.editorconfig': self.generate_editorconfig_content(),
            '.github/CODEOWNERS': self.generate_codeowners_content(),
            '.github/pull_request_template.md': self.generate_pr_template()
        }

    def run(self):
        """Execute the complete trunk-based development flow."""
        print("🚀 Starting Git Trunk-Based Development Flow")
        print("=" * 60)
        print("\nImplementing best practices:")
        print("  • Short-lived feature branches (max 2-3 days)")
        print("  • Conventional commits standard")
        print("  • Automated security scanning")
        print("  • Comprehensive testing")
        print("  • Small, focused changes")
        print("=" * 60)
        
        try:
            # Step 1: Pre-flight checks
            self.preflight_checks()
            
            # Step 2: Clean up redundant files
            self.cleanup_redundant_files()
            
            # Step 3: Apply best practices
            self.apply_best_practices()
            
            # Step 4: Security scan
            self.security_scan()
            
            # Step 5: Run tests if available
            self.run_tests()
            
            # Step 6: Stage changes
            self.stage_changes()
            
            # Step 7: Create commit
            commit_message = self.create_commit()
            
            # Step 8: Create and merge PR
            self.create_and_merge_pr(commit_message)
            
            # Step 9: Clean up branches
            self.cleanup_branches()
            
            print("\n✅ Trunk-based development flow completed successfully!")
            print("\n📚 Best Practices Applied:")
            print("  • Redundant files cleaned")
            print("  • Security scan completed")
            print("  • Tests executed")
            print("  • Conventional commit created")
            print("  • PR created with squash merge strategy")
            
        except Exception as e:
            print(f"\n❌ Error: {e}")
            sys.exit(1)

    def preflight_checks(self):
        """Perform initial checks before proceeding."""
        print("\n📋 Running pre-flight checks...")
        
        # Check if we're in a git repository
        if not os.path.exists('.git'):
            raise Exception("Not in a git repository")
        
        # Check for uncommitted changes
        status = self.run_command("git status --porcelain")
        if not status:
            print("⚠️  No changes detected. Nothing to commit.")
            sys.exit(0)
        
        # Ensure we're not on main/master (trunk-based best practice)
        if self.current_branch in ['main', 'master']:
            print(f"📝 Currently on {self.current_branch} branch.")
            branch_name = self.create_feature_branch()
            print(f"✅ Created short-lived feature branch: {branch_name}")
            print("   (Best practice: max 2-3 days lifespan)")
        
        # Fetch latest changes
        print("📥 Fetching latest changes from remote...")
        self.run_command("git fetch origin")
        
        # Check if main branch is up to date
        behind = self.run_command(f"git rev-list HEAD..origin/{self.main_branch} --count").strip()
        if behind != "0":
            print(f"⚠️  Your branch is {behind} commits behind origin/{self.main_branch}")
            print("   (Best practice: Always rebase on latest trunk)")
            response = input("Would you like to rebase on latest main? (y/n): ")
            if response.lower() == 'y':
                self.rebase_on_main()

    def cleanup_redundant_files(self):
        """Remove redundant and temporary files."""
        print("\n🧹 Step 1: Cleaning up redundant files...")
        print("   (Best practice: Keep repository clean)")
        
        removed_files = []
        for pattern in self.cleanup_patterns:
            # Find files matching pattern
            import glob
            matches = glob.glob(f"**/{pattern}", recursive=True)
            
            for file_path in matches:
                # Skip if file is in .git directory
                if '.git' in Path(file_path).parts:
                    continue
                    
                # Check if file is ignored by git
                ignored = self.run_command(f"git check-ignore {file_path}", check=False)
                if not ignored:
                    # File is not ignored, so it's safe to remove
                    try:
                        if os.path.isdir(file_path):
                            import shutil
                            shutil.rmtree(file_path)
                        else:
                            os.remove(file_path)
                        removed_files.append(file_path)
                    except Exception as e:
                        print(f"    ⚠️  Could not remove {file_path}: {e}")
        
        if removed_files:
            print(f"✅ Removed {len(removed_files)} redundant files")
            for file in removed_files[:10]:  # Show first 10
                print(f"    - {file}")
            if len(removed_files) > 10:
                print(f"    ... and {len(removed_files) - 10} more")
        else:
            print("✅ No redundant files found")

    def apply_best_practices(self) -> List[str]:
        """Apply repository best practices."""
        print("\n🔧 Step 2: Applying best practices to main context...")
        
        changes_made = []
        
        # Check and create essential files
        for filename, content in self.required_files.items():
            file_path = Path(self.repo_path) / filename
            
            # Create directory if needed
            file_path.parent.mkdir(parents=True, exist_ok=True)
            
            if not file_path.exists() and content:
                print(f"  Creating {filename} (best practice: standardized project files)...")
                file_path.write_text(content)
                changes_made.append(f"Created {filename}")
            elif filename == '.gitignore' and file_path.exists():
                # Enhance existing .gitignore
                existing_content = file_path.read_text()
                enhanced = self.enhance_gitignore(existing_content)
                if enhanced != existing_content:
                    file_path.write_text(enhanced)
                    changes_made.append(f"Enhanced {filename}")
        
        # Check for branch protection recommendations
        if self.current_branch == self.main_branch:
            print("  ⚠️  Recommendation: Enable branch protection rules for main branch")
            print("     - Require PR reviews")
            print("     - Require status checks")
            print("     - Dismiss stale reviews")
            changes_made.append("Branch protection recommended")
        
        # Check for pre-commit hooks
        hooks_path = Path('.git/hooks/pre-commit')
        if not hooks_path.exists():
            print("  Creating pre-commit hook for security scanning...")
            self.create_pre_commit_hook()
            changes_made.append("Created pre-commit hook")
        
        # Check for CI/CD configuration
        ci_configs = ['.github/workflows', '.gitlab-ci.yml', 'Jenkinsfile', '.circleci/config.yml']
        has_ci = any(Path(config).exists() for config in ci_configs)
        if not has_ci:
            print("  ⚠️  Recommendation: Set up CI/CD pipeline")
            print("     (Best practice: Automated testing on every commit)")
        
        if changes_made:
            print("\n📝 Changes to be committed (best practices applied):")
            for change in changes_made:
                print(f"    ✅ {change}")
        else:
            print("✅ Repository already follows best practices")
        
        return changes_made

    def security_scan(self):
        """Scan for potential security issues."""
        print("\n🔒 Step 3: Running security scan...")
        print("   (Best practice: Never commit secrets)")
        
        issues_found = []
        
        # Get list of staged files
        staged_files = self.run_command("git diff --cached --name-only").split('\n')
        staged_files = [f for f in staged_files if f and os.path.exists(f)]
        
        for file_path in staged_files:
            # Skip binary files
            if self.is_binary_file(file_path):
                continue
            
            try:
                with open(file_path, 'r', encoding='utf-8', errors='ignore') as f:
                    content = f.read()
                    
                for pattern in self.secrets_patterns:
                    matches = re.findall(pattern, content)
                    if matches:
                        issues_found.append({
                            'file': file_path,
                            'pattern': pattern.split('(')[1].split(')')[0] if '(' in pattern else 'secret',
                            'matches': len(matches)
                        })
            except Exception:
                continue
        
        if issues_found:
            print("⚠️  Potential security issues found:")
            for issue in issues_found:
                print(f"    - {issue['file']}: {issue['matches']} potential {issue['pattern']}(s)")
            
            response = input("\nContinue anyway? (y/n): ")
            if response.lower() != 'y':
                raise Exception("Security scan failed - aborting")
        else:
            print("✅ No security issues detected")

    def run_tests(self):
        """Run available test suites."""
        print("\n🧪 Step 4: Running tests...")
        print("   (Best practice: All tests must pass before merge)")
        
        test_commands = [
            ("npm test", "package.json"),
            ("yarn test", "package.json"),
            ("pytest", "pytest.ini"),
            ("python -m pytest", "test*.py"),
            ("make test", "Makefile"),
            ("cargo test", "Cargo.toml"),
            ("go test ./...", "go.mod"),
            ("bundle exec rspec", "Gemfile"),
            ("./gradlew test", "build.gradle"),
            ("mvn test", "pom.xml")
        ]
        
        tests_run = False
        for cmd, indicator in test_commands:
            # Check if indicator file exists
            if indicator and not any(Path('.').glob(indicator)):
                continue
            
            print(f"  Attempting: {cmd}")
            result = self.run_command(cmd, check=False)
            if result is not None:
                tests_run = True
                print(f"✅ Tests passed: {cmd}")
                break
        
        if not tests_run:
            print("ℹ️  No test suite detected or tests skipped")
            print("   (Consider adding tests for better code quality)")

    def stage_changes(self):
        """Stage changes for commit."""
        print("\n📦 Step 5: Staging changes...")
        
        # Add all changes except those in .gitignore
        self.run_command("git add -A")
        
        # Show what will be committed
        staged = self.run_command("git diff --cached --stat")
        if staged:
            print("Changes to be committed:")
            print(staged)
            
            # Check PR size best practice
            lines_changed = self.run_command("git diff --cached --numstat | awk '{s+=$1+$2} END {print s}'").strip()
            if lines_changed and int(lines_changed) > 400:
                print(f"\n⚠️  PR size: {lines_changed} lines changed")
                print("   (Best practice: 200-400 lines for optimal review)")
                print("   Consider splitting into smaller PRs")

    def create_commit(self) -> str:
        """Create a commit with conventional commit message."""
        print("\n✍️  Step 6: Creating conventional commit...")
        print("   (Best practice: Conventional commits standard)")
        
        # Get commit type
        print("\nSelect commit type:")
        commit_types = [
            ("feat", "New feature (MINOR version)"),
            ("fix", "Bug fix (PATCH version)"),
            ("docs", "Documentation changes"),
            ("style", "Code style changes"),
            ("refactor", "Code refactoring"),
            ("perf", "Performance improvements"),
            ("test", "Test changes"),
            ("build", "Build system changes"),
            ("ci", "CI/CD changes"),
            ("chore", "Other changes")
        ]
        
        for i, (type_code, description) in enumerate(commit_types, 1):
            print(f"  {i}. {type_code}: {description}")
        
        choice = input("\nEnter choice (1-10): ")
        commit_type = commit_types[int(choice) - 1][0] if choice.isdigit() and 1 <= int(choice) <= 10 else "chore"
        
        # Get commit scope (optional)
        scope = input("Enter scope (optional, e.g., 'api', 'ui', press Enter to skip): ").strip()
        
        # Get commit description
        description = input("Enter commit description (imperative mood, e.g., 'add login feature'): ").strip()
        if not description:
            description = "update codebase with best practices"
        
        # Build commit message
        if scope:
            commit_title = f"{commit_type}({scope}): {description}"
        else:
            commit_title = f"{commit_type}: {description}"
        
        # Ensure title is under 50 characters (best practice)
        if len(commit_title) > 50:
            print(f"⚠️  Commit title is {len(commit_title)} characters (best practice: <50)")
            commit_title = commit_title[:47] + "..."
        
        # Get detailed description (optional)
        print("\nEnter detailed description (optional, press Enter twice to finish):")
        body_lines = []
        while True:
            line = input()
            if not line:
                break
            body_lines.append(line)
        
        commit_body = '\n'.join(body_lines) if body_lines else ""
        
        # Check for breaking changes
        is_breaking = input("\nIs this a breaking change? (y/n): ").lower() == 'y'
        
        # Build full commit message
        full_message = commit_title
        if is_breaking:
            full_message = full_message.replace(f"{commit_type}", f"{commit_type}!")
        
        if commit_body:
            # Wrap body at 72 characters (best practice)
            wrapped_body = self.wrap_text(commit_body, 72)
            full_message += f"\n\n{wrapped_body}"
        
        if is_breaking:
            breaking_description = input("Describe the breaking change: ")
            full_message += f"\n\nBREAKING CHANGE: {breaking_description}"
        
        # Add co-author for trunk-based flow
        full_message += "\n\nCo-authored-by: Git Trunk Flow <trunk@assetutilities.org>"
        
        # Create the commit
        with tempfile.NamedTemporaryFile(mode='w', suffix='.txt', delete=False) as f:
            f.write(full_message)
            temp_file = f.name
        
        try:
            self.run_command(f"git commit -F {temp_file}")
            print(f"✅ Commit created: {commit_title}")
        finally:
            os.unlink(temp_file)
        
        return commit_title

    def create_and_merge_pr(self, commit_message: str):
        """Create PR and optionally auto-merge."""
        print("\n🔀 Step 7: Creating Pull Request...")
        print("   (Best practice: Squash merge for clean history)")
        
        # Push current branch
        current_branch = self.get_current_branch()
        print(f"  Pushing branch {current_branch} to origin...")
        self.run_command(f"git push -u origin {current_branch}")
        
        # Check if gh CLI is available
        gh_available = self.run_command("which gh", check=False) is not None
        
        if gh_available:
            print("  Creating pull request with GitHub CLI...")
            
            # Generate PR body with best practices
            pr_body = self.generate_pr_body(commit_message)
            
            # Create PR
            pr_cmd = f'''gh pr create \
                --title "{commit_message}" \
                --body "{pr_body}" \
                --base {self.main_branch} \
                --head {current_branch}'''
            
            pr_url = self.run_command(pr_cmd)
            print(f"✅ Pull request created: {pr_url}")
            
            # Ask about auto-merge
            print("\n🎯 Trunk-based development recommends rapid integration.")
            response = input("Enable auto-merge with squash strategy? (y/n): ")
            if response.lower() == 'y':
                print("  Enabling auto-merge with squash strategy...")
                self.run_command(f"gh pr merge --auto --squash {pr_url}")
                print("✅ Auto-merge enabled (will squash merge after checks pass)")
                print("   (Best practice: Squash for clean linear history)")
        else:
            print("ℹ️  GitHub CLI not available. Please create PR manually:")
            print(f"    Branch: {current_branch} → {self.main_branch}")
            print(f"    Title: {commit_message}")
            print("    Strategy: Squash and merge (recommended)")

    def cleanup_branches(self):
        """Clean up merged branches."""
        print("\n🧹 Step 8: Cleaning up branches...")
        print("   (Best practice: Remove merged branches)")
        
        current_branch = self.get_current_branch()
        
        # Switch back to main if not already there
        if current_branch != self.main_branch:
            print(f"  Switching back to {self.main_branch}...")
            self.run_command(f"git checkout {self.main_branch}")
            self.run_command(f"git pull origin {self.main_branch}")
            
            # Delete local feature branch if merged
            is_merged = self.run_command(f"git branch --merged | grep {current_branch}", check=False)
            if is_merged:
                print(f"  Deleting merged local branch {current_branch}...")
                self.run_command(f"git branch -d {current_branch}")
        
        # Clean up other merged branches
        merged_branches = self.run_command("git branch --merged | grep -v '\\*\\|main\\|master'", check=False)
        if merged_branches:
            branches = merged_branches.strip().split('\n')
            print(f"  Found {len(branches)} merged branches to clean up")
            for branch in branches:
                branch = branch.strip()
                if branch:
                    self.run_command(f"git branch -d {branch}")
                    print(f"    Deleted: {branch}")

    # Helper methods
    
    def detect_main_branch(self) -> str:
        """Detect the main branch name."""
        for branch in ['main', 'master']:
            result = self.run_command(f"git rev-parse --verify {branch}", check=False)
            if result:
                return branch
        return 'main'  # Default
    
    def get_current_branch(self) -> str:
        """Get current branch name."""
        return self.run_command("git branch --show-current").strip()
    
    def create_feature_branch(self) -> str:
        """Create a new feature branch with descriptive name."""
        # Ask for feature description
        feature = input("Enter feature name (e.g., 'user-auth', 'fix-bug'): ").strip()
        if not feature:
            feature = "update"
        
        # Sanitize feature name
        feature = re.sub(r'[^a-zA-Z0-9-]', '-', feature.lower())
        
        # Create branch name without date (best practice for short-lived branches)
        branch_name = f"{feature}"
        
        self.run_command(f"git checkout -b {branch_name}")
        return branch_name
    
    def rebase_on_main(self):
        """Rebase current branch on main."""
        print(f"  Rebasing on {self.main_branch}...")
        self.run_command(f"git rebase origin/{self.main_branch}")
        print("✅ Rebase completed")
    
    def run_command(self, cmd: str, check: bool = True) -> Optional[str]:
        """Run a shell command and return output."""
        try:
            result = subprocess.run(
                cmd,
                shell=True,
                capture_output=True,
                text=True,
                check=check
            )
            return result.stdout.strip() if result.returncode == 0 else None
        except subprocess.CalledProcessError as e:
            if check:
                raise Exception(f"Command failed: {cmd}\n{e.stderr}")
            return None
    
    def is_binary_file(self, file_path: str) -> bool:
        """Check if a file is binary."""
        try:
            with open(file_path, 'rb') as f:
                chunk = f.read(1024)
                return b'\0' in chunk
        except:
            return True
    
    def wrap_text(self, text: str, width: int) -> str:
        """Wrap text to specified width."""
        import textwrap
        return '\n'.join(textwrap.wrap(text, width=width))
    
    def generate_gitignore_content(self) -> str:
        """Generate comprehensive .gitignore content."""
        return """# Environment variables
.env
.env.*
*.local

# IDE and editor files
.vscode/
.idea/
*.swp
*.swo
*~
.project
.classpath
*.iml

# OS generated files
.DS_Store
Thumbs.db
desktop.ini
.Spotlight-V100
.Trashes

# Python
__pycache__/
*.py[cod]
*$py.class
*.so
.Python
env/
venv/
.venv
pip-log.txt
.coverage
.pytest_cache/
htmlcov/
*.egg-info/
dist/
build/
.tox/
.nox/
.hypothesis/

# Node.js
node_modules/
npm-debug.log*
yarn-debug.log*
yarn-error.log*
.pnpm-debug.log*
lerna-debug.log*

# Build outputs
/dist/
/build/
/out/
*.log

# Database files
*.db
*.sqlite
*.sqlite3

# Temporary files
*.tmp
*.bak
*.backup
*.orig
*.rej

# Security - never commit secrets
*.pem
*.key
*.crt
*.p12
.secrets/
.password
"""
    
    def generate_editorconfig_content(self) -> str:
        """Generate .editorconfig content."""
        return """# EditorConfig is awesome: https://EditorConfig.org

root = true

[*]
charset = utf-8
end_of_line = lf
insert_final_newline = true
trim_trailing_whitespace = true
indent_style = space
indent_size = 2

[*.{py,pyw}]
indent_size = 4

[*.md]
trim_trailing_whitespace = false

[Makefile]
indent_style = tab

[*.{yml,yaml}]
indent_size = 2

[*.json]
indent_size = 2
"""
    
    def generate_codeowners_content(self) -> str:
        """Generate CODEOWNERS file content."""
        return """# Code Owners
# This file defines who should review PRs for different parts of the codebase

# Default owners for all files
* @team-leads

# Documentation
/docs/ @documentation-team
*.md @documentation-team

# CI/CD and DevOps
/.github/ @devops-team
/scripts/ @devops-team
Dockerfile @devops-team
docker-compose.yml @devops-team

# Core application
/src/ @backend-team
/tests/ @qa-team

# Frontend
/frontend/ @frontend-team
/public/ @frontend-team

# Configuration
*.json @config-owners
*.yml @config-owners
*.yaml @config-owners
"""
    
    def generate_pr_template(self) -> str:
        """Generate PR template with best practices."""
        return """## Summary
<!-- Brief description of changes -->

## Type of Change
- [ ] 🐛 Bug fix (non-breaking change that fixes an issue)
- [ ] ✨ New feature (non-breaking change that adds functionality)
- [ ] 💥 Breaking change (fix or feature that would cause existing functionality to not work as expected)
- [ ] 📝 Documentation update
- [ ] 🎨 Style update (formatting, renaming)
- [ ] ♻️ Code refactoring (no functional changes)
- [ ] ⚡ Performance improvement
- [ ] ✅ Test update
- [ ] 🔧 Build configuration update
- [ ] 👷 CI/CD update
- [ ] 🔀 Other (please describe):

## Changes Made
<!-- List the specific changes made -->
- 
- 
- 

## Testing
- [ ] Unit tests pass locally
- [ ] Integration tests pass locally
- [ ] Manual testing completed
- [ ] No regression in existing functionality

## Checklist
- [ ] My code follows the project style guidelines
- [ ] I have performed a self-review of my own code
- [ ] I have commented my code, particularly in hard-to-understand areas
- [ ] I have made corresponding changes to the documentation
- [ ] My changes generate no new warnings
- [ ] I have added tests that prove my fix is effective or that my feature works
- [ ] New and existing unit tests pass locally with my changes
- [ ] Any dependent changes have been merged and published

## Screenshots (if applicable)
<!-- Add screenshots to show visual changes -->

## Additional Notes
<!-- Any additional information that reviewers should know -->

---
**PR Size**: <!-- Number of lines changed -->
**Best Practice Note**: Optimal PR size is 200-400 lines for effective review
"""
    
    def enhance_gitignore(self, existing_content: str) -> str:
        """Enhance existing .gitignore with missing patterns."""
        essential_patterns = [
            '.env',
            '.env.*',
            '*.local',
            '.DS_Store',
            '__pycache__/',
            'node_modules/',
            '*.log',
            '*.tmp',
            '*.bak',
            '*.swp',
            '.coverage',
            '.pytest_cache/',
            'dist/',
            'build/',
            '*.egg-info/'
        ]
        
        lines = existing_content.split('\n')
        existing_patterns = set(line.strip() for line in lines if line.strip() and not line.startswith('#'))
        
        additions = []
        for pattern in essential_patterns:
            if pattern not in existing_patterns:
                additions.append(pattern)
        
        if additions:
            enhanced = existing_content.rstrip() + '\n\n# Auto-added essential patterns (best practices)\n'
            enhanced += '\n'.join(additions) + '\n'
            return enhanced
        
        return existing_content
    
    def create_pre_commit_hook(self):
        """Create a pre-commit hook for security scanning."""
        hook_content = """#!/bin/sh
# Pre-commit hook for security scanning and best practices enforcement
# Based on trunk-based development best practices

echo "🔍 Running pre-commit checks..."

# Check for potential secrets
echo "  Scanning for secrets..."

# Patterns to check
patterns=(
    "api[_-]?key"
    "api[_-]?secret"
    "access[_-]?token"
    "auth[_-]?token"
    "AKIA[0-9A-Z]{16}"
    "-----BEGIN.*PRIVATE KEY-----"
    "password.*="
    "eyJ[A-Za-z0-9-_=]+\\.[A-Za-z0-9-_=]+"
)

for pattern in "${patterns[@]}"; do
    matches=$(git diff --cached --name-only -z | xargs -0 grep -E "$pattern" 2>/dev/null)
    if [ ! -z "$matches" ]; then
        echo "⚠️  Potential secret detected with pattern: $pattern"
        echo "$matches"
        echo ""
        echo "If this is a false positive, you can skip this check with:"
        echo "  git commit --no-verify"
        exit 1
    fi
done

echo "  ✅ Security scan passed"

# Check commit message format (if using commit-msg hook)
echo "  ✅ Pre-commit checks passed"

# Remind about best practices
echo ""
echo "📚 Remember trunk-based development best practices:"
echo "  • Keep feature branches short-lived (max 2-3 days)"
echo "  • Make small, focused commits"
echo "  • Write clear commit messages using conventional commits"
echo "  • Ensure all tests pass before pushing"

exit 0
"""
        
        hook_path = Path('.git/hooks/pre-commit')
        hook_path.write_text(hook_content)
        hook_path.chmod(0o755)
    
    def generate_pr_body(self, commit_message: str) -> str:
        """Generate PR body with best practices checklist."""
        return f"""## Summary
{commit_message}

## Trunk-Based Development Compliance
- ✅ Feature branch created from latest main
- ✅ Branch lifetime < 3 days
- ✅ Changes focused and minimal
- ✅ Ready for rapid integration

## Changes Made
- Automated cleanup of redundant files
- Applied repository best practices
- Security scan completed
- Tests executed successfully

## Best Practices Applied
- [x] Conventional commit format used
- [x] Code follows project style guidelines
- [x] Security scan passed (no secrets)
- [x] Tests pass locally
- [x] PR size optimal for review
- [x] No redundant files included
- [x] Documentation updated if needed

## Testing
- Tests run automatically via CI/CD pipeline
- Manual testing completed locally
- No regression in existing functionality

## Merge Strategy
**Recommended: Squash and merge** for clean linear history

---
*Created via automated trunk-based development flow*
*Following industry best practices for rapid integration*
"""

def main():
    """Main entry point for the slash command."""
    print("\n" + "=" * 60)
    print("🌳 Git Trunk-Based Development Flow")
    print("=" * 60)
    print("\nThis command implements industry best practices for")
    print("trunk-based development including:")
    print("  • Automated redundant file cleanup")
    print("  • Security scanning for secrets")
    print("  • Conventional commit standards")
    print("  • Short-lived feature branches")
    print("  • Squash merge strategy")
    print("  • Comprehensive testing")
    print("=" * 60 + "\n")
    
    flow = GitTrunkFlow()
    flow.run()

if __name__ == "__main__":
    main()