#!/usr/bin/env python3
"""
Test script to verify the global AssetUtilities environment is working correctly.
This script can be copied to any repository to test access to AssetUtilities.
"""

import sys

def test_global_environment():
    """Test the global AssetUtilities environment functionality."""
    print("Testing Global AssetUtilities Environment")
    print("=" * 50)
    
    # Test 1: Basic AssetUtilities import
    try:
        import assetutilities
        print("✅ AssetUtilities core import: SUCCESS")
        print(f"   Version: {assetutilities.__version__}")
    except ImportError as e:
        print(f"❌ AssetUtilities core import: FAILED - {e}")
        return False
    
    # Test 2: Engine functionality
    try:
        from assetutilities.engine import engine
        print("✅ AssetUtilities engine import: SUCCESS")
    except ImportError as e:
        print(f"❌ AssetUtilities engine import: FAILED - {e}")
        return False
    
    # Test 3: Excel utilities
    try:
        from assetutilities.modules.excel_utilities import excel_utilities
        print("✅ Excel utilities import: SUCCESS")
    except ImportError as e:
        print(f"❌ Excel utilities import: FAILED - {e}")
    
    # Test 4: Visualization utilities
    try:
        from assetutilities.modules.visualization import plotly_charts
        print("✅ Visualization utilities import: SUCCESS")
    except ImportError as e:
        print(f"❌ Visualization utilities import: FAILED - {e}")
    
    # Test 5: Data exploration utilities
    try:
        from assetutilities.modules.data_exploration import df_basic_statistics
        print("✅ Data exploration utilities import: SUCCESS")
    except ImportError as e:
        print(f"❌ Data exploration utilities import: FAILED - {e}")
    
    # Test 6: Web scraping utilities
    try:
        from assetutilities.modules.web_scraping import BeautifulSoup_utilities
        print("✅ Web scraping utilities import: SUCCESS")
    except ImportError as e:
        print(f"❌ Web scraping utilities import: FAILED - {e}")
    
    # Test 7: File utilities
    try:
        from assetutilities.modules.file_utilities import file_utilities
        print("✅ File utilities import: SUCCESS")
    except ImportError as e:
        print(f"❌ File utilities import: FAILED - {e}")
    
    # Test 8: Core dependencies
    dependencies = [
        ('pandas', 'pd'),
        ('numpy', 'np'),
        ('plotly', 'plotly'),
        ('matplotlib', 'plt'),
        ('yaml', 'yaml'),
        ('scrapy', 'scrapy'),
        ('selenium', 'selenium'),
        ('openpyxl', 'openpyxl'),
    ]
    
    print("\nTesting Core Dependencies:")
    for dep_name, import_name in dependencies:
        try:
            if import_name == 'pd':
                import pandas as pd
            elif import_name == 'np':
                import numpy as np
            elif import_name == 'plt':
                import matplotlib.pyplot as plt
            else:
                __import__(import_name)
            print(f"✅ {dep_name}: Available")
        except ImportError:
            print(f"❌ {dep_name}: Missing")
    
    # Test 9: Environment information
    print("\nPython Information:")
    print(f"   Python version: {sys.version}")
    print(f"   Python executable: {sys.executable}")
    print(f"   Python path: {sys.path[0]}")
    
    # Test 10: Check if we're in the global environment
    global_env_indicators = [
        'assetutilities-global' in sys.executable,
        '.uv' in sys.executable,
        'assetutilities-global' in str(sys.path)
    ]
    
    if any(global_env_indicators):
        print("OK Running in global AssetUtilities environment")
    else:
        print("WARNING May not be running in global environment")
        print(f"   Executable: {sys.executable}")
    
    print("\n" + "=" * 50)
    print("Global environment test completed!")
    return True

if __name__ == "__main__":
    success = test_global_environment()
    sys.exit(0 if success else 1)