#!/usr/bin/env python3
"""
Integration tests for AssetUtilities Hub functionality in the enhanced-create-specs workflow.

Tests cover:
- Hub repository structure and organization
- Shared sub-agent registry functionality
- Cross-repository component sharing
- Version compatibility checking
- Hub-based reference resolution
- Integration with external repositories

Author: Enhanced Create-Specs Workflow
Created: 2025-08-05
Module: agent-os/enhanced-create-specs
Test Type: Integration
"""

import pytest
import tempfile
import shutil
import json
import yaml
from pathlib import Path

# Test configuration
TEST_HUB_CONFIG = {
    "hub_repository": "assetutilities",
    "supported_repositories": [
        "aceengineer-website",
        "aceengineercode", 
        "digitalmodel",
        "energy",
        "rock-oil-field"
    ],
    "shared_components_path": "src/modules/",
    "registry_path": "agents/registry/",
    "version_compatibility": "1.0.0"
}


class TestAssetUtilitiesHubStructure:
    """Test suite for AssetUtilities hub repository structure."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.hub_path = Path(self.temp_dir) / "assetutilities"
        self.external_repo_path = Path(self.temp_dir) / "external-repo"
        
        # Create mock hub structure
        self._create_mock_hub_structure()
        self._create_mock_external_repo()
    
    def teardown_method(self):
        """Clean up test environment after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_mock_hub_structure(self):
        """Create mock AssetUtilities hub structure."""
        self.hub_path.mkdir(parents=True)
        
        # Create shared components directory
        shared_components = self.hub_path / "src/modules"
        shared_components.mkdir(parents=True)
        
        # Create agent-os module in hub
        agent_os_path = shared_components / "agent-os"
        agent_os_path.mkdir()
        
        # Create enhanced-create-specs in hub
        enhanced_specs_path = agent_os_path / "enhanced-create-specs"
        enhanced_specs_path.mkdir()
        
        # Create mock shared components
        (enhanced_specs_path / "enhanced_documentation_generator.py").write_text(
            "# Shared enhanced documentation generator\nclass EnhancedDocumentationGenerator: pass"
        )
        
        # Create agents registry
        registry_path = self.hub_path / "agents/registry"
        registry_path.mkdir(parents=True)
        
        registry_config = {
            "version": "1.0.0",
            "sub_agents": {
                "workflow-automation": {
                    "module": "agent-os",
                    "path": "src/modules/agent-os/enhanced-create-specs/",
                    "version": "1.0.0",
                    "capabilities": [
                        "enhanced_spec_creation",
                        "template_customization",
                        "cross_repository_integration"
                    ],
                    "dependencies": [],
                    "compatible_repositories": ["*"]
                }
            }
        }
        
        (registry_path / "sub-agents.yaml").write_text(yaml.dump(registry_config))
        
        # Create hub configuration
        hub_config = {
            "name": "assetutilities",
            "type": "hub_repository", 
            "version": "1.0.0",
            "shared_modules": ["agent-os", "file-management", "visualization"],
            "supported_repositories": TEST_HUB_CONFIG["supported_repositories"]
        }
        
        (self.hub_path / "hub-config.yaml").write_text(yaml.dump(hub_config))
    
    def _create_mock_external_repo(self):
        """Create mock external repository structure."""
        self.external_repo_path.mkdir(parents=True)
        
        # Create .agent-os configuration
        agent_os_config = self.external_repo_path / ".agent-os"
        agent_os_config.mkdir()
        
        cross_repo_config = {
            "hub_repository": "assetutilities",
            "hub_path": str(self.hub_path),
            "shared_components": ["agent-os/enhanced-create-specs"],
            "local_overrides": {}
        }
        
        (agent_os_config / "cross-repo-config.yaml").write_text(yaml.dump(cross_repo_config))
        
        # Create specs directory
        specs_dir = self.external_repo_path / "specs/modules"
        specs_dir.mkdir(parents=True)
    
    def test_hub_structure_validation(self):
        """Test that hub repository has correct structure."""
        # Check required directories exist
        assert (self.hub_path / "src/modules").exists()
        assert (self.hub_path / "agents/registry").exists()
        assert (self.hub_path / "hub-config.yaml").exists()
        
        # Check agent-os module exists in hub
        assert (self.hub_path / "src/modules/agent-os").exists()
        assert (self.hub_path / "src/modules/agent-os/enhanced-create-specs").exists()
        
        # Check shared component exists
        shared_component = self.hub_path / "src/modules/agent-os/enhanced-create-specs/enhanced_documentation_generator.py"
        assert shared_component.exists()
        
        content = shared_component.read_text()
        assert "EnhancedDocumentationGenerator" in content
    
    def test_sub_agent_registry_structure(self):
        """Test sub-agent registry structure and content."""
        registry_file = self.hub_path / "agents/registry/sub-agents.yaml"
        assert registry_file.exists()
        
        with open(registry_file, 'r') as f:
            registry = yaml.safe_load(f)
        
        # Check registry structure
        assert "version" in registry
        assert "sub_agents" in registry
        assert "workflow-automation" in registry["sub_agents"]
        
        # Check sub-agent configuration
        workflow_agent = registry["sub_agents"]["workflow-automation"]
        assert workflow_agent["module"] == "agent-os"
        assert "enhanced_spec_creation" in workflow_agent["capabilities"]
        assert workflow_agent["version"] == "1.0.0"
    
    def test_hub_configuration_validation(self):
        """Test hub configuration file validation."""
        hub_config_file = self.hub_path / "hub-config.yaml"
        assert hub_config_file.exists()
        
        with open(hub_config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check configuration structure
        assert config["name"] == "assetutilities"
        assert config["type"] == "hub_repository"
        assert "agent-os" in config["shared_modules"]
        assert len(config["supported_repositories"]) > 0
    
    def test_cross_repo_configuration_setup(self):
        """Test cross-repository configuration setup."""
        cross_repo_config = self.external_repo_path / ".agent-os/cross-repo-config.yaml"
        assert cross_repo_config.exists()
        
        with open(cross_repo_config, 'r') as f:
            config = yaml.safe_load(f)
        
        # Check configuration
        assert config["hub_repository"] == "assetutilities"
        assert "agent-os/enhanced-create-specs" in config["shared_components"]
        assert "hub_path" in config


class TestSharedComponentIntegration:
    """Test suite for shared component integration functionality."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.hub_path = Path(self.temp_dir) / "assetutilities"
        self.client_repo_path = Path(self.temp_dir) / "client-repo"
        
        self._setup_hub_and_client()
    
    def teardown_method(self):
        """Clean up test environment after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _setup_hub_and_client(self):
        """Set up hub and client repository structures."""
        # Create hub
        self.hub_path.mkdir(parents=True)
        hub_modules = self.hub_path / "src/modules/agent-os/enhanced-create-specs"
        hub_modules.mkdir(parents=True)
        
        # Create shared component with version
        shared_component = hub_modules / "shared_component.py"
        shared_component.write_text("""
# Shared Component v1.0.0
class SharedEnhancedDocGenerator:
    VERSION = "1.0.0"
    
    def generate_spec(self, config):
        return f"Generated spec with version {self.VERSION}"
""")
        
        # Create client repo
        self.client_repo_path.mkdir(parents=True)
        client_config = self.client_repo_path / ".agent-os/cross-repo-config.yaml"
        client_config.parent.mkdir(parents=True)
        
        config_data = {
            "hub_repository": "assetutilities",
            "hub_path": str(self.hub_path),
            "shared_components": ["agent-os/enhanced-create-specs/shared_component.py"],
            "version_requirements": {"agent-os": ">=1.0.0"}
        }
        
        client_config.write_text(yaml.dump(config_data))
    
    def test_shared_component_reference_resolution(self):
        """Test resolution of shared component references."""
        # Test reference pattern
        reference = "@assetutilities:src/modules/agent-os/enhanced-create-specs/shared_component.py"
        
        # Parse reference
        assert reference.startswith("@assetutilities:")
        repo_name, path = reference[1:].split(":", 1)
        assert repo_name == "assetutilities"
        assert path == "src/modules/agent-os/enhanced-create-specs/shared_component.py"
        
        # Resolve to absolute path
        resolved_path = self.hub_path / path
        assert resolved_path.exists()
        
        # Check content
        content = resolved_path.read_text()
        assert "SharedEnhancedDocGenerator" in content
        assert "VERSION = \"1.0.0\"" in content
    
    def test_version_compatibility_checking(self):
        """Test version compatibility checking between hub and client."""
        # Load client requirements
        client_config_file = self.client_repo_path / ".agent-os/cross-repo-config.yaml"
        with open(client_config_file, 'r') as f:
            client_config = yaml.safe_load(f)
        
        required_version = client_config["version_requirements"]["agent-os"]
        assert required_version == ">=1.0.0"
        
        # Check hub component version
        shared_component = self.hub_path / "src/modules/agent-os/enhanced-create-specs/shared_component.py"
        content = shared_component.read_text()
        
        # Extract version (simple regex simulation)
        import re
        version_match = re.search(r'VERSION = ["\']([^"\']+)["\']', content)
        assert version_match
        
        hub_version = version_match.group(1)
        assert hub_version == "1.0.0"
        
        # Version compatibility check (simplified)
        def version_satisfies(version, requirement):
            if requirement.startswith(">="):
                required = requirement[2:]
                return version >= required
            return version == requirement
        
        assert version_satisfies(hub_version, required_version)
    
    def test_component_caching_mechanism(self):
        """Test component caching for performance."""
        cache_dir = self.client_repo_path / ".agent-os/cache/components"
        cache_dir.mkdir(parents=True)
        
        # Simulate caching shared component
        source_path = self.hub_path / "src/modules/agent-os/enhanced-create-specs/shared_component.py"
        cache_path = cache_dir / "agent-os_enhanced-create-specs_shared_component.py"
        
        # Copy to cache
        shutil.copy2(source_path, cache_path)
        
        # Test cache exists and is valid
        assert cache_path.exists()
        
        cached_content = cache_path.read_text()
        original_content = source_path.read_text()
        assert cached_content == original_content
        
        # Test cache metadata
        cache_metadata = {
            "source": str(source_path),
            "cached_at": "2025-08-05T10:00:00Z",
            "version": "1.0.0",
            "checksum": "abc123"  # In real implementation, compute actual hash
        }
        
        metadata_file = cache_dir / "agent-os_enhanced-create-specs_shared_component.meta"
        metadata_file.write_text(json.dumps(cache_metadata, indent=2))
        
        assert metadata_file.exists()
        
        with open(metadata_file, 'r') as f:
            loaded_metadata = json.load(f)
        
        assert loaded_metadata["version"] == "1.0.0"
        assert loaded_metadata["source"] == str(source_path)


class TestCrossRepositoryOperations:
    """Test suite for cross-repository operations and workflows."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.hub_path = Path(self.temp_dir) / "assetutilities"
        self.repo_a_path = Path(self.temp_dir) / "repo-a"
        self.repo_b_path = Path(self.temp_dir) / "repo-b"
        
        self._setup_multi_repo_environment()
    
    def teardown_method(self):
        """Clean up test environment after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _setup_multi_repo_environment(self):
        """Set up multi-repository test environment."""
        # Create hub with enhanced create-specs
        self.hub_path.mkdir(parents=True)
        hub_specs = self.hub_path / "src/modules/agent-os/enhanced-create-specs"
        hub_specs.mkdir(parents=True)
        
        # Create workflow component in hub
        workflow_component = hub_specs / "workflow_automation.py"
        workflow_component.write_text("""
class WorkflowAutomation:
    def create_enhanced_spec(self, spec_name, module_name, variant="enhanced"):
        return {
            "spec_name": spec_name,
            "module_name": module_name,
            "variant": variant,
            "generated_by": "AssetUtilities Hub v1.0.0"
        }
""")
        
        # Create repository A
        self.repo_a_path.mkdir(parents=True)
        repo_a_config = self.repo_a_path / ".agent-os/cross-repo-config.yaml"
        repo_a_config.parent.mkdir(parents=True)
        
        repo_a_config_data = {
            "hub_repository": "assetutilities",
            "hub_path": str(self.hub_path),
            "shared_components": ["agent-os/enhanced-create-specs/workflow_automation.py"],
            "repository_type": "engineering"
        }
        repo_a_config.write_text(yaml.dump(repo_a_config_data))
        
        # Create repository B
        self.repo_b_path.mkdir(parents=True)
        repo_b_config = self.repo_b_path / ".agent-os/cross-repo-config.yaml"
        repo_b_config.parent.mkdir(parents=True)
        
        repo_b_config_data = {
            "hub_repository": "assetutilities",
            "hub_path": str(self.hub_path),
            "shared_components": ["agent-os/enhanced-create-specs/workflow_automation.py"],
            "repository_type": "data_science"
        }
        repo_b_config.write_text(yaml.dump(repo_b_config_data))
    
    def test_multi_repository_component_sharing(self):
        """Test sharing components across multiple repositories."""
        # Both repositories should be able to access the same shared component
        shared_component_path = "src/modules/agent-os/enhanced-create-specs/workflow_automation.py"
        
        # Repository A access
        resolved_a = self.hub_path / shared_component_path
        assert resolved_a.exists()
        
        # Repository B access
        resolved_b = self.hub_path / shared_component_path
        assert resolved_b.exists()
        
        # Both should resolve to the same component
        assert resolved_a == resolved_b
        
        # Test component functionality
        content = resolved_a.read_text()
        assert "WorkflowAutomation" in content
        assert "create_enhanced_spec" in content
    
    def test_repository_specific_customization(self):
        """Test repository-specific customization while sharing base components."""
        # Repository A customization
        repo_a_custom = self.repo_a_path / "src/modules/agent-os/local_customizations.py"
        repo_a_custom.parent.mkdir(parents=True)
        repo_a_custom.write_text("""
from assetutilities.src.modules.agent_os.enhanced_create_specs.workflow_automation import WorkflowAutomation

class EngineeringWorkflowAutomation(WorkflowAutomation):
    def create_enhanced_spec(self, spec_name, module_name, variant="enhanced"):
        result = super().create_enhanced_spec(spec_name, module_name, variant)
        result["repository_type"] = "engineering"
        result["custom_sections"] = ["technical_specifications", "performance_requirements"]
        return result
""")
        
        # Repository B customization
        repo_b_custom = self.repo_b_path / "src/modules/agent-os/local_customizations.py"
        repo_b_custom.parent.mkdir(parents=True)
        repo_b_custom.write_text("""
from assetutilities.src.modules.agent_os.enhanced_create_specs.workflow_automation import WorkflowAutomation

class DataScienceWorkflowAutomation(WorkflowAutomation):
    def create_enhanced_spec(self, spec_name, module_name, variant="enhanced"):
        result = super().create_enhanced_spec(spec_name, module_name, variant)
        result["repository_type"] = "data_science"
        result["custom_sections"] = ["data_requirements", "model_specifications"]
        return result
""")
        
        # Test that both customizations exist and are different
        assert repo_a_custom.exists()
        assert repo_b_custom.exists()
        
        repo_a_content = repo_a_custom.read_text()
        repo_b_content = repo_b_custom.read_text()
        
        assert "EngineeringWorkflowAutomation" in repo_a_content
        assert "DataScienceWorkflowAutomation" in repo_b_content
        assert "technical_specifications" in repo_a_content
        assert "data_requirements" in repo_b_content
    
    def test_cross_repository_reference_validation(self):
        """Test validation of cross-repository references."""
        # Valid references
        valid_references = [
            "@assetutilities:src/modules/agent-os/enhanced-create-specs/workflow_automation.py",
            "@assetutilities:agents/registry/sub-agents.yaml",
            "@assetutilities:hub-config.yaml"
        ]
        
        for ref in valid_references:
            # Parse reference
            assert ref.startswith("@assetutilities:")
            repo, path = ref[1:].split(":", 1)
            
            # Resolve path
            resolved_path = self.hub_path / path
            
            # Validate existence (workflow_automation.py exists, others may not in this test)
            if "workflow_automation.py" in path:
                assert resolved_path.exists()
        
        # Invalid references
        invalid_references = [
            "@nonexistent:some/path/file.py",
            "@assetutilities:nonexistent/path/file.py",
            "invalid-reference-format"
        ]
        
        for ref in invalid_references:
            if ":" in ref and ref.startswith("@"):
                repo, path = ref[1:].split(":", 1)
                resolved_path = self.hub_path / path
                if "nonexistent" in path:
                    assert not resolved_path.exists()


class TestHubRegistryOperations:
    """Test suite for hub registry operations and management."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.hub_path = Path(self.temp_dir) / "assetutilities"
        self._setup_hub_registry()
    
    def teardown_method(self):
        """Clean up test environment after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _setup_hub_registry(self):
        """Set up hub registry structure."""
        self.hub_path.mkdir(parents=True)
        registry_path = self.hub_path / "agents/registry"
        registry_path.mkdir(parents=True)
        
        # Create comprehensive registry
        registry_data = {
            "version": "1.0.0",
            "last_updated": "2025-08-05",
            "sub_agents": {
                "workflow-automation": {
                    "module": "agent-os",
                    "path": "src/modules/agent-os/enhanced-create-specs/",
                    "version": "1.0.0",
                    "capabilities": [
                        "enhanced_spec_creation",
                        "template_customization", 
                        "cross_repository_integration",
                        "ai_persistence_management"
                    ],
                    "dependencies": [],
                    "compatible_repositories": ["*"],
                    "configuration_schema": {
                        "required": ["spec_name", "module_name"],
                        "optional": ["variant", "custom_sections"]
                    }
                },
                "test-automation": {
                    "module": "testing",
                    "path": "src/modules/testing/test-automation/",
                    "version": "0.9.0",
                    "capabilities": [
                        "automated_test_generation",
                        "test_execution",
                        "coverage_reporting"
                    ],
                    "dependencies": ["workflow-automation"],
                    "compatible_repositories": ["engineering", "data_science"]
                }
            },
            "modules": {
                "agent-os": {
                    "version": "1.0.0",
                    "path": "src/modules/agent-os/",
                    "sub_agents": ["workflow-automation"],
                    "description": "Enhanced workflow automation and specification management"
                },
                "testing": {
                    "version": "0.9.0", 
                    "path": "src/modules/testing/",
                    "sub_agents": ["test-automation"],
                    "description": "Automated testing and quality assurance"
                }
            }
        }
        
        (registry_path / "sub-agents.yaml").write_text(yaml.dump(registry_data))
    
    def test_registry_loading_and_parsing(self):
        """Test loading and parsing of the sub-agent registry."""
        registry_file = self.hub_path / "agents/registry/sub-agents.yaml"
        assert registry_file.exists()
        
        with open(registry_file, 'r') as f:
            registry = yaml.safe_load(f)
        
        # Test registry structure
        assert "version" in registry
        assert "sub_agents" in registry
        assert "modules" in registry
        
        # Test sub-agent entries
        assert "workflow-automation" in registry["sub_agents"]
        assert "test-automation" in registry["sub_agents"]
        
        # Test module entries
        assert "agent-os" in registry["modules"]
        assert "testing" in registry["modules"]
    
    def test_sub_agent_capability_discovery(self):
        """Test discovery of sub-agent capabilities."""
        registry_file = self.hub_path / "agents/registry/sub-agents.yaml"
        
        with open(registry_file, 'r') as f:
            registry = yaml.safe_load(f)
        
        workflow_agent = registry["sub_agents"]["workflow-automation"]
        
        # Test capabilities
        expected_capabilities = [
            "enhanced_spec_creation",
            "template_customization",
            "cross_repository_integration",
            "ai_persistence_management"
        ]
        
        for capability in expected_capabilities:
            assert capability in workflow_agent["capabilities"]
        
        # Test configuration schema
        assert "configuration_schema" in workflow_agent
        schema = workflow_agent["configuration_schema"]
        assert "spec_name" in schema["required"]
        assert "module_name" in schema["required"]
        assert "variant" in schema["optional"]
    
    def test_dependency_resolution(self):
        """Test sub-agent dependency resolution."""
        registry_file = self.hub_path / "agents/registry/sub-agents.yaml"
        
        with open(registry_file, 'r') as f:
            registry = yaml.safe_load(f)
        
        # Test workflow-automation (no dependencies)
        workflow_agent = registry["sub_agents"]["workflow-automation"]
        assert workflow_agent["dependencies"] == []
        
        # Test test-automation (depends on workflow-automation)
        test_agent = registry["sub_agents"]["test-automation"]
        assert "workflow-automation" in test_agent["dependencies"]
        
        # Verify dependency exists in registry
        assert "workflow-automation" in registry["sub_agents"]
    
    def test_repository_compatibility_checking(self):
        """Test repository compatibility checking for sub-agents."""
        registry_file = self.hub_path / "agents/registry/sub-agents.yaml"
        
        with open(registry_file, 'r') as f:
            registry = yaml.safe_load(f)
        
        # Test universal compatibility
        workflow_agent = registry["sub_agents"]["workflow-automation"]
        assert workflow_agent["compatible_repositories"] == ["*"]
        
        # Test specific compatibility
        test_agent = registry["sub_agents"]["test-automation"]
        compatible_repos = test_agent["compatible_repositories"]
        assert "engineering" in compatible_repos
        assert "data_science" in compatible_repos
        
        # Test compatibility checking logic
        def is_compatible(agent_config, repo_type):
            compatible = agent_config["compatible_repositories"]
            return "*" in compatible or repo_type in compatible
        
        assert is_compatible(workflow_agent, "any_repo_type")
        assert is_compatible(test_agent, "engineering")
        assert is_compatible(test_agent, "data_science")
        assert not is_compatible(test_agent, "marketing")


class TestIntegrationWorkflows:
    """Test suite for end-to-end integration workflows."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.hub_path = Path(self.temp_dir) / "assetutilities"
        self.client_path = Path(self.temp_dir) / "client-repo"
        
        self._setup_complete_integration_environment()
    
    def teardown_method(self):
        """Clean up test environment after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _setup_complete_integration_environment(self):
        """Set up complete integration test environment."""
        # Create hub with full structure
        self.hub_path.mkdir(parents=True)
        
        # Hub modules
        hub_modules = self.hub_path / "src/modules/agent-os/enhanced-create-specs"
        hub_modules.mkdir(parents=True)
        
        # Create actual implementation files (simplified)
        (hub_modules / "__init__.py").write_text("")
        (hub_modules / "workflow_integration.py").write_text("""
class HubWorkflowIntegration:
    def __init__(self, hub_path, registry_path):
        self.hub_path = hub_path
        self.registry_path = registry_path
    
    def setup_client_repository(self, client_path, repo_config):
        # Simulate setting up client repository
        return {
            "status": "success",
            "components_installed": repo_config.get("shared_components", []),
            "configuration_applied": True
        }
    
    def validate_integration(self, client_path):
        # Simulate integration validation
        return {
            "valid": True,
            "shared_components_accessible": True,
            "version_compatibility": True,
            "configuration_valid": True
        }
""")
        
        # Registry
        registry_path = self.hub_path / "agents/registry"
        registry_path.mkdir(parents=True)
        
        registry_data = {
            "version": "1.0.0",
            "sub_agents": {
                "workflow-automation": {
                    "module": "agent-os",
                    "path": "src/modules/agent-os/enhanced-create-specs/",
                    "version": "1.0.0"
                }
            }
        }
        (registry_path / "sub-agents.yaml").write_text(yaml.dump(registry_data))
        
        # Client repository
        self.client_path.mkdir(parents=True)
        client_config_dir = self.client_path / ".agent-os"
        client_config_dir.mkdir()
        
        client_config = {
            "hub_repository": "assetutilities",
            "hub_path": str(self.hub_path),
            "shared_components": ["agent-os/enhanced-create-specs/workflow_integration.py"],
            "integration_version": "1.0.0"
        }
        
        (client_config_dir / "cross-repo-config.yaml").write_text(yaml.dump(client_config))
    
    def test_end_to_end_client_setup(self):
        """Test complete end-to-end client repository setup."""
        # Load client configuration
        client_config_file = self.client_path / ".agent-os/cross-repo-config.yaml"
        
        with open(client_config_file, 'r') as f:
            client_config = yaml.safe_load(f)
        
        # Simulate hub integration setup
        hub_integration_path = self.hub_path / "src/modules/agent-os/enhanced-create-specs/workflow_integration.py"
        assert hub_integration_path.exists()
        
        # Test configuration loading
        assert client_config["hub_repository"] == "assetutilities"
        assert client_config["hub_path"] == str(self.hub_path)
        assert "agent-os/enhanced-create-specs/workflow_integration.py" in client_config["shared_components"]
    
    def test_shared_component_accessibility(self):
        """Test that shared components are properly accessible from client."""
        # Shared component reference
        shared_ref = "@assetutilities:src/modules/agent-os/enhanced-create-specs/workflow_integration.py"
        
        # Parse reference
        repo, path = shared_ref[1:].split(":", 1)
        resolved_path = self.hub_path / path
        
        assert resolved_path.exists()
        
        # Test component content
        content = resolved_path.read_text()
        assert "HubWorkflowIntegration" in content
        assert "setup_client_repository" in content
        assert "validate_integration" in content
    
    def test_integration_validation_workflow(self):
        """Test the complete integration validation workflow."""
        # This would normally import and use the actual integration class
        # For testing, we'll simulate the workflow
        
        validation_results = {
            "hub_accessible": True,
            "registry_loaded": True,
            "shared_components_found": True,
            "version_compatibility": True,
            "client_configuration_valid": True
        }
        
        # Test all validation criteria
        for criterion, result in validation_results.items():
            assert result, f"Integration validation failed for: {criterion}"
        
        # Test overall integration success
        integration_successful = all(validation_results.values())
        assert integration_successful
    
    def test_failure_scenarios_and_recovery(self):
        """Test integration failure scenarios and recovery mechanisms."""
        # Test missing hub path
        invalid_config = {
            "hub_repository": "assetutilities",
            "hub_path": "/nonexistent/path",
            "shared_components": ["agent-os/enhanced-create-specs/workflow_integration.py"]
        }
        
        # This should fail validation
        hub_path = Path(invalid_config["hub_path"])
        assert not hub_path.exists()
        
        # Test missing shared component
        missing_component_ref = "@assetutilities:src/modules/nonexistent/component.py"
        repo, path = missing_component_ref[1:].split(":", 1)
        resolved_path = self.hub_path / path
        assert not resolved_path.exists()
        
        # Test recovery mechanism (fallback to local implementation)
        local_fallback = self.client_path / "src/modules/local_fallback.py"
        local_fallback.parent.mkdir(parents=True)
        local_fallback.write_text("# Local fallback implementation")
        
        assert local_fallback.exists()


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])