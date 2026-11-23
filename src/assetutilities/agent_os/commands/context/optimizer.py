# ABOUTME: Top-level optimized context manager with caching and search.
# ABOUTME: Extracted from context_optimization.py OptimizedContext class.
"""Manages optimized context with caching and search capabilities."""

from pathlib import Path
from typing import List, Dict, Any, Optional

from assetutilities.agent_os.commands.context.embedding import (
    ContextCache,
    EmbeddingGenerator,
    SemanticSearch,
)
from assetutilities.agent_os.commands.context.processor import ContextProcessor

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
