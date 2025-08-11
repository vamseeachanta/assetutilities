"""Main Web Contextualizer for Agent OS Module Agents."""

import json
import yaml
import hashlib
import mimetypes
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple
from dataclasses import dataclass, asdict
import logging

from .pdf_processor import PDFProcessor
from .resource_fetcher import ResourceFetcher
from .content_indexer import ContentIndexer

logger = logging.getLogger(__name__)

@dataclass
class WebResource:
    """Enhanced web resource with content management."""
    url: str
    type: str  # official_docs, api_reference, tutorial, standard, user_added
    title: str
    description: str
    content_type: Optional[str] = None  # pdf, html, json, markdown
    last_fetched: Optional[str] = None
    cache_file: Optional[str] = None
    text_file: Optional[str] = None  # Extracted text for PDFs
    indexed: bool = False
    refresh_interval: str = "7d"
    added_by: str = "system"
    notes: str = ""
    status: str = "pending"  # pending, fetched, processed, indexed, error
    error_message: Optional[str] = None
    file_size: Optional[int] = None
    checksum: Optional[str] = None
    metadata: Optional[Dict] = None

class WebContextualizer:
    """Manages complete web resource contextualization pipeline."""
    
    def __init__(self, agent_dir: Path, config: Optional[Dict] = None):
        """Initialize contextualizer with agent directory."""
        self.agent_dir = Path(agent_dir)
        self.web_dir = self.agent_dir / "context" / "external" / "web"
        self.web_dir.mkdir(parents=True, exist_ok=True)
        
        # Component directories
        self.cache_dir = self.web_dir / "cache"
        self.text_dir = self.web_dir / "extracted_text"
        self.index_dir = self.web_dir / "index"
        self.versions_dir = self.web_dir / "versions"
        
        for dir_path in [self.cache_dir, self.text_dir, self.index_dir, self.versions_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Configuration
        self.config_file = self.web_dir / "contextualization_config.yaml"
        self.resources_file = self.web_dir / "resources.json"
        self.config = config or self._load_config()
        
        # Initialize components
        self.fetcher = ResourceFetcher(self.cache_dir, self.versions_dir)
        self.pdf_processor = PDFProcessor(self.text_dir)
        self.indexer = ContentIndexer(self.index_dir)
        
        # Load existing resources
        self.resources = self._load_resources()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load or create configuration."""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f) or {}
        
        default_config = {
            "enabled": True,
            "auto_fetch": True,
            "auto_index": True,
            "pdf_extraction": True,
            "cache_settings": {
                "max_age_days": 7,
                "max_size_mb": 500,
                "version_control": True
            },
            "indexing": {
                "chunk_size": 1000,
                "overlap": 200,
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2"
            },
            "refresh_intervals": {
                "official_docs": "7d",
                "api_reference": "14d",
                "tutorial": "30d",
                "standard": "90d",
                "user_added": "manual"
            }
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False, indent=2)
        
        return default_config
    
    def _load_resources(self) -> Dict[str, WebResource]:
        """Load existing resources from file."""
        if self.resources_file.exists():
            with open(self.resources_file, 'r') as f:
                data = json.load(f)
                return {
                    url: WebResource(**resource_data)
                    for url, resource_data in data.items()
                }
        return {}
    
    def _save_resources(self):
        """Save resources to file."""
        data = {
            url: asdict(resource)
            for url, resource in self.resources.items()
        }
        with open(self.resources_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
    
    def add_resource(self, url: str, resource_type: str = "user_added",
                    title: str = "", description: str = "", notes: str = "",
                    auto_fetch: bool = True) -> WebResource:
        """Add a new web resource and optionally fetch it immediately."""
        # Check if already exists
        if url in self.resources:
            logger.info(f"Resource already exists: {url}")
            return self.resources[url]
        
        # Detect content type from URL
        content_type = self._detect_content_type(url)
        
        # Create resource
        resource = WebResource(
            url=url,
            type=resource_type,
            title=title or self._extract_title_from_url(url),
            description=description,
            content_type=content_type,
            notes=notes,
            added_by="user",
            refresh_interval=self.config["refresh_intervals"].get(
                resource_type, "7d"
            )
        )
        
        self.resources[url] = resource
        self._save_resources()
        
        # Auto-fetch if enabled
        if auto_fetch and self.config.get("auto_fetch", True):
            self.fetch_and_process(url)
        
        return resource
    
    def fetch_and_process(self, url: str) -> Tuple[bool, str]:
        """Fetch, cache, and process a web resource."""
        if url not in self.resources:
            return False, f"Resource not found: {url}"
        
        resource = self.resources[url]
        
        try:
            # Step 1: Fetch the resource
            logger.info(f"Fetching: {url}")
            cache_path, metadata = self.fetcher.fetch(
                url, 
                force=False,
                version_control=self.config["cache_settings"]["version_control"]
            )
            
            if not cache_path:
                raise Exception("Failed to fetch resource")
            
            # Update resource metadata
            resource.cache_file = str(cache_path.relative_to(self.web_dir))
            resource.last_fetched = datetime.now().isoformat()
            resource.file_size = cache_path.stat().st_size
            resource.checksum = self._calculate_checksum(cache_path)
            resource.metadata = metadata
            resource.status = "fetched"
            
            # Step 2: Process based on content type
            if resource.content_type == "pdf" and self.config.get("pdf_extraction", True):
                logger.info(f"Extracting PDF: {url}")
                text_path, pdf_metadata = self.pdf_processor.process_pdf(
                    cache_path,
                    extract_images=True,
                    extract_tables=True
                )
                
                if text_path:
                    resource.text_file = str(text_path.relative_to(self.web_dir))
                    resource.metadata.update(pdf_metadata)
                    resource.status = "processed"
            
            elif resource.content_type in ["html", "markdown", "text"]:
                # For text-based content, use cache directly
                resource.text_file = resource.cache_file
                resource.status = "processed"
            
            # Step 3: Index the content
            if self.config.get("auto_index", True) and resource.text_file:
                logger.info(f"Indexing: {url}")
                text_path = self.web_dir / resource.text_file
                
                if text_path.exists():
                    chunks = self.indexer.index_document(
                        text_path,
                        url,
                        metadata={
                            "title": resource.title,
                            "type": resource.type,
                            "description": resource.description
                        }
                    )
                    resource.indexed = True
                    resource.status = "indexed"
                    logger.info(f"Indexed {len(chunks)} chunks from {url}")
            
            self._save_resources()
            return True, f"Successfully processed: {url}"
            
        except Exception as e:
            logger.error(f"Error processing {url}: {str(e)}")
            resource.status = "error"
            resource.error_message = str(e)
            self._save_resources()
            return False, str(e)
    
    def fetch_all_pending(self) -> Dict[str, Tuple[bool, str]]:
        """Fetch all resources with pending status."""
        results = {}
        for url, resource in self.resources.items():
            if resource.status == "pending":
                success, message = self.fetch_and_process(url)
                results[url] = (success, message)
        return results
    
    def refresh_outdated(self, force: bool = False) -> Dict[str, Tuple[bool, str]]:
        """Refresh resources that need updating."""
        results = {}
        now = datetime.now()
        
        for url, resource in self.resources.items():
            if resource.status == "error" and not force:
                continue
            
            if resource.last_fetched:
                last_fetched = datetime.fromisoformat(resource.last_fetched)
                interval = self._parse_interval(resource.refresh_interval)
                
                if force or (now - last_fetched) > interval:
                    logger.info(f"Refreshing: {url}")
                    success, message = self.fetch_and_process(url)
                    results[url] = (success, message)
        
        return results
    
    def search(self, query: str, top_k: int = 5) -> List[Dict[str, Any]]:
        """Search indexed content for relevant information."""
        if not self.indexer.has_index():
            logger.warning("No index available for search")
            return []
        
        results = self.indexer.search(query, top_k)
        
        # Enhance results with resource metadata
        enhanced_results = []
        for result in results:
            url = result.get("source")
            if url in self.resources:
                resource = self.resources[url]
                result["resource_metadata"] = {
                    "title": resource.title,
                    "type": resource.type,
                    "description": resource.description,
                    "last_updated": resource.last_fetched
                }
            enhanced_results.append(result)
        
        return enhanced_results
    
    def get_context_for_query(self, query: str, max_tokens: int = 4000) -> str:
        """Get contextualized content for a query."""
        search_results = self.search(query, top_k=10)
        
        context_parts = []
        token_count = 0
        
        for result in search_results:
            text = result.get("text", "")
            metadata = result.get("resource_metadata", {})
            
            # Format context entry
            entry = f"[Source: {metadata.get('title', 'Unknown')}]\n{text}\n"
            entry_tokens = len(entry.split())  # Simple token estimation
            
            if token_count + entry_tokens <= max_tokens:
                context_parts.append(entry)
                token_count += entry_tokens
            else:
                break
        
        return "\n---\n".join(context_parts)
    
    def generate_status_report(self) -> str:
        """Generate comprehensive status report."""
        report = []
        report.append("# Web Resource Contextualization Status")
        report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Module: {self.agent_dir.name}\n")
        
        # Statistics
        total = len(self.resources)
        fetched = sum(1 for r in self.resources.values() if r.status == "fetched")
        processed = sum(1 for r in self.resources.values() if r.status == "processed")
        indexed = sum(1 for r in self.resources.values() if r.indexed)
        errors = sum(1 for r in self.resources.values() if r.status == "error")
        
        report.append("## Statistics")
        report.append(f"- Total Resources: {total}")
        report.append(f"- Fetched: {fetched}")
        report.append(f"- Processed: {processed}")
        report.append(f"- Indexed: {indexed}")
        report.append(f"- Errors: {errors}")
        
        # Cache size
        cache_size = sum(
            (self.web_dir / r.cache_file).stat().st_size
            for r in self.resources.values()
            if r.cache_file and (self.web_dir / r.cache_file).exists()
        ) / (1024 * 1024)  # Convert to MB
        
        report.append(f"- Cache Size: {cache_size:.2f} MB")
        
        # Resource details by type
        by_type = {}
        for resource in self.resources.values():
            by_type.setdefault(resource.type, []).append(resource)
        
        for res_type, resources in sorted(by_type.items()):
            report.append(f"\n## {res_type.title().replace('_', ' ')}")
            for resource in resources:
                status_icon = {
                    "indexed": "✅",
                    "processed": "📄",
                    "fetched": "💾",
                    "pending": "⏳",
                    "error": "❌"
                }.get(resource.status, "❓")
                
                report.append(f"- {status_icon} [{resource.title}]({resource.url})")
                if resource.notes:
                    report.append(f"  - Notes: {resource.notes}")
                if resource.status == "error":
                    report.append(f"  - Error: {resource.error_message}")
                if resource.indexed:
                    report.append(f"  - Indexed: Yes")
                if resource.last_fetched:
                    report.append(f"  - Last Updated: {resource.last_fetched}")
        
        return "\n".join(report)
    
    def _detect_content_type(self, url: str) -> str:
        """Detect content type from URL."""
        url_lower = url.lower()
        
        if url_lower.endswith('.pdf'):
            return "pdf"
        elif url_lower.endswith(('.html', '.htm')):
            return "html"
        elif url_lower.endswith('.md'):
            return "markdown"
        elif url_lower.endswith('.json'):
            return "json"
        elif url_lower.endswith(('.txt', '.text')):
            return "text"
        else:
            # Default to HTML for web pages
            return "html"
    
    def _extract_title_from_url(self, url: str) -> str:
        """Extract a reasonable title from URL."""
        from urllib.parse import urlparse
        parsed = urlparse(url)
        
        # Try to get filename
        path_parts = parsed.path.strip('/').split('/')
        if path_parts and path_parts[-1]:
            title = path_parts[-1]
            # Remove extension
            if '.' in title:
                title = title.rsplit('.', 1)[0]
            # Convert separators to spaces
            title = title.replace('-', ' ').replace('_', ' ')
            return title.title()
        
        # Fallback to domain
        return parsed.netloc.replace('www.', '').split('.')[0].title()
    
    def _calculate_checksum(self, file_path: Path) -> str:
        """Calculate SHA256 checksum of file."""
        sha256_hash = hashlib.sha256()
        with open(file_path, "rb") as f:
            for byte_block in iter(lambda: f.read(4096), b""):
                sha256_hash.update(byte_block)
        return sha256_hash.hexdigest()
    
    def _parse_interval(self, interval_str: str) -> timedelta:
        """Parse interval string to timedelta."""
        if interval_str == "manual":
            return timedelta(days=365 * 10)  # 10 years = effectively manual
        
        # Parse format like "7d", "2w", "1m"
        import re
        match = re.match(r'(\d+)([dwmDWM])', interval_str)
        if match:
            value = int(match.group(1))
            unit = match.group(2).lower()
            
            if unit == 'd':
                return timedelta(days=value)
            elif unit == 'w':
                return timedelta(weeks=value)
            elif unit == 'm':
                return timedelta(days=value * 30)
        
        # Default to 7 days
        return timedelta(days=7)