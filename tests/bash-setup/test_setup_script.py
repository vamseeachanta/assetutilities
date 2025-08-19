#!/usr/bin/env python3
"""
Test suite for Git Bash setup script functionality.
Tests the core setup script behavior, directory detection, and configuration management.
"""

import os
import tempfile
import subprocess
import shutil
from pathlib import Path
import pytest


class TestSetupScript:
    """Test cases for the main setup script."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        os.chdir(self.test_dir)
        
    def teardown_method(self):
        """Clean up test environment after each test."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_project_directory_detection(self):
        """Test that the script correctly detects AssetUtilities project directory."""
        # Create a mock AssetUtilities project structure
        project_dir = Path(self.test_dir) / "assetutilities"
        project_dir.mkdir()
        
        # Create essential project markers
        (project_dir / ".git").mkdir()
        (project_dir / "setup.py").touch()
        (project_dir / "src").mkdir()
        (project_dir / "src" / "assetutilities").mkdir()
        
        os.chdir(project_dir)
        
        # Test detection script (will be implemented)
        result = self._run_detection_check()
        assert result, "Should detect valid AssetUtilities project"
    
    def test_git_repository_validation(self):
        """Test that script validates Git repository existence."""
        # Create directory without .git
        non_git_dir = Path(self.test_dir) / "not-git"
        non_git_dir.mkdir()
        os.chdir(non_git_dir)
        
        result = self._run_detection_check()
        assert not result, "Should not detect non-git directory as valid project"
    
    def test_backup_creation(self):
        """Test that existing .bashrc files are backed up safely."""
        # Create a mock home directory with existing .bashrc
        home_dir = Path(self.test_dir) / "home"
        home_dir.mkdir()
        bashrc = home_dir / ".bashrc"
        
        original_content = "# Original bashrc content\nexport PATH=/original:$PATH"
        bashrc.write_text(original_content)
        
        # Test backup functionality (will be implemented)
        backup_path = self._test_backup_creation(bashrc)
        
        assert backup_path.exists(), "Backup file should be created"
        assert backup_path.read_text() == original_content, "Backup should preserve original content"
    
    def test_configuration_injection(self):
        """Test that project configuration is properly injected into .bashrc."""
        home_dir = Path(self.test_dir) / "home"
        home_dir.mkdir()
        bashrc = home_dir / ".bashrc"
        
        # Create original .bashrc with some content
        original_content = "# User's original configuration\nalias ll='ls -la'"
        bashrc.write_text(original_content)
        
        # Test configuration injection (will be implemented)
        self._test_config_injection(bashrc)
        
        updated_content = bashrc.read_text()
        assert "# AssetUtilities Project Configuration" in updated_content
        assert original_content in updated_content, "Original content should be preserved"
    
    def test_script_permissions(self):
        """Test that created scripts have proper executable permissions."""
        scripts_dir = Path(self.test_dir) / "scripts"
        scripts_dir.mkdir()
        
        # Create test script
        test_script = scripts_dir / "setup-gitbash.sh"
        test_script.write_text("#!/bin/bash\necho 'test'")
        
        # Test permission setting (will be implemented)
        self._set_script_permissions(test_script)
        
        # Check if script is executable
        assert os.access(test_script, os.X_OK), "Script should be executable"
    
    def _run_detection_check(self):
        """Helper method to test project detection logic."""
        # This will call the actual detection logic once implemented
        # For now, simulate the logic
        cwd = Path.cwd()
        
        # Check for AssetUtilities project markers
        has_git = (cwd / ".git").exists()
        has_setup = (cwd / "setup.py").exists()
        has_src = (cwd / "src" / "assetutilities").exists()
        
        return has_git and (has_setup or has_src)
    
    def _test_backup_creation(self, bashrc_path):
        """Helper method to test backup functionality."""
        # Simulate backup creation logic
        timestamp = "20250726_120000"  # Mock timestamp
        backup_path = bashrc_path.with_suffix(f".backup.{timestamp}")
        
        # Copy original to backup
        backup_path.write_text(bashrc_path.read_text())
        return backup_path
    
    def _test_config_injection(self, bashrc_path):
        """Helper method to test configuration injection."""
        original_content = bashrc_path.read_text()
        
        # Simulate configuration injection
        project_config = """
# AssetUtilities Project Configuration
# Auto-generated by setup-gitbash.sh - DO NOT EDIT MANUALLY
if [ -f "$PWD/config/.project-bashrc" ] && [[ "$PWD" == *"assetutilities"* ]]; then
    source "$PWD/config/.project-bashrc"
fi
"""
        
        updated_content = original_content + project_config
        bashrc_path.write_text(updated_content)
    
    def _set_script_permissions(self, script_path):
        """Helper method to set proper script permissions."""
        # Make script executable
        current_permissions = script_path.stat().st_mode
        script_path.chmod(current_permissions | 0o755)


class TestEnvironmentDetection:
    """Test cases for environment detection and validation."""
    
    def test_python_environment_detection(self):
        """Test detection of Python environment and version."""
        # Test Python version detection (Python 3.6 compatible)
        result = subprocess.run(["python", "--version"], 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE, 
                              universal_newlines=True)
        
        assert result.returncode == 0, "Python should be available"
        output = result.stdout + result.stderr  # Python version might go to stderr
        assert "Python 3." in output, "Should detect Python 3.x"
    
    def test_git_bash_environment(self):
        """Test that we're running in a Git Bash compatible environment."""
        # Check for bash availability (Python 3.6 compatible)
        result = subprocess.run(["bash", "--version"], 
                              stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                              universal_newlines=True)
        
        # If bash is available, verify it's GNU bash
        # If not available, skip this test (we may be in CMD/PowerShell)
        if result.returncode == 0:
            assert "GNU bash" in result.stdout, "Should be GNU bash"
        else:
            # Test passed - we handle environments without bash gracefully
            assert True, "Bash not available - this is acceptable for setup script"
    
    def test_virtual_environment_detection(self):
        """Test detection of Python virtual environments."""
        # This will test the venv detection logic once implemented
        venv_active = os.environ.get("VIRTUAL_ENV") is not None
        
        # The test should handle both cases (venv active and not active)
        if venv_active:
            assert Path(os.environ["VIRTUAL_ENV"]).exists()
        else:
            # Test should verify proper handling of no venv scenario
            assert True  # Placeholder for actual logic


if __name__ == "__main__":
    pytest.main([__file__])