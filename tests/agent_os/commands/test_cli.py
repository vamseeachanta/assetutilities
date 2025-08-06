"""Tests for command line interface."""

import pytest
import tempfile
import shutil
import sys
from pathlib import Path
from unittest.mock import Mock, patch, mock_open
from io import StringIO

from assetutilities.agent_os.commands.cli import (
    CLIManager,
    InteractiveMode,
    ProgressIndicator,
    HelpSystem,
    ErrorHandler,
    CommandLineInterface
)


class TestCLIManager:
    """Test CLI manager functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.cli_manager = CLIManager()

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_parse_basic_command(self):
        """Test parsing basic command."""
        args = ["create-module-agent", "test-agent"]
        
        parsed = self.cli_manager.parse_command(args)
        
        assert parsed.command == "create-module-agent"
        assert parsed.module_name == "test-agent"
        assert parsed.agent_type == "general-purpose"  # default
        assert parsed.options == {}

    def test_parse_command_with_options(self):
        """Test parsing command with all options."""
        args = [
            "create-module-agent", "finance-agent",
            "--type", "engineering",
            "--repos", "assetutilities,pyproject-starter",
            "--context-cache", "true",
            "--templates", "engineering,documentation"
        ]
        
        parsed = self.cli_manager.parse_command(args)
        
        assert parsed.command == "create-module-agent"
        assert parsed.module_name == "finance-agent"
        assert parsed.agent_type == "engineering"
        assert parsed.repos == ["assetutilities", "pyproject-starter"]
        assert parsed.context_cache is True
        assert parsed.templates == ["engineering", "documentation"]

    def test_parse_invalid_command(self):
        """Test parsing invalid command."""
        args = ["invalid-command", "test"]
        
        with pytest.raises(ValueError) as exc_info:
            self.cli_manager.parse_command(args)
        
        assert "Unknown command" in str(exc_info.value)

    def test_parse_missing_module_name(self):
        """Test parsing command without module name."""
        args = ["create-module-agent"]
        
        with pytest.raises(ValueError) as exc_info:
            self.cli_manager.parse_command(args)
        
        assert "Module name is required" in str(exc_info.value)

    def test_validate_module_name(self):
        """Test module name validation."""
        # Valid names
        assert self.cli_manager.validate_module_name("finance-analytics")
        assert self.cli_manager.validate_module_name("auth_system")
        assert self.cli_manager.validate_module_name("user-management")
        
        # Invalid names
        assert not self.cli_manager.validate_module_name("Finance Analytics")  # spaces
        assert not self.cli_manager.validate_module_name("finance@analytics")  # special chars
        assert not self.cli_manager.validate_module_name("")  # empty
        assert not self.cli_manager.validate_module_name("a")  # too short

    def test_validate_options(self):
        """Test option validation."""
        valid_options = {
            "agent_type": "engineering",
            "repos": ["assetutilities"],
            "context_cache": True,
            "templates": ["engineering"]
        }
        
        result = self.cli_manager.validate_options(valid_options)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_invalid_options(self):
        """Test validation with invalid options."""
        invalid_options = {
            "agent_type": "invalid_type",
            "repos": [],
            "templates": ["nonexistent_template"]
        }
        
        result = self.cli_manager.validate_options(invalid_options)
        assert not result.is_valid
        assert len(result.errors) > 0

    def test_get_help_text(self):
        """Test getting help text."""
        help_text = self.cli_manager.get_help_text()
        
        assert "create-module-agent" in help_text
        assert "Options:" in help_text
        assert "--type" in help_text
        assert "--repos" in help_text

    def test_get_command_help(self):
        """Test getting specific command help."""
        help_text = self.cli_manager.get_command_help("create-module-agent")
        
        assert "create-module-agent" in help_text
        assert "module_name" in help_text
        assert "Examples:" in help_text


class TestInteractiveMode:
    """Test interactive mode functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.interactive = InteractiveMode()

    def test_prompt_for_missing_module_name(self):
        """Test prompting for missing module name."""
        with patch('builtins.input', return_value='test-agent'):
            module_name = self.interactive.prompt_for_module_name()
            assert module_name == 'test-agent'

    def test_prompt_for_agent_type(self):
        """Test prompting for agent type."""
        with patch('builtins.input', return_value='2'):  # engineering
            agent_type = self.interactive.prompt_for_agent_type()
            assert agent_type == 'engineering'

    def test_prompt_for_repositories(self):
        """Test prompting for repositories."""
        with patch('builtins.input', return_value='assetutilities,pyproject-starter'):
            repos = self.interactive.prompt_for_repositories()
            assert repos == ['assetutilities', 'pyproject-starter']

    def test_prompt_for_templates(self):
        """Test prompting for templates."""
        with patch('builtins.input', return_value='engineering,documentation'):
            templates = self.interactive.prompt_for_templates()
            assert templates == ['engineering', 'documentation']

    def test_confirm_action(self):
        """Test action confirmation."""
        with patch('builtins.input', return_value='y'):
            result = self.interactive.confirm_action("Create agent 'test-agent'?")
            assert result is True
        
        with patch('builtins.input', return_value='n'):
            result = self.interactive.confirm_action("Create agent 'test-agent'?")
            assert result is False

    def test_display_summary(self):
        """Test displaying command summary."""
        options = {
            "module_name": "test-agent",
            "agent_type": "engineering",
            "repos": ["assetutilities"],
            "templates": ["engineering"]
        }
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            self.interactive.display_summary(options)
            output = mock_stdout.getvalue()
        
        assert "test-agent" in output
        assert "engineering" in output
        assert "assetutilities" in output

    def test_collect_missing_options(self):
        """Test collecting missing options interactively."""
        partial_options = {
            "module_name": "test-agent"
        }
        
        with patch('builtins.input', side_effect=['2', 'assetutilities', 'y', 'engineering']):
            complete_options = self.interactive.collect_missing_options(partial_options)
        
        assert complete_options["module_name"] == "test-agent"
        assert complete_options["agent_type"] == "engineering"
        assert complete_options["repos"] == ["assetutilities"]

    def test_handle_validation_errors(self):
        """Test handling validation errors interactively."""
        errors = [
            "Invalid agent type: 'invalid_type'",
            "Repository 'nonexistent' not found"
        ]
        
        with patch('builtins.input', side_effect=['engineering', 'assetutilities']):
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                corrected_options = self.interactive.handle_validation_errors(errors, {})
                output = mock_stdout.getvalue()
        
        assert "Validation errors found" in output
        assert corrected_options is not None


class TestProgressIndicator:
    """Test progress indicator functionality."""

    def test_create_simple_progress(self):
        """Test creating simple progress indicator."""
        progress = ProgressIndicator("Creating agent structure...")
        
        assert progress.message == "Creating agent structure..."
        assert progress.total_steps == 1
        assert progress.current_step == 0

    def test_create_stepped_progress(self):
        """Test creating stepped progress indicator."""
        steps = [
            "Setting up directory structure",
            "Generating configuration files",
            "Installing templates",
            "Finalizing setup"
        ]
        
        progress = ProgressIndicator("Creating agent", steps=steps)
        
        assert progress.total_steps == 4
        assert progress.steps == steps

    def test_update_progress(self):
        """Test updating progress."""
        progress = ProgressIndicator("Testing", steps=["Step 1", "Step 2", "Step 3"])
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            progress.update("Starting Step 1")
            output = mock_stdout.getvalue()
        
        assert "Starting Step 1" in output
        assert "[1/3]" in output

    def test_advance_step(self):
        """Test advancing to next step."""
        progress = ProgressIndicator("Testing", steps=["Step 1", "Step 2"])
        
        progress.advance("Step 1 completed")
        assert progress.current_step == 1
        
        progress.advance("Step 2 completed")
        assert progress.current_step == 2

    def test_complete_progress(self):
        """Test completing progress."""
        progress = ProgressIndicator("Testing")
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            progress.complete("Task completed successfully!")
            output = mock_stdout.getvalue()
        
        assert "✓" in output
        assert "completed successfully" in output

    def test_progress_with_spinner(self):
        """Test progress with spinner animation."""
        progress = ProgressIndicator("Processing...", show_spinner=True)
        
        # Test spinner animation
        with patch('sys.stdout', new_callable=StringIO):
            for i in range(4):
                progress.spin()
                # Verify spinner cycles through characters
                expected_char = progress.spinner_chars[i % len(progress.spinner_chars)]
                assert progress.current_spinner == expected_char

    def test_progress_with_percentage(self):
        """Test progress with percentage display."""
        progress = ProgressIndicator("Downloading", total_items=100, show_percentage=True)
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            progress.update_percentage(25)
            output = mock_stdout.getvalue()
        
        assert "25%" in output


class TestHelpSystem:
    """Test help system functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.help_system = HelpSystem()

    def test_get_general_help(self):
        """Test getting general help."""
        help_text = self.help_system.get_general_help()
        
        assert "Agent OS Command Line Interface" in help_text
        assert "Available Commands:" in help_text
        assert "create-module-agent" in help_text

    def test_get_command_help(self):
        """Test getting command-specific help."""
        help_text = self.help_system.get_command_help("create-module-agent")
        
        assert "create-module-agent" in help_text
        assert "Usage:" in help_text
        assert "Options:" in help_text
        assert "Examples:" in help_text

    def test_get_option_help(self):
        """Test getting option-specific help."""
        help_text = self.help_system.get_option_help("--type")
        
        assert "--type" in help_text
        assert "agent type" in help_text.lower()
        assert "general-purpose" in help_text

    def test_search_help(self):
        """Test searching help content."""
        results = self.help_system.search_help("repository")
        
        assert len(results) > 0
        assert any("--repos" in result for result in results)

    def test_get_examples(self):
        """Test getting command examples."""
        examples = self.help_system.get_examples("create-module-agent")
        
        assert len(examples) > 0
        assert any("create-module-agent" in example for example in examples)

    def test_format_help_text(self):
        """Test help text formatting."""
        raw_help = {
            "title": "Test Command",
            "description": "A test command for demonstration",
            "usage": "test-command [options]",
            "options": {
                "--verbose": "Enable verbose output",
                "--help": "Show help message"
            }
        }
        
        formatted = self.help_system.format_help_text(raw_help)
        
        assert "Test Command" in formatted
        assert "--verbose" in formatted
        assert "Enable verbose output" in formatted


class TestErrorHandler:
    """Test error handling functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.error_handler = ErrorHandler()

    def test_handle_validation_error(self):
        """Test handling validation errors."""
        error = ValueError("Invalid module name: 'test name'")
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = self.error_handler.handle_error(error)
            error_output = mock_stderr.getvalue()
        
        assert not result.should_continue
        assert "Invalid module name" in error_output
        assert result.error_code == 1

    def test_handle_file_not_found_error(self):
        """Test handling file not found errors."""
        error = FileNotFoundError("Template file not found: engineering.yaml")
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = self.error_handler.handle_error(error)
            error_output = mock_stderr.getvalue()
        
        assert not result.should_continue
        assert "Template file not found" in error_output
        assert result.error_code == 2

    def test_handle_permission_error(self):
        """Test handling permission errors."""
        error = PermissionError("Permission denied: cannot create directory")
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = self.error_handler.handle_error(error)
            error_output = mock_stderr.getvalue()
        
        assert not result.should_continue
        assert "Permission denied" in error_output
        assert result.error_code == 3

    def test_handle_keyboard_interrupt(self):
        """Test handling keyboard interrupt."""
        error = KeyboardInterrupt()
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = self.error_handler.handle_error(error)
            error_output = mock_stderr.getvalue()
        
        assert not result.should_continue
        assert "Operation cancelled" in error_output
        assert result.error_code == 130

    def test_handle_unexpected_error(self):
        """Test handling unexpected errors."""
        error = RuntimeError("Something went wrong internally")
        
        with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
            result = self.error_handler.handle_error(error)
            error_output = mock_stderr.getvalue()
        
        assert not result.should_continue
        assert "Unexpected error" in error_output
        assert result.error_code == 1

    def test_suggest_solutions(self):
        """Test error solution suggestions."""
        error = ValueError("Invalid agent type: 'custom'")
        
        solutions = self.error_handler.suggest_solutions(error)
        
        assert len(solutions) > 0
        assert any("available agent types" in solution.lower() for solution in solutions)

    def test_format_error_message(self):
        """Test error message formatting."""
        error = ValueError("Test error message")
        context = {"command": "create-module-agent", "module_name": "test"}
        
        formatted = self.error_handler.format_error_message(error, context)
        
        assert "Error:" in formatted
        assert "Test error message" in formatted
        assert "create-module-agent" in formatted

    def test_recovery_suggestions(self):
        """Test recovery suggestions."""
        error = FileNotFoundError("Template not found")
        
        suggestions = self.error_handler.get_recovery_suggestions(error)
        
        assert len(suggestions) > 0
        assert any("check template" in suggestion.lower() for suggestion in suggestions)


class TestCommandLineInterface:
    """Test the main command line interface."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.cli = CommandLineInterface()

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_execute_basic_command(self):
        """Test executing basic command."""
        args = ["create-module-agent", "test-agent"]
        
        with patch('assetutilities.agent_os.commands.create_module_agent.CreateModuleAgentCommand') as mock_command:
            mock_instance = Mock()
            mock_command.return_value = mock_instance
            mock_instance.execute.return_value = Mock(success=True, message="Agent created successfully")
            
            exit_code = self.cli.run(args)
        
        assert exit_code == 0
        mock_instance.execute.assert_called_once()

    def test_execute_command_with_interactive_mode(self):
        """Test executing command with missing options in interactive mode."""
        args = ["create-module-agent"]  # Missing module name
        
        with patch('builtins.input', side_effect=['test-agent', '1', '', 'y']):  # Provide missing inputs
            with patch('assetutilities.agent_os.commands.create_module_agent.CreateModuleAgentCommand') as mock_command:
                mock_instance = Mock()
                mock_command.return_value = mock_instance
                mock_instance.execute.return_value = Mock(success=True, message="Agent created successfully")
                
                exit_code = self.cli.run(args, interactive=True)
        
        assert exit_code == 0

    def test_execute_help_command(self):
        """Test executing help command."""
        args = ["--help"]
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            exit_code = self.cli.run(args)
            output = mock_stdout.getvalue()
        
        assert exit_code == 0
        assert "Agent OS Command Line Interface" in output

    def test_execute_command_help(self):
        """Test executing command-specific help."""
        args = ["create-module-agent", "--help"]
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            exit_code = self.cli.run(args)
            output = mock_stdout.getvalue()
        
        assert exit_code == 0
        assert "create-module-agent" in output

    def test_execute_invalid_command(self):
        """Test executing invalid command."""
        args = ["invalid-command"]
        
        with patch('sys.stderr', new_callable=StringIO):
            exit_code = self.cli.run(args)
        
        assert exit_code != 0

    def test_execute_with_validation_errors(self):
        """Test executing command with validation errors."""
        args = ["create-module-agent", "Invalid Name"]  # Invalid module name
        
        with patch('sys.stderr', new_callable=StringIO):
            exit_code = self.cli.run(args)
        
        assert exit_code != 0

    def test_execute_with_progress_indicator(self):
        """Test executing command with progress indicator."""
        args = ["create-module-agent", "test-agent", "--progress"]
        
        with patch('assetutilities.agent_os.commands.create_module_agent.CreateModuleAgentCommand') as mock_command:
            mock_instance = Mock()
            mock_command.return_value = mock_instance
            mock_instance.execute.return_value = Mock(success=True, message="Agent created successfully")
            
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                exit_code = self.cli.run(args)
                output = mock_stdout.getvalue()
        
        assert exit_code == 0
        # Should show progress indicators
        assert any(char in output for char in ['[', ']', '...'])

    def test_execute_with_verbose_output(self):
        """Test executing command with verbose output."""
        args = ["create-module-agent", "test-agent", "--verbose"]
        
        with patch('assetutilities.agent_os.commands.create_module_agent.CreateModuleAgentCommand') as mock_command:
            mock_instance = Mock()
            mock_command.return_value = mock_instance
            mock_instance.execute.return_value = Mock(success=True, message="Agent created successfully")
            
            with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
                exit_code = self.cli.run(args)
                output = mock_stdout.getvalue()
        
        assert exit_code == 0
        # Should show verbose information
        assert len(output) > 50  # More detailed output

    def test_execute_with_dry_run(self):
        """Test executing command with dry run option."""
        args = ["create-module-agent", "test-agent", "--dry-run"]
        
        with patch('sys.stdout', new_callable=StringIO) as mock_stdout:
            exit_code = self.cli.run(args)
            output = mock_stdout.getvalue()
        
        assert exit_code == 0
        assert "Dry run" in output
        assert "Would create" in output

    def test_error_recovery(self):
        """Test error recovery mechanisms."""
        args = ["create-module-agent", "test-agent"]
        
        with patch('assetutilities.agent_os.commands.create_module_agent.CreateModuleAgentCommand') as mock_command:
            mock_instance = Mock()
            mock_command.return_value = mock_instance
            mock_instance.execute.side_effect = FileNotFoundError("Template not found")
            
            with patch('sys.stderr', new_callable=StringIO) as mock_stderr:
                exit_code = self.cli.run(args)
                error_output = mock_stderr.getvalue()
        
        assert exit_code != 0
        assert "Template not found" in error_output
        assert "Suggestions:" in error_output

    def test_configuration_loading(self):
        """Test loading configuration from file."""
        config_file = Path(self.temp_dir) / "config.yaml"
        config_data = {
            "default_agent_type": "engineering",
            "default_repos": ["assetutilities"],
            "context_cache": True
        }
        
        import yaml
        with open(config_file, 'w') as f:
            yaml.dump(config_data, f)
        
        args = ["create-module-agent", "test-agent", "--config", str(config_file)]
        
        with patch('assetutilities.agent_os.commands.create_module_agent.CreateModuleAgentCommand') as mock_command:
            mock_instance = Mock()
            mock_command.return_value = mock_instance
            mock_instance.execute.return_value = Mock(success=True)
            
            exit_code = self.cli.run(args)
        
        assert exit_code == 0
        # Verify configuration was applied
        call_args = mock_instance.execute.call_args
        assert call_args is not None

    def test_logging_configuration(self):
        """Test logging configuration and output."""
        args = ["create-module-agent", "test-agent", "--log-level", "DEBUG"]
        
        with patch('assetutilities.agent_os.commands.create_module_agent.CreateModuleAgentCommand') as mock_command:
            mock_instance = Mock()
            mock_command.return_value = mock_instance
            mock_instance.execute.return_value = Mock(success=True)
            
            exit_code = self.cli.run(args)
        
        assert exit_code == 0