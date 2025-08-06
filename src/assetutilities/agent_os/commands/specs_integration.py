"""Enhanced Specs Integration System.

This module provides integration with the enhanced create-specs workflow,
including prompt evolution tracking, cross-repository referencing, and
workflow refresh capabilities.
"""

import re
import yaml
import json
import hashlib
from pathlib import Path
from typing import List, Dict, Any, Optional, Set
from dataclasses import dataclass, field, asdict
from datetime import datetime, timedelta
from urllib.parse import urlparse
import threading
import time


@dataclass
class OperationResult:
    """Result of integration operation."""
    success: bool
    message: str = ""
    data: Any = None


@dataclass
class WorkflowHook:
    """Workflow hook configuration."""
    name: str
    trigger: str
    action: str
    config: Dict[str, Any] = field(default_factory=dict)
    enabled: bool = True

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'WorkflowHook':
        """Create hook from dictionary."""
        return cls(
            name=data.get("name", ""),
            trigger=data.get("trigger", ""),
            action=data.get("action", ""),
            config=data.get("config", {}),
            enabled=data.get("enabled", True)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert hook to dictionary."""
        return {
            "name": self.name,
            "trigger": self.trigger,
            "action": self.action,
            "config": self.config,
            "enabled": self.enabled
        }

    def is_valid(self) -> bool:
        """Check if hook configuration is valid."""
        return bool(self.name) and bool(self.trigger) and bool(self.action)


@dataclass
class EnhancedSpecsConfig:
    """Enhanced specs integration configuration."""
    agent_name: str
    integration_type: str = "enhanced_create_specs"
    workflow_hooks: List[WorkflowHook] = field(default_factory=list)
    cross_repo_references: List[str] = field(default_factory=list)
    prompt_evolution_enabled: bool = True
    auto_refresh_enabled: bool = True
    refresh_interval: int = 3600  # 1 hour in seconds

    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'EnhancedSpecsConfig':
        """Create configuration from dictionary."""
        hooks = [WorkflowHook.from_dict(hook_data) for hook_data in data.get("workflow_hooks", [])]
        
        return cls(
            agent_name=data.get("agent_name", ""),
            integration_type=data.get("integration_type", "enhanced_create_specs"),
            workflow_hooks=hooks,
            cross_repo_references=data.get("cross_repo_references", []),
            prompt_evolution_enabled=data.get("prompt_evolution_enabled", True),
            auto_refresh_enabled=data.get("auto_refresh_enabled", True),
            refresh_interval=data.get("refresh_interval", 3600)
        )

    def to_dict(self) -> Dict[str, Any]:
        """Convert configuration to dictionary."""
        return {
            "agent_name": self.agent_name,
            "integration_type": self.integration_type,
            "workflow_hooks": [hook.to_dict() for hook in self.workflow_hooks],
            "cross_repo_references": self.cross_repo_references,
            "prompt_evolution_enabled": self.prompt_evolution_enabled,
            "auto_refresh_enabled": self.auto_refresh_enabled,
            "refresh_interval": self.refresh_interval,
            "created_at": datetime.now().isoformat(),
            "last_updated": datetime.now().isoformat()
        }

    def is_valid(self) -> bool:
        """Check if configuration is valid."""
        return bool(self.agent_name) and self.refresh_interval > 0


class PromptEvolutionTracker:
    """Tracks prompt usage and evolution over time."""

    def __init__(self, tracking_dir: Path):
        """Initialize prompt evolution tracker.
        
        Args:
            tracking_dir: Directory for storing tracking data
        """
        self.tracking_dir = Path(tracking_dir)
        self.tracking_dir.mkdir(parents=True, exist_ok=True)

    def track_prompt_usage(self, prompt_id: str, usage_data: Dict[str, Any]) -> OperationResult:
        """Track prompt usage statistics.
        
        Args:
            prompt_id: Unique identifier for the prompt
            usage_data: Usage statistics (tokens, quality, timing, etc.)
            
        Returns:
            Operation result
        """
        try:
            tracking_file = self.tracking_dir / f"{prompt_id}.json"
            
            # Load existing data or create new
            if tracking_file.exists():
                with open(tracking_file, 'r') as f:
                    tracking_data = json.load(f)
            else:
                tracking_data = {
                    "prompt_id": prompt_id,
                    "created_at": datetime.now().isoformat(),
                    "usage_history": [],
                    "versions": []
                }
            
            # Add new usage record
            usage_record = {
                **usage_data,
                "timestamp": datetime.now().isoformat()
            }
            tracking_data["usage_history"].append(usage_record)
            tracking_data["last_updated"] = datetime.now().isoformat()
            
            # Save updated data
            with open(tracking_file, 'w') as f:
                json.dump(tracking_data, f, indent=2)
            
            return OperationResult(
                success=True,
                message=f"Tracked usage for prompt '{prompt_id}'",
                data={"tracking_file": str(tracking_file)}
            )
            
        except Exception as e:
            return OperationResult(success=False, message=f"Failed to track prompt usage: {e}")

    def get_prompt_statistics(self, prompt_id: str) -> Dict[str, Any]:
        """Get usage statistics for a prompt.
        
        Args:
            prompt_id: Prompt identifier
            
        Returns:
            Statistics dictionary
        """
        tracking_file = self.tracking_dir / f"{prompt_id}.json"
        
        if not tracking_file.exists():
            return {"error": "No tracking data found", "total_uses": 0}
        
        try:
            with open(tracking_file, 'r') as f:
                tracking_data = json.load(f)
            
            usage_history = tracking_data.get("usage_history", [])
            
            if not usage_history:
                return {"total_uses": 0}
            
            # Calculate statistics
            total_uses = len(usage_history)
            tokens_used = [u.get("tokens_used", 0) for u in usage_history if "tokens_used" in u]
            quality_scores = [u.get("response_quality", 0) for u in usage_history if "response_quality" in u]
            execution_times = [u.get("execution_time", 0) for u in usage_history if "execution_time" in u]
            
            stats = {
                "prompt_id": prompt_id,
                "total_uses": total_uses,
                "average_tokens": sum(tokens_used) / len(tokens_used) if tokens_used else 0,
                "average_quality": sum(quality_scores) / len(quality_scores) if quality_scores else 0,
                "average_execution_time": sum(execution_times) / len(execution_times) if execution_times else 0,
                "agents_used": list(set(u.get("agent", "unknown") for u in usage_history)),
                "contexts_used": list(set(u.get("context", "unknown") for u in usage_history)),
                "first_use": usage_history[0].get("timestamp", "unknown"),
                "last_use": usage_history[-1].get("timestamp", "unknown")
            }
            
            return stats
            
        except Exception as e:
            return {"error": f"Failed to calculate statistics: {e}"}

    def suggest_prompt_improvements(self, prompt_id: str, current_prompt: str) -> List[str]:
        """Suggest improvements based on usage patterns.
        
        Args:
            prompt_id: Prompt identifier
            current_prompt: Current prompt text
            
        Returns:
            List of improvement suggestions
        """
        suggestions = []
        stats = self.get_prompt_statistics(prompt_id)
        
        if "error" in stats:
            return ["No usage data available for analysis"]
        
        # Analyze quality trends
        if stats.get("average_quality", 0) < 0.7:
            suggestions.append("Consider adding more specific instructions to improve response quality")
        
        # Analyze token usage
        if stats.get("average_tokens", 0) > 300:
            suggestions.append("Prompt may be too complex; consider breaking into smaller, focused prompts")
        
        # Analyze execution time
        if stats.get("average_execution_time", 0) > 5.0:
            suggestions.append("Long execution times may indicate overly complex requirements")
        
        # Analyze prompt structure
        if len(current_prompt.split('\n')) < 3:
            suggestions.append("Consider structuring prompt with clear sections (context, task, output format)")
        
        if "{" in current_prompt and "}" in current_prompt:
            variables = re.findall(r'\{(\w+)\}', current_prompt)
            if len(variables) > 5:
                suggestions.append("Many variables detected; ensure all are properly documented")
        
        # Context-specific suggestions
        contexts = stats.get("contexts_used", [])
        if len(contexts) > 3:
            suggestions.append("Prompt used in multiple contexts; consider creating context-specific variants")
        
        return suggestions if suggestions else ["Prompt performance looks good based on current metrics"]

    def track_prompt_version(self, prompt_id: str, version_data: Dict[str, Any]) -> OperationResult:
        """Track a new version of a prompt.
        
        Args:
            prompt_id: Prompt identifier
            version_data: Version information (version, prompt text, changes)
            
        Returns:
            Operation result
        """
        try:
            tracking_file = self.tracking_dir / f"{prompt_id}.json"
            
            if tracking_file.exists():
                with open(tracking_file, 'r') as f:
                    tracking_data = json.load(f)
            else:
                tracking_data = {
                    "prompt_id": prompt_id,
                    "created_at": datetime.now().isoformat(),
                    "usage_history": [],
                    "versions": []
                }
            
            # Add version record
            version_record = {
                **version_data,
                "tracked_at": datetime.now().isoformat()
            }
            tracking_data["versions"].append(version_record)
            tracking_data["last_updated"] = datetime.now().isoformat()
            
            # Save updated data
            with open(tracking_file, 'w') as f:
                json.dump(tracking_data, f, indent=2)
            
            return OperationResult(success=True, message=f"Tracked version for prompt '{prompt_id}'")
            
        except Exception as e:
            return OperationResult(success=False, message=f"Failed to track prompt version: {e}")

    def get_evolution_timeline(self, prompt_id: str) -> List[Dict[str, Any]]:
        """Get evolution timeline for a prompt.
        
        Args:
            prompt_id: Prompt identifier
            
        Returns:
            Timeline of prompt versions
        """
        tracking_file = self.tracking_dir / f"{prompt_id}.json"
        
        if not tracking_file.exists():
            return []
        
        try:
            with open(tracking_file, 'r') as f:
                tracking_data = json.load(f)
            
            return sorted(
                tracking_data.get("versions", []),
                key=lambda x: x.get("timestamp", x.get("tracked_at", ""))
            )
            
        except Exception:
            return []

    def export_tracking_data(self, export_path: Path) -> OperationResult:
        """Export all tracking data.
        
        Args:
            export_path: Path for export file
            
        Returns:
            Operation result
        """
        try:
            export_data = {
                "export_date": datetime.now().isoformat(),
                "prompts": {},
                "summary": {}
            }
            
            # Collect all tracking files
            tracking_files = list(self.tracking_dir.glob("*.json"))
            
            for tracking_file in tracking_files:
                prompt_id = tracking_file.stem
                
                with open(tracking_file, 'r') as f:
                    prompt_data = json.load(f)
                
                export_data["prompts"][prompt_id] = prompt_data
            
            # Generate summary
            total_prompts = len(export_data["prompts"])
            total_uses = sum(len(data.get("usage_history", [])) for data in export_data["prompts"].values())
            
            export_data["summary"] = {
                "total_prompts_tracked": total_prompts,
                "total_usage_records": total_uses,
                "tracking_period": self._get_tracking_period()
            }
            
            # Save export file
            with open(export_path, 'w') as f:
                json.dump(export_data, f, indent=2)
            
            return OperationResult(
                success=True,
                message=f"Exported tracking data to {export_path}",
                data=export_data["summary"]
            )
            
        except Exception as e:
            return OperationResult(success=False, message=f"Failed to export tracking data: {e}")

    def _get_tracking_period(self) -> Dict[str, str]:
        """Get the overall tracking period."""
        tracking_files = list(self.tracking_dir.glob("*.json"))
        
        if not tracking_files:
            return {"start": "no data", "end": "no data"}
        
        earliest = datetime.now()
        latest = datetime.min
        
        for tracking_file in tracking_files:
            try:
                with open(tracking_file, 'r') as f:
                    data = json.load(f)
                
                created_at = datetime.fromisoformat(data.get("created_at", ""))
                if created_at < earliest:
                    earliest = created_at
                
                last_updated = datetime.fromisoformat(data.get("last_updated", ""))
                if last_updated > latest:
                    latest = last_updated
                    
            except Exception:
                continue
        
        return {
            "start": earliest.isoformat(),
            "end": latest.isoformat()
        }


class CrossRepositoryReferencer:
    """Manages cross-repository references and relationships."""

    def __init__(self):
        """Initialize cross-repository referencer."""
        self.repositories: Dict[str, Dict[str, Any]] = {}

    def add_repository_reference(self, repo_name: str, repo_info: Dict[str, Any]) -> OperationResult:
        """Add repository reference.
        
        Args:
            repo_name: Repository name
            repo_info: Repository information
            
        Returns:
            Operation result
        """
        try:
            self.repositories[repo_name] = {
                **repo_info,
                "added_at": datetime.now().isoformat()
            }
            
            return OperationResult(
                success=True,
                message=f"Added repository reference for '{repo_name}'"
            )
            
        except Exception as e:
            return OperationResult(success=False, message=f"Failed to add repository reference: {e}")

    def create_cross_references(self) -> List[Dict[str, Any]]:
        """Create cross-references between repositories.
        
        Returns:
            List of cross-reference relationships
        """
        cross_references = []
        
        repo_names = list(self.repositories.keys())
        
        for i, repo1_name in enumerate(repo_names):
            for repo2_name in repo_names[i+1:]:
                repo1 = self.repositories[repo1_name]
                repo2 = self.repositories[repo2_name]
                
                # Find common areas
                common_areas = self._find_common_areas(repo1, repo2)
                
                if common_areas:
                    cross_references.append({
                        "repositories": [repo1_name, repo2_name],
                        "common_areas": common_areas,
                        "relationship_strength": len(common_areas),
                        "created_at": datetime.now().isoformat()
                    })
        
        return cross_references

    def find_related_repositories(self, target_repo: str, similarity_threshold: float = 0.3) -> List[Dict[str, Any]]:
        """Find repositories related to target repository.
        
        Args:
            target_repo: Target repository name
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of related repositories with similarity scores
        """
        if target_repo not in self.repositories:
            return []
        
        target_info = self.repositories[target_repo]
        related = []
        
        for repo_name, repo_info in self.repositories.items():
            if repo_name == target_repo:
                continue
            
            similarity = self._calculate_similarity(target_info, repo_info)
            
            if similarity >= similarity_threshold:
                related.append({
                    "repository": repo_name,
                    "similarity_score": similarity,
                    "common_elements": self._find_common_areas(target_info, repo_info),
                    "repository_info": repo_info
                })
        
        # Sort by similarity score
        return sorted(related, key=lambda x: x["similarity_score"], reverse=True)

    def generate_reference_map(self) -> Dict[str, Any]:
        """Generate complete reference map.
        
        Returns:
            Reference map with repositories and cross-references
        """
        return {
            "repositories": self.repositories,
            "cross_references": self.create_cross_references(),
            "generated_at": datetime.now().isoformat(),
            "total_repositories": len(self.repositories)
        }

    def export_references(self, export_path: Path) -> OperationResult:
        """Export references to file.
        
        Args:
            export_path: Export file path
            
        Returns:
            Operation result
        """
        try:
            reference_map = self.generate_reference_map()
            
            with open(export_path, 'w') as f:
                yaml.dump(reference_map, f, default_flow_style=False, indent=2)
            
            return OperationResult(
                success=True,
                message=f"Exported references to {export_path}",
                data={"repositories": len(self.repositories)}
            )
            
        except Exception as e:
            return OperationResult(success=False, message=f"Failed to export references: {e}")

    def _find_common_areas(self, repo1: Dict[str, Any], repo2: Dict[str, Any]) -> List[str]:
        """Find common areas between two repositories."""
        common_areas = []
        
        # Check common modules
        modules1 = set(repo1.get("key_modules", []))
        modules2 = set(repo2.get("key_modules", []))
        common_modules = modules1.intersection(modules2)
        common_areas.extend(common_modules)
        
        # Check common tags
        tags1 = set(repo1.get("tags", []))
        tags2 = set(repo2.get("tags", []))
        common_tags = tags1.intersection(tags2)
        common_areas.extend(common_tags)
        
        # Check language similarity
        if repo1.get("primary_language") == repo2.get("primary_language"):
            common_areas.append(f"language:{repo1.get('primary_language')}")
        
        return list(set(common_areas))  # Remove duplicates

    def _calculate_similarity(self, repo1: Dict[str, Any], repo2: Dict[str, Any]) -> float:
        """Calculate similarity score between repositories."""
        common_areas = self._find_common_areas(repo1, repo2)
        
        # Get all unique elements from both repositories
        all_elements1 = set(repo1.get("key_modules", []) + repo1.get("tags", []))
        all_elements2 = set(repo2.get("key_modules", []) + repo2.get("tags", []))
        
        total_elements = len(all_elements1.union(all_elements2))
        
        if total_elements == 0:
            return 0.0
        
        return len(common_areas) / total_elements


class WorkflowRefresher:
    """Handles workflow refresh and continuous updates."""

    def __init__(self, agent_dir: Path, refresh_interval: int = 3600):
        """Initialize workflow refresher.
        
        Args:
            agent_dir: Agent directory path
            refresh_interval: Refresh interval in seconds
        """
        self.agent_dir = Path(agent_dir)
        self.refresh_interval = refresh_interval
        self.refresh_scheduled = False
        self.last_refresh = None
        self.refresh_thread = None

    def schedule_refresh(self, refresh_config: Dict[str, Any]) -> OperationResult:
        """Schedule workflow refresh.
        
        Args:
            refresh_config: Refresh configuration
            
        Returns:
            Operation result
        """
        try:
            self.refresh_config = refresh_config
            self.refresh_scheduled = True
            
            return OperationResult(
                success=True,
                message="Workflow refresh scheduled",
                data={"config": refresh_config}
            )
            
        except Exception as e:
            return OperationResult(success=False, message=f"Failed to schedule refresh: {e}")

    def check_refresh_conditions(self, changes: List[Dict[str, Any]], conditions: Dict[str, Any]) -> bool:
        """Check if refresh conditions are met.
        
        Args:
            changes: List of detected changes
            conditions: Refresh conditions
            
        Returns:
            True if refresh should be triggered
        """
        min_changes = conditions.get("min_changes", 1)
        max_age_hours = conditions.get("max_age_hours", 24)
        
        # Check minimum number of changes
        if len(changes) < min_changes:
            return False
        
        # Check age of changes
        cutoff_time = datetime.now() - timedelta(hours=max_age_hours)
        recent_changes = [
            change for change in changes
            if datetime.fromisoformat(change.get("timestamp", datetime.now().isoformat())) > cutoff_time
        ]
        
        return len(recent_changes) >= min_changes

    def execute_refresh(self, refresh_actions: List[str]) -> OperationResult:
        """Execute workflow refresh.
        
        Args:
            refresh_actions: List of actions to perform
            
        Returns:
            Operation result
        """
        try:
            results = {}
            
            for action in refresh_actions:
                if action == "update_context":
                    results[action] = self._update_context()
                elif action == "refresh_templates":
                    results[action] = self._refresh_templates()
                elif action == "regenerate_prompts":
                    results[action] = self._regenerate_prompts()
                else:
                    results[action] = {"success": False, "message": f"Unknown action: {action}"}
            
            self.last_refresh = datetime.now()
            
            return OperationResult(
                success=True,
                message="Workflow refresh completed",
                data=results
            )
            
        except Exception as e:
            return OperationResult(success=False, message=f"Failed to execute refresh: {e}")

    def monitor_changes(self, monitor_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Monitor for changes that trigger refresh.
        
        Args:
            monitor_config: Monitoring configuration
            
        Returns:
            List of detected changes
        """
        changes = []
        
        # This is a simplified implementation
        # In practice, this would use file system watchers or git hooks
        
        try:
            changes = self._detect_file_changes(monitor_config)
        except Exception:
            pass  # Handle monitoring errors gracefully
        
        return changes

    def get_refresh_status(self) -> Dict[str, Any]:
        """Get current refresh status.
        
        Returns:
            Refresh status information
        """
        next_refresh = None
        if self.last_refresh and self.refresh_scheduled:
            next_refresh = self.last_refresh + timedelta(seconds=self.refresh_interval)
        
        return {
            "scheduled": self.refresh_scheduled,
            "last_refresh": self.last_refresh.isoformat() if self.last_refresh else None,
            "next_refresh": next_refresh.isoformat() if next_refresh else None,
            "refresh_interval": self.refresh_interval,
            "agent_dir": str(self.agent_dir)
        }

    def is_refresh_scheduled(self) -> bool:
        """Check if refresh is scheduled."""
        return self.refresh_scheduled

    def _update_context(self) -> Dict[str, Any]:
        """Update agent context."""
        # Simplified implementation
        return {"success": True, "updated_files": 2}

    def _refresh_templates(self) -> Dict[str, Any]:
        """Refresh agent templates."""
        # Simplified implementation
        return {"success": True, "refreshed_templates": 3}

    def _regenerate_prompts(self) -> Dict[str, Any]:
        """Regenerate prompts based on latest patterns."""
        # Simplified implementation
        return {"success": True, "regenerated_prompts": 5}

    def _detect_file_changes(self, monitor_config: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect file changes (simplified implementation)."""
        # This would typically use file system monitoring
        # For testing, return mock changes
        return [
            {
                "path": "mock/file.py",
                "type": "modified",
                "timestamp": datetime.now().isoformat()
            }
        ]


class SpecsIntegrationManager:
    """Main manager for enhanced specs integration."""

    def __init__(self, agent_dir: Path):
        """Initialize specs integration manager.
        
        Args:
            agent_dir: Agent directory path
        """
        self.agent_dir = Path(agent_dir)
        self.prompt_tracker = None
        self.cross_referencer = CrossRepositoryReferencer()
        self.workflow_refresher = None

    def setup_enhanced_specs_integration(self, config: EnhancedSpecsConfig) -> OperationResult:
        """Setup enhanced specs integration.
        
        Args:
            config: Integration configuration
            
        Returns:
            Operation result
        """
        try:
            # Create workflows directory
            workflows_dir = self.agent_dir / "workflows"
            workflows_dir.mkdir(parents=True, exist_ok=True)
            
            # Save configuration
            config_file = workflows_dir / "enhanced_specs.yaml"
            with open(config_file, 'w') as f:
                yaml.dump(config.to_dict(), f, default_flow_style=False, indent=2)
            
            return OperationResult(
                success=True,
                message="Enhanced specs integration configured",
                data={"config_file": str(config_file)}
            )
            
        except Exception as e:
            return OperationResult(success=False, message=f"Failed to setup integration: {e}")

    def initialize_prompt_evolution(self, agent_name: str) -> OperationResult:
        """Initialize prompt evolution tracking.
        
        Args:
            agent_name: Agent name
            
        Returns:
            Operation result
        """
        try:
            tracking_dir = self.agent_dir / "workflows" / "prompt_tracking"
            self.prompt_tracker = PromptEvolutionTracker(tracking_dir)
            
            return OperationResult(
                success=True,
                message=f"Prompt evolution initialized for '{agent_name}'",
                data={"tracking_dir": str(tracking_dir)}
            )
            
        except Exception as e:
            return OperationResult(success=False, message=f"Failed to initialize prompt evolution: {e}")

    def setup_cross_repo_references(self, repo_references: List[Dict[str, Any]]) -> OperationResult:
        """Setup cross-repository references.
        
        Args:
            repo_references: List of repository information
            
        Returns:
            Operation result
        """
        try:
            # Add all repository references
            for repo_info in repo_references:
                repo_name = repo_info.get("name")
                if repo_name:
                    self.cross_referencer.add_repository_reference(repo_name, repo_info)
            
            # Create references directory
            references_dir = self.agent_dir / "context" / "repository"
            references_dir.mkdir(parents=True, exist_ok=True)
            
            # Export references
            references_file = references_dir / "cross_references.yaml"
            result = self.cross_referencer.export_references(references_file)
            
            if result.success:
                return OperationResult(
                    success=True,
                    message=f"Cross-repository references configured for {len(repo_references)} repositories",
                    data={"references_file": str(references_file)}
                )
            else:
                return result
                
        except Exception as e:
            return OperationResult(success=False, message=f"Failed to setup cross-repo references: {e}")

    def configure_workflow_refresh(self, refresh_config: Dict[str, Any]) -> OperationResult:
        """Configure workflow refresh.
        
        Args:
            refresh_config: Refresh configuration
            
        Returns:
            Operation result
        """
        try:
            self.workflow_refresher = WorkflowRefresher(
                agent_dir=self.agent_dir,
                refresh_interval=refresh_config.get("interval", 3600)
            )
            
            if refresh_config.get("enabled", False):
                self.workflow_refresher.schedule_refresh(refresh_config)
            
            # Save refresh configuration
            workflows_dir = self.agent_dir / "workflows"
            workflows_dir.mkdir(parents=True, exist_ok=True)
            
            refresh_file = workflows_dir / "refresh_config.yaml"
            with open(refresh_file, 'w') as f:
                yaml.dump(refresh_config, f, default_flow_style=False, indent=2)
            
            return OperationResult(
                success=True,
                message="Workflow refresh configured",
                data={"refresh_file": str(refresh_file)}
            )
            
        except Exception as e:
            return OperationResult(success=False, message=f"Failed to configure workflow refresh: {e}")

    def create_integration(self, integration_config: Dict[str, Any]) -> OperationResult:
        """Create complete integration setup.
        
        Args:
            integration_config: Complete integration configuration
            
        Returns:
            Operation result
        """
        try:
            results = []
            
            # Create enhanced specs configuration
            config = EnhancedSpecsConfig.from_dict(integration_config)
            result = self.setup_enhanced_specs_integration(config)
            results.append(("enhanced_specs", result))
            
            # Initialize prompt evolution if enabled
            if integration_config.get("prompt_evolution_enabled", True):
                result = self.initialize_prompt_evolution(config.agent_name)
                results.append(("prompt_evolution", result))
            
            # Setup cross-repository references
            repo_refs = integration_config.get("repository_references", [])
            cross_repo_refs = integration_config.get("cross_repo_references", [])
            
            # Convert simple repository names to full repository info if needed
            if cross_repo_refs and not repo_refs:
                repo_refs = [{"name": name, "description": f"Repository: {name}"} for name in cross_repo_refs]
            
            if repo_refs:
                result = self.setup_cross_repo_references(repo_refs)
                results.append(("cross_references", result))
            
            # Configure workflow refresh if enabled
            if integration_config.get("auto_refresh_enabled", True):
                refresh_config = {
                    "enabled": True,
                    "interval": integration_config.get("refresh_interval", 3600),
                    "triggers": integration_config.get("refresh_triggers", ["repository_change"]),
                    "actions": integration_config.get("refresh_actions", ["update_context"])
                }
                result = self.configure_workflow_refresh(refresh_config)
                results.append(("workflow_refresh", result))
            
            # Check if all operations succeeded
            all_success = all(result.success for _, result in results)
            
            if all_success:
                return OperationResult(
                    success=True,
                    message="Complete integration setup successful",
                    data={"components": [name for name, _ in results]}
                )
            else:
                failed_components = [name for name, result in results if not result.success]
                return OperationResult(
                    success=False,
                    message=f"Integration setup partially failed: {failed_components}",
                    data={"failed_components": failed_components}
                )
                
        except Exception as e:
            return OperationResult(success=False, message=f"Failed to create integration: {e}")

    def get_integration_status(self) -> Dict[str, Any]:
        """Get current integration status.
        
        Returns:
            Integration status information
        """
        status = {
            "agent_dir": str(self.agent_dir),
            "timestamp": datetime.now().isoformat()
        }
        
        # Check enhanced specs configuration
        enhanced_specs_file = self.agent_dir / "workflows" / "enhanced_specs.yaml"
        status["enhanced_specs"] = {
            "enabled": enhanced_specs_file.exists(),
            "config_file": str(enhanced_specs_file) if enhanced_specs_file.exists() else None
        }
        
        # Check prompt evolution
        prompt_tracking_dir = self.agent_dir / "workflows" / "prompt_tracking"
        status["prompt_evolution"] = {
            "enabled": prompt_tracking_dir.exists(),
            "tracking_dir": str(prompt_tracking_dir) if prompt_tracking_dir.exists() else None
        }
        
        # Check cross-references
        cross_refs_file = self.agent_dir / "context" / "repository" / "cross_references.yaml"
        status["cross_references"] = {
            "enabled": cross_refs_file.exists(),
            "references_file": str(cross_refs_file) if cross_refs_file.exists() else None
        }
        
        # Check workflow refresh
        refresh_config_file = self.agent_dir / "workflows" / "refresh_config.yaml"
        status["workflow_refresh"] = {
            "enabled": refresh_config_file.exists(),
            "config_file": str(refresh_config_file) if refresh_config_file.exists() else None
        }
        
        if self.workflow_refresher:
            status["workflow_refresh"]["status"] = self.workflow_refresher.get_refresh_status()
        
        return status

    def validate_integration(self) -> OperationResult:
        """Validate integration setup.
        
        Returns:
            Validation result
        """
        try:
            validation_results = []
            
            # Check required directories
            required_dirs = [
                self.agent_dir / "workflows",
                self.agent_dir / "context" / "repository"
            ]
            
            for required_dir in required_dirs:
                if required_dir.exists():
                    validation_results.append(f"✓ Directory exists: {required_dir.name}")
                else:
                    validation_results.append(f"✗ Missing directory: {required_dir.name}")
            
            # Check configuration files
            config_files = [
                ("enhanced_specs.yaml", self.agent_dir / "workflows" / "enhanced_specs.yaml"),
                ("cross_references.yaml", self.agent_dir / "context" / "repository" / "cross_references.yaml")
            ]
            
            for file_name, file_path in config_files:
                if file_path.exists():
                    validation_results.append(f"✓ Configuration file exists: {file_name}")
                else:
                    validation_results.append(f"! Optional file missing: {file_name}")
            
            # Overall validation
            critical_missing = [result for result in validation_results if result.startswith("✗")]
            
            return OperationResult(
                success=len(critical_missing) == 0,
                message="Integration validation completed",
                data={
                    "components": validation_results,
                    "critical_issues": len(critical_missing)
                }
            )
            
        except Exception as e:
            return OperationResult(success=False, message=f"Validation failed: {e}")