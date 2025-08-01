#!/usr/bin/env python3
"""
Git Submodule Setup for Cross-Repository Integration

This script sets up git submodules for the AssetUtilities hub repository
to enable cross-repository referencing and shared sub-agent functionality.

Usage:
    python git_submodule_setup.py --setup
    python git_submodule_setup.py --status
    python git_submodule_setup.py --update
"""

import os
import sys
import argparse
import subprocess
import json
import yaml
from pathlib import Path
from typing import Dict, List, Optional, Any
from dataclasses import dataclass, asdict

from cross_repository_integration import (
    CrossRepositoryManager,
    GitSubmoduleIntegration,
    ParsedReference
)


@dataclass
class SubmoduleConfig:
    """Configuration for a git submodule"""
    name: str
    repository: str
    path: str
    branch: str = "main"
    enabled: bool = True
    description: Optional[str] = None


@dataclass
class CrossRepoSetup:
    """Complete cross-repository setup configuration"""
    hub_repository: str
    base_directory: str
    submodules: List[SubmoduleConfig]
    cross_repo_config: Dict[str, Any]


class GitSubmoduleSetupManager:
    """Manager for setting up git submodules for cross-repository integration"""
    
    def __init__(self, config_path: Optional[str] = None):
        """
        Initialize the setup manager
        
        Args:
            config_path: Path to configuration file, defaults to .agent-os/cross-repo-config.yml
        """
        self.config_path = config_path or '.agent-os/cross-repo-config.yml'
        self.cross_repo_manager = CrossRepositoryManager()
        self.git_integration = GitSubmoduleIntegration()
        self.setup_config = None
        
        # Load configuration if it exists
        self._load_configuration()
    
    def _load_configuration(self):
        """Load cross-repository configuration from file"""
        config_path = Path(self.config_path)
        
        if config_path.exists():
            try:
                with open(config_path, 'r', encoding='utf-8') as f:
                    config_data = yaml.safe_load(f)
                
                # Convert to setup configuration
                self.setup_config = self._parse_configuration(config_data)
                print(f"✓ Loaded configuration from {self.config_path}")
                
            except Exception as e:
                print(f"⚠ Warning: Failed to load configuration from {self.config_path}: {e}")
                self.setup_config = self._get_default_configuration()
        else:
            print(f"ℹ No configuration found at {self.config_path}, using defaults")
            self.setup_config = self._get_default_configuration()
    
    def _parse_configuration(self, config_data: Dict) -> CrossRepoSetup:
        """Parse YAML configuration into setup configuration"""
        cross_repo = config_data.get('cross_repo', {})
        
        # Parse submodules
        submodules = []
        for submod_config in cross_repo.get('submodules', []):
            submodule = SubmoduleConfig(
                name=submod_config['name'],
                repository=submod_config['repository'],
                path=submod_config['path'],
                branch=submod_config.get('branch', 'main'),
                enabled=submod_config.get('enabled', True),
                description=submod_config.get('description')
            )
            submodules.append(submodule)
        
        return CrossRepoSetup(
            hub_repository=cross_repo.get('hub_repository', 'assetutilities'),
            base_directory=cross_repo.get('base_directory', 'src/external'),
            submodules=submodules,
            cross_repo_config=cross_repo
        )
    
    def _get_default_configuration(self) -> CrossRepoSetup:
        """Get default cross-repository configuration"""
        default_submodules = [
            SubmoduleConfig(
                name='assetutilities',
                repository='https://github.com/vamseeachanta/assetutilities.git',
                path='src/external/assetutilities',
                branch='main',
                description='AssetUtilities hub repository for shared components'
            ),
            SubmoduleConfig(
                name='agent-os-core',
                repository='https://github.com/buildermethods/agent-os-core.git',
                path='src/external/agent-os-core',
                branch='main',
                enabled=False,  # Optional - only if available
                description='Agent OS core components (optional)'
            )
        ]
        
        return CrossRepoSetup(
            hub_repository='assetutilities',
            base_directory='src/external',
            submodules=default_submodules,
            cross_repo_config={
                'hub_repository': 'assetutilities',
                'base_directory': 'src/external',
                'enabled': True,
                'auto_update': False
            }
        )
    
    def save_configuration(self):
        """Save current configuration to file"""
        if not self.setup_config:
            print("⚠ No configuration to save")
            return False
        
        try:
            # Create directory if it doesn't exist
            config_path = Path(self.config_path)
            config_path.parent.mkdir(parents=True, exist_ok=True)
            
            # Convert to YAML format
            config_data = {
                'cross_repo': {
                    'hub_repository': self.setup_config.hub_repository,
                    'base_directory': self.setup_config.base_directory,
                    'submodules': [
                        asdict(submod) for submod in self.setup_config.submodules
                    ],
                    **self.setup_config.cross_repo_config
                }
            }
            
            with open(config_path, 'w', encoding='utf-8') as f:
                yaml.dump(config_data, f, default_flow_style=False, indent=2)
            
            print(f"✓ Configuration saved to {self.config_path}")
            return True
            
        except Exception as e:
            print(f"✗ Failed to save configuration: {e}")
            return False
    
    def setup_submodules(self) -> Dict[str, Any]:
        """Set up all configured git submodules"""
        if not self.setup_config:
            return {'success': False, 'error': 'No configuration loaded'}
        
        results = {
            'success': True,
            'submodules_added': [],
            'submodules_failed': [],
            'skipped': [],
            'errors': []
        }
        
        # Create base directory
        base_dir = Path(self.setup_config.base_directory)
        base_dir.mkdir(parents=True, exist_ok=True)
        print(f"✓ Created base directory: {base_dir}")
        
        # Process each submodule
        for submodule in self.setup_config.submodules:
            if not submodule.enabled:
                results['skipped'].append(submodule.name)
                print(f"- Skipping disabled submodule: {submodule.name}")
                continue
            
            print(f"\n📦 Setting up submodule: {submodule.name}")
            print(f"   Repository: {submodule.repository}")
            print(f"   Path: {submodule.path}")
            print(f"   Branch: {submodule.branch}")
            
            # Check if submodule already exists
            if self.git_integration.check_submodule_exists(submodule.name):
                print(f"   ℹ Submodule {submodule.name} already exists")
                results['skipped'].append(submodule.name)
                continue
            
            # Add the submodule
            add_result = self.git_integration.add_submodule({
                'repository': submodule.repository,
                'path': submodule.path,
                'branch': submodule.branch
            })
            
            if add_result['success']:
                print(f"   ✓ Successfully added submodule: {submodule.name}")
                results['submodules_added'].append(submodule.name)
            else:
                print(f"   ✗ Failed to add submodule: {submodule.name}")
                print(f"     Error: {add_result['error']}")
                results['submodules_failed'].append({
                    'name': submodule.name,
                    'error': add_result['error']
                })
                results['success'] = False
        
        # Initialize all submodules
        if results['submodules_added']:
            print(f"\n🔄 Initializing submodules...")
            init_result = self.git_integration.initialize_submodules()
            
            if init_result['success']:
                print(f"✓ Successfully initialized all submodules")
            else:
                print(f"⚠ Warning: Submodule initialization had issues: {init_result['error']}")
                results['errors'].append(f"Initialization warning: {init_result['error']}")
        
        return results
    
    def get_status(self) -> Dict[str, Any]:
        """Get status of all submodules and cross-repository setup"""
        status = {
            'configuration_loaded': self.setup_config is not None,
            'configuration_path': self.config_path,
            'submodules': {},
            'cross_repo_ready': False,
            'recommendations': []
        }
        
        if not self.setup_config:
            status['recommendations'].append('Run setup to create initial configuration')
            return status
        
        # Check git submodule status
        submodule_status = self.git_integration.get_submodule_status()
        
        if submodule_status.get('error'):
            status['git_error'] = submodule_status['error']
            status['recommendations'].append('Ensure you are in a git repository')
            return status
        
        # Process each configured submodule
        for submodule in self.setup_config.submodules:
            submod_info = {
                'configured': True,
                'exists': False,
                'status': 'not-found',
                'path': submodule.path,
                'branch': submodule.branch,
                'enabled': submodule.enabled
            }
            
            # Find matching git submodule
            for git_submod in submodule_status.get('submodules', []):
                if git_submod['name'] == submodule.path or git_submod['name'].endswith(submodule.name):
                    submod_info['exists'] = True
                    submod_info['status'] = git_submod['status']
                    submod_info['commit'] = git_submod['commit']
                    submod_info['current_branch'] = git_submod['branch']
                    break
            
            status['submodules'][submodule.name] = submod_info
        
        # Check if cross-repository setup is ready
        ready_count = sum(1 for info in status['submodules'].values() 
                         if info['exists'] and info['status'] in ['up-to-date', 'different-commit'])
        total_enabled = sum(1 for submod in self.setup_config.submodules if submod.enabled)
        
        status['cross_repo_ready'] = ready_count > 0
        status['ready_submodules'] = ready_count
        status['total_enabled_submodules'] = total_enabled
        
        # Generate recommendations
        if ready_count == 0:
            status['recommendations'].append('Run setup to add git submodules')
        elif ready_count < total_enabled:
            status['recommendations'].append('Some submodules are missing - run setup to add them')
        
        not_initialized = [name for name, info in status['submodules'].items() 
                          if info['exists'] and info['status'] == 'not-initialized']
        if not_initialized:
            status['recommendations'].append(f'Initialize submodules: {", ".join(not_initialized)}')
        
        different_commits = [name for name, info in status['submodules'].items() 
                           if info['exists'] and info['status'] == 'different-commit']
        if different_commits:
            status['recommendations'].append(f'Update submodules: {", ".join(different_commits)}')
        
        return status
    
    def update_submodules(self) -> Dict[str, Any]:
        """Update all existing submodules"""
        if not self.setup_config:
            return {'success': False, 'error': 'No configuration loaded'}
        
        results = {
            'success': True,
            'updated': [],
            'failed': [],
            'skipped': []
        }
        
        # Get current status
        status = self.get_status()
        
        # Update each existing submodule
        for submodule_name, submod_info in status['submodules'].items():
            if not submod_info['exists']:
                results['skipped'].append(f"{submodule_name} (not found)")
                continue
            
            if submod_info['status'] == 'up-to-date':
                results['skipped'].append(f"{submodule_name} (already up-to-date)")
                continue
            
            print(f"🔄 Updating submodule: {submodule_name}")
            
            # Find the configured submodule path
            submodule_path = submod_info['path']
            update_result = self.git_integration.update_submodule(submodule_path)
            
            if update_result['success']:
                print(f"✓ Successfully updated: {submodule_name}")
                results['updated'].append(submodule_name)
            else:
                print(f"✗ Failed to update: {submodule_name}")
                print(f"  Error: {update_result['error']}")
                results['failed'].append({
                    'name': submodule_name,
                    'error': update_result['error']
                })
                results['success'] = False
        
        return results
    
    def test_cross_repo_references(self) -> Dict[str, Any]:
        """Test cross-repository reference resolution"""
        test_results = {
            'success': True,
            'tests_run': 0,
            'tests_passed': 0,
            'tests_failed': 0,
            'test_details': []
        }
        
        if not self.setup_config:
            return {'success': False, 'error': 'No configuration loaded'}
        
        # Test references for each enabled submodule
        for submodule in self.setup_config.submodules:
            if not submodule.enabled:
                continue
            
            # Create test reference
            test_reference = f"@github:{submodule.name}/README.md"
            test_results['tests_run'] += 1
            
            print(f"🧪 Testing reference: {test_reference}")
            
            # Test parsing
            parsed = self.cross_repo_manager.parse_reference(test_reference)
            
            test_detail = {
                'reference': test_reference,
                'parsed_valid': parsed.valid,
                'resolved': False,
                'error': None
            }
            
            if parsed.valid:
                # Test resolution
                try:
                    # Check if file exists (synchronous version for testing)
                    expected_path = os.path.join(submodule.path, 'README.md')
                    test_detail['expected_path'] = expected_path
                    test_detail['resolved'] = os.path.exists(expected_path)
                    
                    if test_detail['resolved']:
                        print(f"✓ Successfully resolved: {test_reference}")
                        test_results['tests_passed'] += 1
                    else:
                        print(f"⚠ Reference parsed but file not found: {expected_path}")
                        test_detail['error'] = f"File not found: {expected_path}"
                        test_results['tests_failed'] += 1
                        test_results['success'] = False
                
                except Exception as e:
                    test_detail['error'] = str(e)
                    test_results['tests_failed'] += 1
                    test_results['success'] = False
                    print(f"✗ Resolution failed: {e}")
            else:
                test_detail['error'] = parsed.error
                test_results['tests_failed'] += 1
                test_results['success'] = False
                print(f"✗ Parsing failed: {parsed.error}")
            
            test_results['test_details'].append(test_detail)
        
        return test_results


def print_status_summary(status: Dict[str, Any]):
    """Print a formatted status summary"""
    print("\n" + "="*60)
    print("📊 CROSS-REPOSITORY STATUS SUMMARY")
    print("="*60)
    
    print(f"Configuration: {'✓ Loaded' if status['configuration_loaded'] else '✗ Not loaded'}")
    print(f"Config file: {status['configuration_path']}")
    
    if status.get('git_error'):
        print(f"Git error: {status['git_error']}")
        return
    
    print(f"Cross-repo ready: {'✓ Yes' if status['cross_repo_ready'] else '✗ No'}")
    print(f"Ready submodules: {status.get('ready_submodules', 0)}/{status.get('total_enabled_submodules', 0)}")
    
    print(f"\n📦 SUBMODULES:")
    for name, info in status.get('submodules', {}).items():
        status_icon = "✓" if info['exists'] and info['status'] == 'up-to-date' else "⚠" if info['exists'] else "✗"
        enabled_text = "" if info['enabled'] else " (disabled)"
        print(f"  {status_icon} {name}: {info['status']}{enabled_text}")
        if info['exists']:
            print(f"    Path: {info['path']}")
            if 'commit' in info:
                print(f"    Commit: {info['commit'][:8]}")
    
    if status.get('recommendations'):
        print(f"\n💡 RECOMMENDATIONS:")
        for i, rec in enumerate(status['recommendations'], 1):
            print(f"  {i}. {rec}")


def main():
    """Main entry point for git submodule setup"""
    parser = argparse.ArgumentParser(
        description='Git Submodule Setup for Cross-Repository Integration'
    )
    parser.add_argument(
        '--setup', 
        action='store_true', 
        help='Set up git submodules for cross-repository integration'
    )
    parser.add_argument(
        '--status', 
        action='store_true', 
        help='Show status of cross-repository setup'
    )
    parser.add_argument(
        '--update', 
        action='store_true', 
        help='Update existing git submodules'
    )
    parser.add_argument(
        '--test', 
        action='store_true', 
        help='Test cross-repository reference resolution'
    )
    parser.add_argument(
        '--config', 
        type=str, 
        help='Path to configuration file (default: .agent-os/cross-repo-config.yml)'
    )
    parser.add_argument(
        '--save-config', 
        action='store_true', 
        help='Save current configuration to file'
    )
    
    args = parser.parse_args()
    
    # Show help if no arguments provided
    if not any([args.setup, args.status, args.update, args.test, args.save_config]):
        parser.print_help()
        return
    
    # Initialize manager
    manager = GitSubmoduleSetupManager(config_path=args.config)
    
    try:
        if args.save_config:
            if manager.save_configuration():
                print("✓ Configuration saved successfully")
            else:
                print("✗ Failed to save configuration")
                sys.exit(1)
        
        if args.setup:
            print("🚀 Setting up cross-repository git submodules...")
            results = manager.setup_submodules()
            
            if results['success']:
                print(f"\n✅ Setup completed successfully!")
                print(f"   Added: {len(results['submodules_added'])} submodules")
                print(f"   Skipped: {len(results['skipped'])} submodules")
            else:
                print(f"\n⚠ Setup completed with errors:")
                print(f"   Added: {len(results['submodules_added'])} submodules")
                print(f"   Failed: {len(results['submodules_failed'])} submodules")
                print(f"   Skipped: {len(results['skipped'])} submodules")
                
                for failure in results['submodules_failed']:
                    print(f"   ✗ {failure['name']}: {failure['error']}")
        
        if args.update:
            print("🔄 Updating git submodules...")
            results = manager.update_submodules()
            
            if results['success']:
                print(f"\n✅ Update completed successfully!")
            else:
                print(f"\n⚠ Update completed with errors:")
            
            print(f"   Updated: {len(results['updated'])} submodules")
            print(f"   Failed: {len(results['failed'])} submodules")
            print(f"   Skipped: {len(results['skipped'])} submodules")
        
        if args.test:
            print("🧪 Testing cross-repository references...")
            results = manager.test_cross_repo_references()
            
            if results['success']:
                print(f"\n✅ All tests passed!")
            else:
                print(f"\n⚠ Some tests failed:")
            
            print(f"   Tests run: {results['tests_run']}")
            print(f"   Passed: {results['tests_passed']}")
            print(f"   Failed: {results['tests_failed']}")
        
        if args.status:
            status = manager.get_status()
            print_status_summary(status)
    
    except KeyboardInterrupt:
        print("\n\n⚠ Operation cancelled by user")
        sys.exit(1)
    except Exception as e:
        print(f"\n✗ Unexpected error: {e}")
        sys.exit(1)


if __name__ == '__main__':
    main()