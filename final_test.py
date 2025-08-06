#!/usr/bin/env python3
"""Final test of the global AssetUtilities environment."""

import os
import sys
import subprocess

def test_global_environment():
    """Test the global environment directly."""
    print("Final Global Environment Test")
    print("=" * 30)
    
    # Check if global environment exists
    user_profile = os.environ.get('USERPROFILE', os.path.expanduser('~'))
    global_python = os.path.join(user_profile, '.uv', 'envs', 'assetutilities-global', 'Scripts', 'python.exe')
    
    if not os.path.exists(global_python):
        print("ERROR: Global environment not found")
        return False
        
    print(f"Found global Python: {global_python}")
    
    # Test basic import
    test_code = '''
import sys
print("Python:", sys.executable)
try:
    import assetutilities
    print("SUCCESS: AssetUtilities version", assetutilities.__version__)
    from assetutilities.engine import engine
    print("SUCCESS: Engine imported")
    import pandas as pd
    print("SUCCESS: Pandas imported")
    import plotly
    print("SUCCESS: Plotly imported")
    print("ALL TESTS PASSED")
except Exception as e:
    print("FAILED:", str(e))
    sys.exit(1)
'''
    
    try:
        result = subprocess.run([global_python, "-c", test_code], 
                              capture_output=True, text=True)
        
        print("\nTest Results:")
        print(result.stdout)
        
        if result.stderr:
            print("Warnings:")
            print(result.stderr)
        
        return result.returncode == 0
        
    except Exception as e:
        print(f"Test failed: {e}")
        return False

if __name__ == "__main__":
    success = test_global_environment()
    print("\n" + "=" * 30)
    if success:
        print("GLOBAL ENVIRONMENT READY!")
    else:
        print("GLOBAL ENVIRONMENT NEEDS WORK")
    
    print("\nUsage Instructions:")
    print("1. Copy scripts/activate-assetutils-global.bat to other repos")
    print("2. Run the script to activate the global environment")
    user_profile = os.environ.get('USERPROFILE', os.path.expanduser('~'))
    global_python_path = os.path.join(user_profile, '.uv', 'envs', 'assetutilities-global', 'Scripts', 'python.exe')
    print(f"3. Or use directly: {global_python_path}")