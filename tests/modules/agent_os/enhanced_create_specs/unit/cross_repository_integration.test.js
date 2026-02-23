/**
 * Unit Tests for Cross-Repository Integration System
 * 
 * Tests the cross-repository sub-agent system including:
 * - Cross-repository referencing and resolution
 * - Git submodule integration for AssetUtilities hub
 * - Version compatibility checking
 * - Caching system for cross-repository components
 * - Offline fallback mechanisms
 * - Reference validation and security
 */

const { describe, it, expect, beforeEach, afterEach, jest } = require('@jest/globals');
const fs = require('fs').promises;
const path = require('path');
const { execSync, spawn } = require('child_process');

// Mock dependencies
jest.mock('fs', () => ({
  promises: {
    readFile: jest.fn(),
    writeFile: jest.fn(),
    access: jest.fn(),
    stat: jest.fn(),
    mkdir: jest.fn(),
    readdir: jest.fn()
  }
}));

jest.mock('child_process');

// Import the modules we'll be testing
const {
  CrossRepositoryManager,
  GitSubmoduleIntegration,
  ReferenceResolver,
  VersionCompatibilityChecker,
  ComponentCacheManager,
  OfflineFallbackManager
} = require('../../../../../src/modules/agent-os/enhanced-create-specs/cross-repository-integration');

describe('Cross-Repository Integration System', () => {
  let mockFs;
  let mockExecSync;
  let mockSpawn;

  beforeEach(() => {
    mockFs = require('fs').promises;
    mockExecSync = require('child_process').execSync;
    mockSpawn = require('child_process').spawn;
    
    jest.clearAllMocks();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('CrossRepositoryManager', () => {
    let crossRepoManager;

    beforeEach(() => {
      crossRepoManager = new CrossRepositoryManager();
    });

    it('should initialize with default configuration', () => {
      expect(crossRepoManager.hubRepository).toBe('assetutilities');
      expect(crossRepoManager.defaultBranch).toBe('main');
      expect(crossRepoManager.cacheEnabled).toBe(true);
    });

    it('should parse cross-repository reference correctly', () => {
      const reference = '@github:assetutilities/src/modules/agent-os/enhanced-create-specs/workflow.md';
      
      const parsed = crossRepoManager.parseReference(reference);
      
      expect(parsed.type).toBe('github');
      expect(parsed.repository).toBe('assetutilities');
      expect(parsed.path).toBe('src/modules/agent-os/enhanced-create-specs/workflow.md');
      expect(parsed.branch).toBe('main');
      expect(parsed.valid).toBe(true);
    });

    it('should parse reference with specific branch', () => {
      const reference = '@github:assetutilities@develop/src/modules/agent-os/workflow.md';
      
      const parsed = crossRepoManager.parseReference(reference);
      
      expect(parsed.repository).toBe('assetutilities');
      expect(parsed.branch).toBe('develop');
      expect(parsed.path).toBe('src/modules/agent-os/workflow.md');
    });

    it('should validate reference format', () => {
      const validReference = '@github:assetutilities/src/workflow.md';
      const invalidReference = 'invalid-reference';
      
      expect(crossRepoManager.validateReference(validReference)).toBe(true);
      expect(crossRepoManager.validateReference(invalidReference)).toBe(false);
    });

    it('should handle malformed references gracefully', () => {
      const malformedReferences = [
        '@github:',
        '@github:repo/',
        '@github:repo/../../dangerous-path',
        '@github:repo/path?query=malicious'
      ];

      malformedReferences.forEach(ref => {
        const parsed = crossRepoManager.parseReference(ref);
        expect(parsed.valid).toBe(false);
      });
    });

    it('should resolve reference to local path', async () => {
      mockFs.access.mockResolvedValue(); // File exists
      
      const reference = '@github:assetutilities/src/modules/agent-os/workflow.md';
      
      const resolved = await crossRepoManager.resolveReference(reference);
      
      expect(resolved.success).toBe(true);
      expect(resolved.localPath).toContain('assetutilities');
      expect(resolved.localPath).toContain('workflow.md');
    });

    it('should handle reference resolution failures', async () => {
      mockFs.access.mockRejectedValue(new Error('File not found'));
      
      const reference = '@github:assetutilities/non-existent-file.md';
      
      const resolved = await crossRepoManager.resolveReference(reference);
      
      expect(resolved.success).toBe(false);
      expect(resolved.error).toContain('File not found');
    });
  });

  describe('GitSubmoduleIntegration', () => {
    let gitIntegration;

    beforeEach(() => {
      gitIntegration = new GitSubmoduleIntegration();
      mockExecSync.mockReturnValue('');
    });

    it('should check if submodule exists', async () => {
      mockExecSync.mockReturnValue('assetutilities src/external/assetutilities (heads/main)');
      
      const exists = await gitIntegration.checkSubmoduleExists('assetutilities');
      
      expect(exists).toBe(true);
      expect(mockExecSync).toHaveBeenCalledWith('git submodule status', expect.any(Object));
    });

    it('should add new git submodule', async () => {
      mockExecSync.mockReturnValue('Submodule added successfully');
      
      const result = await gitIntegration.addSubmodule({
        repository: 'https://github.com/user/assetutilities.git',
        path: 'src/external/assetutilities',
        branch: 'main'
      });
      
      expect(result.success).toBe(true);
      expect(mockExecSync).toHaveBeenCalledWith(
        'git submodule add -b main https://github.com/user/assetutilities.git src/external/assetutilities',
        expect.any(Object)
      );
    });

    it('should update existing submodule', async () => {
      mockExecSync.mockReturnValue('Submodule updated');
      
      const result = await gitIntegration.updateSubmodule('assetutilities');
      
      expect(result.success).toBe(true);
      expect(mockExecSync).toHaveBeenCalledWith(
        'git submodule update --remote assetutilities',
        expect.any(Object)
      );
    });

    it('should handle submodule initialization', async () => {
      mockExecSync.mockReturnValue('Submodules initialized');
      
      const result = await gitIntegration.initializeSubmodules();
      
      expect(result.success).toBe(true);
      expect(mockExecSync).toHaveBeenCalledWith('git submodule init', expect.any(Object));
      expect(mockExecSync).toHaveBeenCalledWith('git submodule update', expect.any(Object));
    });

    it('should handle git command failures', async () => {
      mockExecSync.mockImplementation(() => {
        throw new Error('Git command failed');
      });
      
      const result = await gitIntegration.addSubmodule({
        repository: 'invalid-repo',
        path: 'invalid-path'
      });
      
      expect(result.success).toBe(false);
      expect(result.error).toContain('Git command failed');
    });

    it('should get submodule status information', async () => {
      mockExecSync.mockReturnValue(`
 d85b1d5a8b9c assetutilities (heads/main)
-f7c2d3e9a1b4 shared-components (v1.2.3)
      `.trim());
      
      const status = await gitIntegration.getSubmoduleStatus();
      
      expect(status.submodules).toHaveLength(2);
      expect(status.submodules[0].name).toBe('assetutilities');
      expect(status.submodules[0].status).toBe('up-to-date');
      expect(status.submodules[1].name).toBe('shared-components');
      expect(status.submodules[1].status).toBe('not-initialized');
    });
  });

  describe('ReferenceResolver', () => {
    let referenceResolver;

    beforeEach(() => {
      referenceResolver = new ReferenceResolver();
      mockFs.readFile.mockResolvedValue('file content');
    });

    it('should resolve local file reference', async () => {
      const reference = '@github:assetutilities/src/workflow.md';
      
      const result = await referenceResolver.resolveReference(reference, {
        baseDirectory: '/project/src/external/assetutilities'
      });
      
      expect(result.success).toBe(true);
      expect(result.content).toBe('file content');
      expect(result.resolvedPath).toContain('workflow.md');
    });

    it('should resolve reference with content extraction', async () => {
      const yamlContent = `
workflow:
  name: enhanced-create-specs
  version: 1.0.0
  steps:
    - initialize
    - process
    - finalize
      `;
      
      mockFs.readFile.mockResolvedValue(yamlContent);
      
      const result = await referenceResolver.resolveReference(
        '@github:assetutilities/config/workflow.yml',
        { extractContent: true, format: 'yaml' }
      );
      
      expect(result.success).toBe(true);
      expect(result.parsedContent).toHaveProperty('workflow');
      expect(result.parsedContent.workflow.name).toBe('enhanced-create-specs');
    });

    it('should handle reference resolution with caching', async () => {
      const reference = '@github:assetutilities/src/cached-file.md';
      
      // First resolution
      await referenceResolver.resolveReference(reference, { useCache: true });
      
      // Second resolution should use cache
      await referenceResolver.resolveReference(reference, { useCache: true });
      
      // File should only be read once due to caching
      expect(mockFs.readFile).toHaveBeenCalledTimes(1);
    });

    it('should resolve nested references', async () => {
      const mainContent = 'Main content with @github:assetutilities/templates/nested.md';
      const nestedContent = 'Nested template content';
      
      mockFs.readFile
        .mockResolvedValueOnce(mainContent)
        .mockResolvedValueOnce(nestedContent);
      
      const result = await referenceResolver.resolveReference(
        '@github:assetutilities/main.md',
        { resolveNested: true }
      );
      
      expect(result.success).toBe(true);
      expect(result.resolvedContent).toContain('Nested template content');
      expect(mockFs.readFile).toHaveBeenCalledTimes(2);
    });

    it('should handle circular reference detection', async () => {
      const circularContent1 = 'Content with @github:assetutilities/file2.md';
      const circularContent2 = 'Content with @github:assetutilities/file1.md';
      
      mockFs.readFile
        .mockImplementation((path) => {
          if (path.includes('file1.md')) return Promise.resolve(circularContent1);
          if (path.includes('file2.md')) return Promise.resolve(circularContent2);
          return Promise.reject(new Error('File not found'));
        });
      
      const result = await referenceResolver.resolveReference(
        '@github:assetutilities/file1.md',
        { resolveNested: true, maxDepth: 5 }
      );
      
      expect(result.success).toBe(false);
      expect(result.error).toContain('Circular reference detected');
    });
  });

  describe('VersionCompatibilityChecker', () => {
    let versionChecker;

    beforeEach(() => {
      versionChecker = new VersionCompatibilityChecker();
    });

    it('should check version compatibility correctly', () => {
      const compatibilityRules = {
        'enhanced-create-specs': {
          minVersion: '1.0.0',
          maxVersion: '2.0.0',
          compatible: ['1.0.0', '1.5.0', '1.9.9']
        }
      };

      expect(versionChecker.isCompatible('enhanced-create-specs', '1.5.0', compatibilityRules)).toBe(true);
      expect(versionChecker.isCompatible('enhanced-create-specs', '0.9.0', compatibilityRules)).toBe(false);
      expect(versionChecker.isCompatible('enhanced-create-specs', '2.1.0', compatibilityRules)).toBe(false);
    });

    it('should parse semantic versions correctly', () => {
      const version = '1.2.3-beta.1+build.123';
      const parsed = versionChecker.parseVersion(version);
      
      expect(parsed.major).toBe(1);
      expect(parsed.minor).toBe(2);
      expect(parsed.patch).toBe(3);
      expect(parsed.prerelease).toBe('beta.1');
      expect(parsed.build).toBe('build.123');
    });

    it('should compare versions correctly', () => {
      expect(versionChecker.compareVersions('1.0.0', '1.0.1')).toBe(-1);
      expect(versionChecker.compareVersions('1.5.0', '1.0.0')).toBe(1);
      expect(versionChecker.compareVersions('2.0.0', '2.0.0')).toBe(0);
      expect(versionChecker.compareVersions('2.0.0-alpha', '2.0.0')).toBe(-1);
    });

    it('should check breaking changes', async () => {
      mockFs.readFile.mockResolvedValue(`
# Changelog
## [2.0.0] - 2025-08-01
### Breaking Changes
- Changed API structure
- Removed deprecated methods

## [1.5.0] - 2025-07-01
### Added
- New features
      `);

      const breakingChanges = await versionChecker.checkBreakingChanges('1.0.0', '2.0.0');
      
      expect(breakingChanges.hasBreakingChanges).toBe(true);
      expect(breakingChanges.changes).toContain('Changed API structure');
      expect(breakingChanges.changes).toContain('Removed deprecated methods');
    });

    it('should get version from package file', async () => {
      const packageJson = {
        name: 'enhanced-create-specs',
        version: '1.2.3',
        dependencies: {
          'cross-repo-helper': '^2.0.0'
        }
      };
      
      mockFs.readFile.mockResolvedValue(JSON.stringify(packageJson));
      
      const version = await versionChecker.getVersionFromPackage('/path/package.json');
      
      expect(version).toBe('1.2.3');
    });
  });

  describe('ComponentCacheManager', () => {
    let cacheManager;

    beforeEach(() => {
      cacheManager = new ComponentCacheManager({ 
        cacheDir: '/tmp/cross-repo-cache',
        maxSize: 100,
        ttl: 3600000 // 1 hour
      });
      
      mockFs.readFile.mockResolvedValue('cached content');
      mockFs.writeFile.mockResolvedValue();
      mockFs.mkdir.mockResolvedValue();
      mockFs.stat.mockResolvedValue({ 
        mtime: new Date(),
        size: 1024
      });
    });

    it('should cache component successfully', async () => {
      const component = {
        reference: '@github:assetutilities/workflow.md',
        content: 'workflow content',
        version: '1.0.0'
      };
      
      const result = await cacheManager.cacheComponent(component);
      
      expect(result.cached).toBe(true);
      expect(result.cacheKey).toBeDefined();
      expect(mockFs.writeFile).toHaveBeenCalled();
    });

    it('should retrieve cached component', async () => {
      const cacheKey = 'assetutilities_workflow_md_1_0_0';
      
      const result = await cacheManager.getCachedComponent(cacheKey);
      
      expect(result.found).toBe(true);
      expect(result.content).toBe('cached content');
      expect(mockFs.readFile).toHaveBeenCalled();
    });

    it('should handle cache expiration', async () => {
      const expiredTime = new Date(Date.now() - 7200000); // 2 hours ago
      mockFs.stat.mockResolvedValue({ 
        mtime: expiredTime,
        size: 1024
      });
      
      const result = await cacheManager.getCachedComponent('expired_key');
      
      expect(result.found).toBe(false);
      expect(result.expired).toBe(true);
    });

    it('should clear cache when size limit exceeded', async () => {
      mockFs.readdir.mockResolvedValue(['file1', 'file2', 'file3']);
      mockFs.stat.mockResolvedValue({ size: 50 }); // Total 150 > 100 limit
      
      await cacheManager.clearCacheIfNeeded();
      
      expect(mockFs.readdir).toHaveBeenCalled();
    });

    it('should generate consistent cache keys', () => {
      const reference1 = '@github:assetutilities/workflow.md';
      const reference2 = '@github:assetutilities/workflow.md';
      
      const key1 = cacheManager.generateCacheKey(reference1, '1.0.0');
      const key2 = cacheManager.generateCacheKey(reference2, '1.0.0');
      
      expect(key1).toBe(key2);
      expect(key1).toMatch(/^[a-f0-9]+$/); // Should be hex string
    });
  });

  describe('OfflineFallbackManager', () => {
    let fallbackManager;

    beforeEach(() => {
      fallbackManager = new OfflineFallbackManager({
        fallbackDir: '/fallback/cache',
        enableNetworkCheck: true
      });
    });

    it('should detect offline mode', async () => {
      mockExecSync.mockImplementation(() => {
        throw new Error('Network unreachable');
      });
      
      const isOffline = await fallbackManager.checkOfflineMode();
      
      expect(isOffline).toBe(true);
    });

    it('should use cached fallback when offline', async () => {
      mockFs.readFile.mockResolvedValue('fallback content');
      
      const result = await fallbackManager.getFallbackContent(
        '@github:assetutilities/workflow.md'
      );
      
      expect(result.success).toBe(true);
      expect(result.content).toBe('fallback content');
      expect(result.source).toBe('fallback');
    });

    it('should create fallback cache entry', async () => {
      mockFs.writeFile.mockResolvedValue();
      mockFs.mkdir.mockResolvedValue();
      
      await fallbackManager.createFallbackEntry(
        '@github:assetutilities/workflow.md',
        'content to cache',
        { version: '1.0.0' }
      );
      
      expect(mockFs.mkdir).toHaveBeenCalled();
      expect(mockFs.writeFile).toHaveBeenCalled();
    });

    it('should handle fallback with default templates', async () => {
      mockFs.readFile.mockRejectedValue(new Error('File not found'));
      
      const result = await fallbackManager.getFallbackContent(
        '@github:assetutilities/unknown-template.md',
        { useDefaultTemplate: true }
      );
      
      expect(result.success).toBe(true);
      expect(result.content).toContain('# Default Template');
      expect(result.source).toBe('default-template');
    });

    it('should sync fallback cache when online', async () => {
      mockExecSync.mockReturnValue(''); // Network available
      mockFs.readdir.mockResolvedValue(['cached-file1.json', 'cached-file2.json']);
      
      const result = await fallbackManager.syncFallbackCache();
      
      expect(result.synced).toBe(true);
      expect(result.filesProcessed).toBe(2);
    });
  });

  describe('Integration Tests', () => {
    it('should complete full cross-repository workflow', async () => {
      const crossRepoManager = new CrossRepositoryManager();
      const gitIntegration = new GitSubmoduleIntegration();
      const referenceResolver = new ReferenceResolver();
      
      // Mock successful operations
      mockExecSync.mockReturnValue('submodule added');
      mockFs.readFile.mockResolvedValue('resolved content');
      mockFs.access.mockResolvedValue();
      
      // Step 1: Add submodule
      const submoduleResult = await gitIntegration.addSubmodule({
        repository: 'https://github.com/user/assetutilities.git',
        path: 'src/external/assetutilities'
      });
      
      expect(submoduleResult.success).toBe(true);
      
      // Step 2: Resolve reference
      const resolveResult = await referenceResolver.resolveReference(
        '@github:assetutilities/src/workflow.md'
      );
      
      expect(resolveResult.success).toBe(true);
      expect(resolveResult.content).toBe('resolved content');
      
      // Step 3: Validate reference
      const isValid = crossRepoManager.validateReference('@github:assetutilities/src/workflow.md');
      expect(isValid).toBe(true);
    });

    it('should handle complete offline workflow', async () => {
      const fallbackManager = new OfflineFallbackManager();
      const cacheManager = new ComponentCacheManager();
      
      // Simulate offline mode
      mockExecSync.mockImplementation(() => {
        throw new Error('Network unreachable');
      });
      
      mockFs.readFile.mockResolvedValue('cached fallback content');
      
      // Check offline mode
      const isOffline = await fallbackManager.checkOfflineMode();
      expect(isOffline).toBe(true);
      
      // Get fallback content
      const fallbackResult = await fallbackManager.getFallbackContent(
        '@github:assetutilities/workflow.md'
      );
      
      expect(fallbackResult.success).toBe(true);
      expect(fallbackResult.content).toBe('cached fallback content');
    });
  });
});