# ABOUTME: CLI command management, registration, and execution engine.
# ABOUTME: Extracted from cli.py CLIManager class.
"""CLI command management for the Agent OS system."""

import re
import yaml
import argparse
import logging
from typing import List, Dict, Any, Optional

from assetutilities.agent_os.commands.cli_components.models import (
    ErrorResult,
    ParsedCommand,
    ValidationResult,
)

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


