# ABOUTME: Interactive CLI mode with command history and auto-completion.
# ABOUTME: Extracted from cli.py InteractiveMode class.
"""Interactive mode for the Agent OS CLI system."""

import sys
from typing import List, Dict, Any, Optional

from assetutilities.agent_os.commands.cli_components.manager import CLIManager
from assetutilities.agent_os.commands.cli_components.models import ParsedCommand

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


