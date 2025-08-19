"""
Propagate Commands Module - Distribute slash commands across repositories
"""

import json
import shutil
from pathlib import Path
from typing import List, Dict, Optional
import logging
from datetime import datetime

# Configure logging
logging.basicConfig(level=logging.INFO, format='%(message)s')
logger = logging.getLogger(__name__)

class CommandPropagator:
    """Propagate slash commands across multiple repositories."""
    
    # Standard locations to look for custom commands
    COMMAND_LOCATIONS = [
        ".agent-os/commands",
        ".git-commands",
        "scripts/slash_commands",
        ".claude/commands",
        "slash_commands"
    ]
    
    def __init__(self, source_repo: Path, target_dir: Path, force: bool = False):
        self.source_repo = Path(source_repo)
        self.target_dir = Path(target_dir)
        self.force = force
        self.commands_found = {}
        self.command_registry = {}
        
    def discover_commands(self) -> Dict[str, Dict]:
        """Discover all custom commands in the source repository."""
        commands = {}
        
        for location in self.COMMAND_LOCATIONS:
            cmd_path = self.source_repo / location
            if cmd_path.exists():
                if cmd_path.is_dir():
                    # Look for Python files in the directory
                    for py_file in cmd_path.glob("*.py"):
                        if py_file.name != "__init__.py":
                            command_name = self._extract_command_name(py_file)
                            if command_name:
                                commands[command_name] = {
                                    "file": py_file,
                                    "location": location,
                                    "type": "python",
                                    "description": self._extract_description(py_file)
                                }
                elif cmd_path.suffix == ".py":
                    # Single Python file
                    command_name = self._extract_command_name(cmd_path)
                    if command_name:
                        commands[command_name] = {
                            "file": cmd_path,
                            "location": str(cmd_path.parent.relative_to(self.source_repo)),
                            "type": "python",
                            "description": self._extract_description(cmd_path)
                        }
        
        # Look for command registry file
        registry_file = self.source_repo / ".command-registry.json"
        if registry_file.exists():
            with open(registry_file, 'r') as f:
                self.command_registry = json.load(f)
        
        self.commands_found = commands
        return commands
    
    def _extract_command_name(self, file_path: Path) -> Optional[str]:
        """Extract command name from file content or filename."""
        try:
            content = file_path.read_text()
            
            # Look for command name in docstring or comments
            import re
            
            # Pattern 1: /command-name in docstring
            pattern1 = r'"""\s*/([a-z-]+)'
            match = re.search(pattern1, content)
            if match:
                return f"/{match.group(1)}"
            
            # Pattern 2: Command name in first line comment
            pattern2 = r'^#\s*/([a-z-]+)'
            match = re.search(pattern2, content, re.MULTILINE)
            if match:
                return f"/{match.group(1)}"
            
            # Fallback to filename
            name = file_path.stem.replace('_', '-')
            if name and not name.startswith('.'):
                return f"/{name}"
                
        except Exception as e:
            logger.debug(f"Could not extract command name from {file_path}: {e}")
        
        return None
    
    def _extract_description(self, file_path: Path) -> str:
        """Extract description from file docstring."""
        try:
            content = file_path.read_text()
            
            # Extract docstring
            import ast
            tree = ast.parse(content)
            docstring = ast.get_docstring(tree)
            
            if docstring:
                # Get first non-empty line after command name
                lines = docstring.split('\n')
                for line in lines:
                    line = line.strip()
                    if line and not line.startswith('/'):
                        return line[:100]  # Limit description length
            
        except Exception as e:
            logger.debug(f"Could not extract description from {file_path}: {e}")
        
        return "Custom slash command"
    
    def create_command_structure(self, repo_path: Path) -> bool:
        """Create the standard command structure in a repository."""
        try:
            # Create .agent-os/commands directory
            commands_dir = repo_path / ".agent-os" / "commands"
            commands_dir.mkdir(parents=True, exist_ok=True)
            
            # Create __init__.py
            init_file = commands_dir / "__init__.py"
            if not init_file.exists():
                init_file.write_text('"""Agent OS Custom Commands"""\n')
            
            # Create command wrapper
            wrapper_file = repo_path / "slash_commands.py"
            if not wrapper_file.exists() or self.force:
                wrapper_content = self._generate_command_wrapper()
                wrapper_file.write_text(wrapper_content)
                wrapper_file.chmod(0o755)
            
            return True
            
        except Exception as e:
            logger.error(f"Failed to create command structure: {e}")
            return False
    
    def _generate_command_wrapper(self) -> str:
        """Generate the command wrapper script."""
        return '''#!/usr/bin/env python
"""
Slash Command Wrapper - Auto-generated by AssetUtilities DevTools
This file provides a unified interface for all custom slash commands.
"""

import sys
import os
from pathlib import Path
import importlib.util

# Add command directory to path
COMMAND_DIR = Path(__file__).parent / ".agent-os/commands"
sys.path.insert(0, str(COMMAND_DIR))

def load_command(command_name: str):
    """Dynamically load a command module."""
    # Remove leading slash and convert to module name
    module_name = command_name.lstrip('/').replace('-', '_')
    module_path = COMMAND_DIR / f"{module_name}.py"
    
    if not module_path.exists():
        print(f"❌ Command {command_name} not found!")
        return None
    
    # Load the module
    spec = importlib.util.spec_from_file_location(module_name, module_path)
    if spec and spec.loader:
        module = importlib.util.module_from_spec(spec)
        sys.modules[module_name] = module
        spec.loader.exec_module(module)
        return module
    
    return None

def list_available_commands():
    """List all available commands."""
    print("📋 Available Slash Commands:")
    print("=" * 40)
    
    # Load command registry if exists
    registry_file = Path(__file__).parent / ".command-registry.json"
    if registry_file.exists():
        import json
        with open(registry_file, 'r') as f:
            registry = json.load(f)
            for cmd, info in registry.get("commands", {}).items():
                print(f"  {cmd:<20} - {info.get('description', 'No description')}")
    
    print()
    print("Usage: ./slash_commands.py <command> [args...]")

def main():
    """Main entry point for slash commands."""
    if len(sys.argv) < 2 or sys.argv[1] in ["--list", "-l", "list"]:
        list_available_commands()
        sys.exit(0)
    
    command = sys.argv[1]
    
    # Load and execute command
    module = load_command(command)
    if module and hasattr(module, 'main'):
        sys.argv = [command] + sys.argv[2:]
        sys.exit(module.main())
    else:
        print(f"❌ Unknown command: {command}")
        sys.exit(1)

if __name__ == "__main__":
    main()
'''
    
    def copy_command_files(self, repo_path: Path) -> List[str]:
        """Copy command files to the target repository."""
        copied_files = []
        
        commands_dir = repo_path / ".agent-os" / "commands"
        
        for cmd_name, cmd_info in self.commands_found.items():
            source_file = cmd_info["file"]
            
            # Generate target filename
            target_name = cmd_name.lstrip('/').replace('-', '_') + ".py"
            target_file = commands_dir / target_name
            
            try:
                # Copy the file
                shutil.copy2(source_file, target_file)
                copied_files.append(cmd_name)
                logger.debug(f"    Copied {cmd_name}")
                
            except Exception as e:
                logger.error(f"    Failed to copy {cmd_name}: {e}")
        
        return copied_files
    
    def create_command_registry(self, repo_path: Path, commands: List[str]):
        """Create or update the command registry file."""
        registry_file = repo_path / ".command-registry.json"
        
        # Load existing registry if exists
        existing_registry = {}
        if registry_file.exists() and not self.force:
            try:
                with open(registry_file, 'r') as f:
                    existing_registry = json.load(f)
            except:
                pass
        
        # Build new registry
        registry = {
            "version": "1.0.0",
            "last_updated": datetime.now().isoformat(),
            "source": str(self.source_repo),
            "commands": existing_registry.get("commands", {})
        }
        
        # Update with new commands
        for cmd_name in commands:
            if cmd_name in self.commands_found:
                cmd_info = self.commands_found[cmd_name]
                registry["commands"][cmd_name] = {
                    "description": cmd_info["description"],
                    "source": f".agent-os/commands/{cmd_name.lstrip('/').replace('-', '_')}.py",
                    "type": cmd_info["type"],
                    "last_updated": datetime.now().isoformat()
                }
        
        # Write registry
        with open(registry_file, 'w') as f:
            json.dump(registry, f, indent=2)
        
        return True
    
    def create_commands_documentation(self, repo_path: Path, commands: List[str]):
        """Create COMMANDS.md documentation file."""
        doc_file = repo_path / "COMMANDS.md"
        
        content = [
            "# Custom Slash Commands",
            "",
            f"Last updated: {datetime.now().strftime('%Y-%m-%d %H:%M')}",
            f"Propagated from: {self.source_repo.name}",
            "",
            "## Available Commands",
            ""
        ]
        
        for cmd_name in sorted(commands):
            if cmd_name in self.commands_found:
                cmd_info = self.commands_found[cmd_name]
                content.append(f"### `{cmd_name}`")
                content.append(f"{cmd_info['description']}")
                content.append("")
        
        content.extend([
            "## Usage",
            "",
            "```bash",
            "# List all available commands",
            "./slash_commands.py --list",
            "",
            "# Execute a specific command",
            "./slash_commands.py /modernize-deps",
            "```",
            ""
        ])
        
        doc_file.write_text('\n'.join(content))
        return True
    
    def propagate_to_repository(self, repo_path: Path) -> Dict:
        """Propagate commands to a single repository."""
        result = {
            "repo": repo_path.name,
            "success": False,
            "commands_installed": [],
            "errors": []
        }
        
        try:
            # Skip source repository
            if repo_path.resolve() == self.source_repo.resolve():
                result["success"] = True
                result["skipped"] = True
                return result
            
            # Step 1: Create command structure
            if not self.create_command_structure(repo_path):
                result["errors"].append("Failed to create command structure")
                return result
            
            # Step 2: Copy command files
            copied_commands = self.copy_command_files(repo_path)
            result["commands_installed"] = copied_commands
            
            # Step 3: Create command registry
            self.create_command_registry(repo_path, copied_commands)
            
            # Step 4: Create documentation
            self.create_commands_documentation(repo_path, copied_commands)
            
            result["success"] = True
            
        except Exception as e:
            result["errors"].append(str(e))
        
        return result


def find_repositories(base_dir: Path, include_non_git: bool = False) -> List[Path]:
    """Find all repositories in the given directory."""
    repos = []
    
    for item in base_dir.iterdir():
        if item.is_dir() and not item.name.startswith('.'):
            # Check if it's a git repository
            if (item / ".git").exists():
                repos.append(item)
            elif include_non_git:
                # Include non-git directories that look like projects
                if any((item / indicator).exists() for indicator in 
                       ["setup.py", "pyproject.toml", "package.json", "Makefile"]):
                    repos.append(item)
    
    return sorted(repos)