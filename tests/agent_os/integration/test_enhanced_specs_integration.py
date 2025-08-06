"""Integration tests for enhanced specs functionality."""

import pytest
import tempfile
import yaml
from pathlib import Path
from unittest.mock import Mock, patch

from assetutilities.agent_os.integration.enhanced_specs import (
    EnhancedSpecsIntegration,
    EnhancedSpecsConfig
)
from assetutilities.agent_os.integration.prompt_evolution import PromptEvolutionTracker
from assetutilities.agent_os.commands.create_module_agent import CreateModuleAgentCommand


class TestEnhancedSpecsIntegration:
    """Test enhanced specs integration functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.agent_path = Path(self.temp_dir) / "test-agent"
        self.integration = EnhancedSpecsIntegration(self.agent_path)

    def test_config_creation(self):
        """Test enhanced specs configuration creation."""
        config = self.integration.create_enhanced_specs_config(
            "test-module", 
            ["assetutilities", "pyproject-starter"]
        )
        
        # Verify configuration structure
        assert "integration" in config
        assert config["integration"]["type"] == "enhanced_create_specs"
        assert config["integration"]["version"] == "2.0.0"
        
        assert "configuration" in config
        assert config["configuration"]["agent_module"] == "test-module"
        assert config["configuration"]["repositories"] == ["assetutilities", "pyproject-starter"]
        
        # Verify features are enabled
        features = config["configuration"]["features"]
        assert features["prompt_evolution"] is True
        assert features["executive_summaries"] is True
        assert features["mermaid_diagrams"] is True

    def test_workflow_refresh_setup(self):
        """Test workflow refresh configuration."""
        refresh_config = self.integration.setup_workflow_refresh("test-module")
        
        assert refresh_config["enabled"] is True
        assert refresh_config["module"] == "test-module"
        assert "triggers" in refresh_config
        assert "actions" in refresh_config
        assert "learning" in refresh_config

    def test_integration_hooks_creation(self):
        """Test integration hooks configuration."""
        hooks = self.integration.create_integration_hooks("test-module")
        
        expected_hooks = [
            "pre_spec_creation",
            "post_spec_creation", 
            "pre_task_execution",
            "post_task_execution",
            "on_workflow_completion"
        ]
        
        for hook in expected_hooks:
            assert hook in hooks
            assert "handler" in hooks[hook]
            assert "actions" in hooks[hook]

    def test_complete_integration(self):
        """Test complete integration process."""
        config = self.integration.integrate("test-module", ["assetutilities"])
        
        # Verify all sections are present
        assert "integration" in config
        assert "configuration" in config
        assert "workflow_refresh" in config
        assert "connection" in config
        assert "hooks" in config
        assert "metadata" in config
        
        # Verify metadata
        metadata = config["metadata"]
        assert metadata["module_name"] == "test-module"
        assert metadata["repositories"] == ["assetutilities"]
        assert "created_at" in metadata

    def test_config_save_and_load(self):
        """Test configuration save and load functionality."""
        config = self.integration.create_enhanced_specs_config("test-module", [])
        self.integration.save_config(config)
        
        # Check file was created
        config_path = self.agent_path / "workflows" / "enhanced_specs.yaml"
        assert config_path.exists()
        
        # Verify content
        with open(config_path, 'r') as f:
            loaded_config = yaml.safe_load(f)
        
        assert loaded_config == config


class TestPromptEvolutionTracker:
    """Test prompt evolution tracking functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.agent_path = Path(self.temp_dir) / "test-agent"
        self.tracker = PromptEvolutionTracker(self.agent_path)

    def test_prompt_tracking(self):
        """Test prompt tracking functionality."""
        self.tracker.track_prompt(
            prompt_content="Test prompt",
            template_name="default",
            parameters={"param1": "value1"},
            response_quality=0.8,
            execution_time=1.5,
            tokens_used=100,
            context_size=500,
            success=True
        )
        
        assert len(self.tracker.prompt_history) == 1
        
        entry = self.tracker.prompt_history[0]
        assert entry.prompt_content == "Test prompt"
        assert entry.template_name == "default"
        assert entry.response_quality == 0.8
        assert entry.execution_time == 1.5
        assert entry.tokens_used == 100
        assert entry.success is True

    def test_improvement_suggestions(self):
        """Test improvement suggestions generation."""
        # Track a low-quality prompt
        self.tracker.track_prompt(
            prompt_content="Bad prompt",
            template_name="default",
            parameters={},
            response_quality=0.3,
            execution_time=5.0,
            tokens_used=1500,
            success=False
        )
        
        entry = self.tracker.prompt_history[0]
        
        # Check that improvements were suggested
        assert len(entry.improvements) > 0
        
        # Should suggest improvements for low quality
        improvement_text = " ".join(entry.improvements)
        assert "context" in improvement_text.lower() or "examples" in improvement_text.lower()

    def test_evolution_summary_generation(self):
        """Test evolution summary generation."""
        # Add multiple entries
        for i in range(5):
            self.tracker.track_prompt(
                prompt_content=f"Test prompt {i}",
                template_name="default",
                parameters={},
                response_quality=0.7 + i * 0.05,
                execution_time=1.0,
                tokens_used=100,
                success=True
            )
        
        # Generate summary
        summary = self.tracker._generate_evolution_summary()
        
        assert "# Prompt Evolution Summary" in summary
        assert "**Total Prompts:** 5" in summary
        assert "Average Quality Score:" in summary
        assert "**Most Used Template:** default" in summary

    def test_evolution_statistics(self):
        """Test evolution statistics calculation."""
        # Add test data
        self.tracker.track_prompt("prompt1", "template1", {}, 0.8, 1.0, 100, 0, True)
        self.tracker.track_prompt("prompt2", "template2", {}, 0.9, 2.0, 200, 0, True)
        self.tracker.track_prompt("prompt3", "template1", {}, 0.7, 1.5, 150, 0, False)
        
        stats = self.tracker.get_evolution_stats()
        
        assert stats["total_prompts"] == 3
        assert abs(stats["avg_quality"] - 0.8) < 0.01
        assert abs(stats["success_rate"] - 0.667) < 0.01
        assert stats["most_used_template"] == "template1"


class TestEndToEndIntegration:
    """Test end-to-end integration scenarios."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()

    def test_create_module_agent_with_enhanced_specs(self):
        """Test creating module agent with enhanced specs integration."""
        command = CreateModuleAgentCommand(base_dir=Path(self.temp_dir))
        result = command.execute([
            "/create-module-agent", "integration-test",
            "--type", "infrastructure",
            "--repos", "assetutilities,pyproject-starter"
        ])
        
        assert result.success is True
        
        # Verify agent structure
        agent_dir = Path(self.temp_dir) / "agents" / "integration-test"
        assert agent_dir.exists()
        
        # Verify enhanced specs integration
        enhanced_config = agent_dir / "workflows" / "enhanced_specs_full.yaml"
        assert enhanced_config.exists()
        
        # Verify configuration content
        with open(enhanced_config, 'r') as f:
            config = yaml.safe_load(f)
        
        assert config["configuration"]["agent_module"] == "integration-test"
        assert "assetutilities" in config["configuration"]["repositories"]
        assert "pyproject-starter" in config["configuration"]["repositories"]

    def test_multiple_agent_creation(self):
        """Test creating multiple agents with different configurations."""
        command = CreateModuleAgentCommand(base_dir=Path(self.temp_dir))
        
        # Create first agent
        result1 = command.execute([
            "/create-module-agent", "agent-1",
            "--type", "api",
            "--repos", "assetutilities"
        ])
        
        # Create second agent
        result2 = command.execute([
            "/create-module-agent", "agent-2", 
            "--type", "data-processing",
            "--repos", "worldenergydata"
        ])
        
        assert result1.success is True
        assert result2.success is True
        
        # Verify both agents exist
        agent1_dir = Path(self.temp_dir) / "agents" / "agent-1"
        agent2_dir = Path(self.temp_dir) / "agents" / "agent-2"
        
        assert agent1_dir.exists()
        assert agent2_dir.exists()
        
        # Verify different configurations
        config1_path = agent1_dir / "workflows" / "enhanced_specs_full.yaml"
        config2_path = agent2_dir / "workflows" / "enhanced_specs_full.yaml"
        
        with open(config1_path, 'r') as f:
            config1 = yaml.safe_load(f)
        with open(config2_path, 'r') as f:
            config2 = yaml.safe_load(f)
        
        assert config1["configuration"]["repositories"] == ["assetutilities"]
        assert config2["configuration"]["repositories"] == ["worldenergydata"]

    def test_agent_with_prompt_evolution(self):
        """Test agent creation includes prompt evolution setup."""
        command = CreateModuleAgentCommand(base_dir=Path(self.temp_dir))
        result = command.execute([
            "/create-module-agent", "evolution-test"
        ])
        
        assert result.success is True
        
        # Create prompt evolution tracker
        agent_dir = Path(self.temp_dir) / "agents" / "evolution-test"
        tracker = PromptEvolutionTracker(agent_dir)
        
        # Test tracking functionality
        tracker.track_prompt(
            prompt_content="Test evolution prompt",
            template_name="default",
            parameters={},
            response_quality=0.85,
            execution_time=1.2,
            tokens_used=120,
            success=True
        )
        
        # Verify tracking works
        assert len(tracker.prompt_history) == 1
        
        # Verify evolution file is created
        evolution_file = agent_dir / "context" / "prompt_evolution.md"
        assert evolution_file.exists()
        
        # Verify content
        with open(evolution_file, 'r') as f:
            content = f.read()
        
        assert "# Prompt Evolution Summary" in content
        assert "**Total Prompts:** 1" in content

    @patch('assetutilities.agent_os.commands.create_module_agent.DocumentationScanner')
    def test_documentation_integration(self, mock_scanner):
        """Test documentation integration functionality."""
        # Mock documentation scanner
        mock_scanner.return_value.scan_repositories.return_value = {
            "assetutilities": {
                "docs": ["README.md", "docs/api.md"],
                "references": ["@assetutilities:src/", "@assetutilities:tests/"],
                "last_updated": "2025-08-06"
            }
        }
        
        command = CreateModuleAgentCommand(base_dir=Path(self.temp_dir))
        result = command.execute([
            "/create-module-agent", "doc-test",
            "--repos", "assetutilities"
        ])
        
        assert result.success is True
        
        # Verify documentation references were created
        agent_dir = Path(self.temp_dir) / "agents" / "doc-test"
        references_file = agent_dir / "context" / "repository" / "references.yaml"
        
        assert references_file.exists()
        
        with open(references_file, 'r') as f:
            references = yaml.safe_load(f)
        
        assert "assetutilities" in references
        assert references["assetutilities"]["last_updated"] == "2025-08-06"