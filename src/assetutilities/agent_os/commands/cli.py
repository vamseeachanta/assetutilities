"""Command Line Interface for Agent OS.

This module provides a comprehensive CLI system with interactive mode,
progress indicators, help system, and error handling.
"""

import re
import sys
import time
import yaml
import argparse
import logging
import threading
from pathlib import Path
from typing import List, Dict, Any, Optional, Union
from dataclasses import dataclass, field
from datetime import datetime


@dataclass
class ValidationResult:
    """Result of validation operation."""
    is_valid: bool
    errors: List[str] = field(default_factory=list)
    warnings: List[str] = field(default_factory=list)


@dataclass
class ParsedCommand:
    """Parsed command structure."""
    command: str
    module_name: str = ""
    agent_type: str = "general-purpose"
    repos: List[str] = field(default_factory=list)
    context_cache: bool = True
    templates: List[str] = field(default_factory=list)
    options: Dict[str, Any] = field(default_factory=dict)


@dataclass
class ErrorResult:
    """Error handling result."""
    should_continue: bool
    error_code: int
    message: str = ""
    suggestions: List[str] = field(default_factory=list)


class CLIManager:
    """Main CLI management class."""

    def __init__(self):
        """Initialize CLI manager."""
        self.available_commands = {
            "create-module-agent": {
                "description": "Create a new module-specific agent",
                "usage": "create-module-agent <module_name> [options]",
                "required_args": ["module_name"],
                "optional_args": {
                    "--type": "Agent type (general-purpose, engineering, analysis, etc.)",
                    "--repos": "Comma-separated list of repositories to include",
                    "--context-cache": "Enable context optimization and caching (default: true)",
                    "--templates": "Comma-separated list of templates to use"
                }
            }
        }
        
        self.valid_agent_types = [
            "general-purpose", "engineering", "analysis", "infrastructure",
            "documentation", "testing", "deployment", "monitoring"
        ]
        
        self.available_repos = [
            "aceengineer-website", "aceengineercode", "digitalmodel",
            "energy", "rock-oil-field", "saipem", "acma-projects",
            "client_projects", "investments", "teamresumes", "assethold",
            "assetutilities", "pyproject-starter", "worldenergydata",
            "ai-native-traditional-eng", "frontierdeepwater", "OGManufacturing"
        ]

    def parse_command(self, args: List[str]) -> ParsedCommand:
        """Parse command line arguments.
        
        Args:
            args: List of command line arguments
            
        Returns:
            Parsed command structure
            
        Raises:
            ValueError: If command is invalid or required arguments are missing
        """
        if not args:
            raise ValueError("No command provided")
        
        command = args[0]
        
        if command not in self.available_commands:
            available = ", ".join(self.available_commands.keys())
            raise ValueError(f"Unknown command '{command}'. Available commands: {available}")
        
        parser = argparse.ArgumentParser(description=self.available_commands[command]["description"], add_help=False)
        
        # Add positional arguments
        if command == "create-module-agent":
            parser.add_argument("module_name", nargs="?", help="Name of the module agent to create")
            parser.add_argument("--type", default="general-purpose", help="Agent type")
            parser.add_argument("--repos", help="Comma-separated list of repositories")
            parser.add_argument("--context-cache", type=str, default="true", help="Enable context caching")
            parser.add_argument("--templates", help="Comma-separated list of templates")
            parser.add_argument("--progress", action="store_true", help="Show progress indicators")
            parser.add_argument("--verbose", action="store_true", help="Enable verbose output")
            parser.add_argument("--dry-run", action="store_true", help="Show what would be done without executing")
            parser.add_argument("--config", help="Path to configuration file")
            parser.add_argument("--log-level", choices=["DEBUG", "INFO", "WARNING", "ERROR"], default="INFO")
            parser.add_argument("--help", action="store_true", help="Show help message")
        
        try:
            parsed_args = parser.parse_args(args[1:])
        except SystemExit:
            # argparse calls sys.exit on error, catch and re-raise as ValueError
            raise ValueError("Invalid command arguments")
        
        # Build parsed command
        parsed = ParsedCommand(command=command)
        
        if command == "create-module-agent":
            if not parsed_args.module_name:
                raise ValueError("Module name is required")
            
            parsed.module_name = parsed_args.module_name
            parsed.agent_type = parsed_args.type
            parsed.context_cache = parsed_args.context_cache.lower() == "true" if isinstance(parsed_args.context_cache, str) else parsed_args.context_cache
            
            if parsed_args.repos:
                parsed.repos = [repo.strip() for repo in parsed_args.repos.split(",")]
            
            if parsed_args.templates:
                parsed.templates = [template.strip() for template in parsed_args.templates.split(",")]
            
            # Store additional options
            parsed.options = {
                "progress": getattr(parsed_args, "progress", False),
                "verbose": getattr(parsed_args, "verbose", False),
                "dry_run": getattr(parsed_args, "dry_run", False),
                "config": getattr(parsed_args, "config", None),
                "log_level": getattr(parsed_args, "log_level", "INFO")
            }
        
        return parsed

    def validate_module_name(self, module_name: str) -> bool:
        """Validate module name.
        
        Args:
            module_name: Module name to validate
            
        Returns:
            True if valid, False otherwise
        """
        if not module_name or len(module_name) < 2:
            return False
        
        # Allow letters, numbers, hyphens, and underscores
        if not re.match(r'^[a-zA-Z0-9_-]+$', module_name):
            return False
        
        # Should not start or end with special characters
        if module_name.startswith(('-', '_')) or module_name.endswith(('-', '_')):
            return False
        
        return True

    def validate_options(self, options: Dict[str, Any]) -> ValidationResult:
        """Validate command options.
        
        Args:
            options: Options to validate
            
        Returns:
            Validation result
        """
        errors = []
        warnings = []
        
        # Validate agent type
        agent_type = options.get("agent_type", "general-purpose")
        if agent_type not in self.valid_agent_types:
            errors.append(f"Invalid agent type '{agent_type}'. Valid types: {', '.join(self.valid_agent_types)}")
        
        # Validate repositories
        repos = options.get("repos", [])
        if repos:
            for repo in repos:
                if repo not in self.available_repos:
                    warnings.append(f"Repository '{repo}' not in standard list. Available: {', '.join(self.available_repos[:5])}...")
        
        # Validate templates
        templates = options.get("templates", [])
        if templates:
            known_templates = ["general-purpose", "engineering", "analysis", "documentation", "infrastructure"]
            for template in templates:
                if template not in known_templates:
                    warnings.append(f"Template '{template}' not in standard list. Available: {', '.join(known_templates)}")
        
        return ValidationResult(is_valid=len(errors) == 0, errors=errors, warnings=warnings)

    def get_help_text(self) -> str:
        """Get general help text.
        
        Returns:
            Formatted help text
        """
        help_text = []
        help_text.append("Agent OS Command Line Interface")
        help_text.append("=" * 35)
        help_text.append("")
        help_text.append("Available Commands:")
        help_text.append("")
        
        for command, info in self.available_commands.items():
            help_text.append(f"  {command}")
            help_text.append(f"    {info['description']}")
            help_text.append(f"    Usage: {info['usage']}")
            help_text.append("")
        
        help_text.append("Options:")
        help_text.append("  --help     Show this help message")
        help_text.append("  --verbose  Enable verbose output")
        help_text.append("  --dry-run  Show what would be done without executing")
        help_text.append("")
        help_text.append("For command-specific help, use: <command> --help")
        
        return "\n".join(help_text)

    def get_command_help(self, command: str) -> str:
        """Get help text for specific command.
        
        Args:
            command: Command to get help for
            
        Returns:
            Formatted help text
        """
        if command not in self.available_commands:
            return f"Unknown command: {command}"
        
        info = self.available_commands[command]
        help_text = []
        
        help_text.append(f"Command: {command}")
        help_text.append("=" * (len(command) + 9))
        help_text.append("")
        help_text.append(f"Description: {info['description']}")
        help_text.append(f"Usage: {info['usage']}")
        help_text.append("")
        
        if "optional_args" in info:
            help_text.append("Options:")
            for option, description in info["optional_args"].items():
                help_text.append(f"  {option:<15} {description}")
            help_text.append("")
        
        help_text.append("Examples:")
        if command == "create-module-agent":
            help_text.append("  create-module-agent finance-analytics")
            help_text.append("  create-module-agent devops --type infrastructure --repos assetutilities,pyproject-starter")
            help_text.append("  create-module-agent api-service --templates engineering,documentation")
        
        return "\n".join(help_text)


class InteractiveMode:
    """Interactive mode for collecting missing options."""

    def __init__(self):
        """Initialize interactive mode."""
        self.cli_manager = CLIManager()

    def prompt_for_module_name(self) -> str:
        """Prompt user for module name.
        
        Returns:
            Module name
        """
        while True:
            module_name = input("Enter module name: ").strip()
            if self.cli_manager.validate_module_name(module_name):
                return module_name
            else:
                print("Invalid module name. Use letters, numbers, hyphens, and underscores only.")

    def prompt_for_agent_type(self) -> str:
        """Prompt user for agent type.
        
        Returns:
            Selected agent type
        """
        print("\nSelect agent type:")
        agent_types = self.cli_manager.valid_agent_types
        
        for i, agent_type in enumerate(agent_types, 1):
            print(f"  {i}. {agent_type}")
        
        while True:
            try:
                choice = input(f"Enter choice (1-{len(agent_types)}) [1]: ").strip()
                if not choice:
                    choice = "1"
                
                index = int(choice) - 1
                if 0 <= index < len(agent_types):
                    return agent_types[index]
                else:
                    print(f"Please enter a number between 1 and {len(agent_types)}")
            except ValueError:
                print("Please enter a valid number")

    def prompt_for_repositories(self) -> List[str]:
        """Prompt user for repositories.
        
        Returns:
            List of selected repositories
        """
        repos_input = input("Enter repositories (comma-separated) [none]: ").strip()
        if not repos_input:
            return []
        
        return [repo.strip() for repo in repos_input.split(",")]

    def prompt_for_templates(self) -> List[str]:
        """Prompt user for templates.
        
        Returns:
            List of selected templates
        """
        templates_input = input("Enter templates (comma-separated) [auto]: ").strip()
        if not templates_input or templates_input.lower() == "auto":
            return []
        
        return [template.strip() for template in templates_input.split(",")]

    def confirm_action(self, message: str) -> bool:
        """Confirm action with user.
        
        Args:
            message: Confirmation message
            
        Returns:
            True if confirmed, False otherwise
        """
        response = input(f"{message} (y/N): ").strip().lower()
        return response in ['y', 'yes']

    def display_summary(self, options: Dict[str, Any]) -> None:
        """Display command summary.
        
        Args:
            options: Command options to display
        """
        print("\nCommand Summary:")
        print("-" * 16)
        print(f"Module Name: {options.get('module_name', 'N/A')}")
        print(f"Agent Type: {options.get('agent_type', 'general-purpose')}")
        
        repos = options.get('repos', [])
        if repos:
            print(f"Repositories: {', '.join(repos)}")
        
        templates = options.get('templates', [])
        if templates:
            print(f"Templates: {', '.join(templates)}")
        
        print(f"Context Cache: {options.get('context_cache', True)}")

    def collect_missing_options(self, partial_options: Dict[str, Any]) -> Dict[str, Any]:
        """Collect missing options interactively.
        
        Args:
            partial_options: Partially completed options
            
        Returns:
            Complete options dictionary
        """
        options = partial_options.copy()
        
        # Collect module name if missing
        if not options.get("module_name"):
            options["module_name"] = self.prompt_for_module_name()
        
        # Collect agent type if not specified
        if not options.get("agent_type") or options["agent_type"] == "general-purpose":
            print(f"\nCurrent agent type: {options.get('agent_type', 'general-purpose')}")
            if self.confirm_action("Change agent type?"):
                options["agent_type"] = self.prompt_for_agent_type()
        
        # Collect repositories if not specified
        if not options.get("repos"):
            options["repos"] = self.prompt_for_repositories()
        
        # Collect templates if not specified
        if not options.get("templates"):
            options["templates"] = self.prompt_for_templates()
        
        # Display summary and confirm
        self.display_summary(options)
        if not self.confirm_action("\nProceed with these settings?"):
            print("Operation cancelled by user.")
            return {}
        
        return options

    def handle_validation_errors(self, errors: List[str], options: Dict[str, Any]) -> Dict[str, Any]:
        """Handle validation errors interactively.
        
        Args:
            errors: List of validation errors
            options: Current options
            
        Returns:
            Corrected options
        """
        print("Validation errors found:")
        for error in errors:
            print(f"  • {error}")
        print()
        
        corrected_options = options.copy()
        
        for error in errors:
            if "Invalid agent type" in error:
                print("Please select a valid agent type:")
                corrected_options["agent_type"] = self.prompt_for_agent_type()
            elif "Repository" in error and "not found" in error:
                print("Please enter valid repositories:")
                corrected_options["repos"] = self.prompt_for_repositories()
        
        return corrected_options


class ProgressIndicator:
    """Progress indicator with spinner and step tracking."""

    def __init__(self, message: str, steps: Optional[List[str]] = None, 
                 show_spinner: bool = False, show_percentage: bool = False, total_items: int = 0):
        """Initialize progress indicator.
        
        Args:
            message: Main progress message
            steps: List of step descriptions
            show_spinner: Whether to show spinner animation
            show_percentage: Whether to show percentage
            total_items: Total number of items for percentage calculation
        """
        self.message = message
        self.steps = steps or []
        self.total_steps = len(self.steps) if self.steps else 1
        self.current_step = 0
        self.show_spinner = show_spinner
        self.show_percentage = show_percentage
        self.total_items = total_items
        self.current_items = 0
        
        self.spinner_chars = ['⠋', '⠙', '⠹', '⠸', '⠼', '⠴', '⠦', '⠧', '⠇', '⠏']
        self.current_spinner = 0
        self.spinner_thread = None
        self.spinner_running = False

    def update(self, status_message: str) -> None:
        """Update progress with status message.
        
        Args:
            status_message: Current status message
        """
        if self.steps:
            step_info = f"[{self.current_step + 1}/{self.total_steps}]"
            print(f"\r{step_info} {status_message}", end="", flush=True)
        else:
            print(f"\r{self.message}: {status_message}", end="", flush=True)

    def advance(self, completion_message: str) -> None:
        """Advance to next step.
        
        Args:
            completion_message: Message for completed step
        """
        if self.current_step < self.total_steps:
            print(f"\r✓ {completion_message}")
            self.current_step += 1

    def complete(self, final_message: str) -> None:
        """Complete progress indication.
        
        Args:
            final_message: Final completion message
        """
        self.stop_spinner()
        print(f"\r✓ {final_message}")

    def spin(self) -> None:
        """Update spinner character."""
        if self.show_spinner:
            self.current_spinner = (self.current_spinner + 1) % len(self.spinner_chars)
            spinner_char = self.spinner_chars[self.current_spinner]
            print(f"\r{spinner_char} {self.message}", end="", flush=True)

    def start_spinner(self) -> None:
        """Start spinner in background thread."""
        if self.show_spinner and not self.spinner_running:
            self.spinner_running = True
            self.spinner_thread = threading.Thread(target=self._spinner_loop)
            self.spinner_thread.daemon = True
            self.spinner_thread.start()

    def stop_spinner(self) -> None:
        """Stop spinner thread."""
        if self.spinner_running:
            self.spinner_running = False
            if self.spinner_thread:
                self.spinner_thread.join(timeout=0.1)

    def _spinner_loop(self) -> None:
        """Spinner animation loop."""
        while self.spinner_running:
            self.spin()
            time.sleep(0.1)

    def update_percentage(self, completed_items: int) -> None:
        """Update percentage progress.
        
        Args:
            completed_items: Number of completed items
        """
        if self.show_percentage and self.total_items > 0:
            self.current_items = completed_items
            percentage = (completed_items / self.total_items) * 100
            print(f"\r{self.message}: {percentage:.1f}% ({completed_items}/{self.total_items})", end="", flush=True)


class HelpSystem:
    """Comprehensive help system."""

    def __init__(self):
        """Initialize help system."""
        self.cli_manager = CLIManager()

    def get_general_help(self) -> str:
        """Get general help information.
        
        Returns:
            General help text
        """
        return self.cli_manager.get_help_text()

    def get_command_help(self, command: str) -> str:
        """Get help for specific command.
        
        Args:
            command: Command name
            
        Returns:
            Command-specific help text
        """
        return self.cli_manager.get_command_help(command)

    def get_option_help(self, option: str) -> str:
        """Get help for specific option.
        
        Args:
            option: Option name (e.g., '--type')
            
        Returns:
            Option-specific help text
        """
        option_help = {
            "--type": "Specify the agent type. Available types: general-purpose, engineering, analysis, infrastructure, documentation, testing, deployment, monitoring",
            "--repos": "Comma-separated list of repositories to include in the agent context",
            "--context-cache": "Enable context optimization and local caching for faster responses",
            "--templates": "Comma-separated list of predefined templates to use for agent configuration",
            "--progress": "Show progress indicators during agent creation",
            "--verbose": "Enable verbose output with detailed information",
            "--dry-run": "Show what would be done without actually executing the command",
            "--config": "Path to configuration file with default settings",
            "--log-level": "Set logging level (DEBUG, INFO, WARNING, ERROR)"
        }
        
        return option_help.get(option, f"No help available for option: {option}")

    def search_help(self, query: str) -> List[str]:
        """Search help content for query.
        
        Args:
            query: Search query
            
        Returns:
            List of matching help entries
        """
        results = []
        query = query.lower()
        
        # Search in commands
        for command, info in self.cli_manager.available_commands.items():
            if query in command.lower() or query in info["description"].lower():
                results.append(f"Command: {command} - {info['description']}")
        
        # Search in options
        option_help = {
            "--type": "agent type selection",
            "--repos": "repository configuration",
            "--context-cache": "context optimization",
            "--templates": "template selection",
            "--progress": "progress indicators",
            "--verbose": "detailed output",
            "--dry-run": "preview mode",
            "--config": "configuration file",
            "--log-level": "logging configuration"
        }
        
        for option, description in option_help.items():
            if query in option.lower() or query in description.lower():
                results.append(f"Option: {option} - {description}")
        
        return results

    def get_examples(self, command: str) -> List[str]:
        """Get examples for command.
        
        Args:
            command: Command name
            
        Returns:
            List of example usages
        """
        examples = {
            "create-module-agent": [
                "create-module-agent finance-analytics",
                "create-module-agent devops --type infrastructure",
                "create-module-agent api-service --repos assetutilities,pyproject-starter",
                "create-module-agent documentation --templates documentation --verbose",
                "create-module-agent test-agent --dry-run"
            ]
        }
        
        return examples.get(command, [])

    def format_help_text(self, help_data: Dict[str, Any]) -> str:
        """Format help text from structured data.
        
        Args:
            help_data: Structured help information
            
        Returns:
            Formatted help text
        """
        lines = []
        
        if "title" in help_data:
            lines.append(help_data["title"])
            lines.append("=" * len(help_data["title"]))
            lines.append("")
        
        if "description" in help_data:
            lines.append(help_data["description"])
            lines.append("")
        
        if "usage" in help_data:
            lines.append(f"Usage: {help_data['usage']}")
            lines.append("")
        
        if "options" in help_data:
            lines.append("Options:")
            for option, description in help_data["options"].items():
                lines.append(f"  {option:<15} {description}")
            lines.append("")
        
        return "\n".join(lines)


class ErrorHandler:
    """Comprehensive error handling system."""

    def __init__(self):
        """Initialize error handler."""
        self.error_codes = {
            ValueError: 1,
            FileNotFoundError: 2,
            PermissionError: 3,
            KeyboardInterrupt: 130,
            RuntimeError: 1
        }

    def handle_error(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> ErrorResult:
        """Handle error and provide recovery suggestions.
        
        Args:
            error: Exception to handle
            context: Additional context information
            
        Returns:
            Error handling result
        """
        error_code = self.error_codes.get(type(error), 1)
        
        if isinstance(error, KeyboardInterrupt):
            message = "Operation cancelled by user."
            print(f"\n{message}", file=sys.stderr)
            return ErrorResult(should_continue=False, error_code=error_code, message=message)
        
        # Format and display error message
        formatted_message = self.format_error_message(error, context)
        print(formatted_message, file=sys.stderr)
        
        # Get and display suggestions
        suggestions = self.suggest_solutions(error)
        if suggestions:
            print("\nSuggestions:", file=sys.stderr)
            for suggestion in suggestions:
                print(f"  • {suggestion}", file=sys.stderr)
        
        return ErrorResult(
            should_continue=False,
            error_code=error_code,
            message=str(error),
            suggestions=suggestions
        )

    def suggest_solutions(self, error: Exception) -> List[str]:
        """Suggest solutions for error.
        
        Args:
            error: Exception to suggest solutions for
            
        Returns:
            List of solution suggestions
        """
        suggestions = []
        error_str = str(error).lower()
        
        if isinstance(error, ValueError):
            if "invalid agent type" in error_str:
                suggestions.append("Check available agent types with 'create-module-agent --help'")
                suggestions.append("Use one of: general-purpose, engineering, analysis, infrastructure")
            elif "invalid module name" in error_str:
                suggestions.append("Use only letters, numbers, hyphens, and underscores")
                suggestions.append("Ensure name is at least 2 characters long")
            elif "unknown command" in error_str:
                suggestions.append("Check available commands with '--help'")
                suggestions.append("Verify command spelling")
        
        elif isinstance(error, FileNotFoundError):
            if "template" in error_str:
                suggestions.append("Check available templates")
                suggestions.append("Verify template name spelling")
                suggestions.append("Ensure templates are properly installed")
            else:
                suggestions.append("Check file path and permissions")
                suggestions.append("Ensure required files exist")
        
        elif isinstance(error, PermissionError):
            suggestions.append("Check file and directory permissions")
            suggestions.append("Try running with appropriate privileges")
            suggestions.append("Ensure target directory is writable")
        
        else:
            suggestions.append("Check command syntax and arguments")
            suggestions.append("Try running with --verbose for more information")
            suggestions.append("Use --help for usage information")
        
        return suggestions

    def format_error_message(self, error: Exception, context: Optional[Dict[str, Any]] = None) -> str:
        """Format error message with context.
        
        Args:
            error: Exception to format
            context: Additional context information
            
        Returns:
            Formatted error message
        """
        lines = []
        
        lines.append(f"Error: {str(error)}")
        
        if context:
            lines.append("")
            lines.append("Context:")
            for key, value in context.items():
                lines.append(f"  {key}: {value}")
        
        return "\n".join(lines)

    def get_recovery_suggestions(self, error: Exception) -> List[str]:
        """Get recovery suggestions for error.
        
        Args:
            error: Exception to get recovery for
            
        Returns:
            List of recovery suggestions
        """
        return self.suggest_solutions(error)


class CommandLineInterface:
    """Main command line interface."""

    def __init__(self):
        """Initialize CLI."""
        self.cli_manager = CLIManager()
        self.interactive_mode = InteractiveMode()
        self.help_system = HelpSystem()
        self.error_handler = ErrorHandler()
        self.logger = self._setup_logging()

    def run(self, args: List[str], interactive: bool = False) -> int:
        """Run CLI with given arguments.
        
        Args:
            args: Command line arguments
            interactive: Whether to use interactive mode
            
        Returns:
            Exit code (0 for success, non-zero for error)
        """
        try:
            # Handle help requests
            if not args or "--help" in args or "-h" in args:
                print(self.help_system.get_general_help())
                return 0
            
            # Handle command-specific help
            if len(args) >= 2 and args[1] == "--help":
                print(self.help_system.get_command_help(args[0]))
                return 0
            
            # Parse command
            try:
                parsed_command = self.cli_manager.parse_command(args)
            except ValueError as e:
                if interactive:
                    # Try to collect missing information interactively
                    partial_options = {"command": args[0] if args else ""}
                    if len(args) > 1:
                        partial_options["module_name"] = args[1]
                    
                    complete_options = self.interactive_mode.collect_missing_options(partial_options)
                    if not complete_options:
                        return 1
                    
                    # Rebuild parsed command from complete options
                    parsed_command = self._build_parsed_command_from_options(complete_options)
                else:
                    raise e
            
            # Load configuration if specified
            if parsed_command.options.get("config"):
                self._load_configuration(parsed_command.options["config"], parsed_command)
            
            # Configure logging
            log_level = parsed_command.options.get("log_level", "INFO")
            self.logger.setLevel(getattr(logging, log_level))
            
            # Validate options
            validation_options = {
                "agent_type": parsed_command.agent_type,
                "repos": parsed_command.repos,
                "templates": parsed_command.templates
            }
            
            validation_result = self.cli_manager.validate_options(validation_options)
            
            if not validation_result.is_valid:
                if interactive:
                    # Handle validation errors interactively
                    corrected_options = self.interactive_mode.handle_validation_errors(
                        validation_result.errors, validation_options
                    )
                    # Update parsed command with corrected options
                    parsed_command.agent_type = corrected_options.get("agent_type", parsed_command.agent_type)
                    parsed_command.repos = corrected_options.get("repos", parsed_command.repos)
                else:
                    for error in validation_result.errors:
                        print(f"Error: {error}", file=sys.stderr)
                    return 1
            
            # Show warnings
            if validation_result.warnings:
                for warning in validation_result.warnings:
                    print(f"Warning: {warning}", file=sys.stderr)
            
            # Handle dry run
            if parsed_command.options.get("dry_run"):
                self._show_dry_run(parsed_command)
                return 0
            
            # Execute command
            return self._execute_command(parsed_command)
            
        except KeyboardInterrupt:
            error_result = self.error_handler.handle_error(KeyboardInterrupt())
            return error_result.error_code
        except Exception as e:
            context = {"args": args, "interactive": interactive}
            error_result = self.error_handler.handle_error(e, context)
            return error_result.error_code

    def _execute_command(self, parsed_command: ParsedCommand) -> int:
        """Execute parsed command.
        
        Args:
            parsed_command: Parsed command to execute
            
        Returns:
            Exit code
        """
        if parsed_command.command == "create-module-agent":
            return self._execute_create_module_agent(parsed_command)
        else:
            print(f"Unknown command: {parsed_command.command}", file=sys.stderr)
            return 1

    def _execute_create_module_agent(self, parsed_command: ParsedCommand) -> int:
        """Execute create-module-agent command.
        
        Args:
            parsed_command: Parsed command
            
        Returns:
            Exit code
        """
        try:
            # Import here to avoid circular imports
            from .create_module_agent import CreateModuleAgentCommand
            
            # Setup progress indicator if requested
            progress = None
            if parsed_command.options.get("progress"):
                steps = [
                    "Setting up directory structure",
                    "Generating configuration files",
                    "Installing templates",
                    "Finalizing setup"
                ]
                progress = ProgressIndicator("Creating agent", steps=steps)
                progress.start_spinner()
            
            # Create and configure command
            command = CreateModuleAgentCommand()
            
            # Build execution arguments
            execution_args = {
                "module_name": parsed_command.module_name,
                "agent_type": parsed_command.agent_type,
                "repos": parsed_command.repos,
                "context_cache": parsed_command.context_cache,
                "templates": parsed_command.templates
            }
            
            if parsed_command.options.get("verbose"):
                execution_args["verbose"] = True
            
            # Execute command
            if progress:
                progress.update("Initializing...")
            
            result = command.execute(execution_args)
            
            if progress:
                progress.complete("Agent created successfully!")
            
            if result.success:
                print(f"✓ {result.message}")
                return 0
            else:
                print(f"Error: {result.message}", file=sys.stderr)
                return 1
                
        except Exception as e:
            if progress:
                progress.stop_spinner()
            raise e

    def _show_dry_run(self, parsed_command: ParsedCommand) -> None:
        """Show what would be done without executing.
        
        Args:
            parsed_command: Parsed command
        """
        print("Dry run - showing what would be done:")
        print(f"  Command: {parsed_command.command}")
        print(f"  Module name: {parsed_command.module_name}")
        print(f"  Agent type: {parsed_command.agent_type}")
        
        if parsed_command.repos:
            print(f"  Repositories: {', '.join(parsed_command.repos)}")
        
        if parsed_command.templates:
            print(f"  Templates: {', '.join(parsed_command.templates)}")
        
        print(f"  Context cache: {parsed_command.context_cache}")
        print("\nWould create agent structure with above configuration.")

    def _build_parsed_command_from_options(self, options: Dict[str, Any]) -> ParsedCommand:
        """Build ParsedCommand from options dictionary.
        
        Args:
            options: Complete options dictionary
            
        Returns:
            ParsedCommand instance
        """
        return ParsedCommand(
            command=options.get("command", "create-module-agent"),
            module_name=options.get("module_name", ""),
            agent_type=options.get("agent_type", "general-purpose"),
            repos=options.get("repos", []),
            context_cache=options.get("context_cache", True),
            templates=options.get("templates", []),
            options={}
        )

    def _load_configuration(self, config_path: str, parsed_command: ParsedCommand) -> None:
        """Load configuration from file.
        
        Args:
            config_path: Path to configuration file
            parsed_command: Parsed command to update
        """
        try:
            with open(config_path, 'r') as f:
                config = yaml.safe_load(f)
            
            # Apply configuration defaults
            if "default_agent_type" in config and not parsed_command.agent_type:
                parsed_command.agent_type = config["default_agent_type"]
            
            if "default_repos" in config and not parsed_command.repos:
                parsed_command.repos = config["default_repos"]
            
            if "context_cache" in config:
                parsed_command.context_cache = config["context_cache"]
            
        except Exception as e:
            print(f"Warning: Failed to load configuration from {config_path}: {e}", file=sys.stderr)

    def _setup_logging(self) -> logging.Logger:
        """Setup logging configuration.
        
        Returns:
            Configured logger
        """
        logger = logging.getLogger("agent_os_cli")
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        logger.setLevel(logging.INFO)
        return logger


# Main entry point for CLI
def main():
    """Main entry point for command line interface."""
    cli = CommandLineInterface()
    exit_code = cli.run(sys.argv[1:])
    sys.exit(exit_code)


if __name__ == "__main__":
    main()