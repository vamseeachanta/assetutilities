"""Documentation Integration System.

This module provides comprehensive documentation scanning, linking, and
processing capabilities for the Agent OS create-module-agent system.
"""

import re
import ast
import yaml
import requests
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional
from dataclasses import dataclass
from bs4 import BeautifulSoup


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


class ReferenceManager:
    """Manages documentation references and cross-references."""

    def __init__(self, base_dir: Path):
        """Initialize the reference manager.
        
        Args:
            base_dir: Base directory for agents
        """
        self.base_dir = base_dir

    def create_reference_structure(self, agent_name: str, 
                                 references: Dict[str, Any]) -> None:
        """Create reference structure for an agent.
        
        Args:
            agent_name: Name of the agent
            references: Reference configuration
        """
        agent_dir = self.base_dir / agent_name
        context_dir = agent_dir / "context"
        
        # Create directories
        (context_dir / "repository").mkdir(parents=True, exist_ok=True)
        (context_dir / "external").mkdir(parents=True, exist_ok=True)
        
        # Save references configuration
        references_path = context_dir / "repository" / "references.yaml"
        with open(references_path, 'w') as f:
            yaml.dump(references, f, default_flow_style=False, indent=2)

    def update_internal_references(self, agent_name: str, 
                                 repo_docs: Dict[str, Dict[str, Any]]) -> None:
        """Update internal documentation references.
        
        Args:
            agent_name: Name of the agent
            repo_docs: Repository documentation data
        """
        agent_dir = self.base_dir / agent_name
        internal_path = agent_dir / "context" / "repository" / "internal.md"
        
        # Generate internal documentation
        content = self._generate_internal_doc(repo_docs)
        
        agent_dir.mkdir(parents=True, exist_ok=True)
        internal_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(internal_path, 'w') as f:
            f.write(content)

    def update_external_references(self, agent_name: str,
                                 external_docs: List[Dict[str, Any]]) -> None:
        """Update external documentation references.
        
        Args:
            agent_name: Name of the agent
            external_docs: External documentation data
        """
        agent_dir = self.base_dir / agent_name
        external_path = agent_dir / "context" / "external" / "web_sources.yaml"
        
        external_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(external_path, 'w') as f:
            yaml.dump(external_docs, f, default_flow_style=False, indent=2)

    def generate_cross_references(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate cross-references between documents.
        
        Args:
            documents: List of documents to cross-reference
            
        Returns:
            List of cross-references
        """
        cross_refs = []
        
        # Extract terms from all documents
        all_terms = set()
        for doc in documents:
            terms = self._extract_terms(doc["content"])
            all_terms.update(terms)
        
        # Find cross-references
        for term in all_terms:
            references = []
            for doc in documents:
                if term.lower() in doc["content"].lower():
                    references.append({
                        "document": doc["name"],
                        "context": self._extract_context(doc["content"], term)
                    })
            
            if len(references) > 1:  # Term appears in multiple documents
                cross_refs.append({
                    "term": term,
                    "references": references,
                    "count": len(references)
                })
        
        return cross_refs

    def _generate_internal_doc(self, repo_docs: Dict[str, Dict[str, Any]]) -> str:
        """Generate internal documentation content.
        
        Args:
            repo_docs: Repository documentation data
            
        Returns:
            Generated documentation content
        """
        content = ["# Internal Documentation References\n"]
        content.append(f"Generated: {datetime.now().isoformat()}\n")
        
        for repo_name, docs in repo_docs.items():
            content.append(f"## {repo_name}\n")
            
            # Add README content
            if docs.get("readme_content"):
                content.append("### README\n")
                content.append(docs["readme_content"][:500] + "...\n")
            
            # Add markdown files
            if docs.get("markdown_files"):
                content.append("### Documentation Files\n")
                for md_file in docs["markdown_files"]:
                    content.append(f"#### {md_file['name']}\n")
                    content.append(f"Path: `{md_file['path']}`\n")
                    content.append(md_file["content"][:300] + "...\n")
            
            # Add docstrings
            if docs.get("python_docstrings"):
                content.append("### Python Documentation\n")
                for docstring in docs["python_docstrings"]:
                    content.append(f"#### {docstring['name']} ({docstring['type']})\n")
                    content.append(f"File: `{docstring['file']}`\n")
                    content.append(docstring["content"] + "\n")
        
        return "\n".join(content)

    def _extract_terms(self, content: str) -> List[str]:
        """Extract important terms from content.
        
        Args:
            content: Content to extract terms from
            
        Returns:
            List of extracted terms
        """
        # Simple term extraction - could be enhanced with NLP
        terms = []
        
        # Extract class names (PascalCase)
        class_pattern = r'\b[A-Z][a-zA-Z0-9]*(?:[A-Z][a-zA-Z0-9]*)*\b'
        terms.extend(re.findall(class_pattern, content))
        
        # Extract function names with parentheses
        function_pattern = r'\b[a-z_][a-zA-Z0-9_]*\(\)'
        terms.extend([term[:-2] for term in re.findall(function_pattern, content)])
        
        # Extract API endpoints
        api_pattern = r'/[a-zA-Z0-9_/\-]+'
        terms.extend(re.findall(api_pattern, content))
        
        return list(set(terms))

    def _extract_context(self, content: str, term: str) -> str:
        """Extract context around a term.
        
        Args:
            content: Content containing the term
            term: Term to find context for
            
        Returns:
            Context around the term
        """
        # Find the term and extract surrounding context
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        match = pattern.search(content)
        
        if match:
            start = max(0, match.start() - 50)
            end = min(len(content), match.end() + 50)
            return content[start:end].strip()
        
        return ""


class DocumentationProcessor:
    """Processes and analyzes documentation content."""

    def __init__(self):
        """Initialize the processor."""
        self.markdown_parser = MarkdownParser()

    def process_markdown_content(self, content: str) -> Dict[str, Any]:
        """Process markdown content.
        
        Args:
            content: Markdown content
            
        Returns:
            Processed content information
        """
        result = {
            "title": self._extract_title(content),
            "sections": self.markdown_parser.parse_headers(content),
            "code_blocks": self.markdown_parser.parse_code_blocks(content),
            "links": self.markdown_parser.parse_links(content),
            "tables": self.markdown_parser.extract_tables(content),
            "word_count": len(content.split()),
            "line_count": len(content.splitlines())
        }
        
        return result

    def extract_api_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Extract API patterns from content.
        
        Args:
            content: Content to analyze
            
        Returns:
            List of API patterns
        """
        patterns = []
        
        # HTTP method patterns
        http_pattern = r'(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-\{\}]+)(?:\s*-\s*(.+))?'
        matches = re.finditer(http_pattern, content, re.IGNORECASE | re.MULTILINE)
        
        for match in matches:
            patterns.append({
                "method": match.group(1).upper(),
                "endpoint": match.group(2),
                "description": match.group(3) or "",
                "line": content[:match.start()].count('\n') + 1
            })
        
        return patterns

    def extract_domain_concepts(self, content: str) -> List[Dict[str, Any]]:
        """Extract domain-specific concepts.
        
        Args:
            content: Content to analyze
            
        Returns:
            List of domain concepts
        """
        concepts = []
        
        # Common domain concept patterns
        patterns = [
            r'\b([A-Z][a-zA-Z]*(?:Service|Manager|Controller|Handler|Processor))\b',
            r'\b([A-Z][a-zA-Z]*(?:Repository|DAO|Model|Entity))\b',
            r'\b([A-Z][a-zA-Z]*(?:Factory|Builder|Strategy|Adapter))\b'
        ]
        
        for pattern in patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                concept_name = match.group(1)
                context = self._extract_concept_context(content, match)
                
                concepts.append({
                    "name": concept_name,
                    "type": self._classify_concept(concept_name),
                    "context": context,
                    "line": content[:match.start()].count('\n') + 1
                })
        
        # Remove duplicates
        seen = set()
        unique_concepts = []
        for concept in concepts:
            if concept["name"] not in seen:
                seen.add(concept["name"])
                unique_concepts.append(concept)
        
        return unique_concepts

    def create_summary(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create summary of documentation.
        
        Args:
            documents: List of documents
            
        Returns:
            Documentation summary
        """
        summary = {
            "total_documents": len(documents),
            "document_types": {},
            "total_size": 0,
            "key_topics": [],
            "generated_at": datetime.now().isoformat()
        }
        
        # Analyze document types and sizes
        for doc in documents:
            doc_type = doc.get("type", "unknown")
            summary["document_types"][doc_type] = summary["document_types"].get(doc_type, 0) + 1
            summary["total_size"] += len(doc.get("content", ""))
        
        # Extract key topics (simplified - could use NLP)
        all_content = " ".join(doc.get("content", "") for doc in documents)
        key_topics = self._extract_key_topics(all_content)
        summary["key_topics"] = key_topics[:10]  # Top 10 topics
        
        return summary

    def _extract_title(self, content: str) -> Optional[str]:
        """Extract title from markdown content."""
        lines = content.split('\n')
        for line in lines:
            line = line.strip()
            if line.startswith('# '):
                return line[2:].strip()
        return None

    def _extract_concept_context(self, content: str, match: re.Match) -> str:
        """Extract context around a concept match."""
        start = max(0, match.start() - 100)
        end = min(len(content), match.end() + 100)
        return content[start:end].strip()

    def _classify_concept(self, concept_name: str) -> str:
        """Classify a concept by its name."""
        if any(suffix in concept_name for suffix in ['Service', 'Manager', 'Handler']):
            return 'service'
        elif any(suffix in concept_name for suffix in ['Repository', 'DAO']):
            return 'data_access'
        elif any(suffix in concept_name for suffix in ['Model', 'Entity']):
            return 'model'
        elif any(suffix in concept_name for suffix in ['Controller']):
            return 'controller'
        else:
            return 'other'

    def _extract_key_topics(self, content: str) -> List[str]:
        """Extract key topics from content."""
        # Simple keyword extraction - could be enhanced with TF-IDF or NLP
        words = re.findall(r'\b[A-Za-z]{4,}\b', content.lower())
        
        # Common technical terms to prioritize
        tech_terms = {
            'api', 'endpoint', 'service', 'function', 'class', 'method',
            'database', 'model', 'authentication', 'authorization', 'user',
            'configuration', 'integration', 'documentation', 'testing'
        }
        
        # Count word frequencies
        word_freq = {}
        for word in words:
            if word in tech_terms or len(word) > 6:
                word_freq[word] = word_freq.get(word, 0) + 1
        
        # Return most frequent terms
        return sorted(word_freq.keys(), key=lambda x: word_freq[x], reverse=True)


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