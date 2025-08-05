"""Tests for documentation integration system."""

import pytest
import tempfile
import shutil
from pathlib import Path
from unittest.mock import Mock, patch, mock_open

from assetutilities.agent_os.commands.documentation_integration import (
    RepositoryDocumentationScanner,
    ExternalDocumentationLinker,
    ReferenceManager,
    DocumentationProcessor,
    MarkdownParser
)


class TestRepositoryDocumentationScanner:
    """Test repository documentation scanning functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.repo_dir = Path(self.temp_dir) / "test_repo"
        self.repo_dir.mkdir()
        self.scanner = RepositoryDocumentationScanner()

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_scan_single_repository(self):
        """Test scanning a single repository for documentation."""
        # Create test files
        (self.repo_dir / "README.md").write_text("# Test Repository\nThis is a test.")
        (self.repo_dir / "docs").mkdir()
        (self.repo_dir / "docs" / "api.md").write_text("# API Documentation")
        (self.repo_dir / "src").mkdir()
        (self.repo_dir / "src" / "main.py").write_text('"""Main module."""\nclass TestClass:\n    """Test class."""\n    pass')

        result = self.scanner.scan_repository(self.repo_dir)

        assert result["name"] == "test_repo"
        assert len(result["markdown_files"]) >= 2
        assert len(result["python_docstrings"]) >= 1
        assert result["readme_content"] is not None
        assert "last_updated" in result

    def test_scan_multiple_repositories(self):
        """Test scanning multiple repositories."""
        # Create second repo
        repo2_dir = Path(self.temp_dir) / "repo2"
        repo2_dir.mkdir()
        (repo2_dir / "README.md").write_text("# Repo 2")

        repo_paths = [self.repo_dir, repo2_dir]
        results = self.scanner.scan_repositories(repo_paths)

        assert len(results) == 2
        assert "test_repo" in results
        assert "repo2" in results

    def test_extract_markdown_files(self):
        """Test extraction of markdown files."""
        # Create markdown files
        (self.repo_dir / "README.md").write_text("# Main README")
        docs_dir = self.repo_dir / "docs"
        docs_dir.mkdir()
        (docs_dir / "guide.md").write_text("# User Guide")
        (docs_dir / "api.md").write_text("# API Reference")

        markdown_files = self.scanner._extract_markdown_files(self.repo_dir)

        assert len(markdown_files) == 3
        file_names = [f["name"] for f in markdown_files]
        assert "README.md" in file_names
        assert "guide.md" in file_names
        assert "api.md" in file_names

    def test_extract_python_docstrings(self):
        """Test extraction of Python docstrings."""
        # Create Python files with docstrings
        python_file = self.repo_dir / "example.py"
        python_content = '''"""Module docstring."""

class TestClass:
    """Class docstring."""
    
    def test_method(self):
        """Method docstring."""
        pass

def test_function():
    """Function docstring."""
    return True
'''
        python_file.write_text(python_content)

        docstrings = self.scanner._extract_python_docstrings(self.repo_dir)

        assert len(docstrings) >= 1
        assert any("Module docstring" in ds["content"] for ds in docstrings)

    def test_scan_nonexistent_repository(self):
        """Test handling of non-existent repository."""
        nonexistent_path = Path(self.temp_dir) / "nonexistent"
        
        result = self.scanner.scan_repository(nonexistent_path)
        
        assert result["name"] == "nonexistent"
        assert result["markdown_files"] == []
        assert result["python_docstrings"] == []
        assert result["readme_content"] is None

    def test_filter_by_patterns(self):
        """Test filtering files by patterns."""
        # Create various files
        (self.repo_dir / "README.md").write_text("# README")
        (self.repo_dir / "CHANGELOG.md").write_text("# Changes")
        (self.repo_dir / "temp.md").write_text("# Temp")
        
        # Test include patterns
        files = self.scanner._extract_markdown_files(
            self.repo_dir, 
            include_patterns=["README*", "CHANGELOG*"]
        )
        
        file_names = [f["name"] for f in files]
        assert "README.md" in file_names
        assert "CHANGELOG.md" in file_names
        assert "temp.md" not in file_names


class TestExternalDocumentationLinker:
    """Test external documentation linking functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.linker = ExternalDocumentationLinker()

    @patch.object(ExternalDocumentationLinker, 'fetch_web_documentation')
    def test_fetch_web_documentation(self, mock_fetch):
        """Test fetching documentation from web sources."""
        mock_fetch.return_value = {
            "url": "https://example.com/docs",
            "status": "success",
            "content": "Documentation",
            "title": "Test Docs",
            "content_type": "text/html",
            "fetched_at": "2025-08-05T10:00:00",
            "size": 100
        }

        result = self.linker.fetch_web_documentation("https://example.com/docs")

        assert result["url"] == "https://example.com/docs"
        assert result["status"] == "success"
        assert "Documentation" in result["content"]
        assert "fetched_at" in result

    @patch.object(ExternalDocumentationLinker, 'fetch_web_documentation')
    def test_fetch_web_documentation_failure(self, mock_fetch):
        """Test handling of failed web requests."""
        mock_fetch.return_value = {
            "url": "https://example.com/docs",
            "status": "error",
            "error": "Network error",
            "fetched_at": "2025-08-05T10:00:00"
        }

        result = self.linker.fetch_web_documentation("https://example.com/docs")

        assert result["status"] == "error"
        assert "Network error" in result["error"]

    def test_parse_api_documentation(self):
        """Test parsing of API documentation."""
        api_content = """
        # API Reference
        
        ## GET /api/users
        Returns list of users
        
        ## POST /api/users
        Creates a new user
        """

        result = self.linker.parse_api_documentation(api_content)

        assert len(result["endpoints"]) == 2
        assert any(ep["method"] == "GET" for ep in result["endpoints"])
        assert any(ep["method"] == "POST" for ep in result["endpoints"])

    def test_extract_code_examples(self):
        """Test extraction of code examples from documentation."""
        doc_content = """
        # Documentation
        
        Here's an example:
        
        ```python
        def hello():
            print("Hello, World!")
        ```
        
        And another:
        
        ```javascript
        console.log("Hello, World!");
        ```
        """

        examples = self.linker.extract_code_examples(doc_content)

        assert len(examples) == 2
        languages = [ex["language"] for ex in examples]
        assert "python" in languages
        assert "javascript" in languages


class TestReferenceManager:
    """Test reference management functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = ReferenceManager(Path(self.temp_dir))

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_create_reference_structure(self):
        """Test creation of reference structure."""
        references = {
            "repositories": ["repo1", "repo2"],
            "external_docs": ["https://example.com/docs"],
            "api_endpoints": ["/api/v1/users"]
        }

        self.manager.create_reference_structure("test-agent", references)

        agent_dir = Path(self.temp_dir) / "test-agent"
        assert agent_dir.exists()
        assert (agent_dir / "context" / "repository" / "references.yaml").exists()

    def test_update_internal_references(self):
        """Test updating internal documentation references."""
        agent_dir = Path(self.temp_dir) / "test-agent"
        agent_dir.mkdir(parents=True)
        
        repo_docs = {
            "repo1": {
                "markdown_files": [{"name": "README.md", "path": "README.md", "content": "# Repo 1"}],
                "python_docstrings": [{"content": "Module docs", "name": "module", "file": "module.py", "type": "module"}]
            }
        }

        self.manager.update_internal_references("test-agent", repo_docs)

        internal_md = agent_dir / "context" / "repository" / "internal.md"
        assert internal_md.exists()
        
        content = internal_md.read_text()
        assert "Repo 1" in content
        assert "Module docs" in content

    def test_update_external_references(self):
        """Test updating external documentation references."""
        agent_dir = Path(self.temp_dir) / "test-agent"
        agent_dir.mkdir(parents=True)
        
        external_docs = [
            {
                "url": "https://example.com/docs",
                "content": "External documentation",
                "type": "web"
            }
        ]

        self.manager.update_external_references("test-agent", external_docs)

        external_yaml = agent_dir / "context" / "external" / "web_sources.yaml"
        assert external_yaml.exists()

    def test_generate_cross_references(self):
        """Test generation of cross-references between documents."""
        documents = [
            {"name": "doc1.md", "content": "This refers to UserClass"},
            {"name": "doc2.md", "content": "UserClass is defined here"},
            {"name": "doc3.md", "content": "See the API endpoint /users"}
        ]

        cross_refs = self.manager.generate_cross_references(documents)

        assert len(cross_refs) > 0
        assert any("UserClass" in ref["term"] for ref in cross_refs)


class TestDocumentationProcessor:
    """Test documentation processing functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.processor = DocumentationProcessor()

    def test_process_markdown_content(self):
        """Test processing of markdown content."""
        markdown_content = """
        # Title
        
        This is **bold** text and *italic* text.
        
        ## Code Example
        
        ```python
        def hello():
            return "Hello, World!"
        ```
        
        - List item 1
        - List item 2
        """

        result = self.processor.process_markdown_content(markdown_content)

        assert result["title"] == "Title"
        assert len(result["sections"]) >= 2
        assert len(result["code_blocks"]) == 1
        assert result["code_blocks"][0]["language"] == "python"

    def test_extract_api_patterns(self):
        """Test extraction of API patterns from documentation."""
        content = """
        GET /api/users - Get all users
        POST /api/users - Create user
        PUT /api/users/{id} - Update user
        DELETE /api/users/{id} - Delete user
        """

        patterns = self.processor.extract_api_patterns(content)

        assert len(patterns) == 4
        methods = [p["method"] for p in patterns]
        assert "GET" in methods
        assert "POST" in methods
        assert "PUT" in methods
        assert "DELETE" in methods

    def test_extract_domain_concepts(self):
        """Test extraction of domain-specific concepts."""
        content = """
        The UserService handles user management operations.
        The PaymentProcessor processes financial transactions.
        Authentication is handled by the AuthManager.
        """

        concepts = self.processor.extract_domain_concepts(content)

        concept_names = [c["name"] for c in concepts]
        assert "UserService" in concept_names
        assert "PaymentProcessor" in concept_names
        assert "AuthManager" in concept_names

    def test_create_summary(self):
        """Test creation of documentation summary."""
        documents = [
            {
                "name": "user_guide.md",
                "content": "This guide explains how to use the system.",
                "type": "markdown"
            },
            {
                "name": "api_reference.md", 
                "content": "API endpoints for the system.",
                "type": "markdown"
            }
        ]

        summary = self.processor.create_summary(documents)

        assert "total_documents" in summary
        assert summary["total_documents"] == 2
        assert "document_types" in summary
        assert "key_topics" in summary


class TestMarkdownParser:
    """Test markdown parsing functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.parser = MarkdownParser()

    def test_parse_headers(self):
        """Test parsing of markdown headers."""
        markdown = """
        # Main Title
        
        ## Section 1
        
        Content here.
        
        ### Subsection 1.1
        
        More content.
        
        ## Section 2
        
        Final content.
        """

        headers = self.parser.parse_headers(markdown)

        assert len(headers) == 4
        assert headers[0]["level"] == 1
        assert headers[0]["text"] == "Main Title"
        assert headers[1]["level"] == 2
        assert headers[1]["text"] == "Section 1"

    def test_parse_code_blocks(self):
        """Test parsing of code blocks."""
        markdown = """
        Here's some Python:
        
        ```python
        def hello():
            return "Hello"
        ```
        
        And some JavaScript:
        
        ```js
        function hello() {
            return "Hello";
        }
        ```
        """

        code_blocks = self.parser.parse_code_blocks(markdown)

        assert len(code_blocks) == 2
        assert code_blocks[0]["language"] == "python"
        assert code_blocks[1]["language"] == "js"
        assert "def hello" in code_blocks[0]["content"]

    def test_parse_links(self):
        """Test parsing of markdown links."""
        markdown = """
        Check out [Google](https://google.com) and [GitHub](https://github.com).
        
        Also see [internal link](./docs/api.md).
        """

        links = self.parser.parse_links(markdown)

        assert len(links) == 3
        urls = [link["url"] for link in links]
        assert "https://google.com" in urls
        assert "https://github.com" in urls
        assert "./docs/api.md" in urls

    def test_extract_tables(self):
        """Test extraction of markdown tables."""
        markdown = """
        | Method | Endpoint | Description |
        |--------|----------|-------------|
        | GET    | /users   | Get users   |
        | POST   | /users   | Create user |
        """

        tables = self.parser.extract_tables(markdown)

        assert len(tables) == 1
        table = tables[0]
        assert len(table["headers"]) == 3
        assert len(table["rows"]) == 2
        assert "Method" in table["headers"]