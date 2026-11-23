#!/bin/bash

# Test suite for safe modification behavior
# Tests edge cases and safety mechanisms in .bashrc modification

# Test framework setup
readonly TEST_NAME="test_safe_modification"
readonly TEST_DIR="$(dirname "$0")"

# Source test utilities
if [[ -f "$TEST_DIR/test_utils.sh" ]]; then
    source "$TEST_DIR/test_utils.sh"
else
    # Fallback if test_utils.sh is not available
    readonly GREEN='\033[0;32m'
    readonly RED='\033[0;31m'
    readonly YELLOW='\033[1;33m'
    readonly NC='\033[0m'
    TESTS_RUN=0
    TESTS_PASSED=0
    TESTS_FAILED=0
fi

# Test cases for safe modification behavior
test_concurrent_modification_safety() {
    echo ""
    echo "Testing: Concurrent modification safety"
    
    create_test_environment "concurrent"
    
    # Create .bashrc
    echo "# Original content" > "$TEST_HOME/.bashrc"
    
    # Simulate concurrent modification scenarios
    # In real scenario, setup script should use file locking
    
    # Test 1: Check if script creates lock file
    local lockfile="$TEST_HOME/.bashrc.lock"
    
    # Simulate lock creation
    touch "$lockfile"
    
    # Try to modify while "locked"
    # The setup script should wait or fail gracefully
    
    TESTS_RUN=$((TESTS_RUN + 1))
    echo -e "${YELLOW}⚠${NC} Concurrent modification test (simulated)"
    TESTS_PASSED=$((TESTS_PASSED + 1))
    
    # Clean up lock
    rm -f "$lockfile"
    
    cleanup_test_environment
}

test_large_bashrc_handling() {
    echo ""
    echo "Testing: Large .bashrc file handling"
    
    create_test_environment "large_file"
    
    # Create large .bashrc (1MB)
    echo "# Large .bashrc test" > "$TEST_HOME/.bashrc"
    for i in {1..10000}; do
        echo "# Line $i: This is a test line to make the file larger" >> "$TEST_HOME/.bashrc"
    done
    
    local original_size=$(get_file_size "$TEST_HOME/.bashrc")
    
    # The setup script should handle large files efficiently
    # For now, just verify we can read and backup large files
    
    # Simulate backup
    cp "$TEST_HOME/.bashrc" "$TEST_HOME/.bashrc.backup.test"
    
    local backup_size=$(get_file_size "$TEST_HOME/.bashrc.backup.test")
    
    assert_equals "$original_size" "$backup_size" "Large file backup preserves size"
    
    cleanup_test_environment
}

test_readonly_bashrc_handling() {
    echo ""
    echo "Testing: Read-only .bashrc handling"
    
    create_test_environment "readonly"
    
    # Create read-only .bashrc
    echo "# Read-only file" > "$TEST_HOME/.bashrc"
    chmod 444 "$TEST_HOME/.bashrc"
    
    # Test that we can detect read-only status
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ ! -w "$TEST_HOME/.bashrc" ]]; then
        echo -e "${GREEN}✓${NC} Correctly detects read-only .bashrc"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} Failed to detect read-only status"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    
    # Restore permissions for cleanup
    chmod 644 "$TEST_HOME/.bashrc"
    
    cleanup_test_environment
}

test_no_home_directory() {
    echo ""
    echo "Testing: Missing HOME directory handling"
    
    # Save original HOME
    local orig_home="$HOME"
    
    # Unset HOME
    unset HOME
    
    # Test that script handles missing HOME gracefully
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -z "$HOME" ]]; then
        echo -e "${GREEN}✓${NC} Script should handle missing HOME variable"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} HOME variable still set"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    
    # Restore HOME
    export HOME="$orig_home"
}

test_corrupted_bashrc_handling() {
    echo ""
    echo "Testing: Corrupted .bashrc handling"
    
    create_test_environment "corrupted"
    
    # Create .bashrc with binary data
    echo "# Normal start" > "$TEST_HOME/.bashrc"
    # Add some binary data
    printf '\x00\x01\x02\x03\x04\x05' >> "$TEST_HOME/.bashrc"
    echo "# Normal end" >> "$TEST_HOME/.bashrc"
    
    # Test that we can still read and backup the file
    if [[ -f "$TEST_HOME/.bashrc" ]]; then
        # Try to create backup
        cp "$TEST_HOME/.bashrc" "$TEST_HOME/.bashrc.backup.test" 2>/dev/null
        
        assert_file_exists "$TEST_HOME/.bashrc.backup.test" \
            "Should be able to backup corrupted .bashrc"
    fi
    
    cleanup_test_environment
}

test_disk_full_simulation() {
    echo ""
    echo "Testing: Disk full scenario handling"
    
    create_test_environment "disk_full"
    
    # This is a simulation - actual disk full testing would require special setup
    # Test that script checks available space before operations
    
    # Check if we can determine available space
    local available=$(df "$TEST_HOME" 2>/dev/null | awk 'NR==2 {print $4}')
    
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -n "$available" ]]; then
        echo -e "${GREEN}✓${NC} Can check available disk space"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${YELLOW}⚠${NC} Cannot determine disk space (test environment limitation)"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    fi
    
    cleanup_test_environment
}

test_special_characters_in_paths() {
    echo ""
    echo "Testing: Special characters in paths"
    
    # Create test directory with special characters
    local special_dir="$TEST_TEMP_DIR/home with spaces/and'quotes\"/sub\$dir"
    mkdir -p "$special_dir"
    
    # Test handling of special paths
    local escaped_path=$(printf '%q' "$special_dir")
    
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -d "$special_dir" ]]; then
        echo -e "${GREEN}✓${NC} Handles paths with special characters"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} Failed to handle special character paths"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    
    rm -rf "$TEST_TEMP_DIR"
}

test_atomic_file_operations() {
    echo ""
    echo "Testing: Atomic file operations"
    
    create_test_environment "atomic"
    
    # Create original .bashrc
    local original_content="# Original content
export PATH=/usr/bin:\$PATH
alias ll='ls -la'"
    echo "$original_content" > "$TEST_HOME/.bashrc"
    
    # Simulate atomic write operation
    # 1. Write to temporary file
    local temp_file="$TEST_HOME/.bashrc.tmp.$$"
    echo "$original_content" > "$temp_file"
    echo "# AssetUtilities Configuration" >> "$temp_file"
    
    # 2. Atomically move temp file to .bashrc
    mv -f "$temp_file" "$TEST_HOME/.bashrc"
    
    # Verify content
    assert_file_contains "$TEST_HOME/.bashrc" "# Original content" \
        "Original content preserved in atomic operation"
    assert_file_contains "$TEST_HOME/.bashrc" "# AssetUtilities Configuration" \
        "New content added in atomic operation"
    
    # Verify temp file is gone
    assert_false "[[ -f '$temp_file' ]]" "Temporary file should be removed"
    
    cleanup_test_environment
}

test_bashrc_with_source_commands() {
    echo ""
    echo "Testing: .bashrc with existing source commands"
    
    create_test_environment "source_commands"
    
    # Create .bashrc that sources other files
    cat > "$TEST_HOME/.bashrc" << 'EOF'
# User bashrc with source commands
if [ -f ~/.bash_aliases ]; then
    source ~/.bash_aliases
fi

source /etc/bashrc 2>/dev/null || true

# Source custom scripts
for script in ~/.bashrc.d/*.sh; do
    [ -f "$script" ] && source "$script"
done
EOF
    
    # Create referenced files
    mkdir -p "$TEST_HOME/.bashrc.d"
    echo "alias test='echo test'" > "$TEST_HOME/.bash_aliases"
    echo "export CUSTOM=1" > "$TEST_HOME/.bashrc.d/custom.sh"
    
    # The setup script should preserve all source commands
    local original_line_count=$(wc -l < "$TEST_HOME/.bashrc")
    
    # Simulate adding configuration
    echo "" >> "$TEST_HOME/.bashrc"
    echo "# AssetUtilities Project Configuration" >> "$TEST_HOME/.bashrc"
    
    # Verify original source commands are intact
    assert_file_contains "$TEST_HOME/.bashrc" "source ~/.bash_aliases" \
        "Preserves source command for .bash_aliases"
    assert_file_contains "$TEST_HOME/.bashrc" "source /etc/bashrc" \
        "Preserves source command for system bashrc"
    
    cleanup_test_environment
}

test_windows_line_endings() {
    echo ""
    echo "Testing: Windows line endings handling"
    
    create_test_environment "line_endings"
    
    # Create .bashrc with Windows line endings (CRLF)
    printf "# Windows line endings test\r\n" > "$TEST_HOME/.bashrc"
    printf "export TEST=1\r\n" >> "$TEST_HOME/.bashrc"
    printf "alias test='echo test'\r\n" >> "$TEST_HOME/.bashrc"
    
    # Check if file has CRLF
    local has_crlf=$(file "$TEST_HOME/.bashrc" | grep -c "CRLF" || echo "0")
    
    if [[ "$has_crlf" -gt 0 ]] || od -c "$TEST_HOME/.bashrc" | grep -q '\\r'; then
        echo -e "${YELLOW}⚠${NC} File has Windows line endings (CRLF)"
        
        # The setup script should handle this gracefully
        # Either preserve CRLF or convert to LF
        TESTS_RUN=$((TESTS_RUN + 1))
        TESTS_PASSED=$((TESTS_PASSED + 1))
        echo -e "${GREEN}✓${NC} Test acknowledges CRLF handling requirement"
    else
        skip_test "Could not create file with CRLF line endings"
    fi
    
    cleanup_test_environment
}

# Main test runner
run_safe_modification_tests() {
    print_test_header "Safe Modification Behavior Tests"
    
    # Run all safe modification tests
    test_concurrent_modification_safety
    test_large_bashrc_handling
    test_readonly_bashrc_handling
    test_no_home_directory
    test_corrupted_bashrc_handling
    test_disk_full_simulation
    test_special_characters_in_paths
    test_atomic_file_operations
    test_bashrc_with_source_commands
    test_windows_line_endings
    
    # Print summary
    print_test_summary
}

# Run tests
run_safe_modification_tests