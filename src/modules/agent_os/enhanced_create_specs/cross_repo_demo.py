#!/usr/bin/env python3
"""
Cross-Repository Integration Demo

This script demonstrates the complete cross-repository integration functionality
including reference parsing, submodule management, and resolution.

Usage:
    python cross_repo_demo.py
"""

import asyncio

# Import cross-repository components
from cross_repository_integration import (
    CrossRepositoryManager,
    GitSubmoduleIntegration,
    ReferenceResolver,
    VersionCompatibilityChecker,
    ComponentCacheManager,
    OfflineFallbackManager
)

from git_submodule_setup import GitSubmoduleSetupManager


async def main():
    """Main demo function"""
    print("🚀 Cross-Repository Integration Demo")
    print("=" * 50)
    
    # 1. Initialize managers
    print("\n1️⃣ Initializing cross-repository managers...")
    
    cross_repo_manager = CrossRepositoryManager()
    GitSubmoduleIntegration()
    reference_resolver = ReferenceResolver()
    version_checker = VersionCompatibilityChecker()
    cache_manager = ComponentCacheManager()
    fallback_manager = OfflineFallbackManager()
    setup_manager = GitSubmoduleSetupManager()
    
    print("✓ All managers initialized successfully")
    
    # 2. Test reference parsing
    print("\n2️⃣ Testing cross-repository reference parsing...")
    
    test_references = [
        "@github:assetutilities/README.md",
        "@github:assetutilities@main/src/modules/agent-os/enhanced-create-specs/workflow.md",
        "@github:shared-templates/base.yml",
        "invalid-reference"
    ]
    
    for ref in test_references:
        parsed = cross_repo_manager.parse_reference(ref)
        status = "✓ Valid" if parsed.valid else "✗ Invalid"
        print(f"   {status}: {ref}")
        if not parsed.valid:
            print(f"      Error: {parsed.error}")
    
    # 3. Check git submodule status
    print("\n3️⃣ Checking git submodule status...")
    
    status = setup_manager.get_status()
    
    if status['cross_repo_ready']:
        print("✓ Cross-repository setup is ready")
        print(f"   Ready submodules: {status['ready_submodules']}/{status['total_enabled_submodules']}")
        
        for name, info in status['submodules'].items():
            if info['exists']:
                print(f"   ✓ {name}: {info['status']}")
            else:
                print(f"   - {name}: not found")
    else:
        print("⚠ Cross-repository setup needs configuration")
        for rec in status.get('recommendations', []):
            print(f"   💡 {rec}")
    
    # 4. Test version compatibility
    print("\n4️⃣ Testing version compatibility checking...")
    
    compatibility_rules = {
        'enhanced-create-specs': {
            'min_version': '1.0.0',
            'max_version': '3.0.0'
        }
    }
    
    test_versions = [
        ('enhanced-create-specs', '1.5.0', True),
        ('enhanced-create-specs', '0.9.0', False),
        ('enhanced-create-specs', '3.5.0', False),
        ('unknown-component', '1.0.0', True)  # No rules = compatible
    ]
    
    for component, version, expected in test_versions:
        compatible = version_checker.is_compatible(component, version, compatibility_rules)
        status = "✓" if compatible == expected else "✗"
        print(f"   {status} {component} v{version}: {'Compatible' if compatible else 'Incompatible'}")
    
    # 5. Test reference resolution (if submodules are available)
    print("\n5️⃣ Testing reference resolution...")
    
    if status['cross_repo_ready']:
        test_ref = "@github:assetutilities/README.md"
        try:
            result = await reference_resolver.resolve_reference(test_ref, use_cache=True)
            
            if result['success']:
                content_preview = result['content'][:100] + "..." if len(result['content']) > 100 else result['content']
                print(f"✓ Resolved {test_ref}")
                print(f"   Path: {result['resolved_path']}")
                print(f"   Content preview: {content_preview}")
            else:
                print(f"✗ Failed to resolve {test_ref}: {result['error']}")
        
        except Exception as e:
            print(f"✗ Resolution error: {e}")
    else:
        print("⚠ Skipping resolution test - submodules not ready")
    
    # 6. Test caching functionality
    print("\n6️⃣ Testing component caching...")
    
    test_component = {
        'reference': '@github:assetutilities/demo-content',
        'content': 'This is demo content for caching test',
        'version': '1.0.0',
        'metadata': {'size': 100, 'type': 'demo'}
    }
    
    try:
        # Cache the component
        cache_result = await cache_manager.cache_component(test_component)
        
        if cache_result['cached']:
            print(f"✓ Component cached with key: {cache_result['cache_key']}")
            
            # Retrieve from cache
            cached = await cache_manager.get_cached_component(cache_result['cache_key'])
            
            if cached['found']:
                print("✓ Component retrieved from cache successfully")
                print(f"   Content: {cached['content']}")
            else:
                print("✗ Failed to retrieve cached component")
        else:
            print(f"✗ Failed to cache component: {cache_result['error']}")
    
    except Exception as e:
        print(f"✗ Caching error: {e}")
    
    # 7. Test offline fallback
    print("\n7️⃣ Testing offline fallback mechanisms...")
    
    try:
        # Create a fallback entry
        fallback_ref = '@github:assetutilities/fallback-demo.md'
        fallback_content = '# Fallback Demo\n\nThis is fallback content for offline mode.'
        
        await fallback_manager.create_fallback_entry(
            fallback_ref, 
            fallback_content, 
            {'created': 'demo', 'version': '1.0.0'}
        )
        
        print(f"✓ Created fallback entry for {fallback_ref}")
        
        # Retrieve fallback content
        fallback_result = await fallback_manager.get_fallback_content(fallback_ref)
        
        if fallback_result['success']:
            print("✓ Retrieved fallback content successfully")
            print(f"   Source: {fallback_result['source']}")
            print(f"   Content: {fallback_result['content'][:50]}...")
        else:
            print(f"✗ Failed to retrieve fallback content: {fallback_result['error']}")
    
    except Exception as e:
        print(f"✗ Fallback error: {e}")
    
    # 8. Summary
    print("\n8️⃣ Cross-Repository Integration Summary")
    print("=" * 50)
    
    print("✅ IMPLEMENTED FEATURES:")
    print("   • Cross-repository reference parsing and validation")
    print("   • Git submodule integration for AssetUtilities hub")
    print("   • Reference resolution with content extraction")
    print("   • Version compatibility checking with semantic versioning")
    print("   • Component caching with automatic cleanup")
    print("   • Offline fallback mechanisms with default templates")
    print("   • Security validation and path traversal protection")
    print("   • Comprehensive error handling and logging")
    
    print("\n🎯 CROSS-REPOSITORY PATTERN:")
    print("   @github:assetutilities/src/modules/agent-os/enhanced-create-specs/")
    
    print("\n⚙️ SETUP COMMAND:")
    print("   python git_submodule_setup.py --setup")
    
    print("\n📊 STATUS COMMAND:")
    print("   python git_submodule_setup.py --status")
    
    print("\n🚀 Ready for cross-repository development!")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠ Demo cancelled by user")
    except Exception as e:
        print(f"\n✗ Demo error: {e}")