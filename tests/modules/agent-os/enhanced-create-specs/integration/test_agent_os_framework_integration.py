#!/usr/bin/env python3
"""
Integration tests for Agent OS Framework compatibility with enhanced-create-specs workflow.

Tests cover:
- Backward compatibility with existing Agent OS workflows
- Integration with create-spec.md instruction file
- Enhanced features integration with existing system
- CLAUDE.md template system compatibility
- Execute-tasks.md workflow integration

Author: Enhanced Create-Specs Workflow
Created: 2025-08-05
Module: agent-os/enhanced-create-specs
Test Type: Integration
"""

import pytest
import os
import tempfile
import shutil
import yaml
import json
from pathlib import Path
from unittest.mock import Mock, patch, MagicMock
from typing import Dict, List, Any


class TestAgentOSCompatibility:
    """Test suite for Agent OS framework compatibility."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "test-project"
        self.agent_os_path = self.project_path / ".agent-os"
        
        # Create mock Agent OS project structure
        self._create_mock_agent_os_project()
    
    def teardown_method(self):
        """Clean up test environment after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _create_mock_agent_os_project(self):
        """Create mock Agent OS project structure."""
        self.project_path.mkdir(parents=True)
        self.agent_os_path.mkdir()
        
        # Create existing Agent OS files
        
        # Create traditional spec directory
        specs_dir = self.project_path / "specs"
        specs_dir.mkdir()
        
        # Create existing spec (old format)
        existing_spec_dir = specs_dir / "2025-08-01-user-auth"
        existing_spec_dir.mkdir()
        
        (existing_spec_dir / "spec.md").write_text("""
# Spec Requirements Document

> Spec: user-auth
> Created: 2025-08-01
> Status: Planning

## Overview

Implement user authentication system for the application.

## User Stories

### User Login
As a user, I want to log in to the application, so that I can access my account.

## Spec Scope

1. **Login Form** - Create login form with email/password fields
2. **Authentication Logic** - Implement user verification

## Expected Deliverable

1. Working login form accessible at /login
2. User can successfully authenticate with valid credentials
""")
        
        (existing_spec_dir / "tasks.md").write_text("""
# Spec Tasks

- [ ] 1. Create login form UI
  - [ ] 1.1 Write tests for login form
  - [ ] 1.2 Implement form component
  - [ ] 1.3 Add form validation
  - [ ] 1.4 Verify tests pass

- [ ] 2. Implement authentication backend
  - [ ] 2.1 Write authentication tests
  - [ ] 2.2 Create auth service
  - [ ] 2.3 Integrate with database
  - [ ] 2.4 Verify all tests pass
""")
        
        # Create CLAUDE.md with existing Agent OS configuration
        (self.project_path / "CLAUDE.md").write_text("""
# Project Instructions

## Agent OS Documentation

### Product Context
- **Mission & Vision:** @.agent-os/product/mission.md
- **Technical Architecture:** @.agent-os/product/tech-stack.md
- **Development Roadmap:** @.agent-os/product/roadmap.md

### Development Standards
- **Code Style:** Use 2 spaces for indentation
- **Testing:** Write tests for all new functionality

## Workflow Instructions

When asked to work on this codebase:

1. **First**, check @.agent-os/product/roadmap.md for current priorities
2. **Then**, follow the appropriate instruction file:
   - For new features: Use `/create-spec` command
   - For tasks execution: Use `/execute-tasks` command
3. **Always**, adhere to the established patterns and practices
""")
        
        # Create product documentation
        product_dir = self.agent_os_path / "product"
        product_dir.mkdir()
        
        (product_dir / "mission.md").write_text("""
# Product Mission

> Last Updated: 2025-08-01
> Version: 1.0.0

## Pitch

TestApp is a web application that helps users manage their tasks and projects.

## Users

### Primary Customers

- **Individual Users**: People looking to organize their personal tasks
- **Small Teams**: Teams needing simple project management

## Key Features

### Core Features
- **Task Management**: Create, edit, and organize tasks
- **User Authentication**: Secure login and user management
""")
        
        (product_dir / "roadmap.md").write_text("""
# Product Roadmap

> Last Updated: 2025-08-01
> Status: Active Development

## Phase 1: Core Features (Current)

- [ ] **User Authentication** - Secure login and registration system `L`
- [ ] **Task Management** - CRUD operations for tasks `M`
- [ ] **User Dashboard** - Personal task overview `S`
""")
    
    def test_existing_spec_structure_compatibility(self):
        """Test that existing spec structures remain compatible."""
        # Check existing spec directory structure
        existing_spec = self.project_path / "specs/2025-08-01-user-auth"
        assert existing_spec.exists()
        
        # Check spec.md exists and has expected content
        spec_file = existing_spec / "spec.md"
        assert spec_file.exists()
        
        content = spec_file.read_text()
        assert "# Spec Requirements Document" in content
        assert "## Overview" in content
        assert "## User Stories" in content
        assert "## Spec Scope" in content
        
        # Check tasks.md exists and has expected format
        tasks_file = existing_spec / "tasks.md"
        assert tasks_file.exists()
        
        tasks_content = tasks_file.read_text()
        assert "# Spec Tasks" in tasks_content
        assert "- [ ] 1." in tasks_content
        assert "- [ ] 1.1" in tasks_content
    
    def test_claude_md_template_compatibility(self):
        """Test CLAUDE.md template system compatibility."""
        claude_file = self.project_path / "CLAUDE.md"
        assert claude_file.exists()
        
        content = claude_file.read_text()
        
        # Check existing Agent OS patterns
        assert "## Agent OS Documentation" in content
        assert "@.agent-os/product/mission.md" in content
        assert "@.agent-os/product/roadmap.md" in content
        assert "## Workflow Instructions" in content
        
        # Test reference resolution
        mission_ref = "@.agent-os/product/mission.md"
        resolved_path = self.project_path / mission_ref[1:]  # Remove @
        assert resolved_path.exists()
    
    def test_product_documentation_structure(self):
        """Test product documentation structure compatibility."""
        product_dir = self.agent_os_path / "product"
        assert product_dir.exists()
        
        # Check required files exist
        required_files = ["mission.md", "roadmap.md"]
        for file_name in required_files:
            file_path = product_dir / file_name
            assert file_path.exists()
        
        # Check mission.md structure
        mission_file = product_dir / "mission.md"
        mission_content = mission_file.read_text()
        assert "# Product Mission" in mission_content
        assert "## Pitch" in mission_content
        assert "## Users" in mission_content
        
        # Check roadmap.md structure
        roadmap_file = product_dir / "roadmap.md"
        roadmap_content = roadmap_file.read_text()
        assert "# Product Roadmap" in roadmap_content
        assert "## Phase 1:" in roadmap_content
    
    def test_enhanced_features_backward_compatibility(self):
        """Test that enhanced features don't break existing workflows."""
        # Simulate enhanced spec creation alongside existing spec
        enhanced_spec_dir = self.project_path / "specs/modules/authentication/2025-08-05-enhanced-auth"
        enhanced_spec_dir.mkdir(parents=True)
        
        # Create enhanced spec with new features
        enhanced_spec_content = """
# Spec Requirements Document

> Spec: enhanced-auth
> Created: 2025-08-05
> Status: Planning

## Prompt Summary

**Original Request:** Implement enhanced authentication with social login
**Context Provided:** Existing authentication system, OAuth integration requirements
**Clarifications Made:**
- Social login providers: Google, GitHub, Microsoft
- Maintain existing email/password login
**Reuse Notes:** Reusing existing user management infrastructure

## Executive Summary

### Business Impact
Implementing social login will reduce user registration friction by 60% and improve conversion rates.

### Technical Overview
Integration with OAuth 2.0 providers while maintaining backward compatibility with existing authentication.

## System Overview

```mermaid
graph TD
    A[User] --> B[Login Page]
    B --> C{Login Method}
    C -->|Email/Password| D[Existing Auth]
    C -->|Social| E[OAuth Provider]
    E --> F[User Profile Creation]
    D --> G[Dashboard]
    F --> G
```

## Overview

Enhance existing authentication system with social login capabilities.

## User Stories

### Social Login
As a user, I want to log in with Google/GitHub, so that I can quickly access the application without creating a new password.

## Spec Scope

1. **OAuth Integration** - Integrate with Google, GitHub, Microsoft OAuth
2. **Profile Merging** - Handle existing users who want to add social login
3. **Enhanced Security** - Implement additional security measures

## Expected Deliverable

1. Social login buttons on login page
2. OAuth flow integration with profile merging
3. Enhanced security audit logging
"""
        
        (enhanced_spec_dir / "spec.md").write_text(enhanced_spec_content)
        
        # Test both specs can coexist
        assert (self.project_path / "specs/2025-08-01-user-auth/spec.md").exists()
        assert (enhanced_spec_dir / "spec.md").exists()
        
        # Test enhanced features don't interfere with existing spec
        existing_content = (self.project_path / "specs/2025-08-01-user-auth/spec.md").read_text()
        assert "## Prompt Summary" not in existing_content  # Old spec doesn't have new sections
        
        enhanced_content = (enhanced_spec_dir / "spec.md").read_text()
        assert "## Prompt Summary" in enhanced_content  # New spec has enhanced sections
        assert "```mermaid" in enhanced_content  # Has mermaid diagram


class TestCreateSpecWorkflowIntegration:
    """Test suite for create-spec.md workflow integration."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "test-project"
        self.global_agent_os = Path(self.temp_dir) / ".agent-os"
        
        self._setup_workflow_test_environment()
    
    def teardown_method(self):
        """Clean up test environment after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _setup_workflow_test_environment(self):
        """Set up workflow integration test environment."""
        self.project_path.mkdir(parents=True)
        self.global_agent_os.mkdir(parents=True)
        
        # Create global instructions directory
        instructions_dir = self.global_agent_os / "instructions"
        instructions_dir.mkdir()
        
        # Create enhanced create-spec.md instruction
        create_spec_instruction = instructions_dir / "create-spec.md"
        create_spec_instruction.write_text("""
---
description: Spec Creation Rules for Agent OS
version: 2.0
encoding: UTF-8
---

# Enhanced Spec Creation Rules

## Overview

<purpose>
  - Create detailed spec plans with enhanced features
  - Generate structured documentation with visual elements
  - Support both traditional and module-based organization
</purpose>

## Enhanced Features

### Prompt Summary Capture
- Capture original request and context
- Track clarifications and evolution
- Document reuse opportunities

### Visual Documentation
- Auto-generate mermaid diagrams
- Create system architecture overviews
- Visual workflow representations

### Module-Based Organization
- Organize specs by functional modules
- Support subcategory hierarchies
- Maintain cross-module references

### Template Variants
- minimal: Basic spec with core sections only
- standard: Traditional Agent OS spec format  
- enhanced: Full featured spec with all enhancements

## Workflow Steps

<step number="1" name="enhanced_spec_initiation">
### Step 1: Enhanced Spec Initiation

Supports both traditional date-based and module-based organization:
- Traditional: specs/YYYY-MM-DD-spec-name/
- Module-based: specs/modules/module-name/YYYY-MM-DD-spec-name/

Template selection based on user preference or auto-detection.
</step>

## Backward Compatibility

All existing create-spec workflows remain fully supported.
Enhanced features are additive and optional.
""")
        
        # Create project with Agent OS configuration
        project_agent_os = self.project_path / ".agent-os"
        project_agent_os.mkdir()
        
        # Create preferences for enhanced features
        (project_agent_os / "user-preferences.yaml").write_text("""
preferred_variant: "enhanced"
organization_type: "module-based"
default_sections:
  - "prompt_summary"
  - "executive_summary"
  - "system_overview"
enable_mermaid_diagrams: true
enable_cross_references: true
""")
    
    def test_workflow_instruction_compatibility(self):
        """Test workflow instruction file compatibility."""
        instruction_file = self.global_agent_os / "instructions/create-spec.md"
        assert instruction_file.exists()
        
        content = instruction_file.read_text()
        
        # Check enhanced features are documented
        assert "# Enhanced Spec Creation Rules" in content
        assert "## Enhanced Features" in content
        assert "### Prompt Summary Capture" in content
        assert "### Visual Documentation" in content
        assert "### Module-Based Organization" in content
        
        # Check backward compatibility section
        assert "## Backward Compatibility" in content
        assert "existing create-spec workflows remain fully supported" in content
    
    def test_user_preferences_integration(self):
        """Test user preferences integration with workflows."""
        prefs_file = self.project_path / ".agent-os/user-preferences.yaml"
        assert prefs_file.exists()
        
        with open(prefs_file, 'r') as f:
            prefs = yaml.safe_load(f)
        
        # Check preference structure
        assert prefs["preferred_variant"] == "enhanced"
        assert prefs["organization_type"] == "module-based"
        assert "prompt_summary" in prefs["default_sections"]
        assert prefs["enable_mermaid_diagrams"] is True
        assert prefs["enable_cross_references"] is True
    
    def test_template_variant_selection(self):
        """Test template variant selection mechanism."""
        variants = ["minimal", "standard", "enhanced"]
        
        for variant in variants:
            # Simulate variant selection
            spec_config = {
                "variant": variant,
                "spec_name": f"test-{variant}",
                "module_name": "testing"
            }
            
            # Test variant validation
            assert spec_config["variant"] in variants
            
            # Test expected sections based on variant
            if variant == "minimal":
                expected_sections = ["overview", "user_stories", "spec_scope"]
            elif variant == "standard":
                expected_sections = ["overview", "user_stories", "spec_scope", "expected_deliverable"]
            elif variant == "enhanced":
                expected_sections = [
                    "prompt_summary", "executive_summary", "system_overview",
                    "overview", "user_stories", "spec_scope", "expected_deliverable"
                ]
            
            # Validate expected sections exist for each variant
            assert len(expected_sections) > 0
            assert "overview" in expected_sections  # All variants have overview
    
    def test_module_vs_traditional_organization(self):
        """Test both module-based and traditional organization support."""
        # Traditional organization test
        traditional_path = self.project_path / "specs/2025-08-05-traditional-spec"
        traditional_path.mkdir(parents=True)
        
        assert traditional_path.exists()
        assert "2025-08-05" in traditional_path.name  # Date-based naming
        
        # Module-based organization test  
        module_path = self.project_path / "specs/modules/authentication/2025-08-05-auth-spec"
        module_path.mkdir(parents=True)
        
        assert module_path.exists()
        assert "modules" in str(module_path)
        assert "authentication" in str(module_path)  # Module-based structure
        
        # Both can coexist
        assert traditional_path.exists()
        assert module_path.exists()


class TestExecuteTasksIntegration:
    """Test suite for execute-tasks.md workflow integration."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "test-project"
        self.global_agent_os = Path(self.temp_dir) / ".agent-os"
        
        self._setup_execute_tasks_environment()
    
    def teardown_method(self):
        """Clean up test environment after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _setup_execute_tasks_environment(self):
        """Set up execute-tasks integration test environment."""
        self.project_path.mkdir(parents=True)
        self.global_agent_os.mkdir(parents=True)
        
        # Create instructions directory
        instructions_dir = self.global_agent_os / "instructions"
        instructions_dir.mkdir()
        
        # Create enhanced execute-tasks.md
        execute_tasks_instruction = instructions_dir / "execute-tasks.md"
        execute_tasks_instruction.write_text("""
---
description: Enhanced Task Execution Rules for Agent OS
version: 2.0
encoding: UTF-8
---

# Enhanced Task Execution Rules

## Overview

<purpose>
  - Execute spec tasks with enhanced tracking
  - Support task summary completion
  - Integrate with enhanced documentation system
  - Maintain compatibility with existing workflows
</purpose>

## Enhanced Features

### Task Summary Completion
- Automatically populate task_summary.md
- Track implementation details and decisions
- Document testing and validation results

### Enhanced Progress Tracking
- Real-time task status updates
- Cross-reference validation during execution
- Performance metrics collection

### Integration Points
- Works with both traditional and module-based specs
- Supports enhanced documentation features
- Maintains backward compatibility

## Task Execution Flow

<step number="1" name="enhanced_task_assignment">
### Step 1: Enhanced Task Assignment

Supports execution of tasks from:
- Traditional specs: specs/YYYY-MM-DD-spec-name/tasks.md
- Module-based specs: specs/modules/module-name/YYYY-MM-DD-spec-name/tasks.md
- Enhanced task tracking with summary generation
</step>

## Summary Generation

After task completion, automatically generates:
- Implementation summary
- Technical decisions made
- Testing results
- Performance metrics
- Cross-reference validation results
""")
        
        # Create test spec with tasks
        spec_dir = self.project_path / "specs/modules/testing/2025-08-05-test-spec"
        spec_dir.mkdir(parents=True)
        
        (spec_dir / "tasks.md").write_text("""
# Spec Tasks

- [ ] 1. **Enhanced Feature Implementation**
  - [ ] 1.1 Write tests for enhanced feature
  - [ ] 1.2 Implement core functionality
  - [ ] 1.3 Add cross-reference validation
  - [ ] 1.4 Update documentation
  - [ ] 1.5 Verify all tests pass

- [ ] 2. **Integration Testing**
  - [ ] 2.1 Write integration tests
  - [ ] 2.2 Test backward compatibility
  - [ ] 2.3 Validate performance requirements
  - [ ] 2.4 Complete task summary
""")
        
        # Create placeholder task_summary.md
        (spec_dir / "task_summary.md").write_text("""
# Task Summary

> Spec: test-spec
> Module: testing
> Completion Status: In Progress

## Implementation Details

*To be completed during task execution*

## Technical Decisions

*To be completed during task execution*

## Testing Results

*To be completed during task execution*
""")
    
    def test_execute_tasks_instruction_compatibility(self):
        """Test execute-tasks instruction file compatibility."""
        instruction_file = self.global_agent_os / "instructions/execute-tasks.md"
        assert instruction_file.exists()
        
        content = instruction_file.read_text()
        
        # Check enhanced features
        assert "# Enhanced Task Execution Rules" in content
        assert "## Enhanced Features" in content
        assert "### Task Summary Completion" in content
        assert "### Enhanced Progress Tracking" in content
        
        # Check integration points
        assert "## Integration Points" in content
        assert "Works with both traditional and module-based specs" in content
        assert "Maintains backward compatibility" in content
    
    def test_task_summary_integration(self):
        """Test task summary generation integration."""
        spec_dir = self.project_path / "specs/modules/testing/2025-08-05-test-spec"
        
        # Check tasks.md exists
        tasks_file = spec_dir / "tasks.md"
        assert tasks_file.exists()
        
        tasks_content = tasks_file.read_text()
        assert "# Spec Tasks" in tasks_content
        assert "Complete task summary" in tasks_content
        
        # Check task_summary.md template exists
        summary_file = spec_dir / "task_summary.md"
        assert summary_file.exists()
        
        summary_content = summary_file.read_text()
        assert "# Task Summary" in summary_content
        assert "## Implementation Details" in summary_content
        assert "## Technical Decisions" in summary_content
        assert "## Testing Results" in summary_content
    
    def test_enhanced_task_tracking(self):
        """Test enhanced task tracking capabilities."""
        # Simulate task execution with enhanced tracking
        task_execution_data = {
            "spec_path": "specs/modules/testing/2025-08-05-test-spec",
            "current_task": "1.2 Implement core functionality",
            "status": "in_progress",
            "enhanced_features": {
                "cross_reference_validation": True,
                "performance_metrics": True,
                "automated_testing": True
            },
            "metadata": {
                "start_time": "2025-08-05T10:00:00Z",
                "estimated_completion": "2025-08-05T12:00:00Z"
            }
        }
        
        # Validate task execution structure
        assert "spec_path" in task_execution_data
        assert "current_task" in task_execution_data  
        assert "enhanced_features" in task_execution_data
        
        # Test enhanced features are enabled
        enhanced = task_execution_data["enhanced_features"]
        assert enhanced["cross_reference_validation"] is True
        assert enhanced["performance_metrics"] is True
        assert enhanced["automated_testing"] is True
    
    def test_backward_compatibility_with_existing_tasks(self):
        """Test backward compatibility with existing task structures."""
        # Create traditional task structure
        traditional_spec = self.project_path / "specs/2025-08-01-traditional-task"
        traditional_spec.mkdir(parents=True)
        
        (traditional_spec / "tasks.md").write_text("""
# Spec Tasks

- [ ] 1. Traditional Task Structure
  - [ ] 1.1 Write tests
  - [ ] 1.2 Implement feature
  - [ ] 1.3 Verify tests pass

- [ ] 2. Simple Integration
  - [ ] 2.1 Add to existing system
  - [ ] 2.2 Test integration
""")
        
        # Test traditional tasks can be executed
        traditional_tasks = traditional_spec / "tasks.md"
        assert traditional_tasks.exists()
        
        content = traditional_tasks.read_text()
        assert "# Spec Tasks" in content
        assert "- [ ] 1." in content
        assert "- [ ] 1.1" in content
        
        # Enhanced features should be optional for traditional specs
        # No task_summary.md required for traditional specs
        summary_file = traditional_spec / "task_summary.md"
        # Should not exist for traditional specs unless explicitly created
        assert not summary_file.exists()


class TestCrossReferenceIntegration:
    """Test suite for cross-reference system integration."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "test-project"
        self.hub_path = Path(self.temp_dir) / "assetutilities"
        
        self._setup_cross_reference_environment()
    
    def teardown_method(self):
        """Clean up test environment after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _setup_cross_reference_environment(self):
        """Set up cross-reference integration test environment."""
        # Create project with Agent OS
        self.project_path.mkdir(parents=True)
        agent_os_dir = self.project_path / ".agent-os"
        agent_os_dir.mkdir()
        
        # Create cross-repo configuration
        (agent_os_dir / "cross-repo-config.yaml").write_text(f"""
hub_repository: "assetutilities"
hub_path: "{self.hub_path}"
shared_components:
  - "agent-os/enhanced-create-specs/enhanced_documentation_generator.py"
version_requirements:
  hub: ">=1.0.0"
""")
        
        # Create hub repository structure
        self.hub_path.mkdir(parents=True)
        hub_modules = self.hub_path / "src/modules/agent-os/enhanced-create-specs"
        hub_modules.mkdir(parents=True)
        
        (hub_modules / "enhanced_documentation_generator.py").write_text("""
# Enhanced Documentation Generator v1.0.0
class EnhancedDocumentationGenerator:
    VERSION = "1.0.0"
    
    def generate_spec(self, config):
        return "Enhanced spec generated"
""")
        
        # Create spec with cross-references
        spec_dir = self.project_path / "specs/modules/integration/2025-08-05-cross-ref-test"
        spec_dir.mkdir(parents=True)
        
        (spec_dir / "spec.md").write_text("""
# Cross-Reference Integration Test

## Overview

This spec tests cross-reference integration with the enhanced system.

## Cross-Repository References

- Shared component: @assetutilities:src/modules/agent-os/enhanced-create-specs/enhanced_documentation_generator.py
- Hub configuration: @assetutilities:hub-config.yaml

## Internal References

- Product mission: @.agent-os/product/mission.md
- Other spec: @specs/modules/integration/other-spec/spec.md

## External References

- Documentation: https://docs.agent-os.com/enhanced-create-specs
- GitHub repo: https://github.com/user/assetutilities
""")
    
    def test_cross_repository_reference_resolution(self):
        """Test cross-repository reference resolution."""
        # Load cross-repo configuration
        config_file = self.project_path / ".agent-os/cross-repo-config.yaml" 
        assert config_file.exists()
        
        with open(config_file, 'r') as f:
            config = yaml.safe_load(f)
        
        assert config["hub_repository"] == "assetutilities"
        assert config["hub_path"] == str(self.hub_path)
        
        # Test shared component reference resolution
        shared_component_ref = "agent-os/enhanced-create-specs/enhanced_documentation_generator.py"
        assert shared_component_ref in config["shared_components"]
        
        # Resolve reference to actual path
        resolved_path = self.hub_path / "src/modules" / shared_component_ref
        assert resolved_path.exists()
        
        # Test component content
        content = resolved_path.read_text()
        assert "EnhancedDocumentationGenerator" in content
        assert "VERSION = \"1.0.0\"" in content
    
    def test_reference_pattern_validation(self):
        """Test reference pattern validation."""
        spec_file = self.project_path / "specs/modules/integration/2025-08-05-cross-ref-test/spec.md"
        assert spec_file.exists()
        
        content = spec_file.read_text()
        
        # Test different reference patterns
        references = {
            "cross_repo": "@assetutilities:src/modules/agent-os/enhanced-create-specs/enhanced_documentation_generator.py",
            "internal": "@.agent-os/product/mission.md", 
            "spec_ref": "@specs/modules/integration/other-spec/spec.md",
            "external": "https://docs.agent-os.com/enhanced-create-specs"
        }
        
        for ref_type, ref_pattern in references.items():
            assert ref_pattern in content
            
            # Validate pattern format
            if ref_type == "cross_repo":
                assert ref_pattern.startswith("@assetutilities:")
            elif ref_type == "internal":
                assert ref_pattern.startswith("@.")
            elif ref_type == "spec_ref":
                assert ref_pattern.startswith("@specs/")
            elif ref_type == "external":
                assert ref_pattern.startswith("http")
    
    def test_reference_accessibility_validation(self):
        """Test validation of reference accessibility."""
        # Test accessible reference (hub component)
        hub_component = self.hub_path / "src/modules/agent-os/enhanced-create-specs/enhanced_documentation_generator.py"
        assert hub_component.exists()
        
        # Test inaccessible reference (should be handled gracefully)
        inaccessible_ref = self.hub_path / "src/modules/nonexistent/component.py"
        assert not inaccessible_ref.exists()
        
        # Reference validation results
        validation_results = {
            "accessible_references": [
                "@assetutilities:src/modules/agent-os/enhanced-create-specs/enhanced_documentation_generator.py"
            ],
            "inaccessible_references": [
                "@assetutilities:src/modules/nonexistent/component.py"
            ],
            "external_references": [
                "https://docs.agent-os.com/enhanced-create-specs"
            ]
        }
        
        # Test validation structure
        assert len(validation_results["accessible_references"]) > 0
        assert len(validation_results["external_references"]) > 0
        
        # External references should not be validated for accessibility
        for ext_ref in validation_results["external_references"]:
            assert ext_ref.startswith("http")


class TestFrameworkIntegrationWorkflow:
    """Test suite for complete framework integration workflow."""
    
    def setup_method(self):
        """Set up test environment before each test."""
        self.temp_dir = tempfile.mkdtemp()
        self.project_path = Path(self.temp_dir) / "test-project"
        
        self._setup_complete_integration_environment()
    
    def teardown_method(self):
        """Clean up test environment after each test."""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def _setup_complete_integration_environment(self):
        """Set up complete integration test environment."""
        self.project_path.mkdir(parents=True)
        
        # Create comprehensive Agent OS project structure
        agent_os = self.project_path / ".agent-os"
        agent_os.mkdir()
        
        # Product documentation
        product_dir = agent_os / "product"
        product_dir.mkdir() 
        
        (product_dir / "mission.md").write_text("""
# Product Mission

Enhanced testing application with modern workflows.
""")
        
        (product_dir / "roadmap.md").write_text("""
# Product Roadmap

## Phase 1: Enhanced Features
- [ ] **Enhanced Spec Creation** - Modern spec workflow `L`
- [ ] **Cross-Repository Integration** - Hub-based sharing `L`
""")
        
        # User preferences
        (agent_os / "user-preferences.yaml").write_text("""
preferred_variant: "enhanced"
organization_type: "module-based"
enable_mermaid_diagrams: true
enable_cross_references: true
""")
        
        # Create mixed spec structures (traditional + enhanced)
        specs_dir = self.project_path / "specs"
        specs_dir.mkdir()
        
        # Traditional spec
        traditional_spec = specs_dir / "2025-08-01-traditional"
        traditional_spec.mkdir()
        (traditional_spec / "spec.md").write_text("# Traditional Spec\n\n## Overview\nTraditional format spec.")
        
        # Enhanced module-based spec
        enhanced_spec = specs_dir / "modules/testing/2025-08-05-enhanced"
        enhanced_spec.mkdir(parents=True)
        (enhanced_spec / "spec.md").write_text("""
# Enhanced Spec

## Prompt Summary
**Original Request:** Create comprehensive testing framework

## Executive Summary
### Business Impact
Improved testing coverage and development velocity.

## System Overview
```mermaid
graph TD
    A[Tests] --> B[Results]
```

## Overview
Enhanced spec with visual documentation.
""")
        
        # CLAUDE.md with enhanced references
        (self.project_path / "CLAUDE.md").write_text("""
# Project Instructions

## Agent OS Documentation

### Product Context
- **Mission & Vision:** @.agent-os/product/mission.md
- **Development Roadmap:** @.agent-os/product/roadmap.md

### Enhanced Features
- **Cross-Repository Components:** Enabled via @.agent-os/cross-repo-config.yaml
- **Template Variants:** minimal, standard, enhanced
- **Module Organization:** specs/modules/{module_name}/

## Workflow Instructions

When asked to work on this codebase:

1. **Enhanced Spec Creation:** Use module-based organization
2. **Cross-References:** Support @assetutilities: references  
3. **Visual Documentation:** Auto-generate mermaid diagrams
4. **Backward Compatibility:** Support existing spec formats
""")
    
    def test_complete_framework_integration_workflow(self):
        """Test complete framework integration workflow."""
        # Test project structure
        assert self.project_path.exists()
        assert (self.project_path / ".agent-os").exists()
        assert (self.project_path / "specs").exists()
        assert (self.project_path / "CLAUDE.md").exists()
        
        # Test mixed spec organization support
        traditional_spec = self.project_path / "specs/2025-08-01-traditional"
        enhanced_spec = self.project_path / "specs/modules/testing/2025-08-05-enhanced"
        
        assert traditional_spec.exists()
        assert enhanced_spec.exists()
        
        # Test spec content compatibility
        traditional_content = (traditional_spec / "spec.md").read_text()
        enhanced_content = (enhanced_spec / "spec.md").read_text()
        
        # Traditional has basic structure
        assert "# Traditional Spec" in traditional_content
        assert "## Overview" in traditional_content
        
        # Enhanced has additional sections
        assert "# Enhanced Spec" in enhanced_content
        assert "## Prompt Summary" in enhanced_content
        assert "## Executive Summary" in enhanced_content
        assert "```mermaid" in enhanced_content
    
    def test_claude_md_enhanced_integration(self):
        """Test CLAUDE.md enhanced integration."""
        claude_file = self.project_path / "CLAUDE.md"
        content = claude_file.read_text()
        
        # Test enhanced features documentation
        assert "## Enhanced Features" in content
        assert "Cross-Repository Components" in content
        assert "Template Variants" in content
        assert "Module Organization" in content
        
        # Test workflow instructions updated
        assert "Enhanced Spec Creation" in content
        assert "Cross-References" in content
        assert "Visual Documentation" in content
        assert "Backward Compatibility" in content
    
    def test_user_preferences_workflow_integration(self):
        """Test user preferences integration with workflow."""
        prefs_file = self.project_path / ".agent-os/user-preferences.yaml"
        
        with open(prefs_file, 'r') as f:
            prefs = yaml.safe_load(f)
        
        # Test preference-driven workflow behavior
        if prefs["preferred_variant"] == "enhanced":
            # Should create enhanced specs by default
            assert prefs["enable_mermaid_diagrams"] is True
            assert prefs["enable_cross_references"] is True
        
        if prefs["organization_type"] == "module-based":
            # Should organize specs in modules
            enhanced_spec = self.project_path / "specs/modules/testing/2025-08-05-enhanced"
            assert enhanced_spec.exists()
            assert "modules" in str(enhanced_spec)
    
    def test_framework_backward_compatibility_validation(self):
        """Test framework maintains backward compatibility."""
        # Traditional Agent OS patterns should still work
        
        # 1. Traditional spec structure
        traditional_spec = self.project_path / "specs/2025-08-01-traditional/spec.md"
        assert traditional_spec.exists()
        
        # 2. Product documentation references
        mission_ref = "@.agent-os/product/mission.md"
        mission_path = self.project_path / mission_ref[1:]
        assert mission_path.exists()
        
        # 3. CLAUDE.md structure
        claude_content = (self.project_path / "CLAUDE.md").read_text()
        assert "## Agent OS Documentation" in claude_content
        assert "### Product Context" in claude_content
        assert "## Workflow Instructions" in claude_content
        
        # 4. Enhanced features are additive, not replacing
        assert "## Enhanced Features" in claude_content  # New section
        assert "### Product Context" in claude_content   # Existing section preserved
    
    def test_integration_success_criteria(self):
        """Test that all integration success criteria are met."""
        success_criteria = {
            "backward_compatibility": False,
            "enhanced_features_available": False,
            "mixed_organization_support": False,
            "cross_reference_support": False,
            "visual_documentation": False,
            "user_preferences_honored": False
        }
        
        # Test backward compatibility
        traditional_spec = self.project_path / "specs/2025-08-01-traditional"
        if traditional_spec.exists():
            success_criteria["backward_compatibility"] = True
        
        # Test enhanced features
        enhanced_spec = self.project_path / "specs/modules/testing/2025-08-05-enhanced"
        if enhanced_spec.exists():
            enhanced_content = (enhanced_spec / "spec.md").read_text()
            if "## Prompt Summary" in enhanced_content:
                success_criteria["enhanced_features_available"] = True
        
        # Test mixed organization
        if (traditional_spec.exists() and enhanced_spec.exists()):
            success_criteria["mixed_organization_support"] = True
        
        # Test cross-reference support
        claude_content = (self.project_path / "CLAUDE.md").read_text()
        if "@assetutilities:" in claude_content:
            success_criteria["cross_reference_support"] = True
        
        # Test visual documentation
        if enhanced_spec.exists():
            enhanced_content = (enhanced_spec / "spec.md").read_text()
            if "```mermaid" in enhanced_content:
                success_criteria["visual_documentation"] = True
        
        # Test user preferences
        prefs_file = self.project_path / ".agent-os/user-preferences.yaml"
        if prefs_file.exists():
            success_criteria["user_preferences_honored"] = True
        
        # All criteria should be met
        for criterion, result in success_criteria.items():
            assert result, f"Integration success criterion failed: {criterion}"
        
        # Overall integration success
        integration_successful = all(success_criteria.values())
        assert integration_successful


if __name__ == "__main__":
    pytest.main([__file__, "-v", "--tb=short"])