#!/usr/bin/env python3
import sys
print("Python executable:", sys.executable)
print("Python version:", sys.version)

try:
    import assetutilities
    print("SUCCESS: AssetUtilities imported")
    print("Version:", assetutilities.__version__)
except ImportError as e:
    print("FAILED: AssetUtilities import error:", e)

try:
    from assetutilities.engine import engine
    print("SUCCESS: Engine imported")
except ImportError as e:
    print("FAILED: Engine import error:", e)

try:
    import pandas as pd
    print("SUCCESS: Pandas imported")
except ImportError as e:
    print("FAILED: Pandas import error:", e)