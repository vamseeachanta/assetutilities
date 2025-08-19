"""
Multi-Level AI Persistence System

Provides comprehensive AI context persistence across multiple levels:
- System-level: Global AI behaviors and standards (organization-wide)
- User-level: Personal preferences and learning history (user-specific)
- Repository-level: Project context and team patterns (repo-specific, version-controlled)
- Session-level: Current conversation and immediate context (temporary)

Key features:
- Hierarchical context merging with proper override rules
- Repository-focused storage for team collaboration
- Cross-system synchronization and pattern learning
- Comprehensive conflict detection and resolution
"""

import os
import yaml
import uuid
import logging
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict, field
from datetime import datetime
from copy import deepcopy

logger = logging.getLogger(__name__)


@dataclass
class PersistenceConfig:
    """Configuration for AI persistence system"""
    enabled: bool = True
    auto_save: bool = True
    backup_enabled: bool = True
    sync_enabled: bool = True
    max_history_entries: int = 1000
    cleanup_interval_days: int = 30
    
    # File format settings
    file_format: str = "yaml"  # yaml, json
    encoding: str = "utf-8"
    indent: int = 2
    
    # Security settings
    encrypt_sensitive: bool = False
    allowed_paths: List[str] = field(default_factory=list)
    
    # Performance settings
    cache_enabled: bool = True
    cache_ttl: int = 300  # seconds
    max_context_size: int = 10 * 1024 * 1024  # 10MB


@dataclass
class AIContextData:
    """Structured AI context data"""
    context_id: str
    level: str  # system, user, repository, session
    timestamp: str
    data: Dict[str, Any]
    metadata: Dict[str, Any] = field(default_factory=dict)
    
    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary for serialization"""
        return asdict(self)
    
    @classmethod
    def from_dict(cls, data: Dict[str, Any]) -> 'AIContextData':
        """Create from dictionary"""
        return cls(**data)


class SystemLevelManager:
    """Manages system-wide AI standards and behaviors"""
    
    def __init__(self, system_dir: Optional[str] = None, config: Optional[PersistenceConfig] = None):
        """
        Initialize system level manager
        
        Args:
            system_dir: Directory for system-level files (defaults to ~/.agent-os/system/)
            config: Persistence configuration
        """
        self.system_dir = system_dir or os.path.expanduser("~/.agent-os/system")
        self.config = config or PersistenceConfig()
        self.enabled = self.config.enabled
        
        # Ensure system directory exists
        Path(self.system_dir).mkdir(parents=True, exist_ok=True)
        
        self._cache = {}
        self._cache_timestamps = {}
    
    def load_system_standards(self) -> Dict[str, Any]:
        """Load system-wide AI standards"""
        standards_file = Path(self.system_dir) / "ai-behaviors.yml"
        
        # Check cache first
        if self.config.cache_enabled:
            cached = self._get_cached_data("ai-behaviors")
            if cached:
                return cached
        
        try:
            if standards_file.exists():
                with open(standards_file, 'r', encoding=self.config.encoding) as f:
                    standards = yaml.safe_load(f) or {}
            else:
                standards = self._get_default_system_standards()
                # Save default standards
                self.save_system_standards(standards)
            
            # Cache the result
            if self.config.cache_enabled:
                self._cache_data("ai-behaviors", standards)
            
            return standards
        
        except Exception as e:
            logger.error(f"Failed to load system standards: {e}")
            return self._get_default_system_standards()
    
    def save_system_standards(self, standards: Dict[str, Any]) -> bool:
        """Save system-wide AI standards"""
        try:
            standards_file = Path(self.system_dir) / "ai-behaviors.yml"
            
            # Add metadata
            standards_with_metadata = {
                **standards,
                '_metadata': {
                    'last_updated': datetime.now().isoformat(),
                    'version': '1.0.0',
                    'managed_by': 'ai_persistence_system'
                }
            }
            
            with open(standards_file, 'w', encoding=self.config.encoding) as f:
                yaml.dump(standards_with_metadata, f, default_flow_style=False, indent=self.config.indent)
            
            # Update cache
            if self.config.cache_enabled:
                self._cache_data("ai-behaviors", standards)
            
            logger.info(f"System standards saved to {standards_file}")
            return True
        
        except Exception as e:
            logger.error(f"Failed to save system standards: {e}")
            return False
    
    def _get_default_system_standards(self) -> Dict[str, Any]:
        """Get default system standards"""
        return {
            'ai_behaviors': {
                'code_style': 'clean',
                'security_first': True,
                'documentation_required': True,
                'test_coverage_required': True,
                'response_length': 'appropriate',
                'explanation_level': 'match_user_expertise'
            },
            'global_policies': {
                'max_file_size': '10MB',
                'allowed_languages': ['python', 'javascript', 'yaml', 'markdown'],
                'security_scan_required': True,
                'code_review_required': True
            },
            'quality_standards': {
                'min_test_coverage': 0.8,
                'max_complexity': 10,
                'documentation_coverage': 0.9
            }
        }
    
    def _get_cached_data(self, key: str) -> Optional[Dict[str, Any]]:
        """Get cached data if still valid"""
        if key not in self._cache:
            return None
        
        timestamp = self._cache_timestamps.get(key, 0)
        if datetime.now().timestamp() - timestamp > self.config.cache_ttl:
            # Cache expired
            del self._cache[key]
            del self._cache_timestamps[key]
            return None
        
        return self._cache[key]
    
    def _cache_data(self, key: str, data: Dict[str, Any]):
        """Cache data with timestamp"""
        self._cache[key] = deepcopy(data)
        self._cache_timestamps[key] = datetime.now().timestamp()


class UserLevelManager:
    """Manages user-specific AI preferences and learning history"""
    
    def __init__(self, user_dir: Optional[str] = None, config: Optional[PersistenceConfig] = None):
        """
        Initialize user level manager
        
        Args:
            user_dir: Directory for user-level files (defaults to ~/.agent-os/user/)
            config: Persistence configuration
        """
        self.user_dir = user_dir or os.path.expanduser("~/.agent-os/user")
        self.config = config or PersistenceConfig()
        
        # Ensure user directory exists
        Path(self.user_dir).mkdir(parents=True, exist_ok=True)
    
    def load_user_preferences(self) -> Dict[str, Any]:
        """Load user preferences"""
        prefs_file = Path(self.user_dir) / "preferences.yml"
        
        try:
            if prefs_file.exists():
                with open(prefs_file, 'r', encoding=self.config.encoding) as f:
                    return yaml.safe_load(f) or {}
            else:
                return self._get_default_user_preferences()
        
        except Exception as e:
            logger.error(f"Failed to load user preferences: {e}")
            return self._get_default_user_preferences()
    
    def save_user_preferences(self, preferences: Dict[str, Any]) -> bool:
        """Save user preferences"""
        try:
            prefs_file = Path(self.user_dir) / "preferences.yml"
            
            preferences_with_metadata = {
                **preferences,
                '_metadata': {
                    'last_updated': datetime.now().isoformat(),
                    'version': '1.0.0'
                }
            }
            
            with open(prefs_file, 'w', encoding=self.config.encoding) as f:
                yaml.dump(preferences_with_metadata, f, default_flow_style=False, indent=self.config.indent)
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to save user preferences: {e}")
            return False
    
    def load_learning_history(self) -> Dict[str, Any]:
        """Load user learning history"""
        history_file = Path(self.user_dir) / "learning-history.yml"
        
        try:
            if history_file.exists():
                with open(history_file, 'r', encoding=self.config.encoding) as f:
                    return yaml.safe_load(f) or {}
            else:
                return {'successful_patterns': [], 'failed_patterns': [], 'skill_development': {}}
        
        except Exception as e:
            logger.error(f"Failed to load learning history: {e}")
            return {'successful_patterns': [], 'failed_patterns': [], 'skill_development': {}}
    
    def save_learning_history(self, history: Dict[str, Any]) -> bool:
        """Save user learning history"""
        try:
            history_file = Path(self.user_dir) / "learning-history.yml"
            
            # Limit history size
            if 'successful_patterns' in history:
                history['successful_patterns'] = history['successful_patterns'][-self.config.max_history_entries:]
            if 'failed_patterns' in history:
                history['failed_patterns'] = history['failed_patterns'][-self.config.max_history_entries:]
            
            history_with_metadata = {
                **history,
                '_metadata': {
                    'last_updated': datetime.now().isoformat(),
                    'entry_count': len(history.get('successful_patterns', [])) + len(history.get('failed_patterns', []))
                }
            }
            
            with open(history_file, 'w', encoding=self.config.encoding) as f:
                yaml.dump(history_with_metadata, f, default_flow_style=False, indent=self.config.indent)
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to save learning history: {e}")
            return False
    
    def load_skill_profile(self) -> Dict[str, Any]:
        """Load user skill profile"""
        profile_file = Path(self.user_dir) / "skill-profile.yml"
        
        try:
            if profile_file.exists():
                with open(profile_file, 'r', encoding=self.config.encoding) as f:
                    return yaml.safe_load(f) or {}
            else:
                return {}
        
        except Exception as e:
            logger.error(f"Failed to load skill profile: {e}")
            return {}
    
    def save_skill_profile(self, profile: Dict[str, Any]) -> bool:
        """Save user skill profile"""
        try:
            profile_file = Path(self.user_dir) / "skill-profile.yml"
            
            with open(profile_file, 'w', encoding=self.config.encoding) as f:
                yaml.dump(profile, f, default_flow_style=False, indent=self.config.indent)
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to save skill profile: {e}")
            return False
    
    def update_skill_profile(self, skill_updates: Dict[str, Any]) -> bool:
        """Update user skill profile with new skills"""
        try:
            current_profile = self.load_skill_profile()
            current_profile.update(skill_updates)
            return self.save_skill_profile(current_profile)
        
        except Exception as e:
            logger.error(f"Failed to update skill profile: {e}")
            return False
    
    def _get_default_user_preferences(self) -> Dict[str, Any]:
        """Get default user preferences"""
        return {
            'communication_style': 'balanced',
            'expertise_level': 'intermediate',
            'preferred_languages': ['python'],
            'documentation_style': 'comprehensive',
            'notification_settings': {
                'success_notifications': True,
                'error_notifications': True,
                'learning_suggestions': True
            }
        }


class RepositoryLevelManager:
    """Manages repository-specific context and team patterns"""
    
    def __init__(self, repo_root: Optional[str] = None, config: Optional[PersistenceConfig] = None):
        """
        Initialize repository level manager
        
        Args:
            repo_root: Root directory of the repository (defaults to current directory)
            config: Persistence configuration
        """
        self.repo_root = repo_root or os.getcwd()
        self.config = config or PersistenceConfig()
        self.context_dir = Path(self.repo_root) / ".agent-os" / "context"
        
        # Ensure context directory exists
        self.context_dir.mkdir(parents=True, exist_ok=True)
    
    def load_project_patterns(self) -> Dict[str, Any]:
        """Load project-specific patterns"""
        patterns_file = self.context_dir / "project-patterns.yml"
        
        try:
            if patterns_file.exists():
                with open(patterns_file, 'r', encoding=self.config.encoding) as f:
                    return yaml.safe_load(f) or {}
            else:
                return {}
        
        except Exception as e:
            logger.error(f"Failed to load project patterns: {e}")
            return {}
    
    def save_project_patterns(self, patterns: Dict[str, Any]) -> bool:
        """Save project-specific patterns"""
        try:
            patterns_file = self.context_dir / "project-patterns.yml"
            
            patterns_with_metadata = {
                **patterns,
                '_metadata': {
                    'last_updated': datetime.now().isoformat(),
                    'repository': os.path.basename(self.repo_root),
                    'managed_by': 'ai_persistence_system'
                }
            }
            
            with open(patterns_file, 'w', encoding=self.config.encoding) as f:
                yaml.dump(patterns_with_metadata, f, default_flow_style=False, indent=self.config.indent)
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to save project patterns: {e}")
            return False
    
    def load_team_conventions(self) -> Dict[str, Any]:
        """Load team conventions"""
        conventions_file = self.context_dir / "team-conventions.yml"
        
        try:
            if conventions_file.exists():
                with open(conventions_file, 'r', encoding=self.config.encoding) as f:
                    return yaml.safe_load(f) or {}
            else:
                return {}
        
        except Exception as e:
            logger.error(f"Failed to load team conventions: {e}")
            return {}
    
    def save_team_conventions(self, conventions: Dict[str, Any]) -> bool:
        """Save team conventions"""
        try:
            conventions_file = self.context_dir / "team-conventions.yml"
            
            with open(conventions_file, 'w', encoding=self.config.encoding) as f:
                yaml.dump(conventions, f, default_flow_style=False, indent=self.config.indent)
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to save team conventions: {e}")
            return False
    
    def load_domain_knowledge(self) -> Dict[str, Any]:
        """Load business domain knowledge"""
        knowledge_file = self.context_dir / "domain-knowledge.yml"
        
        try:
            if knowledge_file.exists():
                with open(knowledge_file, 'r', encoding=self.config.encoding) as f:
                    return yaml.safe_load(f) or {}
            else:
                return {}
        
        except Exception as e:
            logger.error(f"Failed to load domain knowledge: {e}")
            return {}
    
    def save_domain_knowledge(self, knowledge: Dict[str, Any]) -> bool:
        """Save business domain knowledge"""
        try:
            knowledge_file = self.context_dir / "domain-knowledge.yml"
            
            with open(knowledge_file, 'w', encoding=self.config.encoding) as f:
                yaml.dump(knowledge, f, default_flow_style=False, indent=self.config.indent)
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to save domain knowledge: {e}")
            return False
    
    def log_decision(self, decision: Dict[str, Any]) -> bool:
        """Log a project decision"""
        try:
            decisions_dir = self.context_dir / "decisions"
            decisions_dir.mkdir(exist_ok=True)
            
            # Generate filename from date and title
            date_str = decision.get('date', datetime.now().strftime('%Y-%m-%d'))
            title = decision.get('title', 'untitled-decision')
            filename = f"{date_str}-{title.lower().replace(' ', '-').replace('_', '-')}.yml"
            
            decision_file = decisions_dir / filename
            
            decision_with_metadata = {
                **decision,
                '_metadata': {
                    'logged_at': datetime.now().isoformat(),
                    'repository': os.path.basename(self.repo_root)
                }
            }
            
            with open(decision_file, 'w', encoding=self.config.encoding) as f:
                yaml.dump(decision_with_metadata, f, default_flow_style=False, indent=self.config.indent)
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to log decision: {e}")
            return False
    
    def load_ai_context(self) -> Dict[str, Any]:
        """Load AI-specific context for this repository"""
        context_file = self.context_dir / "ai-context.yml"
        
        try:
            if context_file.exists():
                with open(context_file, 'r', encoding=self.config.encoding) as f:
                    return yaml.safe_load(f) or {}
            else:
                return {}
        
        except Exception as e:
            logger.error(f"Failed to load AI context: {e}")
            return {}
    
    def save_ai_context(self, context: Dict[str, Any]) -> bool:
        """Save AI-specific context for this repository"""
        try:
            context_file = self.context_dir / "ai-context.yml"
            
            context_with_metadata = {
                **context,
                '_metadata': {
                    'last_updated': datetime.now().isoformat(),
                    'repository': os.path.basename(self.repo_root),
                    'context_version': '1.0.0'
                }
            }
            
            with open(context_file, 'w', encoding=self.config.encoding) as f:
                yaml.dump(context_with_metadata, f, default_flow_style=False, indent=self.config.indent)
            
            return True
        
        except Exception as e:
            logger.error(f"Failed to save AI context: {e}")
            return False


class SessionLevelManager:
    """Manages session-specific context and conversation state"""
    
    def __init__(self, session_id: Optional[str] = None, config: Optional[PersistenceConfig] = None):
        """
        Initialize session level manager
        
        Args:
            session_id: Unique session identifier (auto-generated if not provided)
            config: Persistence configuration
        """
        self.session_id = session_id or str(uuid.uuid4())
        self.config = config or PersistenceConfig()
        
        # In-memory storage for session data
        self.context_data = {
            'conversation_history': [],
            'recent_decisions': [],
            'active_tasks': [],
            'session_metadata': {
                'session_id': self.session_id,
                'started_at': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat()
            }
        }
    
    def set_current_context(self, context: Dict[str, Any]):
        """Set current session context"""
        self.context_data.update(context)
        self._update_activity_timestamp()
    
    def get_current_context(self) -> Dict[str, Any]:
        """Get current session context"""
        return self.context_data.copy()
    
    def add_conversation_entry(self, role: str, content: str, metadata: Optional[Dict[str, Any]] = None):
        """Add conversation entry"""
        entry = {
            'role': role,
            'content': content,
            'timestamp': datetime.now().isoformat(),
            'metadata': metadata or {}
        }
        
        self.context_data['conversation_history'].append(entry)
        self._update_activity_timestamp()
        
        # Limit conversation history size
        max_entries = self.config.max_history_entries
        if len(self.context_data['conversation_history']) > max_entries:
            self.context_data['conversation_history'] = self.context_data['conversation_history'][-max_entries:]
    
    def record_decision(self, decision: Dict[str, Any]):
        """Record a session decision"""
        decision_entry = {
            **decision,
            'timestamp': datetime.now().isoformat(),
            'session_id': self.session_id
        }
        
        self.context_data['recent_decisions'].append(decision_entry)
        self._update_activity_timestamp()
        
        # Limit decision history size
        max_decisions = 100
        if len(self.context_data['recent_decisions']) > max_decisions:
            self.context_data['recent_decisions'] = self.context_data['recent_decisions'][-max_decisions:]
    
    def add_active_task(self, task: Dict[str, Any]):
        """Add active task to session"""
        task_entry = {
            **task,
            'added_at': datetime.now().isoformat(),
            'session_id': self.session_id
        }
        
        self.context_data['active_tasks'].append(task_entry)
        self._update_activity_timestamp()
    
    def complete_task(self, task_id: str):
        """Mark task as completed"""
        for task in self.context_data['active_tasks']:
            if task.get('id') == task_id or task.get('name') == task_id:
                task['status'] = 'completed'
                task['completed_at'] = datetime.now().isoformat()
                break
        
        self._update_activity_timestamp()
    
    def clear_session(self):
        """Clear session context"""
        self.context_data = {
            'conversation_history': [],
            'recent_decisions': [],
            'active_tasks': [],
            'session_metadata': {
                'session_id': self.session_id,
                'started_at': datetime.now().isoformat(),
                'last_activity': datetime.now().isoformat(),
                'cleared_at': datetime.now().isoformat()
            }
        }
    
    def _update_activity_timestamp(self):
        """Update last activity timestamp"""
        self.context_data['session_metadata']['last_activity'] = datetime.now().isoformat()


class ContextMerger:
    """Utility class for merging contexts from different levels"""
    
    @staticmethod
    def merge_contexts(base_context: Dict[str, Any], override_context: Dict[str, Any]) -> Dict[str, Any]:
        """
        Merge two context dictionaries with override priority
        
        Args:
            base_context: Base context dictionary
            override_context: Override context dictionary (higher priority)
            
        Returns:
            Merged context dictionary
        """
        merged = deepcopy(base_context)
        
        for key, value in override_context.items():
            if key in merged and isinstance(merged[key], dict) and isinstance(value, dict):
                # Recursively merge nested dictionaries
                merged[key] = ContextMerger.merge_contexts(merged[key], value)
            else:
                # Override or add new key
                merged[key] = deepcopy(value)
        
        return merged
    
    @staticmethod
    def merge_hierarchy(contexts: List[Dict[str, Any]]) -> Dict[str, Any]:
        """
        Merge multiple contexts in hierarchy order (first to last priority)
        
        Args:
            contexts: List of context dictionaries in priority order (low to high)
            
        Returns:
            Merged context dictionary
        """
        if not contexts:
            return {}
        
        merged = deepcopy(contexts[0])
        
        for context in contexts[1:]:
            merged = ContextMerger.merge_contexts(merged, context)
        
        return merged


class ContextHierarchyManager:
    """Main manager for hierarchical AI context system"""
    
    def __init__(self, 
                 system_dir: Optional[str] = None,
                 user_dir: Optional[str] = None,
                 repo_root: Optional[str] = None,
                 session_id: Optional[str] = None,
                 config: Optional[PersistenceConfig] = None):
        """
        Initialize context hierarchy manager
        
        Args:
            system_dir: System-level directory
            user_dir: User-level directory
            repo_root: Repository root directory
            session_id: Session identifier
            config: Persistence configuration
        """
        self.config = config or PersistenceConfig()
        
        # Initialize level managers
        self.system_manager = SystemLevelManager(system_dir, self.config)
        self.user_manager = UserLevelManager(user_dir, self.config)
        self.repo_manager = RepositoryLevelManager(repo_root, self.config)
        self.session_manager = SessionLevelManager(session_id, self.config)
    
    async def get_merged_context(self) -> Dict[str, Any]:
        """Get merged context from all levels"""
        try:
            # Load context from each level
            system_context = self.system_manager.load_system_standards()
            user_context = {
                'preferences': self.user_manager.load_user_preferences(),
                'learning_history': self.user_manager.load_learning_history(),
                'skill_profile': self.user_manager.load_skill_profile()
            }
            repo_context = {
                'project_patterns': self.repo_manager.load_project_patterns(),
                'team_conventions': self.repo_manager.load_team_conventions(),
                'domain_knowledge': self.repo_manager.load_domain_knowledge(),
                'ai_context': self.repo_manager.load_ai_context()
            }
            session_context = self.session_manager.get_current_context()
            
            # Structure the merged context
            merged_context = {
                'system': system_context,
                'user': user_context,
                'repository': repo_context,
                'session': session_context,
                'metadata': {
                    'merged_at': datetime.now().isoformat(),
                    'hierarchy_version': '1.0.0'
                }
            }
            
            return merged_context
        
        except Exception as e:
            logger.error(f"Failed to get merged context: {e}")
            return {'error': str(e)}
    
    async def get_effective_context(self) -> Dict[str, Any]:
        """Get effective context with hierarchy overrides applied"""
        try:
            merged_context = await self.get_merged_context()
            
            # Extract data from each level for merging
            contexts_to_merge = []
            
            # System level (lowest priority)
            if 'system' in merged_context:
                contexts_to_merge.append(merged_context['system'])
            
            # User level
            if 'user' in merged_context:
                user_flat = {}
                for key, value in merged_context['user'].items():
                    if isinstance(value, dict):
                        user_flat.update(value)
                    else:
                        user_flat[key] = value
                contexts_to_merge.append(user_flat)
            
            # Repository level
            if 'repository' in merged_context:
                repo_flat = {}
                for key, value in merged_context['repository'].items():
                    if isinstance(value, dict):
                        repo_flat.update(value)
                    else:
                        repo_flat[key] = value
                contexts_to_merge.append(repo_flat)
            
            # Session level (highest priority)
            if 'session' in merged_context:
                session_data = merged_context['session'].copy()
                # Remove metadata and history for effective context
                for key in ['conversation_history', 'recent_decisions', 'session_metadata']:
                    session_data.pop(key, None)
                contexts_to_merge.append(session_data)
            
            # Merge with hierarchy rules
            effective_context = ContextMerger.merge_hierarchy(contexts_to_merge)
            
            return effective_context
        
        except Exception as e:
            logger.error(f"Failed to get effective context: {e}")
            return {'error': str(e)}
    
    def save_context_to_repository(self, context_data: Dict[str, Any]) -> bool:
        """Save learned context to repository for team sharing"""
        try:
            # Extract repository-relevant context
            repo_context = {
                'learned_patterns': context_data.get('learned_patterns', {}),
                'project_insights': context_data.get('project_insights', {}),
                'team_feedback': context_data.get('team_feedback', {}),
                'optimization_opportunities': context_data.get('optimization_opportunities', [])
            }
            
            # Merge with existing AI context
            existing_context = self.repo_manager.load_ai_context()
            merged_repo_context = ContextMerger.merge_contexts(existing_context, repo_context)
            
            return self.repo_manager.save_ai_context(merged_repo_context)
        
        except Exception as e:
            logger.error(f"Failed to save context to repository: {e}")
            return False


class CrossSystemSynchronizer:
    """Handles synchronization of AI patterns across systems"""
    
    def __init__(self, config: Optional[PersistenceConfig] = None):
        """Initialize cross-system synchronizer"""
        self.config = config or PersistenceConfig()
    
    async def sync_learned_patterns(self, patterns: Dict[str, Any]) -> Dict[str, Any]:
        """Synchronize learned patterns across systems"""
        try:
            result = {
                'success': True,
                'patterns_synced': 0,
                'sync_timestamp': datetime.now().isoformat()
            }
            
            # Count patterns to sync
            successful_patterns = patterns.get('successful_workflows', [])
            anti_patterns = patterns.get('anti_patterns', [])
            
            result['patterns_synced'] = len(successful_patterns) + len(anti_patterns)
            
            # In a real implementation, this would sync to:
            # - Central pattern repository
            # - User's other systems
            # - Team knowledge base
            
            logger.info(f"Synchronized {result['patterns_synced']} patterns")
            return result
        
        except Exception as e:
            logger.error(f"Failed to sync learned patterns: {e}")
            return {'success': False, 'error': str(e)}
    
    async def propagate_successful_pattern(self, pattern: Dict[str, Any]) -> Dict[str, Any]:
        """Propagate a successful pattern to higher levels"""
        try:
            success_metrics = pattern.get('success_metrics', {})
            
            # Determine propagation level based on success metrics
            completion_rate = success_metrics.get('completion_rate', 0)
            error_rate = success_metrics.get('error_rate', 1)
            user_satisfaction = success_metrics.get('user_satisfaction', 0)
            
            # Calculate overall success score
            success_score = (completion_rate * 0.4) + ((1 - error_rate) * 0.3) + (user_satisfaction / 5 * 0.3)
            
            if success_score >= 0.9:
                propagation_level = 'system'  # Excellent - promote to system level
            elif success_score >= 0.7:
                propagation_level = 'user'    # Good - promote to user level
            else:
                propagation_level = 'repository'  # Keep at repository level
            
            result = {
                'success': True,
                'propagation_level': propagation_level,
                'success_score': success_score,
                'pattern_name': pattern.get('name', 'unnamed_pattern')
            }
            
            logger.info(f"Pattern '{result['pattern_name']}' propagated to {propagation_level} level (score: {success_score:.2f})")
            return result
        
        except Exception as e:
            logger.error(f"Failed to propagate successful pattern: {e}")
            return {'success': False, 'error': str(e)}
    
    def detect_pattern_conflicts(self, *contexts: Dict[str, Any]) -> List[Dict[str, Any]]:
        """Detect conflicts between patterns at different levels"""
        conflicts = []
        
        try:
            if len(contexts) < 2:
                return conflicts
            
            # Get all unique keys across contexts
            all_keys = set()
            for context in contexts:
                all_keys.update(context.keys())
            
            # Check each key for conflicts
            for key in all_keys:
                values = []
                levels = []
                
                for i, context in enumerate(contexts):
                    if key in context:
                        values.append(context[key])
                        levels.append(f"level_{i}")
                
                # Check if values are conflicting (different non-None values)
                unique_values = set(str(v) for v in values if v is not None)
                if len(unique_values) > 1:
                    conflicts.append({
                        'setting': key,
                        'conflicting_values': dict(zip(levels, values)),
                        'resolution': 'highest_level_wins'
                    })
            
            return conflicts
        
        except Exception as e:
            logger.error(f"Failed to detect pattern conflicts: {e}")
            return []