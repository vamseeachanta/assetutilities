"""Cross-Repository Command Distributor.

Distributes Agent OS commands to multiple repositories in the ecosystem.
"""

import shutil
from pathlib import Path
from typing import List, Dict, Any


class CrossRepoDistributor:
    """Distribute Agent OS commands across repositories."""
    
    def __init__(self, base_github_path: Path = None):
        """Initialize cross-repo distributor.
        
        Args:
            base_github_path: Path to GitHub repositories base directory
        """
        self.base_github_path = base_github_path or Path("/mnt/github/github")
        self.assetutilities_path = self.base_github_path / "assetutilities"
        
        # List of target repositories
        self.target_repos = [
            "aceengineer-website",
            "aceengineercode", 
            "acma-projects",
            "ai-native-traditional-eng",
            "assethold",
            "client_projects",
            "digitalmodel",
            "energy",
            "frontierdeepwater",
            "OGManufacturing",
            "pyproject-starter",
            "rock-oil-field",
            "saipem",
            "teamresumes",
            "worldenergydata"
        ]
    
    def get_available_repositories(self) -> List[str]:
        """Get list of available repositories.
        
        Returns:
            List of repository names that exist and have Agent OS config
        """
        available_repos = []
        
        for repo in self.target_repos:
            repo_path = self.base_github_path / repo
            if repo_path.exists() and (repo_path / "CLAUDE.md").exists():
                available_repos.append(repo)
                
        return available_repos
    
    def distribute_command(self, command_name: str) -> Dict[str, Any]:
        """Distribute a command to all available repositories.
        
        Args:
            command_name: Name of the command to distribute
            
        Returns:
            Distribution results
        """
        results = {
            "command": command_name,
            "source_repo": "assetutilities",
            "distributed_to": [],
            "failed": [],
            "skipped": []
        }
        
        # Check if command exists in source
        source_command_path = self._get_command_path(command_name)
        if not source_command_path.exists():
            results["error"] = f"Command {command_name} not found in assetutilities"
            return results
        
        available_repos = self.get_available_repositories()
        
        for repo in available_repos:
            try:
                if self._install_command_to_repo(repo, command_name):
                    results["distributed_to"].append(repo)
                else:
                    results["skipped"].append(repo)
            except Exception as e:
                results["failed"].append({"repo": repo, "error": str(e)})
        
        return results
    
    def _get_command_path(self, command_name: str) -> Path:
        """Get path to command in assetutilities.
        
        Args:
            command_name: Name of the command
            
        Returns:
            Path to command file
        """
        command_file = f"{command_name.replace('-', '_')}.py"
        return self.assetutilities_path / "src" / "assetutilities" / "agent_os" / "commands" / command_file
    
    def _install_command_to_repo(self, repo_name: str, command_name: str) -> bool:
        """Install command to specific repository.
        
        Args:
            repo_name: Target repository name
            command_name: Command to install
            
        Returns:
            True if installed successfully
        """
        repo_path = self.base_github_path / repo_name
        
        # Create agent_os structure if it doesn't exist
        agent_os_path = repo_path / "agent_os"
        agent_os_path.mkdir(exist_ok=True)
        
        # Create commands directory
        commands_path = agent_os_path / "commands"
        commands_path.mkdir(exist_ok=True)
        
        # Copy command file with import fixes
        source_command = self._get_command_path(command_name)
        target_command = commands_path / source_command.name
        
        self._copy_command_with_fixed_imports(source_command, target_command)
        
        # Copy supporting modules if needed
        if command_name == "create-module-agent":
            self._copy_supporting_modules(repo_path)
        
        # Update CLAUDE.md
        self._update_claude_md(repo_path, command_name)
        
        return True
    
    def _copy_supporting_modules(self, repo_path: Path) -> None:
        """Copy supporting modules for create-module-agent.
        
        Args:
            repo_path: Target repository path
        """
        # Copy integration modules
        source_integration = self.assetutilities_path / "src" / "assetutilities" / "agent_os" / "integration"
        target_integration = repo_path / "agent_os" / "integration"
        
        if source_integration.exists():
            shutil.copytree(source_integration, target_integration, dirs_exist_ok=True)
            self._fix_module_imports(target_integration)
        
        # Copy CLI modules
        source_cli = self.assetutilities_path / "src" / "assetutilities" / "agent_os" / "cli"
        target_cli = repo_path / "agent_os" / "cli"
        
        if source_cli.exists():
            shutil.copytree(source_cli, target_cli, dirs_exist_ok=True)
            self._fix_module_imports(target_cli)
    
    def _fix_module_imports(self, module_dir: Path) -> None:
        """Fix imports in all Python files in a module directory.
        
        Args:
            module_dir: Directory containing Python modules
        """
        for py_file in module_dir.rglob("*.py"):
            with open(py_file, 'r') as f:
                content = f.read()
            
            # Fix assetutilities-specific imports
            content = content.replace(
                "from assetutilities.agent_os.commands.create_module_agent",
                "from agent_os.commands.create_module_agent" 
            )
            content = content.replace(
                "from assetutilities.agent_os.integration",
                "from agent_os.integration"
            )
            content = content.replace(
                "from assetutilities.agent_os.cli",
                "from agent_os.cli"
            )
            
            # Fix the problematic agent_oscommands import
            content = content.replace(
                "from agent_oscommands.create_module_agent",
                "from agent_os.commands.create_module_agent"
            )
            
            # Fix relative imports
            content = content.replace("from ..", "from agent_os")
            
            with open(py_file, 'w') as f:
                f.write(content)
    
    def _update_claude_md(self, repo_path: Path, command_name: str) -> None:
        """Update CLAUDE.md with command information.
        
        Args:
            repo_path: Repository path
            command_name: Command name
        """
        claude_md_path = repo_path / "CLAUDE.md"
        
        if not claude_md_path.exists():
            return
        
        # Read current content
        with open(claude_md_path, 'r') as f:
            content = f.read()
        
        # Add command reference if not already present
        command_ref = f"- **{command_name.title()}:** Available via `/{command_name}` command"
        
        if command_ref not in content:
            # Find the right place to insert
            if "## Available Commands" in content:
                # Add to existing commands section
                content = content.replace(
                    "## Available Commands",
                    f"## Available Commands\n\n{command_ref}"
                )
            else:
                # Add new commands section
                content += f"\n\n## Available Commands\n\n{command_ref}\n"
        
        # Write updated content
        with open(claude_md_path, 'w') as f:
            f.write(content)
    
    def create_usage_script(self, repo_path: Path, command_name: str) -> None:
        """Create usage script for the command.
        
        Args:
            repo_path: Repository path
            command_name: Command name
        """
        script_content = f"""#!/usr/bin/env python3
\"\"\"
{command_name.title()} Command for {repo_path.name}

This script provides access to the /{command_name} command.
\"\"\"

import sys
from pathlib import Path

# Add agent_os to path
agent_os_path = Path(__file__).parent / "agent_os"
sys.path.insert(0, str(agent_os_path))

from commands.{command_name.replace('-', '_')} import main

if __name__ == "__main__":
    sys.exit(main())
"""
        
        script_path = repo_path / f"{command_name}.py"
        with open(script_path, 'w') as f:
            f.write(script_content)
        
        # Make executable
        script_path.chmod(0o755)
    
    def distribute_create_module_agent(self) -> Dict[str, Any]:
        """Distribute the create-module-agent command.
        
        Returns:
            Distribution results
        """
        print("🚀 Distributing /create-module-agent to all repositories...")
        
        results = self.distribute_command("create-module-agent")
        
        # Create usage scripts for each repo
        for repo in results["distributed_to"]:
            repo_path = self.base_github_path / repo
            self.create_usage_script(repo_path, "create-module-agent")
        
        return results
    
    def create_distribution_summary(self, results: Dict[str, Any]) -> str:
        """Create summary of distribution results.
        
        Args:
            results: Distribution results
            
        Returns:
            Formatted summary string
        """
        summary = f"""
# Command Distribution Summary

## Command: /{results['command']}

### ✅ Successfully Distributed To ({len(results['distributed_to'])} repositories):
"""
        
        for repo in results["distributed_to"]:
            summary += f"- {repo}\n"
        
        if results["failed"]:
            summary += f"\n### ❌ Failed ({len(results['failed'])} repositories):\n"
            for failure in results["failed"]:
                summary += f"- {failure['repo']}: {failure['error']}\n"
        
        if results["skipped"]:
            summary += f"\n### ⏭️ Skipped ({len(results['skipped'])} repositories):\n"
            for repo in results["skipped"]:
                summary += f"- {repo}\n"
        
        summary += f"""
## Usage Instructions

In any of the distributed repositories, you can now use:

```bash
# Direct command execution
python create-module-agent.py my-agent --type infrastructure

# Or via agent_os module
python -m agent_os.commands.create_module_agent my-agent
```

## Integration Status

The command is now available across {len(results['distributed_to'])} repositories with:
- ✅ Full command functionality
- ✅ Enhanced specs integration  
- ✅ CLI interface with interactive mode
- ✅ Progress indicators and error handling
- ✅ Cross-repository references

Each repository can now create module agents that integrate with their specific context and documentation.
"""
        
        return summary
    
    def _copy_command_with_fixed_imports(self, source_path: Path, target_path: Path) -> None:
        """Copy command file and fix import paths.
        
        Args:
            source_path: Source command file
            target_path: Target command file
        """
        with open(source_path, 'r') as f:
            content = f.read()
        
        # Fix relative imports to work in distributed context
        content = content.replace(
            "from ..integration.enhanced_specs import EnhancedSpecsIntegration",
            "from agent_os.integration.enhanced_specs import EnhancedSpecsIntegration"
        )
        content = content.replace(
            "from ..cli.main import main_cli",
            "from agent_os.cli.main import main_cli"
        )
        content = content.replace(
            "from ..cli.interactive import InteractiveMode",
            "from agent_os.cli.interactive import InteractiveMode"
        )
        
        # Write fixed content
        with open(target_path, 'w') as f:
            f.write(content)