"""Web Resource Contextualization Module for Agent OS.

This module provides comprehensive web resource management including:
- URL fetching and caching
- PDF processing and extraction
- Content indexing and search
- Automatic refresh and versioning
"""

from .web_contextualizer import WebContextualizer
from .pdf_processor import PDFProcessor
from .content_indexer import ContentIndexer
from .resource_fetcher import ResourceFetcher

__version__ = "1.0.0"
__all__ = [
    "WebContextualizer",
    "PDFProcessor", 
    "ContentIndexer",
    "ResourceFetcher"
]