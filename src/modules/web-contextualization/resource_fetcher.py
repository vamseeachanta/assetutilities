"""Resource Fetcher Module for Web Contextualization."""

import hashlib
import json
import logging
import shutil
from datetime import datetime
from pathlib import Path
from typing import Tuple, Dict, Any, Optional
from urllib.parse import urlparse, unquote
import subprocess

logger = logging.getLogger(__name__)

class ResourceFetcher:
    """Fetch and cache web resources with version control."""
    
    def __init__(self, cache_dir: Path, versions_dir: Optional[Path] = None):
        """Initialize fetcher with cache directory."""
        self.cache_dir = Path(cache_dir)
        self.cache_dir.mkdir(parents=True, exist_ok=True)
        
        self.versions_dir = versions_dir
        if self.versions_dir:
            self.versions_dir.mkdir(parents=True, exist_ok=True)
        
        # Check available tools
        self.has_wget = self._check_command("wget")
        self.has_curl = self._check_command("curl")
        self.has_requests = False
        
        try:
            import requests
            self.has_requests = True
            logger.info("requests library available for fetching")
        except ImportError:
            pass
    
    def fetch(self, url: str, force: bool = False,
             version_control: bool = True) -> Tuple[Optional[Path], Dict[str, Any]]:
        """Fetch a resource from URL and cache it."""
        metadata = {
            "url": url,
            "fetch_time": datetime.now().isoformat(),
            "method": None,
            "status": None,
            "error": None
        }
        
        # Generate cache filename
        cache_path = self._get_cache_path(url)
        
        # Check if already cached and not forcing refresh
        if cache_path.exists() and not force:
            logger.info(f"Using cached version: {cache_path}")
            metadata["status"] = "cached"
            metadata["cached_file"] = str(cache_path)
            return cache_path, metadata
        
        # Save previous version if version control enabled
        if version_control and cache_path.exists() and self.versions_dir:
            self._save_version(cache_path, url)
        
        # Try different fetching methods
        success = False
        
        if self.has_requests:
            success = self._fetch_with_requests(url, cache_path, metadata)
        
        if not success and self.has_wget:
            success = self._fetch_with_wget(url, cache_path, metadata)
        
        if not success and self.has_curl:
            success = self._fetch_with_curl(url, cache_path, metadata)
        
        if success:
            metadata["status"] = "success"
            metadata["cached_file"] = str(cache_path)
            
            # Save metadata
            meta_path = cache_path.with_suffix(cache_path.suffix + '.meta.json')
            with open(meta_path, 'w') as f:
                json.dump(metadata, f, indent=2)
            
            return cache_path, metadata
        else:
            metadata["status"] = "failed"
            return None, metadata
    
    def _fetch_with_requests(self, url: str, output_path: Path,
                            metadata: Dict) -> bool:
        """Fetch using Python requests library."""
        try:
            import requests
            
            logger.info(f"Fetching with requests: {url}")
            
            # Set headers to avoid bot detection
            headers = {
                'User-Agent': 'Mozilla/5.0 (compatible; AgentOS/1.0; +https://github.com/agent-os)'
            }
            
            response = requests.get(
                url,
                headers=headers,
                timeout=30,
                stream=True,
                allow_redirects=True
            )
            response.raise_for_status()
            
            # Get content type
            content_type = response.headers.get('content-type', '')
            metadata['content_type'] = content_type
            metadata['method'] = 'requests'
            
            # Stream download for large files
            with open(output_path, 'wb') as f:
                for chunk in response.iter_content(chunk_size=8192):
                    if chunk:
                        f.write(chunk)
            
            metadata['file_size'] = output_path.stat().st_size
            logger.info(f"Successfully fetched: {url}")
            return True
            
        except Exception as e:
            logger.error(f"Requests fetch failed: {e}")
            metadata['error'] = str(e)
            return False
    
    def _fetch_with_wget(self, url: str, output_path: Path,
                        metadata: Dict) -> bool:
        """Fetch using wget command."""
        try:
            logger.info(f"Fetching with wget: {url}")
            
            cmd = [
                'wget',
                '-q',  # Quiet
                '-O', str(output_path),  # Output file
                '--timeout=30',  # Timeout
                '--tries=3',  # Retry attempts
                '--user-agent=Mozilla/5.0 (compatible; AgentOS/1.0)',
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0:
                metadata['method'] = 'wget'
                metadata['file_size'] = output_path.stat().st_size
                logger.info(f"Successfully fetched with wget: {url}")
                return True
            else:
                logger.error(f"wget failed: {result.stderr}")
                metadata['error'] = result.stderr
                return False
                
        except Exception as e:
            logger.error(f"wget fetch failed: {e}")
            metadata['error'] = str(e)
            return False
    
    def _fetch_with_curl(self, url: str, output_path: Path,
                        metadata: Dict) -> bool:
        """Fetch using curl command."""
        try:
            logger.info(f"Fetching with curl: {url}")
            
            cmd = [
                'curl',
                '-s',  # Silent
                '-L',  # Follow redirects
                '-o', str(output_path),  # Output file
                '--max-time', '60',  # Timeout
                '--retry', '3',  # Retry attempts
                '--user-agent', 'Mozilla/5.0 (compatible; AgentOS/1.0)',
                url
            ]
            
            result = subprocess.run(cmd, capture_output=True, text=True, timeout=60)
            
            if result.returncode == 0 and output_path.exists():
                metadata['method'] = 'curl'
                metadata['file_size'] = output_path.stat().st_size
                logger.info(f"Successfully fetched with curl: {url}")
                return True
            else:
                logger.error(f"curl failed: {result.stderr}")
                metadata['error'] = result.stderr
                return False
                
        except Exception as e:
            logger.error(f"curl fetch failed: {e}")
            metadata['error'] = str(e)
            return False
    
    def _get_cache_path(self, url: str) -> Path:
        """Generate cache file path from URL."""
        parsed = urlparse(url)
        
        # Try to get filename from URL
        path_parts = unquote(parsed.path).strip('/').split('/')
        
        if path_parts and path_parts[-1]:
            filename = path_parts[-1]
            # Sanitize filename
            filename = "".join(c for c in filename if c.isalnum() or c in '.-_')
        else:
            # Generate filename from URL hash
            url_hash = hashlib.md5(url.encode()).hexdigest()[:8]
            filename = f"{parsed.netloc}_{url_hash}"
        
        # Add extension if missing
        if '.' not in filename:
            # Try to determine extension from URL
            if '.pdf' in url.lower():
                filename += '.pdf'
            elif '.html' in url.lower() or parsed.scheme in ['http', 'https']:
                filename += '.html'
            else:
                filename += '.txt'
        
        return self.cache_dir / filename
    
    def _save_version(self, file_path: Path, url: str):
        """Save a version of the file before overwriting."""
        if not self.versions_dir or not file_path.exists():
            return
        
        timestamp = datetime.now().strftime('%Y%m%d_%H%M%S')
        version_name = f"{file_path.stem}_{timestamp}{file_path.suffix}"
        version_path = self.versions_dir / version_name
        
        shutil.copy2(file_path, version_path)
        
        # Save version metadata
        version_meta = {
            "original_url": url,
            "version_time": datetime.now().isoformat(),
            "original_file": str(file_path.name),
            "file_size": file_path.stat().st_size
        }
        
        meta_path = version_path.with_suffix(version_path.suffix + '.meta.json')
        with open(meta_path, 'w') as f:
            json.dump(version_meta, f, indent=2)
        
        logger.info(f"Saved version: {version_path}")
    
    def _check_command(self, command: str) -> bool:
        """Check if a command is available."""
        try:
            result = subprocess.run(
                ['which', command],
                capture_output=True,
                text=True
            )
            return result.returncode == 0
        except:
            return False
    
    def clean_cache(self, max_age_days: int = 30, max_size_mb: int = 500):
        """Clean old cache files."""
        from datetime import timedelta
        
        now = datetime.now()
        total_size = 0
        files_by_age = []
        
        # Collect all cache files with age and size
        for file_path in self.cache_dir.glob('*'):
            if file_path.suffix == '.meta.json':
                continue
            
            stat = file_path.stat()
            age = now - datetime.fromtimestamp(stat.st_mtime)
            size_mb = stat.st_size / (1024 * 1024)
            
            files_by_age.append({
                'path': file_path,
                'age_days': age.days,
                'size_mb': size_mb
            })
            total_size += size_mb
        
        # Sort by age (oldest first)
        files_by_age.sort(key=lambda x: x['age_days'], reverse=True)
        
        # Remove old files
        for file_info in files_by_age:
            if file_info['age_days'] > max_age_days:
                file_info['path'].unlink()
                logger.info(f"Removed old cache file: {file_info['path'].name}")
                total_size -= file_info['size_mb']
        
        # Remove files if cache is too large
        while total_size > max_size_mb and files_by_age:
            file_info = files_by_age.pop(0)
            if file_info['path'].exists():
                file_info['path'].unlink()
                logger.info(f"Removed cache file for size limit: {file_info['path'].name}")
                total_size -= file_info['size_mb']
        
        logger.info(f"Cache cleaned. Current size: {total_size:.2f} MB")