#!/usr/bin/env python3
"""
Cross-Reference Management System for Enhanced Create-Specs Workflow.

This module provides comprehensive cross-reference management with:
- Internal repository reference validation
- Cross-repository reference resolution
- External link validation
- Reference indexing and search
- Broken link detection and reporting
- Automatic reference generation

Author: Enhanced Create-Specs Workflow
Created: 2025-08-05
Module: agent-os/enhanced-create-specs
"""

import os
import re
import json
import yaml
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any, Tuple, Set
from dataclasses import dataclass, field
from enum import Enum
from urllib.parse import urlparse
import asyncio
import aiohttp
from concurrent.futures import ThreadPoolExecutor, as_completed
import logging


class ReferenceType(Enum):
    """Enumeration of reference types."""
    INTERNAL = "internal"
    CROSS_REPO = "cross_repo"
    EXTERNAL = "external"
    RELATIVE = "relative"
    ANCHOR = "anchor"


class ReferenceStatus(Enum):
    """Enumeration of reference validation statuses."""
    VALID = "valid"
    INVALID = "invalid"
    BROKEN = "broken"
    PENDING = "pending"
    UNKNOWN = "unknown"


@dataclass
class Reference:
    """Data class for reference information."""
    original: str
    type: ReferenceType
    resolved_path: str = ""
    target_exists: bool = False
    status: ReferenceStatus = ReferenceStatus.PENDING
    error_message: str = ""
    context: Dict[str, Any] = field(default_factory=dict)
    
    # For cross-repository references
    repository: str = ""
    repository_path: str = ""
    
    # For external references
    response_code: int = 0
    last_checked: str = ""
    
    # For internal references
    absolute_path: str = ""
    relative_from_source: str = ""


@dataclass
class CrossReferenceIndex:
    """Index of all cross-references in the system."""
    references: Dict[str, Reference] = field(default_factory=dict)
    by_type: Dict[ReferenceType, List[str]] = field(default_factory=dict)
    by_status: Dict[ReferenceStatus, List[str]] = field(default_factory=dict)
    by_source_file: Dict[str, List[str]] = field(default_factory=dict)
    by_target: Dict[str, List[str]] = field(default_factory=dict)
    
    def add_reference(self, ref_id: str, reference: Reference, source_file: str = ""):
        """Add a reference to the index."""
        self.references[ref_id] = reference
        
        # Update type index
        if reference.type not in self.by_type:
            self.by_type[reference.type] = []
        self.by_type[reference.type].append(ref_id)
        
        # Update status index
        if reference.status not in self.by_status:
            self.by_status[reference.status] = []
        self.by_status[reference.status].append(ref_id)
        
        # Update source file index
        if source_file:
            if source_file not in self.by_source_file:
                self.by_source_file[source_file] = []
            self.by_source_file[source_file].append(ref_id)
        
        # Update target index
        target = reference.resolved_path or reference.original
        if target not in self.by_target:
            self.by_target[target] = []
        self.by_target[target].append(ref_id)
    
    def get_references_by_type(self, ref_type: ReferenceType) -> List[Reference]:
        """Get all references of a specific type."""
        ref_ids = self.by_type.get(ref_type, [])
        return [self.references[ref_id] for ref_id in ref_ids]
    
    def get_references_by_status(self, status: ReferenceStatus) -> List[Reference]:
        """Get all references with a specific status."""
        ref_ids = self.by_status.get(status, [])
        return [self.references[ref_id] for ref_id in ref_ids]


class ReferenceParser:
    """Parser for extracting references from various document formats."""
    
    def __init__(self):
        self.patterns = {
            # Internal repository references (@path/to/file)
            "internal": re.compile(r'@([^:\s\)]+)'),
            
            # Cross-repository references (@repo:path/to/file)
            "cross_repo": re.compile(r'@(\w+):([^\s\)]+)'),
            
            # External HTTP/HTTPS links
            "external": re.compile(r'https?://[^\s\)\]]+'),
            
            # Markdown links [text](url)
            "markdown_link": re.compile(r'\[([^\]]+)\]\(([^\)]+)\)'),
            
            # HTML links <a href="url">
            "html_link": re.compile(r'<a\s+href=["\']([^"\']+)["\'][^>]*>'),
            
            # Relative paths ./path or ../path
            "relative": re.compile(r'\.{1,2}/[^\s\)\]]+'),
            
            # Anchor links #section
            "anchor": re.compile(r'#[a-zA-Z0-9_-]+')
        }
    
    def extract_references(self, content: str, source_file: str = "") -> List[Reference]:
        """Extract all references from content."""
        references = []
        
        # Extract markdown links first to get context
        markdown_links = self.patterns["markdown_link"].findall(content)
        link_contexts = {url: text for text, url in markdown_links}
        
        # Extract cross-repository references
        for match in self.patterns["cross_repo"].finditer(content):
            repo, path = match.group(1), match.group(2)
            ref = Reference(
                original=match.group(0),
                type=ReferenceType.CROSS_REPO,
                repository=repo,
                repository_path=path,
                context={"source_file": source_file, "link_text": link_contexts.get(match.group(0), "")}
            )
            references.append(ref)
        
        # Extract internal references (excluding cross-repo)
        for match in self.patterns["internal"].finditer(content):
            if not self.patterns["cross_repo"].match(match.group(0)):  # Exclude cross-repo matches
                ref = Reference(
                    original=match.group(0),
                    type=ReferenceType.INTERNAL,
                    context={"source_file": source_file, "link_text": link_contexts.get(match.group(0), "")}
                )
                references.append(ref)
        
        # Extract external references
        for match in self.patterns["external"].finditer(content):
            ref = Reference(
                original=match.group(0),
                type=ReferenceType.EXTERNAL,
                context={"source_file": source_file, "link_text": link_contexts.get(match.group(0), "")}
            )
            references.append(ref)
        
        # Extract relative references
        for match in self.patterns["relative"].finditer(content):
            ref = Reference(
                original=match.group(0),
                type=ReferenceType.RELATIVE,
                context={"source_file": source_file, "link_text": link_contexts.get(match.group(0), "")}
            )
            references.append(ref)
        
        # Extract anchor references
        for match in self.patterns["anchor"].finditer(content):
            ref = Reference(
                original=match.group(0),
                type=ReferenceType.ANCHOR,
                context={"source_file": source_file, "link_text": link_contexts.get(match.group(0), "")}
            )
            references.append(ref)
        
        return references


class ReferenceResolver:
    """Resolver for converting references to absolute paths and validating existence."""
    
    def __init__(self, base_path: str = "", repository_config: Optional[Dict[str, str]] = None):
        self.base_path = Path(base_path) if base_path else Path.cwd()
        self.repository_config = repository_config or {}
        self.session = requests.Session()
        self.session.timeout = 10
    
    def resolve_reference(self, reference: Reference, source_file: str = "") -> Reference:
        """Resolve a reference to its absolute path and validate existence."""
        if reference.type == ReferenceType.INTERNAL:
            return self._resolve_internal_reference(reference, source_file)
        elif reference.type == ReferenceType.CROSS_REPO:
            return self._resolve_cross_repo_reference(reference)
        elif reference.type == ReferenceType.EXTERNAL:
            return self._resolve_external_reference(reference)
        elif reference.type == ReferenceType.RELATIVE:
            return self._resolve_relative_reference(reference, source_file)
        elif reference.type == ReferenceType.ANCHOR:
            return self._resolve_anchor_reference(reference, source_file)
        else:
            reference.status = ReferenceStatus.UNKNOWN
            reference.error_message = f"Unknown reference type: {reference.type}"
            return reference
    
    def _resolve_internal_reference(self, reference: Reference, source_file: str = "") -> Reference:
        """Resolve internal repository reference."""
        # Remove @ prefix
        path = reference.original[1:] if reference.original.startswith("@") else reference.original
        
        # Convert to absolute path
        absolute_path = self.base_path / path
        reference.absolute_path = str(absolute_path)
        reference.resolved_path = str(absolute_path)
        
        # Check if path exists
        if absolute_path.exists():
            reference.target_exists = True
            reference.status = ReferenceStatus.VALID
        else:
            reference.target_exists = False
            reference.status = ReferenceStatus.BROKEN
            reference.error_message = f"Path does not exist: {absolute_path}"
        
        # Calculate relative path from source
        if source_file:
            try:
                source_path = Path(source_file).parent
                relative_path = os.path.relpath(absolute_path, source_path)
                reference.relative_from_source = relative_path
            except ValueError:
                pass  # Paths on different drives on Windows
        
        return reference
    
    def _resolve_cross_repo_reference(self, reference: Reference) -> Reference:
        """Resolve cross-repository reference."""
        repo_name = reference.repository
        repo_path = reference.repository_path
        
        if repo_name in self.repository_config:
            # Get repository base path from configuration
            repo_base = Path(self.repository_config[repo_name])
            absolute_path = repo_base / repo_path
            
            reference.resolved_path = str(absolute_path)
            reference.absolute_path = str(absolute_path)
            
            # Check if path exists
            if absolute_path.exists():
                reference.target_exists = True
                reference.status = ReferenceStatus.VALID
            else:
                reference.target_exists = False
                reference.status = ReferenceStatus.BROKEN
                reference.error_message = f"Cross-repo path does not exist: {absolute_path}"
        else:
            reference.status = ReferenceStatus.INVALID
            reference.error_message = f"Unknown repository: {repo_name}"
        
        return reference
    
    def _resolve_external_reference(self, reference: Reference) -> Reference:
        """Resolve external HTTP/HTTPS reference."""
        try:
            response = self.session.head(reference.original, allow_redirects=True)
            reference.response_code = response.status_code
            
            if response.status_code == 200:
                reference.target_exists = True
                reference.status = ReferenceStatus.VALID
            elif response.status_code in [301, 302, 303, 307, 308]:
                reference.target_exists = True
                reference.status = ReferenceStatus.VALID
                reference.resolved_path = response.url
            else:
                reference.target_exists = False
                reference.status = ReferenceStatus.BROKEN
                reference.error_message = f"HTTP {response.status_code}: {reference.original}"
        
        except requests.exceptions.RequestException as e:
            reference.target_exists = False
            reference.status = ReferenceStatus.BROKEN
            reference.error_message = f"Request failed: {str(e)}"
        
        reference.last_checked = str(datetime.now())
        return reference
    
    def _resolve_relative_reference(self, reference: Reference, source_file: str = "") -> Reference:
        """Resolve relative path reference."""
        if not source_file:
            reference.status = ReferenceStatus.INVALID
            reference.error_message = "Cannot resolve relative path without source file context"
            return reference
        
        source_path = Path(source_file).parent
        absolute_path = source_path / reference.original
        absolute_path = absolute_path.resolve()  # Normalize path
        
        reference.absolute_path = str(absolute_path)
        reference.resolved_path = str(absolute_path)
        
        # Check if path exists
        if absolute_path.exists():
            reference.target_exists = True
            reference.status = ReferenceStatus.VALID
        else:
            reference.target_exists = False
            reference.status = ReferenceStatus.BROKEN
            reference.error_message = f"Relative path does not exist: {absolute_path}"
        
        return reference
    
    def _resolve_anchor_reference(self, reference: Reference, source_file: str = "") -> Reference:
        """Resolve anchor reference within document."""
        # For anchor references, we need to check if the anchor exists in the current document
        # or in the referenced document if it's part of a link
        
        if source_file:
            reference.resolved_path = f"{source_file}{reference.original}"
            
            # Check if anchor exists in source file
            if Path(source_file).exists():
                with open(source_file, 'r', encoding='utf-8') as f:
                    content = f.read()
                
                # Look for header that matches anchor
                anchor_name = reference.original[1:]  # Remove #
                header_patterns = [
                    rf'^#{1,6}\s+.*{re.escape(anchor_name)}.*$',  # Markdown headers
                    rf'<h[1-6][^>]*id=["\']?{re.escape(anchor_name)}["\']?[^>]*>',  # HTML headers with id
                    rf'<[^>]+id=["\']?{re.escape(anchor_name)}["\']?[^>]*>'  # Any element with id
                ]
                
                anchor_found = any(
                    re.search(pattern, content, re.MULTILINE | re.IGNORECASE)
                    for pattern in header_patterns
                )
                
                if anchor_found:
                    reference.target_exists = True
                    reference.status = ReferenceStatus.VALID
                else:
                    reference.target_exists = False
                    reference.status = ReferenceStatus.BROKEN
                    reference.error_message = f"Anchor not found in document: {anchor_name}"
            else:
                reference.target_exists = False
                reference.status = ReferenceStatus.BROKEN
                reference.error_message = f"Source file does not exist: {source_file}"
        else:
            reference.status = ReferenceStatus.INVALID
            reference.error_message = "Cannot resolve anchor without source file context"
        
        return reference


class CrossReferenceValidator:
    """Validator for cross-reference integrity and quality."""
    
    def __init__(self, resolver: ReferenceResolver):
        self.resolver = resolver
        self.validation_cache = {}
    
    def validate_references(self, references: List[Reference], source_file: str = "") -> Dict[str, Any]:
        """Validate a list of references and return comprehensive results."""
        results = {
            "total_references": len(references),
            "valid_references": 0,
            "broken_references": 0,
            "invalid_references": 0,
            "unknown_references": 0,
            "by_type": {},
            "issues": [],
            "warnings": [],
            "suggestions": []
        }
        
        # Validate each reference
        for i, reference in enumerate(references):
            ref_id = f"{source_file}#{i}" if source_file else str(i)
            
            # Check cache first
            cache_key = f"{reference.original}#{reference.type.value}"
            if cache_key in self.validation_cache:
                cached_ref = self.validation_cache[cache_key]
                reference.status = cached_ref.status
                reference.target_exists = cached_ref.target_exists
                reference.error_message = cached_ref.error_message
            else:
                # Resolve and validate
                reference = self.resolver.resolve_reference(reference, source_file)
                self.validation_cache[cache_key] = reference
            
            # Update counters
            if reference.status == ReferenceStatus.VALID:
                results["valid_references"] += 1
            elif reference.status == ReferenceStatus.BROKEN:
                results["broken_references"] += 1
                results["issues"].append({
                    "type": "broken_reference",
                    "reference": reference.original,
                    "error": reference.error_message,
                    "source": source_file
                })
            elif reference.status == ReferenceStatus.INVALID:
                results["invalid_references"] += 1
                results["issues"].append({
                    "type": "invalid_reference",
                    "reference": reference.original,
                    "error": reference.error_message,
                    "source": source_file
                })
            else:
                results["unknown_references"] += 1
            
            # Update type counters
            ref_type = reference.type.value
            if ref_type not in results["by_type"]:
                results["by_type"][ref_type] = {"total": 0, "valid": 0, "broken": 0}
            
            results["by_type"][ref_type]["total"] += 1
            if reference.status == ReferenceStatus.VALID:
                results["by_type"][ref_type]["valid"] += 1
            elif reference.status == ReferenceStatus.BROKEN:
                results["by_type"][ref_type]["broken"] += 1
        
        # Generate warnings and suggestions
        self._generate_quality_feedback(results, references)
        
        return results
    
    def _generate_quality_feedback(self, results: Dict[str, Any], references: List[Reference]):
        """Generate quality feedback, warnings, and suggestions."""
        total = results["total_references"]
        broken = results["broken_references"]
        
        # Warning thresholds
        if total > 0:
            broken_percentage = (broken / total) * 100
            
            if broken_percentage > 10:
                results["warnings"].append(
                    f"High percentage of broken references: {broken_percentage:.1f}% ({broken}/{total})"
                )
            
            if broken_percentage > 25:
                results["warnings"].append(
                    "Consider reviewing reference management practices"
                )
        
        # Suggestions based on reference patterns
        external_refs = [r for r in references if r.type == ReferenceType.EXTERNAL]
        if len(external_refs) > 20:
            results["suggestions"].append(
                "Consider caching external references or creating a reference index"
            )
        
        # Check for duplicate references
        ref_counts = {}
        for ref in references:
            ref_counts[ref.original] = ref_counts.get(ref.original, 0) + 1
        
        duplicates = {ref: count for ref, count in ref_counts.items() if count > 3}
        if duplicates:
            results["suggestions"].append(
                f"Consider consolidating frequently referenced items: {list(duplicates.keys())[:3]}"
            )


class CrossReferenceManager:
    """Main manager for cross-reference system."""
    
    def __init__(self, base_path: str = "", repository_config: Optional[Dict[str, str]] = None):
        self.base_path = base_path
        self.repository_config = repository_config or {}
        self.parser = ReferenceParser()
        self.resolver = ReferenceResolver(base_path, repository_config)
        self.validator = CrossReferenceValidator(self.resolver)
        self.index = CrossReferenceIndex()
        self.logger = self._setup_logging()
    
    def _setup_logging(self) -> logging.Logger:
        """Set up logging for the cross-reference manager."""
        logger = logging.getLogger("cross_reference_manager")
        logger.setLevel(logging.INFO)
        
        if not logger.handlers:
            handler = logging.StreamHandler()
            formatter = logging.Formatter(
                '%(asctime)s - %(name)s - %(levelname)s - %(message)s'
            )
            handler.setFormatter(formatter)
            logger.addHandler(handler)
        
        return logger
    
    def scan_directory(self, directory: str, file_patterns: List[str] = None) -> Dict[str, Any]:
        """Scan directory for all references and build comprehensive index."""
        if file_patterns is None:
            file_patterns = ["*.md", "*.txt", "*.rst", "*.html"]
        
        directory_path = Path(directory)
        scan_results = {
            "scanned_files": 0,
            "total_references": 0,
            "validation_results": {},
            "summary": {}
        }
        
        self.logger.info(f"Starting directory scan: {directory}")
        
        # Find all matching files
        files_to_scan = []
        for pattern in file_patterns:
            files_to_scan.extend(directory_path.rglob(pattern))
        
        # Scan each file
        for file_path in files_to_scan:
            try:
                self.logger.debug(f"Scanning file: {file_path}")
                file_results = self.scan_file(str(file_path))
                scan_results["scanned_files"] += 1
                scan_results["total_references"] += file_results["total_references"]
                scan_results["validation_results"][str(file_path)] = file_results
            
            except Exception as e:
                self.logger.error(f"Error scanning file {file_path}: {str(e)}")
        
        # Generate summary
        scan_results["summary"] = self._generate_scan_summary(scan_results)
        
        self.logger.info(f"Scan complete: {scan_results['scanned_files']} files, {scan_results['total_references']} references")
        
        return scan_results
    
    def scan_file(self, file_path: str) -> Dict[str, Any]:
        """Scan a single file for references."""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                content = f.read()
        except UnicodeDecodeError:
            # Try with different encoding
            with open(file_path, 'r', encoding='latin-1') as f:
                content = f.read()
        
        # Extract references
        references = self.parser.extract_references(content, file_path)
        
        # Validate references
        validation_results = self.validator.validate_references(references, file_path)
        
        # Add to index
        for i, reference in enumerate(references):
            ref_id = f"{file_path}#{i}"
            self.index.add_reference(ref_id, reference, file_path)
        
        return validation_results
    
    def generate_reference_report(self, output_format: str = "markdown") -> str:
        """Generate comprehensive reference report."""
        if output_format == "markdown":
            return self._generate_markdown_report()
        elif output_format == "json":
            return self._generate_json_report()
        elif output_format == "html":
            return self._generate_html_report()
        else:
            raise ValueError(f"Unsupported output format: {output_format}")
    
    def _generate_markdown_report(self) -> str:
        """Generate markdown format report."""
        report_lines = []
        
        # Header
        report_lines.extend([
            "# Cross-Reference Analysis Report",
            "",
            f"**Generated:** {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}",
            f"**Total References:** {len(self.index.references)}",
            ""
        ])
        
        # Summary by type
        report_lines.append("## Summary by Reference Type")
        report_lines.append("")
        
        for ref_type in ReferenceType:
            refs = self.index.get_references_by_type(ref_type)
            if refs:
                valid_count = len([r for r in refs if r.status == ReferenceStatus.VALID])
                broken_count = len([r for r in refs if r.status == ReferenceStatus.BROKEN])
                
                report_lines.extend([
                    f"### {ref_type.value.title()} References",
                    f"- **Total:** {len(refs)}",
                    f"- **Valid:** {valid_count}",
                    f"- **Broken:** {broken_count}",
                    ""
                ])
        
        # Broken references section
        broken_refs = self.index.get_references_by_status(ReferenceStatus.BROKEN)
        if broken_refs:
            report_lines.extend([
                "## Broken References",
                "",
                "The following references need attention:",
                ""
            ])
            
            for ref in broken_refs:
                source_files = [
                    source for source, ref_ids in self.index.by_source_file.items()
                    if any(self.index.references[ref_id] == ref for ref_id in ref_ids)
                ]
                
                report_lines.extend([
                    f"- **Reference:** `{ref.original}`",
                    f"  - **Error:** {ref.error_message}",
                    f"  - **Source:** {', '.join(source_files)}",
                    ""
                ])
        
        # Recommendations
        report_lines.extend([
            "## Recommendations",
            "",
            "1. Fix all broken references listed above",
            "2. Consider implementing reference validation in CI/CD pipeline",
            "3. Use consistent reference formats across documents",
            "4. Regularly validate external links for availability",
            ""
        ])
        
        return "\n".join(report_lines)
    
    def _generate_json_report(self) -> str:
        """Generate JSON format report."""
        report_data = {
            "generated_at": datetime.now().isoformat(),
            "summary": {
                "total_references": len(self.index.references),
                "by_type": {},
                "by_status": {}
            },
            "references": {},
            "issues": []
        }
        
        # Summary by type
        for ref_type in ReferenceType:
            refs = self.index.get_references_by_type(ref_type)
            report_data["summary"]["by_type"][ref_type.value] = len(refs)
        
        # Summary by status
        for status in ReferenceStatus:
            refs = self.index.get_references_by_status(status)
            report_data["summary"]["by_status"][status.value] = len(refs)
        
        # Detailed references
        for ref_id, reference in self.index.references.items():
            report_data["references"][ref_id] = {
                "original": reference.original,
                "type": reference.type.value,
                "status": reference.status.value,
                "resolved_path": reference.resolved_path,
                "target_exists": reference.target_exists,
                "error_message": reference.error_message,
                "context": reference.context
            }
            
            # Add to issues if broken
            if reference.status == ReferenceStatus.BROKEN:
                report_data["issues"].append({
                    "reference_id": ref_id,
                    "reference": reference.original,
                    "error": reference.error_message,
                    "type": reference.type.value
                })
        
        return json.dumps(report_data, indent=2)
    
    def _generate_html_report(self) -> str:
        """Generate HTML format report."""
        # Basic HTML report template
        html_template = """
<!DOCTYPE html>
<html>
<head>
    <title>Cross-Reference Analysis Report</title>
    <style>
        body { font-family: Arial, sans-serif; margin: 20px; }
        .summary { background: #f5f5f5; padding: 15px; border-radius: 5px; }
        .broken { color: #d32f2f; }
        .valid { color: #388e3c; }
        table { border-collapse: collapse; width: 100%; }
        th, td { border: 1px solid #ddd; padding: 8px; text-align: left; }
        th { background-color: #f2f2f2; }
    </style>
</head>
<body>
    <h1>Cross-Reference Analysis Report</h1>
    <div class="summary">
        <h2>Summary</h2>
        <p><strong>Generated:</strong> {generated_at}</p>
        <p><strong>Total References:</strong> {total_references}</p>
    </div>
    
    <h2>References by Type</h2>
    <table>
        <tr><th>Type</th><th>Total</th><th>Valid</th><th>Broken</th></tr>
        {type_rows}
    </table>
    
    {broken_section}
</body>
</html>
        """
        
        # Generate type summary rows
        type_rows = []
        for ref_type in ReferenceType:
            refs = self.index.get_references_by_type(ref_type)
            if refs:
                valid_count = len([r for r in refs if r.status == ReferenceStatus.VALID])
                broken_count = len([r for r in refs if r.status == ReferenceStatus.BROKEN])
                
                type_rows.append(f"""
                <tr>
                    <td>{ref_type.value.title()}</td>
                    <td>{len(refs)}</td>
                    <td class="valid">{valid_count}</td>
                    <td class="broken">{broken_count}</td>
                </tr>
                """)
        
        # Generate broken references section
        broken_refs = self.index.get_references_by_status(ReferenceStatus.BROKEN)
        broken_section = ""
        if broken_refs:
            broken_section = "<h2>Broken References</h2><ul>"
            for ref in broken_refs:
                broken_section += f"<li><strong>{ref.original}</strong> - {ref.error_message}</li>"
            broken_section += "</ul>"
        
        return html_template.format(
            generated_at=datetime.now().strftime('%Y-%m-%d %H:%M:%S'),
            total_references=len(self.index.references),
            type_rows="".join(type_rows),
            broken_section=broken_section
        )
    
    def _generate_scan_summary(self, scan_results: Dict[str, Any]) -> Dict[str, Any]:
        """Generate summary statistics from scan results."""
        summary = {
            "files_scanned": scan_results["scanned_files"],
            "total_references": scan_results["total_references"],
            "valid_references": 0,
            "broken_references": 0,
            "most_referenced_files": [],
            "problematic_files": []
        }
        
        # Aggregate validation results
        for file_path, file_results in scan_results["validation_results"].items():
            summary["valid_references"] += file_results["valid_references"]
            summary["broken_references"] += file_results["broken_references"]
            
            # Track problematic files
            if file_results["broken_references"] > 0:
                summary["problematic_files"].append({
                    "file": file_path,
                    "broken_count": file_results["broken_references"]
                })
        
        # Sort problematic files by broken count
        summary["problematic_files"].sort(key=lambda x: x["broken_count"], reverse=True)
        
        return summary


# Import datetime here to avoid circular imports
from datetime import datetime


# Example usage and configuration
if __name__ == "__main__":
    # Example repository configuration
    repo_config = {
        "assetutilities": "/path/to/assetutilities",
        "aceengineer": "/path/to/aceengineer",
        "digitalmodel": "/path/to/digitalmodel"
    }
    
    # Initialize cross-reference manager
    manager = CrossReferenceManager(
        base_path="/mnt/github/github/assetutilities",
        repository_config=repo_config
    )
    
    # Scan directory for references
    results = manager.scan_directory(
        "/mnt/github/github/assetutilities/specs",
        ["*.md", "*.txt"]
    )
    
    # Generate report
    report = manager.generate_reference_report("markdown")
    print(report)
    
    # Save report to file
    with open("cross_reference_report.md", "w") as f:
        f.write(report)
    
    print(f"Scanned {results['scanned_files']} files")
    print(f"Found {results['total_references']} references")
    print(f"Report saved to cross_reference_report.md")