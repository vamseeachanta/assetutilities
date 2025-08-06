"""Tests for enhanced specs integration system."""

import pytest
import tempfile
import shutil
import yaml
import json
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from datetime import datetime

from assetutilities.agent_os.commands.specs_integration import (
    SpecsIntegrationManager,
    WorkflowHook,
    PromptEvolutionTracker,
    CrossRepositoryReferencer,
    EnhancedSpecsConfig,
    WorkflowRefresher
)


class TestWorkflowHook:
    """Test workflow hook functionality."""

    def test_create_basic_hook(self):
        """Test creating a basic workflow hook."""
        hook = WorkflowHook(
            name="test_hook",
            trigger="on_spec_creation",
            action="generate_documentation",
            config={"format": "markdown"}
        )
        
        assert hook.name == "test_hook"
        assert hook.trigger == "on_spec_creation"
        assert hook.action == "generate_documentation"
        assert hook.config["format"] == "markdown"
        assert hook.enabled is True

    def test_hook_from_dict(self):
        """Test creating hook from dictionary."""
        hook_data = {
            "name": "integration_hook",
            "trigger": "on_task_completion",
            "action": "update_references",
            "config": {"repository": "assetutilities", "branch": "main"},
            "enabled": False
        }
        
        hook = WorkflowHook.from_dict(hook_data)
        
        assert hook.name == "integration_hook"
        assert hook.trigger == "on_task_completion"
        assert hook.action == "update_references"
        assert hook.config["repository"] == "assetutilities"
        assert hook.enabled is False

    def test_hook_to_dict(self):
        """Test converting hook to dictionary."""
        hook = WorkflowHook(
            name="export_hook",
            trigger="on_completion",
            action="export_results",
            config={"format": "json"},
            enabled=True
        )
        
        data = hook.to_dict()
        
        assert data["name"] == "export_hook"
        assert data["trigger"] == "on_completion"
        assert data["action"] == "export_results"
        assert data["config"]["format"] == "json"
        assert data["enabled"] is True

    def test_hook_validation(self):
        """Test hook validation."""
        # Valid hook
        valid_hook = WorkflowHook(
            name="valid_hook",
            trigger="on_start",
            action="initialize"
        )
        assert valid_hook.is_valid()
        
        # Invalid hook (missing required fields)
        invalid_hook = WorkflowHook(name="", trigger="", action="")
        assert not invalid_hook.is_valid()


class TestPromptEvolutionTracker:
    """Test prompt evolution tracking functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.tracker = PromptEvolutionTracker(tracking_dir=Path(self.temp_dir))

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_track_prompt_usage(self):
        """Test tracking prompt usage."""
        prompt_id = "test_prompt_1"
        usage_data = {
            "agent": "test_agent",
            "context": "code_review",
            "tokens_used": 150,
            "response_quality": 0.85,
            "execution_time": 2.3
        }
        
        result = self.tracker.track_prompt_usage(prompt_id, usage_data)
        
        assert result.success
        
        # Verify tracking file exists
        tracking_file = self.tracker.tracking_dir / f"{prompt_id}.json"
        assert tracking_file.exists()
        
        # Verify data is stored correctly
        with open(tracking_file, 'r') as f:
            stored_data = json.load(f)
        
        assert len(stored_data["usage_history"]) == 1
        assert stored_data["usage_history"][0]["agent"] == "test_agent"
        assert stored_data["usage_history"][0]["tokens_used"] == 150

    def test_get_prompt_statistics(self):
        """Test getting prompt usage statistics."""
        prompt_id = "stats_prompt"
        
        # Track multiple usages
        for i in range(5):
            usage_data = {
                "agent": f"agent_{i}",
                "context": "testing",
                "tokens_used": 100 + i * 10,
                "response_quality": 0.8 + i * 0.02,
                "execution_time": 1.0 + i * 0.1
            }
            self.tracker.track_prompt_usage(prompt_id, usage_data)
        
        stats = self.tracker.get_prompt_statistics(prompt_id)
        
        assert stats["total_uses"] == 5
        assert stats["average_tokens"] == 120.0
        assert abs(stats["average_quality"] - 0.84) < 0.001
        assert abs(stats["average_execution_time"] - 1.2) < 0.001

    def test_suggest_prompt_improvements(self):
        """Test prompt improvement suggestions."""
        prompt_id = "improvement_prompt"
        current_prompt = "Review this code: {code}"
        
        # Track usage with varying quality
        usage_data_low = {
            "agent": "test_agent",
            "context": "code_review",
            "tokens_used": 200,
            "response_quality": 0.6,
            "execution_time": 3.0
        }
        
        usage_data_high = {
            "agent": "test_agent",
            "context": "code_review",
            "tokens_used": 150,
            "response_quality": 0.9,
            "execution_time": 2.0
        }
        
        self.tracker.track_prompt_usage(prompt_id, usage_data_low)
        self.tracker.track_prompt_usage(prompt_id, usage_data_high)
        
        suggestions = self.tracker.suggest_prompt_improvements(prompt_id, current_prompt)
        
        assert len(suggestions) > 0
        # Should have suggestions since quality is mixed
        assert isinstance(suggestions, list)

    def test_get_evolution_timeline(self):
        """Test getting prompt evolution timeline."""
        prompt_id = "timeline_prompt"
        
        # Create timeline with multiple versions
        versions = [
            {"version": "1.0", "prompt": "Basic prompt", "timestamp": "2025-01-01T00:00:00"},
            {"version": "1.1", "prompt": "Improved prompt", "timestamp": "2025-01-02T00:00:00"},
            {"version": "2.0", "prompt": "Advanced prompt", "timestamp": "2025-01-03T00:00:00"}
        ]
        
        for version in versions:
            self.tracker.track_prompt_version(prompt_id, version)
        
        timeline = self.tracker.get_evolution_timeline(prompt_id)
        
        assert len(timeline) == 3
        assert timeline[0]["version"] == "1.0"
        assert timeline[-1]["version"] == "2.0"

    def test_export_tracking_data(self):
        """Test exporting tracking data."""
        # Create some tracking data
        for i in range(3):
            prompt_id = f"export_prompt_{i}"
            usage_data = {
                "agent": f"agent_{i}",
                "context": "testing",
                "tokens_used": 100,
                "response_quality": 0.8,
                "execution_time": 1.0
            }
            self.tracker.track_prompt_usage(prompt_id, usage_data)
        
        export_file = Path(self.temp_dir) / "export.json"
        result = self.tracker.export_tracking_data(export_file)
        
        assert result.success
        assert export_file.exists()
        
        with open(export_file, 'r') as f:
            export_data = json.load(f)
        
        assert len(export_data["prompts"]) == 3
        assert "export_date" in export_data
        assert "summary" in export_data


class TestCrossRepositoryReferencer:
    """Test cross-repository referencing functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.referencer = CrossRepositoryReferencer()

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_add_repository_reference(self):
        """Test adding repository reference."""
        repo_info = {
            "name": "assetutilities",
            "path": "/path/to/assetutilities",
            "description": "Utility library for asset management",
            "primary_language": "python",
            "key_modules": ["excel", "visualization", "file_management"]
        }
        
        result = self.referencer.add_repository_reference("assetutilities", repo_info)
        
        assert result.success
        assert "assetutilities" in self.referencer.repositories
        assert self.referencer.repositories["assetutilities"]["primary_language"] == "python"

    def test_create_cross_references(self):
        """Test creating cross-references between repositories."""
        # Add test repositories
        repos = [
            {
                "name": "repo1",
                "description": "Repository 1 with Excel utilities",
                "key_modules": ["excel", "data_processing"]
            },
            {
                "name": "repo2", 
                "description": "Repository 2 with visualization tools",
                "key_modules": ["visualization", "charts", "data_processing"]
            }
        ]
        
        for repo in repos:
            self.referencer.add_repository_reference(repo["name"], repo)
        
        references = self.referencer.create_cross_references()
        
        assert len(references) > 0
        # Should find connection through "data_processing"
        assert any("data_processing" in ref["common_areas"] for ref in references)

    def test_find_related_repositories(self):
        """Test finding related repositories."""
        # Add repositories with overlapping functionality
        test_repos = {
            "financial": {
                "name": "financial",
                "key_modules": ["accounting", "reporting", "excel"],
                "tags": ["finance", "business", "data"]
            },
            "analytics": {
                "name": "analytics",
                "key_modules": ["visualization", "reporting", "statistics"],
                "tags": ["data", "analysis", "charts"]
            },
            "utilities": {
                "name": "utilities",
                "key_modules": ["excel", "file_management", "helpers"],
                "tags": ["tools", "utilities", "data"]
            }
        }
        
        for repo_name, repo_info in test_repos.items():
            self.referencer.add_repository_reference(repo_name, repo_info)
        
        related = self.referencer.find_related_repositories("financial", similarity_threshold=0.1)
        
        assert len(related) > 0
        # Should find analytics (common: reporting, data tag) and utilities (common: excel, data tag)
        related_names = [r["repository"] for r in related]
        assert "analytics" in related_names or "utilities" in related_names

    def test_generate_reference_map(self):
        """Test generating reference map."""
        # Add test repositories
        repos = {
            "core": {"name": "core", "key_modules": ["base", "utils"]},
            "web": {"name": "web", "key_modules": ["api", "utils"]},
            "data": {"name": "data", "key_modules": ["processing", "utils"]}
        }
        
        for repo_name, repo_info in repos.items():
            self.referencer.add_repository_reference(repo_name, repo_info)
        
        reference_map = self.referencer.generate_reference_map()
        
        assert "repositories" in reference_map
        assert "cross_references" in reference_map
        assert len(reference_map["repositories"]) == 3
        
        # Should find connections through "utils" module
        cross_refs = reference_map["cross_references"]
        assert len(cross_refs) > 0

    def test_export_references(self):
        """Test exporting references to file."""
        # Add a test repository
        self.referencer.add_repository_reference("test_repo", {
            "name": "test_repo",
            "description": "Test repository",
            "key_modules": ["test_module"]
        })
        
        export_file = Path(self.temp_dir) / "references.yaml"
        result = self.referencer.export_references(export_file)
        
        assert result.success
        assert export_file.exists()
        
        with open(export_file, 'r') as f:
            exported_data = yaml.safe_load(f)
        
        assert "repositories" in exported_data
        assert "test_repo" in exported_data["repositories"]


class TestEnhancedSpecsConfig:
    """Test enhanced specs configuration."""

    def test_create_basic_config(self):
        """Test creating basic enhanced specs configuration."""
        config = EnhancedSpecsConfig(
            agent_name="test_agent",
            workflow_hooks=[],
            cross_repo_references=[],
            prompt_evolution_enabled=True
        )
        
        assert config.agent_name == "test_agent"
        assert config.prompt_evolution_enabled is True
        assert config.auto_refresh_enabled is True  # default
        assert len(config.workflow_hooks) == 0

    def test_config_from_dict(self):
        """Test creating configuration from dictionary."""
        config_data = {
            "agent_name": "finance_agent",
            "integration_type": "enhanced_create_specs",
            "workflow_hooks": [
                {
                    "name": "documentation_hook",
                    "trigger": "on_completion",
                    "action": "generate_docs",
                    "config": {"format": "markdown"}
                }
            ],
            "cross_repo_references": ["assetutilities", "pyproject-starter"],
            "prompt_evolution_enabled": True,
            "auto_refresh_enabled": False,
            "refresh_interval": 3600
        }
        
        config = EnhancedSpecsConfig.from_dict(config_data)
        
        assert config.agent_name == "finance_agent"
        assert config.integration_type == "enhanced_create_specs"
        assert len(config.workflow_hooks) == 1
        assert config.workflow_hooks[0].name == "documentation_hook"
        assert len(config.cross_repo_references) == 2
        assert config.auto_refresh_enabled is False
        assert config.refresh_interval == 3600

    def test_config_to_dict(self):
        """Test converting configuration to dictionary."""
        hook = WorkflowHook(
            name="test_hook",
            trigger="on_start",
            action="initialize"
        )
        
        config = EnhancedSpecsConfig(
            agent_name="test_agent",
            workflow_hooks=[hook],
            cross_repo_references=["repo1", "repo2"]
        )
        
        data = config.to_dict()
        
        assert data["agent_name"] == "test_agent"
        assert len(data["workflow_hooks"]) == 1
        assert data["workflow_hooks"][0]["name"] == "test_hook"
        assert len(data["cross_repo_references"]) == 2
        assert "repo1" in data["cross_repo_references"]

    def test_config_validation(self):
        """Test configuration validation."""
        # Valid config
        valid_config = EnhancedSpecsConfig(
            agent_name="valid_agent",
            workflow_hooks=[],
            cross_repo_references=[]
        )
        assert valid_config.is_valid()
        
        # Invalid config (missing agent name)
        invalid_config = EnhancedSpecsConfig(
            agent_name="",
            workflow_hooks=[],
            cross_repo_references=[]
        )
        assert not invalid_config.is_valid()


class TestWorkflowRefresher:
    """Test workflow refresh functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.refresher = WorkflowRefresher(
            agent_dir=Path(self.temp_dir),
            refresh_interval=60  # 1 minute for testing
        )

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_schedule_refresh(self):
        """Test scheduling workflow refresh."""
        refresh_config = {
            "triggers": ["repository_change", "spec_update"],
            "actions": ["update_context", "regenerate_prompts"],
            "conditions": {"min_changes": 5}
        }
        
        result = self.refresher.schedule_refresh(refresh_config)
        
        assert result.success
        assert self.refresher.is_refresh_scheduled()

    def test_check_refresh_conditions(self):
        """Test checking refresh trigger conditions."""
        # Mock some changes
        changes = [
            {"type": "file_change", "path": "src/module.py", "timestamp": datetime.now().isoformat()},
            {"type": "spec_update", "spec": "test_spec", "timestamp": datetime.now().isoformat()},
            {"type": "dependency_change", "package": "numpy", "timestamp": datetime.now().isoformat()}
        ]
        
        conditions = {"min_changes": 2, "max_age_hours": 24}
        
        should_refresh = self.refresher.check_refresh_conditions(changes, conditions)
        
        assert should_refresh is True  # 3 changes >= min_changes of 2

    def test_execute_refresh(self):
        """Test executing workflow refresh."""
        # Create a mock agent configuration
        agent_config = {
            "name": "test_agent",
            "context_sources": ["repo1", "repo2"],
            "last_update": "2025-01-01T00:00:00"
        }
        
        config_file = Path(self.temp_dir) / "agent.yaml"
        with open(config_file, 'w') as f:
            yaml.dump(agent_config, f)
        
        refresh_actions = ["update_context", "refresh_templates"]
        
        with patch('assetutilities.agent_os.commands.specs_integration.WorkflowRefresher._update_context') as mock_update:
            mock_update.return_value = {"success": True, "updated_files": 2}
            
            result = self.refresher.execute_refresh(refresh_actions)
        
        assert result.success
        assert "update_context" in result.data
        assert result.data["update_context"]["updated_files"] == 2

    def test_monitor_changes(self):
        """Test monitoring for changes that trigger refresh."""
        # Create test files to monitor
        test_file = Path(self.temp_dir) / "test_file.py"
        test_file.write_text("# Test file content")
        
        monitor_config = {
            "watch_paths": [str(self.temp_dir)],
            "file_patterns": ["*.py", "*.yaml"],
            "ignore_patterns": ["__pycache__", "*.pyc"]
        }
        
        with patch('assetutilities.agent_os.commands.specs_integration.WorkflowRefresher._detect_file_changes') as mock_detect:
            mock_detect.return_value = [
                {"path": str(test_file), "type": "modified", "timestamp": datetime.now()}
            ]
            
            changes = self.refresher.monitor_changes(monitor_config)
        
        assert len(changes) > 0
        assert changes[0]["type"] == "modified"

    def test_get_refresh_status(self):
        """Test getting refresh status."""
        # Schedule a refresh
        self.refresher.schedule_refresh({"triggers": ["test"]})
        
        status = self.refresher.get_refresh_status()
        
        assert "scheduled" in status
        assert "last_refresh" in status
        assert "next_refresh" in status
        assert status["scheduled"] is True


class TestSpecsIntegrationManager:
    """Test the main specs integration manager."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = SpecsIntegrationManager(agent_dir=Path(self.temp_dir))

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_setup_enhanced_specs_integration(self):
        """Test setting up enhanced specs integration."""
        config = EnhancedSpecsConfig(
            agent_name="integration_test_agent",
            workflow_hooks=[
                WorkflowHook("test_hook", "on_completion", "export_results")
            ],
            cross_repo_references=["assetutilities", "pyproject-starter"]
        )
        
        result = self.manager.setup_enhanced_specs_integration(config)
        
        assert result.success
        
        # Verify configuration file was created
        config_file = self.manager.agent_dir / "workflows" / "enhanced_specs.yaml"
        assert config_file.exists()
        
        with open(config_file, 'r') as f:
            saved_config = yaml.safe_load(f)
        
        assert saved_config["agent_name"] == "integration_test_agent"
        assert len(saved_config["workflow_hooks"]) == 1

    def test_initialize_prompt_evolution(self):
        """Test initializing prompt evolution tracking."""
        agent_name = "evolution_test_agent"
        
        result = self.manager.initialize_prompt_evolution(agent_name)
        
        assert result.success
        
        # Verify tracking directory was created
        tracking_dir = self.manager.agent_dir / "workflows" / "prompt_tracking"
        assert tracking_dir.exists()

    def test_setup_cross_repo_references(self):
        """Test setting up cross-repository references."""
        repo_references = [
            {
                "name": "assetutilities",
                "path": "/path/to/assetutilities",
                "description": "Utility library",
                "key_modules": ["excel", "visualization"]
            },
            {
                "name": "pyproject-starter",
                "path": "/path/to/pyproject-starter", 
                "description": "Project templates",
                "key_modules": ["templates", "configuration"]
            }
        ]
        
        result = self.manager.setup_cross_repo_references(repo_references)
        
        assert result.success
        
        # Verify references file was created
        references_file = self.manager.agent_dir / "context" / "repository" / "cross_references.yaml"
        assert references_file.exists()
        
        with open(references_file, 'r') as f:
            references_data = yaml.safe_load(f)
        
        assert len(references_data["repositories"]) == 2
        assert "assetutilities" in references_data["repositories"]

    def test_configure_workflow_refresh(self):
        """Test configuring workflow refresh."""
        refresh_config = {
            "enabled": True,
            "interval": 3600,  # 1 hour
            "triggers": ["repository_change", "spec_update"],
            "actions": ["update_context", "refresh_prompts"],
            "conditions": {"min_changes": 3}
        }
        
        result = self.manager.configure_workflow_refresh(refresh_config)
        
        assert result.success
        
        # Verify refresh configuration was saved
        refresh_file = self.manager.agent_dir / "workflows" / "refresh_config.yaml"
        assert refresh_file.exists()
        
        with open(refresh_file, 'r') as f:
            saved_config = yaml.safe_load(f)
        
        assert saved_config["enabled"] is True
        assert saved_config["interval"] == 3600

    def test_create_integration_complete(self):
        """Test complete integration setup."""
        integration_config = {
            "agent_name": "complete_test_agent",
            "workflow_hooks": [
                {
                    "name": "documentation_hook",
                    "trigger": "on_completion",
                    "action": "generate_documentation",
                    "config": {"format": "markdown"}
                }
            ],
            "cross_repo_references": ["assetutilities"],
            "prompt_evolution_enabled": True,
            "auto_refresh_enabled": True,
            "refresh_interval": 7200
        }
        
        result = self.manager.create_integration(integration_config)
        
        assert result.success
        
        # Verify all integration components were created
        expected_files = [
            "workflows/enhanced_specs.yaml",
            "workflows/prompt_tracking",
            "context/repository/cross_references.yaml",
            "workflows/refresh_config.yaml"
        ]
        
        for file_path in expected_files:
            full_path = self.manager.agent_dir / file_path
            assert full_path.exists(), f"Expected file not found: {file_path}"

    def test_get_integration_status(self):
        """Test getting integration status."""
        # Setup some integration components
        self.manager.initialize_prompt_evolution("status_test_agent")
        
        status = self.manager.get_integration_status()
        
        assert "prompt_evolution" in status
        assert "cross_references" in status
        assert "workflow_refresh" in status
        assert status["prompt_evolution"]["enabled"] is True

    def test_validate_integration(self):
        """Test integration validation."""
        # Create a complete integration
        config = EnhancedSpecsConfig(
            agent_name="validation_test_agent",
            workflow_hooks=[],
            cross_repo_references=[]
        )
        
        self.manager.setup_enhanced_specs_integration(config)
        self.manager.initialize_prompt_evolution("validation_test_agent")
        
        # Create the required directory structure for validation
        (self.manager.agent_dir / "context" / "repository").mkdir(parents=True, exist_ok=True)
        
        validation_result = self.manager.validate_integration()
        
        assert validation_result.success
        assert len(validation_result.data["components"]) > 0