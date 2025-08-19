"""Command Installer for Cross-Repository Distribution."""

from pathlib import Path
from typing import Dict, Any


class CommandInstaller:
    """Install Agent OS commands in target repositories."""
    
    def __init__(self, target_repo_path: Path):
        """Initialize command installer.
        
        Args:
            target_repo_path: Path to target repository
        """
        self.target_repo_path = target_repo_path
        self.agent_os_path = target_repo_path / "agent_os"
    
    def install_command_infrastructure(self) -> bool:
        """Install basic command infrastructure.
        
        Returns:
            True if successful
        """
        try:
            # Create directory structure
            self.agent_os_path.mkdir(exist_ok=True)
            (self.agent_os_path / "commands").mkdir(exist_ok=True)
            (self.agent_os_path / "integration").mkdir(exist_ok=True)
            (self.agent_os_path / "cli").mkdir(exist_ok=True)
            
            # Create __init__.py files
            self._create_init_file(self.agent_os_path)
            self._create_init_file(self.agent_os_path / "commands")
            self._create_init_file(self.agent_os_path / "integration")
            self._create_init_file(self.agent_os_path / "cli")
            
            return True
            
        except Exception as e:
            print(f"Failed to install command infrastructure: {e}")
            return False
    
    def _create_init_file(self, directory: Path) -> None:
        """Create __init__.py file in directory.
        
        Args:
            directory: Directory to create __init__.py in
        """
        init_file = directory / "__init__.py"
        if not init_file.exists():
            with open(init_file, 'w') as f:
                f.write(f'"""Agent OS {directory.name} module."""\n')
    
    def create_repository_config(self) -> Dict[str, Any]:
        """Create repository-specific configuration.
        
        Returns:
            Repository configuration
        """
        repo_name = self.target_repo_path.name
        
        config = {
            "repository": {
                "name": repo_name,
                "agent_os_version": "1.0.0",
                "commands": [],
                "integrations": []
            },
            "cross_repo": {
                "source": "assetutilities",
                "sync_enabled": True,
                "auto_update": False
            }
        }
        
        return config
    
    def install_create_module_agent_wrapper(self) -> bool:
        """Install wrapper script for create-module-agent.
        
        Returns:
            True if successful
        """
        wrapper_content = f'''#!/usr/bin/env python3
"""
Create Module Agent Command for {self.target_repo_path.name}

This script provides the /create-module-agent functionality
using the Agent OS cross-repository system.
"""

import sys
from pathlib import Path

def main():
    """Main entry point."""
    try:
        # Try to import from local agent_os
        from agent_os.commands.create_module_agent import CreateModuleAgentCommand
        
        # Set base directory to current repository
        base_dir = Path.cwd()
        command = CreateModuleAgentCommand(base_dir=base_dir)
        
        result = command.execute(sys.argv)
        
        if result.success:
            print(f"✅ {{result.message}}")
            return 0
        else:
            print(f"❌ {{result.message}}")
            return 1
            
    except ImportError:
        print("❌ Agent OS commands not available in this repository.")
        print("💡 Run the distribution script from assetutilities to install commands.")
        return 1
    except Exception as e:
        print(f"❌ Error: {{e}}")
        return 1

if __name__ == "__main__":
    sys.exit(main())
'''
        
        wrapper_path = self.target_repo_path / "create-module-agent.py"
        
        try:
            with open(wrapper_path, 'w') as f:
                f.write(wrapper_content)
            
            # Make executable
            wrapper_path.chmod(0o755)
            
            return True
            
        except Exception as e:
            print(f"Failed to create wrapper script: {e}")
            return False