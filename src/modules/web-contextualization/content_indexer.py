"""Content Indexer Module for Web Contextualization."""

import json
import logging
import pickle
from pathlib import Path
from typing import List, Dict, Any, Optional
import hashlib
from datetime import datetime

logger = logging.getLogger(__name__)

class ContentIndexer:
    """Index and search document content for RAG."""
    
    def __init__(self, index_dir: Path):
        """Initialize indexer with index directory."""
        self.index_dir = Path(index_dir)
        self.index_dir.mkdir(parents=True, exist_ok=True)
        
        self.index_file = self.index_dir / "content_index.json"
        self.chunks_file = self.index_dir / "chunks.json"
        self.embeddings_file = self.index_dir / "embeddings.pkl"
        
        # Check for embedding libraries
        self.has_sentence_transformers = False
        self.has_openai = False
        
        try:
            from sentence_transformers import SentenceTransformer
            self.has_sentence_transformers = True
            self.model = SentenceTransformer('all-MiniLM-L6-v2')
            logger.info("Sentence Transformers available for embeddings")
        except ImportError:
            self.model = None
        
        # Load existing index
        self.index = self._load_index()
        self.chunks = self._load_chunks()
    
    def _load_index(self) -> Dict[str, Any]:
        """Load existing index from file."""
        if self.index_file.exists():
            with open(self.index_file, 'r') as f:
                return json.load(f)
        return {
            "documents": {},
            "statistics": {
                "total_documents": 0,
                "total_chunks": 0,
                "total_tokens": 0
            }
        }
    
    def _load_chunks(self) -> List[Dict[str, Any]]:
        """Load existing chunks from file."""
        if self.chunks_file.exists():
            with open(self.chunks_file, 'r') as f:
                return json.load(f)
        return []
    
    def _save_index(self):
        """Save index to file."""
        with open(self.index_file, 'w') as f:
            json.dump(self.index, f, indent=2)
    
    def _save_chunks(self):
        """Save chunks to file."""
        with open(self.chunks_file, 'w') as f:
            json.dump(self.chunks, f, indent=2)
    
    def index_document(self, text_path: Path, source_url: str,
                      metadata: Optional[Dict] = None,
                      chunk_size: int = 1000,
                      overlap: int = 200) -> List[Dict[str, Any]]:
        """Index a document by chunking and optionally creating embeddings."""
        text_path = Path(text_path)
        
        if not text_path.exists():
            logger.error(f"Text file not found: {text_path}")
            return []
        
        # Read document content
        with open(text_path, 'r', encoding='utf-8', errors='ignore') as f:
            content = f.read()
        
        # Create document ID
        doc_id = hashlib.md5(source_url.encode()).hexdigest()
        
        # Chunk the document
        chunks = self._chunk_text(content, chunk_size, overlap)
        
        # Create chunk records
        chunk_records = []
        for i, chunk_text in enumerate(chunks):
            chunk_record = {
                "id": f"{doc_id}_{i}",
                "doc_id": doc_id,
                "source": source_url,
                "chunk_index": i,
                "text": chunk_text,
                "tokens": len(chunk_text.split()),
                "metadata": metadata or {}
            }
            
            # Create embedding if available
            if self.has_sentence_transformers and self.model:
                embedding = self.model.encode(chunk_text).tolist()
                chunk_record["embedding"] = embedding
            
            chunk_records.append(chunk_record)
            self.chunks.append(chunk_record)
        
        # Update index
        self.index["documents"][doc_id] = {
            "source": source_url,
            "path": str(text_path),
            "chunks": len(chunks),
            "total_tokens": sum(c["tokens"] for c in chunk_records),
            "metadata": metadata or {},
            "indexed_at": datetime.now().isoformat()
        }
        
        self.index["statistics"]["total_documents"] += 1
        self.index["statistics"]["total_chunks"] += len(chunks)
        self.index["statistics"]["total_tokens"] += sum(c["tokens"] for c in chunk_records)
        
        # Save updated index and chunks
        self._save_index()
        self._save_chunks()
        
        # Save embeddings if created
        if self.has_sentence_transformers:
            self._save_embeddings()
        
        logger.info(f"Indexed {len(chunks)} chunks from {source_url}")
        return chunk_records
    
    def _chunk_text(self, text: str, chunk_size: int = 1000,
                   overlap: int = 200) -> List[str]:
        """Chunk text into overlapping segments."""
        # Split by paragraphs first
        paragraphs = text.split('\n\n')
        
        chunks = []
        current_chunk = []
        current_size = 0
        
        for para in paragraphs:
            para_words = para.split()
            para_size = len(para_words)
            
            if current_size + para_size <= chunk_size:
                # Add to current chunk
                current_chunk.extend(para_words)
                current_size += para_size
            else:
                # Save current chunk and start new one
                if current_chunk:
                    chunks.append(' '.join(current_chunk))
                
                # Handle large paragraphs
                if para_size > chunk_size:
                    # Split large paragraph
                    for i in range(0, para_size, chunk_size - overlap):
                        chunk_words = para_words[i:i + chunk_size]
                        chunks.append(' '.join(chunk_words))
                    current_chunk = para_words[-(overlap):]
                    current_size = len(current_chunk)
                else:
                    # Start new chunk with overlap
                    if chunks and overlap > 0:
                        # Get last words from previous chunk
                        prev_words = chunks[-1].split()[-overlap:]
                        current_chunk = prev_words + para_words
                        current_size = len(current_chunk)
                    else:
                        current_chunk = para_words
                        current_size = para_size
        
        # Add final chunk
        if current_chunk:
            chunks.append(' '.join(current_chunk))
        
        return chunks
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search indexed content for relevant chunks."""
        if not self.chunks:
            logger.warning("No chunks indexed for search")
            return []
        
        results = []
        
        if self.has_sentence_transformers and self.model:
            # Semantic search using embeddings
            results = self._semantic_search(query, top_k)
        else:
            # Fallback to keyword search
            results = self._keyword_search(query, top_k)
        
        return results
    
    def _semantic_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Search using semantic similarity with embeddings."""
        try:
            import numpy as np
            
            # Encode query
            query_embedding = self.model.encode(query)
            
            # Calculate similarities
            similarities = []
            for chunk in self.chunks:
                if "embedding" in chunk:
                    chunk_embedding = np.array(chunk["embedding"])
                    # Cosine similarity
                    similarity = np.dot(query_embedding, chunk_embedding) / (
                        np.linalg.norm(query_embedding) * np.linalg.norm(chunk_embedding)
                    )
                    similarities.append({
                        "chunk": chunk,
                        "score": float(similarity)
                    })
            
            # Sort by similarity
            similarities.sort(key=lambda x: x["score"], reverse=True)
            
            # Return top results
            results = []
            for item in similarities[:top_k]:
                result = {
                    "text": item["chunk"]["text"],
                    "source": item["chunk"]["source"],
                    "score": item["score"],
                    "chunk_id": item["chunk"]["id"],
                    "metadata": item["chunk"].get("metadata", {})
                }
                results.append(result)
            
            return results
            
        except Exception as e:
            logger.error(f"Semantic search failed: {e}")
            return self._keyword_search(query, top_k)
    
    def _keyword_search(self, query: str, top_k: int) -> List[Dict[str, Any]]:
        """Fallback keyword-based search."""
        query_words = set(query.lower().split())
        
        scores = []
        for chunk in self.chunks:
            chunk_text_lower = chunk["text"].lower()
            chunk_words = set(chunk_text_lower.split())
            
            # Calculate overlap
            overlap = len(query_words & chunk_words)
            
            # Boost if exact phrase appears
            exact_match_boost = 5 if query.lower() in chunk_text_lower else 0
            
            score = overlap + exact_match_boost
            
            if score > 0:
                scores.append({
                    "chunk": chunk,
                    "score": score
                })
        
        # Sort by score
        scores.sort(key=lambda x: x["score"], reverse=True)
        
        # Return top results
        results = []
        for item in scores[:top_k]:
            result = {
                "text": item["chunk"]["text"],
                "source": item["chunk"]["source"],
                "score": item["score"],
                "chunk_id": item["chunk"]["id"],
                "metadata": item["chunk"].get("metadata", {})
            }
            results.append(result)
        
        return results
    
    def _save_embeddings(self):
        """Save embeddings to file."""
        embeddings = {}
        for chunk in self.chunks:
            if "embedding" in chunk:
                embeddings[chunk["id"]] = chunk["embedding"]
        
        with open(self.embeddings_file, 'wb') as f:
            pickle.dump(embeddings, f)
    
    def has_index(self) -> bool:
        """Check if index exists and has content."""
        return len(self.chunks) > 0
    
    def clear_index(self):
        """Clear all indexed content."""
        self.index = {
            "documents": {},
            "statistics": {
                "total_documents": 0,
                "total_chunks": 0,
                "total_tokens": 0
            }
        }
        self.chunks = []
        
        # Remove files
        for file_path in [self.index_file, self.chunks_file, self.embeddings_file]:
            if file_path.exists():
                file_path.unlink()
        
        logger.info("Index cleared")
    
    def get_statistics(self) -> Dict[str, Any]:
        """Get indexing statistics."""
        return self.index.get("statistics", {})

