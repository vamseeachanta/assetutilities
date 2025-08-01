"""
Unit Tests for Multi-Level AI Persistence System

Tests the AI persistence system including:
- System-level configuration management
- User-level preferences and learning history  
- Repository-level context and team patterns
- Session-level context management
- Context hierarchy and merging logic
- Cross-system synchronization
"""

import pytest
import asyncio
import os
import json
import yaml
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock, mock_open
from pathlib import Path
from datetime import datetime, timedelta
from dataclasses import asdict

# Import the modules we'll be testing
import sys
sys.path.insert(0, '/mnt/github/github/assetutilities/src/modules/agent_os/enhanced_create_specs')

from ai_persistence_system import (
    SystemLevelManager,
    UserLevelManager,
    RepositoryLevelManager,
    SessionLevelManager,
    ContextHierarchyManager,
    AIContextData,
    PersistenceConfig,
    ContextMerger,
    CrossSystemSynchronizer
)


class TestSystemLevelManager:
    """Tests for SystemLevelManager class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.system_manager = SystemLevelManager(system_dir=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test system manager initialization"""
        assert self.system_manager.system_dir == self.temp_dir
        assert isinstance(self.system_manager.config, PersistenceConfig)
        assert self.system_manager.enabled == True
    
    def test_load_system_standards(self):
        """Test loading system-wide AI standards"""
        # Create test system standards file
        standards = {
            'ai_behaviors': {
                'code_style': 'pythonic',
                'security_first': True,
                'documentation_level': 'comprehensive'
            },
            'global_policies': {
                'max_file_size': '10MB',
                'allowed_languages': ['python', 'javascript', 'yaml']
            }
        }
        
        standards_file = Path(self.temp_dir) / 'ai-behaviors.yml'
        with open(standards_file, 'w') as f:
            yaml.dump(standards, f)
        
        loaded_standards = self.system_manager.load_system_standards()
        
        assert loaded_standards['ai_behaviors']['code_style'] == 'pythonic'
        assert loaded_standards['ai_behaviors']['security_first'] == True
        assert loaded_standards['global_policies']['max_file_size'] == '10MB'
    
    def test_load_system_standards_missing_file(self):
        """Test loading system standards when file doesn't exist"""
        loaded_standards = self.system_manager.load_system_standards()
        
        # Should return default standards
        assert 'ai_behaviors' in loaded_standards
        assert 'global_policies' in loaded_standards
        assert loaded_standards['ai_behaviors']['code_style'] == 'clean'
    
    def test_save_system_standards(self):
        """Test saving system-wide standards"""
        standards = {
            'ai_behaviors': {
                'code_style': 'pythonic',
                'response_length': 'concise'
            }
        }
        
        result = self.system_manager.save_system_standards(standards)
        
        assert result == True
        
        # Verify file was created
        standards_file = Path(self.temp_dir) / 'ai-behaviors.yml'
        assert standards_file.exists()
        
        # Verify content
        with open(standards_file, 'r') as f:
            saved_data = yaml.safe_load(f)
        
        assert saved_data['ai_behaviors']['code_style'] == 'pythonic'


class TestUserLevelManager:
    """Tests for UserLevelManager class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.user_manager = UserLevelManager(user_dir=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_load_user_preferences(self):
        """Test loading user preferences"""
        preferences = {
            'communication_style': 'detailed',
            'expertise_level': 'senior',
            'preferred_languages': ['python', 'javascript'],
            'notification_settings': {
                'email_updates': True,
                'desktop_notifications': False
            }
        }
        
        prefs_file = Path(self.temp_dir) / 'preferences.yml'
        with open(prefs_file, 'w') as f:
            yaml.dump(preferences, f)
        
        loaded_prefs = self.user_manager.load_user_preferences()
        
        assert loaded_prefs['communication_style'] == 'detailed'
        assert loaded_prefs['expertise_level'] == 'senior'
        assert 'python' in loaded_prefs['preferred_languages']
    
    def test_save_learning_history(self):
        """Test saving user learning history"""
        learning_history = {
            'successful_patterns': [
                {'pattern': 'enhanced_create_specs', 'success_rate': 0.95, 'last_used': '2025-08-01'},
                {'pattern': 'uv_integration', 'success_rate': 0.88, 'last_used': '2025-07-30'}
            ],
            'preferred_workflows': [
                'test_driven_development',
                'module_based_organization'
            ],
            'skill_development': {
                'python': 'expert',
                'docker': 'intermediate',
                'kubernetes': 'beginner'
            }
        }
        
        result = self.user_manager.save_learning_history(learning_history)
        
        assert result == True
        
        # Verify file was created
        history_file = Path(self.temp_dir) / 'learning-history.yml'
        assert history_file.exists()
    
    def test_update_skill_profile(self):
        """Test updating user skill profile"""
        initial_skills = {
            'python': 'intermediate',
            'docker': 'beginner'
        }
        
        # Save initial profile
        self.user_manager.save_skill_profile(initial_skills)
        
        # Update skills
        skill_updates = {
            'python': 'expert',
            'kubernetes': 'intermediate'
        }
        
        result = self.user_manager.update_skill_profile(skill_updates)
        
        assert result == True
        
        # Load and verify updated profile
        updated_profile = self.user_manager.load_skill_profile()
        
        assert updated_profile['python'] == 'expert'
        assert updated_profile['docker'] == 'beginner'  # Should remain unchanged
        assert updated_profile['kubernetes'] == 'intermediate'


class TestRepositoryLevelManager:
    """Tests for RepositoryLevelManager class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_manager = RepositoryLevelManager(repo_root=self.temp_dir)
    
    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_initialization_creates_context_directory(self):
        """Test that initialization creates .agent-os/context directory"""
        context_dir = Path(self.temp_dir) / '.agent-os' / 'context'
        
        assert context_dir.exists()
        assert context_dir.is_dir()
    
    def test_load_project_patterns(self):
        """Test loading project-specific patterns"""
        patterns = {
            'architecture_patterns': {
                'design': 'microservices',
                'database': 'postgresql',
                'caching': 'redis'
            },
            'code_patterns': {
                'testing_framework': 'pytest',
                'linting': 'ruff',
                'formatting': 'black'
            },
            'workflow_patterns': {
                'branching_strategy': 'git-flow',
                'ci_cd': 'github-actions',
                'deployment': 'docker'
            }
        }
        
        patterns_file = Path(self.temp_dir) / '.agent-os' / 'context' / 'project-patterns.yml'
        patterns_file.parent.mkdir(parents=True, exist_ok=True)
        
        with open(patterns_file, 'w') as f:
            yaml.dump(patterns, f)
        
        loaded_patterns = self.repo_manager.load_project_patterns()
        
        assert loaded_patterns['architecture_patterns']['design'] == 'microservices'
        assert loaded_patterns['code_patterns']['testing_framework'] == 'pytest'
        assert loaded_patterns['workflow_patterns']['branching_strategy'] == 'git-flow'
    
    def test_save_team_conventions(self):
        """Test saving team conventions"""
        conventions = {
            'code_review': {
                'min_reviewers': 2,
                'auto_merge': False,
                'required_checks': ['tests', 'linting', 'security']
            },
            'documentation': {
                'style': 'sphinx',
                'coverage_required': True,
                'api_docs': 'auto-generated'
            },
            'communication': {
                'daily_standup': '9:00 AM',
                'retrospective': 'bi-weekly',
                'demo_day': 'friday'
            }
        }
        
        result = self.repo_manager.save_team_conventions(conventions)
        
        assert result == True
        
        # Verify file was created
        conventions_file = Path(self.temp_dir) / '.agent-os' / 'context' / 'team-conventions.yml'
        assert conventions_file.exists()
        
        # Load and verify content
        loaded_conventions = self.repo_manager.load_team_conventions()
        assert loaded_conventions['code_review']['min_reviewers'] == 2
    
    def test_save_domain_knowledge(self):
        """Test saving business domain knowledge"""
        domain_knowledge = {
            'business_domain': 'financial_services',
            'key_concepts': {
                'assets': 'Financial instruments and investments',
                'utilities': 'Tools for processing financial data',
                'compliance': 'Regulatory requirements and reporting'
            },
            'stakeholders': {
                'primary': ['portfolio_managers', 'risk_analysts'],
                'secondary': ['compliance_officers', 'auditors']
            },
            'data_sources': {
                'market_data': 'Bloomberg API',
                'reference_data': 'Internal database',
                'regulatory_data': 'Government APIs'
            }
        }
        
        result = self.repo_manager.save_domain_knowledge(domain_knowledge)
        
        assert result == True
        
        # Verify content was saved correctly
        knowledge_file = Path(self.temp_dir) / '.agent-os' / 'context' / 'domain-knowledge.yml'
        assert knowledge_file.exists()
        
        with open(knowledge_file, 'r') as f:
            saved_knowledge = yaml.safe_load(f)
        
        assert saved_knowledge['business_domain'] == 'financial_services'
        assert 'portfolio_managers' in saved_knowledge['stakeholders']['primary']
    
    def test_log_decision(self):
        """Test logging project decisions"""
        decision = {
            'id': 'DEC-001',
            'title': 'Choose Python web framework',
            'date': '2025-08-01',
            'status': 'accepted',
            'decision': 'Use FastAPI for REST API development',
            'rationale': 'High performance, automatic documentation, type hints support',
            'consequences': {
                'positive': ['Fast development', 'Great documentation'],
                'negative': ['Learning curve for team']
            },
            'stakeholders': ['tech_lead', 'senior_developers']
        }
        
        result = self.repo_manager.log_decision(decision)
        
        assert result == True
        
        # Verify decision file was created
        decisions_dir = Path(self.temp_dir) / '.agent-os' / 'context' / 'decisions'
        decision_file = decisions_dir / '2025-08-01-choose-python-web-framework.yml'
        
        assert decision_file.exists()
        
        # Verify content
        with open(decision_file, 'r') as f:
            saved_decision = yaml.safe_load(f)
        
        assert saved_decision['id'] == 'DEC-001'
        assert saved_decision['decision'] == 'Use FastAPI for REST API development'


class TestSessionLevelManager:
    """Tests for SessionLevelManager class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.session_manager = SessionLevelManager()
    
    def test_initialization(self):
        """Test session manager initialization"""
        assert self.session_manager.session_id is not None
        assert len(self.session_manager.session_id) > 10
        assert isinstance(self.session_manager.context_data, dict)
    
    def test_set_current_context(self):
        """Test setting current session context"""
        context = {
            'current_task': 'implement_ai_persistence',
            'active_spec': 'enhanced-create-specs',
            'conversation_history': [
                {'role': 'user', 'content': 'Implement Task 4'},
                {'role': 'assistant', 'content': 'I will implement the AI persistence system'}
            ],
            'recent_decisions': [
                {'decision': 'Use YAML for configuration files', 'timestamp': '2025-08-01T10:30:00Z'}
            ]
        }
        
        self.session_manager.set_current_context(context)
        
        stored_context = self.session_manager.get_current_context()
        
        assert stored_context['current_task'] == 'implement_ai_persistence'
        assert stored_context['active_spec'] == 'enhanced-create-specs'
        assert len(stored_context['conversation_history']) == 2
    
    def test_add_conversation_entry(self):
        """Test adding conversation entries"""
        self.session_manager.add_conversation_entry('user', 'What is the next task?')
        self.session_manager.add_conversation_entry('assistant', 'The next task is Task 4: AI Persistence System')
        
        context = self.session_manager.get_current_context()
        
        assert len(context['conversation_history']) == 2
        assert context['conversation_history'][0]['role'] == 'user'
        assert context['conversation_history'][1]['content'] == 'The next task is Task 4: AI Persistence System'
    
    def test_record_decision(self):
        """Test recording session decisions"""
        decision = {
            'decision': 'Use file-based storage for MVP',
            'rationale': 'Simpler implementation, version controllable',
            'impact': 'medium'
        }
        
        self.session_manager.record_decision(decision)
        
        context = self.session_manager.get_current_context()
        
        assert len(context['recent_decisions']) == 1
        assert context['recent_decisions'][0]['decision'] == 'Use file-based storage for MVP'
        assert 'timestamp' in context['recent_decisions'][0]
    
    def test_clear_session(self):
        """Test clearing session context"""
        # Add some context first
        self.session_manager.add_conversation_entry('user', 'Test message')
        self.session_manager.record_decision({'decision': 'Test decision'})
        
        # Verify context exists
        context = self.session_manager.get_current_context()
        assert len(context['conversation_history']) > 0
        assert len(context['recent_decisions']) > 0
        
        # Clear session
        self.session_manager.clear_session()
        
        # Verify context is cleared
        context = self.session_manager.get_current_context()
        assert len(context['conversation_history']) == 0
        assert len(context['recent_decisions']) == 0


class TestContextHierarchyManager:
    """Tests for ContextHierarchyManager class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.temp_dirs = {
            'system': tempfile.mkdtemp(),
            'user': tempfile.mkdtemp(),
            'repo': tempfile.mkdtemp()
        }
        
        self.hierarchy_manager = ContextHierarchyManager(
            system_dir=self.temp_dirs['system'],
            user_dir=self.temp_dirs['user'],
            repo_root=self.temp_dirs['repo']
        )
    
    def teardown_method(self):
        """Clean up test fixtures"""
        for temp_dir in self.temp_dirs.values():
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    def test_initialization(self):
        """Test hierarchy manager initialization"""
        assert self.hierarchy_manager.system_manager is not None
        assert self.hierarchy_manager.user_manager is not None
        assert self.hierarchy_manager.repo_manager is not None
        assert self.hierarchy_manager.session_manager is not None
    
    @pytest.mark.asyncio
    async def test_get_merged_context(self):
        """Test getting merged context from all levels"""
        # Setup context at each level
        
        # System level
        system_standards = {
            'ai_behaviors': {
                'code_style': 'pythonic',
                'security_first': True
            }
        }
        self.hierarchy_manager.system_manager.save_system_standards(system_standards)
        
        # User level  
        user_prefs = {
            'communication_style': 'detailed',
            'expertise_level': 'senior'
        }
        self.hierarchy_manager.user_manager.save_user_preferences(user_prefs)
        
        # Repository level
        project_patterns = {
            'testing_framework': 'pytest',
            'linting': 'ruff'
        }
        self.hierarchy_manager.repo_manager.save_project_patterns(project_patterns)
        
        # Session level
        session_context = {
            'current_task': 'test_context_merging'
        }
        self.hierarchy_manager.session_manager.set_current_context(session_context)
        
        # Get merged context
        merged_context = await self.hierarchy_manager.get_merged_context()
        
        # Verify all levels are represented
        assert merged_context['system']['ai_behaviors']['code_style'] == 'pythonic'
        assert merged_context['user']['communication_style'] == 'detailed'
        assert merged_context['repository']['testing_framework'] == 'pytest'
        assert merged_context['session']['current_task'] == 'test_context_merging'
    
    @pytest.mark.asyncio
    async def test_context_override_hierarchy(self):
        """Test that context follows proper override hierarchy"""
        # Set conflicting values at different levels
        system_standards = {'code_style': 'system_standard'}
        user_prefs = {'code_style': 'user_preference'}
        project_patterns = {'code_style': 'project_pattern'}
        session_context = {'code_style': 'session_override'}
        
        self.hierarchy_manager.system_manager.save_system_standards({'ai_behaviors': system_standards})
        self.hierarchy_manager.user_manager.save_user_preferences(user_prefs)
        self.hierarchy_manager.repo_manager.save_project_patterns(project_patterns)
        self.hierarchy_manager.session_manager.set_current_context(session_context)
        
        # Get effective context (with overrides applied)
        effective_context = await self.hierarchy_manager.get_effective_context()
        
        # Session should override all others
        assert effective_context['code_style'] == 'session_override'
    
    def test_save_context_to_repository(self):
        """Test saving merged context to repository"""
        context_data = {
            'learned_patterns': {
                'successful_workflows': ['enhanced_create_specs'],
                'team_preferences': {'review_style': 'thorough'}
            },
            'project_insights': {
                'complexity_level': 'high',
                'domain_expertise_required': True
            }
        }
        
        result = self.hierarchy_manager.save_context_to_repository(context_data)
        
        assert result == True
        
        # Verify context was saved in repository
        context_file = Path(self.temp_dirs['repo']) / '.agent-os' / 'context' / 'ai-context.yml'
        assert context_file.exists()


class TestContextMerger:
    """Tests for ContextMerger utility class"""
    
    def test_merge_contexts_simple(self):
        """Test merging simple context dictionaries"""
        base_context = {
            'setting1': 'base_value',
            'setting2': 'base_value2'
        }
        
        override_context = {
            'setting1': 'override_value',
            'setting3': 'new_value'
        }
        
        merged = ContextMerger.merge_contexts(base_context, override_context)
        
        assert merged['setting1'] == 'override_value'  # Overridden
        assert merged['setting2'] == 'base_value2'     # Preserved
        assert merged['setting3'] == 'new_value'       # Added
    
    def test_merge_contexts_nested(self):
        """Test merging nested context dictionaries"""
        base_context = {
            'ai_behaviors': {
                'code_style': 'base_style',
                'documentation': {
                    'level': 'basic',
                    'format': 'markdown'
                }
            },
            'preferences': {
                'theme': 'dark'
            }
        }
        
        override_context = {
            'ai_behaviors': {
                'code_style': 'override_style',
                'documentation': {
                    'level': 'detailed'
                    # format should be preserved
                }
            },
            'new_section': {
                'value': 'new'
            }
        }
        
        merged = ContextMerger.merge_contexts(base_context, override_context)
        
        assert merged['ai_behaviors']['code_style'] == 'override_style'
        assert merged['ai_behaviors']['documentation']['level'] == 'detailed'
        assert merged['ai_behaviors']['documentation']['format'] == 'markdown'  # Preserved
        assert merged['preferences']['theme'] == 'dark'  # Preserved
        assert merged['new_section']['value'] == 'new'   # Added
    
    def test_merge_hierarchy(self):
        """Test merging multiple contexts in hierarchy order"""
        system_context = {
            'setting': 'system',
            'system_only': 'system_value'
        }
        
        user_context = {
            'setting': 'user',
            'user_only': 'user_value'
        }
        
        repo_context = {
            'setting': 'repo',
            'repo_only': 'repo_value'
        }
        
        session_context = {
            'setting': 'session',
            'session_only': 'session_value'  
        }
        
        contexts = [system_context, user_context, repo_context, session_context]
        merged = ContextMerger.merge_hierarchy(contexts)
        
        # Session should override all
        assert merged['setting'] == 'session'
        
        # All unique values should be preserved
        assert merged['system_only'] == 'system_value'
        assert merged['user_only'] == 'user_value'
        assert merged['repo_only'] == 'repo_value'
        assert merged['session_only'] == 'session_value'


class TestCrossSystemSynchronizer:
    """Tests for CrossSystemSynchronizer class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.synchronizer = CrossSystemSynchronizer()
    
    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_sync_learned_patterns(self):
        """Test synchronizing learned patterns across systems"""
        learned_patterns = {
            'successful_workflows': [
                {
                    'name': 'enhanced_create_specs',
                    'success_rate': 0.95,
                    'context': 'python_projects',
                    'learned_at': '2025-08-01T10:00:00Z'
                }
            ],
            'anti_patterns': [
                {
                    'name': 'skip_tests',
                    'failure_rate': 0.8,
                    'context': 'all_projects'
                }
            ]
        }
        
        result = await self.synchronizer.sync_learned_patterns(learned_patterns)
        
        assert result['success'] == True
        assert result['patterns_synced'] > 0
    
    @pytest.mark.asyncio
    async def test_propagate_successful_pattern(self):
        """Test propagating a successful pattern from repo to user level"""
        pattern = {
            'name': 'cross_repo_integration',
            'success_metrics': {
                'completion_rate': 0.98,
                'error_rate': 0.02,
                'user_satisfaction': 4.8
            },
            'context': {
                'project_type': 'python_utility_library',
                'team_size': 'small',
                'complexity': 'high'
            },
            'implementation_details': {
                'components': ['git_submodules', 'reference_resolution'],
                'time_to_complete': '4_hours',
                'dependencies': ['pyyaml', 'requests']
            }
        }
        
        result = await self.synchronizer.propagate_successful_pattern(pattern)
        
        assert result['success'] == True
        assert result['propagation_level'] in ['user', 'system']
    
    def test_detect_pattern_conflicts(self):
        """Test detecting conflicts between different context levels"""
        system_patterns = {
            'code_style': 'pep8',
            'testing_required': True
        }
        
        user_patterns = {
            'code_style': 'black',  # Conflict
            'documentation_style': 'sphinx'
        }
        
        repo_patterns = {
            'code_style': 'ruff',   # Conflict
            'testing_required': False  # Conflict
        }
        
        conflicts = self.synchronizer.detect_pattern_conflicts(
            system_patterns, 
            user_patterns, 
            repo_patterns
        )
        
        assert len(conflicts) == 2  # code_style and testing_required
        assert 'code_style' in [c['setting'] for c in conflicts]
        assert 'testing_required' in [c['setting'] for c in conflicts]


class TestIntegrationScenarios:
    """Integration tests for complete AI persistence workflows"""
    
    def setup_method(self):
        """Setup integration test fixtures"""
        self.temp_dirs = {
            'system': tempfile.mkdtemp(),
            'user': tempfile.mkdtemp(), 
            'repo': tempfile.mkdtemp()
        }
        
        self.hierarchy_manager = ContextHierarchyManager(
            system_dir=self.temp_dirs['system'],
            user_dir=self.temp_dirs['user'],
            repo_root=self.temp_dirs['repo']
        )
    
    def teardown_method(self):
        """Clean up integration test fixtures"""
        for temp_dir in self.temp_dirs.values():
            shutil.rmtree(temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_complete_ai_context_workflow(self):
        """Test complete AI context workflow from initialization to usage"""
        
        # 1. Initialize system with organization standards
        system_standards = {
            'ai_behaviors': {
                'code_style': 'pythonic',
                'security_first': True,
                'documentation_required': True
            },
            'global_policies': {
                'max_complexity': 10,
                'test_coverage_min': 0.8
            }
        }
        
        result = self.hierarchy_manager.system_manager.save_system_standards(system_standards)
        assert result == True
        
        # 2. Set user preferences
        user_preferences = {
            'communication_style': 'detailed_explanations',
            'expertise_level': 'senior_developer',
            'preferred_patterns': ['test_driven_development', 'module_organization']
        }
        
        result = self.hierarchy_manager.user_manager.save_user_preferences(user_preferences)
        assert result == True
        
        # 3. Establish project context
        project_patterns = {
            'architecture': 'utility_library',
            'primary_language': 'python',
            'testing_framework': 'pytest',
            'documentation_tool': 'sphinx',
            'deployment_target': 'pypi'
        }
        
        result = self.hierarchy_manager.repo_manager.save_project_patterns(project_patterns)
        assert result == True
        
        # 4. Start development session
        session_context = {
            'current_task': 'implement_ai_persistence_system',
            'active_spec': 'enhanced-create-specs',
            'phase': 'implementation'
        }
        
        self.hierarchy_manager.session_manager.set_current_context(session_context)
        
        # 5. Get merged context for AI decision making
        merged_context = await self.hierarchy_manager.get_merged_context()
        
        # Verify all levels are properly merged
        assert merged_context['system']['ai_behaviors']['code_style'] == 'pythonic'
        assert merged_context['user']['communication_style'] == 'detailed_explanations'
        assert merged_context['repository']['testing_framework'] == 'pytest'
        assert merged_context['session']['current_task'] == 'implement_ai_persistence_system'
        
        # 6. Make a decision and record it
        decision = {
            'id': 'DEC-AI-001',
            'title': 'Choose storage format for AI context',
            'decision': 'Use YAML for human readability and version control',
            'rationale': 'YAML is human-readable, supports comments, and works well with git',
            'stakeholders': ['ai_system', 'development_team']
        }
        
        result = self.hierarchy_manager.repo_manager.log_decision(decision)
        assert result == True
        
        # 7. Record learning from successful implementation
        learning_entry = {
            'pattern': 'ai_persistence_implementation',
            'success_metrics': {
                'implementation_time': '2_hours',
                'code_quality': 'high',
                'test_coverage': 0.95
            },
            'key_insights': [
                'YAML format works well for configuration',
                'Hierarchical context merging is powerful',
                'Repository-level storage enables team sharing'
            ]
        }
        
        current_history = self.hierarchy_manager.user_manager.load_learning_history()
        current_history.setdefault('successful_patterns', []).append(learning_entry)
        
        result = self.hierarchy_manager.user_manager.save_learning_history(current_history)
        assert result == True
        
        # 8. Verify persistence across restart
        new_hierarchy_manager = ContextHierarchyManager(
            system_dir=self.temp_dirs['system'],
            user_dir=self.temp_dirs['user'], 
            repo_root=self.temp_dirs['repo']
        )
        
        restored_context = await new_hierarchy_manager.get_merged_context()
        
        # Context should be restored from files
        assert restored_context['system']['ai_behaviors']['code_style'] == 'pythonic'
        assert restored_context['user']['communication_style'] == 'detailed_explanations'
        assert restored_context['repository']['testing_framework'] == 'pytest'
        
        print("✅ Complete AI context workflow test passed!")


if __name__ == '__main__':
    pytest.main([__file__, '-v'])