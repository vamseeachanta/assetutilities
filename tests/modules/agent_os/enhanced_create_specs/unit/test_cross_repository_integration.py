"""
Unit Tests for Cross-Repository Integration System

Tests the cross-repository sub-agent system including:
- Cross-repository referencing and resolution
- Git submodule integration for AssetUtilities hub
- Version compatibility checking
- Caching system for cross-repository components
- Offline fallback mechanisms
- Reference validation and security
"""

import pytest
import asyncio
import os
import json
import tempfile
import shutil
from unittest.mock import Mock, patch, MagicMock, AsyncMock, mock_open
from pathlib import Path
from datetime import datetime, timedelta

# Import the modules we'll be testing
import sys
sys.path.insert(0, '/mnt/github/github/assetutilities/src/modules/agent_os/enhanced_create_specs')

from cross_repository_integration import (
    CrossRepositoryManager,
    GitSubmoduleIntegration,
    ReferenceResolver,
    VersionCompatibilityChecker,
    ComponentCacheManager,
    OfflineFallbackManager,
    ParsedReference,
    ResolutionResult
)


class TestCrossRepositoryManager:
    """Tests for CrossRepositoryManager class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.cross_repo_manager = CrossRepositoryManager()
    
    def test_initialization_with_defaults(self):
        """Test initialization with default configuration"""
        assert self.cross_repo_manager.hub_repository == 'assetutilities'
        assert self.cross_repo_manager.default_branch == 'main'
        assert self.cross_repo_manager.cache_enabled == True
        assert self.cross_repo_manager.security_enabled == True
    
    def test_initialization_with_custom_options(self):
        """Test initialization with custom configuration"""
        options = {
            'hub_repository': 'custom-hub',
            'default_branch': 'develop',
            'cache_enabled': False,
            'security_enabled': False,
            'allowed_repositories': ['repo1', 'repo2']
        }
        manager = CrossRepositoryManager(**options)
        
        assert manager.hub_repository == 'custom-hub'
        assert manager.default_branch == 'develop'
        assert manager.cache_enabled == False
        assert manager.security_enabled == False
        assert manager.allowed_repositories == ['repo1', 'repo2']
    
    def test_parse_reference_valid(self):
        """Test parsing valid cross-repository reference"""
        reference = '@github:assetutilities/src/modules/agent-os/enhanced-create-specs/workflow.md'
        
        parsed = self.cross_repo_manager.parse_reference(reference)
        
        assert parsed.valid == True
        assert parsed.type == 'github'
        assert parsed.repository == 'assetutilities'
        assert parsed.path == 'src/modules/agent-os/enhanced-create-specs/workflow.md'
        assert parsed.branch == 'main'
        assert parsed.error is None
    
    def test_parse_reference_with_branch(self):
        """Test parsing reference with specific branch"""
        reference = '@github:assetutilities@develop/src/modules/agent-os/workflow.md'
        
        parsed = self.cross_repo_manager.parse_reference(reference)
        
        assert parsed.valid == True
        assert parsed.repository == 'assetutilities'
        assert parsed.branch == 'develop'
        assert parsed.path == 'src/modules/agent-os/workflow.md'
    
    def test_parse_reference_invalid_format(self):
        """Test parsing invalid reference formats"""
        invalid_references = [
            'invalid-reference',
            '@github:',
            '@github:repo/',
            'github:repo/path',
            '@:repo/path',
            '@github:repo',
            '@github:repo/../../dangerous-path',
            '@github:repo/path?query=malicious',
            '@github:repo/path<script>alert("xss")</script>'
        ]
        
        for ref in invalid_references:
            parsed = self.cross_repo_manager.parse_reference(ref)
            assert parsed.valid == False
            assert parsed.error is not None
    
    def test_parse_reference_security_validation(self):
        """Test security validation for repositories"""
        # Test with disallowed repository
        reference = '@github:malicious-repo/src/file.md'
        
        parsed = self.cross_repo_manager.parse_reference(reference)
        
        assert parsed.valid == False
        assert 'not in allowed list' in parsed.error
    
    def test_validate_reference(self):
        """Test reference validation method"""
        valid_reference = '@github:assetutilities/src/workflow.md'
        invalid_reference = 'invalid-reference'
        
        assert self.cross_repo_manager.validate_reference(valid_reference) == True
        assert self.cross_repo_manager.validate_reference(invalid_reference) == False
    
    @pytest.mark.asyncio
    async def test_resolve_reference_success(self):
        """Test successful reference resolution"""
        reference = '@github:assetutilities/src/modules/agent-os/workflow.md'
        
        with patch('os.path.exists', return_value=True):
            result = await self.cross_repo_manager.resolve_reference(reference)
            
            assert result.success == True
            assert result.local_path is not None
            assert 'assetutilities' in result.local_path
            assert 'workflow.md' in result.local_path
    
    @pytest.mark.asyncio
    async def test_resolve_reference_file_not_found(self):
        """Test reference resolution when file doesn't exist"""
        reference = '@github:assetutilities/non-existent-file.md'
        
        with patch('os.path.exists', return_value=False):
            result = await self.cross_repo_manager.resolve_reference(reference)
            
            assert result.success == False
            assert 'File not found' in result.error
    
    @pytest.mark.asyncio
    async def test_resolve_reference_invalid(self):
        """Test resolution of invalid reference"""
        invalid_reference = 'invalid-reference'
        
        result = await self.cross_repo_manager.resolve_reference(invalid_reference)
        
        assert result.success == False
        assert result.error is not None
    
    def test_find_all_references(self):
        """Test finding all cross-repository references in project"""
        mock_files = [
            '/project/spec.md',
            '/project/config.yml'
        ]
        
        mock_content = """
        This spec references @github:assetutilities/templates/workflow.md
        and also uses @github:shared-templates/base.yml for configuration.
        """
        
        with patch.object(self.cross_repo_manager, '_get_all_files', return_value=mock_files), \
             patch('builtins.open', mock_open(read_data=mock_content)):
            
            references = self.cross_repo_manager.find_all_references('/project')
            
            assert len(references) == 2
            assert references[0]['reference'] == '@github:assetutilities/templates/workflow.md'
            assert references[1]['reference'] == '@github:shared-templates/base.yml'
            assert all('file' in ref for ref in references)
            assert all('line' in ref for ref in references)


class TestGitSubmoduleIntegration:
    """Tests for GitSubmoduleIntegration class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.git_integration = GitSubmoduleIntegration()
    
    def test_initialization(self):
        """Test initialization with default values"""
        assert self.git_integration.git_command == 'git'
        assert self.git_integration.working_directory == os.getcwd()
    
    def test_initialization_with_options(self):
        """Test initialization with custom options"""
        options = {
            'git_command': 'custom-git',
            'working_directory': '/custom/dir'
        }
        integration = GitSubmoduleIntegration(**options)
        
        assert integration.git_command == 'custom-git'
        assert integration.working_directory == '/custom/dir'
    
    def test_check_submodule_exists_true(self):
        """Test checking if submodule exists - exists"""
        mock_result = Mock()
        mock_result.stdout = 'assetutilities src/external/assetutilities (heads/main)'
        
        with patch('subprocess.run', return_value=mock_result):
            exists = self.git_integration.check_submodule_exists('assetutilities')
            assert exists == True
    
    def test_check_submodule_exists_false(self):
        """Test checking if submodule exists - doesn't exist"""
        mock_result = Mock()
        mock_result.stdout = 'other-submodule src/external/other (heads/main)'
        
        with patch('subprocess.run', return_value=mock_result):
            exists = self.git_integration.check_submodule_exists('assetutilities')
            assert exists == False
    
    def test_check_submodule_exists_command_failure(self):
        """Test checking submodule when git command fails"""
        with patch('subprocess.run', side_effect=Exception('Git error')):
            exists = self.git_integration.check_submodule_exists('assetutilities')
            assert exists == False
    
    def test_add_submodule_success(self):
        """Test successful submodule addition"""
        config = {
            'repository': 'https://github.com/user/assetutilities.git',
            'path': 'src/external/assetutilities',
            'branch': 'main'
        }
        
        with patch('subprocess.run') as mock_run:
            result = self.git_integration.add_submodule(config)
            
            assert result['success'] == True
            assert 'added successfully' in result['message']
            mock_run.assert_called_once()
    
    def test_add_submodule_failure(self):
        """Test submodule addition failure"""
        config = {
            'repository': 'invalid-repo',
            'path': 'invalid-path'
        }
        
        mock_error = Exception('Git command failed')
        mock_error.stderr = 'Repository not found'
        
        with patch('subprocess.run', side_effect=mock_error):
            result = self.git_integration.add_submodule(config)
            
            assert result['success'] == False
            assert 'Failed to add submodule' in result['message']
    
    def test_update_submodule_success(self):
        """Test successful submodule update"""
        with patch('subprocess.run') as mock_run:
            result = self.git_integration.update_submodule('assetutilities')
            
            assert result['success'] == True
            assert 'updated successfully' in result['message']
            mock_run.assert_called_once()
    
    def test_initialize_submodules_success(self):
        """Test successful submodule initialization"""
        with patch('subprocess.run') as mock_run:
            result = self.git_integration.initialize_submodules()
            
            assert result['success'] == True
            assert 'initialized successfully' in result['message']
            assert mock_run.call_count == 2  # init and update calls
    
    def test_get_submodule_status(self):
        """Test getting submodule status information"""
        mock_result = Mock()
        mock_result.stdout = """
 d85b1d5a8b9c assetutilities (heads/main)
-f7c2d3e9a1b4 shared-components (v1.2.3)
+a1b2c3d4e5f6 other-module (develop)
        """.strip()
        
        with patch('subprocess.run', return_value=mock_result):
            status = self.git_integration.get_submodule_status()
            
            assert len(status['submodules']) == 3
            
            # Check first submodule (up-to-date)
            submodule1 = status['submodules'][0]
            assert submodule1['name'] == 'assetutilities'
            assert submodule1['commit'] == 'd85b1d5a8b9c'
            assert submodule1['branch'] == 'heads/main'
            assert submodule1['status'] == 'up-to-date'
            
            # Check second submodule (not-initialized)
            submodule2 = status['submodules'][1]
            assert submodule2['name'] == 'shared-components'
            assert submodule2['status'] == 'not-initialized'
            
            # Check third submodule (different-commit)
            submodule3 = status['submodules'][2]
            assert submodule3['name'] == 'other-module'
            assert submodule3['status'] == 'different-commit'


class TestReferenceResolver:
    """Tests for ReferenceResolver class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.reference_resolver = ReferenceResolver()
    
    def test_initialization(self):
        """Test initialization with default values"""
        assert self.reference_resolver.cache == {}
        assert self.reference_resolver.max_cache_size == 100
        assert self.reference_resolver.cache_enabled == True
    
    @pytest.mark.asyncio
    async def test_resolve_reference_success(self):
        """Test successful reference resolution"""
        reference = '@github:assetutilities/src/workflow.md'
        mock_content = 'workflow content'
        
        with patch.object(CrossRepositoryManager, 'resolve_reference') as mock_resolve, \
             patch('builtins.open', mock_open(read_data=mock_content)):
            
            mock_resolve.return_value = ResolutionResult(
                success=True,
                reference=reference,
                local_path='/path/to/workflow.md'
            )
            
            result = await self.reference_resolver.resolve_reference(reference)
            
            assert result['success'] == True
            assert result['content'] == mock_content
            assert result['resolved_path'] == '/path/to/workflow.md'
    
    @pytest.mark.asyncio
    async def test_resolve_reference_with_yaml_parsing(self):
        """Test reference resolution with YAML content parsing"""
        reference = '@github:assetutilities/config/workflow.yml'
        yaml_content = """
workflow:
  name: enhanced-create-specs
  version: 1.0.0
  steps:
    - initialize
    - process
    - finalize
        """
        
        with patch.object(CrossRepositoryManager, 'resolve_reference') as mock_resolve, \
             patch('builtins.open', mock_open(read_data=yaml_content)):
            
            mock_resolve.return_value = ResolutionResult(
                success=True,
                reference=reference,
                local_path='/path/to/workflow.yml'
            )
            
            result = await self.reference_resolver.resolve_reference(
                reference, 
                extract_content=True, 
                format='yaml'
            )
            
            assert result['success'] == True
            assert result['parsed_content']['workflow']['name'] == 'enhanced-create-specs'
    
    @pytest.mark.asyncio
    async def test_resolve_reference_with_caching(self):
        """Test reference resolution with caching"""
        reference = '@github:assetutilities/src/cached-file.md'
        
        with patch.object(CrossRepositoryManager, 'resolve_reference') as mock_resolve, \
             patch('builtins.open', mock_open(read_data='cached content')):
            
            mock_resolve.return_value = ResolutionResult(
                success=True,
                reference=reference,
                local_path='/path/to/cached-file.md'
            )
            
            # First resolution
            await self.reference_resolver.resolve_reference(reference, use_cache=True)
            
            # Second resolution should use cache
            result = await self.reference_resolver.resolve_reference(reference, use_cache=True)
            
            assert result['success'] == True
            assert result.get('from_cache') == True
    
    @pytest.mark.asyncio
    async def test_resolve_nested_references(self):
        """Test resolving nested references within content"""
        main_reference = '@github:assetutilities/main.md'
        nested_reference = '@github:assetutilities/templates/nested.md'
        
        main_content = f'Main content with {nested_reference}'
        nested_content = 'Nested template content'
        
        def mock_open_side_effect(path, *args, **kwargs):
            if 'main.md' in path:
                return mock_open(read_data=main_content)()
            elif 'nested.md' in path:
                return mock_open(read_data=nested_content)()
            return mock_open(read_data='')()
        
        with patch.object(CrossRepositoryManager, 'resolve_reference') as mock_resolve, \
             patch('builtins.open', side_effect=mock_open_side_effect):
            
            # Mock resolve for both references
            mock_resolve.side_effect = [
                ResolutionResult(success=True, reference=main_reference, local_path='/path/main.md'),
                ResolutionResult(success=True, reference=nested_reference, local_path='/path/nested.md')
            ]
            
            result = await self.reference_resolver.resolve_reference(
                main_reference,
                resolve_nested=True
            )
            
            assert result['success'] == True
            assert 'Nested template content' in result['resolved_content']
    
    @pytest.mark.asyncio
    async def test_circular_reference_detection(self):
        """Test detection and handling of circular references"""
        reference1 = '@github:assetutilities/file1.md'
        reference2 = '@github:assetutilities/file2.md'
        
        # Create circular content
        content1 = f'Content with {reference2}'
        content2 = f'Content with {reference1}'
        
        def mock_open_side_effect(path, *args, **kwargs):
            if 'file1.md' in path:
                return mock_open(read_data=content1)()
            elif 'file2.md' in path:
                return mock_open(read_data=content2)()
            return mock_open(read_data='')()
        
        with patch.object(CrossRepositoryManager, 'resolve_reference') as mock_resolve, \
             patch('builtins.open', side_effect=mock_open_side_effect):
            
            # Mock resolve for both references
            mock_resolve.side_effect = [
                ResolutionResult(success=True, reference=reference1, local_path='/path/file1.md'),
                ResolutionResult(success=True, reference=reference2, local_path='/path/file2.md')
            ]
            
            result = await self.reference_resolver.resolve_reference(
                reference1,
                resolve_nested=True,
                max_depth=5
            )
            
            assert result['success'] == False
            assert 'Circular reference detected' in result['error']


class TestVersionCompatibilityChecker:
    """Tests for VersionCompatibilityChecker class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.version_checker = VersionCompatibilityChecker()
    
    def test_parse_version_valid(self):
        """Test parsing valid semantic versions"""
        test_cases = [
            ('1.2.3', {'major': 1, 'minor': 2, 'patch': 3, 'prerelease': None, 'build': None}),
            ('1.2.3-beta.1', {'major': 1, 'minor': 2, 'patch': 3, 'prerelease': 'beta.1', 'build': None}),
            ('1.2.3+build.123', {'major': 1, 'minor': 2, 'patch': 3, 'prerelease': None, 'build': 'build.123'}),
            ('1.2.3-alpha.1+build.456', {'major': 1, 'minor': 2, 'patch': 3, 'prerelease': 'alpha.1', 'build': 'build.456'})
        ]
        
        for version, expected in test_cases:
            parsed = self.version_checker.parse_version(version)
            
            assert parsed['valid'] == True
            assert parsed['major'] == expected['major']
            assert parsed['minor'] == expected['minor']
            assert parsed['patch'] == expected['patch']
            assert parsed['prerelease'] == expected['prerelease']
            assert parsed['build'] == expected['build']
    
    def test_parse_version_invalid(self):
        """Test parsing invalid version strings"""
        invalid_versions = [
            '1.2',
            '1.2.3.4',
            'v1.2.3',
            '1.2.3-',
            '1.2.3+',
            'invalid',
            ''
        ]
        
        for version in invalid_versions:
            parsed = self.version_checker.parse_version(version)
            assert parsed['valid'] == False
    
    def test_compare_versions(self):
        """Test version comparison logic"""
        test_cases = [
            ('1.0.0', '1.0.1', -1),  # First is older
            ('1.5.0', '1.0.0', 1),   # First is newer
            ('2.0.0', '2.0.0', 0),   # Equal
            ('2.0.0-alpha', '2.0.0', -1),  # Prerelease is older
            ('2.0.0', '2.0.0-beta', 1),    # Release is newer
            ('2.0.0-alpha', '2.0.0-beta', -1)  # Alpha < Beta
        ]
        
        for v1, v2, expected in test_cases:
            result = self.version_checker.compare_versions(v1, v2)
            assert result == expected
    
    def test_is_compatible_with_rules(self):
        """Test version compatibility checking with rules"""
        compatibility_rules = {
            'enhanced-create-specs': {
                'min_version': '1.0.0',
                'max_version': '2.0.0',
                'compatible': ['1.0.0', '1.5.0', '1.9.9'],
                'incompatible': ['1.2.3']
            }
        }
        
        # Test compatible versions
        assert self.version_checker.is_compatible('enhanced-create-specs', '1.5.0', compatibility_rules) == True
        assert self.version_checker.is_compatible('enhanced-create-specs', '1.9.9', compatibility_rules) == True
        
        # Test incompatible versions
        assert self.version_checker.is_compatible('enhanced-create-specs', '0.9.0', compatibility_rules) == False  # Below min
        assert self.version_checker.is_compatible('enhanced-create-specs', '2.1.0', compatibility_rules) == False  # Above max
        assert self.version_checker.is_compatible('enhanced-create-specs', '1.2.3', compatibility_rules) == False  # Explicitly incompatible
    
    def test_is_compatible_no_rules(self):
        """Test compatibility when no rules exist for component"""
        compatibility_rules = {}
        
        # Should return True when no rules exist
        assert self.version_checker.is_compatible('unknown-component', '1.0.0', compatibility_rules) == True


class TestComponentCacheManager:
    """Tests for ComponentCacheManager class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.cache_manager = ComponentCacheManager(
            cache_dir=self.temp_dir,
            max_size=100,  # 100 MB
            ttl=3600  # 1 hour
        )
    
    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_cache_component_success(self):
        """Test successful component caching"""
        component = {
            'reference': '@github:assetutilities/workflow.md',
            'content': 'workflow content',
            'version': '1.0.0',
            'metadata': {'size': 1024}
        }
        
        result = await self.cache_manager.cache_component(component)
        
        assert result['cached'] == True
        assert result['cache_key'] is not None
        assert result['error'] is None
        
        # Verify file was created
        cache_file = Path(self.temp_dir) / f"{result['cache_key']}.json"
        assert cache_file.exists()
    
    @pytest.mark.asyncio
    async def test_get_cached_component_success(self):
        """Test successful cached component retrieval"""
        # First cache a component
        component = {
            'reference': '@github:assetutilities/workflow.md',
            'content': 'workflow content',
            'version': '1.0.0'
        }
        
        cache_result = await self.cache_manager.cache_component(component)
        cache_key = cache_result['cache_key']
        
        # Then retrieve it
        result = await self.cache_manager.get_cached_component(cache_key)
        
        assert result['found'] == True
        assert result['content'] == 'workflow content'
        assert result['expired'] == False
    
    @pytest.mark.asyncio
    async def test_get_cached_component_not_found(self):
        """Test cached component retrieval when not found"""
        result = await self.cache_manager.get_cached_component('nonexistent-key')
        
        assert result['found'] == False
        assert result['content'] is None
    
    @pytest.mark.asyncio
    async def test_cache_expiration(self):
        """Test cache expiration logic"""
        # Create cache manager with very short TTL
        short_ttl_manager = ComponentCacheManager(
            cache_dir=self.temp_dir,
            ttl=1  # 1 second
        )
        
        component = {
            'reference': '@github:assetutilities/workflow.md',
            'content': 'workflow content',
            'version': '1.0.0'
        }
        
        cache_result = await short_ttl_manager.cache_component(component)
        cache_key = cache_result['cache_key']
        
        # Wait for expiration
        await asyncio.sleep(2)
        
        result = await short_ttl_manager.get_cached_component(cache_key)
        
        assert result['found'] == False
        assert result['expired'] == True
    
    def test_generate_cache_key_consistency(self):
        """Test cache key generation consistency"""
        reference1 = '@github:assetutilities/workflow.md'
        reference2 = '@github:assetutilities/workflow.md'
        
        key1 = self.cache_manager.generate_cache_key(reference1, '1.0.0')
        key2 = self.cache_manager.generate_cache_key(reference2, '1.0.0')
        
        assert key1 == key2
        assert len(key1) == 32  # MD5 hash length
        
        # Different versions should produce different keys
        key3 = self.cache_manager.generate_cache_key(reference1, '2.0.0')
        assert key1 != key3


class TestOfflineFallbackManager:
    """Tests for OfflineFallbackManager class"""
    
    def setup_method(self):
        """Setup test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.fallback_manager = OfflineFallbackManager(
            fallback_dir=self.temp_dir,
            enable_network_check=True
        )
    
    def teardown_method(self):
        """Clean up test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    def test_check_offline_mode_online(self):
        """Test offline mode detection when online"""
        with patch('subprocess.run') as mock_run:
            mock_run.return_value = None  # Successful ping
            
            is_offline = self.fallback_manager.check_offline_mode()
            assert is_offline == False
    
    def test_check_offline_mode_offline(self):
        """Test offline mode detection when offline"""
        with patch('subprocess.run', side_effect=Exception('Network unreachable')):
            is_offline = self.fallback_manager.check_offline_mode()
            assert is_offline == True
    
    @pytest.mark.asyncio
    async def test_create_and_get_fallback_entry(self):
        """Test creating and retrieving fallback cache entry"""
        reference = '@github:assetutilities/workflow.md'
        content = 'fallback content'
        metadata = {'version': '1.0.0', 'size': 1024}
        
        # Create fallback entry
        await self.fallback_manager.create_fallback_entry(reference, content, metadata)
        
        # Retrieve fallback content
        result = await self.fallback_manager.get_fallback_content(reference)
        
        assert result['success'] == True
        assert result['content'] == content
        assert result['source'] == 'fallback'
        assert result['metadata'] == metadata
    
    @pytest.mark.asyncio
    async def test_get_fallback_content_not_found(self):
        """Test fallback content retrieval when not cached"""
        reference = '@github:assetutilities/nonexistent.md'
        
        result = await self.fallback_manager.get_fallback_content(reference)
        
        assert result['success'] == False
        assert 'No fallback content available' in result['error']
    
    @pytest.mark.asyncio
    async def test_get_fallback_with_default_template(self):
        """Test fallback with default template"""
        reference = '@github:assetutilities/unknown-template.md'
        
        result = await self.fallback_manager.get_fallback_content(
            reference,
            use_default_template=True
        )
        
        assert result['success'] == True
        assert result['content'].startswith('# Default Template')
        assert result['source'] == 'default-template'
    
    def test_default_template_generation(self):
        """Test default template generation for different file types"""
        test_cases = [
            ('@github:assetutilities/file.md', '# Default Template'),
            ('@github:assetutilities/config.yml', 'default: true'),
            ('@github:assetutilities/config.yaml', 'default: true'),
            ('@github:assetutilities/data.json', '{"default": true'),
            ('@github:assetutilities/file.txt', 'Default content for unavailable')
        ]
        
        for reference, expected_content in test_cases:
            template = self.fallback_manager._get_default_template(reference)
            assert expected_content in template


class TestIntegrationScenarios:
    """Integration tests for complete cross-repository workflows"""
    
    def setup_method(self):
        """Setup integration test fixtures"""
        self.temp_dir = tempfile.mkdtemp()
        self.cross_repo_manager = CrossRepositoryManager()
        self.git_integration = GitSubmoduleIntegration()
        self.reference_resolver = ReferenceResolver()
        self.fallback_manager = OfflineFallbackManager(fallback_dir=self.temp_dir)
    
    def teardown_method(self):
        """Clean up integration test fixtures"""
        shutil.rmtree(self.temp_dir, ignore_errors=True)
    
    @pytest.mark.asyncio
    async def test_complete_cross_repository_workflow(self):
        """Test complete cross-repository workflow from submodule to resolution"""
        reference = '@github:assetutilities/src/workflow.md'
        
        # Mock successful operations
        with patch('subprocess.run') as mock_subprocess, \
             patch('os.path.exists', return_value=True), \
             patch('builtins.open', mock_open(read_data='resolved content')):
            
            mock_subprocess.return_value = Mock(stdout='submodule added')
            
            # Step 1: Add submodule
            submodule_result = self.git_integration.add_submodule({
                'repository': 'https://github.com/user/assetutilities.git',
                'path': 'src/external/assetutilities'
            })
            
            assert submodule_result['success'] == True
            
            # Step 2: Resolve reference
            resolve_result = await self.reference_resolver.resolve_reference(reference)
            
            assert resolve_result['success'] == True
            assert resolve_result['content'] == 'resolved content'
            
            # Step 3: Validate reference
            is_valid = self.cross_repo_manager.validate_reference(reference)
            assert is_valid == True
    
    @pytest.mark.asyncio
    async def test_offline_workflow_with_fallback(self):
        """Test complete offline workflow with fallback mechanisms"""
        reference = '@github:assetutilities/workflow.md'
        fallback_content = 'cached fallback content'
        
        # Create fallback entry first
        await self.fallback_manager.create_fallback_entry(
            reference, 
            fallback_content, 
            {'version': '1.0.0'}
        )
        
        # Simulate offline mode
        with patch('subprocess.run', side_effect=Exception('Network unreachable')):
            # Check offline mode
            is_offline = self.fallback_manager.check_offline_mode()
            assert is_offline == True
            
            # Get fallback content
            fallback_result = await self.fallback_manager.get_fallback_content(reference)
            
            assert fallback_result['success'] == True
            assert fallback_result['content'] == fallback_content
            assert fallback_result['source'] == 'fallback'
    
    @pytest.mark.asyncio
    async def test_version_compatibility_workflow(self):
        """Test version compatibility checking in cross-repository context"""
        version_checker = VersionCompatibilityChecker()
        
        compatibility_rules = {
            'enhanced-create-specs': {
                'min_version': '1.0.0',
                'max_version': '2.0.0'
            }
        }
        
        # Test compatible version
        is_compatible = version_checker.is_compatible(
            'enhanced-create-specs', 
            '1.5.0', 
            compatibility_rules
        )
        assert is_compatible == True
        
        # Test incompatible version
        is_incompatible = version_checker.is_compatible(
            'enhanced-create-specs', 
            '2.5.0', 
            compatibility_rules
        )
        assert is_incompatible == False


if __name__ == '__main__':
    pytest.main([__file__, '-v'])