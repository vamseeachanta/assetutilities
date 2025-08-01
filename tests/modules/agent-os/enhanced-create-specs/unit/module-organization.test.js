/**
 * Unit Tests for Module-Based Repository Organization
 * 
 * Tests the module organization system including:
 * - Module identification algorithm
 * - Automatic folder structure generation
 * - Subcategory handling for modules with >5 specs
 * - Module index management
 */

const { describe, it, expect, beforeEach, afterEach, jest } = require('@jest/globals');
const fs = require('fs').promises;
const path = require('path');

// Mock dependencies
jest.mock('fs', () => ({
  promises: {
    mkdir: jest.fn(),
    writeFile: jest.fn(),
    readFile: jest.fn(),
    access: jest.fn(),
    stat: jest.fn(),
    readdir: jest.fn()
  }
}));

// Import the modules we'll be testing
const {
  ModuleOrganizer,
  FolderStructureGenerator,
  SubcategoryManager,
  ModuleIndexManager
} = require('../../../../../src/modules/agent-os/enhanced-create-specs/module-organization');

describe('Module-Based Repository Organization', () => {
  let mockFs;
  
  beforeEach(() => {
    mockFs = require('fs').promises;
    jest.clearAllMocks();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('ModuleOrganizer', () => {
    let moduleOrganizer;

    beforeEach(() => {
      moduleOrganizer = new ModuleOrganizer();
    });

    it('should organize specs into correct module structure', async () => {
      const specs = [
        { name: 'user-auth', module: 'authentication' },
        { name: 'payment-gateway', module: 'payment' },
        { name: 'product-catalog', module: 'e-commerce' }
      ];

      const result = await moduleOrganizer.organizeSpecs(specs);

      expect(result.modules).toHaveProperty('authentication');
      expect(result.modules).toHaveProperty('payment');
      expect(result.modules).toHaveProperty('e-commerce');
      expect(result.modules.authentication).toContain('user-auth');
      expect(result.modules.payment).toContain('payment-gateway');
      expect(result.modules['e-commerce']).toContain('product-catalog');
    });

    it('should handle default module assignment for unclassified specs', async () => {
      const specs = [
        { name: 'generic-feature', module: undefined },
        { name: 'unknown-spec', module: null }
      ];

      const result = await moduleOrganizer.organizeSpecs(specs);

      expect(result.modules).toHaveProperty('product');
      expect(result.modules.product).toContain('generic-feature');
      expect(result.modules.product).toContain('unknown-spec');
    });

    it('should track module statistics', async () => {
      const specs = [
        { name: 'spec1', module: 'authentication' },
        { name: 'spec2', module: 'authentication' },
        { name: 'spec3', module: 'payment' }
      ];

      const result = await moduleOrganizer.organizeSpecs(specs);

      expect(result.statistics.totalModules).toBe(2);
      expect(result.statistics.totalSpecs).toBe(3);
      expect(result.statistics.moduleDistribution.authentication).toBe(2);
      expect(result.statistics.moduleDistribution.payment).toBe(1);
    });

    it('should identify modules requiring subcategories', async () => {
      const specs = Array.from({ length: 8 }, (_, i) => ({
        name: `auth-spec-${i + 1}`,
        module: 'authentication'
      }));

      const result = await moduleOrganizer.organizeSpecs(specs);

      expect(result.subcategoriesNeeded).toContain('authentication');
      expect(result.modules.authentication.length).toBe(8);
    });
  });

  describe('FolderStructureGenerator', () => {
    let folderGenerator;

    beforeEach(() => {
      folderGenerator = new FolderStructureGenerator();
      mockFs.mkdir.mockResolvedValue();
      mockFs.access.mockRejectedValue(new Error('Path does not exist'));
    });

    it('should create complete module folder structure', async () => {
      const moduleName = 'authentication';
      const specName = 'user-auth-system';

      await folderGenerator.createModuleStructure(moduleName, specName);

      expect(mockFs.mkdir).toHaveBeenCalledWith(
        `specs/modules/${moduleName}/${specName}`,
        { recursive: true }
      );
      expect(mockFs.mkdir).toHaveBeenCalledWith(
        `specs/modules/${moduleName}/${specName}/sub-specs`,
        { recursive: true }
      );
      expect(mockFs.mkdir).toHaveBeenCalledWith(
        `docs/modules/${moduleName}`,
        { recursive: true }
      );
      expect(mockFs.mkdir).toHaveBeenCalledWith(
        `src/modules/${moduleName}`,
        { recursive: true }
      );
      expect(mockFs.mkdir).toHaveBeenCalledWith(
        `tests/modules/${moduleName}/${specName}`,
        { recursive: true }
      );
    });

    it('should create test subdirectories', async () => {
      const moduleName = 'payment';
      const specName = 'payment-gateway';

      await folderGenerator.createModuleStructure(moduleName, specName);

      expect(mockFs.mkdir).toHaveBeenCalledWith(
        `tests/modules/${moduleName}/${specName}/unit`,
        { recursive: true }
      );
      expect(mockFs.mkdir).toHaveBeenCalledWith(
        `tests/modules/${moduleName}/${specName}/integration`,
        { recursive: true }
      );
      expect(mockFs.mkdir).toHaveBeenCalledWith(
        `tests/modules/${moduleName}/${specName}/e2e`,
        { recursive: true }
      );
    });

    it('should skip creation if directories already exist', async () => {
      mockFs.access.mockResolvedValue(); // Directory exists

      const moduleName = 'authentication';
      const specName = 'existing-spec';

      const result = await folderGenerator.createModuleStructure(moduleName, specName);

      expect(result.created).toBe(false);
      expect(result.reason).toContain('already exists');
    });

    it('should handle permission errors gracefully', async () => {
      mockFs.mkdir.mockRejectedValue(new Error('Permission denied'));

      const moduleName = 'authentication';
      const specName = 'test-spec';

      await expect(
        folderGenerator.createModuleStructure(moduleName, specName)
      ).rejects.toThrow('Permission denied');
    });

    it('should generate folder structure report', async () => {
      const moduleName = 'e-commerce';
      const specName = 'product-catalog';

      const result = await folderGenerator.createModuleStructure(moduleName, specName);

      expect(result).toHaveProperty('created', true);
      expect(result).toHaveProperty('directories');
      expect(result.directories).toBeInstanceOf(Array);
      expect(result.directories.length).toBeGreaterThan(5);
    });
  });

  describe('SubcategoryManager', () => {
    let subcategoryManager;

    beforeEach(() => {
      subcategoryManager = new SubcategoryManager();
      mockFs.readdir.mockResolvedValue([]);
    });

    it('should identify when subcategories are needed', async () => {
      const specs = Array.from({ length: 8 }, (_, i) => `spec-${i + 1}`);
      
      const needsSubcategories = await subcategoryManager.needsSubcategories('authentication', specs);
      
      expect(needsSubcategories).toBe(true);
    });

    it('should not require subcategories for small modules', async () => {
      const specs = ['spec-1', 'spec-2', 'spec-3'];
      
      const needsSubcategories = await subcategoryManager.needsSubcategories('payment', specs);
      
      expect(needsSubcategories).toBe(false);
    });

    it('should generate appropriate subcategories for authentication module', async () => {
      const specs = [
        'user-registration',
        'user-login',
        'password-reset',
        'jwt-tokens',
        'oauth-integration',
        'session-management',
        'security-audit',
        'user-permissions'
      ];

      const subcategories = await subcategoryManager.generateSubcategories('authentication', specs);

      expect(subcategories).toHaveProperty('user-management');
      expect(subcategories).toHaveProperty('security');
      expect(subcategories).toHaveProperty('integration');
      expect(subcategories['user-management']).toContain('user-registration');
      expect(subcategories.security).toContain('security-audit');
    });

    it('should generate subcategories for e-commerce module', async () => {
      const specs = [
        'product-catalog',
        'shopping-cart',
        'order-processing',
        'inventory-management',
        'payment-integration',
        'shipping-calculation',
        'customer-reviews',
        'recommendation-engine'
      ];

      const subcategories = await subcategoryManager.generateSubcategories('e-commerce', specs);

      expect(subcategories).toHaveProperty('catalog');
      expect(subcategories).toHaveProperty('orders');
      expect(subcategories).toHaveProperty('customer');
      expect(subcategories.catalog).toContain('product-catalog');
      expect(subcategories.orders).toContain('order-processing');
    });

    it('should create subcategory folder structure', async () => {
      mockFs.mkdir.mockResolvedValue();
      
      const subcategories = {
        'user-management': ['user-registration', 'user-login'],
        'security': ['password-reset', 'jwt-tokens']
      };

      await subcategoryManager.createSubcategoryStructure('authentication', subcategories);

      expect(mockFs.mkdir).toHaveBeenCalledWith(
        'specs/modules/authentication/user-management',
        { recursive: true }
      );
      expect(mockFs.mkdir).toHaveBeenCalledWith(
        'specs/modules/authentication/security',
        { recursive: true }
      );
    });

    it('should handle edge cases for subcategory generation', async () => {
      const specs = ['very-specific-unique-spec-name-that-doesnt-match-patterns'];

      const subcategories = await subcategoryManager.generateSubcategories('unknown-module', specs);

      expect(subcategories).toHaveProperty('misc');
      expect(subcategories.misc).toContain('very-specific-unique-spec-name-that-doesnt-match-patterns');
    });
  });

  describe('ModuleIndexManager', () => {
    let indexManager;

    beforeEach(() => {
      indexManager = new ModuleIndexManager();
      mockFs.readFile.mockResolvedValue('{}');
      mockFs.writeFile.mockResolvedValue();
    });

    it('should create module index with spec listings', async () => {
      const moduleData = {
        name: 'authentication',
        specs: ['user-auth-system', 'oauth-integration'],
        description: 'Authentication and security features'
      };

      await indexManager.updateModuleIndex(moduleData);

      expect(mockFs.writeFile).toHaveBeenCalledWith(
        'docs/modules/authentication/README.md',
        expect.stringContaining('# Authentication Module')
      );
    });

    it('should update existing module index', async () => {
      mockFs.readFile.mockResolvedValue(`# Authentication Module

## Existing Specs
- existing-spec`);

      const moduleData = {
        name: 'authentication',
        specs: ['existing-spec', 'new-spec'],
        description: 'Updated authentication features'
      };

      await indexManager.updateModuleIndex(moduleData);

      const writeCall = mockFs.writeFile.mock.calls[0];
      expect(writeCall[1]).toContain('new-spec');
      expect(writeCall[1]).toContain('existing-spec');
    });

    it('should generate cross-repository references', async () => {
      const moduleData = {
        name: 'authentication',
        specs: ['user-auth-system'],
        description: 'Authentication features',
        crossRepoReferences: true
      };

      await indexManager.updateModuleIndex(moduleData);

      const writeCall = mockFs.writeFile.mock.calls[0];
      expect(writeCall[1]).toContain('@github:assetutilities/');
    });

    it('should create global repository index', async () => {
      const repositoryData = {
        modules: {
          'authentication': ['user-auth', 'oauth'],
          'payment': ['payment-gateway'],
          'e-commerce': ['product-catalog', 'shopping-cart']
        },
        statistics: {
          totalModules: 3,
          totalSpecs: 5
        }
      };

      await indexManager.createRepositoryIndex(repositoryData);

      expect(mockFs.writeFile).toHaveBeenCalledWith(
        'docs/modules/README.md',
        expect.stringContaining('# Module Index')
      );
    });

    it('should handle subcategory organization in index', async () => {
      const moduleData = {
        name: 'authentication',
        specs: ['user-auth', 'oauth', 'security-audit'],
        subcategories: {
          'user-management': ['user-auth'],
          'integration': ['oauth'],
          'security': ['security-audit']
        },
        description: 'Authentication with subcategories'
      };

      await indexManager.updateModuleIndex(moduleData);

      const writeCall = mockFs.writeFile.mock.calls[0];
      expect(writeCall[1]).toContain('## User Management');
      expect(writeCall[1]).toContain('## Integration');
      expect(writeCall[1]).toContain('## Security');
    });

    it('should generate usage statistics in index', async () => {
      const moduleData = {
        name: 'authentication',
        specs: ['spec1', 'spec2', 'spec3'],
        statistics: {
          totalSpecs: 3,
          completedSpecs: 2,
          inProgressSpecs: 1
        },
        description: 'Authentication module'
      };

      await indexManager.updateModuleIndex(moduleData);

      const writeCall = mockFs.writeFile.mock.calls[0];
      expect(writeCall[1]).toContain('Statistics');
      expect(writeCall[1]).toContain('3');
      expect(writeCall[1]).toContain('2');
      expect(writeCall[1]).toContain('1');
    });

    it('should handle index creation errors', async () => {
      mockFs.writeFile.mockRejectedValue(new Error('Write permission denied'));

      const moduleData = {
        name: 'authentication',
        specs: ['user-auth'],
        description: 'Test module'
      };

      await expect(
        indexManager.updateModuleIndex(moduleData)
      ).rejects.toThrow('Write permission denied');
    });
  });

  describe('Integration Tests', () => {
    it('should complete full module organization workflow', async () => {
      const moduleOrganizer = new ModuleOrganizer();
      const folderGenerator = new FolderStructureGenerator();
      const indexManager = new ModuleIndexManager();

      mockFs.mkdir.mockResolvedValue();
      mockFs.writeFile.mockResolvedValue();
      mockFs.readFile.mockResolvedValue('{}');
      mockFs.access.mockRejectedValue(new Error('Not found'));

      const specs = [
        { name: 'user-auth', module: 'authentication' },
        { name: 'payment-processing', module: 'payment' }
      ];

      // Step 1: Organize specs
      const organized = await moduleOrganizer.organizeSpecs(specs);
      
      // Step 2: Create folder structures
      for (const [moduleName, specNames] of Object.entries(organized.modules)) {
        for (const specName of specNames) {
          await folderGenerator.createModuleStructure(moduleName, specName);
        }
      }

      // Step 3: Update indexes
      for (const [moduleName, specNames] of Object.entries(organized.modules)) {
        await indexManager.updateModuleIndex({
          name: moduleName,
          specs: specNames,
          description: `${moduleName} module specifications`
        });
      }

      expect(mockFs.mkdir).toHaveBeenCalledTimes(14); // 7 directories * 2 specs
      expect(mockFs.writeFile).toHaveBeenCalledTimes(2); // 2 module indexes
    });
  });
});