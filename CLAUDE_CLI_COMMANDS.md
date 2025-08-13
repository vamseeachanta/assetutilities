# 🚀 Claude CLI Slash Commands Integration

## Quick Start

All slash commands are now easily accessible through the `slash` wrapper:

```bash
# From any directory:
/mnt/github/github/assetutilities/slash <command> [options]

# Or add to PATH:
export PATH="/mnt/github/github/assetutilities:$PATH"
slash <command> [options]
```

## 🔍 Search & Discovery

### Find Commands Easily

```bash
# Search for specific commands
slash search-commands git           # Find git-related commands
slash search-commands --hooks       # Commands with hook support
slash search-commands --multi-repo  # Multi-repository commands

# List all available commands
slash --list                        # Show all commands
slash search-commands --categories  # Organized by category

# Get detailed help
slash search-commands --help-for /git-trunk-flow
slash git-trunk-flow --help
```

## 📚 Available Commands

### Core Workflow Commands

```bash
# Git operations
slash git-trunk-flow          # Complete git workflow
slash git-trunk-flow-enhanced # With hooks and improvements
slash git-sync               # Sync with remote

# Code organization
slash organize-structure     # Organize project structure
slash modernize-deps        # Update dependencies

# Testing
slash test-automation       # Run tests across repos
slash test-automation-enhanced # Enhanced testing
```

### Ecosystem Management

```bash
# Command distribution
slash propagate-commands    # Push commands to all repos
slash sync-all-commands     # Bidirectional sync
slash install-ecosystem-awareness # Add AI awareness
```

## 🎯 Claude CLI Usage Patterns

### 1. Quick Command Execution

When Claude needs to run a slash command:

```python
# In Claude's Python environment
import subprocess

# Run any slash command
result = subprocess.run([
    "/mnt/github/github/assetutilities/slash",
    "git-trunk-flow"
], capture_output=True, text=True)
```

### 2. Command Discovery

Claude can discover available commands:

```python
# Search for relevant commands
subprocess.run([
    "/mnt/github/github/assetutilities/slash",
    "search-commands",
    "git"
])

# List all commands
subprocess.run([
    "/mnt/github/github/assetutilities/slash",
    "--list"
])
```

### 3. Interactive Help

Get help for any command:

```python
# Get command help
subprocess.run([
    "/mnt/github/github/assetutilities/slash",
    "git-trunk-flow",
    "--help"
])
```

## 🔧 Setup for Optimal Use

### 1. Add to PATH (Optional)

```bash
# Add to .bashrc or .zshrc
export PATH="/mnt/github/github/assetutilities:$PATH"

# Now use directly
slash git-trunk-flow
slash search-commands
```

### 2. Enable Tab Completion

```bash
# Source the completion script
source /mnt/github/github/assetutilities/slash_completion.bash

# Now use tab completion
slash <TAB><TAB>  # Shows all commands
slash git-<TAB>    # Shows git commands
```

### 3. Create Alias (Optional)

```bash
# Add to .bashrc or .zshrc
alias s='/mnt/github/github/assetutilities/slash'

# Use short alias
s git-trunk-flow
s search-commands git
```

## 📖 Command Categories

### 🔀 Git & Version Control
- `/git-trunk-flow` - Complete git workflow
- `/git-trunk-flow-enhanced` - Enhanced with hooks
- `/git-sync` - Sync with remote

### 📦 Dependencies & Structure
- `/modernize-deps` - Update dependencies
- `/organize-structure` - Organize project

### 🧪 Testing & Quality
- `/test-automation` - Automated testing
- `/test-automation-enhanced` - Enhanced testing

### 🔄 Command Distribution
- `/propagate-commands` - Push to repos
- `/sync-all-commands` - Bidirectional sync
- `/install-ecosystem-awareness` - AI integration

## 💡 Advanced Features

### Search with Filters

```bash
# Find commands by feature
slash search-commands --hooks --multi-repo

# Find by tags
slash search-commands --tags git testing

# Find in specific repo
slash search-commands --repo assetutilities

# Export command registry
slash search-commands --export commands.json
```

### Command Help System

```bash
# Detailed help for any command
slash search-commands --help-for /git-trunk-flow

# Show command categories
slash search-commands --categories

# Detailed search results
slash search-commands git --detailed
```

## 🤖 AI Agent Integration

When Claude or other AI agents need to:

1. **Find a command**: Use `slash search-commands <query>`
2. **Run a command**: Use `slash <command-name> [options]`
3. **Get help**: Use `slash <command> --help`
4. **List all**: Use `slash --list`

### Example Claude Code

```python
# Claude can use this pattern
def run_slash_command(command, *args):
    """Run a slash command from Claude."""
    import subprocess
    
    cmd = ["/mnt/github/github/assetutilities/slash", command]
    cmd.extend(args)
    
    result = subprocess.run(
        cmd,
        capture_output=True,
        text=True,
        cwd="/mnt/github/github"  # Or specific repo
    )
    
    if result.returncode == 0:
        print(f"✅ {command} completed successfully")
        print(result.stdout)
    else:
        print(f"❌ {command} failed")
        print(result.stderr)
    
    return result.returncode

# Usage
run_slash_command("git-trunk-flow")
run_slash_command("search-commands", "git", "--detailed")
run_slash_command("modernize-deps", "--dry-run")
```

## 📊 Command Registry

The system maintains a searchable registry of all commands with:
- Descriptions and usage
- Tags and categories
- Features (hooks, multi-repo)
- Examples and help
- File locations and metadata

Access the registry:
```bash
# Export registry
slash search-commands --export registry.json

# View by category
slash search-commands --categories

# Search with filters
slash search-commands --hooks --tags git
```

## 🚀 Benefits

1. **Universal Access**: Commands available from any directory
2. **Easy Discovery**: Intelligent search and categorization
3. **Claude Integration**: Direct access from Claude CLI
4. **Tab Completion**: Fast command entry
5. **Help System**: Comprehensive documentation
6. **Cross-Repo**: Commands work across all repositories

---

*The slash command system makes all commands easily discoverable and executable from Claude CLI and terminal!*