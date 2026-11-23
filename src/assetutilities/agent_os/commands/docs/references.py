# ABOUTME: Documentation reference management and cross-referencing.
# ABOUTME: Extracted from documentation_integration.py ReferenceManager class.
"""Documentation reference management."""

import re
import yaml
from pathlib import Path
from typing import List, Dict, Any
from datetime import datetime

from assetutilities.agent_os.commands.docs.scanner import DocumentReference

class ReferenceManager:
    """Manages documentation references and cross-references."""

    def __init__(self, base_dir: Path):
        """Initialize the reference manager.
        
        Args:
            base_dir: Base directory for agents
        """
        self.base_dir = base_dir

    def create_reference_structure(self, agent_name: str, 
                                 references: Dict[str, Any]) -> None:
        """Create reference structure for an agent.
        
        Args:
            agent_name: Name of the agent
            references: Reference configuration
        """
        agent_dir = self.base_dir / agent_name
        context_dir = agent_dir / "context"
        
        # Create directories
        (context_dir / "repository").mkdir(parents=True, exist_ok=True)
        (context_dir / "external").mkdir(parents=True, exist_ok=True)
        
        # Save references configuration
        references_path = context_dir / "repository" / "references.yaml"
        with open(references_path, 'w') as f:
            yaml.dump(references, f, default_flow_style=False, indent=2)

    def update_internal_references(self, agent_name: str, 
                                 repo_docs: Dict[str, Dict[str, Any]]) -> None:
        """Update internal documentation references.
        
        Args:
            agent_name: Name of the agent
            repo_docs: Repository documentation data
        """
        agent_dir = self.base_dir / agent_name
        internal_path = agent_dir / "context" / "repository" / "internal.md"
        
        # Generate internal documentation
        content = self._generate_internal_doc(repo_docs)
        
        agent_dir.mkdir(parents=True, exist_ok=True)
        internal_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(internal_path, 'w') as f:
            f.write(content)

    def update_external_references(self, agent_name: str,
                                 external_docs: List[Dict[str, Any]]) -> None:
        """Update external documentation references.
        
        Args:
            agent_name: Name of the agent
            external_docs: External documentation data
        """
        agent_dir = self.base_dir / agent_name
        external_path = agent_dir / "context" / "external" / "web_sources.yaml"
        
        external_path.parent.mkdir(parents=True, exist_ok=True)
        
        with open(external_path, 'w') as f:
            yaml.dump(external_docs, f, default_flow_style=False, indent=2)

    def generate_cross_references(self, documents: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
        """Generate cross-references between documents.
        
        Args:
            documents: List of documents to cross-reference
            
        Returns:
            List of cross-references
        """
        cross_refs = []
        
        # Extract terms from all documents
        all_terms = set()
        for doc in documents:
            terms = self._extract_terms(doc["content"])
            all_terms.update(terms)
        
        # Find cross-references
        for term in all_terms:
            references = []
            for doc in documents:
                if term.lower() in doc["content"].lower():
                    references.append({
                        "document": doc["name"],
                        "context": self._extract_context(doc["content"], term)
                    })
            
            if len(references) > 1:  # Term appears in multiple documents
                cross_refs.append({
                    "term": term,
                    "references": references,
                    "count": len(references)
                })
        
        return cross_refs

    def _generate_internal_doc(self, repo_docs: Dict[str, Dict[str, Any]]) -> str:
        """Generate internal documentation content.
        
        Args:
            repo_docs: Repository documentation data
            
        Returns:
            Generated documentation content
        """
        content = ["# Internal Documentation References\n"]
        content.append(f"Generated: {datetime.now().isoformat()}\n")
        
        for repo_name, docs in repo_docs.items():
            content.append(f"## {repo_name}\n")
            
            # Add README content
            if docs.get("readme_content"):
                content.append("### README\n")
                content.append(docs["readme_content"][:500] + "...\n")
            
            # Add markdown files
            if docs.get("markdown_files"):
                content.append("### Documentation Files\n")
                for md_file in docs["markdown_files"]:
                    content.append(f"#### {md_file['name']}\n")
                    content.append(f"Path: `{md_file['path']}`\n")
                    content.append(md_file["content"][:300] + "...\n")
            
            # Add docstrings
            if docs.get("python_docstrings"):
                content.append("### Python Documentation\n")
                for docstring in docs["python_docstrings"]:
                    content.append(f"#### {docstring['name']} ({docstring['type']})\n")
                    content.append(f"File: `{docstring['file']}`\n")
                    content.append(docstring["content"] + "\n")
        
        return "\n".join(content)

    def _extract_terms(self, content: str) -> List[str]:
        """Extract important terms from content.
        
        Args:
            content: Content to extract terms from
            
        Returns:
            List of extracted terms
        """
        # Simple term extraction - could be enhanced with NLP
        terms = []
        
        # Extract class names (PascalCase)
        class_pattern = r'\b[A-Z][a-zA-Z0-9]*(?:[A-Z][a-zA-Z0-9]*)*\b'
        terms.extend(re.findall(class_pattern, content))
        
        # Extract function names with parentheses
        function_pattern = r'\b[a-z_][a-zA-Z0-9_]*\(\)'
        terms.extend([term[:-2] for term in re.findall(function_pattern, content)])
        
        # Extract API endpoints
        api_pattern = r'/[a-zA-Z0-9_/\-]+'
        terms.extend(re.findall(api_pattern, content))
        
        return list(set(terms))

    def _extract_context(self, content: str, term: str) -> str:
        """Extract context around a term.
        
        Args:
            content: Content containing the term
            term: Term to find context for
            
        Returns:
            Context around the term
        """
        # Find the term and extract surrounding context
        pattern = re.compile(re.escape(term), re.IGNORECASE)
        match = pattern.search(content)
        
        if match:
            start = max(0, match.start() - 50)
            end = min(len(content), match.end() + 50)
            return content[start:end].strip()
        
        return ""


