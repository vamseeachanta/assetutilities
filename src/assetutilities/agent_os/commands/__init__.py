"""Agent OS commands module."""

from .create_module_agent import CreateModuleAgentCommand
from .documentation_integration import (
    RepositoryDocumentationScanner,
    ExternalDocumentationLinker,
    ReferenceManager,
    DocumentationProcessor,
    MarkdownParser
)
from .context_optimization import (
    ContextProcessor,
    DocumentChunker,
    EmbeddingGenerator,
    ContextCache,
    SemanticSearch,
    OptimizedContext
)
from .template_management import (
    TemplateManager,
    Template,
    TemplateValidator,
    TemplateComposer,
    TemplateInstantiator,
    TemplateRegistry
)
from .specs_integration import (
    SpecsIntegrationManager,
    WorkflowHook,
    PromptEvolutionTracker,
    CrossRepositoryReferencer,
    EnhancedSpecsConfig,
    WorkflowRefresher
)
from .cli import (
    CLIManager,
    InteractiveMode,
    ProgressIndicator,
    HelpSystem,
    ErrorHandler,
    CommandLineInterface
)

__all__ = [
    'CreateModuleAgentCommand',
    'RepositoryDocumentationScanner',
    'ExternalDocumentationLinker', 
    'ReferenceManager',
    'DocumentationProcessor',
    'MarkdownParser',
    'ContextProcessor',
    'DocumentChunker',
    'EmbeddingGenerator',
    'ContextCache',
    'SemanticSearch',
    'OptimizedContext',
    'TemplateManager',
    'Template',
    'TemplateValidator',
    'TemplateComposer',
    'TemplateInstantiator',
    'TemplateRegistry',
    'SpecsIntegrationManager',
    'WorkflowHook',
    'PromptEvolutionTracker',
    'CrossRepositoryReferencer',
    'EnhancedSpecsConfig',
    'WorkflowRefresher',
    'CLIManager',
    'InteractiveMode',
    'ProgressIndicator',
    'HelpSystem',
    'ErrorHandler',
    'CommandLineInterface'
]