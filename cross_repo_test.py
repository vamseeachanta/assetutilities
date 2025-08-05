#!/usr/bin/env python3
"""
Cross-repository test to demonstrate global AssetUtilities environment usage.
This script simulates how other repositories would use the global environment.
"""

import os
import sys
import tempfile
import subprocess

def create_test_repository():
    """Create a temporary test repository to simulate cross-repo usage."""
    # Create temporary directory
    test_repo = tempfile.mkdtemp(prefix="assetutils_test_repo_")
    print(f"Created test repository: {test_repo}")
    
    # Create a simple test script that uses AssetUtilities
    test_script = os.path.join(test_repo, "use_assetutils.py")
    script_content = '''#!/usr/bin/env python3
"""Test script that uses AssetUtilities from global environment."""

import sys
print(f"Python executable: {sys.executable}")
print(f"Python version: {sys.version.split()[0]}")

# Test AssetUtilities import
try:
    import assetutilities
    print(f"SUCCESS: AssetUtilities {assetutilities.__version__} imported")
    
    # Test core modules
    from assetutilities.engine import engine
    from assetutilities.modules.file_utilities import file_utilities
    print("SUCCESS: Core modules imported")
    
    # Test dependencies
    import pandas as pd
    import plotly
    import numpy as np
    print("SUCCESS: Core dependencies available")
    
    print("\\nALL TESTS PASSED - Global environment working correctly!")
    return True
    
except ImportError as e:
    print(f"FAILED: Import error - {e}")
    return False
'''
    
    with open(test_script, 'w') as f:
        f.write(script_content)
    
    # Copy activation script to test repo
    activation_script = os.path.join(test_repo, "activate-assetutils-global.bat")
    with open("scripts/activate-assetutils-global.bat", 'r') as src:
        with open(activation_script, 'w') as dst:
            dst.write(src.read())
    
    return test_repo, test_script, activation_script

def test_global_environment_access():
    """Test accessing the global environment from a different repository."""
    print("Testing Cross-Repository Global Environment Access")
    print("=" * 55)
    
    # Create test repository
    test_repo, test_script, activation_script = create_test_repository()
    
    try:
        # Test 1: Check global environment exists
        global_python = os.path.expanduser("~/.uv/envs/assetutilities-global/Scripts/python.exe")
        if os.path.exists(global_python):
            print("✅ Global environment found")
        else:
            print("❌ Global environment not found")
            return False
        
        # Test 2: Run test script with global Python
        print(f"\nRunning test from: {test_repo}")
        print("Using global AssetUtilities environment...")
        print("-" * 40)
        
        # Execute the test script using global Python
        result = subprocess.run([global_python, test_script], 
                              capture_output=True, text=True, cwd=test_repo)
        
        if result.returncode == 0:
            print(result.stdout)
            print("✅ Cross-repository test PASSED")
            return True
        else:
            print("❌ Cross-repository test FAILED")
            print("STDOUT:", result.stdout)
            print("STDERR:", result.stderr)
            return False
            
    except Exception as e:
        print(f"❌ Test failed with exception: {e}")
        return False
    
    finally:
        # Cleanup
        try:
            import shutil
            shutil.rmtree(test_repo)
            print(f"\nCleaned up test repository: {test_repo}")
        except:
            pass

if __name__ == "__main__":
    success = test_global_environment_access()
    if success:
        print("\n🎉 Global environment is ready for cross-repository use!")
    else:
        print("\n❌ Global environment needs troubleshooting")
    
    sys.exit(0 if success else 1)