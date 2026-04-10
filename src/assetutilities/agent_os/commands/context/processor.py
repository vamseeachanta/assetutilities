# ABOUTME: Context processing engine for document analysis and pattern extraction.
# ABOUTME: Extracted from context_optimization.py ContextProcessor class.
"""Processes and analyzes document context."""

import re
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any

from assetutilities.agent_os.commands.context.chunking import DocumentChunker

class ContextProcessor:
    """Processes and analyzes document context."""

    def __init__(self, cache_dir: Path):
        """Initialize the processor.
        
        Args:
            cache_dir: Directory for caching processed data
        """
        self.cache_dir = cache_dir
        self.chunker = DocumentChunker()

    def process_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Process multiple documents into structured context.
        
        Args:
            documents: List of document dictionaries
            
        Returns:
            Processed context data
        """
        all_chunks = []
        all_content = ""
        
        # Process each document
        for doc in documents:
            content = doc.get("content", "")
            doc_type = doc.get("type", "text")
            
            # Chunk the document
            if doc_type == "markdown":
                chunks = self.chunker.chunk_markdown(content)
            elif doc_type == "code":
                language = doc.get("language", "python")
                chunks = self.chunker.chunk_code(content, language)
            else:
                # Default text chunking
                text_chunks = self.chunker.chunk_text(content)
                chunks = []
                for i, chunk in enumerate(text_chunks):
                    chunks.append({
                        "content": chunk,
                        "metadata": {
                            "chunk_index": i,
                            "chunk_type": "text",
                            "source_doc": doc.get("id", "unknown")
                        }
                    })
            
            # Add document metadata to chunks
            for chunk in chunks:
                chunk["metadata"]["source_document"] = doc.get("id", "unknown")
                chunk["metadata"]["source_path"] = doc.get("path", "")
                chunk["metadata"]["document_type"] = doc_type
            
            all_chunks.extend(chunks)
            all_content += content + "\n"
        
        # Extract patterns, concepts, and APIs from all content
        patterns = self.extract_patterns(all_content)
        concepts = self.identify_concepts(all_content)
        apis = self.extract_api_signatures(all_content)
        
        return {
            "chunks": all_chunks,
            "patterns": patterns,
            "concepts": concepts,
            "apis": apis,
            "processed_at": datetime.now().isoformat(),
            "total_documents": len(documents)
        }

    def extract_patterns(self, content: str) -> List[Dict[str, Any]]:
        """Extract design and code patterns from content.
        
        Args:
            content: Content to analyze
            
        Returns:
            List of identified patterns
        """
        patterns = []
        
        # Design pattern keywords
        design_patterns = {
            "Factory": r"\b(?:factory|Factory)\s+(?:pattern|Pattern|method|Method)\b",
            "Observer": r"\b(?:observer|Observer)\s+(?:pattern|Pattern)\b",
            "Singleton": r"\b(?:singleton|Singleton)\s+(?:pattern|Pattern)\b",
            "Strategy": r"\b(?:strategy|Strategy)\s+(?:pattern|Pattern)\b",
            "Builder": r"\b(?:builder|Builder)\s+(?:pattern|Pattern)\b",
            "Adapter": r"\b(?:adapter|Adapter)\s+(?:pattern|Pattern)\b",
            "Decorator": r"\b(?:decorator|Decorator)\s+(?:pattern|Pattern)\b",
            "Command": r"\b(?:command|Command)\s+(?:pattern|Pattern)\b"
        }
        
        for pattern_name, pattern_regex in design_patterns.items():
            matches = list(re.finditer(pattern_regex, content, re.IGNORECASE))
            if matches:
                # Extract context around matches
                examples = []
                for match in matches[:3]:  # Limit to 3 examples
                    start = max(0, match.start() - 50)
                    end = min(len(content), match.end() + 50)
                    context = content[start:end].strip()
                    examples.append(context)
                
                patterns.append({
                    "name": pattern_name,
                    "type": "design_pattern",
                    "description": f"{pattern_name} pattern implementation",
                    "examples": examples,
                    "confidence": min(1.0, len(matches) * 0.3)
                })
        
        # Code patterns (common programming constructs)
        code_patterns = {
            "API_Endpoint": r"(?:GET|POST|PUT|DELETE|PATCH)\s+/[/\w\-{}]+",
            "Class_Definition": r"class\s+\w+(?:\([^)]*\))?:",
            "Function_Definition": r"def\s+\w+\([^)]*\):",
            "Error_Handling": r"try:|except\s+\w+:|finally:",
            "Async_Pattern": r"async\s+def|await\s+\w+"
        }
        
        for pattern_name, pattern_regex in code_patterns.items():
            matches = list(re.finditer(pattern_regex, content, re.IGNORECASE | re.MULTILINE))
            if matches:
                patterns.append({
                    "name": pattern_name.replace("_", " "),
                    "type": "code_pattern",
                    "description": f"Code pattern: {pattern_name.replace('_', ' ')}",
                    "examples": [match.group() for match in matches[:5]],
                    "confidence": min(1.0, len(matches) * 0.1)
                })
        
        return patterns

    def identify_concepts(self, content: str) -> List[Dict[str, Any]]:
        """Identify domain-specific concepts in content.
        
        Args:
            content: Content to analyze
            
        Returns:
            List of identified concepts
        """
        concepts = []
        
        # Technical concepts (classes ending with common suffixes)
        technical_patterns = [
            (r'\b([A-Z][a-zA-Z]*(?:Service|Manager|Controller|Handler|Processor))\b', 'service'),
            (r'\b([A-Z][a-zA-Z]*(?:Repository|DAO|Model|Entity))\b', 'data'),
            (r'\b([A-Z][a-zA-Z]*(?:Factory|Builder|Strategy|Adapter))\b', 'pattern'),
            (r'\b([A-Z][a-zA-Z]*(?:Exception|Error))\b', 'exception'),
            (r'\b([A-Z][a-zA-Z]*(?:Config|Configuration|Settings))\b', 'configuration')
        ]
        
        concept_counts = {}
        concept_types = {}
        
        for pattern, concept_type in technical_patterns:
            matches = re.finditer(pattern, content)
            for match in matches:
                concept_name = match.group(1)
                concept_counts[concept_name] = concept_counts.get(concept_name, 0) + 1
                concept_types[concept_name] = concept_type
        
        # Convert to concept objects
        for name, frequency in concept_counts.items():
            if frequency >= 1:  # Include concepts that appear at least once
                # Find related concepts (other concepts that appear near this one)
                related = self._find_related_concepts(content, name, list(concept_counts.keys()))
                
                concepts.append({
                    "name": name,
                    "type": concept_types[name],
                    "description": f"{concept_types[name].title()} component: {name}",
                    "related": related,
                    "frequency": frequency
                })
        
        return concepts

    def extract_api_signatures(self, content: str) -> List[Dict[str, Any]]:
        """Extract API signatures from content.
        
        Args:
            content: Content to analyze
            
        Returns:
            List of API signatures
        """
        apis = []
        
        # REST API endpoints
        rest_pattern = r'(GET|POST|PUT|DELETE|PATCH)\s+([/\w\-{}]+)(?:\s*-\s*(.+?)(?:\n|$))?'
        rest_matches = re.finditer(rest_pattern, content, re.IGNORECASE | re.MULTILINE)
        
        for match in rest_matches:
            method = match.group(1).upper()
            path = match.group(2)
            description = match.group(3) or ""
            
            apis.append({
                "name": f"{method} {path}",
                "signature": f"{method} {path}",
                "description": description.strip(),
                "parameters": self._extract_path_parameters(path),
                "return_type": "JSON",
                "api_type": "REST"
            })
        
        # Python function signatures
        func_pattern = r'def\s+(\w+)\s*\(([^)]*)\)(?:\s*->\s*([^:]+))?:'
        func_matches = re.finditer(func_pattern, content, re.MULTILINE)
        
        for match in func_matches:
            func_name = match.group(1)
            params_str = match.group(2) or ""
            return_type = match.group(3) or "Any"
            
            # Parse parameters
            parameters = []
            if params_str.strip():
                param_parts = [p.strip() for p in params_str.split(',')]
                for param in param_parts:
                    if ':' in param:
                        param_name, param_type = param.split(':', 1)
                        parameters.append({
                            "name": param_name.strip(),
                            "type": param_type.strip(),
                            "required": '=' not in param
                        })
                    else:
                        parameters.append({
                            "name": param.strip(),
                            "type": "Any",
                            "required": '=' not in param
                        })
            
            apis.append({
                "name": func_name,
                "signature": f"def {func_name}({params_str}) -> {return_type.strip()}",
                "description": f"Function: {func_name}",
                "parameters": parameters,
                "return_type": return_type.strip(),
                "api_type": "function"
            })
        
        return apis

    def _find_related_concepts(self, content: str, concept: str, all_concepts: List[str]) -> List[str]:
        """Find concepts that appear near the given concept."""
        related = []
        concept_positions = [m.start() for m in re.finditer(re.escape(concept), content)]
        
        for other_concept in all_concepts:
            if other_concept == concept:
                continue
                
            other_positions = [m.start() for m in re.finditer(re.escape(other_concept), content)]
            
            # Check if concepts appear within 500 characters of each other
            for pos1 in concept_positions:
                for pos2 in other_positions:
                    if abs(pos1 - pos2) < 500:
                        if other_concept not in related:
                            related.append(other_concept)
                        break
                if other_concept in related:
                    break
        
        return related[:5]  # Limit to 5 related concepts

    def _extract_path_parameters(self, path: str) -> List[Dict[str, Any]]:
        """Extract parameters from REST API path."""
        parameters = []
        param_pattern = r'\{(\w+)\}'
        
        for match in re.finditer(param_pattern, path):
            param_name = match.group(1)
            parameters.append({
                "name": param_name,
                "type": "string",
                "location": "path",
                "required": True
            })
        
        return parameters


