# ABOUTME: Markdown parsing and content extraction utilities.
# ABOUTME: Extracted from documentation_integration.py MarkdownParser class.
"""Markdown parsing for the documentation integration system."""

import re
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

class MarkdownParser:
    """Parses markdown content for structured information."""

    def parse_headers(self, content: str) -> List[Dict[str, Any]]:
        """Parse markdown headers.
        
        Args:
            content: Markdown content
            
        Returns:
            List of headers with levels and text
        """
        headers = []
        header_pattern = r'^(#{1,6})\s+(.+)$'
        
        for line_num, line in enumerate(content.split('\n'), 1):
            match = re.match(header_pattern, line.strip())
            if match:
                level = len(match.group(1))
                text = match.group(2).strip()
                headers.append({
                    "level": level,
                    "text": text,
                    "line": line_num
                })
        
        return headers

    def parse_code_blocks(self, content: str) -> List[Dict[str, Any]]:
        """Parse code blocks from markdown.
        
        Args:
            content: Markdown content
            
        Returns:
            List of code blocks
        """
        code_blocks = []
        pattern = r'```(\w+)\n(.*?)\n\s*```'
        
        for match in re.finditer(pattern, content, re.DOTALL):
            language = match.group(1) or 'text'
            code = match.group(2)
            line = content[:match.start()].count('\n') + 1
            
            code_blocks.append({
                "language": language.lower(),
                "content": code,
                "line": line,
                "size": len(code)
            })
        
        return code_blocks

    def parse_links(self, content: str) -> List[Dict[str, Any]]:
        """Parse links from markdown.
        
        Args:
            content: Markdown content
            
        Returns:
            List of links
        """
        links = []
        pattern = r'\[([^\]]+)\]\(([^)]+)\)'
        
        for match in re.finditer(pattern, content):
            text = match.group(1)
            url = match.group(2)
            line = content[:match.start()].count('\n') + 1
            
            links.append({
                "text": text,
                "url": url,
                "line": line,
                "type": "external" if url.startswith('http') else "internal"
            })
        
        return links

    def extract_tables(self, content: str) -> List[Dict[str, Any]]:
        """Extract tables from markdown.
        
        Args:
            content: Markdown content
            
        Returns:
            List of table data
        """
        tables = []
        lines = content.split('\n')
        
        i = 0
        while i < len(lines):
            line = lines[i].strip()
            
            # Check if this looks like a table header
            if '|' in line and i + 1 < len(lines):
                next_line = lines[i + 1].strip()
                
                # Check for separator line
                if '|' in next_line and '-' in next_line:
                    # Extract table
                    table = self._extract_table(lines, i)
                    if table:
                        tables.append(table)
                        i += len(table["rows"]) + 2  # Skip processed lines
                        continue
            
            i += 1
        
        return tables

    def _extract_table(self, lines: List[str], start_index: int) -> Optional[Dict[str, Any]]:
        """Extract a single table starting at the given index."""
        if start_index + 1 >= len(lines):
            return None
        
        # Parse header
        header_line = lines[start_index].strip()
        headers = [h.strip() for h in header_line.split('|') if h.strip()]
        
        # Skip separator line
        table_rows = []
        i = start_index + 2
        
        # Parse data rows
        while i < len(lines):
            line = lines[i].strip()
            if not line or '|' not in line:
                break
            
            row_data = [cell.strip() for cell in line.split('|') if cell.strip()]
            if row_data:
                table_rows.append(row_data)
            
            i += 1
        
        if headers and table_rows:
            return {
                "headers": headers,
                "rows": table_rows,
                "line": start_index + 1
            }
        
        return None