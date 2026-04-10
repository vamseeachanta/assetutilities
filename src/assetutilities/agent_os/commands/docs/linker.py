# ABOUTME: External documentation linking and URL validation.
# ABOUTME: Extracted from documentation_integration.py ExternalDocumentationLinker class.
"""External documentation linking for the documentation integration system."""

import re
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from bs4 import BeautifulSoup

class ExternalDocumentationLinker:
    """Links and processes external documentation sources."""

    def __init__(self):
        """Initialize the linker."""
        self.session = requests.Session()
        self.session.headers.update({
            'User-Agent': 'Agent-OS-Documentation-Scanner/1.0'
        })

    def fetch_web_documentation(self, url: str, timeout: int = 30) -> Dict[str, Any]:
        """Fetch documentation from web URL.
        
        Args:
            url: URL to fetch
            timeout: Request timeout in seconds
            
        Returns:
            Dictionary with fetched content and metadata
        """
        try:
            response = self.session.get(url, timeout=timeout)
            response.raise_for_status()
            
            # Parse HTML content
            soup = BeautifulSoup(response.text, 'html.parser')
            
            # Extract main content (remove navigation, footer, etc.)
            main_content = self._extract_main_content(soup)
            
            return {
                "url": url,
                "status": "success",
                "content": main_content,
                "title": soup.title.string if soup.title else None,
                "content_type": response.headers.get('content-type', ''),
                "fetched_at": datetime.now().isoformat(),
                "size": len(response.text)
            }
            
        except Exception as e:
            return {
                "url": url,
                "status": "error",
                "error": str(e),
                "fetched_at": datetime.now().isoformat()
            }

    def parse_api_documentation(self, content: str) -> Dict[str, Any]:
        """Parse API documentation content.
        
        Args:
            content: Documentation content
            
        Returns:
            Parsed API information
        """
        endpoints = []
        seen_endpoints = set()
        
        # Common API documentation patterns (in order of specificity)
        patterns = [
            r'###?\s+(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-\{\}]+)',  # Markdown headers (most specific)
            r'`(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-\{\}]+)`',  # Code blocks
            r'(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-\{\}]+)',  # HTTP methods with paths (least specific)
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content, re.IGNORECASE | re.MULTILINE)
            for match in matches:
                method = match.group(1).upper()
                path = match.group(2)
                endpoint_key = f"{method} {path}"
                
                # Skip if we've already found this endpoint
                if endpoint_key in seen_endpoints:
                    continue
                    
                seen_endpoints.add(endpoint_key)
                
                # Extract description (look for text after the endpoint)
                start_pos = match.end()
                description = self._extract_endpoint_description(content, start_pos)
                
                endpoints.append({
                    "method": method,
                    "path": path,
                    "description": description,
                    "line": content[:match.start()].count('\n') + 1
                })

        return {
            "endpoints": endpoints,
            "total_endpoints": len(endpoints),
            "methods": list(set(ep["method"] for ep in endpoints))
        }

    def extract_code_examples(self, content: str) -> List[Dict[str, Any]]:
        """Extract code examples from documentation.
        
        Args:
            content: Documentation content
            
        Returns:
            List of code examples
        """
        examples = []
        
        # Markdown code blocks  
        code_block_pattern = r'```(\w+)\n(.*?)\n\s*```'
        matches = re.finditer(code_block_pattern, content, re.DOTALL)
        
        for match in matches:
            language = match.group(1) or 'text'
            code = match.group(2).strip()
            
            examples.append({
                "language": language.lower(),
                "content": code,
                "line": content[:match.start()].count('\n') + 1,
                "size": len(code)
            })

        return examples

    def _extract_main_content(self, soup: BeautifulSoup) -> str:
        """Extract main content from HTML soup.
        
        Args:
            soup: BeautifulSoup object
            
        Returns:
            Extracted main content
        """
        # Remove navigation, footer, sidebar elements
        for tag in soup.find_all(['nav', 'footer', 'aside', 'header']):
            tag.decompose()
        
        # Remove script and style elements
        for tag in soup.find_all(['script', 'style']):
            tag.decompose()
        
        # Look for main content areas
        main_selectors = ['main', 'article', '.content', '#content', '.documentation']
        
        for selector in main_selectors:
            element = soup.select_one(selector)
            if element:
                return element.get_text(strip=True)
        
        # Fallback to body content
        body = soup.find('body')
        if body:
            return body.get_text(strip=True)
        
        return soup.get_text(strip=True)

    def _extract_endpoint_description(self, content: str, start_pos: int) -> str:
        """Extract description for an API endpoint.
        
        Args:
            content: Full content
            start_pos: Position after endpoint definition
            
        Returns:
            Endpoint description
        """
        # Look for description in the next few lines
        remaining_content = content[start_pos:start_pos + 200]
        lines = remaining_content.split('\n')
        
        description_lines = []
        for line in lines[:3]:  # Check first 3 lines
            line = line.strip()
            if line and not line.startswith(('#', '##', '###')):
                description_lines.append(line)
            elif description_lines:
                break
        
        return ' '.join(description_lines)


