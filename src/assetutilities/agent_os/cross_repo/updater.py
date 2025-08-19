"""Command Updater for Cross-Repository Distribution."""

import hashlib
from pathlib import Path
from typing import Dict, Any


class CommandUpdater:
    """Update Agent OS commands across repositories."""
    
    def __init__(self, source_repo_path: Path):
        """Initialize command updater.
        
        Args:
            source_repo_path: Path to source repository (assetutilities)
        """
        self.source_repo_path = source_repo_path
        self.github_base = source_repo_path.parent
    
    def check_command_version(self, command_name: str, target_repo: str) -> Dict[str, Any]:
        """Check if command needs updating in target repository.
        
        Args:
            command_name: Name of command to check
            target_repo: Target repository name
            
        Returns:
            Version check results
        """
        source_path = self._get_source_command_path(command_name)
        target_path = self._get_target_command_path(command_name, target_repo)
        
        result = {
            "command": command_name,
            "target_repo": target_repo,
            "needs_update": False,
            "source_exists": source_path.exists(),
            "target_exists": target_path.exists(),
            "source_hash": None,
            "target_hash": None
        }
        
        if not source_path.exists():
            result["error"] = "Source command not found"
            return result
        
        # Calculate source hash
        result["source_hash"] = self._calculate_file_hash(source_path)
        
        if target_path.exists():
            result["target_hash"] = self._calculate_file_hash(target_path)
            result["needs_update"] = result["source_hash"] != result["target_hash"]
        else:
            result["needs_update"] = True
        
        return result
    
    def update_command(self, command_name: str, target_repo: str) -> Dict[str, Any]:
        """Update command in target repository.
        
        Args:
            command_name: Name of command to update
            target_repo: Target repository name
            
        Returns:
            Update results
        """
        result = {
            "command": command_name,
            "target_repo": target_repo,
            "updated": False,
            "error": None
        }
        
        try:
            from .distributor import CrossRepoDistributor
            
            distributor = CrossRepoDistributor(self.github_base)
            install_result = distributor._install_command_to_repo(target_repo, command_name)
            
            result["updated"] = install_result
            
        except Exception as e:
            result["error"] = str(e)
        
        return result
    
    def update_all_repositories(self, command_name: str) -> Dict[str, Any]:
        """Update command in all repositories.
        
        Args:
            command_name: Name of command to update
            
        Returns:
            Update results for all repositories
        """
        from .distributor import CrossRepoDistributor
        
        distributor = CrossRepoDistributor(self.github_base)
        available_repos = distributor.get_available_repositories()
        
        results = {
            "command": command_name,
            "total_repos": len(available_repos),
            "updated": [],
            "up_to_date": [],
            "failed": []
        }
        
        for repo in available_repos:
            version_check = self.check_command_version(command_name, repo)
            
            if version_check.get("error"):
                results["failed"].append({
                    "repo": repo,
                    "error": version_check["error"]
                })
            elif version_check["needs_update"]:
                update_result = self.update_command(command_name, repo)
                if update_result["updated"]:
                    results["updated"].append(repo)
                else:
                    results["failed"].append({
                        "repo": repo,
                        "error": update_result.get("error", "Update failed")
                    })
            else:
                results["up_to_date"].append(repo)
        
        return results
    
    def _get_source_command_path(self, command_name: str) -> Path:
        """Get path to source command.
        
        Args:
            command_name: Command name
            
        Returns:
            Path to source command
        """
        command_file = f"{command_name.replace('-', '_')}.py"
        return (self.source_repo_path / "src" / "assetutilities" / 
                "agent_os" / "commands" / command_file)
    
    def _get_target_command_path(self, command_name: str, target_repo: str) -> Path:
        """Get path to target command.
        
        Args:
            command_name: Command name
            target_repo: Target repository name
            
        Returns:
            Path to target command
        """
        command_file = f"{command_name.replace('-', '_')}.py"
        return (self.github_base / target_repo / "agent_os" / 
                "commands" / command_file)
    
    def _calculate_file_hash(self, file_path: Path) -> str:
        """Calculate SHA-256 hash of file.
        
        Args:
            file_path: Path to file
            
        Returns:
            SHA-256 hash string
        """
        hasher = hashlib.sha256()
        
        with open(file_path, 'rb') as f:
            for chunk in iter(lambda: f.read(4096), b""):
                hasher.update(chunk)
        
        return hasher.hexdigest()
    
    def create_update_summary(self, results: Dict[str, Any]) -> str:
        """Create summary of update results.
        
        Args:
            results: Update results
            
        Returns:
            Formatted summary string
        """
        summary = f"""
# Command Update Summary

## Command: /{results['command']}
## Total Repositories: {results['total_repos']}

### ✅ Updated ({len(results['updated'])} repositories):
"""
        
        for repo in results["updated"]:
            summary += f"- {repo}\n"
        
        if results["up_to_date"]:
            summary += f"\n### ✅ Already Up-to-Date ({len(results['up_to_date'])} repositories):\n"
            for repo in results["up_to_date"]:
                summary += f"- {repo}\n"
        
        if results["failed"]:
            summary += f"\n### ❌ Failed ({len(results['failed'])} repositories):\n"
            for failure in results["failed"]:
                summary += f"- {failure['repo']}: {failure['error']}\n"
        
        summary += "\n## Status: Update Complete ✅\n"
        
        return summary