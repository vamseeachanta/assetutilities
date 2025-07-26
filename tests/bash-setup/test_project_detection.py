#!/usr/bin/env python3
"""
Test suite for project directory detection logic.
Tests the core functionality that determines if we're in an AssetUtilities project.
"""

import os
import tempfile
import shutil
from pathlib import Path
import pytest


class TestProjectDetection:
    """Test cases for AssetUtilities project detection."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.test_dir = tempfile.mkdtemp()
        self.original_cwd = os.getcwd()
        
    def teardown_method(self):
        """Clean up test environment after each test."""
        os.chdir(self.original_cwd)
        shutil.rmtree(self.test_dir, ignore_errors=True)
    
    def test_valid_assetutilities_project(self):
        """Test detection of valid AssetUtilities project structure."""
        # Create complete AssetUtilities project structure
        project_dir = Path(self.test_dir) / "assetutilities"
        project_dir.mkdir()
        
        # Create Git repository
        git_dir = project_dir / ".git"
        git_dir.mkdir()
        
        # Create Python package structure
        src_dir = project_dir / "src" / "assetutilities"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").touch()
        
        # Create setup files
        (project_dir / "setup.py").touch()
        (project_dir / "pyproject.toml").touch()
        
        os.chdir(project_dir)
        
        assert self._is_assetutilities_project(), "Should detect valid AssetUtilities project"
    
    def test_project_with_only_setup_py(self):
        """Test detection with only setup.py present."""
        project_dir = Path(self.test_dir) / "assetutilities"
        project_dir.mkdir()
        
        (project_dir / ".git").mkdir()
        (project_dir / "setup.py").touch()
        
        os.chdir(project_dir)
        
        assert self._is_assetutilities_project(), "Should detect project with setup.py"
    
    def test_project_with_only_src_structure(self):
        """Test detection with only src/assetutilities structure."""
        project_dir = Path(self.test_dir) / "assetutilities"
        project_dir.mkdir()
        
        (project_dir / ".git").mkdir()
        src_dir = project_dir / "src" / "assetutilities"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").touch()
        
        os.chdir(project_dir)
        
        assert self._is_assetutilities_project(), "Should detect project with src structure"
    
    def test_non_git_directory(self):
        """Test that non-git directories are not detected as projects."""
        project_dir = Path(self.test_dir) / "not-a-git-repo"
        project_dir.mkdir()
        
        # Create AssetUtilities structure but no .git
        (project_dir / "setup.py").touch()
        src_dir = project_dir / "src" / "assetutilities"
        src_dir.mkdir(parents=True)
        
        os.chdir(project_dir)
        
        assert not self._is_assetutilities_project(), "Should not detect non-git directory"
    
    def test_different_python_project(self):
        """Test that other Python projects are not detected as AssetUtilities."""
        project_dir = Path(self.test_dir) / "other-project"
        project_dir.mkdir()
        
        (project_dir / ".git").mkdir()
        (project_dir / "setup.py").touch()
        
        # Create different package structure
        src_dir = project_dir / "src" / "different_package"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").touch()
        
        os.chdir(project_dir)
        
        assert not self._is_assetutilities_project(), "Should not detect different Python project"
    
    def test_subdirectory_detection(self):
        """Test detection when in project subdirectory."""
        project_dir = Path(self.test_dir) / "assetutilities"
        project_dir.mkdir()
        
        (project_dir / ".git").mkdir()
        (project_dir / "setup.py").touch()
        
        # Create and navigate to subdirectory
        sub_dir = project_dir / "tests" / "unit"
        sub_dir.mkdir(parents=True)
        os.chdir(sub_dir)
        
        assert self._is_assetutilities_project(), "Should detect project from subdirectory"
    
    def test_parent_directory_traversal(self):
        """Test that detection works by traversing up to find project root."""
        project_dir = Path(self.test_dir) / "assetutilities"
        project_dir.mkdir()
        
        (project_dir / ".git").mkdir()
        src_dir = project_dir / "src" / "assetutilities"
        src_dir.mkdir(parents=True)
        (src_dir / "__init__.py").touch()
        
        # Navigate to deeply nested directory
        deep_dir = project_dir / "docs" / "examples" / "data" / "processing"
        deep_dir.mkdir(parents=True)
        os.chdir(deep_dir)
        
        assert self._is_assetutilities_project(), "Should find project root from deep directory"
    
    def test_project_root_finding(self):
        """Test that project root is correctly identified."""
        project_dir = Path(self.test_dir) / "assetutilities"
        project_dir.mkdir()
        
        (project_dir / ".git").mkdir()
        (project_dir / "setup.py").touch()
        
        sub_dir = project_dir / "src" / "assetutilities"
        sub_dir.mkdir(parents=True)
        os.chdir(sub_dir)
        
        root = self._find_project_root()
        assert root == project_dir, f"Should find correct project root: {project_dir}, got: {root}"
    
    def test_no_project_found(self):
        """Test behavior when no project is found."""
        # Navigate to a directory that's not in any project
        temp_dir = Path(self.test_dir) / "random-directory"
        temp_dir.mkdir()
        os.chdir(temp_dir)
        
        assert not self._is_assetutilities_project(), "Should not find project in random directory"
        assert self._find_project_root() is None, "Should return None when no project found"
    
    def _is_assetutilities_project(self):
        """
        Implementation of project detection logic.
        This simulates the actual bash logic that will be implemented.
        """
        current_dir = Path.cwd()
        
        # Traverse up the directory tree looking for project markers
        for path in [current_dir] + list(current_dir.parents):
            # Check for Git repository
            if not (path / ".git").exists():
                continue
                
            # Check for AssetUtilities-specific markers
            has_setup = (path / "setup.py").exists()
            has_pyproject = (path / "pyproject.toml").exists()
            has_src_package = (path / "src" / "assetutilities").exists()
            
            # Check if directory name indicates AssetUtilities
            dir_name = path.name.lower()
            has_assetutilities_name = "assetutilities" in dir_name
            
            # Check content of setup files for AssetUtilities references
            has_content_match = False
            if has_setup:
                try:
                    setup_content = (path / "setup.py").read_text()
                    if "assetutilities" in setup_content.lower():
                        has_content_match = True
                except:
                    pass
            
            if has_pyproject:
                try:
                    pyproject_content = (path / "pyproject.toml").read_text()
                    if "assetutilities" in pyproject_content.lower():
                        has_content_match = True
                except:
                    pass
            
            # Must have AssetUtilities-specific evidence
            if (has_setup or has_pyproject or has_src_package) and (has_assetutilities_name or has_content_match or has_src_package):
                return True
                
        return False
    
    def _find_project_root(self):
        """
        Find the root directory of the AssetUtilities project.
        Returns Path object or None if not found.
        """
        current_dir = Path.cwd()
        
        for path in [current_dir] + list(current_dir.parents):
            if not (path / ".git").exists():
                continue
                
            has_setup = (path / "setup.py").exists()
            has_pyproject = (path / "pyproject.toml").exists()
            has_src_package = (path / "src" / "assetutilities").exists()
            
            # Check if directory name indicates AssetUtilities
            dir_name = path.name.lower()
            has_assetutilities_name = "assetutilities" in dir_name
            
            # Check content matches
            has_content_match = False
            if has_setup:
                try:
                    setup_content = (path / "setup.py").read_text()
                    if "assetutilities" in setup_content.lower():
                        has_content_match = True
                except:
                    pass
            
            if has_pyproject:
                try:
                    pyproject_content = (path / "pyproject.toml").read_text()
                    if "assetutilities" in pyproject_content.lower():
                        has_content_match = True
                except:
                    pass
            
            if (has_setup or has_pyproject or has_src_package) and (has_assetutilities_name or has_content_match or has_src_package):
                return path
                
        return None


if __name__ == "__main__":
    pytest.main([__file__])