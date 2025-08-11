#!/usr/bin/env python
"""Test script to validate web-contextualization module improvements."""

import sys
import json
from pathlib import Path
import tempfile
import shutil

def test_module_import():
    """Test that the module can be imported."""
    try:
        # Add module path to sys.path
        module_path = Path(__file__).parent / "src" / "modules" / "web-contextualization"
        sys.path.insert(0, str(module_path))
        
        # Try importing all modules
        from web_contextualizer import WebContextualizer
        from web_contextualizer_enhanced import WebContextualizerEnhanced
        from pdf_processor import PDFProcessor
        from content_indexer import ContentIndexer
        from resource_fetcher import ResourceFetcher
        
        print("✅ All modules imported successfully")
        return True
    except ImportError as e:
        print(f"❌ Import error: {e}")
        return False

def test_basic_functionality():
    """Test basic functionality of the enhanced module."""
    try:
        # Add module path to sys.path
        module_path = Path(__file__).parent / "src" / "modules" / "web-contextualization"
        sys.path.insert(0, str(module_path))
        
        from web_contextualizer_enhanced import WebContextualizerEnhanced
        
        # Create temporary directory for testing
        with tempfile.TemporaryDirectory() as temp_dir:
            agent_dir = Path(temp_dir) / "test_agent"
            
            # Initialize contextualizer
            contextualizer = WebContextualizerEnhanced(
                agent_dir=agent_dir,
                max_workers=2
            )
            
            # Test 1: Configuration created
            config_file = agent_dir / "context" / "external" / "web" / "contextualization_config.yaml"
            assert config_file.exists(), "Configuration file not created"
            print("✅ Configuration file created")
            
            # Test 2: Add a resource
            resource = contextualizer.add_resource(
                url="https://example.com/test.html",
                resource_type="tutorial",
                title="Test Resource",
                description="A test resource",
                priority=5,
                tags=["test", "example"],
                auto_fetch=False  # Don't actually fetch
            )
            assert resource.url == "https://example.com/test.html"
            assert resource.priority == 5
            assert "test" in resource.tags
            print("✅ Resource added successfully")
            
            # Test 3: Batch add resources
            batch_resources = [
                {
                    "url": "https://example.com/doc1.pdf",
                    "type": "official_docs",
                    "priority": 3,
                    "tags": ["documentation"]
                },
                {
                    "url": "https://example.com/doc2.html",
                    "type": "api_reference",
                    "priority": 4,
                    "tags": ["api", "reference"]
                }
            ]
            added = contextualizer.add_resources_batch(batch_resources, auto_fetch=False)
            assert len(added) == 2
            print("✅ Batch resources added successfully")
            
            # Test 4: Resources saved
            resources_file = agent_dir / "context" / "external" / "web" / "resources.json"
            assert resources_file.exists(), "Resources file not created"
            
            with open(resources_file, 'r') as f:
                saved_resources = json.load(f)
            assert len(saved_resources) == 3
            print("✅ Resources saved to file")
            
            # Test 5: Status report generation
            report = contextualizer.generate_enhanced_status_report()
            assert "Web Resource Contextualization Status Report" in report
            assert "Total Resources: 3" in report
            print("✅ Status report generated")
            
            # Test 6: Cleanup
            contextualizer.cleanup()
            print("✅ Cleanup successful")
            
        return True
        
    except Exception as e:
        print(f"❌ Test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_parallel_configuration():
    """Test that parallel processing configuration is set up correctly."""
    try:
        # Check pyproject.toml has parallel configuration
        pyproject_path = Path(__file__).parent / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml not found"
        
        with open(pyproject_path, 'r') as f:
            content = f.read()
            assert "[tool.parallel]" in content, "Parallel configuration not found in pyproject.toml"
            assert "max_workers" in content, "max_workers not configured"
        
        print("✅ Parallel processing configuration found in pyproject.toml")
        
        # Check uv.toml has parallel configuration
        uv_toml_path = Path(__file__).parent / "uv.toml"
        assert uv_toml_path.exists(), "uv.toml not found"
        
        with open(uv_toml_path, 'r') as f:
            content = f.read()
            assert "[tool.uv.parallel]" in content or "parallel" in content, "Parallel configuration not found in uv.toml"
        
        print("✅ Parallel processing configuration found in uv.toml")
        
        return True
        
    except AssertionError as e:
        print(f"❌ Configuration test failed: {e}")
        return False

def test_single_source_of_truth():
    """Test that dependencies are centralized in pyproject.toml."""
    try:
        # Check that pyproject.toml exists and has dependencies
        pyproject_path = Path(__file__).parent / "pyproject.toml"
        assert pyproject_path.exists(), "pyproject.toml not found"
        
        with open(pyproject_path, 'r') as f:
            content = f.read()
            assert "dependencies = [" in content, "Dependencies section not found"
            # Check for key dependencies
            assert "numpy" in content, "numpy not in dependencies"
            assert "pandas" in content, "pandas not in dependencies"
            assert "PyPDF2" in content or "pypdf2" in content.lower(), "PyPDF2 not in dependencies"
        
        print("✅ Dependencies centralized in pyproject.toml")
        
        # Check that requirements.txt references pyproject.toml
        req_path = Path(__file__).parent / "requirements.txt"
        if req_path.exists():
            with open(req_path, 'r') as f:
                content = f.read()
                assert "pyproject.toml" in content or "pip install -e" in content, \
                    "requirements.txt doesn't reference pyproject.toml"
            print("✅ requirements.txt references pyproject.toml")
        
        # Check that module-specific requirements are removed
        module_req_path = Path(__file__).parent / "src" / "modules" / "web-contextualization" / "requirements.txt"
        assert not module_req_path.exists(), "Module-specific requirements.txt still exists"
        print("✅ Module-specific requirements.txt removed")
        
        return True
        
    except AssertionError as e:
        print(f"❌ Single source of truth test failed: {e}")
        return False

def main():
    """Run all tests."""
    print("=" * 60)
    print("Testing AssetUtilities Web-Contextualization Improvements")
    print("=" * 60)
    
    tests = [
        ("Module Import Test", test_module_import),
        ("Basic Functionality Test", test_basic_functionality),
        ("Parallel Configuration Test", test_parallel_configuration),
        ("Single Source of Truth Test", test_single_source_of_truth),
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🔍 Running: {test_name}")
        print("-" * 40)
        success = test_func()
        results.append((test_name, success))
        print()
    
    # Summary
    print("=" * 60)
    print("Test Summary")
    print("=" * 60)
    
    passed = sum(1 for _, success in results if success)
    total = len(results)
    
    for test_name, success in results:
        status = "✅ PASSED" if success else "❌ FAILED"
        print(f"{test_name}: {status}")
    
    print(f"\nTotal: {passed}/{total} tests passed")
    
    if passed == total:
        print("\n🎉 All tests passed! The improvements are working correctly.")
    else:
        print(f"\n⚠️  {total - passed} test(s) failed. Please review the errors above.")
    
    return passed == total

if __name__ == "__main__":
    success = main()
    sys.exit(0 if success else 1)