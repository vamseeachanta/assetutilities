"""Tests for create-module-agent command."""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import patch

from assetutilities.agent_os.commands.create_module_agent import (
    CreateModuleAgentCommand,
    ArgumentParser,
    AgentStructureGenerator,
    ConfigGenerator
)


class TestArgumentParser:
    """Test argument parsing for create-module-agent command."""

    def test_parse_basic_module_name(self):
        """Test parsing basic module name."""
        parser = ArgumentParser()
        args = parser.parse(["/create-module-agent", "finance-analytics"])
        
        assert args.module_name == "finance-analytics"
        assert args.type == "general-purpose"  # default
        assert args.repos == []
        assert args.context_cache is True  # default
        assert args.templates == []

    def test_parse_with_all_options(self):
        """Test parsing with all options specified."""
        parser = ArgumentParser()
        args = parser.parse([
            "/create-module-agent", "devops",
            "--type", "infrastructure",
            "--repos", "assetutilities,pyproject-starter",
            "--context-cache", "false",
            "--templates", "infrastructure,monitoring"
        ])
        
        assert args.module_name == "devops"
        assert args.type == "infrastructure"
        assert args.repos == ["assetutilities", "pyproject-starter"]
        assert args.context_cache is False
        assert args.templates == ["infrastructure", "monitoring"]

    def test_invalid_module_name(self):
        """Test validation of module names."""
        parser = ArgumentParser()
        
        with pytest.raises(ValueError, match="Invalid module name"):
            parser.parse(["/create-module-agent", "invalid@name"])
        
        with pytest.raises(ValueError, match="Invalid module name"):
            parser.parse(["/create-module-agent", ""])

    def test_missing_module_name(self):
        """Test error when module name is missing."""
        parser = ArgumentParser()
        
        with pytest.raises(ValueError, match="Module name is required"):
            parser.parse(["/create-module-agent"])


class TestAgentStructureGenerator:
    """Test agent folder structure generation."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.agents_dir = Path(self.temp_dir) / "agents"
        self.generator = AgentStructureGenerator(self.agents_dir)

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_create_basic_structure(self):
        """Test creation of basic agent structure."""
        module_path = self.generator.create_structure("finance-analytics")
        
        # Verify main directory
        assert module_path.exists()
        assert module_path.name == "finance-analytics"
        
        # Verify subdirectories
        assert (module_path / "context" / "repository").exists()
        assert (module_path / "context" / "external").exists()
        assert (module_path / "context" / "optimized").exists()
        assert (module_path / "templates" / "responses").exists()
        assert (module_path / "templates" / "prompts").exists()
        assert (module_path / "workflows").exists()

    def test_create_structure_existing_directory(self):
        """Test handling of existing directory."""
        # Create directory first
        module_path = self.generator.create_structure("test-agent")
        
        # Try to create again - should not raise error
        module_path2 = self.generator.create_structure("test-agent")
        assert module_path == module_path2

    def test_validate_module_name(self):
        """Test module name validation."""
        # Valid names
        assert self.generator.validate_module_name("finance-analytics")
        assert self.generator.validate_module_name("simple_name")
        assert self.generator.validate_module_name("name123")
        
        # Invalid names
        assert not self.generator.validate_module_name("invalid@name")
        assert not self.generator.validate_module_name("")
        assert not self.generator.validate_module_name("name with spaces")


class TestConfigGenerator:
    """Test agent configuration file generation."""

    def test_generate_basic_config(self):
        """Test generation of basic agent configuration."""
        generator = ConfigGenerator()
        config = generator.generate_agent_config(
            module_name="finance-analytics",
            agent_type="general-purpose",
            repos=[],
            templates=[]
        )
        
        assert config["name"] == "finance-analytics"
        assert config["type"] == "general-purpose"
        assert config["version"] == "1.0.0"
        assert "created_at" in config
        assert config["repositories"] == []
        assert config["templates"] == []

    def test_generate_config_with_options(self):
        """Test generation with all options."""
        generator = ConfigGenerator()
        config = generator.generate_agent_config(
            module_name="devops",
            agent_type="infrastructure",
            repos=["assetutilities", "pyproject-starter"],
            templates=["infrastructure", "monitoring"]
        )
        
        assert config["name"] == "devops"
        assert config["type"] == "infrastructure"
        assert config["repositories"] == ["assetutilities", "pyproject-starter"]
        assert config["templates"] == ["infrastructure", "monitoring"]
        assert "context_optimization" in config
        assert config["context_optimization"]["enabled"] is True


class TestCreateModuleAgentCommand:
    """Test main command execution."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.command = CreateModuleAgentCommand(base_dir=Path(self.temp_dir))

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_execute_basic_command(self):
        """Test execution of basic create-module-agent command."""
        result = self.command.execute([
            "/create-module-agent", "finance-analytics"
        ])
        
        assert result.success is True
        assert "finance-analytics" in result.message
        
        # Verify structure was created
        agent_dir = Path(self.temp_dir) / "agents" / "finance-analytics"
        assert agent_dir.exists()
        assert (agent_dir / "agent.yaml").exists()

    def test_execute_with_options(self):
        """Test execution with all options."""
        result = self.command.execute([
            "/create-module-agent", "devops",
            "--type", "infrastructure",
            "--repos", "assetutilities,pyproject-starter"
        ])
        
        assert result.success is True
        
        # Verify configuration includes options
        agent_dir = Path(self.temp_dir) / "agents" / "devops"
        config_file = agent_dir / "agent.yaml"
        assert config_file.exists()

    def test_execute_with_documentation_integration(self):
        """Test execution includes documentation integration."""
        with patch.object(self.command.doc_scanner, 'scan_repositories') as mock_scan:
            mock_scan.return_value = {
                "assetutilities": {"docs": [], "references": []}
            }
            
            result = self.command.execute([
                "/create-module-agent", "test-agent",
                "--repos", "assetutilities"
            ])
            
            assert result.success is True
            mock_scan.assert_called_once_with(["assetutilities"])

    def test_execute_invalid_arguments(self):
        """Test execution with invalid arguments."""
        result = self.command.execute([
            "/create-module-agent", "invalid@name"
        ])
        
        assert result.success is False
        assert "Invalid module name" in result.message