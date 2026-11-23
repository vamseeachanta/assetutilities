# ABOUTME: Embedding generation, context caching, and semantic search capabilities.
# ABOUTME: Extracted from context_optimization.py EmbeddingGenerator, ContextCache, SemanticSearch.
"""Embedding generation and semantic search for context optimization."""

import json
import hashlib
from datetime import datetime
from pathlib import Path
from typing import List, Dict, Any, Optional

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

