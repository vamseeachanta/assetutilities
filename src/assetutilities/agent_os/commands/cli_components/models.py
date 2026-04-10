# ABOUTME: Data models for CLI system command parsing and validation.
# ABOUTME: Extracted from cli.py dataclasses.
"""Data models for the CLI system."""

from typing import List, Dict, Any, Optional
from dataclasses import dataclass, field


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


