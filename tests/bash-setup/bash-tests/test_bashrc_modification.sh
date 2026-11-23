#!/bin/bash

# Test suite for .bashrc modification and backup functionality
# Tests the safe modification of .bashrc by the setup script

# Test framework setup
readonly TEST_NAME="test_bashrc_modification"
readonly TEST_DIR="$(dirname "$0")"
readonly PROJECT_ROOT="$(cd "$TEST_DIR/../../.." && pwd)"
readonly SETUP_SCRIPT="$PROJECT_ROOT/scripts/setup-gitbash.sh"

# Colors for test output
readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly NC='\033[0m' # No Color

# Test counters
TESTS_RUN=0
TESTS_PASSED=0
TESTS_FAILED=0

# Test utilities
setup_test_environment() {
    # Create temporary test directory
    export TEST_TEMP_DIR=$(mktemp -d)
    export TEST_HOME="$TEST_TEMP_DIR/home"
    export TEST_PROJECT="$TEST_TEMP_DIR/project"
    
    # Create test directories
    mkdir -p "$TEST_HOME"
    mkdir -p "$TEST_PROJECT/.git"
    mkdir -p "$TEST_PROJECT/scripts"
    mkdir -p "$TEST_PROJECT/config"
    mkdir -p "$TEST_PROJECT/src/assetutilities"
    
    # Copy setup script to test project
    cp "$SETUP_SCRIPT" "$TEST_PROJECT/scripts/"
    
    # Create marker files
    touch "$TEST_PROJECT/setup.py"
    echo "name = 'assetutilities'" > "$TEST_PROJECT/setup.py"
    
    # Override HOME for testing
    export ORIGINAL_HOME="$HOME"
    export HOME="$TEST_HOME"
    
    # Change to test project directory
    cd "$TEST_PROJECT"
}

cleanup_test_environment() {
    # Restore original HOME
    export HOME="$ORIGINAL_HOME"
    
    # Remove test directory
    rm -rf "$TEST_TEMP_DIR"
}

# Test assertion functions
assert_equals() {
    local expected="$1"
    local actual="$2"
    local message="$3"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if [[ "$expected" == "$actual" ]]; then
        echo -e "${GREEN}✓${NC} $message"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} $message"
        echo "  Expected: $expected"
        echo "  Actual: $actual"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

assert_file_exists() {
    local file="$1"
    local message="$2"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if [[ -f "$file" ]]; then
        echo -e "${GREEN}✓${NC} $message"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} $message"
        echo "  File not found: $file"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

assert_file_contains() {
    local file="$1"
    local pattern="$2"
    local message="$3"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if grep -q "$pattern" "$file" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $message"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} $message"
        echo "  Pattern not found in $file: $pattern"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

assert_file_not_contains() {
    local file="$1"
    local pattern="$2"
    local message="$3"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    if ! grep -q "$pattern" "$file" 2>/dev/null; then
        echo -e "${GREEN}✓${NC} $message"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} $message"
        echo "  Pattern found in $file: $pattern"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Test cases
test_backup_creation_new_bashrc() {
    echo ""
    echo "Testing: Backup creation for new .bashrc"
    
    setup_test_environment
    
    # Ensure no .bashrc exists
    rm -f "$TEST_HOME/.bashrc"
    
    # Run setup script
    cd "$TEST_PROJECT"
    bash "$TEST_PROJECT/scripts/setup-gitbash.sh" install >/dev/null 2>&1
    
    # Test that .bashrc was created
    assert_file_exists "$TEST_HOME/.bashrc" "New .bashrc should be created"
    
    # Test that no backup was created (since .bashrc didn't exist)
    local backup_count=$(ls "$TEST_HOME"/.bashrc.backup.* 2>/dev/null | wc -l)
    assert_equals "0" "$backup_count" "No backup should be created for new .bashrc"
    
    cleanup_test_environment
}

test_backup_creation_existing_bashrc() {
    echo ""
    echo "Testing: Backup creation for existing .bashrc"
    
    setup_test_environment
    
    # Create existing .bashrc with content
    local original_content="# Original user configuration
alias ll='ls -la'
export PATH=/custom/path:\$PATH"
    echo "$original_content" > "$TEST_HOME/.bashrc"
    
    # Run setup script
    cd "$TEST_PROJECT"
    bash "$TEST_PROJECT/scripts/setup-gitbash.sh" install >/dev/null 2>&1
    
    # Test that backup was created
    local backup_files=("$TEST_HOME"/.bashrc.backup.*)
    assert_equals "1" "${#backup_files[@]}" "One backup file should be created"
    
    # Test backup content matches original
    if [[ -f "${backup_files[0]}" ]]; then
        local backup_content=$(cat "${backup_files[0]}")
        assert_equals "$original_content" "$backup_content" "Backup should preserve original content"
    fi
    
    cleanup_test_environment
}

test_configuration_injection() {
    echo ""
    echo "Testing: Configuration injection into .bashrc"
    
    setup_test_environment
    
    # Create existing .bashrc
    echo "# User's original config" > "$TEST_HOME/.bashrc"
    
    # Run setup script
    cd "$TEST_PROJECT"
    bash "$TEST_PROJECT/scripts/setup-gitbash.sh" install >/dev/null 2>&1
    
    # Test that configuration marker was added
    assert_file_contains "$TEST_HOME/.bashrc" "# AssetUtilities Project Configuration" \
        "Configuration marker should be added"
    
    # Test that load function was added
    assert_file_contains "$TEST_HOME/.bashrc" "load_assetutilities_config()" \
        "Load function should be added"
    
    # Test that original content is preserved
    assert_file_contains "$TEST_HOME/.bashrc" "# User's original config" \
        "Original content should be preserved"
    
    cleanup_test_environment
}

test_idempotent_installation() {
    echo ""
    echo "Testing: Idempotent installation (no duplicate configs)"
    
    setup_test_environment
    
    # Create .bashrc
    echo "# Original config" > "$TEST_HOME/.bashrc"
    
    # Run setup script twice
    cd "$TEST_PROJECT"
    bash "$TEST_PROJECT/scripts/setup-gitbash.sh" install >/dev/null 2>&1
    bash "$TEST_PROJECT/scripts/setup-gitbash.sh" install >/dev/null 2>&1
    
    # Count occurrences of configuration marker
    local marker_count=$(grep -c "# AssetUtilities Project Configuration" "$TEST_HOME/.bashrc" || echo "0")
    assert_equals "1" "$marker_count" "Configuration should only be added once"
    
    # Check backup count (should only be one from first install)
    local backup_count=$(ls "$TEST_HOME"/.bashrc.backup.* 2>/dev/null | wc -l)
    assert_equals "1" "$backup_count" "Only one backup should exist"
    
    cleanup_test_environment
}

test_safe_modification_permissions() {
    echo ""
    echo "Testing: Safe modification with restricted permissions"
    
    setup_test_environment
    
    # Create .bashrc with restricted permissions
    echo "# Protected config" > "$TEST_HOME/.bashrc"
    chmod 444 "$TEST_HOME/.bashrc"  # Read-only
    
    # Run setup script (should handle permission issues gracefully)
    cd "$TEST_PROJECT"
    local output=$(bash "$TEST_PROJECT/scripts/setup-gitbash.sh" install 2>&1)
    
    # The script should handle this gracefully (might fail but shouldn't crash)
    # This is a boundary test - we're testing error handling
    
    # Restore permissions for cleanup
    chmod 644 "$TEST_HOME/.bashrc"
    
    cleanup_test_environment
}

test_backup_timestamp_format() {
    echo ""
    echo "Testing: Backup file timestamp format"
    
    setup_test_environment
    
    # Create existing .bashrc
    echo "# Test config" > "$TEST_HOME/.bashrc"
    
    # Run setup script
    cd "$TEST_PROJECT"
    bash "$TEST_PROJECT/scripts/setup-gitbash.sh" install >/dev/null 2>&1
    
    # Check backup filename format
    local backup_file=$(ls "$TEST_HOME"/.bashrc.backup.* 2>/dev/null | head -1)
    if [[ -n "$backup_file" ]]; then
        local backup_name=$(basename "$backup_file")
        # Expected format: .bashrc.backup.YYYYMMDD_HHMMSS
        if [[ "$backup_name" =~ \.bashrc\.backup\.[0-9]{8}_[0-9]{6}$ ]]; then
            echo -e "${GREEN}✓${NC} Backup filename follows correct timestamp format"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo -e "${RED}✗${NC} Backup filename doesn't match expected format"
            echo "  Got: $backup_name"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
        TESTS_RUN=$((TESTS_RUN + 1))
    fi
    
    cleanup_test_environment
}

test_configuration_removal() {
    echo ""
    echo "Testing: Configuration removal (uninstall)"
    
    setup_test_environment
    
    # Create .bashrc with some content
    echo "# Before AssetUtilities" > "$TEST_HOME/.bashrc"
    
    # Install configuration
    cd "$TEST_PROJECT"
    bash "$TEST_PROJECT/scripts/setup-gitbash.sh" install >/dev/null 2>&1
    
    # Verify installation
    assert_file_contains "$TEST_HOME/.bashrc" "# AssetUtilities Project Configuration" \
        "Configuration should be installed"
    
    # Uninstall configuration
    bash "$TEST_PROJECT/scripts/setup-gitbash.sh" uninstall >/dev/null 2>&1
    
    # Verify removal
    assert_file_not_contains "$TEST_HOME/.bashrc" "# AssetUtilities Project Configuration" \
        "Configuration should be removed"
    
    # Verify original content is preserved
    assert_file_contains "$TEST_HOME/.bashrc" "# Before AssetUtilities" \
        "Original content should remain after uninstall"
    
    cleanup_test_environment
}

test_empty_bashrc_handling() {
    echo ""
    echo "Testing: Empty .bashrc file handling"
    
    setup_test_environment
    
    # Create empty .bashrc
    touch "$TEST_HOME/.bashrc"
    
    # Run setup script
    cd "$TEST_PROJECT"
    bash "$TEST_PROJECT/scripts/setup-gitbash.sh" install >/dev/null 2>&1
    
    # Test that configuration was added to empty file
    assert_file_contains "$TEST_HOME/.bashrc" "# AssetUtilities Project Configuration" \
        "Configuration should be added to empty .bashrc"
    
    # Test file is not empty after installation
    local file_size=$(stat -c%s "$TEST_HOME/.bashrc" 2>/dev/null || stat -f%z "$TEST_HOME/.bashrc" 2>/dev/null || echo "0")
    if [[ "$file_size" -gt "0" ]]; then
        echo -e "${GREEN}✓${NC} .bashrc is no longer empty after installation"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} .bashrc is still empty after installation"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    TESTS_RUN=$((TESTS_RUN + 1))
    
    cleanup_test_environment
}

# Main test runner
run_all_tests() {
    echo "=================================="
    echo "Running .bashrc Modification Tests"
    echo "=================================="
    
    # Run all test cases
    test_backup_creation_new_bashrc
    test_backup_creation_existing_bashrc
    test_configuration_injection
    test_idempotent_installation
    test_safe_modification_permissions
    test_backup_timestamp_format
    test_configuration_removal
    test_empty_bashrc_handling
    
    # Print summary
    echo ""
    echo "=================================="
    echo "Test Summary"
    echo "=================================="
    echo "Tests run: $TESTS_RUN"
    echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "\n${GREEN}All tests passed!${NC}"
        exit 0
    else
        echo -e "\n${RED}Some tests failed!${NC}"
        exit 1
    fi
}

# Check if setup script exists
if [[ ! -f "$SETUP_SCRIPT" ]]; then
    echo -e "${RED}Error: Setup script not found at $SETUP_SCRIPT${NC}"
    exit 1
fi

# Run tests
run_all_tests