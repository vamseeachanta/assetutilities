#!/usr/bin/env python3
"""Fix import paths in distributed create-module-agent commands."""

import sys
from pathlib import Path

# Add src to path
sys.path.insert(0, str(Path(__file__).parent / "src"))

from assetutilities.agent_os.cross_repo.distributor import CrossRepoDistributor

def main():
    """Fix import paths in all distributed repositories."""
    print("🔧 Fixing import paths in distributed /create-module-agent commands...")
    
    distributor = CrossRepoDistributor()
    available_repos = distributor.get_available_repositories()
    
    for repo in available_repos:
        repo_path = distributor.base_github_path / repo
        agent_os_cli_path = repo_path / "agent_os" / "cli"
        
        if agent_os_cli_path.exists():
            print(f"   • Fixing imports in {repo}")
            distributor._fix_module_imports(agent_os_cli_path)
        else:
            print(f"   • Skipping {repo} (no CLI module found)")
    
    print(f"✅ Fixed import paths in {len(available_repos)} repositories")

if __name__ == "__main__":
    main()