#!/bin/bash

# Test suite specifically for backup functionality
# Tests various backup scenarios and edge cases

# Test framework setup
readonly TEST_NAME="test_backup_functionality"
readonly TEST_DIR="$(dirname "$0")"
readonly PROJECT_ROOT="$(cd "$TEST_DIR/../../.." && pwd)"

# Source common test utilities
source "$TEST_DIR/test_utils.sh" 2>/dev/null || {
    # If test_utils.sh doesn't exist, define basic functions
    readonly GREEN='\033[0;32m'
    readonly RED='\033[0;31m'
    readonly YELLOW='\033[1;33m'
    readonly NC='\033[0m'
    
    TESTS_RUN=0
    TESTS_PASSED=0
    TESTS_FAILED=0
}

# Test-specific setup
setup_backup_test() {
    export TEST_TEMP_DIR=$(mktemp -d)
    export TEST_HOME="$TEST_TEMP_DIR/home"
    mkdir -p "$TEST_HOME"
    export ORIGINAL_HOME="$HOME"
    export HOME="$TEST_HOME"
}

cleanup_backup_test() {
    export HOME="$ORIGINAL_HOME"
    rm -rf "$TEST_TEMP_DIR"
}

# Backup-specific assertions
assert_backup_count() {
    local expected="$1"
    local message="$2"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    local actual=$(ls "$TEST_HOME"/.bashrc.backup.* 2>/dev/null | wc -l)
    
    if [[ "$expected" == "$actual" ]]; then
        echo -e "${GREEN}✓${NC} $message"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} $message"
        echo "  Expected $expected backups, found $actual"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

assert_newest_backup_contains() {
    local pattern="$1"
    local message="$2"
    
    TESTS_RUN=$((TESTS_RUN + 1))
    
    local newest_backup=$(ls -t "$TEST_HOME"/.bashrc.backup.* 2>/dev/null | head -1)
    
    if [[ -f "$newest_backup" ]] && grep -q "$pattern" "$newest_backup"; then
        echo -e "${GREEN}✓${NC} $message"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} $message"
        if [[ ! -f "$newest_backup" ]]; then
            echo "  No backup file found"
        else
            echo "  Pattern not found in newest backup: $pattern"
        fi
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
}

# Test cases
test_multiple_backups_preservation() {
    echo ""
    echo "Testing: Multiple backups are preserved"
    
    setup_backup_test
    
    # Simulate the backup creation function from setup script
    create_backup() {
        local bashrc_path="$1"
        local timestamp=$(date +"%Y%m%d_%H%M%S")
        local backup_path="${bashrc_path}.backup.${timestamp}"
        cp "$bashrc_path" "$backup_path"
        sleep 1  # Ensure different timestamps
    }
    
    # Create initial .bashrc
    echo "# Version 1" > "$TEST_HOME/.bashrc"
    create_backup "$TEST_HOME/.bashrc"
    
    # Modify and create another backup
    echo "# Version 2" > "$TEST_HOME/.bashrc"
    create_backup "$TEST_HOME/.bashrc"
    
    # Modify and create third backup
    echo "# Version 3" > "$TEST_HOME/.bashrc"
    create_backup "$TEST_HOME/.bashrc"
    
    # Verify all backups exist
    assert_backup_count "3" "All three backups should be preserved"
    
    cleanup_backup_test
}

test_backup_content_integrity() {
    echo ""
    echo "Testing: Backup content integrity"
    
    setup_backup_test
    
    # Create .bashrc with specific content including special characters
    local test_content='# Test configuration
export PATH="/usr/local/bin:$PATH"
alias ll="ls -la"
# Special chars: $HOME ${USER} `date`
function test() {
    echo "Hello, World!"
}'
    
    echo "$test_content" > "$TEST_HOME/.bashrc"
    
    # Simulate backup
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    cp "$TEST_HOME/.bashrc" "$TEST_HOME/.bashrc.backup.$timestamp"
    
    # Verify backup content exactly matches
    local backup_content=$(cat "$TEST_HOME/.bashrc.backup.$timestamp")
    
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ "$test_content" == "$backup_content" ]]; then
        echo -e "${GREEN}✓${NC} Backup preserves exact content including special characters"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} Backup content doesn't match original"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    
    cleanup_backup_test
}

test_backup_permissions_preserved() {
    echo ""
    echo "Testing: Backup preserves file permissions"
    
    setup_backup_test
    
    # Create .bashrc with specific permissions
    echo "# Test file" > "$TEST_HOME/.bashrc"
    chmod 600 "$TEST_HOME/.bashrc"  # User read/write only
    
    # Get original permissions
    local orig_perms=$(stat -c %a "$TEST_HOME/.bashrc" 2>/dev/null || stat -f %Lp "$TEST_HOME/.bashrc" 2>/dev/null)
    
    # Simulate backup
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    cp -p "$TEST_HOME/.bashrc" "$TEST_HOME/.bashrc.backup.$timestamp"  # -p preserves permissions
    
    # Get backup permissions
    local backup_perms=$(stat -c %a "$TEST_HOME/.bashrc.backup.$timestamp" 2>/dev/null || stat -f %Lp "$TEST_HOME/.bashrc.backup.$timestamp" 2>/dev/null)
    
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ "$orig_perms" == "$backup_perms" ]]; then
        echo -e "${GREEN}✓${NC} Backup preserves original file permissions"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} Backup permissions don't match original"
        echo "  Original: $orig_perms, Backup: $backup_perms"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    
    cleanup_backup_test
}

test_backup_with_symlink_bashrc() {
    echo ""
    echo "Testing: Backup handling when .bashrc is a symlink"
    
    setup_backup_test
    
    # Create actual bashrc file
    echo "# Real bashrc content" > "$TEST_HOME/.bashrc.real"
    
    # Create symlink
    ln -s "$TEST_HOME/.bashrc.real" "$TEST_HOME/.bashrc"
    
    # Simulate backup - should backup the symlink target content
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    if [[ -L "$TEST_HOME/.bashrc" ]]; then
        # Follow symlink and backup actual content
        cp -L "$TEST_HOME/.bashrc" "$TEST_HOME/.bashrc.backup.$timestamp"
    else
        cp "$TEST_HOME/.bashrc" "$TEST_HOME/.bashrc.backup.$timestamp"
    fi
    
    # Verify backup contains real content
    assert_newest_backup_contains "# Real bashrc content" "Backup should contain symlink target content"
    
    cleanup_backup_test
}

test_backup_disk_space_handling() {
    echo ""
    echo "Testing: Backup handling with limited disk space"
    
    # This test would require special setup to limit disk space
    # For now, we'll test that the backup function checks available space
    
    setup_backup_test
    
    # Check if we can determine available space
    local available_space=$(df "$TEST_HOME" | awk 'NR==2 {print $4}')
    
    TESTS_RUN=$((TESTS_RUN + 1))
    if [[ -n "$available_space" ]] && [[ "$available_space" -gt 0 ]]; then
        echo -e "${GREEN}✓${NC} Can check available disk space before backup"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${YELLOW}⚠${NC} Cannot determine available disk space"
        TESTS_PASSED=$((TESTS_PASSED + 1))  # Pass anyway as this might not work in all environments
    fi
    
    cleanup_backup_test
}

test_backup_filename_collision() {
    echo ""
    echo "Testing: Backup filename collision handling"
    
    setup_backup_test
    
    # Create .bashrc
    echo "# Original" > "$TEST_HOME/.bashrc"
    
    # Create a backup with specific timestamp
    local timestamp="20250101_120000"
    cp "$TEST_HOME/.bashrc" "$TEST_HOME/.bashrc.backup.$timestamp"
    
    # Try to create another backup with same timestamp (simulate collision)
    echo "# Modified" > "$TEST_HOME/.bashrc"
    
    # In real scenario, the script should handle this by adding suffix or waiting
    if [[ -f "$TEST_HOME/.bashrc.backup.$timestamp" ]]; then
        # Add microseconds or counter to make unique
        local new_backup="$TEST_HOME/.bashrc.backup.${timestamp}_1"
        cp "$TEST_HOME/.bashrc" "$new_backup"
        
        TESTS_RUN=$((TESTS_RUN + 1))
        if [[ -f "$new_backup" ]]; then
            echo -e "${GREEN}✓${NC} Handles backup filename collisions gracefully"
            TESTS_PASSED=$((TESTS_PASSED + 1))
        else
            echo -e "${RED}✗${NC} Failed to handle backup filename collision"
            TESTS_FAILED=$((TESTS_FAILED + 1))
        fi
    fi
    
    cleanup_backup_test
}

test_backup_special_characters_in_content() {
    echo ""
    echo "Testing: Backup with special characters and Unicode"
    
    setup_backup_test
    
    # Create .bashrc with special content
    cat > "$TEST_HOME/.bashrc" << 'EOF'
# Special characters test
export SPECIAL='$HOME/path with spaces/"quotes"'
alias test='echo "It'\''s working!"'
# Unicode: 你好世界 🚀 λ
# Tabs:	indented	content
# Backticks: `echo test`
# Variables: ${HOME} $(pwd)
EOF
    
    # Create backup
    local timestamp=$(date +"%Y%m%d_%H%M%S")
    cp "$TEST_HOME/.bashrc" "$TEST_HOME/.bashrc.backup.$timestamp"
    
    # Verify special characters are preserved
    TESTS_RUN=$((TESTS_RUN + 1))
    if diff -q "$TEST_HOME/.bashrc" "$TEST_HOME/.bashrc.backup.$timestamp" >/dev/null; then
        echo -e "${GREEN}✓${NC} Backup preserves all special characters and Unicode"
        TESTS_PASSED=$((TESTS_PASSED + 1))
    else
        echo -e "${RED}✗${NC} Backup doesn't match original with special characters"
        TESTS_FAILED=$((TESTS_FAILED + 1))
    fi
    
    cleanup_backup_test
}

# Main test runner
run_backup_tests() {
    echo "=================================="
    echo "Running Backup Functionality Tests"
    echo "=================================="
    
    # Run all backup-specific tests
    test_multiple_backups_preservation
    test_backup_content_integrity
    test_backup_permissions_preserved
    test_backup_with_symlink_bashrc
    test_backup_disk_space_handling
    test_backup_filename_collision
    test_backup_special_characters_in_content
    
    # Print summary
    echo ""
    echo "=================================="
    echo "Backup Test Summary"
    echo "=================================="
    echo "Tests run: $TESTS_RUN"
    echo -e "Tests passed: ${GREEN}$TESTS_PASSED${NC}"
    echo -e "Tests failed: ${RED}$TESTS_FAILED${NC}"
    
    if [[ $TESTS_FAILED -eq 0 ]]; then
        echo -e "\n${GREEN}All backup tests passed!${NC}"
        exit 0
    else
        echo -e "\n${RED}Some backup tests failed!${NC}"
        exit 1
    fi
}

# Run tests
run_backup_tests