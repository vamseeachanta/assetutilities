# ABOUTME: Cross-repository reference management for specs integration.
# ABOUTME: Extracted from specs_integration.py CrossRepositoryReferencer class.
"""Cross-repository referencing for specs integration."""

import json
import yaml
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from assetutilities.agent_os.commands.specs.models import OperationResult

class CrossRepositoryReferencer:
    """Manages cross-repository references and relationships."""

    def __init__(self):
        """Initialize cross-repository referencer."""
        self.repositories: Dict[str, Dict[str, Any]] = {}

    def add_repository_reference(self, repo_name: str, repo_info: Dict[str, Any]) -> OperationResult:
        """Add repository reference.
        
        Args:
            repo_name: Repository name
            repo_info: Repository information
            
        Returns:
            Operation result
        """
        try:
            self.repositories[repo_name] = {
                **repo_info,
                "added_at": datetime.now().isoformat()
            }
            
            return OperationResult(
                success=True,
                message=f"Added repository reference for '{repo_name}'"
            )
            
        except Exception as e:
            return OperationResult(success=False, message=f"Failed to add repository reference: {e}")

    def create_cross_references(self) -> List[Dict[str, Any]]:
        """Create cross-references between repositories.
        
        Returns:
            List of cross-reference relationships
        """
        cross_references = []
        
        repo_names = list(self.repositories.keys())
        
        for i, repo1_name in enumerate(repo_names):
            for repo2_name in repo_names[i+1:]:
                repo1 = self.repositories[repo1_name]
                repo2 = self.repositories[repo2_name]
                
                # Find common areas
                common_areas = self._find_common_areas(repo1, repo2)
                
                if common_areas:
                    cross_references.append({
                        "repositories": [repo1_name, repo2_name],
                        "common_areas": common_areas,
                        "relationship_strength": len(common_areas),
                        "created_at": datetime.now().isoformat()
                    })
        
        return cross_references

    def find_related_repositories(self, target_repo: str, similarity_threshold: float = 0.3) -> List[Dict[str, Any]]:
        """Find repositories related to target repository.
        
        Args:
            target_repo: Target repository name
            similarity_threshold: Minimum similarity score
            
        Returns:
            List of related repositories with similarity scores
        """
        if target_repo not in self.repositories:
            return []
        
        target_info = self.repositories[target_repo]
        related = []
        
        for repo_name, repo_info in self.repositories.items():
            if repo_name == target_repo:
                continue
            
            similarity = self._calculate_similarity(target_info, repo_info)
            
            if similarity >= similarity_threshold:
                related.append({
                    "repository": repo_name,
                    "similarity_score": similarity,
                    "common_elements": self._find_common_areas(target_info, repo_info),
                    "repository_info": repo_info
                })
        
        # Sort by similarity score
        return sorted(related, key=lambda x: x["similarity_score"], reverse=True)

    def generate_reference_map(self) -> Dict[str, Any]:
        """Generate complete reference map.
        
        Returns:
            Reference map with repositories and cross-references
        """
        return {
            "repositories": self.repositories,
            "cross_references": self.create_cross_references(),
            "generated_at": datetime.now().isoformat(),
            "total_repositories": len(self.repositories)
        }

    def export_references(self, export_path: Path) -> OperationResult:
        """Export references to file.
        
        Args:
            export_path: Export file path
            
        Returns:
            Operation result
        """
        try:
            reference_map = self.generate_reference_map()
            
            with open(export_path, 'w') as f:
                yaml.dump(reference_map, f, default_flow_style=False, indent=2)
            
            return OperationResult(
                success=True,
                message=f"Exported references to {export_path}",
                data={"repositories": len(self.repositories)}
            )
            
        except Exception as e:
            return OperationResult(success=False, message=f"Failed to export references: {e}")

    def _find_common_areas(self, repo1: Dict[str, Any], repo2: Dict[str, Any]) -> List[str]:
        """Find common areas between two repositories."""
        common_areas = []
        
        # Check common modules
        modules1 = set(repo1.get("key_modules", []))
        modules2 = set(repo2.get("key_modules", []))
        common_modules = modules1.intersection(modules2)
        common_areas.extend(common_modules)
        
        # Check common tags
        tags1 = set(repo1.get("tags", []))
        tags2 = set(repo2.get("tags", []))
        common_tags = tags1.intersection(tags2)
        common_areas.extend(common_tags)
        
        # Check language similarity
        if repo1.get("primary_language") == repo2.get("primary_language"):
            common_areas.append(f"language:{repo1.get('primary_language')}")
        
        return list(set(common_areas))  # Remove duplicates

    def _calculate_similarity(self, repo1: Dict[str, Any], repo2: Dict[str, Any]) -> float:
        """Calculate similarity score between repositories."""
        common_areas = self._find_common_areas(repo1, repo2)
        
        # Get all unique elements from both repositories
        all_elements1 = set(repo1.get("key_modules", []) + repo1.get("tags", []))
        all_elements2 = set(repo2.get("key_modules", []) + repo2.get("tags", []))
        
        total_elements = len(all_elements1.union(all_elements2))
        
        if total_elements == 0:
            return 0.0
        
        return len(common_areas) / total_elements


