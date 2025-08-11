#!/usr/bin/env python
"""Example usage of the enhanced Web Contextualization module."""

from pathlib import Path
from web_contextualizer_enhanced import WebContextualizerEnhanced

def main():
    """Demonstrate the enhanced web contextualization features."""
    
    # Initialize the contextualizer
    agent_dir = Path("./agent_example")
    contextualizer = WebContextualizerEnhanced(
        agent_dir=agent_dir,
        max_workers=4  # Use 4 parallel workers
    )
    
    # Example 1: Add a single resource
    print("Adding a single resource...")
    resource = contextualizer.add_resource(
        url="https://docs.python.org/3/tutorial/index.html",
        resource_type="official_docs",
        title="Python Tutorial",
        description="Official Python tutorial documentation",
        priority=5,  # High priority
        tags=["python", "tutorial", "documentation"],
        auto_fetch=True
    )
    print(f"Added resource: {resource.title}")
    
    # Example 2: Add multiple resources in batch
    print("\nAdding multiple resources in batch...")
    batch_resources = [
        {
            "url": "https://docs.python.org/3/library/asyncio.html",
            "type": "api_reference",
            "title": "AsyncIO Documentation",
            "priority": 4,
            "tags": ["python", "asyncio", "concurrency"]
        },
        {
            "url": "https://realpython.com/python-concurrency/",
            "type": "tutorial",
            "title": "Python Concurrency Guide",
            "priority": 3,
            "tags": ["python", "concurrency", "tutorial"]
        },
        {
            "url": "https://peps.python.org/pep-0008/",
            "type": "standard",
            "title": "PEP 8 Style Guide",
            "priority": 5,
            "tags": ["python", "style", "standards"]
        }
    ]
    
    added = contextualizer.add_resources_batch(batch_resources)
    print(f"Added {len(added)} resources in batch")
    
    # Example 3: Fetch all pending resources in parallel
    print("\nFetching resources in parallel...")
    results = contextualizer.fetch_resources_parallel()
    
    for url, (success, message) in results.items():
        status = "✅" if success else "❌"
        print(f"{status} {url}: {message}")
    
    # Example 4: Search with filters
    print("\nSearching for Python concurrency information...")
    search_results = contextualizer.search_enhanced(
        query="python asyncio concurrent programming",
        top_k=3,
        filters={"tags": ["python", "concurrency"]}
    )
    
    for i, result in enumerate(search_results, 1):
        metadata = result.get("resource_metadata", {})
        print(f"{i}. {metadata.get('title')} (Score: {result.get('score', 0):.2f})")
        print(f"   Tags: {', '.join(metadata.get('tags', []))}")
        print(f"   {result.get('text', '')[:100]}...")
    
    # Example 5: Get contextualized content for a query
    print("\nGetting context for asyncio query...")
    context = contextualizer.get_context_for_query(
        query="How to use asyncio in Python?",
        max_tokens=500,
        filters={"type": "official_docs"}
    )
    print(f"Context (first 200 chars): {context[:200]}...")
    
    # Example 6: Generate status report
    print("\nGenerating status report...")
    report = contextualizer.generate_enhanced_status_report()
    print(report[:500] + "...")  # Print first 500 chars
    
    # Example 7: Using cached context retrieval
    print("\nUsing cached context retrieval...")
    # First call will compute and cache
    context1 = contextualizer.get_context_for_query_cached(
        "Python best practices",
        max_tokens=300
    )
    
    # Second call will use cache (much faster)
    context2 = contextualizer.get_context_for_query_cached(
        "Python best practices",
        max_tokens=300
    )
    
    print("Cached retrieval successful:", context1 == context2)
    
    # Example 8: Resource with dependencies
    print("\nAdding resource with dependencies...")
    main_resource = contextualizer.add_resource(
        url="https://example.com/advanced-python-guide.pdf",
        resource_type="tutorial",
        title="Advanced Python Guide",
        description="Comprehensive guide to advanced Python features",
        priority=4,
        tags=["python", "advanced"],
        dependencies=[
            "https://docs.python.org/3/tutorial/index.html",  # Depends on basic tutorial
            "https://peps.python.org/pep-0008/"  # Depends on style guide
        ],
        auto_fetch=True
    )
    print(f"Added resource with {len(main_resource.dependencies)} dependencies")
    
    # Cleanup
    contextualizer.cleanup()
    print("\nExample completed successfully!")

if __name__ == "__main__":
    main()