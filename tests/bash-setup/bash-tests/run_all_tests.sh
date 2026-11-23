#!/bin/bash

# Main test runner for all bash setup tests
# Executes all test suites and provides comprehensive results

# Setup
readonly SCRIPT_DIR="$(cd "$(dirname "$0")" && pwd)"
readonly PROJECT_ROOT="$(cd "$SCRIPT_DIR/../../.." && pwd)"

# Colors
readonly GREEN='\033[0;32m'
readonly RED='\033[0;31m'
readonly YELLOW='\033[1;33m'
readonly BLUE='\033[0;34m'
readonly PURPLE='\033[0;35m'
readonly NC='\033[0m'

# Test results
TOTAL_SUITES=0
PASSED_SUITES=0
FAILED_SUITES=0
TOTAL_TESTS=0
TOTAL_PASSED=0
TOTAL_FAILED=0
TOTAL_SKIPPED=0

# Print header
print_header() {
    echo -e "${BLUE}============================================${NC}"
    echo -e "${BLUE}AssetUtilities Bash Setup Test Suite${NC}"
    echo -e "${BLUE}============================================${NC}"
    echo ""
    echo "Running all bash setup tests..."
    echo "Project root: $PROJECT_ROOT"
    echo "Test directory: $SCRIPT_DIR"
    echo ""
}

# Run a single test suite
run_test_suite() {
    local test_file="$1"
    local test_name=$(basename "$test_file" .sh)
    
    echo -e "\n${PURPLE}Running test suite: $test_name${NC}"
    echo "----------------------------------------"
    
    TOTAL_SUITES=$((TOTAL_SUITES + 1))
    
    # Run the test and capture output
    local output_file=$(mktemp)
    local exit_code
    
    if bash "$test_file" > "$output_file" 2>&1; then
        exit_code=0
        PASSED_SUITES=$((PASSED_SUITES + 1))
        echo -e "${GREEN}✓ Suite passed${NC}"
    else
        exit_code=$?
        FAILED_SUITES=$((FAILED_SUITES + 1))
        echo -e "${RED}✗ Suite failed (exit code: $exit_code)${NC}"
    fi
    
    # Display output
    cat "$output_file"
    
    # Extract test statistics if available
    local suite_stats=$(grep -E "(Tests run:|Tests passed:|Tests failed:|Tests skipped:)" "$output_file")
    if [[ -n "$suite_stats" ]]; then
        local suite_run=$(echo "$suite_stats" | grep "Tests run:" | grep -o '[0-9]*' | head -1)
        local suite_passed=$(echo "$suite_stats" | grep "Tests passed:" | grep -o '[0-9]*' | head -1)
        local suite_failed=$(echo "$suite_stats" | grep "Tests failed:" | grep -o '[0-9]*' | head -1)
        local suite_skipped=$(echo "$suite_stats" | grep "Tests skipped:" | grep -o '[0-9]*' | head -1)
        
        TOTAL_TESTS=$((TOTAL_TESTS + ${suite_run:-0}))
        TOTAL_PASSED=$((TOTAL_PASSED + ${suite_passed:-0}))
        TOTAL_FAILED=$((TOTAL_FAILED + ${suite_failed:-0}))
        TOTAL_SKIPPED=$((TOTAL_SKIPPED + ${suite_skipped:-0}))
    fi
    
    # Clean up
    rm -f "$output_file"
    
    return $exit_code
}

# Find and run all test files
run_all_tests() {
    local failed_suites=()
    
    # Find all test files (excluding this runner and utilities)
    for test_file in "$SCRIPT_DIR"/test_*.sh; do
        # Skip if no test files found
        [[ ! -f "$test_file" ]] && continue
        
        # Skip test_utils.sh
        [[ "$(basename "$test_file")" == "test_utils.sh" ]] && continue
        
        # Make sure test file is executable
        chmod +x "$test_file"
        
        # Run the test suite
        if ! run_test_suite "$test_file"; then
            failed_suites+=("$(basename "$test_file")")
        fi
    done
    
    # Return failed suite names if any
    if [[ ${#failed_suites[@]} -gt 0 ]]; then
        echo -e "\n${RED}Failed test suites:${NC}"
        for suite in "${failed_suites[@]}"; do
            echo "  - $suite"
        done
    fi
}

# Print final summary
print_summary() {
    echo -e "\n${BLUE}============================================${NC}"
    echo -e "${BLUE}Test Execution Summary${NC}"
    echo -e "${BLUE}============================================${NC}"
    
    echo ""
    echo "Test Suites:"
    echo "  Total: $TOTAL_SUITES"
    echo -e "  Passed: ${GREEN}$PASSED_SUITES${NC}"
    echo -e "  Failed: ${RED}$FAILED_SUITES${NC}"
    
    echo ""
    echo "Individual Tests:"
    echo "  Total: $TOTAL_TESTS"
    echo -e "  Passed: ${GREEN}$TOTAL_PASSED${NC}"
    echo -e "  Failed: ${RED}$TOTAL_FAILED${NC}"
    
    if [[ $TOTAL_SKIPPED -gt 0 ]]; then
        echo -e "  Skipped: ${YELLOW}$TOTAL_SKIPPED${NC}"
    fi
    
    echo ""
    
    if [[ $FAILED_SUITES -eq 0 ]]; then
        echo -e "${GREEN}✓ All test suites passed!${NC}"
        return 0
    else
        echo -e "${RED}✗ Some test suites failed!${NC}"
        return 1
    fi
}

# Check prerequisites
check_prerequisites() {
    local missing_prereqs=()
    
    # Check for bash
    if ! command -v bash >/dev/null 2>&1; then
        missing_prereqs+=("bash")
    fi
    
    # Check for setup script
    if [[ ! -f "$PROJECT_ROOT/scripts/setup-gitbash.sh" ]]; then
        missing_prereqs+=("setup-gitbash.sh script")
    fi
    
    # Check for test utilities
    if [[ ! -f "$SCRIPT_DIR/test_utils.sh" ]]; then
        echo -e "${YELLOW}Warning: test_utils.sh not found. Some tests may have limited functionality.${NC}"
    fi
    
    if [[ ${#missing_prereqs[@]} -gt 0 ]]; then
        echo -e "${RED}Missing prerequisites:${NC}"
        for prereq in "${missing_prereqs[@]}"; do
            echo "  - $prereq"
        done
        echo ""
        echo "Please ensure all prerequisites are installed before running tests."
        return 1
    fi
    
    return 0
}

# Main execution
main() {
    print_header
    
    # Check prerequisites
    if ! check_prerequisites; then
        exit 1
    fi
    
    # Make all test scripts executable
    find "$SCRIPT_DIR" -name "*.sh" -type f -exec chmod +x {} \;
    
    # Run all tests
    run_all_tests
    
    # Print summary
    print_summary
    local exit_code=$?
    
    # Additional information
    echo ""
    echo "Test execution completed at: $(date)"
    echo ""
    
    exit $exit_code
}

# Handle script arguments
case "${1:-}" in
    "--help"|"-h")
        echo "Usage: $0 [OPTIONS]"
        echo ""
        echo "Run all bash setup test suites"
        echo ""
        echo "Options:"
        echo "  -h, --help     Show this help message"
        echo "  -v, --verbose  Show verbose output"
        echo "  -f, --filter   Run only tests matching pattern"
        echo ""
        echo "Examples:"
        echo "  $0                    # Run all tests"
        echo "  $0 -f backup          # Run only backup tests"
        echo ""
        exit 0
        ;;
    "--verbose"|"-v")
        set -x  # Enable verbose mode
        main
        ;;
    "--filter"|"-f")
        # TODO: Implement test filtering
        echo "Test filtering not yet implemented"
        exit 1
        ;;
    *)
        main
        ;;
esac