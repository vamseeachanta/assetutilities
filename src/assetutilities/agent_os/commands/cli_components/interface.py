# ABOUTME: Top-level CLI interface coordinating all CLI components.
# ABOUTME: Extracted from cli.py CommandLineInterface class and main().
"""Top-level command line interface for Agent OS."""

import sys
import argparse
import logging
from typing import List, Dict, Any, Optional

from assetutilities.agent_os.commands.cli_components.models import ParsedCommand
from assetutilities.agent_os.commands.cli_components.error_handler import ErrorHandler
from assetutilities.agent_os.commands.cli_components.help_system import HelpSystem
from assetutilities.agent_os.commands.cli_components.interactive import InteractiveMode
from assetutilities.agent_os.commands.cli_components.manager import CLIManager
from assetutilities.agent_os.commands.cli_components.progress import ProgressIndicator

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
            from assetutilities.agent_os.commands.create_module_agent import CreateModuleAgentCommand
            
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