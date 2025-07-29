#!/bin/bash

# Common test utilities for bash test suites
# Provides shared functions and variables for all bash tests

# Color codes for test output
readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly CYAN='\033[0;36m'
readonly NC='\033[0m' # No Color

# Test counters (should be initialized in each test file)
TESTS_RUN=${TESTS_RUN:-0}
TESTS_PASSED=${TESTS_PASSED:-0}
TESTS_FAILED=${TESTS_FAILED:-0}
TESTS_SKIPPED=${TESTS_SKIPPED:-0}

# Common paths
readonly TESTS_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
readonly PROJECT_ROOT="$(cd "$TESTS_DIR/../../.." && pwd)"
readonly SETUP_SCRIPT="$PROJECT_ROOT/scripts/setup-gitbash.sh"

# Test environment utilities
create_test_environment() {
    local test_name="${1:-test}"
    
    # Create unique test directory
    export TEST_TEMP_DIR=$(mktemp -d -t "assetutilities_${test_name}_XXXXXX")
    export TEST_HOME="$TEST_TEMP_DIR/home"
    export TEST_PROJECT="$TEST_TEMP_DIR/project"
    
    # Create directory structure
    mkdir -p "$TEST_HOME"
    mkdir -p "$TEST_PROJECT/.git"
    mkdir -p "$TEST_PROJECT/scripts"
    mkdir -p "$TEST_PROJECT/config"
    mkdir -p "$TEST_PROJECT/src/assetutilities"
    
    # Copy necessary files
    if [[ -f "$SETUP_SCRIPT" ]]; then
        cp "$SETUP_SCRIPT" "$TEST_PROJECT/scripts/"
    fi
    
    # Create marker files for valid project
    touch "$TEST_PROJECT/setup.py"
    echo "name = 'assetutilities'" > "$TEST_PROJECT/setup.py"
    
    # Store original environment
    export ORIGINAL_HOME="$HOME"
    export ORIGINAL_PWD="$PWD"
    
    # Set test environment
    export HOME="$TEST_HOME"
    cd "$TEST_PROJECT"
}

cleanup_test_environment() {
    # Restore original environment
    if [[ -n "$ORIGINAL_HOME" ]]; then
        export HOME="$ORIGINAL_HOME"
    fi
    
    if [[ -n "$ORIGINAL_PWD" ]]; then
        cd "$ORIGINAL_PWD"
    fi
    
    # Clean up test directory
    if [[ -n "$TEST_TEMP_DIR" ]] && [[ -d "$TEST_TEMP_DIR" ]]; then
        rm -rf "$TEST_TEMP_DIR"
    fi
    
    # Unset test variables
    unset TEST_TEMP_DIR TEST_HOME TEST_PROJECT
    unset ORIGINAL_HOME ORIGINAL_PWD
}

# Assertion functions
assert_equals() {
    local expected="$1"
    local actual="$2"
    local message="$3"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if [[ "$expected" == "$actual" ]]; then
        echo -e "${GREEN}✓${NC} $message"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $message"
        echo "  Expected: '$expected'"
        echo "  Actual: '$actual'"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

assert_not_equals() {
    local not_expected="$1"
    local actual="$2"
    local message="$3"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if [[ "$not_expected" != "$actual" ]]; then
        echo -e "${GREEN}✓${NC} $message"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $message"
        echo "  Should not be: '$not_expected'"
        echo "  But got: '$actual'"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

assert_true() {
    local condition="$1"
    local message="$2"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if eval "$condition"; then
        echo -e "${GREEN}✓${NC} $message"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $message"
        echo "  Condition failed: $condition"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

assert_false() {
    local condition="$1"
    local message="$2"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if ! eval "$condition"; then
        echo -e "${GREEN}✓${NC} $message"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $message"
        echo "  Condition should have failed: $condition"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

assert_file_exists() {
    local file="$1"
    local message="$2"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if [[ -f "$file" ]]; then
        echo -e "${GREEN}✓${NC} $message"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $message"
        echo "  File not found: $file"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

assert_dir_exists() {
    local dir="$1"
    local message="$2"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if [[ -d "$dir" ]]; then
        echo -e "${GREEN}✓${NC} $message"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $message"
        echo "  Directory not found: $dir"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

assert_file_contains() {
    local file="$1"
    local pattern="$2"
    local message="$3"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if [[ -f "$file" ]] && grep -q "$pattern" "$file" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $message"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $message"
        if [[ ! -f "$file" ]]; then
            echo "  File not found: $file"
        else
            echo "  Pattern not found in $file: '$pattern'"
        fi
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

assert_file_not_contains() {
    local file="$1"
    local pattern="$2"
    local message="$3"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if [[ ! -f "$file" ]] || ! grep -q "$pattern" "$file" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $message"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $message"
        echo "  Pattern found in $file: '$pattern'"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

assert_command_success() {
    local command="$1"
    local message="$2"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if eval "$command" >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $message"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $message"
        echo "  Command failed: $command"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

assert_command_fails() {
    local command="$1"
    local message="$2"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if ! eval "$command" >/dev/null 2>&1; then
        echo -e "${GREEN}✓${NC} $message"
        TESTS_PASSED=$((TESTS_PASSED + 1))
        return 0
    else
        echo -e "${RED}✗${NC} $message"
        echo "  Command should have failed: $command"
        TESTS_FAILED=$((TESTS_FAILED + 1))
        return 1
    fi
}

# Skip test function
skip_test() {
    local message="$1"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    TESTS_SKIPPED=$((TESTS_SKIPPED + 1))
    
    echo -e "${YELLOW}⚠${NC} SKIPPED: $message"
}

# Test output utilities
print_test_header() {
    local test_name="$1"
    
    echo ""
    echo "=================================="
    echo "$test_name"
    echo "=================================="
}

print_test_summary() {
    echo ""
    echo "=================================="
    echo "Test Summary"
    echo "=================================="
    echo "Tests run: $TESTS_RUN"
    echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"
    
    if [[ $TESTS_SKIPPED -gt 0 ]]; then
        echo -e "Tests skipped: ${YELLOW}$TESTS_SKIPPED${NC}"
    fi
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "\n${GREEN}All tests passed!${NC}"
        return 0
    else
        echo -e "\n${RED}Some tests failed!${NC}"
        return 1
    fi
}

# Mock functions for testing
mock_date() {
    # Mock date command for consistent testing
    echo "20250101_120000"
}

mock_command_exists() {
    local command="$1"
    # Mock command existence check
    case "$command" in
        "python"|"bash"|"git")
            return 0
            ;;
        *)
            return 1
            ;;
    esac
}

# Platform detection
is_windows_git_bash() {
    [[ "$OSTYPE" == "msys" ]] || [[ "$OSTYPE" == "cygwin" ]]
}

is_wsl() {
    grep -qi microsoft /proc/version 2>/dev/null
}

is_macos() {
    [[ "$OSTYPE" == "darwin"* ]]
}

is_linux() {
    [[ "$OSTYPE" == "linux-gnu"* ]] && ! is_wsl
}

# File system utilities
get_file_permissions() {
    local file="$1"
    
    if is_macos; then
        stat -f %Lp "$file" 2>/dev/null
    else
        stat -c %a "$file" 2>/dev/null
    fi
}

get_file_size() {
    local file="$1"
    
    if is_macos; then
        stat -f %z "$file" 2>/dev/null
    else
        stat -c %s "$file" 2>/dev/null
    fi
}

# Temporary file utilities
create_temp_file() {
    local prefix="${1:-test}"
    mktemp -t "${prefix}_XXXXXX"
}

create_temp_dir() {
    local prefix="${1:-test}"
    mktemp -d -t "${prefix}_XXXXXX"
}

# Cleanup trap utility
setup_cleanup_trap() {
    trap 'cleanup_test_environment' EXIT INT TERM
}

# Export all functions so they're available to test scripts
export -f assert_equals assert_not_equals assert_true assert_false
export -f assert_file_exists assert_dir_exists
export -f assert_file_contains assert_file_not_contains
export -f assert_command_success assert_command_fails
export -f skip_test print_test_header print_test_summary
export -f create_test_environment cleanup_test_environment
export -f is_windows_git_bash is_wsl is_macos is_linux
export -f get_file_permissions get_file_size
export -f create_temp_file create_temp_dir
export -f setup_cleanup_trap