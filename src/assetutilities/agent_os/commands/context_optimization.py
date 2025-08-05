"""Context Optimization Engine.

This module provides comprehensive context optimization, caching, and
semantic search capabilities for the Agent OS create-module-agent system.
"""

import re
import ast
import json
import hashlib
import pickle
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Union, Tuple
from dataclasses import dataclass, asdict
import numpy as np

try:
    from sentence_transformers import SentenceTransformer
    SENTENCE_TRANSFORMERS_AVAILABLE = True
except ImportError:
    SENTENCE_TRANSFORMERS_AVAILABLE = False
    SentenceTransformer = None

try:
    import faiss
    FAISS_AVAILABLE = True
except ImportError:
    FAISS_AVAILABLE = False
    faiss = None


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


class EmbeddingGenerator:
    """Generates embeddings for semantic search."""

    def __init__(self, model_name: str = "all-MiniLM-L6-v2"):
        """Initialize the embedding generator.
        
        Args:
            model_name: Name of the sentence transformer model
        """
        self.model_name = model_name
        self.model = None
        
        if SENTENCE_TRANSFORMERS_AVAILABLE:
            try:
                self.model = SentenceTransformer(model_name)
            except Exception as e:
                print(f"Warning: Could not load sentence transformer model: {e}")
                self.model = None
        else:
            print("Warning: sentence-transformers not available. Embeddings will be mock vectors.")

    def generate_text_embedding(self, text: str) -> np.ndarray:
        """Generate embedding for a single text.
        
        Args:
            text: Text to embed
            
        Returns:
            Embedding vector
        """
        if self.model is not None:
            return self.model.encode(text)
        else:
            # Return mock embedding for testing
            hash_val = hashlib.md5(text.encode()).hexdigest()
            # Convert hex to numbers
            mock_embedding = [int(hash_val[i:i+2], 16) / 255.0 for i in range(0, min(len(hash_val), 8), 2)]
            return np.array(mock_embedding + [0.0] * (384 - len(mock_embedding)))

    def generate_batch_embeddings(self, texts: List[str]) -> np.ndarray:
        """Generate embeddings for multiple texts.
        
        Args:
            texts: List of texts to embed
            
        Returns:
            Array of embedding vectors
        """
        if self.model is not None:
            return self.model.encode(texts)
        else:
            # Return mock embeddings
            return np.array([self.generate_text_embedding(text) for text in texts])

    def embed_document_chunks(self, chunks: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Generate embeddings for document chunks.
        
        Args:
            chunks: List of document chunks
            
        Returns:
            Dictionary with embeddings and chunk metadata
        """
        texts = [chunk["content"] for chunk in chunks]
        embeddings = self.generate_batch_embeddings(texts)
        
        # Add embeddings to chunks
        for i, chunk in enumerate(chunks):
            chunk["embedding"] = embeddings[i]
        
        return {
            "embeddings": embeddings,
            "chunk_ids": [chunk.get("metadata", {}).get("id", str(i)) for i, chunk in enumerate(chunks)],
            "chunks": chunks
        }


class ContextCache:
    """Manages context caching and persistence."""

    def __init__(self, cache_dir: Path):
        """Initialize the cache.
        
        Args:
            cache_dir: Directory for cache files
        """
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.cache_file = self.cache_dir / "cache.json"
        self.embeddings_file = self.cache_dir / "embeddings.npy"
        self.metadata_file = self.cache_dir / "metadata.json"

    def save_cache_data(self, data: Dict[str, Any]) -> None:
        """Save cache data to JSON file.
        
        Args:
            data: Cache data to save
        """
        # Separate embeddings from main data
        clean_data = self._clean_data_for_json(data)
        
        with open(self.cache_file, 'w') as f:
            json.dump(clean_data, f, indent=2, default=str)

    def load_cache_data(self) -> Dict[str, Any]:
        """Load cache data from JSON file.
        
        Returns:
            Loaded cache data
        """
        if not self.cache_file.exists():
            return {}
        
        with open(self.cache_file, 'r') as f:
            return json.load(f)

    def save_embeddings(self, embeddings: np.ndarray) -> None:
        """Save embeddings to binary file.
        
        Args:
            embeddings: Embedding vectors to save
        """
        np.save(self.embeddings_file, embeddings)

    def load_embeddings(self) -> Optional[np.ndarray]:
        """Load embeddings from binary file.
        
        Returns:
            Loaded embedding vectors or None if not found
        """
        if not self.embeddings_file.exists():
            return None
        
        return np.load(self.embeddings_file)

    def is_valid(self, max_age_hours: int = 24) -> bool:
        """Check if cache is still valid.
        
        Args:
            max_age_hours: Maximum age in hours
            
        Returns:
            True if cache is valid
        """
        if not self.cache_file.exists():
            return False
        
        # Check age
        cache_time = datetime.fromtimestamp(self.cache_file.stat().st_mtime)
        age = datetime.now() - cache_time
        
        return age.total_seconds() < max_age_hours * 3600

    def is_valid_for_sources(self, source_files: List[Path]) -> bool:
        """Check if cache is valid for given source files.
        
        Args:
            source_files: List of source file paths
            
        Returns:
            True if cache is newer than all source files
        """
        if not self.cache_file.exists():
            return False
        
        cache_time = self.cache_file.stat().st_mtime
        
        for source_file in source_files:
            if source_file.exists() and source_file.stat().st_mtime > cache_time:
                return False
        
        return True

    def update_chunks(self, new_chunks: List[Dict[str, Any]]) -> None:
        """Update cache with new chunks.
        
        Args:
            new_chunks: New chunks to add
        """
        data = self.load_cache_data()
        
        if "chunks" not in data:
            data["chunks"] = []
        
        data["chunks"].extend(new_chunks)
        data["last_updated"] = datetime.now().isoformat()
        
        self.save_cache_data(data)

    def get_cache_info(self) -> Dict[str, Any]:
        """Get information about the cache.
        
        Returns:
            Cache information dictionary
        """
        info = {
            "exists": self.cache_file.exists(),
            "cache_file": str(self.cache_file),
            "embeddings_file": str(self.embeddings_file)
        }
        
        if self.cache_file.exists():
            stat = self.cache_file.stat()
            info.update({
                "size_bytes": stat.st_size,
                "created": datetime.fromtimestamp(stat.st_ctime).isoformat(),
                "modified": datetime.fromtimestamp(stat.st_mtime).isoformat()
            })
            
            data = self.load_cache_data()
            info.update({
                "version": data.get("version", "unknown"),
                "total_chunks": len(data.get("chunks", [])),
                "total_patterns": len(data.get("patterns", [])),
                "total_concepts": len(data.get("concepts", []))
            })
        
        return info

    def _clean_data_for_json(self, data: Dict[str, Any]) -> Dict[str, Any]:
        """Clean data for JSON serialization by removing numpy arrays."""
        clean_data = {}
        
        for key, value in data.items():
            if isinstance(value, np.ndarray):
                continue  # Skip numpy arrays
            elif isinstance(value, list):
                clean_list = []
                for item in value:
                    if isinstance(item, dict):
                        clean_item = {}
                        for k, v in item.items():
                            if not isinstance(v, np.ndarray):
                                clean_item[k] = v
                        clean_list.append(clean_item)
                    else:
                        clean_list.append(item)
                clean_data[key] = clean_list
            else:
                clean_data[key] = value
        
        return clean_data


class SemanticSearch:
    """Provides semantic search capabilities."""

    def __init__(self, embeddings: np.ndarray, documents: List[Dict[str, Any]]):
        """Initialize semantic search.
        
        Args:
            embeddings: Document embeddings
            documents: Document metadata
        """
        self.embeddings = embeddings
        self.documents = documents
        self.index = None
        self.embedding_generator = EmbeddingGenerator()
        
        if FAISS_AVAILABLE and embeddings is not None:
            self._build_faiss_index()

    def _build_faiss_index(self) -> None:
        """Build FAISS index for fast similarity search."""
        if self.embeddings is None or len(self.embeddings) == 0:
            return
        
        dimension = self.embeddings.shape[1]
        self.index = faiss.IndexFlatL2(dimension)
        self.index.add(self.embeddings.astype('float32'))

    def search(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """Search for similar content.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            List of search results
        """
        if self.index is None:
            # Fallback to simple text matching
            return self._text_search(query, k)
        
        # Generate query embedding
        query_embedding = self.embedding_generator.generate_text_embedding(query)
        
        # Search index
        distances, indices = self.index.search(
            query_embedding.astype('float32').reshape(1, -1), 
            min(k, len(self.documents))
        )
        
        # Build results
        results = []
        for idx, distance in zip(indices[0], distances[0]):
            if idx < len(self.documents):
                doc = self.documents[idx]
                score = 1.0 / (1.0 + float(distance))  # Convert distance to similarity
                
                results.append({
                    "content": doc.get("content", ""),
                    "score": score,
                    "metadata": doc.get("metadata", {}),
                    "document_id": doc.get("id", str(idx))
                })
        
        return results

    def _text_search(self, query: str, k: int) -> List[Dict[str, Any]]:
        """Fallback text search when FAISS is not available."""
        results = []
        query_lower = query.lower()
        
        for i, doc in enumerate(self.documents):
            content = doc.get("content", "").lower()
            
            # Simple scoring based on term frequency
            score = 0.0
            query_terms = query_lower.split()
            
            for term in query_terms:
                score += content.count(term) * 0.1
            
            if score > 0:
                results.append({
                    "content": doc.get("content", ""),
                    "score": min(score, 1.0),
                    "metadata": doc.get("metadata", {}),
                    "document_id": doc.get("id", str(i))
                })
        
        # Sort by score and return top k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:k]

    def filter_by_metadata(self, documents: List[Dict[str, Any]], 
                          filters: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Filter documents by metadata criteria.
        
        Args:
            documents: Documents to filter
            filters: Metadata filters to apply
            
        Returns:
            Filtered documents
        """
        filtered = []
        
        for doc in documents:
            metadata = doc.get("metadata", {})
            match = True
            
            for key, value in filters.items():
                if key not in metadata or metadata[key] != value:
                    match = False
                    break
            
            if match:
                filtered.append(doc)
        
        return filtered

    def rank_results(self, results: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Rank search results by relevance.
        
        Args:
            results: Search results to rank
            
        Returns:
            Ranked results
        """
        return sorted(results, key=lambda x: x.get("score", 0), reverse=True)


class OptimizedContext:
    """Manages optimized context with caching and search capabilities."""

    def __init__(self, cache_dir: Path):
        """Initialize optimized context.
        
        Args:
            cache_dir: Directory for cache files
        """
        self.cache_dir = cache_dir
        self.cache = ContextCache(cache_dir)
        self.processor = ContextProcessor(cache_dir)
        self.embedding_generator = EmbeddingGenerator()
        self._data = None
        self._search_index = None

    def create_from_documents(self, documents: List[Dict[str, Any]]) -> Dict[str, Any]:
        """Create optimized context from documents.
        
        Args:
            documents: List of documents to process
            
        Returns:
            Processed context data
        """
        # Process documents
        processed = self.processor.process_documents(documents)
        
        # Generate embeddings for chunks
        chunks = processed.get("chunks", [])
        if chunks:
            embedding_data = self.embedding_generator.embed_document_chunks(chunks)
            processed["embeddings"] = embedding_data["embeddings"]
        
        # Save to cache
        self.cache.save_cache_data(processed)
        if "embeddings" in processed:
            self.cache.save_embeddings(processed["embeddings"])
        
        self._data = processed
        return processed

    def load_from_cache(self) -> Optional[Dict[str, Any]]:
        """Load context from cache.
        
        Returns:
            Cached context data or None if not available
        """
        if not self.cache.is_valid():
            return None
        
        data = self.cache.load_cache_data()
        embeddings = self.cache.load_embeddings()
        
        if embeddings is not None:
            data["embeddings"] = embeddings
        
        self._data = data
        return data

    def query(self, query: str, k: int = 10) -> List[Dict[str, Any]]:
        """Query the optimized context.
        
        Args:
            query: Search query
            k: Number of results to return
            
        Returns:
            Search results
        """
        if self._data is None:
            self.load_from_cache()
        
        if self._data is None:
            return []
        
        # Initialize search index if needed
        if self._search_index is None and "embeddings" in self._data:
            chunks = self._data.get("chunks", [])
            self._search_index = SemanticSearch(self._data["embeddings"], chunks)
        
        if self._search_index:
            return self._search_index.search(query, k)
        else:
            # Fallback to simple text search
            return self._simple_text_search(query, k)

    def add_document(self, document: Dict[str, Any]) -> None:
        """Add a new document to the context.
        
        Args:
            document: Document to add
        """
        if self._data is None:
            self.load_from_cache()
        
        # Process the new document
        processed = self.processor.process_documents([document])
        
        # Update existing data
        if self._data is None:
            self._data = processed
        else:
            self._data["chunks"].extend(processed.get("chunks", []))
            self._data["patterns"].extend(processed.get("patterns", []))
            self._data["concepts"].extend(processed.get("concepts", []))
            self._data["apis"].extend(processed.get("apis", []))
        
        # Invalidate search index
        self._search_index = None

    def get_statistics(self) -> Dict[str, Any]:
        """Get context statistics.
        
        Returns:
            Statistics dictionary
        """
        if self._data is None:
            self.load_from_cache()
        
        if self._data is None:
            return {"error": "No context data available"}
        
        stats = {
            "total_chunks": len(self._data.get("chunks", [])),
            "total_patterns": len(self._data.get("patterns", [])),
            "total_concepts": len(self._data.get("concepts", [])),
            "total_apis": len(self._data.get("apis", [])),
            "cache_info": self.cache.get_cache_info()
        }
        
        # Add memory usage estimate
        if "embeddings" in self._data:
            embeddings = self._data["embeddings"]
            stats["memory_usage"] = {
                "embeddings_size_mb": embeddings.nbytes / (1024 * 1024),
                "embedding_dimensions": embeddings.shape[1] if len(embeddings.shape) > 1 else 0,
                "total_embeddings": len(embeddings)
            }
        
        return stats

    def _simple_text_search(self, query: str, k: int) -> List[Dict[str, Any]]:
        """Simple text search fallback."""
        if self._data is None or "chunks" not in self._data:
            return []
        
        results = []
        query_lower = query.lower()
        
        for chunk in self._data["chunks"]:
            content = chunk.get("content", "").lower()
            score = 0.0
            
            # Simple scoring
            for term in query_lower.split():
                score += content.count(term) * 0.1
            
            if score > 0:
                results.append({
                    "content": chunk.get("content", ""),
                    "score": min(score, 1.0),
                    "metadata": chunk.get("metadata", {})
                })
        
        # Sort and return top k
        results.sort(key=lambda x: x["score"], reverse=True)
        return results[:k]