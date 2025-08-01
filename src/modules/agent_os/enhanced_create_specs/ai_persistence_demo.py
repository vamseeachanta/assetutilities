#!/usr/bin/env python3
"""
AI Persistence System Demo

Demonstrates the complete Multi-Level AI Persistence System including:
- System-level standards and behaviors
- User-level preferences and learning
- Repository-level context and team patterns  
- Session-level conversation and decisions
- Hierarchical context merging
- Cross-system synchronization

Usage:
    python ai_persistence_demo.py
"""

import os
import asyncio
from pathlib import Path

# Import AI persistence components
from ai_persistence_system import (
    ContextHierarchyManager,
    SystemLevelManager,
    UserLevelManager,
    RepositoryLevelManager,
    SessionLevelManager,
    ContextMerger,
    CrossSystemSynchronizer,
    PersistenceConfig
)


async def main():
    """Main demo function"""
    print("🧠 AI Persistence System Demo")
    print("=" * 50)
    
    # 1. Initialize AI persistence system
    print("\n1️⃣ Initializing AI Persistence System...")
    
    # Create custom configuration
    config = PersistenceConfig(
        enabled=True,
        auto_save=True,
        cache_enabled=True,
        file_format="yaml"
    )
    
    # Initialize hierarchy manager for this repository
    hierarchy_manager = ContextHierarchyManager(
        repo_root='.',
        config=config
    )
    
    print("✓ AI persistence system initialized")
    print(f"   Repository: {os.path.basename(os.getcwd())}")
    print(f"   Session ID: {hierarchy_manager.session_manager.session_id[:8]}...")
    
    # 2. Demonstrate system-level standards
    print("\n2️⃣ System-Level AI Standards...")
    
    system_standards = hierarchy_manager.system_manager.load_system_standards()
    print(f"✓ System standards loaded")
    print(f"   Code style: {system_standards.get('ai_behaviors', {}).get('code_style', 'unknown')}")
    print(f"   Security first: {system_standards.get('ai_behaviors', {}).get('security_first', False)}")
    print(f"   Documentation required: {system_standards.get('ai_behaviors', {}).get('documentation_required', False)}")
    
    # 3. Demonstrate user-level preferences
    print("\n3️⃣ User-Level Preferences...")
    
    # Create sample user preferences
    user_preferences = {
        'communication_style': 'detailed_explanations',
        'expertise_level': 'senior_developer',
        'preferred_languages': ['python', 'yaml', 'markdown'],
        'working_style': {
            'prefers_examples': True,
            'likes_step_by_step': True,
            'wants_background_context': True
        }
    }
    
    hierarchy_manager.user_manager.save_user_preferences(user_preferences)
    
    loaded_prefs = hierarchy_manager.user_manager.load_user_preferences()
    print(f"✓ User preferences saved and loaded")
    print(f"   Communication style: {loaded_prefs.get('communication_style', 'unknown')}")
    print(f"   Expertise level: {loaded_prefs.get('expertise_level', 'unknown')}")
    print(f"   Preferred languages: {len(loaded_prefs.get('preferred_languages', []))}")
    
    # 4. Demonstrate repository-level context
    print("\n4️⃣ Repository-Level Context...")
    
    # Load existing repository context (from files we created)
    project_patterns = hierarchy_manager.repo_manager.load_project_patterns()
    team_conventions = hierarchy_manager.repo_manager.load_team_conventions()
    domain_knowledge = hierarchy_manager.repo_manager.load_domain_knowledge()
    
    print(f"✓ Repository context loaded")
    print(f"   Project type: {project_patterns.get('architecture_patterns', {}).get('type', 'unknown')}")
    print(f"   Primary language: {project_patterns.get('architecture_patterns', {}).get('primary_language', 'unknown')}")
    print(f"   Business domain: {domain_knowledge.get('business_domain', 'unknown')}")
    print(f"   Team practices: {len(team_conventions.get('development_practices', {}))}")
    
    # 5. Demonstrate session-level context
    print("\n5️⃣ Session-Level Context...")
    
    # Simulate a development session
    hierarchy_manager.session_manager.add_conversation_entry(
        'user', 
        'I want to implement the AI persistence system for enhanced create-specs'
    )
    hierarchy_manager.session_manager.add_conversation_entry(
        'assistant',
        'I will implement a multi-level AI persistence system with system, user, repository, and session levels.'
    )
    
    # Record a decision
    hierarchy_manager.session_manager.record_decision({
        'decision': 'Use YAML format for all persistence files',
        'rationale': 'Human readable, supports comments, version control friendly',
        'impact': 'all_persistence_levels'
    })
    
    # Add active task
    hierarchy_manager.session_manager.add_active_task({
        'id': 'task-4-persistence',
        'name': 'Implement AI Persistence System',
        'status': 'in_progress',
        'priority': 'high'
    })
    
    session_context = hierarchy_manager.session_manager.get_current_context()
    print(f"✓ Session context updated")
    print(f"   Conversation entries: {len(session_context['conversation_history'])}")
    print(f"   Recent decisions: {len(session_context['recent_decisions'])}")
    print(f"   Active tasks: {len(session_context['active_tasks'])}")
    
    # 6. Demonstrate hierarchical context merging
    print("\n6️⃣ Hierarchical Context Merging...")
    
    merged_context = await hierarchy_manager.get_merged_context()
    
    print(f"✓ Context merged from all levels")
    print(f"   System level: {'✓' if merged_context.get('system') else '✗'}")
    print(f"   User level: {'✓' if merged_context.get('user') else '✗'}")
    print(f"   Repository level: {'✓' if merged_context.get('repository') else '✗'}")
    print(f"   Session level: {'✓' if merged_context.get('session') else '✗'}")
    
    # Show effective context with overrides
    effective_context = await hierarchy_manager.get_effective_context()
    print(f"   Effective context keys: {len(effective_context)}")
    
    # 7. Demonstrate context learning and saving
    print("\n7️⃣ Context Learning and Repository Sharing...")
    
    # Simulate learning from successful implementation
    learned_context = {
        'learned_patterns': {
            'ai_persistence_implementation': {
                'success_rate': 0.95,
                'completion_time': '4_hours',
                'key_insights': [
                    'YAML format works excellently for configuration',
                    'Hierarchical merging provides powerful context control',
                    'Repository storage enables effective team knowledge sharing',
                    'Session management maintains conversation continuity'
                ],
                'best_practices': [
                    'Always validate file permissions before writing',
                    'Use structured metadata for tracking',
                    'Implement proper error handling and fallbacks',
                    'Cache frequently accessed context data'
                ]
            }
        },
        'project_insights': {
            'complexity_level': 'high',
            'ai_assistance_effectiveness': 'very_high',
            'team_collaboration_impact': 'positive',
            'knowledge_preservation': 'excellent'
        },
        'optimization_opportunities': [
            'Add encryption for sensitive context data',
            'Implement background synchronization',
            'Add context search and discovery features',
            'Create visual context hierarchy browser'
        ]
    }
    
    save_result = hierarchy_manager.save_context_to_repository(learned_context)
    print(f"✓ Learned context saved to repository: {save_result}")
    
    # 8. Demonstrate cross-system synchronization
    print("\n8️⃣ Cross-System Synchronization...")
    
    synchronizer = CrossSystemSynchronizer(config)
    
    # Test pattern synchronization
    patterns_to_sync = {
        'successful_workflows': [
            {
                'name': 'ai_persistence_implementation',
                'success_rate': 0.95,
                'context': 'python_utility_projects',
                'reusability': 'high'
            }
        ]
    }
    
    sync_result = await synchronizer.sync_learned_patterns(patterns_to_sync)
    print(f"✓ Pattern synchronization: {sync_result['success']}")
    print(f"   Patterns synced: {sync_result['patterns_synced']}")
    
    # Test pattern propagation
    successful_pattern = {
        'name': 'multi_level_ai_persistence',
        'success_metrics': {
            'completion_rate': 0.98,
            'error_rate': 0.02,
            'user_satisfaction': 4.9
        },
        'implementation_details': {
            'components': ['system_manager', 'user_manager', 'repo_manager', 'session_manager'],
            'time_to_implement': '4_hours',
            'complexity': 'high'
        }
    }
    
    propagation_result = await synchronizer.propagate_successful_pattern(successful_pattern)
    print(f"✓ Pattern propagation: {propagation_result['success']}")
    print(f"   Propagation level: {propagation_result['propagation_level']}")
    print(f"   Success score: {propagation_result['success_score']:.2f}")
    
    # 9. Demonstrate conflict detection
    print("\n9️⃣ Context Conflict Detection...")
    
    # Create conflicting contexts for demonstration
    system_context = {'code_style': 'pep8', 'testing_required': True}
    user_context = {'code_style': 'black', 'documentation_style': 'sphinx'}  
    repo_context = {'code_style': 'ruff', 'testing_required': False}
    
    conflicts = synchronizer.detect_pattern_conflicts(system_context, user_context, repo_context)
    
    print(f"✓ Conflict detection completed")
    print(f"   Conflicts found: {len(conflicts)}")
    for conflict in conflicts:
        print(f"   - {conflict['setting']}: {conflict['resolution']}")
    
    # 10. Summary and next steps
    print("\n🎯 AI Persistence System Summary")
    print("=" * 50)
    
    print("✅ IMPLEMENTED CAPABILITIES:")
    print("   • Multi-level context hierarchy (System/User/Repository/Session)")
    print("   • Hierarchical context merging with proper override rules")
    print("   • Repository-focused storage for team collaboration")
    print("   • Session management for conversation continuity")
    print("   • Learning pattern capture and sharing")
    print("   • Cross-system synchronization and propagation")
    print("   • Conflict detection and resolution")
    print("   • YAML-based human-readable storage")
    
    print(f"\n🎨 CONTEXT STORAGE LOCATIONS:")
    print(f"   • System: ~/.agent-os/system/ (global standards)")
    print(f"   • User: ~/.agent-os/user/ (personal preferences)")
    print(f"   • Repository: .agent-os/context/ (team knowledge)")
    print(f"   • Session: Memory (conversation state)")
    
    print(f"\n🔄 CONTEXT HIERARCHY:")
    print(f"   Session > Repository > User > System")
    print(f"   (Higher levels override lower levels)")
    
    print(f"\n📈 BENEFITS DELIVERED:")
    print("   • Consistent AI behavior across all repositories")
    print("   • Team knowledge preservation and sharing")
    print("   • Personal learning accumulation")
    print("   • Conversation continuity across sessions")
    print("   • Automatic pattern recognition and improvement")
    
    print("\n🚀 AI Persistence System is fully operational!")


if __name__ == '__main__':
    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\n⚠ Demo cancelled by user")
    except Exception as e:
        print(f"\n✗ Demo error: {e}")
        import traceback
        traceback.print_exc()