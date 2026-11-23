# ABOUTME: Repository documentation scanning and reference discovery.
# ABOUTME: Extracted from documentation_integration.py scanner classes.
"""Repository documentation scanning and reference discovery."""

import re
import ast
import yaml
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass


@dataclass
class DocumentReference:
    """Reference to a documentation source."""
    name: str
    path: str
    type: str
    content: str
    last_updated: str


class RepositoryDocumentationScanner:
    """Scans repositories for documentation content."""

    def __init__(self):
        """Initialize the scanner."""
        self.supported_extensions = {'.md', '.rst', '.txt'}
        self.python_extensions = {'.py'}

    def scan_repository(self, repo_path: Path) -> Dict[str, Any]:
        """Scan a single repository for documentation.
        
        Args:
            repo_path: Path to the repository
            
        Returns:
            Dictionary containing scanned documentation
        """
        if not repo_path.exists():
            return {
                "name": repo_path.name,
                "path": str(repo_path),
                "markdown_files": [],
                "python_docstrings": [],
                "readme_content": None,
                "last_updated": datetime.now().isoformat(),
                "status": "not_found"
            }

        result = {
            "name": repo_path.name,
            "path": str(repo_path),
            "markdown_files": self._extract_markdown_files(repo_path),
            "python_docstrings": self._extract_python_docstrings(repo_path),
            "readme_content": self._extract_readme(repo_path),
            "last_updated": datetime.now().isoformat(),
            "status": "success"
        }

        return result

    def scan_repositories(self, repo_paths: List[Path]) -> Dict[str, Dict[str, Any]]:
        """Scan multiple repositories.
        
        Args:
            repo_paths: List of repository paths
            
        Returns:
            Dictionary mapping repo names to scan results
        """
        results = {}
        for repo_path in repo_paths:
            results[repo_path.name] = self.scan_repository(repo_path)
        return results

    def _extract_markdown_files(self, repo_path: Path, 
                               include_patterns: Optional[List[str]] = None,
                               exclude_patterns: Optional[List[str]] = None) -> List[Dict[str, Any]]:
        """Extract markdown files from repository.
        
        Args:
            repo_path: Path to repository
            include_patterns: Patterns to include
            exclude_patterns: Patterns to exclude
            
        Returns:
            List of markdown file information
        """
        markdown_files = []
        
        # Default exclude patterns
        if exclude_patterns is None:
            exclude_patterns = ['node_modules', '.git', '__pycache__', '.pytest_cache']

        for file_path in repo_path.rglob('*'):
            if not file_path.is_file():
                continue
                
            if file_path.suffix not in self.supported_extensions:
                continue
                
            # Check exclude patterns
            if any(pattern in str(file_path) for pattern in exclude_patterns):
                continue
                
            # Check include patterns if specified
            if include_patterns:
                if not any(file_path.match(pattern) for pattern in include_patterns):
                    continue

            try:
                content = file_path.read_text(encoding='utf-8')
                relative_path = file_path.relative_to(repo_path)
                
                markdown_files.append({
                    "name": file_path.name,
                    "path": str(relative_path),
                    "full_path": str(file_path),
                    "content": content,
                    "size": len(content),
                    "lines": len(content.splitlines()),
                    "last_modified": datetime.fromtimestamp(
                        file_path.stat().st_mtime
                    ).isoformat()
                })
            except (UnicodeDecodeError, PermissionError):
                # Skip files that can't be read
                continue

        return markdown_files

    def _extract_python_docstrings(self, repo_path: Path) -> List[Dict[str, Any]]:
        """Extract docstrings from Python files.
        
        Args:
            repo_path: Path to repository
            
        Returns:
            List of docstring information
        """
        docstrings = []

        for file_path in repo_path.rglob('*.py'):
            if '__pycache__' in str(file_path) or '.git' in str(file_path):
                continue

            try:
                content = file_path.read_text(encoding='utf-8')
                relative_path = file_path.relative_to(repo_path)
                
                # Parse Python AST to extract docstrings
                tree = ast.parse(content)
                
                # Module docstring
                if (tree.body and isinstance(tree.body[0], ast.Expr) and
                    isinstance(tree.body[0].value, ast.Constant)):
                    docstrings.append({
                        "file": str(relative_path),
                        "type": "module",
                        "name": file_path.stem,
                        "content": tree.body[0].value.value,
                        "line": 1
                    })

                # Class and function docstrings
                for node in ast.walk(tree):
                    if isinstance(node, (ast.FunctionDef, ast.ClassDef)):
                        if (node.body and isinstance(node.body[0], ast.Expr) and
                            isinstance(node.body[0].value, ast.Constant)):
                            docstrings.append({
                                "file": str(relative_path),
                                "type": "class" if isinstance(node, ast.ClassDef) else "function",
                                "name": node.name,
                                "content": node.body[0].value.value,
                                "line": node.lineno
                            })

            except (SyntaxError, UnicodeDecodeError, PermissionError):
                # Skip files that can't be parsed
                continue

        return docstrings

    def _extract_readme(self, repo_path: Path) -> Optional[str]:
        """Extract README content.
        
        Args:
            repo_path: Path to repository
            
        Returns:
            README content if found
        """
        readme_patterns = ['README.md', 'README.rst', 'README.txt', 'readme.md']
        
        for pattern in readme_patterns:
            readme_path = repo_path / pattern
            if readme_path.exists():
                try:
                    return readme_path.read_text(encoding='utf-8')
                except (UnicodeDecodeError, PermissionError):
                    continue
        
        return None


