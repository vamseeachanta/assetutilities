# ABOUTME: Document chunking engine for text, markdown, and code content.
# ABOUTME: Extracted from context_optimization.py dataclasses and DocumentChunker class.
"""Document chunking with various strategies."""

import re
import ast
from typing import List, Dict, Any, Optional
from dataclasses import dataclass

import numpy as np


@dataclass
class DocumentChunk:
    """Represents a chunk of document content."""
    id: str
    content: str
    metadata: Dict[str, Any]
    embedding: Optional[np.ndarray] = None


@dataclass
class Pattern:
    """Represents an identified pattern."""
    name: str
    type: str
    description: str
    examples: List[str]
    confidence: float


@dataclass
class Concept:
    """Represents a domain concept."""
    name: str
    type: str
    description: str
    related: List[str]
    frequency: int


@dataclass
class APISignature:
    """Represents an API signature."""
    name: str
    signature: str
    description: str
    parameters: List[Dict[str, Any]]
    return_type: str


class DocumentChunker:
    """Handles document chunking with various strategies."""

    def __init__(self, chunk_size: int = 512, overlap: int = 50):
        """Initialize the chunker.

        Args:
            chunk_size: Target size for chunks in characters
            overlap: Overlap between chunks in characters
        """
        self.chunk_size = chunk_size
        self.overlap = overlap

    def chunk_text(self, text: str, chunk_size: Optional[int] = None,
                   overlap: Optional[int] = None) -> List[str]:
        """Chunk text into overlapping segments.

        Args:
            text: Text to chunk
            chunk_size: Override default chunk size
            overlap: Override default overlap

        Returns:
            List of text chunks
        """
        chunk_size = chunk_size or self.chunk_size
        overlap = overlap or self.overlap

        if len(text) <= chunk_size:
            return [text]

        chunks = []
        start = 0

        while start < len(text):
            end = start + chunk_size

            # Try to break at word boundaries
            if end < len(text):
                # Look for word boundary within last 20% of chunk
                boundary_start = max(start + int(chunk_size * 0.8), start + 1)
                word_boundary = text.rfind(' ', boundary_start, end)

                if word_boundary != -1:
                    end = word_boundary

            chunk = text[start:end].strip()
            if chunk:
                chunks.append(chunk)

            # Move start position with overlap
            start = max(end - overlap, start + 1)

            if start >= len(text):
                break

        return chunks

    def chunk_markdown(self, content: str) -> List[Dict[str, Any]]:
        """Chunk markdown content by sections.

        Args:
            content: Markdown content

        Returns:
            List of chunk dictionaries with content and metadata
        """
        chunks = []
        lines = content.split('\n')
        current_section = []
        current_header = ""
        header_level = 0

        for line in lines:
            # Check for headers
            header_match = re.match(r'^(#{1,6})\s+(.+)$', line.strip())

            if header_match:
                # Save previous section if it exists
                if current_section:
                    section_content = '\n'.join(current_section).strip()
                    if section_content:
                        chunks.append({
                            "content": section_content,
                            "metadata": {
                                "section_type": "content",
                                "header": current_header,
                                "header_level": header_level,
                                "chunk_type": "markdown_section"
                            }
                        })

                # Start new section
                header_level = len(header_match.group(1))
                current_header = header_match.group(2)
                current_section = [line]
            else:
                current_section.append(line)

        # Add final section
        if current_section:
            section_content = '\n'.join(current_section).strip()
            if section_content:
                chunks.append({
                    "content": section_content,
                    "metadata": {
                        "section_type": "content",
                        "header": current_header,
                        "header_level": header_level,
                        "chunk_type": "markdown_section"
                    }
                })

        return chunks

    def chunk_code(self, content: str, language: str = "python") -> List[Dict[str, Any]]:
        """Chunk code content by functions and classes.

        Args:
            content: Code content
            language: Programming language

        Returns:
            List of chunk dictionaries with content and metadata
        """
        chunks = []

        if language == "python":
            chunks.extend(self._chunk_python_code(content))
        else:
            # Fallback to simple text chunking for other languages
            text_chunks = self.chunk_text(content)
            for i, chunk in enumerate(text_chunks):
                chunks.append({
                    "content": chunk,
                    "metadata": {
                        "code_type": "generic",
                        "language": language,
                        "chunk_index": i,
                        "chunk_type": "code_block"
                    }
                })

        return chunks

    def _chunk_python_code(self, content: str) -> List[Dict[str, Any]]:
        """Chunk Python code by AST nodes."""
        chunks = []

        try:
            tree = ast.parse(content)
            lines = content.split('\n')

            for node in ast.walk(tree):
                if isinstance(node, (ast.FunctionDef, ast.ClassDef, ast.AsyncFunctionDef)):
                    start_line = node.lineno - 1
                    end_line = node.end_lineno if hasattr(node, 'end_lineno') else start_line + 10

                    # Extract the code block
                    code_lines = lines[start_line:end_line]
                    code_content = '\n'.join(code_lines)

                    # Get docstring if available
                    docstring = ast.get_docstring(node)

                    chunks.append({
                        "content": code_content,
                        "metadata": {
                            "code_type": "function" if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) else "class",
                            "name": node.name,
                            "language": "python",
                            "start_line": start_line + 1,
                            "end_line": end_line,
                            "docstring": docstring,
                            "chunk_type": "code_block"
                        }
                    })

        except SyntaxError:
            # Fallback to text chunking if parsing fails
            text_chunks = self.chunk_text(content)
            for i, chunk in enumerate(text_chunks):
                chunks.append({
                    "content": chunk,
                    "metadata": {
                        "code_type": "unparseable",
                        "language": "python",
                        "chunk_index": i,
                        "chunk_type": "code_block"
                    }
                })

        return chunks
