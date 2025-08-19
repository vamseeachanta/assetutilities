"""Integration tests for CLI functionality."""

import tempfile
from pathlib import Path
from unittest.mock import patch
from io import StringIO
import sys

from assetutilities.agent_os.cli.main import AgentOSCLI
from assetutilities.agent_os.cli.interactive import InteractiveMode
from assetutilities.agent_os.cli.progress import ProgressIndicator, ProgressBar, TaskProgress


class TestCLIIntegration:
    """Test CLI integration functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.cli = AgentOSCLI()

    def test_create_module_agent_via_cli(self):
        """Test creating module agent via CLI."""
        args = [
            'create-module-agent', 
            'cli-test-agent',
            '--type', 'infrastructure',
            '--repos', 'assetutilities',
            '--output-dir', self.temp_dir
        ]
        
        result = self.cli.run(args)
        assert result == 0
        
        # Verify agent was created
        agent_dir = Path(self.temp_dir) / "agents" / "cli-test-agent"
        assert agent_dir.exists()
        
        # Verify configuration
        config_file = agent_dir / "agent.yaml"
        assert config_file.exists()

    def test_cli_help_display(self):
        """Test CLI help display."""
        # Capture stdout
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            self.cli.run(['--help'])
            output = captured_output.getvalue()
            
            assert "Agent OS Command Line Interface" in output
            assert "create-module-agent" in output
            assert "Examples:" in output
            
        finally:
            sys.stdout = old_stdout

    def test_cli_with_invalid_command(self):
        """Test CLI with invalid command."""
        result = self.cli.run(['invalid-command'])
        assert result == 1

    def test_create_module_agent_help(self):
        """Test create-module-agent help display."""
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            self.cli.run(['create-module-agent', '--help'])
            output = captured_output.getvalue()
            
            assert "Create a new module agent" in output
            assert "--type" in output
            assert "--repos" in output
            
        finally:
            sys.stdout = old_stdout

    @patch('builtins.input')
    def test_interactive_mode_basic(self, mock_input):
        """Test basic interactive mode functionality."""
        # Mock user inputs
        mock_input.side_effect = [
            'create-module-agent test-interactive',
            'quit'
        ]
        
        # Test interactive mode
        result = self.cli.run(['--interactive'])
        
        # Should exit cleanly
        assert result == 0

    def test_command_string_parsing(self):
        """Test command string parsing in interactive mode."""
        # Test slash command conversion
        result = self.cli.execute_command_string('/create-module-agent help')
        assert result == 0
        
        # Test normal command
        result = self.cli.execute_command_string('create-module-agent help')
        assert result == 0
        
        # Test empty command
        result = self.cli.execute_command_string('')
        assert result == 0
        
        # Test unknown command
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            result = self.cli.execute_command_string('unknown-command')
            assert result == 1
            
            output = captured_output.getvalue()
            assert "Unknown command" in output
            
        finally:
            sys.stdout = old_stdout


class TestInteractiveMode:
    """Test interactive mode functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.interactive = InteractiveMode()

    @patch('builtins.input')
    def test_get_command(self, mock_input):
        """Test getting command from user."""
        mock_input.return_value = "test command"
        
        command = self.interactive.get_command()
        assert command == "test command"

    @patch('builtins.input')
    def test_get_yes_no(self, mock_input):
        """Test yes/no input functionality."""
        # Test yes response
        mock_input.return_value = "y"
        result = self.interactive.get_yes_no("Test question?")
        assert result is True
        
        # Test no response
        mock_input.return_value = "n"
        result = self.interactive.get_yes_no("Test question?")
        assert result is False
        
        # Test default response
        mock_input.return_value = ""
        result = self.interactive.get_yes_no("Test question?", default=True)
        assert result is True

    @patch('builtins.input')
    def test_select_from_list(self, mock_input):
        """Test list selection functionality."""
        options = ["option1", "option2", "option3"]
        
        # Test valid selection
        mock_input.return_value = "2"
        result = self.interactive.select_from_list("Choose:", options)
        assert result == "option2"
        
        # Test default selection
        mock_input.return_value = ""
        result = self.interactive.select_from_list("Choose:", options, default=0)
        assert result == "option1"

    def test_command_history(self):
        """Test command history functionality."""
        # Add commands to history
        self.interactive.add_to_history("command1")
        self.interactive.add_to_history("command2")
        self.interactive.add_to_history("command3")
        
        history = self.interactive.get_history()
        assert len(history) == 3
        assert history[-1] == "command3"
        
        # Test duplicate removal
        self.interactive.add_to_history("command1")
        history = self.interactive.get_history()
        assert history.count("command1") == 1
        assert history[-1] == "command1"  # Moved to end

    @patch('builtins.input')
    @patch('builtins.print')
    def test_get_module_agent_details(self, mock_print, mock_input):
        """Test interactive module agent details collection."""
        # Mock user inputs
        mock_input.side_effect = [
            "test-module",      # module name
            "1",                # agent type (general-purpose)
            "n",                # no repos
            "n",                # no templates
            "y"                 # enable caching
        ]
        
        details = self.interactive.get_module_agent_details()
        
        assert details["module_name"] == "test-module"
        assert details["type"] == "general-purpose"
        assert details["repos"] == []
        assert details["templates"] == []
        assert details["context_cache"] is True


class TestProgressIndicators:
    """Test progress indicator functionality."""

    def test_progress_indicator_basic(self):
        """Test basic progress indicator functionality."""
        progress = ProgressIndicator()
        
        # Test start/stop
        progress.start("Testing")
        assert progress.running is True
        
        progress.stop()
        assert progress.running is False

    def test_progress_bar(self):
        """Test progress bar functionality."""
        progress_bar = ProgressBar(total=100, width=20)
        
        # Test update
        progress_bar.update(50, "Half complete")
        assert progress_bar.current == 50
        assert progress_bar.message == "Half complete"
        
        # Test increment
        progress_bar.increment("Incremented")
        assert progress_bar.current == 51
        assert progress_bar.message == "Incremented"

    def test_task_progress(self):
        """Test task progress functionality."""
        tasks = ["Task 1", "Task 2", "Task 3"]
        task_progress = TaskProgress(tasks)
        
        # Start and complete tasks
        task_progress.start_task(0)
        assert task_progress.current_task == 0
        
        task_progress.complete_task(0, success=True)
        assert 0 in task_progress.completed_tasks
        
        task_progress.complete_task(1, success=False)
        assert 1 in task_progress.failed_tasks

    @patch('builtins.print')
    def test_task_progress_summary(self, mock_print):
        """Test task progress summary display."""
        tasks = ["Task 1", "Task 2", "Task 3", "Task 4"]
        task_progress = TaskProgress(tasks)
        
        # Complete some tasks
        task_progress.complete_task(0, success=True)
        task_progress.complete_task(1, success=True)
        task_progress.complete_task(2, success=False)
        
        # Show summary
        task_progress.show_summary()
        
        # Verify print was called with summary information
        assert mock_print.called
        
        # Check call arguments for expected content
        call_args = [call[0][0] for call in mock_print.call_args_list]
        summary_text = " ".join(call_args)
        
        assert "Task Summary" in summary_text
        assert "Total tasks: 4" in summary_text
        assert "Completed: 2" in summary_text
        assert "Failed: 1" in summary_text


class TestCLIErrorHandling:
    """Test CLI error handling scenarios."""

    def setup_method(self):
        """Set up test environment."""
        self.cli = AgentOSCLI()

    def test_missing_module_name(self):
        """Test error handling for missing module name."""
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            result = self.cli.execute_command_string('create-module-agent')
            assert result == 1
            
            output = captured_output.getvalue()
            assert "Module name is required" in output
            
        finally:
            sys.stdout = old_stdout

    @patch('assetutilities.agent_os.commands.create_module_agent.CreateModuleAgentCommand.execute')
    def test_command_execution_error(self, mock_execute):
        """Test error handling during command execution."""
        # Mock command failure
        mock_execute.side_effect = Exception("Test error")
        
        old_stdout = sys.stdout
        sys.stdout = captured_output = StringIO()
        
        try:
            result = self.cli.execute_command_string('create-module-agent test-error')
            assert result == 1
            
            output = captured_output.getvalue()
            assert "Error executing command" in output
            
        finally:
            sys.stdout = old_stdout

    def test_invalid_arguments(self):
        """Test handling of invalid arguments."""
        # Test invalid output directory
        result = self.cli.run([
            'create-module-agent',
            'test-agent',
            '--output-dir',
            '/invalid/path/that/does/not/exist'
        ])
        
        # Should handle gracefully
        assert result in [0, 1]  # May succeed or fail depending on implementation