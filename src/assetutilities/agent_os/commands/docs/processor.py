# ABOUTME: Documentation processing and context generation pipeline.
# ABOUTME: Extracted from documentation_integration.py DocumentationProcessor class.
"""Documentation processing for the documentation integration system."""

import re
import yaml
from pathlib import Path
from typing import List, Dict, Any, Optional
from datetime import datetime

from assetutilities.agent_os.commands.docs.scanner import RepositoryDocumentationScanner
from assetutilities.agent_os.commands.docs.linker import ExternalDocumentationLinker
from assetutilities.agent_os.commands.docs.parser import MarkdownParser
from assetutilities.agent_os.commands.docs.references import ReferenceManager

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


