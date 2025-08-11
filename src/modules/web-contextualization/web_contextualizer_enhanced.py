"""Enhanced Web Contextualizer with performance optimizations and better error handling."""

import asyncio
import json
import yaml
import hashlib
import mimetypes
from datetime import datetime, timedelta
from pathlib import Path
from typing import List, Dict, Any, Optional, Tuple, Union
from dataclasses import dataclass, asdict, field
import logging
from concurrent.futures import ThreadPoolExecutor, as_completed
import threading
from functools import lru_cache

try:
    from .pdf_processor import PDFProcessor
    from .resource_fetcher import ResourceFetcher
    from .content_indexer import ContentIndexer
except ImportError:
    # Handle absolute imports when module is run directly
    from pdf_processor import PDFProcessor
    from resource_fetcher import ResourceFetcher
    from content_indexer import ContentIndexer

logger = logging.getLogger(__name__)

@dataclass
class WebResourceEnhanced:
    """Enhanced web resource with additional features."""
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
    metadata: Optional[Dict] = field(default_factory=dict)
    priority: int = 0  # Higher priority resources fetched first
    retry_count: int = 0
    max_retries: int = 3
    tags: List[str] = field(default_factory=list)
    dependencies: List[str] = field(default_factory=list)  # URLs of dependent resources

class WebContextualizerEnhanced:
    """Enhanced web resource contextualization with parallel processing and caching."""
    
    def __init__(self, agent_dir: Path, config: Optional[Dict] = None, max_workers: int = 4):
        """Initialize enhanced contextualizer with parallel processing capabilities."""
        self.agent_dir = Path(agent_dir)
        self.web_dir = self.agent_dir / "context" / "external" / "web"
        self.web_dir.mkdir(parents=True, exist_ok=True)
        
        # Component directories
        self.cache_dir = self.web_dir / "cache"
        self.text_dir = self.web_dir / "extracted_text"
        self.index_dir = self.web_dir / "index"
        self.versions_dir = self.web_dir / "versions"
        self.metrics_dir = self.web_dir / "metrics"
        
        for dir_path in [self.cache_dir, self.text_dir, self.index_dir, 
                         self.versions_dir, self.metrics_dir]:
            dir_path.mkdir(exist_ok=True)
        
        # Configuration
        self.config_file = self.web_dir / "contextualization_config.yaml"
        self.resources_file = self.web_dir / "resources.json"
        self.metrics_file = self.metrics_dir / "performance_metrics.json"
        self.config = config or self._load_config()
        
        # Threading and parallel processing
        self.max_workers = max_workers
        self.executor = ThreadPoolExecutor(max_workers=max_workers)
        self.processing_lock = threading.Lock()
        self.resource_locks = {}  # Per-resource locks to prevent duplicate processing
        
        # Initialize components
        self.fetcher = ResourceFetcher(self.cache_dir, self.versions_dir)
        self.pdf_processor = PDFProcessor(self.text_dir)
        self.indexer = ContentIndexer(self.index_dir)
        
        # Load existing resources
        self.resources = self._load_resources()
        
        # Performance metrics
        self.metrics = self._load_metrics()
    
    def _load_config(self) -> Dict[str, Any]:
        """Load or create enhanced configuration."""
        if self.config_file.exists():
            with open(self.config_file, 'r') as f:
                return yaml.safe_load(f) or {}
        
        default_config = {
            "enabled": True,
            "auto_fetch": True,
            "auto_index": True,
            "pdf_extraction": True,
            "parallel_processing": True,
            "max_parallel_fetches": 4,
            "cache_settings": {
                "max_age_days": 7,
                "max_size_mb": 500,
                "version_control": True,
                "compression": False
            },
            "indexing": {
                "chunk_size": 1000,
                "overlap": 200,
                "embedding_model": "sentence-transformers/all-MiniLM-L6-v2",
                "batch_size": 32
            },
            "refresh_intervals": {
                "official_docs": "7d",
                "api_reference": "14d",
                "tutorial": "30d",
                "standard": "90d",
                "user_added": "manual"
            },
            "performance": {
                "request_timeout": 30,
                "max_retries": 3,
                "retry_delay": 5,
                "rate_limit": 10  # requests per minute
            },
            "monitoring": {
                "log_level": "INFO",
                "metrics_enabled": True,
                "alert_on_errors": True
            }
        }
        
        with open(self.config_file, 'w') as f:
            yaml.dump(default_config, f, default_flow_style=False, indent=2)
        
        return default_config
    
    def _load_resources(self) -> Dict[str, WebResourceEnhanced]:
        """Load existing resources from file with migration support."""
        if self.resources_file.exists():
            with open(self.resources_file, 'r') as f:
                data = json.load(f)
                resources = {}
                for url, resource_data in data.items():
                    # Handle migration from old format
                    if 'priority' not in resource_data:
                        resource_data['priority'] = 0
                    if 'retry_count' not in resource_data:
                        resource_data['retry_count'] = 0
                    if 'max_retries' not in resource_data:
                        resource_data['max_retries'] = 3
                    if 'tags' not in resource_data:
                        resource_data['tags'] = []
                    if 'dependencies' not in resource_data:
                        resource_data['dependencies'] = []
                    if 'metadata' not in resource_data:
                        resource_data['metadata'] = {}
                    
                    resources[url] = WebResourceEnhanced(**resource_data)
                return resources
        return {}
    
    def _save_resources(self):
        """Save resources to file with atomic write."""
        temp_file = self.resources_file.with_suffix('.tmp')
        data = {
            url: asdict(resource)
            for url, resource in self.resources.items()
        }
        with open(temp_file, 'w') as f:
            json.dump(data, f, indent=2, default=str)
        
        # Atomic rename
        temp_file.replace(self.resources_file)
    
    def _load_metrics(self) -> Dict[str, Any]:
        """Load performance metrics."""
        if self.metrics_file.exists():
            with open(self.metrics_file, 'r') as f:
                return json.load(f)
        return {
            "total_fetches": 0,
            "successful_fetches": 0,
            "failed_fetches": 0,
            "total_processing_time": 0,
            "average_fetch_time": 0,
            "cache_hits": 0,
            "cache_misses": 0
        }
    
    def _save_metrics(self):
        """Save performance metrics."""
        with open(self.metrics_file, 'w') as f:
            json.dump(self.metrics, f, indent=2)
    
    def add_resources_batch(self, resources: List[Dict[str, Any]], 
                           auto_fetch: bool = True) -> List[WebResourceEnhanced]:
        """Add multiple resources in batch."""
        added_resources = []
        
        for resource_data in resources:
            resource = self.add_resource(
                url=resource_data['url'],
                resource_type=resource_data.get('type', 'user_added'),
                title=resource_data.get('title', ''),
                description=resource_data.get('description', ''),
                notes=resource_data.get('notes', ''),
                priority=resource_data.get('priority', 0),
                tags=resource_data.get('tags', []),
                dependencies=resource_data.get('dependencies', []),
                auto_fetch=False  # We'll fetch in parallel later
            )
            added_resources.append(resource)
        
        if auto_fetch and self.config.get("auto_fetch", True):
            self.fetch_resources_parallel(
                [r.url for r in added_resources]
            )
        
        return added_resources
    
    def add_resource(self, url: str, resource_type: str = "user_added",
                    title: str = "", description: str = "", notes: str = "",
                    priority: int = 0, tags: List[str] = None, 
                    dependencies: List[str] = None,
                    auto_fetch: bool = True) -> WebResourceEnhanced:
        """Add a new web resource with enhanced metadata."""
        # Check if already exists
        if url in self.resources:
            logger.info(f"Resource already exists: {url}")
            return self.resources[url]
        
        # Detect content type from URL
        content_type = self._detect_content_type(url)
        
        # Create resource
        resource = WebResourceEnhanced(
            url=url,
            type=resource_type,
            title=title or self._extract_title_from_url(url),
            description=description,
            content_type=content_type,
            notes=notes,
            added_by="user",
            refresh_interval=self.config["refresh_intervals"].get(
                resource_type, "7d"
            ),
            priority=priority,
            tags=tags or [],
            dependencies=dependencies or []
        )
        
        # Create per-resource lock
        self.resource_locks[url] = threading.Lock()
        
        self.resources[url] = resource
        self._save_resources()
        
        # Auto-fetch if enabled
        if auto_fetch and self.config.get("auto_fetch", True):
            self.executor.submit(self.fetch_and_process, url)
        
        return resource
    
    def fetch_resources_parallel(self, urls: List[str] = None, 
                                priority_threshold: int = None) -> Dict[str, Tuple[bool, str]]:
        """Fetch multiple resources in parallel."""
        if urls is None:
            # Get all pending resources
            urls = [
                url for url, resource in self.resources.items()
                if resource.status == "pending" and 
                (priority_threshold is None or resource.priority >= priority_threshold)
            ]
        
        # Sort by priority
        urls.sort(key=lambda u: self.resources[u].priority, reverse=True)
        
        results = {}
        futures = []
        
        # Limit parallel fetches
        max_parallel = self.config.get("max_parallel_fetches", 4)
        
        with ThreadPoolExecutor(max_workers=max_parallel) as executor:
            for url in urls:
                future = executor.submit(self.fetch_and_process, url)
                futures.append((url, future))
            
            for url, future in futures:
                try:
                    success, message = future.result(timeout=60)
                    results[url] = (success, message)
                except Exception as e:
                    logger.error(f"Parallel fetch failed for {url}: {e}")
                    results[url] = (False, str(e))
        
        return results
    
    def fetch_and_process(self, url: str) -> Tuple[bool, str]:
        """Enhanced fetch and process with retry logic and dependency handling."""
        if url not in self.resources:
            return False, f"Resource not found: {url}"
        
        resource = self.resources[url]
        
        # Use per-resource lock to prevent duplicate processing
        lock = self.resource_locks.get(url, threading.Lock())
        
        if not lock.acquire(blocking=False):
            return False, f"Resource already being processed: {url}"
        
        try:
            # Check dependencies first
            for dep_url in resource.dependencies:
                if dep_url in self.resources:
                    dep_resource = self.resources[dep_url]
                    if dep_resource.status not in ["fetched", "processed", "indexed"]:
                        logger.info(f"Fetching dependency first: {dep_url}")
                        self.fetch_and_process(dep_url)
            
            # Record start time for metrics
            start_time = datetime.now()
            
            # Step 1: Fetch the resource with retry logic
            logger.info(f"Fetching: {url}")
            
            max_retries = resource.max_retries
            retry_delay = self.config["performance"]["retry_delay"]
            
            for attempt in range(max_retries):
                try:
                    cache_path, metadata = self.fetcher.fetch(
                        url, 
                        force=False,
                        version_control=self.config["cache_settings"]["version_control"]
                    )
                    
                    if cache_path:
                        break
                    
                except Exception as e:
                    resource.retry_count = attempt + 1
                    if attempt < max_retries - 1:
                        logger.warning(f"Fetch attempt {attempt + 1} failed for {url}, retrying...")
                        asyncio.sleep(retry_delay)
                    else:
                        raise e
            
            if not cache_path:
                raise Exception("Failed to fetch resource after all retries")
            
            # Update resource metadata
            resource.cache_file = str(cache_path.relative_to(self.web_dir))
            resource.last_fetched = datetime.now().isoformat()
            resource.file_size = cache_path.stat().st_size
            resource.checksum = self._calculate_checksum(cache_path)
            resource.metadata = metadata
            resource.status = "fetched"
            
            # Update metrics
            fetch_time = (datetime.now() - start_time).total_seconds()
            self.metrics["total_fetches"] += 1
            self.metrics["successful_fetches"] += 1
            self.metrics["total_processing_time"] += fetch_time
            self.metrics["average_fetch_time"] = (
                self.metrics["total_processing_time"] / self.metrics["total_fetches"]
            )
            
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
                            "description": resource.description,
                            "tags": resource.tags
                        }
                    )
                    resource.indexed = True
                    resource.status = "indexed"
                    logger.info(f"Indexed {len(chunks)} chunks from {url}")
            
            self._save_resources()
            self._save_metrics()
            
            return True, f"Successfully processed: {url}"
            
        except Exception as e:
            logger.error(f"Error processing {url}: {str(e)}")
            resource.status = "error"
            resource.error_message = str(e)
            self.metrics["failed_fetches"] += 1
            self._save_resources()
            self._save_metrics()
            return False, str(e)
        
        finally:
            lock.release()
    
    def search_enhanced(self, query: str, top_k: int = 5, 
                       filters: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """Enhanced search with filtering and ranking."""
        if not self.indexer.has_index():
            logger.warning("No index available for search")
            return []
        
        results = self.indexer.search(query, top_k * 2)  # Get more results for filtering
        
        # Enhance and filter results
        enhanced_results = []
        for result in results:
            url = result.get("source")
            if url in self.resources:
                resource = self.resources[url]
                
                # Apply filters
                if filters:
                    if "type" in filters and resource.type != filters["type"]:
                        continue
                    if "tags" in filters:
                        filter_tags = set(filters["tags"])
                        resource_tags = set(resource.tags)
                        if not filter_tags.intersection(resource_tags):
                            continue
                
                # Enhance result with metadata
                result["resource_metadata"] = {
                    "title": resource.title,
                    "type": resource.type,
                    "description": resource.description,
                    "last_updated": resource.last_fetched,
                    "tags": resource.tags,
                    "priority": resource.priority
                }
                
                # Boost score based on resource priority
                result["score"] = result.get("score", 0) * (1 + resource.priority * 0.1)
                
                enhanced_results.append(result)
        
        # Sort by enhanced score and return top k
        enhanced_results.sort(key=lambda x: x["score"], reverse=True)
        return enhanced_results[:top_k]
    
    @lru_cache(maxsize=128)
    def get_context_for_query_cached(self, query: str, max_tokens: int = 4000) -> str:
        """Cached version of context retrieval for frequently used queries."""
        return self.get_context_for_query(query, max_tokens)
    
    def get_context_for_query(self, query: str, max_tokens: int = 4000,
                             filters: Optional[Dict[str, Any]] = None) -> str:
        """Get contextualized content for a query with filtering."""
        search_results = self.search_enhanced(query, top_k=10, filters=filters)
        
        context_parts = []
        token_count = 0
        
        for result in search_results:
            text = result.get("text", "")
            metadata = result.get("resource_metadata", {})
            
            # Format context entry with tags
            tags_str = ", ".join(metadata.get("tags", []))
            entry = f"[Source: {metadata.get('title', 'Unknown')} | Type: {metadata.get('type', '')} | Tags: {tags_str}]\n{text}\n"
            entry_tokens = len(entry.split())  # Simple token estimation
            
            if token_count + entry_tokens <= max_tokens:
                context_parts.append(entry)
                token_count += entry_tokens
            else:
                break
        
        return "\n---\n".join(context_parts)
    
    def generate_enhanced_status_report(self) -> str:
        """Generate comprehensive status report with metrics."""
        report = []
        report.append("# Web Resource Contextualization Status Report")
        report.append(f"\nGenerated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}")
        report.append(f"Module: {self.agent_dir.name}\n")
        
        # Statistics
        total = len(self.resources)
        fetched = sum(1 for r in self.resources.values() if r.status == "fetched")
        processed = sum(1 for r in self.resources.values() if r.status == "processed")
        indexed = sum(1 for r in self.resources.values() if r.indexed)
        errors = sum(1 for r in self.resources.values() if r.status == "error")
        pending = sum(1 for r in self.resources.values() if r.status == "pending")
        
        report.append("## Statistics")
        report.append(f"- Total Resources: {total}")
        report.append(f"- Pending: {pending}")
        report.append(f"- Fetched: {fetched}")
        report.append(f"- Processed: {processed}")
        report.append(f"- Indexed: {indexed}")
        report.append(f"- Errors: {errors}")
        
        # Performance Metrics
        report.append("\n## Performance Metrics")
        report.append(f"- Total Fetches: {self.metrics.get('total_fetches', 0)}")
        report.append(f"- Success Rate: {self.metrics.get('successful_fetches', 0) / max(self.metrics.get('total_fetches', 1), 1) * 100:.1f}%")
        report.append(f"- Average Fetch Time: {self.metrics.get('average_fetch_time', 0):.2f}s")
        report.append(f"- Cache Hits: {self.metrics.get('cache_hits', 0)}")
        report.append(f"- Cache Misses: {self.metrics.get('cache_misses', 0)}")
        
        # Cache size
        cache_size = sum(
            (self.web_dir / r.cache_file).stat().st_size
            for r in self.resources.values()
            if r.cache_file and (self.web_dir / r.cache_file).exists()
        ) / (1024 * 1024)  # Convert to MB
        
        report.append(f"- Cache Size: {cache_size:.2f} MB")
        report.append(f"- Cache Limit: {self.config['cache_settings']['max_size_mb']} MB")
        
        # Resource details by type and priority
        by_type = {}
        high_priority = []
        
        for resource in self.resources.values():
            by_type.setdefault(resource.type, []).append(resource)
            if resource.priority >= 5:
                high_priority.append(resource)
        
        if high_priority:
            report.append(f"\n## High Priority Resources ({len(high_priority)})")
            for resource in sorted(high_priority, key=lambda r: r.priority, reverse=True):
                status_icon = {
                    "indexed": "✅",
                    "processed": "📄",
                    "fetched": "💾",
                    "pending": "⏳",
                    "error": "❌"
                }.get(resource.status, "❓")
                
                report.append(f"- {status_icon} [{resource.title}]({resource.url}) [Priority: {resource.priority}]")
                if resource.tags:
                    report.append(f"  - Tags: {', '.join(resource.tags)}")
        
        for res_type, resources in sorted(by_type.items()):
            report.append(f"\n## {res_type.title().replace('_', ' ')} ({len(resources)})")
            for resource in resources[:10]:  # Limit to 10 per type
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
                    report.append(f"  - Retries: {resource.retry_count}/{resource.max_retries}")
        
        # Recent errors
        recent_errors = [
            r for r in self.resources.values() 
            if r.status == "error" and r.last_fetched
        ]
        if recent_errors:
            report.append("\n## Recent Errors")
            for resource in sorted(recent_errors, 
                                 key=lambda r: r.last_fetched or "", 
                                 reverse=True)[:5]:
                report.append(f"- [{resource.title}]({resource.url})")
                report.append(f"  - Error: {resource.error_message}")
                report.append(f"  - Last Attempt: {resource.last_fetched}")
        
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
    
    def cleanup(self):
        """Clean up resources and save state."""
        self._save_resources()
        self._save_metrics()
        self.executor.shutdown(wait=True)
        logger.info("WebContextualizerEnhanced cleanup completed")