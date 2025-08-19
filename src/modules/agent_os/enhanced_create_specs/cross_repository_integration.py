"""
Cross-Repository Integration System for Enhanced Create-Specs

Provides comprehensive cross-repository capabilities including:
- Cross-repository reference parsing and resolution
- Git submodule integration for AssetUtilities hub
- Version compatibility checking and validation
- Component caching for improved performance
- Offline fallback mechanisms
- Security validation for cross-repository operations
"""

import os
import re
import json
import yaml
import hashlib
import subprocess
import pathlib
from typing import Dict, List, Optional, Any, Set
from dataclasses import dataclass
from datetime import datetime, timedelta
import logging

logger = logging.getLogger(__name__)


@dataclass
class ParsedReference:
    """Parsed cross-repository reference"""
    original: str
    valid: bool
    type: Optional[str] = None
    repository: Optional[str] = None
    branch: str = "main"
    path: Optional[str] = None
    error: Optional[str] = None


@dataclass
class ResolutionResult:
    """Reference resolution result"""
    success: bool
    reference: str
    local_path: Optional[str] = None
    parsed_reference: Optional[ParsedReference] = None
    error: Optional[str] = None


class CrossRepositoryManager:
    """Main cross-repository manager"""
    
    def __init__(self, **options):
        self.hub_repository = options.get('hub_repository', 'assetutilities')
        self.default_branch = options.get('default_branch', 'main')
        self.base_url = options.get('base_url', 'https://github.com')
        self.cache_enabled = options.get('cache_enabled', True)
        self.security_enabled = options.get('security_enabled', True)
        
        # Allowed repositories for security
        self.allowed_repositories = options.get('allowed_repositories', [
            'assetutilities',
            'agent-os-core', 
            'shared-templates'
        ])
    
    def parse_reference(self, reference: str) -> ParsedReference:
        """Parse cross-repository reference
        
        Args:
            reference: Reference in format @github:repo/path or @github:repo@branch/path
            
        Returns:
            Parsed reference object
        """
        result = ParsedReference(
            original=reference,
            valid=False,
            branch=self.default_branch
        )
        
        try:
            # Validate basic format
            if not reference or not isinstance(reference, str) or not reference.startswith('@'):
                result.error = 'Invalid reference format'
                return result
            
            # Parse reference pattern: @type:repository[@branch]/path
            pattern = r'^@([^:]+):([^/@]+)(?:@([^/]+))?/(.+)$'
            match = re.match(pattern, reference)
            
            if not match:
                result.error = 'Reference does not match expected pattern'
                return result
            
            ref_type, repository, branch, file_path = match.groups()
            
            # Validate components
            if not ref_type or not repository or not file_path:
                result.error = 'Missing required reference components'
                return result
            
            # Security validation
            if self.security_enabled and repository not in self.allowed_repositories:
                result.error = f"Repository '{repository}' not in allowed list"
                return result
            
            # Path traversal protection
            if '..' in file_path or '~' in file_path or re.search(r'[<>:"|?*]', file_path):
                result.error = 'Path contains invalid characters'
                return result
            
            result.type = ref_type
            result.repository = repository
            result.branch = branch or self.default_branch
            result.path = file_path
            result.valid = True
            
        except Exception as e:
            result.error = str(e)
            
        return result
    
    def validate_reference(self, reference: str) -> bool:
        """Validate reference format and security"""
        parsed = self.parse_reference(reference)
        return parsed.valid
    
    async def resolve_reference(self, reference: str, **options) -> ResolutionResult:
        """Resolve cross-repository reference to local path"""
        result = ResolutionResult(
            success=False,
            reference=reference
        )
        
        try:
            parsed = self.parse_reference(reference)
            
            if not parsed.valid:
                result.error = parsed.error
                return result
            
            # Determine local path based on submodule or cache
            local_path = self._get_local_path(parsed, options)
            
            # Check if file exists
            if not os.path.exists(local_path):
                result.error = f"File not found: {local_path}"
                return result
            
            result.success = True
            result.local_path = local_path
            result.parsed_reference = parsed
            
        except Exception as e:
            result.error = str(e)
            
        return result
    
    def _get_local_path(self, parsed: ParsedReference, options: Dict) -> str:
        """Get local path for resolved reference"""
        base_dir = options.get('base_directory', os.getcwd())
        
        if options.get('use_submodule'):
            return os.path.join(base_dir, 'src', 'external', parsed.repository, parsed.path)
        else:
            return os.path.join(base_dir, '.cross-repo-cache', parsed.repository, parsed.branch, parsed.path)
    
    def find_all_references(self, project_path: str) -> List[Dict]:
        """List all cross-repository references in a project"""
        references = []
        reference_pattern = r'@[^:]+:[^/@]+(?:@[^/]+)?/[^\s)]+'
        
        try:
            files = self._get_all_files(project_path, ['.md', '.yml', '.yaml', '.json', '.py'])
            
            for file_path in files:
                try:
                    with open(file_path, 'r', encoding='utf-8') as f:
                        content = f.read()
                    
                    matches = re.findall(reference_pattern, content)
                    
                    for match in matches:
                        if self.validate_reference(match):
                            references.append({
                                'reference': match,
                                'file': file_path,
                                'line': self._find_line_number(content, match)
                            })
                            
                except Exception as e:
                    logger.warning(f"Error reading file {file_path}: {e}")
                    
        except Exception as e:
            logger.error(f"Error finding references: {e}")
            
        return references
    
    def _get_all_files(self, directory: str, extensions: List[str]) -> List[str]:
        """Get all files with specific extensions"""
        files = []
        
        try:
            for root, dirs, filenames in os.walk(directory):
                # Skip hidden directories and node_modules
                dirs[:] = [d for d in dirs if not d.startswith('.') and d != 'node_modules']
                
                for filename in filenames:
                    if any(filename.endswith(ext) for ext in extensions):
                        files.append(os.path.join(root, filename))
                        
        except Exception as e:
            logger.warning(f"Error walking directory {directory}: {e}")
            
        return files
    
    def _find_line_number(self, content: str, text: str) -> int:
        """Find line number of text in content"""
        lines = content.split('\n')
        for i, line in enumerate(lines):
            if text in line:
                return i + 1
        return 0


class GitSubmoduleIntegration:
    """Git submodule integration manager"""
    
    def __init__(self, **options):
        self.git_command = options.get('git_command', 'git')
        self.working_directory = options.get('working_directory', os.getcwd())
    
    def check_submodule_exists(self, submodule_name: str) -> bool:
        """Check if a submodule exists"""
        try:
            result = subprocess.run(
                [self.git_command, 'submodule', 'status'],
                cwd=self.working_directory,
                capture_output=True,
                text=True,
                check=True
            )
            return submodule_name in result.stdout
        except subprocess.CalledProcessError:
            return False
    
    def add_submodule(self, config: Dict) -> Dict:
        """Add git submodule"""
        repository = config['repository']
        submodule_path = config['path']
        branch = config.get('branch', 'main')
        
        result = {
            'success': False,
            'message': None,
            'error': None
        }
        
        try:
            subprocess.run(
                [self.git_command, 'submodule', 'add', '-b', branch, repository, submodule_path],
                cwd=self.working_directory,
                capture_output=True,
                text=True,
                check=True
            )
            
            result['success'] = True
            result['message'] = f"Submodule added successfully: {submodule_path}"
            
        except subprocess.CalledProcessError as e:
            result['error'] = e.stderr or str(e)
            result['message'] = f"Failed to add submodule: {result['error']}"
            
        return result
    
    def update_submodule(self, submodule_name: str) -> Dict:
        """Update existing submodule"""
        result = {
            'success': False,
            'message': None,
            'error': None
        }
        
        try:
            subprocess.run(
                [self.git_command, 'submodule', 'update', '--remote', submodule_name],
                cwd=self.working_directory,
                capture_output=True,
                text=True,
                check=True
            )
            
            result['success'] = True
            result['message'] = f"Submodule updated successfully: {submodule_name}"
            
        except subprocess.CalledProcessError as e:
            result['error'] = e.stderr or str(e)
            result['message'] = f"Failed to update submodule: {result['error']}"
            
        return result
    
    def initialize_submodules(self) -> Dict:
        """Initialize all submodules"""
        result = {
            'success': False,
            'message': None,
            'error': None
        }
        
        try:
            # Initialize submodules
            subprocess.run(
                [self.git_command, 'submodule', 'init'],
                cwd=self.working_directory,
                check=True
            )
            
            # Update submodules
            subprocess.run(
                [self.git_command, 'submodule', 'update'],
                cwd=self.working_directory,
                check=True
            )
            
            result['success'] = True
            result['message'] = 'All submodules initialized successfully'
            
        except subprocess.CalledProcessError as e:
            result['error'] = str(e)
            result['message'] = f"Failed to initialize submodules: {result['error']}"
            
        return result
    
    def get_submodule_status(self) -> Dict:
        """Get status of all submodules"""
        result = {
            'submodules': [],
            'error': None
        }
        
        try:
            output = subprocess.run(
                [self.git_command, 'submodule', 'status'],
                cwd=self.working_directory,
                capture_output=True,
                text=True,
                check=True
            ).stdout
            
            for line in output.strip().split('\n'):
                if not line.strip():
                    continue
                    
                match = re.match(r'^([-+ ]?)([a-f0-9]+) (.+?)(?: \((.+)\))?$', line)
                if match:
                    status_char, commit, name, branch = match.groups()
                    
                    status = 'up-to-date'
                    if status_char == '-':
                        status = 'not-initialized'
                    elif status_char == '+':
                        status = 'different-commit'
                    
                    result['submodules'].append({
                        'name': name.strip(),
                        'commit': commit,
                        'branch': branch or 'unknown',
                        'status': status
                    })
                    
        except subprocess.CalledProcessError as e:
            result['error'] = str(e)
            
        return result


class ReferenceResolver:
    """Reference resolver with content extraction"""
    
    def __init__(self, **options):
        self.cache = {}
        self.max_cache_size = options.get('max_cache_size', 100)
        self.cache_enabled = options.get('cache_enabled', True)
    
    async def resolve_reference(self, reference: str, **options) -> Dict:
        """Resolve reference and return content"""
        result = {
            'success': False,
            'reference': reference,
            'content': None,
            'parsed_content': None,
            'resolved_path': None,
            'error': None
        }
        
        try:
            # Check cache first
            if self.cache_enabled and options.get('use_cache'):
                cached = self.cache.get(reference)
                if cached and datetime.now() - cached['timestamp'] < timedelta(seconds=options.get('cache_ttl', 300)):
                    return {**cached['result'], 'from_cache': True}
            
            # Resolve path
            cross_repo_manager = CrossRepositoryManager()
            resolved = await cross_repo_manager.resolve_reference(reference, **options)
            
            if not resolved.success:
                result['error'] = resolved.error
                return result
            
            # Read content
            with open(resolved.local_path, 'r', encoding='utf-8') as f:
                content = f.read()
            
            result['success'] = True
            result['content'] = content
            result['resolved_path'] = resolved.local_path
            
            # Parse content if requested
            if options.get('extract_content'):
                result['parsed_content'] = self._parse_content(content, options.get('format'))
            
            # Resolve nested references if requested
            if options.get('resolve_nested'):
                result['resolved_content'] = await self._resolve_nested_references(
                    content, options, {reference}
                )
            
            # Cache result
            if self.cache_enabled and options.get('use_cache'):
                self._cache_result(reference, result)
                
        except Exception as e:
            result['error'] = str(e)
            
        return result
    
    def _parse_content(self, content: str, format_type: Optional[str]) -> Any:
        """Parse content based on format"""
        try:
            if format_type and format_type.lower() in ['yaml', 'yml']:
                return yaml.safe_load(content)
            elif format_type and format_type.lower() == 'json':
                return json.loads(content)
            else:
                return content
        except Exception as e:
            raise ValueError(f"Failed to parse content as {format_type}: {e}")
    
    async def _resolve_nested_references(self, content: str, options: Dict, visited: Set[str]) -> str:
        """Resolve nested references within content"""
        reference_pattern = r'@[^:]+:[^/@]+(?:@[^/]+)?/[^\s)]+'
        references = re.findall(reference_pattern, content)
        
        resolved_content = content
        max_depth = options.get('max_depth', 10)
        
        if len(visited) >= max_depth:
            raise ValueError('Maximum nesting depth reached')
        
        for ref in references:
            if ref in visited:
                raise ValueError(f'Circular reference detected: {ref}')
            
            try:
                nested_visited = visited.copy()
                nested_visited.add(ref)
                
                resolved = await self.resolve_reference(ref, **{**options, 'resolve_nested': False})
                
                if resolved['success']:
                    resolved_content = resolved_content.replace(ref, resolved['content'])
                    
            except Exception as e:
                logger.warning(f"Failed to resolve nested reference {ref}: {e}")
                
        return resolved_content
    
    def _cache_result(self, reference: str, result: Dict):
        """Cache resolution result"""
        # Implement LRU cache eviction
        if len(self.cache) >= self.max_cache_size:
            oldest_key = next(iter(self.cache))
            del self.cache[oldest_key]
        
        self.cache[reference] = {
            'result': result.copy(),
            'timestamp': datetime.now()
        }
    
    def clear_cache(self):
        """Clear resolution cache"""
        self.cache.clear()


class VersionCompatibilityChecker:
    """Version compatibility checker"""
    
    def __init__(self):
        self.version_pattern = re.compile(r'^(\d+)\.(\d+)\.(\d+)(?:-([^+]+))?(?:\+(.+))?$')
    
    def is_compatible(self, component: str, version: str, compatibility_rules: Dict) -> bool:
        """Check if versions are compatible"""
        rules = compatibility_rules.get(component)
        if not rules:
            return True  # No rules means compatible
        
        version_info = self.parse_version(version)
        if not version_info['valid']:
            return False
        
        # Check minimum version
        if rules.get('min_version') and self.compare_versions(version, rules['min_version']) < 0:
            return False
        
        # Check maximum version
        if rules.get('max_version') and self.compare_versions(version, rules['max_version']) > 0:
            return False
        
        # Check explicit compatibility list
        if rules.get('compatible') and version not in rules['compatible']:
            return False
        
        # Check incompatible list
        if rules.get('incompatible') and version in rules['incompatible']:
            return False
        
        return True
    
    def parse_version(self, version: str) -> Dict:
        """Parse semantic version"""
        match = self.version_pattern.match(version)
        
        if not match:
            return {'valid': False}
        
        major, minor, patch, prerelease, build = match.groups()
        
        return {
            'valid': True,
            'major': int(major),
            'minor': int(minor),
            'patch': int(patch),
            'prerelease': prerelease,
            'build': build,
            'original': version
        }
    
    def compare_versions(self, version1: str, version2: str) -> int:
        """Compare two versions"""
        v1 = self.parse_version(version1)
        v2 = self.parse_version(version2)
        
        if not v1['valid'] or not v2['valid']:
            raise ValueError('Invalid version format')
        
        # Compare major.minor.patch
        for component in ['major', 'minor', 'patch']:
            if v1[component] < v2[component]:
                return -1
            elif v1[component] > v2[component]:
                return 1
        
        # Compare prerelease
        if v1['prerelease'] and not v2['prerelease']:
            return -1
        elif not v1['prerelease'] and v2['prerelease']:
            return 1
        elif v1['prerelease'] and v2['prerelease']:
            if v1['prerelease'] < v2['prerelease']:
                return -1
            elif v1['prerelease'] > v2['prerelease']:
                return 1
        
        return 0


class ComponentCacheManager:
    """Component cache manager for cross-repository components"""
    
    def __init__(self, **options):
        self.cache_dir = pathlib.Path(options.get('cache_dir', '.cross-repo-cache'))
        self.max_size = options.get('max_size', 100)  # MB
        self.ttl = options.get('ttl', 3600)  # seconds
    
    async def cache_component(self, component: Dict) -> Dict:
        """Cache component content"""
        result = {
            'cached': False,
            'cache_key': None,
            'error': None
        }
        
        try:
            cache_key = self.generate_cache_key(component['reference'], component.get('version', 'latest'))
            cache_path = self.cache_dir / f"{cache_key}.json"
            
            # Ensure cache directory exists
            self.cache_dir.mkdir(parents=True, exist_ok=True)
            
            cache_data = {
                'reference': component['reference'],
                'content': component['content'],
                'version': component.get('version'),
                'timestamp': datetime.now().isoformat(),
                'metadata': component.get('metadata', {})
            }
            
            with open(cache_path, 'w') as f:
                json.dump(cache_data, f, indent=2)
            
            result['cached'] = True
            result['cache_key'] = cache_key
            
            # Clean cache if needed
            await self.clear_cache_if_needed()
            
        except Exception as e:
            result['error'] = str(e)
            
        return result
    
    async def get_cached_component(self, cache_key: str) -> Dict:
        """Get cached component"""
        result = {
            'found': False,
            'content': None,
            'expired': False,
            'error': None
        }
        
        try:
            cache_path = self.cache_dir / f"{cache_key}.json"
            
            if not cache_path.exists():
                return result
            
            # Check expiration
            if datetime.now().timestamp() - cache_path.stat().st_mtime > self.ttl:
                result['expired'] = True
                return result
            
            with open(cache_path, 'r') as f:
                cache_data = json.load(f)
            
            result['found'] = True
            result['content'] = cache_data['content']
            result['metadata'] = cache_data.get('metadata', {})
            result['timestamp'] = cache_data['timestamp']
            
        except Exception as e:
            result['error'] = str(e)
            
        return result
    
    def generate_cache_key(self, reference: str, version: str = 'latest') -> str:
        """Generate cache key from reference and version"""
        data = f"{reference}:{version}"
        return hashlib.md5(data.encode()).hexdigest()
    
    async def clear_cache_if_needed(self):
        """Clear cache if size limit exceeded"""
        try:
            if not self.cache_dir.exists():
                return
            
            total_size = 0
            file_stats = []
            
            for file_path in self.cache_dir.glob('*.json'):
                stat = file_path.stat()
                total_size += stat.st_size
                file_stats.append({
                    'path': file_path,
                    'size': stat.st_size,
                    'mtime': stat.st_mtime
                })
            
            # Convert maxSize from MB to bytes
            max_size_bytes = self.max_size * 1024 * 1024
            
            if total_size > max_size_bytes:
                # Sort by modification time (oldest first)
                file_stats.sort(key=lambda x: x['mtime'])
                
                # Remove oldest files until under size limit
                current_size = total_size
                for file_stat in file_stats:
                    if current_size <= max_size_bytes:
                        break
                    
                    file_stat['path'].unlink()
                    current_size -= file_stat['size']
                    
        except Exception as e:
            logger.warning(f"Cache cleanup failed: {e}")


class OfflineFallbackManager:
    """Offline fallback manager"""
    
    def __init__(self, **options):
        self.fallback_dir = pathlib.Path(options.get('fallback_dir', '.fallback-cache'))
        self.enable_network_check = options.get('enable_network_check', True)
        self.default_templates = options.get('default_templates', {})
    
    def check_offline_mode(self) -> bool:
        """Check if system is in offline mode"""
        if not self.enable_network_check:
            return False
        
        try:
            # Try to ping a reliable service
            subprocess.run(['ping', '-c', '1', '8.8.8.8'], 
                         timeout=5, check=True, capture_output=True)
            return False
        except (subprocess.CalledProcessError, subprocess.TimeoutExpired):
            return True
    
    async def get_fallback_content(self, reference: str, **options) -> Dict:
        """Get fallback content for reference"""
        result = {
            'success': False,
            'content': None,
            'source': None,
            'error': None
        }
        
        try:
            fallback_key = self._generate_fallback_key(reference)
            fallback_path = self.fallback_dir / f"{fallback_key}.json"
            
            # Try to read cached fallback
            if fallback_path.exists():
                with open(fallback_path, 'r') as f:
                    fallback_data = json.load(f)
                
                result['success'] = True
                result['content'] = fallback_data['content']
                result['source'] = 'fallback'
                result['metadata'] = fallback_data.get('metadata', {})
                
                return result
            
            # Use default template if available
            if options.get('use_default_template'):
                template = self._get_default_template(reference)
                if template:
                    result['success'] = True
                    result['content'] = template
                    result['source'] = 'default-template'
                    return result
            
            result['error'] = 'No fallback content available'
            
        except Exception as e:
            result['error'] = str(e)
            
        return result
    
    async def create_fallback_entry(self, reference: str, content: str, metadata: Dict = None):
        """Create fallback cache entry"""
        try:
            self.fallback_dir.mkdir(parents=True, exist_ok=True)
            
            fallback_key = self._generate_fallback_key(reference)
            fallback_path = self.fallback_dir / f"{fallback_key}.json"
            
            fallback_data = {
                'reference': reference,
                'content': content,
                'metadata': metadata or {},
                'timestamp': datetime.now().isoformat()
            }
            
            with open(fallback_path, 'w') as f:
                json.dump(fallback_data, f, indent=2)
                
        except Exception as e:
            logger.warning(f"Failed to create fallback entry: {e}")
    
    def _generate_fallback_key(self, reference: str) -> str:
        """Generate fallback key from reference"""
        return hashlib.md5(reference.encode()).hexdigest()
    
    def _get_default_template(self, reference: str) -> Optional[str]:
        """Get default template for reference"""
        try:
            cross_repo_manager = CrossRepositoryManager()
            parsed = cross_repo_manager.parse_reference(reference)
            
            if not parsed.valid:
                return None
            
            filename = os.path.basename(parsed.path)
            extension = os.path.splitext(filename)[1]
            
            # Return appropriate default template
            templates = {
                '.md': '# Default Template\n\nThis is a default template used when the original reference is unavailable.\n',
                '.yml': 'default: true\ntemplate: basic\n',
                '.yaml': 'default: true\ntemplate: basic\n',
                '.json': '{"default": true, "template": "basic"}'
            }
            
            return templates.get(extension, 'Default content for unavailable reference.')
            
        except Exception:
            return None