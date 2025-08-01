/**
 * Module-Based Repository Organization Components
 * 
 * Handles the organization of specs into module-based directory structures:
 * - Module identification and classification
 * - Automatic folder structure generation  
 * - Subcategory handling for large modules
 * - Module index management and cross-references
 */

const fs = require('fs').promises;
const path = require('path');

/**
 * Organizes specs into module-based structures
 */
class ModuleOrganizer {
  constructor() {
    this.defaultModule = 'product';
    this.subcategoryThreshold = 5;
  }

  /**
   * Organize specs into module-based structure
   * @param {Array} specs - Array of spec objects with name and module properties
   * @returns {Object} Organized module structure with statistics
   */
  async organizeSpecs(specs) {
    const modules = {};
    const statistics = {
      totalSpecs: specs.length,
      totalModules: 0,
      moduleDistribution: {},
      subcategoriesNeeded: []
    };

    // Organize specs by module
    for (const spec of specs) {
      const moduleName = spec.module || this.defaultModule;
      
      if (!modules[moduleName]) {
        modules[moduleName] = [];
        statistics.moduleDistribution[moduleName] = 0;
      }
      
      modules[moduleName].push(spec.name);
      statistics.moduleDistribution[moduleName]++;
    }

    // Calculate statistics
    statistics.totalModules = Object.keys(modules).length;

    // Identify modules needing subcategories
    for (const [moduleName, specList] of Object.entries(modules)) {
      if (specList.length > this.subcategoryThreshold) {
        statistics.subcategoriesNeeded.push(moduleName);
      }
    }

    return {
      modules,
      statistics,
      subcategoriesNeeded: statistics.subcategoriesNeeded,
      organizationComplete: true
    };
  }

  /**
   * Get module organization recommendations
   * @param {Object} organizedData - Result from organizeSpecs
   * @returns {Object} Recommendations for module organization
   */
  getOrganizationRecommendations(organizedData) {
    const recommendations = [];

    // Check for large modules
    for (const moduleName of organizedData.subcategoriesNeeded) {
      recommendations.push({
        type: 'subcategory',
        module: moduleName,
        reason: `Module has ${organizedData.modules[moduleName].length} specs, consider subcategories`,
        action: 'Create subcategories for better organization'
      });
    }

    // Check for single-spec modules
    for (const [moduleName, specs] of Object.entries(organizedData.modules)) {
      if (specs.length === 1 && moduleName !== this.defaultModule) {
        recommendations.push({
          type: 'consolidation',
          module: moduleName,
          reason: 'Module has only one spec',
          action: 'Consider moving to a more general module or adding related specs'
        });
      }
    }

    return {
      recommendations,
      needsReview: recommendations.length > 0
    };
  }
}

/**
 * Generates folder structures for module-based organization
 */
class FolderStructureGenerator {
  constructor() {
    this.requiredDirectories = [
      'specs/modules',
      'docs/modules', 
      'src/modules',
      'tests/modules'
    ];
  }

  /**
   * Create complete module folder structure
   * @param {string} moduleName - Name of the module
   * @param {string} specName - Name of the spec
   * @returns {Object} Creation result with status and directories
   */
  async createModuleStructure(moduleName, specName) {
    const directories = this.generateDirectoryList(moduleName, specName);
    const result = {
      created: false,
      directories: directories,
      errors: []
    };

    try {
      // Check if main spec directory already exists
      const mainSpecPath = `specs/modules/${moduleName}/${specName}`;
      try {
        await fs.access(mainSpecPath);
        result.created = false;
        result.reason = `Spec directory ${mainSpecPath} already exists`;
        return result;
      } catch (error) {
        // Directory doesn't exist, continue with creation
      }

      // Create all directories
      for (const directory of directories) {
        try {
          await fs.mkdir(directory, { recursive: true });
        } catch (error) {
          result.errors.push({
            directory,
            error: error.message
          });
        }
      }

      if (result.errors.length === 0) {
        result.created = true;
        result.message = `Successfully created module structure for ${moduleName}/${specName}`;
      } else {
        result.created = false;
        result.message = `Partial creation with ${result.errors.length} errors`;
      }

      return result;

    } catch (error) {
      throw new Error(`Failed to create module structure: ${error.message}`);
    }
  }

  /**
   * Generate list of directories to create
   * @param {string} moduleName - Module name
   * @param {string} specName - Spec name
   * @returns {Array} List of directory paths
   * @private
   */
  generateDirectoryList(moduleName, specName) {
    return [
      // Spec directories
      `specs/modules/${moduleName}/${specName}`,
      `specs/modules/${moduleName}/${specName}/sub-specs`,
      
      // Documentation directories
      `docs/modules/${moduleName}`,
      
      // Source code directories
      `src/modules/${moduleName}`,
      
      // Test directories
      `tests/modules/${moduleName}/${specName}`,
      `tests/modules/${moduleName}/${specName}/unit`,
      `tests/modules/${moduleName}/${specName}/integration`,
      `tests/modules/${moduleName}/${specName}/e2e`,
      `tests/modules/${moduleName}/${specName}/security`,
      `tests/modules/${moduleName}/${specName}/performance`
    ];
  }

  /**
   * Create batch module structures for multiple specs
   * @param {Object} organizedModules - Organized module data
   * @returns {Object} Batch creation results
   */
  async createBatchStructures(organizedModules) {
    const results = {
      successful: [],
      failed: [],
      total: 0
    };

    for (const [moduleName, specNames] of Object.entries(organizedModules.modules)) {
      for (const specName of specNames) {
        results.total++;
        
        try {
          const result = await this.createModuleStructure(moduleName, specName);
          
          if (result.created) {
            results.successful.push({ moduleName, specName, directories: result.directories.length });
          } else {
            results.failed.push({ moduleName, specName, reason: result.reason || 'Unknown error' });
          }
        } catch (error) {
          results.failed.push({ moduleName, specName, reason: error.message });
        }
      }
    }

    results.successRate = (results.successful.length / results.total) * 100;
    return results;
  }

  /**
   * Validate existing module structure
   * @param {string} moduleName - Module name
   * @param {string} specName - Spec name
   * @returns {Object} Validation results
   */
  async validateModuleStructure(moduleName, specName) {
    const expectedDirectories = this.generateDirectoryList(moduleName, specName);
    const validation = {
      valid: true,
      missing: [],
      existing: []
    };

    for (const directory of expectedDirectories) {
      try {
        await fs.access(directory);
        validation.existing.push(directory);
      } catch (error) {
        validation.missing.push(directory);
        validation.valid = false;
      }
    }

    validation.completeness = (validation.existing.length / expectedDirectories.length) * 100;
    return validation;
  }
}

/**
 * Manages subcategories for large modules
 */
class SubcategoryManager {
  constructor() {
    this.subcategoryThreshold = 5;
    this.subcategoryPatterns = {
      'authentication': {
        'user-management': ['user', 'registration', 'profile', 'account'],
        'security': ['security', 'audit', 'encryption', 'hash', 'token'],
        'integration': ['oauth', 'saml', 'ldap', 'sso', 'integration'],
        'session': ['session', 'login', 'logout', 'jwt']
      },
      'e-commerce': {
        'catalog': ['product', 'catalog', 'inventory', 'category'],
        'orders': ['order', 'cart', 'checkout', 'purchase'],
        'customer': ['customer', 'review', 'rating', 'recommendation'],
        'payment': ['payment', 'billing', 'invoice', 'subscription']
      },
      'payment': {
        'processing': ['processing', 'transaction', 'gateway', 'merchant'],
        'security': ['fraud', 'security', 'validation', 'compliance'],
        'integration': ['integration', 'api', 'webhook', 'callback'],
        'reporting': ['reporting', 'analytics', 'reconciliation', 'audit']
      },
      'api': {
        'endpoints': ['endpoint', 'route', 'controller', 'handler'],
        'authentication': ['auth', 'token', 'security', 'permission'],
        'validation': ['validation', 'schema', 'sanitization', 'filter'],
        'integration': ['integration', 'webhook', 'client', 'sdk']
      }
    };
  }

  /**
   * Check if module needs subcategories
   * @param {string} moduleName - Module name
   * @param {Array} specs - List of spec names
   * @returns {boolean} Whether subcategories are needed
   */
  async needsSubcategories(moduleName, specs) {
    return specs.length > this.subcategoryThreshold;
  }

  /**
   * Generate subcategories for a module
   * @param {string} moduleName - Module name
   * @param {Array} specs - List of spec names
   * @returns {Object} Subcategory organization
   */
  async generateSubcategories(moduleName, specs) {
    const patterns = this.subcategoryPatterns[moduleName];
    const subcategories = {};
    const unmatched = [];

    if (!patterns) {
      // Generic subcategorization for unknown modules
      return this.generateGenericSubcategories(specs);
    }

    // Initialize subcategories
    for (const subcategoryName of Object.keys(patterns)) {
      subcategories[subcategoryName] = [];
    }

    // Categorize specs based on patterns
    for (const specName of specs) {
      let matched = false;
      const lowerSpecName = specName.toLowerCase();

      for (const [subcategoryName, keywords] of Object.entries(patterns)) {
        if (keywords.some(keyword => lowerSpecName.includes(keyword))) {
          subcategories[subcategoryName].push(specName);
          matched = true;
          break;
        }
      }

      if (!matched) {
        unmatched.push(specName);
      }
    }

    // Add unmatched specs to a misc category
    if (unmatched.length > 0) {
      subcategories.misc = unmatched;
    }

    // Remove empty subcategories
    for (const [subcategoryName, specList] of Object.entries(subcategories)) {
      if (specList.length === 0) {
        delete subcategories[subcategoryName];
      }
    }

    return subcategories;
  }

  /**
   * Generate generic subcategories for unknown modules
   * @param {Array} specs - List of spec names
   * @returns {Object} Generic subcategory organization
   * @private
   */
  generateGenericSubcategories(specs) {
    const subcategories = {
      'core': [],
      'integration': [],
      'misc': []
    };

    for (const specName of specs) {
      const lowerSpecName = specName.toLowerCase();
      
      if (lowerSpecName.includes('integration') || lowerSpecName.includes('api') || lowerSpecName.includes('webhook')) {
        subcategories.integration.push(specName);
      } else if (lowerSpecName.includes('core') || lowerSpecName.includes('main') || lowerSpecName.includes('primary')) {
        subcategories.core.push(specName);
      } else {
        subcategories.misc.push(specName);
      }
    }

    // Remove empty subcategories
    return Object.fromEntries(
      Object.entries(subcategories).filter(([_, specs]) => specs.length > 0)
    );
  }

  /**
   * Create subcategory folder structure
   * @param {string} moduleName - Module name
   * @param {Object} subcategories - Subcategory organization
   * @returns {Object} Creation results
   */
  async createSubcategoryStructure(moduleName, subcategories) {
    const results = {
      created: [],
      errors: []
    };

    for (const subcategoryName of Object.keys(subcategories)) {
      const subcategoryPath = `specs/modules/${moduleName}/${subcategoryName}`;
      
      try {
        await fs.mkdir(subcategoryPath, { recursive: true });
        results.created.push(subcategoryPath);
      } catch (error) {
        results.errors.push({
          subcategory: subcategoryName,
          path: subcategoryPath,
          error: error.message
        });
      }
    }

    return results;
  }

  /**
   * Get subcategory recommendations
   * @param {string} moduleName - Module name
   * @param {Array} specs - List of spec names
   * @returns {Object} Subcategory recommendations
   */
  async getSubcategoryRecommendations(moduleName, specs) {
    const recommendations = {
      shouldUseSubcategories: await this.needsSubcategories(moduleName, specs),
      suggestedStructure: null,
      benefits: [],
      considerations: []
    };

    if (recommendations.shouldUseSubcategories) {
      recommendations.suggestedStructure = await this.generateSubcategories(moduleName, specs);
      
      recommendations.benefits = [
        'Improved organization for large number of specs',
        'Easier navigation and discovery',
        'Better logical grouping of related functionality',
        'Reduced cognitive load when browsing specs'
      ];

      recommendations.considerations = [
        'Additional folder depth may complicate file paths',
        'Need to maintain subcategory consistency',
        'May require migration of existing specs',
        'Team needs to understand subcategory logic'
      ];
    }

    return recommendations;
  }
}

/**
 * Manages module indexes and cross-references
 */
class ModuleIndexManager {
  constructor() {
    this.indexTemplates = {
      module: this.generateModuleIndexTemplate.bind(this),
      repository: this.generateRepositoryIndexTemplate.bind(this)
    };
  }

  /**
   * Update module index documentation
   * @param {Object} moduleData - Module information
   * @returns {Object} Update results
   */
  async updateModuleIndex(moduleData) {
    const indexPath = `docs/modules/${moduleData.name}/README.md`;
    const indexContent = await this.generateModuleIndexContent(moduleData);

    try {
      await fs.mkdir(path.dirname(indexPath), { recursive: true });
      await fs.writeFile(indexPath, indexContent, 'utf8');
      
      return {
        updated: true,
        path: indexPath,
        specCount: moduleData.specs.length
      };
    } catch (error) {
      throw new Error(`Failed to update module index: ${error.message}`);
    }
  }

  /**
   * Create repository-wide module index
   * @param {Object} repositoryData - Repository organization data
   * @returns {Object} Creation results
   */
  async createRepositoryIndex(repositoryData) {
    const indexPath = 'docs/modules/README.md';
    const indexContent = await this.generateRepositoryIndexContent(repositoryData);

    try {
      await fs.mkdir(path.dirname(indexPath), { recursive: true });
      await fs.writeFile(indexPath, indexContent, 'utf8');
      
      return {
        created: true,
        path: indexPath,
        moduleCount: repositoryData.statistics.totalModules,
        specCount: repositoryData.statistics.totalSpecs
      };
    } catch (error) {
      throw new Error(`Failed to create repository index: ${error.message}`);
    }
  }

  /**
   * Generate module index content
   * @param {Object} moduleData - Module data
   * @returns {string} Module index markdown content
   * @private
   */
  async generateModuleIndexContent(moduleData) {
    const template = await this.generateModuleIndexTemplate(moduleData);
    return template;
  }

  /**
   * Generate repository index content
   * @param {Object} repositoryData - Repository data
   * @returns {string} Repository index markdown content
   * @private
   */
  async generateRepositoryIndexContent(repositoryData) {
    const template = await this.generateRepositoryIndexTemplate(repositoryData);
    return template;
  }

  /**
   * Generate module index template
   * @param {Object} moduleData - Module data
   * @returns {string} Module index template
   * @private
   */
  generateModuleIndexTemplate(moduleData) {
    const today = new Date().toISOString().split('T')[0];
    const moduleName = moduleData.name;
    const specs = moduleData.specs || [];
    const subcategories = moduleData.subcategories || null;

    let content = `# ${moduleName.charAt(0).toUpperCase() + moduleName.slice(1)} Module

> Last Updated: ${today}
> Module: ${moduleName}
> Spec Count: ${specs.length}

## Description

${moduleData.description || `Specifications for ${moduleName} functionality and features.`}

## Module Specifications

`;

    if (subcategories) {
      // Organize by subcategories
      for (const [subcategoryName, subcategorySpecs] of Object.entries(subcategories)) {
        content += `### ${subcategoryName.charAt(0).toUpperCase() + subcategoryName.slice(1)}\n\n`;
        
        for (const specName of subcategorySpecs) {
          content += `- **[${specName}](../../specs/modules/${moduleName}/${specName}/spec.md)** - ${this.generateSpecDescription(specName)}\n`;
        }
        content += '\n';
      }
    } else {
      // Simple list
      for (const specName of specs) {
        content += `- **[${specName}](../../specs/modules/${moduleName}/${specName}/spec.md)** - ${this.generateSpecDescription(specName)}\n`;
      }
    }

    content += `
## Module Structure

\`\`\`
${moduleName}/
├── specs/modules/${moduleName}/     # Specification documents
├── src/modules/${moduleName}/       # Implementation code
├── tests/modules/${moduleName}/     # Test suites
└── docs/modules/${moduleName}/      # Documentation
\`\`\`

## Quick Links

- [Module Specifications](../../specs/modules/${moduleName}/)
- [Source Code](../../src/modules/${moduleName}/)
- [Test Suites](../../tests/modules/${moduleName}/)

`;

    // Add statistics if available
    if (moduleData.statistics) {
      content += `## Statistics

- **Total Specs:** ${moduleData.statistics.totalSpecs || specs.length}
- **Completed Specs:** ${moduleData.statistics.completedSpecs || 0}
- **In Progress:** ${moduleData.statistics.inProgressSpecs || 0}
- **Planned:** ${moduleData.statistics.plannedSpecs || 0}

`;
    }

    // Add cross-repository references if enabled
    if (moduleData.crossRepoReferences) {
      content += `## Cross-Repository Integration

This module integrates with the Agent OS enhanced workflow system:

- **Enhanced Workflow:** @github:assetutilities/src/modules/agent-os/enhanced-create-specs/
- **Shared Templates:** @github:assetutilities/src/modules/agent-os/enhanced-create-specs/templates/
- **Module Standards:** @github:assetutilities/docs/modules/agent-os/module-standards.md

`;
    }

    content += `---

*This index is automatically generated and maintained by the Agent OS enhanced create-specs workflow.*`;

    return content;
  }

  /**
   * Generate repository index template
   * @param {Object} repositoryData - Repository data
   * @returns {string} Repository index template
   * @private
   */
  generateRepositoryIndexTemplate(repositoryData) {
    const today = new Date().toISOString().split('T')[0];
    const modules = repositoryData.modules || {};
    const stats = repositoryData.statistics || {};

    let content = `# Module Index

> Last Updated: ${today}
> Total Modules: ${stats.totalModules || 0}
> Total Specifications: ${stats.totalSpecs || 0}

## Repository Organization

This repository follows a module-based organization structure for better maintainability and navigation.

## Available Modules

`;

    for (const [moduleName, specs] of Object.entries(modules)) {
      content += `### [${moduleName}](${moduleName}/README.md)

**Specifications:** ${specs.length}
**Latest Specs:** ${specs.slice(-3).join(', ')}

`;
    }

    content += `## Module Statistics

| Module | Spec Count | Status |
|--------|------------|--------|
`;

    for (const [moduleName, specs] of Object.entries(modules)) {
      const status = specs.length > 5 ? 'Active' : 'Developing';
      content += `| [${moduleName}](${moduleName}/README.md) | ${specs.length} | ${status} |\n`;
    }

    content += `
## Structure Overview

\`\`\`
docs/modules/
├── authentication/     # Authentication and security
├── e-commerce/        # E-commerce functionality  
├── payment/           # Payment processing
├── api/              # API and integration
├── ui-ux/            # User interface
└── product/          # General product features
\`\`\`

## Getting Started

1. Browse modules by functionality area
2. Review individual spec documents for detailed requirements
3. Follow the enhanced create-specs workflow for new specifications
4. Maintain module organization standards

## Cross-Repository Integration

This repository integrates with:

- **[AssetUtilities](https://github.com/vamseeachanta/assetutilities)** - Enhanced workflow system
- **Agent OS Framework** - Specification and task management
- **Shared Templates** - Cross-repository templates and standards

---

*Generated by Agent OS Enhanced Create-Specs Workflow*`;

    return content;
  }

  /**
   * Generate spec description from spec name
   * @param {string} specName - Spec name
   * @returns {string} Generated description
   * @private
   */
  generateSpecDescription(specName) {
    const cleanName = specName.replace(/-/g, ' ').replace(/system$/, '').trim();
    return `${cleanName.charAt(0).toUpperCase() + cleanName.slice(1)} functionality and implementation`;
  }

  /**
   * Update existing index with new spec
   * @param {string} moduleName - Module name
   * @param {string} specName - New spec name
   * @returns {Object} Update results
   */
  async addSpecToIndex(moduleName, specName) {
    const indexPath = `docs/modules/${moduleName}/README.md`;
    
    try {
      // Try to read existing index
      let existingContent = '';
      try {
        existingContent = await fs.readFile(indexPath, 'utf8');
      } catch (error) {
        // Index doesn't exist, will create new one
      }

      // Parse existing specs from content
      const existingSpecs = this.parseSpecsFromIndex(existingContent);
      
      // Add new spec if not already present
      if (!existingSpecs.includes(specName)) {
        existingSpecs.push(specName);
        
        // Regenerate index with updated spec list
        const moduleData = {
          name: moduleName,
          specs: existingSpecs,
          description: this.extractDescriptionFromIndex(existingContent) || `${moduleName} module specifications`
        };
        
        return await this.updateModuleIndex(moduleData);
      }

      return {
        updated: false,
        reason: 'Spec already exists in index'
      };

    } catch (error) {
      throw new Error(`Failed to add spec to index: ${error.message}`);
    }
  }

  /**
   * Parse specs from existing index content
   * @param {string} content - Index content
   * @returns {Array} List of spec names
   * @private
   */
  parseSpecsFromIndex(content) {
    const specs = [];
    const specRegex = /\*\*\[([^\]]+)\]/g;
    let match;

    while ((match = specRegex.exec(content)) !== null) {
      specs.push(match[1]);
    }

    return specs;
  }

  /**
   * Extract description from existing index
   * @param {string} content - Index content
   * @returns {string|null} Extracted description
   * @private
   */
  extractDescriptionFromIndex(content) {
    const descriptionMatch = content.match(/## Description\s*\n\n([^\n]+)/);
    return descriptionMatch ? descriptionMatch[1] : null;
  }
}

module.exports = {
  ModuleOrganizer,
  FolderStructureGenerator,
  SubcategoryManager,
  ModuleIndexManager
};