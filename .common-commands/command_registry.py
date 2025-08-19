#!/usr/bin/env python3
"""
Central Command Registry for AssetUtilities
All repositories MUST reference commands from here
"""

import sys
from pathlib import Path
from typing import Dict, List

class CentralCommandRegistry:
    """
    Central registry for all slash commands across repositories
    This is the SINGLE SOURCE OF TRUTH for common commands
    """
    
    # GitHub raw content URL for assetutilities
    GITHUB_BASE_URL = "https://raw.githubusercontent.com/username/assetutilities/main"
    
    # Available commands (MANDATORY for all repos)
    COMMANDS = {
        # Git Management Commands
        "/git-sync": {
            "description": "Sync repository with remote",
            "module": "git_manager",
            "function": "git_sync",
            "scope": "local"
        },
        "/git-sync-all": {
            "description": "Sync all repositories",
            "module": "git_manager",
            "function": "git_sync_all",
            "scope": "global"
        },
        "/git-commit": {
            "description": "Commit changes",
            "module": "git_manager",
            "function": "git_commit",
            "scope": "local"
        },
        "/git-commit-all": {
            "description": "Commit all repositories",
            "module": "git_manager",
            "function": "git_commit_all",
            "scope": "global"
        },
        "/git-pr": {
            "description": "Create pull request",
            "module": "git_manager",
            "function": "git_pr",
            "scope": "local"
        },
        "/git-pr-all": {
            "description": "Create PRs for all repos",
            "module": "git_manager",
            "function": "git_pr_all",
            "scope": "global"
        },
        "/git-clean": {
            "description": "Clean merged branches",
            "module": "git_manager",
            "function": "git_clean",
            "scope": "local"
        },
        "/git-clean-all": {
            "description": "Clean all repositories",
            "module": "git_manager",
            "function": "git_clean_all",
            "scope": "global"
        },
        "/git-flow": {
            "description": "Complete Git workflow",
            "module": "git_manager",
            "function": "git_flow",
            "scope": "local"
        },
        "/git-flow-all": {
            "description": "Complete workflow for all repos",
            "module": "git_manager",
            "function": "git_flow_all",
            "scope": "global"
        },
        
        # Agent Commands
        "/create-module-agent": {
            "description": "Create or update module agent",
            "module": "agent_manager",
            "function": "create_module_agent",
            "scope": "local"
        },
        "/create-spec": {
            "description": "Create specification",
            "module": "spec_manager",
            "function": "create_spec",
            "scope": "local"
        },
        "/execute-tasks": {
            "description": "Execute tasks from spec",
            "module": "task_executor",
            "function": "execute_tasks",
            "scope": "local"
        },
        
        # Utility Commands
        "/parallel-check": {
            "description": "Check parallel processing status",
            "module": "parallel_utils",
            "function": "check_parallel",
            "scope": "local"
        },
        "/health-check": {
            "description": "System health check",
            "module": "system_utils",
            "function": "health_check",
            "scope": "local"
        },
        "/update-from-central": {
            "description": "Update commands from AssetUtilities",
            "module": "updater",
            "function": "update_from_central",
            "scope": "local"
        }
    }
    
    @classmethod
    def get_command_url(cls, command: str) -> str:
        """Get GitHub URL for a command module"""
        cmd_info = cls.COMMANDS.get(command)
        if not cmd_info:
            raise ValueError(f"Unknown command: {command}")
        
        module = cmd_info["module"]
        return f"{cls.GITHUB_BASE_URL}/.common-commands/modules/{module}.py"
    
    @classmethod
    def fetch_command(cls, command: str) -> str:
        """Fetch command implementation from GitHub"""
        url = cls.get_command_url(command)
        
        try:
            import urllib.request
            with urllib.request.urlopen(url) as response:
                return response.read().decode('utf-8')
        except Exception as e:
            # Fallback to local if GitHub unavailable
            print(f"⚠️ Could not fetch from GitHub: {e}")
            return cls.get_local_command(command)
    
    @classmethod
    def get_local_command(cls, command: str) -> str:
        """Get command from local assetutilities"""
        cmd_info = cls.COMMANDS.get(command)
        if not cmd_info:
            raise ValueError(f"Unknown command: {command}")
        
        module_path = Path(__file__).parent / "modules" / f"{cmd_info['module']}.py"
        if module_path.exists():
            return module_path.read_text()
        return ""
    
    @classmethod
    def execute_command(cls, command: str, args: List[str] = None) -> int:
        """Execute a centralized command"""
        if command not in cls.COMMANDS:
            print(f"❌ Unknown command: {command}")
            print("Available commands:")
            for cmd, info in cls.COMMANDS.items():
                print(f"  {cmd}: {info['description']}")
            return 1
        
        cmd_info = cls.COMMANDS[command]
        
        # Fetch and execute command
        try:
            # For now, execute locally - can be enhanced to fetch from GitHub
            module_name = cmd_info["module"]
            function_name = cmd_info["function"]
            
            # Dynamic import and execution
            module = __import__(f"modules.{module_name}", fromlist=[function_name])
            func = getattr(module, function_name)
            
            return func(args or [])
        except Exception as e:
            print(f"❌ Error executing {command}: {e}")
            return 1
    
    @classmethod
    def list_commands(cls, scope: str = None) -> Dict:
        """List available commands"""
        if scope:
            return {k: v for k, v in cls.COMMANDS.items() if v["scope"] == scope}
        return cls.COMMANDS
    
    @classmethod
    def validate_installation(cls, repo_path: Path) -> bool:
        """Validate that a repo is properly configured for central commands"""
        required_files = [
            repo_path / ".command-link",
            repo_path / "CLAUDE.md"
        ]
        
        for file in required_files:
            if not file.exists():
                return False
            
            # Check if CLAUDE.md has AssetUtilities reference
            if file.name == "CLAUDE.md":
                content = file.read_text()
                if "@assetutilities:" not in content:
                    return False
        
        return True


def main():
    """Main entry point"""
    import sys
    
    if len(sys.argv) < 2:
        print("Usage: command_registry.py <command> [args...]")
        print("\nAvailable commands:")
        for cmd, info in CentralCommandRegistry.COMMANDS.items():
            print(f"  {cmd}: {info['description']}")
        return 1
    
    command = sys.argv[1]
    args = sys.argv[2:] if len(sys.argv) > 2 else []
    
    return CentralCommandRegistry.execute_command(command, args)


if __name__ == "__main__":
    sys.exit(main())
