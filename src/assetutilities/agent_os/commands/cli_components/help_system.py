# ABOUTME: Help system providing command documentation and usage guides.
# ABOUTME: Extracted from cli.py HelpSystem class.
"""Help system for the Agent OS CLI."""

from typing import List, Dict, Any, Optional

from assetutilities.agent_os.commands.cli_components.manager import CLIManager


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


