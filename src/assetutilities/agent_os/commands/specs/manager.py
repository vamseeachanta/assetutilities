# ABOUTME: Top-level manager coordinating all specs integration operations.
# ABOUTME: Extracted from specs_integration.py SpecsIntegrationManager class.
"""Manages the overall specs integration workflow."""

import yaml
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from assetutilities.agent_os.commands.specs.models import EnhancedSpecsConfig, OperationResult
from assetutilities.agent_os.commands.specs.referencer import CrossRepositoryReferencer
from assetutilities.agent_os.commands.specs.refresher import WorkflowRefresher
from assetutilities.agent_os.commands.specs.tracker import PromptEvolutionTracker

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