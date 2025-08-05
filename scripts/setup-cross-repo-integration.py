#!/usr/bin/env python3
"""
Cross-Repository Integration Setup Script for AssetUtilities Hub.

This script sets up cross-repository integration for client repositories,
configuring them to use shared components and sub-agents from the AssetUtilities hub.

Features:
- Automatic detection of repository type and requirements
- Interactive configuration with intelligent defaults
- Validation of hub accessibility and compatibility
- Setup of local configuration files and directory structure
- Integration testing and validation

Author: AssetUtilities Hub Team
Created: 2025-08-05
Version: 1.0.0
"""

import os
import json
import yaml
import argparse
import sys
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple
import subprocess
import shutil
from dataclasses import dataclass, asdict
from enum import Enum
import logging
import urllib.request
import urllib.error


class IntegrationType(Enum):
    """Integration types supported by the hub."""
    FULL = "full"
    PARTIAL = "partial"
    MINIMAL = "minimal"


class RepositoryType(Enum):
    """Repository types in the ecosystem."""
    ENGINEERING = "engineering"
    DATA_SCIENCE = "data_science"
    PROJECT_MANAGEMENT = "project_management"
    DOCUMENTATION = "documentation"
    INFRASTRUCTURE = "infrastructure"
    WEB_APPLICATION = "web_application"
    UNKNOWN = "unknown"


@dataclass
class HubConfiguration:
    """Hub configuration data."""
    name: str
    url: str
    local_path: str
    version: str
    registry_path: str
    modules: List[str]
    sub_agents: List[str]


@dataclass
class IntegrationConfiguration:
    """Integration configuration for client repository."""
    hub_repository: str
    hub_path: str
    hub_url: str
    integration_type: str
    shared_components: List[str]
    sub_agents: List[str]
    version_requirements: Dict[str, str]
    local_overrides: Dict[str, Any]
    cache_config: Dict[str, Any]


class CrossRepoSetup:
    """Main class for cross-repository integration setup."""
    
    def __init__(self, hub_path: Optional[str] = None, verbose: bool = False):
        self.hub_path = Path(hub_path) if hub_path else self._detect_hub_path()
        self.verbose = verbose
        self.logger = self._setup_logging()
        
        # Configuration
        self.hub_config: Optional[HubConfiguration] = None
        self.client_repo_path = Path.cwd()
        self.repository_type = RepositoryType.UNKNOWN
        
    def _setup_logging(self) -> logging.Logger:
        """Set up logging configuration."""
        logger = logging.getLogger("cross_repo_setup")
        logger.setLevel(logging.DEBUG if self.verbose else logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def _detect_hub_path(self) -> Optional[Path]:
        """Attempt to detect AssetUtilities hub path."""
        # Common locations to check
        possible_paths = [
            Path.cwd().parent / "assetutilities",
            Path.home() / "projects" / "assetutilities",
            Path.home() / "github" / "assetutilities",
            Path("/mnt/github/github/assetutilities"),
        ]
        
        for path in possible_paths:
            if self._is_valid_hub_path(path):
                return path
        
        return None
    
    def _is_valid_hub_path(self, path: Path) -> bool:
        """Check if a path is a valid AssetUtilities hub."""
        if not path.exists():
            return False
        
        # Check for required hub files
        required_files = [
            "hub-config.yaml",
            "agents/registry/sub-agents.yaml",
            "src/modules"
        ]
        
        return all((path / file).exists() for file in required_files)
    
    def load_hub_configuration(self) -> bool:
        """Load hub configuration from hub-config.yaml."""
        if not self.hub_path:
            self.logger.error("Hub path not found. Please specify --hub-path")
            return False
        
        hub_config_file = self.hub_path / "hub-config.yaml"
        if not hub_config_file.exists():
            self.logger.error(f"Hub configuration not found: {hub_config_file}")
            return False
        
        try:
            with open(hub_config_file, 'r') as f:
                config_data = yaml.safe_load(f)
            
            self.hub_config = HubConfiguration(
                name=config_data["metadata"]["name"],
                url=config_data.get("hub_configuration", {}).get("repository_url", ""),
                local_path=str(self.hub_path),
                version=config_data["metadata"]["version"],
                registry_path=str(self.hub_path / "agents/registry"),
                modules=list(config_data.get("shared_modules", {}).keys()),
                sub_agents=[]
            )
            
            # Load sub-agents from registry
            registry_file = self.hub_path / "agents/registry/sub-agents.yaml"
            if registry_file.exists():
                with open(registry_file, 'r') as f:
                    registry_data = yaml.safe_load(f)
                self.hub_config.sub_agents = list(registry_data.get("sub_agents", {}).keys())
            
            self.logger.info(f"Loaded hub configuration: {self.hub_config.name} v{self.hub_config.version}")
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to load hub configuration: {str(e)}")
            return False
    
    def detect_repository_type(self) -> RepositoryType:
        """Detect the type of the current repository."""
        repo_name = self.client_repo_path.name.lower()
        
        # Repository type detection patterns
        type_patterns = {
            RepositoryType.ENGINEERING: [
                "engineer", "analysis", "simulation", "model", "energy", "rock", "oil", "field"
            ],
            RepositoryType.PROJECT_MANAGEMENT: [
                "project", "client", "investment", "resume", "acma"
            ],
            RepositoryType.INFRASTRUCTURE: [
                "asset", "infrastructure", "starter", "template", "utilities"
            ],
            RepositoryType.DATA_SCIENCE: [
                "data", "analytics", "ml", "ai", "science"
            ],
            RepositoryType.DOCUMENTATION: [
                "docs", "documentation", "wiki", "guide", "manual"
            ],
            RepositoryType.WEB_APPLICATION: [
                "web", "site", "app", "frontend", "backend", "api"
            ]
        }
        
        # Check repository name against patterns
        for repo_type, patterns in type_patterns.items():
            if any(pattern in repo_name for pattern in patterns):
                self.repository_type = repo_type
                self.logger.info(f"Detected repository type: {repo_type.value}")
                return repo_type
        
        # Check for specific files that indicate repository type
        file_indicators = {
            RepositoryType.WEB_APPLICATION: ["package.json", "requirements.txt", "app.py", "index.html"],
            RepositoryType.DATA_SCIENCE: ["notebooks/", "data/", "models/", "jupyter_notebook_config.py"],
            RepositoryType.DOCUMENTATION: ["docs/", "README.md", "mkdocs.yml", "sphinx/"]
        }
        
        for repo_type, indicators in file_indicators.items():
            if any((self.client_repo_path / indicator).exists() for indicator in indicators):
                self.repository_type = repo_type
                self.logger.info(f"Detected repository type from files: {repo_type.value}")
                return repo_type
        
        self.repository_type = RepositoryType.UNKNOWN
        self.logger.warning("Could not determine repository type automatically")
        return RepositoryType.UNKNOWN
    
    def get_recommended_integration(self) -> Tuple[IntegrationType, List[str], List[str]]:
        """Get recommended integration type and components based on repository type."""
        if not self.hub_config:
            return IntegrationType.MINIMAL, [], []
        
        # Recommendations based on repository type
        recommendations = {
            RepositoryType.ENGINEERING: {
                "integration_type": IntegrationType.FULL,
                "modules": ["agent-os", "visualization", "file-management"],
                "sub_agents": ["workflow-automation", "visualization-automation", "file-management-automation"]
            },
            RepositoryType.DATA_SCIENCE: {
                "integration_type": IntegrationType.FULL,
                "modules": ["agent-os", "visualization", "file-management"],
                "sub_agents": ["workflow-automation", "visualization-automation", "file-management-automation"]
            },
            RepositoryType.PROJECT_MANAGEMENT: {
                "integration_type": IntegrationType.FULL,
                "modules": ["agent-os", "authentication", "git-utilities"],
                "sub_agents": ["workflow-automation", "auth-system", "git-workflow-automation"]
            },
            RepositoryType.WEB_APPLICATION: {
                "integration_type": IntegrationType.PARTIAL,
                "modules": ["authentication", "visualization"],
                "sub_agents": ["auth-system", "visualization-automation"]
            },
            RepositoryType.INFRASTRUCTURE: {
                "integration_type": IntegrationType.FULL,
                "modules": ["agent-os", "git-utilities", "file-management"],
                "sub_agents": ["workflow-automation", "git-workflow-automation", "file-management-automation"]
            },
            RepositoryType.DOCUMENTATION: {
                "integration_type": IntegrationType.PARTIAL,
                "modules": ["agent-os", "file-management"],
                "sub_agents": ["workflow-automation", "file-management-automation"]
            },
            RepositoryType.UNKNOWN: {
                "integration_type": IntegrationType.MINIMAL,
                "modules": ["agent-os"],
                "sub_agents": ["workflow-automation"]
            }
        }
        
        rec = recommendations.get(self.repository_type, recommendations[RepositoryType.UNKNOWN])
        
        # Validate recommendations against available modules/sub-agents
        available_modules = [m for m in rec["modules"] if m in self.hub_config.modules]
        available_sub_agents = [s for s in rec["sub_agents"] if s in self.hub_config.sub_agents]
        
        return rec["integration_type"], available_modules, available_sub_agents
    
    def interactive_configuration(self) -> IntegrationConfiguration:
        """Interactive configuration with user input."""
        print(f"\\n=== AssetUtilities Hub Integration Setup ===")
        print(f"Hub: {self.hub_config.name} v{self.hub_config.version}")
        print(f"Repository: {self.client_repo_path.name}")
        print(f"Detected Type: {self.repository_type.value}")
        
        # Get recommendations
        rec_integration, rec_modules, rec_sub_agents = self.get_recommended_integration()
        
        print(f"\\nRecommended Integration: {rec_integration.value}")
        print(f"Recommended Modules: {', '.join(rec_modules)}")
        print(f"Recommended Sub-Agents: {', '.join(rec_sub_agents)}")
        
        # User input for integration type
        print("\\nIntegration Types:")
        print("  full    - Complete integration with all hub features")
        print("  partial - Limited integration with selected modules")
        print("  minimal - Basic integration for documentation only")
        
        while True:
            integration_input = input(f"\\nSelect integration type [{rec_integration.value}]: ").strip().lower()
            if not integration_input:
                integration_type = rec_integration
                break
            elif integration_input in ["full", "partial", "minimal"]:
                integration_type = IntegrationType(integration_input)
                break
            else:
                print("Invalid choice. Please enter 'full', 'partial', or 'minimal'")
        
        # Module selection
        print(f"\\nAvailable Modules: {', '.join(self.hub_config.modules)}")
        modules_input = input(f"Select modules (comma-separated) [{', '.join(rec_modules)}]: ").strip()
        
        if modules_input:
            selected_modules = [m.strip() for m in modules_input.split(",")]
            # Validate selections
            selected_modules = [m for m in selected_modules if m in self.hub_config.modules]
        else:
            selected_modules = rec_modules
        
        # Sub-agent selection
        print(f"\\nAvailable Sub-Agents: {', '.join(self.hub_config.sub_agents)}")
        agents_input = input(f"Select sub-agents (comma-separated) [{', '.join(rec_sub_agents)}]: ").strip()
        
        if agents_input:
            selected_sub_agents = [a.strip() for a in agents_input.split(",")]
            # Validate selections
            selected_sub_agents = [a for a in selected_sub_agents if a in self.hub_config.sub_agents]
        else:
            selected_sub_agents = rec_sub_agents
        
        # Generate shared components list
        shared_components = []
        for module in selected_modules:
            # Add key components for each module (simplified)
            if module == "agent-os":
                shared_components.extend([
                    "agent-os/enhanced-create-specs/enhanced_documentation_generator.py",
                    "agent-os/enhanced-create-specs/template_customization_system.py"
                ])
            elif module == "file-management":
                shared_components.append("file-management/automation/batch_processor.py")
            elif module == "visualization":
                shared_components.append("visualization/automation/chart_generator.py")
            elif module == "authentication":
                shared_components.append("authentication/system/auth_manager.py")
            elif module == "git-utilities":
                shared_components.append("git-utilities/automation/branch_manager.py")
        
        # Version requirements
        version_requirements = {
            "hub": f">={self.hub_config.version}",
        }
        for module in selected_modules:
            version_requirements[module] = ">=1.0.0"  # Simplified
        
        # Local overrides
        local_overrides = {
            "template_variant": "enhanced",
            "organization_standards": True
        }
        
        # Cache configuration
        cache_config = {
            "enabled": True,
            "max_age_hours": 24,
            "auto_refresh": True
        }
        
        return IntegrationConfiguration(
            hub_repository=self.hub_config.name,
            hub_path=self.hub_config.local_path,
            hub_url=self.hub_config.url,
            integration_type=integration_type.value,
            shared_components=shared_components,
            sub_agents=selected_sub_agents,
            version_requirements=version_requirements,
            local_overrides=local_overrides,
            cache_config=cache_config
        )
    
    def create_configuration_files(self, config: IntegrationConfiguration) -> bool:
        """Create configuration files in the client repository."""
        try:
            # Create .agent-os directory
            agent_os_dir = self.client_repo_path / ".agent-os"
            agent_os_dir.mkdir(exist_ok=True)
            
            # Create cross-repo-config.yaml
            cross_repo_config = agent_os_dir / "cross-repo-config.yaml"
            with open(cross_repo_config, 'w') as f:
                yaml.dump(asdict(config), f, default_flow_style=False, indent=2)
            
            self.logger.info(f"Created cross-repository configuration: {cross_repo_config}")
            
            # Create cache directory
            cache_dir = agent_os_dir / "cache" / "components"
            cache_dir.mkdir(parents=True, exist_ok=True)
            
            # Create user preferences template
            user_prefs_file = agent_os_dir / "user-preferences.yaml"
            if not user_prefs_file.exists():
                user_prefs = {
                    "preferred_variant": "enhanced",
                    "default_sections": [
                        "prompt_summary",
                        "executive_summary",
                        "system_overview"
                    ],
                    "custom_variables": {
                        "organization": "Your Organization",
                        "contact_email": "user@organization.com"
                    }
                }
                
                with open(user_prefs_file, 'w') as f:
                    yaml.dump(user_prefs, f, default_flow_style=False, indent=2)
                
                self.logger.info(f"Created user preferences template: {user_prefs_file}")
            
            # Create specs directory structure if it doesn't exist
            specs_dir = self.client_repo_path / "specs" / "modules"
            specs_dir.mkdir(parents=True, exist_ok=True)
            
            return True
            
        except Exception as e:
            self.logger.error(f"Failed to create configuration files: {str(e)}")
            return False
    
    def validate_integration(self, config: IntegrationConfiguration) -> Dict[str, Any]:
        """Validate the integration setup."""
        validation_results = {
            "valid": True,
            "errors": [],
            "warnings": [],
            "components_accessible": 0,
            "components_total": len(config.shared_components)
        }
        
        # Check hub accessibility
        hub_path = Path(config.hub_path)
        if not hub_path.exists():
            validation_results["valid"] = False
            validation_results["errors"].append(f"Hub path not accessible: {config.hub_path}")
            return validation_results
        
        # Validate shared components
        for component in config.shared_components:
            component_path = hub_path / "src" / "modules" / component
            if component_path.exists():
                validation_results["components_accessible"] += 1
            else:
                validation_results["warnings"].append(f"Component not found: {component}")
        
        # Check sub-agent registry
        registry_path = hub_path / "agents" / "registry" / "sub-agents.yaml"
        if registry_path.exists():
            try:
                with open(registry_path, 'r') as f:
                    registry_data = yaml.safe_load(f)
                
                for agent in config.sub_agents:
                    if agent not in registry_data.get("sub_agents", {}):
                        validation_results["warnings"].append(f"Sub-agent not found in registry: {agent}")
                        
            except Exception as e:
                validation_results["warnings"].append(f"Could not validate sub-agent registry: {str(e)}")
        
        # Check version compatibility (simplified)
        if validation_results["components_accessible"] < validation_results["components_total"]:
            if validation_results["components_accessible"] == 0:
                validation_results["valid"] = False
                validation_results["errors"].append("No shared components are accessible")
            else:
                validation_results["warnings"].append(
                    f"Only {validation_results['components_accessible']}/{validation_results['components_total']} components accessible"
                )
        
        return validation_results
    
    def run_integration_test(self, config: IntegrationConfiguration) -> bool:
        """Run basic integration test."""
        try:
            self.logger.info("Running integration test...")
            
            # Test 1: Import shared component (simulate)
            test_component_path = Path(config.hub_path) / "src" / "modules" / "agent-os" / "enhanced-create-specs"
            if test_component_path.exists():
                self.logger.info("✓ Hub components accessible")
            else:
                self.logger.warning("⚠ Hub components not accessible")
                return False
            
            # Test 2: Configuration file creation
            config_file = self.client_repo_path / ".agent-os" / "cross-repo-config.yaml"
            if config_file.exists():
                self.logger.info("✓ Configuration files created")
            else:
                self.logger.error("✗ Configuration files missing")
                return False
            
            # Test 3: Directory structure
            required_dirs = [
                ".agent-os",
                ".agent-os/cache",
                "specs/modules"
            ]
            
            for dir_path in required_dirs:
                if (self.client_repo_path / dir_path).exists():
                    self.logger.info(f"✓ Directory exists: {dir_path}")
                else:
                    self.logger.warning(f"⚠ Directory missing: {dir_path}")
            
            self.logger.info("Integration test completed successfully")
            return True
            
        except Exception as e:
            self.logger.error(f"Integration test failed: {str(e)}")
            return False
    
    def generate_usage_examples(self, config: IntegrationConfiguration) -> str:
        """Generate usage examples for the configured integration."""
        examples = []
        
        examples.append("# AssetUtilities Hub Integration - Usage Examples\\n")
        
        if "workflow-automation" in config.sub_agents:
            examples.extend([
                "## Enhanced Spec Creation",
                "```bash",
                "# Create enhanced spec with all features",
                "/create-specs my-feature my-module enhanced",
                "",
                "# Create minimal spec for simple changes", 
                "/create-specs bug-fix utils minimal",
                "```\\n"
            ])
        
        if "file-management-automation" in config.sub_agents:
            examples.extend([
                "## File Management Automation",
                "```bash",
                "# Organize files by pattern",
                "/organize-files ./data --pattern *.csv --by-date",
                "",
                "# Batch rename files",
                "/batch-rename ./reports --prefix project_ --extension .pdf",
                "```\\n"
            ])
        
        if "visualization-automation" in config.sub_agents:
            examples.extend([
                "## Visualization Automation",
                "```bash",
                "# Auto-generate charts",
                "/create-chart ./data.csv --auto-detect --export png,html",
                "",
                "# Create interactive dashboard",
                "/create-dashboard ./metrics --interactive --template business",
                "```\\n"
            ])
        
        examples.extend([
            "## Cross-Repository References",
            "```markdown",
            "# Reference shared components",
            f"@{config.hub_repository}:src/modules/agent-os/enhanced-create-specs/",
            "",
            "# Reference sub-agents",
            f"@{config.hub_repository}:agents/registry/sub-agents/workflow-automation",
            "```\\n"
        ])
        
        return "\\n".join(examples)
    
    def setup_integration(self, auto_confirm: bool = False) -> bool:
        """Main setup method."""
        self.logger.info("Starting cross-repository integration setup...")
        
        # Load hub configuration
        if not self.load_hub_configuration():
            return False
        
        # Detect repository type
        self.detect_repository_type()
        
        # Interactive configuration (or use defaults if auto_confirm)
        if auto_confirm:
            integration_type, modules, sub_agents = self.get_recommended_integration()
            
            config = IntegrationConfiguration(
                hub_repository=self.hub_config.name,
                hub_path=self.hub_config.local_path,
                hub_url=self.hub_config.url,
                integration_type=integration_type.value,
                shared_components=[f"{m}/main_component.py" for m in modules],  # Simplified
                sub_agents=sub_agents,
                version_requirements={"hub": f">={self.hub_config.version}"},
                local_overrides={"template_variant": "enhanced"},
                cache_config={"enabled": True, "max_age_hours": 24}
            )
        else:
            config = self.interactive_configuration()
        
        # Create configuration files
        if not self.create_configuration_files(config):
            return False
        
        # Validate integration
        validation_results = self.validate_integration(config)
        
        if not validation_results["valid"]:
            self.logger.error("Integration validation failed:")
            for error in validation_results["errors"]:
                self.logger.error(f"  - {error}")
            return False
        
        if validation_results["warnings"]:
            self.logger.warning("Integration validation warnings:")
            for warning in validation_results["warnings"]:
                self.logger.warning(f"  - {warning}")
        
        # Run integration test
        if not self.run_integration_test(config):
            self.logger.error("Integration test failed")
            return False
        
        # Generate usage examples
        examples = self.generate_usage_examples(config)
        examples_file = self.client_repo_path / ".agent-os" / "usage-examples.md"
        with open(examples_file, 'w') as f:
            f.write(examples)
        
        self.logger.info(f"✅ Cross-repository integration setup completed successfully!")
        self.logger.info(f"Configuration saved to: {self.client_repo_path}/.agent-os/")
        self.logger.info(f"Usage examples: {examples_file}")
        
        return True


def main():
    """Main entry point."""
    parser = argparse.ArgumentParser(
        description="Set up cross-repository integration with AssetUtilities hub",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Interactive setup
  python setup-cross-repo-integration.py
  
  # Automatic setup with default recommendations
  python setup-cross-repo-integration.py --auto-confirm
  
  # Specify custom hub path
  python setup-cross-repo-integration.py --hub-path /path/to/assetutilities
  
  # Verbose output for debugging
  python setup-cross-repo-integration.py --verbose
        """
    )
    
    parser.add_argument(
        "--hub-path",
        type=str,
        help="Path to AssetUtilities hub repository"
    )
    
    parser.add_argument(
        "--auto-confirm",
        action="store_true",
        help="Use recommended settings without interactive prompts"
    )
    
    parser.add_argument(
        "--verbose",
        action="store_true",
        help="Enable verbose output"
    )
    
    parser.add_argument(
        "--validate-only",
        action="store_true",
        help="Only validate existing integration without making changes"
    )
    
    args = parser.parse_args()
    
    # Initialize setup
    setup = CrossRepoSetup(
        hub_path=args.hub_path,
        verbose=args.verbose
    )
    
    if args.validate_only:
        # Validation-only mode
        if setup.load_hub_configuration():
            config_file = setup.client_repo_path / ".agent-os" / "cross-repo-config.yaml"
            if config_file.exists():
                with open(config_file, 'r') as f:
                    config_data = yaml.safe_load(f)
                
                config = IntegrationConfiguration(**config_data)
                validation_results = setup.validate_integration(config)
                
                if validation_results["valid"]:
                    print("✅ Integration validation passed")
                    sys.exit(0)
                else:
                    print("❌ Integration validation failed")
                    for error in validation_results["errors"]:
                        print(f"  - {error}")
                    sys.exit(1)
            else:
                print("❌ No integration configuration found")
                sys.exit(1)
        else:
            print("❌ Could not load hub configuration")
            sys.exit(1)
    else:
        # Normal setup mode
        success = setup.setup_integration(auto_confirm=args.auto_confirm)
        sys.exit(0 if success else 1)


if __name__ == "__main__":
    main()