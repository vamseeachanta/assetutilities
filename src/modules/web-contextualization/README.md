# Web Contextualization Module

An enhanced web resource management system for Agent OS that provides comprehensive web resource fetching, caching, processing, and contextual search capabilities.

## Features

### Core Capabilities
- **Parallel Resource Fetching**: Fetch multiple web resources simultaneously with configurable worker pools
- **Intelligent Caching**: Automatic caching with version control and expiration management
- **PDF Processing**: Extract text, tables, and metadata from PDF documents
- **Content Indexing**: Semantic search using sentence transformers and keyword fallback
- **Dependency Management**: Handle resource dependencies automatically
- **Performance Monitoring**: Track metrics, success rates, and cache efficiency

### Enhanced Features (web_contextualizer_enhanced.py)
- **Batch Operations**: Add and process multiple resources efficiently
- **Priority-Based Processing**: Process high-priority resources first
- **Retry Logic**: Automatic retry with exponential backoff for failed fetches
- **Resource Tagging**: Organize resources with tags for better filtering
- **Cached Queries**: LRU cache for frequently used search queries
- **Advanced Filtering**: Search with type, tag, and priority filters
- **Comprehensive Reporting**: Detailed status reports with performance metrics

## Installation

The module dependencies are included in the main AssetUtilities package. Install using:

```bash
# Using pip
pip install -e .

# Using uv (recommended)
uv pip install -e .
```

## Usage

### Basic Usage

```python
from pathlib import Path
from web_contextualizer import WebContextualizer

# Initialize
agent_dir = Path("./my_agent")
contextualizer = WebContextualizer(agent_dir)

# Add a resource
resource = contextualizer.add_resource(
    url="https://example.com/document.pdf",
    resource_type="official_docs",
    title="Example Document",
    description="An example PDF document"
)

# Fetch and process
success, message = contextualizer.fetch_and_process(resource.url)

# Search
results = contextualizer.search("example query", top_k=5)

# Get context for RAG
context = contextualizer.get_context_for_query("How to do X?", max_tokens=4000)
```

### Enhanced Usage

```python
from web_contextualizer_enhanced import WebContextualizerEnhanced

# Initialize with parallel processing
contextualizer = WebContextualizerEnhanced(
    agent_dir=Path("./my_agent"),
    max_workers=4  # Use 4 parallel workers
)

# Add resources in batch
resources = [
    {"url": "https://example1.com", "type": "tutorial", "priority": 5},
    {"url": "https://example2.com", "type": "api_reference", "priority": 3}
]
contextualizer.add_resources_batch(resources)

# Fetch with priority threshold
results = contextualizer.fetch_resources_parallel(priority_threshold=3)

# Search with filters
results = contextualizer.search_enhanced(
    query="python async",
    top_k=5,
    filters={"type": "tutorial", "tags": ["python"]}
)

# Use cached queries for performance
context = contextualizer.get_context_for_query_cached(
    "common query",
    max_tokens=2000
)
```

## Configuration

The module creates a configuration file at `context/external/web/contextualization_config.yaml`:

```yaml
enabled: true
auto_fetch: true
auto_index: true
pdf_extraction: true
parallel_processing: true
max_parallel_fetches: 4

cache_settings:
  max_age_days: 7
  max_size_mb: 500
  version_control: true
  compression: false

indexing:
  chunk_size: 1000
  overlap: 200
  embedding_model: sentence-transformers/all-MiniLM-L6-v2
  batch_size: 32

refresh_intervals:
  official_docs: 7d
  api_reference: 14d
  tutorial: 30d
  standard: 90d
  user_added: manual

performance:
  request_timeout: 30
  max_retries: 3
  retry_delay: 5
  rate_limit: 10  # requests per minute

monitoring:
  log_level: INFO
  metrics_enabled: true
  alert_on_errors: true
```

## Resource Types

- `official_docs`: Official documentation (7-day refresh)
- `api_reference`: API references (14-day refresh)
- `tutorial`: Tutorials and guides (30-day refresh)
- `standard`: Standards and specifications (90-day refresh)
- `user_added`: User-added resources (manual refresh)

## Directory Structure

```
agent_dir/
└── context/
    └── external/
        └── web/
            ├── cache/                 # Cached web resources
            ├── extracted_text/        # Extracted text from PDFs
            ├── index/                 # Search index files
            ├── versions/              # Version history
            ├── metrics/               # Performance metrics
            ├── contextualization_config.yaml
            └── resources.json         # Resource metadata
```

## Performance Optimization

### Parallel Processing
- Configure `max_workers` for optimal performance based on your system
- Use batch operations for adding multiple resources
- Priority-based processing ensures important resources are fetched first

### Caching Strategy
- Automatic cache management with size and age limits
- Version control for tracking changes
- Cached search queries with LRU eviction

### Resource Management
- Automatic retry with exponential backoff
- Dependency resolution before processing
- Smart content type detection

## API Reference

### WebContextualizerEnhanced

#### Methods

- `add_resource(url, resource_type, title, description, priority, tags, dependencies)`: Add a single resource
- `add_resources_batch(resources, auto_fetch)`: Add multiple resources efficiently
- `fetch_resources_parallel(urls, priority_threshold)`: Fetch resources in parallel
- `fetch_and_process(url)`: Fetch and process a single resource
- `search_enhanced(query, top_k, filters)`: Search with advanced filtering
- `get_context_for_query(query, max_tokens, filters)`: Get contextual content
- `get_context_for_query_cached(query, max_tokens)`: Cached context retrieval
- `generate_enhanced_status_report()`: Generate comprehensive status report
- `cleanup()`: Clean up resources and save state

## Examples

See `example_usage.py` for comprehensive examples of all features.

## Performance Metrics

The module tracks:
- Total fetches and success rate
- Average fetch time
- Cache hit/miss ratio
- Processing time per resource
- Index size and search performance

Access metrics via the status report or directly from `metrics/performance_metrics.json`.

## Error Handling

- Automatic retry with configurable attempts
- Graceful degradation for missing dependencies
- Fallback search methods (keyword-based if embeddings unavailable)
- Comprehensive error logging and reporting

## Best Practices

1. **Use batch operations** for adding multiple resources
2. **Set appropriate priorities** for critical resources
3. **Configure refresh intervals** based on content volatility
4. **Monitor cache size** and adjust limits as needed
5. **Use filters** in search for better relevance
6. **Leverage cached queries** for frequently used searches
7. **Clean up old versions** periodically to save space

## Troubleshooting

### Common Issues

1. **PDF extraction fails**: Ensure at least one PDF library is installed (PyPDF2, pdfplumber, or PyMuPDF)
2. **Slow fetching**: Increase `max_workers` for more parallelism
3. **Out of memory**: Reduce `cache_settings.max_size_mb` or clean old cache
4. **Search not working**: Check if index exists and has been populated

### Debug Mode

Enable debug logging:

```python
import logging
logging.getLogger('web_contextualizer').setLevel(logging.DEBUG)
```

## License

Part of AssetUtilities - MIT License