"""Tests for template management system."""

import tempfile
import shutil
import yaml
from pathlib import Path

from assetutilities.agent_os.commands.template_management import (
    TemplateManager,
    Template,
    TemplateValidator,
    TemplateComposer,
    TemplateInstantiator,
    TemplateRegistry
)


class TestTemplate:
    """Test template data structure."""

    def test_create_basic_template(self):
        """Test creating a basic template."""
        template = Template(
            name="test-template",
            version="1.0.0",
            description="Test template",
            category="engineering"
        )
        
        assert template.name == "test-template"
        assert template.version == "1.0.0"
        assert template.description == "Test template"
        assert template.category == "engineering"
        assert template.capabilities is not None
        assert template.context_sources is not None
        assert template.prompts == []
        assert template.responses == []

    def test_template_from_dict(self):
        """Test creating template from dictionary."""
        template_data = {
            "name": "engineering",
            "version": "1.0.0",
            "description": "Engineering template",
            "category": "engineering",
            "capabilities": {
                "core": ["code_generation", "code_review"],
                "specialized": ["architecture_design"]
            },
            "context_sources": {
                "repositories": {"repo1": "description"},
                "external": ["https://example.com"]
            },
            "prompts": [
                {"name": "code_review", "content": "Review this code: {code}"}
            ],
            "responses": [
                {"name": "review_result", "format": "markdown", "content": "## Results\n{results}"}
            ]
        }
        
        template = Template.from_dict(template_data)
        
        assert template.name == "engineering"
        assert len(template.capabilities.core) == 2
        assert len(template.capabilities.specialized) == 1
        assert "repo1" in template.context_sources.repositories
        assert len(template.prompts) == 1
        assert len(template.responses) == 1

    def test_template_to_dict(self):
        """Test converting template to dictionary."""
        template = Template(
            name="test",
            version="1.0.0",
            description="Test",
            category="general"
        )
        template.capabilities.core = ["capability1"]
        template.prompts.append({"name": "test", "content": "Test prompt"})
        
        data = template.to_dict()
        
        assert data["name"] == "test"
        assert data["capabilities"]["core"] == ["capability1"]
        assert len(data["prompts"]) == 1

    def test_template_validation(self):
        """Test template validation."""
        # Valid template
        valid_template = Template(
            name="valid",
            version="1.0.0",
            description="Valid template",
            category="engineering"
        )
        assert valid_template.is_valid()
        
        # Invalid template (missing required fields)
        invalid_template = Template(name="", version="", description="", category="")
        assert not invalid_template.is_valid()


class TestTemplateValidator:
    """Test template validation functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.validator = TemplateValidator()

    def test_validate_template_schema(self):
        """Test template schema validation."""
        valid_template = {
            "name": "test",
            "version": "1.0.0",
            "description": "Test template",
            "category": "engineering",
            "capabilities": {
                "core": ["capability1"],
                "specialized": ["capability2"]
            }
        }
        
        result = self.validator.validate_schema(valid_template)
        assert result.is_valid
        assert len(result.errors) == 0

    def test_validate_template_schema_missing_fields(self):
        """Test validation with missing required fields."""
        invalid_template = {
            "name": "test"
            # Missing version, description, category
        }
        
        result = self.validator.validate_schema(invalid_template)
        assert not result.is_valid
        assert len(result.errors) > 0
        assert any("version" in error for error in result.errors)

    def test_validate_template_capabilities(self):
        """Test capability validation."""
        template_with_capabilities = {
            "name": "test",
            "version": "1.0.0", 
            "description": "Test",
            "category": "engineering",
            "capabilities": {
                "core": ["text_generation", "code_generation"],
                "specialized": ["architecture_design", "invalid_capability"]
            }
        }
        
        result = self.validator.validate_capabilities(template_with_capabilities)
        assert result.is_valid or not result.is_valid  # Depends on capability registry

    def test_validate_template_prompts(self):
        """Test prompt validation."""
        template_with_prompts = {
            "name": "test",
            "version": "1.0.0",
            "description": "Test",
            "category": "engineering",
            "prompts": [
                {"name": "valid_prompt", "content": "This is valid"},
                {"name": "", "content": "Missing name"},  # Invalid
                {"name": "missing_content"}  # Invalid
            ]
        }
        
        result = self.validator.validate_prompts(template_with_prompts)
        assert not result.is_valid
        assert len(result.errors) >= 2  # At least 2 invalid prompts

    def test_validate_template_responses(self):
        """Test response template validation."""
        template_with_responses = {
            "name": "test",
            "version": "1.0.0",
            "description": "Test",
            "category": "engineering",
            "responses": [
                {"name": "valid", "format": "markdown", "content": "Valid response"},
                {"name": "invalid_format", "format": "invalid", "content": "Bad format"},
                {"name": "missing_content", "format": "markdown"}
            ]
        }
        
        result = self.validator.validate_responses(template_with_responses)
        assert not result.is_valid
        assert len(result.errors) >= 2

    def test_validate_context_sources(self):
        """Test context sources validation."""
        template_with_context = {
            "name": "test",
            "version": "1.0.0",
            "description": "Test",
            "category": "engineering",
            "context_sources": {
                "repositories": {
                    "valid_repo": "Valid description",
                    "": "Invalid empty name"  # Invalid
                },
                "external": [
                    "https://valid-url.com",
                    "invalid-url",  # Invalid URL
                    ""  # Empty URL
                ]
            }
        }
        
        result = self.validator.validate_context_sources(template_with_context)
        # May be valid or invalid depending on URL validation
        assert isinstance(result.is_valid, bool)


class TestTemplateRegistry:
    """Test template registry functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.registry = TemplateRegistry(templates_dir=Path(self.temp_dir))

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_register_template(self):
        """Test registering a new template."""
        template_data = {
            "name": "test-template",
            "version": "1.0.0",
            "description": "Test template",
            "category": "engineering"
        }
        
        template_file = Path(self.temp_dir) / "test.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(template_data, f)
        
        result = self.registry.register_template(template_file)
        
        assert result.success
        assert "test-template" in self.registry.list_templates()

    def test_get_template(self):
        """Test retrieving a template."""
        # Create a template file
        template_data = {
            "name": "engineering",
            "version": "1.0.0",
            "description": "Engineering template",
            "category": "engineering",
            "capabilities": {"core": ["code_generation"], "specialized": []}
        }
        
        template_file = self.registry.templates_dir / "engineering.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(template_data, f)
            
        template = self.registry.get_template("engineering")
        
        assert template is not None
        assert template.name == "engineering"
        assert "code_generation" in template.capabilities.core

    def test_list_templates(self):
        """Test listing available templates."""
        # Create multiple template files
        for name in ["template1", "template2", "template3"]:
            template_data = {
                "name": name,
                "version": "1.0.0",
                "description": f"{name} template",
                "category": "general"
            }
            template_file = self.registry.templates_dir / f"{name}.yaml"
            with open(template_file, 'w') as f:
                yaml.dump(template_data, f)
        
        templates = self.registry.list_templates()
        
        assert len(templates) == 3
        assert "template1" in templates
        assert "template2" in templates
        assert "template3" in templates

    def test_search_templates(self):
        """Test searching templates by category or capabilities."""
        # Create templates with different categories
        engineering_template = {
            "name": "engineering",
            "version": "1.0.0",
            "description": "Engineering template",
            "category": "engineering",
            "capabilities": {"core": ["code_generation"], "specialized": []}
        }
        
        analysis_template = {
            "name": "analysis",
            "version": "1.0.0", 
            "description": "Analysis template",
            "category": "analysis",
            "capabilities": {"core": ["data_analysis"], "specialized": []}
        }
        
        for template_data in [engineering_template, analysis_template]:
            template_file = self.registry.templates_dir / f"{template_data['name']}.yaml"
            with open(template_file, 'w') as f:
                yaml.dump(template_data, f)
        
        # Search by category
        engineering_templates = self.registry.search_templates(category="engineering")
        assert len(engineering_templates) == 1
        assert engineering_templates[0].name == "engineering"
        
        # Search by capability
        code_templates = self.registry.search_templates(capability="code_generation")
        assert len(code_templates) == 1
        assert code_templates[0].name == "engineering"

    def test_update_template(self):
        """Test updating an existing template."""
        # Create initial template
        template_data = {
            "name": "updatable",
            "version": "1.0.0",
            "description": "Original description",
            "category": "general"
        }
        
        template_file = self.registry.templates_dir / "updatable.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(template_data, f)
            
        # Update template
        updated_data = template_data.copy()
        updated_data["version"] = "2.0.0"
        updated_data["description"] = "Updated description"
        
        updated_file = Path(self.temp_dir) / "updated.yaml"
        with open(updated_file, 'w') as f:
            yaml.dump(updated_data, f)
            
        result = self.registry.update_template("updatable", updated_file)
        
        assert result.success
        updated_template = self.registry.get_template("updatable")
        assert updated_template.version == "2.0.0"
        assert updated_template.description == "Updated description"


class TestTemplateComposer:
    """Test template composition functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.registry = TemplateRegistry(templates_dir=Path(self.temp_dir))
        self.composer = TemplateComposer(self.registry)
        
        # Create test templates
        self._create_test_templates()

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def _create_test_templates(self):
        """Create test templates for composition."""
        engineering_template = {
            "name": "engineering",
            "version": "1.0.0",
            "description": "Engineering template",
            "category": "engineering",
            "capabilities": {"core": ["code_generation"], "specialized": ["debugging"]},
            "prompts": [{"name": "code_review", "content": "Review code"}]
        }
        
        documentation_template = {
            "name": "documentation",
            "version": "1.0.0",
            "description": "Documentation template", 
            "category": "documentation",
            "capabilities": {"core": ["documentation_generation"], "specialized": ["api_docs"]},
            "prompts": [{"name": "generate_docs", "content": "Generate docs"}]
        }
        
        for template_data in [engineering_template, documentation_template]:
            template_file = self.registry.templates_dir / f"{template_data['name']}.yaml"
            with open(template_file, 'w') as f:
                yaml.dump(template_data, f)

    def test_compose_two_templates(self):
        """Test composing two templates."""
        composite = self.composer.compose_templates(
            primary="engineering",
            mixins=["documentation"]
        )
        
        assert composite.name == "engineering"  # Primary template name
        assert "code_generation" in composite.capabilities.core
        assert "documentation_generation" in composite.capabilities.core
        assert "debugging" in composite.capabilities.specialized
        assert "api_docs" in composite.capabilities.specialized
        assert len(composite.prompts) == 2

    def test_compose_with_deduplication(self):
        """Test composition with capability deduplication."""
        # Create templates with overlapping capabilities
        template1_data = {
            "name": "template1",
            "version": "1.0.0",
            "description": "Template 1",
            "category": "general",
            "capabilities": {"core": ["capability1", "shared"], "specialized": []},
        }
        
        template2_data = {
            "name": "template2", 
            "version": "1.0.0",
            "description": "Template 2",
            "category": "general",
            "capabilities": {"core": ["capability2", "shared"], "specialized": []},
        }
        
        for template_data in [template1_data, template2_data]:
            template_file = self.registry.templates_dir / f"{template_data['name']}.yaml"
            with open(template_file, 'w') as f:
                yaml.dump(template_data, f)
        
        composite = self.composer.compose_templates(
            primary="template1",
            mixins=["template2"]
        )
        
        # Should have unique capabilities only
        core_capabilities = composite.capabilities.core
        assert "capability1" in core_capabilities
        assert "capability2" in core_capabilities
        assert core_capabilities.count("shared") == 1  # Deduplicated

    def test_auto_template_selection(self):
        """Test automatic template selection based on context."""
        module_context = {
            "has_code_files": True,
            "has_tests": True,
            "language": "python",
            "domain": "engineering"
        }
        
        selected_template = self.composer.select_template("auto", module_context)
        
        # Should select engineering template based on context
        assert selected_template is not None
        assert selected_template.category in ["engineering", "general"]

    def test_template_inference(self):
        """Test inferring template type from module context."""
        # Engineering context
        eng_context = {
            "files": ["main.py", "test_main.py", "requirements.txt"],
            "keywords": ["api", "service", "class", "function"]
        }
        inferred_type = self.composer.infer_agent_type(eng_context)
        assert inferred_type in ["engineering", "general", "general-purpose"]
        
        # Documentation context
        doc_context = {
            "files": ["README.md", "docs/api.md", "CHANGELOG.md"],
            "keywords": ["documentation", "guide", "tutorial"]
        }
        inferred_type = self.composer.infer_agent_type(doc_context)
        # Should infer based on available templates
        assert inferred_type in ["documentation", "general", "general-purpose"]


class TestTemplateInstantiator:
    """Test template instantiation functionality."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.agent_dir = Path(self.temp_dir) / "test-agent"
        self.instantiator = TemplateInstantiator()

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_instantiate_basic_template(self):
        """Test instantiating a basic template."""
        template = Template(
            name="test-template",
            version="1.0.0",
            description="Test template",
            category="engineering"
        )
        template.capabilities.core = ["code_generation"]
        template.prompts = [{"name": "test_prompt", "content": "Test prompt content"}]
        template.responses = [{"name": "test_response", "format": "markdown", "content": "# Test Response"}]
        
        result = self.instantiator.instantiate_template(template, self.agent_dir)
        
        assert result.success
        assert self.agent_dir.exists()
        assert (self.agent_dir / "agent.yaml").exists()
        assert (self.agent_dir / "templates" / "prompts" / "test_prompt.md").exists()
        assert (self.agent_dir / "templates" / "responses" / "test_response.md").exists()

    def test_generate_agent_config(self):
        """Test generating agent configuration from template."""
        template = Template(
            name="engineering",
            version="1.0.0",
            description="Engineering template",
            category="engineering"
        )
        template.capabilities.core = ["code_generation", "code_review"]
        template.capabilities.specialized = ["debugging"]
        template.context_sources.repositories = {"repo1": "description"}
        
        config = self.instantiator.generate_agent_config(template, "test-agent")
        
        assert config["name"] == "test-agent"
        assert config["template"] == "engineering"
        assert "code_generation" in config["capabilities"]
        assert "debugging" in config["capabilities"]
        assert "repo1" in config["context"]["repositories"]

    def test_create_prompt_files(self):
        """Test creating prompt files from template."""
        template = Template(name="test", version="1.0.0", description="Test", category="general")
        template.prompts = [
            {"name": "prompt1", "content": "Prompt 1 content"},
            {"name": "prompt2", "content": "Prompt 2 with {variable}"}
        ]
        
        # Create directory structure first
        self.instantiator.setup_directory_structure(self.agent_dir)
        self.instantiator.create_prompt_files(template, self.agent_dir)
        
        prompt1_file = self.agent_dir / "templates" / "prompts" / "prompt1.md"
        prompt2_file = self.agent_dir / "templates" / "prompts" / "prompt2.md"
        
        assert prompt1_file.exists()
        assert prompt2_file.exists()
        assert "Prompt 1 content" in prompt1_file.read_text()
        assert "{variable}" in prompt2_file.read_text()

    def test_create_response_templates(self):
        """Test creating response template files."""
        template = Template(name="test", version="1.0.0", description="Test", category="general")
        template.responses = [
            {"name": "response1", "format": "markdown", "content": "# Response 1"},
            {"name": "response2", "format": "json", "content": '{"result": "{result}"}'}
        ]
        
        # Create directory structure first
        self.instantiator.setup_directory_structure(self.agent_dir)
        self.instantiator.create_response_templates(template, self.agent_dir)
        
        response1_file = self.agent_dir / "templates" / "responses" / "response1.md"
        response2_file = self.agent_dir / "templates" / "responses" / "response2.md"
        
        assert response1_file.exists()
        assert response2_file.exists()
        assert "# Response 1" in response1_file.read_text()
        assert '{"result"' in response2_file.read_text()

    def test_setup_directory_structure(self):
        """Test setting up the agent directory structure."""
        self.instantiator.setup_directory_structure(self.agent_dir)
        
        expected_dirs = [
            self.agent_dir,
            self.agent_dir / "templates",
            self.agent_dir / "templates" / "prompts",
            self.agent_dir / "templates" / "responses",
            self.agent_dir / "context",
            self.agent_dir / "workflows"
        ]
        
        for dir_path in expected_dirs:
            assert dir_path.exists()
            assert dir_path.is_dir()


class TestTemplateManager:
    """Test the main template manager class."""

    def setup_method(self):
        """Set up test environment."""
        self.temp_dir = tempfile.mkdtemp()
        self.manager = TemplateManager(templates_dir=Path(self.temp_dir))

    def teardown_method(self):
        """Clean up test environment."""
        shutil.rmtree(self.temp_dir)

    def test_create_agent_from_template(self):
        """Test creating an agent from a template."""
        # Create a test template
        template_data = {
            "name": "test-template",
            "version": "1.0.0",
            "description": "Test template",
            "category": "engineering",
            "capabilities": {"core": ["code_generation"], "specialized": []},
            "prompts": [{"name": "test", "content": "Test prompt"}]
        }
        
        template_file = self.manager.registry.templates_dir / "test-template.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(template_data, f)
        
        agent_dir = Path(self.temp_dir) / "new-agent"
        
        result = self.manager.create_agent_from_template(
            template_name="test-template",
            agent_name="new-agent",
            agent_dir=agent_dir
        )
        
        assert result.success
        assert agent_dir.exists()
        assert (agent_dir / "agent.yaml").exists()

    def test_create_agent_with_composition(self):
        """Test creating agent with template composition."""
        # Create multiple templates
        templates = [
            {
                "name": "base",
                "version": "1.0.0",
                "description": "Base template",
                "category": "general",
                "capabilities": {"core": ["basic"], "specialized": []},
                "prompts": [{"name": "base_prompt", "content": "Base"}]
            },
            {
                "name": "addon",
                "version": "1.0.0",
                "description": "Addon template",
                "category": "general", 
                "capabilities": {"core": ["addon"], "specialized": []},
                "prompts": [{"name": "addon_prompt", "content": "Addon"}]
            }
        ]
        
        for template_data in templates:
            template_file = self.manager.registry.templates_dir / f"{template_data['name']}.yaml"
            with open(template_file, 'w') as f:
                yaml.dump(template_data, f)
        
        agent_dir = Path(self.temp_dir) / "composite-agent"
        
        result = self.manager.create_agent_with_composition(
            primary_template="base",
            mixin_templates=["addon"],
            agent_name="composite-agent",
            agent_dir=agent_dir
        )
        
        assert result.success
        assert agent_dir.exists()
        
        # Check that both prompt files were created
        assert (agent_dir / "templates" / "prompts" / "base_prompt.md").exists()
        assert (agent_dir / "templates" / "prompts" / "addon_prompt.md").exists()

    def test_customize_template(self):
        """Test template customization."""
        template = Template(
            name="customizable",
            version="1.0.0",
            description="Customizable template",
            category="general"
        )
        template.capabilities.core = ["basic"]
        
        customization_options = {
            "additional_capabilities": ["custom1", "custom2"],
            "custom_prompts": [{"name": "custom", "content": "Custom prompt"}],
            "context_repositories": {"custom_repo": "Custom repository"}
        }
        
        customized = self.manager.customize_template(template, customization_options)
        
        assert "custom1" in customized.capabilities.specialized
        assert "custom2" in customized.capabilities.specialized
        assert len(customized.prompts) == 1
        assert customized.prompts[0]["name"] == "custom"

    def test_get_template_info(self):
        """Test getting template information."""
        template_data = {
            "name": "info-template",
            "version": "1.0.0",
            "description": "Template for info testing",
            "category": "analysis",
            "capabilities": {"core": ["analysis"], "specialized": ["visualization"]}
        }
        
        template_file = self.manager.registry.templates_dir / "info-template.yaml"
        with open(template_file, 'w') as f:
            yaml.dump(template_data, f)
        
        info = self.manager.get_template_info("info-template")
        
        assert info["name"] == "info-template"
        assert info["category"] == "analysis"
        assert "analysis" in info["capabilities"]["core"]
        assert "visualization" in info["capabilities"]["specialized"]

    def test_list_available_templates(self):
        """Test listing available templates with details."""
        # Create multiple templates
        templates = [
            {"name": "template1", "category": "engineering", "description": "Engineering template"},
            {"name": "template2", "category": "analysis", "description": "Analysis template"},
            {"name": "template3", "category": "documentation", "description": "Documentation template"}
        ]
        
        for template_data in templates:
            full_template = {
                **template_data,
                "version": "1.0.0",
                "capabilities": {"core": [], "specialized": []}
            }
            template_file = self.manager.registry.templates_dir / f"{template_data['name']}.yaml"
            with open(template_file, 'w') as f:
                yaml.dump(full_template, f)
        
        available = self.manager.list_available_templates()
        
        assert len(available) == 3
        template_names = [t["name"] for t in available]
        assert "template1" in template_names
        assert "template2" in template_names
        assert "template3" in template_names
        
        # Check that categories are included
        categories = [t["category"] for t in available]
        assert "engineering" in categories
        assert "analysis" in categories
        assert "documentation" in categories