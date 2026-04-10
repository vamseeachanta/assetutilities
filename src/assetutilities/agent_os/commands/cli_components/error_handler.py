# ABOUTME: Error handling and recovery for CLI operations.
# ABOUTME: Extracted from cli.py ErrorHandler class.
"""Error handling for the Agent OS CLI system."""

import sys
import logging
from typing import List, Dict, Any, Optional

from assetutilities.agent_os.commands.cli_components.models import ErrorResult

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


