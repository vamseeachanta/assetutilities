# Bash Setup Tests

This directory contains comprehensive bash test suites for testing the Git Bash setup script functionality, specifically focusing on .bashrc modification and backup operations.

## Test Structure

```
bash-tests/
├── README.md                      # This file
├── run_all_tests.sh              # Main test runner
├── test_utils.sh                 # Shared test utilities
├── test_bashrc_modification.sh   # Core .bashrc modification tests
├── test_backup_functionality.sh  # Backup-specific tests
└── test_safe_modification.sh     # Safety and edge case tests
```

## Running Tests

### Run All Tests
```bash
cd tests/bash-setup/bash-tests
./run_all_tests.sh
```

### Run Individual Test Suites
```bash
# Run only .bashrc modification tests
./test_bashrc_modification.sh

# Run only backup functionality tests
./test_backup_functionality.sh

# Run only safe modification tests
./test_safe_modification.sh
```

### Test Output
Tests will output:
- ✓ Green checkmarks for passed tests
- ✗ Red X marks for failed tests
- ⚠ Yellow warnings for skipped tests
- Detailed error messages for failures
- Summary statistics at the end

## Test Coverage

### test_bashrc_modification.sh
Tests core functionality:
- Backup creation for new and existing .bashrc files
- Configuration injection into .bashrc
- Idempotent installation (no duplicates)
- Permission handling
- Backup timestamp formatting
- Configuration removal (uninstall)
- Empty file handling

### test_backup_functionality.sh
Tests backup-specific features:
- Multiple backup preservation
- Content integrity with special characters
- Permission preservation
- Symlink handling
- Disk space checks
- Filename collision handling
- Unicode and special character support

### test_safe_modification.sh
Tests safety mechanisms and edge cases:
- Concurrent modification safety
- Large file handling
- Read-only file handling
- Missing HOME directory
- Corrupted file handling
- Disk full scenarios
- Special characters in paths
- Atomic operations
- Existing source commands preservation
- Windows line ending handling

## Test Environment

Tests create isolated temporary environments for each test case:
- Temporary HOME directory
- Mock project structure
- Clean environment variables
- No interference with actual user configuration

## Writing New Tests

To add new tests:

1. Create a new test file or add to existing ones
2. Source `test_utils.sh` for common utilities
3. Use assertion functions:
   ```bash
   assert_equals "expected" "actual" "Test description"
   assert_file_exists "/path/to/file" "File should exist"
   assert_file_contains "/path/to/file" "pattern" "Should contain pattern"
   ```
4. Follow the test structure:
   ```bash
   test_my_feature() {
       echo ""
       echo "Testing: My feature description"
       
       create_test_environment "my_test"
       
       # Test implementation
       
       cleanup_test_environment
   }
   ```

## Requirements

- Git Bash (or compatible bash environment)
- Basic Unix utilities (grep, sed, awk, etc.)
- Write permissions in temp directory
- The main setup-gitbash.sh script must exist

## Platform Support

Tests are designed to work on:
- Windows Git Bash (primary target)
- WSL (Windows Subsystem for Linux)
- macOS (with adaptations)
- Linux (with adaptations)

Platform-specific behavior is handled by utility functions in `test_utils.sh`.

## Continuous Integration

These tests can be integrated into CI/CD pipelines:
```yaml
# Example GitHub Actions step
- name: Run Bash Setup Tests
  run: |
    cd tests/bash-setup/bash-tests
    ./run_all_tests.sh
```

## Troubleshooting

### Tests fail with "command not found"
Ensure you're running in Git Bash or a compatible bash environment.

### Permission denied errors
Make scripts executable:
```bash
chmod +x *.sh
```

### Tests can't find setup script
Ensure you're running from the correct directory and the main setup script exists at:
`scripts/setup-gitbash.sh`

### Temporary directory issues
Check that your system's temp directory is writable and has sufficient space.

## Contributing

When adding new tests:
1. Ensure tests are isolated and don't affect the host system
2. Clean up all temporary files and directories
3. Use descriptive test names and messages
4. Follow existing patterns and conventions
5. Update this README if adding new test categories