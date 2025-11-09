# ABOUTME: Test troubleshooting progress report tracking fixes and improvements
# ABOUTME: Documents the systematic debugging process and results

# Test Suite Troubleshooting Progress

## Session: 2025-01-18

### Initial State
- **Total tests**: 337 collectable (21 files excluded due to collection errors)
- **Pass rate**: 271/337 (80.4%)
- **Failures**: 64
- **Errors**: 2

---

## Fix #1: sys.argv File Path Issue

### Problem Identified
**Root Cause**: `cli_parser.py` was checking `sys.argv[1]` even during pytest runs. When pytest ran with `pytest tests/`, it passed "tests/" as `sys.argv[1]`, causing `FileNotFoundError: Input file tests/ not found`.

**Impact**: Affected 26 tests across multiple modules:
- Data exploration (7 tests)
- Visualization (11 tests)
- Web scraping (2 tests)
- CSV utilities (1 test)
- Download data (1 test)
- Excel utilities (1 test)
- Zip utilities (2 tests)
- Pipeline CI/CD (1 test)

### Solution Implemented
**File**: `src/assetutilities/common/cli_parser.py`

**Changes**:
```python
# Detect if running under pytest
is_pytest = any("pytest" in arg or "_pytest" in arg for arg in sys.argv[0:2])

# Handle input file
if len(sys.argv) > 1:
    if inputfile is not None:
        # If running under pytest, skip sys.argv processing since inputfile is provided
        if is_pytest:
            pass  # Use the provided inputfile, ignore sys.argv
        else:
            raise Exception("2 Input files provided...")
    elif not is_pytest:
        # Only use sys.argv[1] when NOT running under pytest
        if os.path.isfile(sys.argv[1]):
            inputfile = sys.argv[1]
        elif not sys.argv[1].startswith('--'):
            raise FileNotFoundError(f"Input file {sys.argv[1]} not found ... FAIL")
```

### Results
✅ **Fix successful**: Tests no longer fail with "Input file tests/ not found"

❌ **New issue revealed**: Tests now progress further but fail with YAML parsing errors:
```
yaml.scanner.ScannerError: mapping values are not allowed here
  in "tests/modules/csv_utilities/csv_with_latin1_test.py", line 5, column 28
```

**Analysis**: The ApplicationManager is attempting to parse test .py files as YAML configuration files instead of the actual .yml files.

### Test Results After Fix
- **Pass rate**: Still 271/337 (80.4%) 
- **Failures**: Still 64 (but error types changed)
- **Errors**: Still 2

**Error Distribution Changed**:
- ✅ **Before**: "FileNotFoundError: Input file tests/ not found" (26 tests)
- ❌ **After**: "SystemExit" from YAML parsing errors (26 tests)

---

## Next Steps

### Priority 1: YAML Path Resolution Issue
**Problem**: `ApplicationManager.py` is setting `customYaml` to the test .py file path instead of the .yml config file path.

**Investigation Needed**:
1. Check how `customYaml` attribute is being set in ApplicationManager
2. Verify path resolution logic in engine.py
3. Ensure test files are passing correct paths

**Affected Tests**: Same 26 tests that were affected by sys.argv issue

### Priority 2: Module-Level Execution (14 files excluded)
Tests executing code at module import time need refactoring.

### Priority 3: CLI/Integration Tests (33 failures)
Update assertions to match current CLI interface behavior.

### Priority 4: Missing Test Data (6 files)
Create or locate missing YAML/CSV/PDF test files.

### Priority 5: Fixture Errors (2 errors)
Add missing pytest fixtures in conftest.py.

---

## Code Coverage Impact

### Before Fixes
- Overall: 32%

### After sys.argv Fix
- Overall: 33% (slight improvement)
- Notable improvements in:
  - `cli_parser.py`: 31% → 58%
  - Agent OS CLI modules: 0% → 61-89%

---

## Summary

### Achievements
1. ✅ Successfully diagnosed sys.argv file path issue
2. ✅ Implemented pytest detection in cli_parser.py
3. ✅ Tests now progress past sys.argv check
4. ✅ Improved code coverage by 1%
5. ✅ Revealed underlying YAML path resolution issue

### Current Blockers
1. ❌ ApplicationManager confusing test file paths with config file paths
2. ❌ 14 test files with module-level execution
3. ❌ 33 CLI/integration test assertions need updating
4. ❌ Missing test data files

### Pass Rate Tracking
| Step | Pass | Fail | Error | Coverage | Notes |
|------|------|------|-------|----------|-------|
| Initial | 271 | 64 | 2 | 32% | Baseline |
| After sys.argv fix | 271 | 64 | 2 | 33% | Error types changed |

---

## Lessons Learned

1. **Systematic Debugging Works**: Following the "Priority 1" approach from baseline document led to quick identification of root cause.

2. **Fix Reveals Deeper Issues**: Fixing sys.argv issue revealed the underlying YAML path resolution problem that was hidden.

3. **Test Environment Detection**: Adding pytest detection improves test isolation but needs to be comprehensive.

4. **Error Message Evolution**: Same failure count but different error messages indicates progress through the issue stack.

---

## Next Session Goals

1. Fix YAML path resolution in ApplicationManager
2. Target: Reduce failures from 64 to <50
3. Fix at least 5 module-level execution test files
4. Increase code coverage to 35%+
