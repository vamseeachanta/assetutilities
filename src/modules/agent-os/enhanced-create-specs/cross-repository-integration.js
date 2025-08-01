/**
 * Cross-Repository Integration System for Enhanced Create-Specs
 * 
 * Provides comprehensive cross-repository capabilities including:
 * - Cross-repository reference parsing and resolution
 * - Git submodule integration for AssetUtilities hub
 * - Version compatibility checking and validation
 * - Component caching for improved performance
 * - Offline fallback mechanisms
 * - Security validation for cross-repository operations
 */

const fs = require('fs').promises;
const path = require('path');
const crypto = require('crypto');
const { execSync, spawn } = require('child_process');
const yaml = require('js-yaml'); // For YAML parsing

/**
 * Main cross-repository manager
 */
class CrossRepositoryManager {
  constructor(options = {}) {
    this.hubRepository = options.hubRepository || 'assetutilities';
    this.defaultBranch = options.defaultBranch || 'main';
    this.baseUrl = options.baseUrl || 'https://github.com';
    this.cacheEnabled = options.cacheEnabled !== false;
    this.securityEnabled = options.securityEnabled !== false;
    
    // Allowed repositories for security
    this.allowedRepositories = options.allowedRepositories || [
      'assetutilities',
      'agent-os-core',
      'shared-templates'
    ];
  }

  /**
   * Parse cross-repository reference
   * @param {string} reference - Reference in format @github:repo/path or @github:repo@branch/path
   * @returns {Object} Parsed reference object
   */
  parseReference(reference) {
    const result = {
      original: reference,
      valid: false,
      type: null,
      repository: null,
      branch: this.defaultBranch,
      path: null,
      error: null
    };

    try {
      // Validate basic format
      if (!reference || typeof reference !== 'string' || !reference.startsWith('@')) {
        result.error = 'Invalid reference format';
        return result;
      }

      // Parse reference pattern: @type:repository[@branch]/path
      const referencePattern = /^@([^:]+):([^/@]+)(?:@([^/]+))?\/(.+)$/;
      const match = reference.match(referencePattern);

      if (!match) {
        result.error = 'Reference does not match expected pattern';
        return result;
      }

      const [, type, repository, branch, filePath] = match;

      // Validate components
      if (!type || !repository || !filePath) {
        result.error = 'Missing required reference components';
        return result;
      }

      // Security validation
      if (this.securityEnabled && !this.allowedRepositories.includes(repository)) {
        result.error = `Repository '${repository}' not in allowed list`;
        return result;
      }

      // Path traversal protection
      if (filePath.includes('..') || filePath.includes('~') || filePath.match(/[<>:"|?*]/)) {
        result.error = 'Path contains invalid characters';
        return result;
      }

      result.type = type;
      result.repository = repository;
      result.branch = branch || this.defaultBranch;
      result.path = filePath;
      result.valid = true;

    } catch (error) {
      result.error = error.message;
    }

    return result;
  }

  /**
   * Validate reference format and security
   * @param {string} reference - Reference to validate
   * @returns {boolean} Whether reference is valid
   */
  validateReference(reference) {
    const parsed = this.parseReference(reference);
    return parsed.valid;
  }

  /**
   * Resolve cross-repository reference to local path
   * @param {string} reference - Cross-repository reference
   * @param {Object} options - Resolution options
   * @returns {Object} Resolution result
   */
  async resolveReference(reference, options = {}) {
    const result = {
      success: false,
      reference: reference,
      localPath: null,
      error: null
    };

    try {
      const parsed = this.parseReference(reference);
      
      if (!parsed.valid) {
        result.error = parsed.error;
        return result;
      }

      // Determine local path based on submodule or cache
      const localPath = this._getLocalPath(parsed, options);
      
      // Check if file exists
      await fs.access(localPath);
      
      result.success = true;
      result.localPath = localPath;
      result.parsedReference = parsed;

    } catch (error) {
      result.error = error.message;
    }

    return result;
  }

  /**
   * Get local path for resolved reference
   * @param {Object} parsed - Parsed reference
   * @param {Object} options - Options
   * @returns {string} Local file path
   * @private
   */
  _getLocalPath(parsed, options) {
    const baseDir = options.baseDirectory || process.cwd();
    
    if (options.useSubmodule) {
      return path.join(baseDir, 'src', 'external', parsed.repository, parsed.path);
    } else {
      return path.join(baseDir, '.cross-repo-cache', parsed.repository, parsed.branch, parsed.path);
    }
  }

  /**
   * List all cross-repository references in a project
   * @param {string} projectPath - Path to search
   * @returns {Array} List of found references
   */
  async findAllReferences(projectPath) {
    const references = [];
    const referencePattern = /@[^:]+:[^/@]+(?:@[^/]+)?\/[^\s)]+/g;

    try {
      const files = await this._getAllFiles(projectPath, ['.md', '.yml', '.yaml', '.json']);
      
      for (const file of files) {
        const content = await fs.readFile(file, 'utf8');
        const matches = content.match(referencePattern) || [];
        
        for (const match of matches) {
          if (this.validateReference(match)) {
            references.push({
              reference: match,
              file: file,
              line: this._findLineNumber(content, match)
            });
          }
        }
      }
    } catch (error) {
      console.error('Error finding references:', error.message);
    }

    return references;
  }

  /**
   * Get all files with specific extensions
   * @param {string} dir - Directory to search
   * @param {Array} extensions - File extensions to include
   * @returns {Array} List of file paths
   * @private
   */
  async _getAllFiles(dir, extensions) {
    const files = [];
    
    try {
      const entries = await fs.readdir(dir, { withFileTypes: true });
      
      for (const entry of entries) {
        const fullPath = path.join(dir, entry.name);
        
        if (entry.isDirectory()) {
          if (!entry.name.startsWith('.') && entry.name !== 'node_modules') {
            files.push(...await this._getAllFiles(fullPath, extensions));
          }
        } else {
          const ext = path.extname(entry.name);
          if (extensions.includes(ext)) {
            files.push(fullPath);
          }
        }
      }
    } catch (error) {
      // Directory might not exist or be accessible
    }
    
    return files;
  }

  /**
   * Find line number of text in content
   * @param {string} content - File content
   * @param {string} text - Text to find
   * @returns {number} Line number (1-based)
   * @private
   */
  _findLineNumber(content, text) {
    const lines = content.split('\n');
    for (let i = 0; i < lines.length; i++) {
      if (lines[i].includes(text)) {
        return i + 1;
      }
    }
    return 0;
  }
}

/**
 * Git submodule integration manager
 */
class GitSubmoduleIntegration {
  constructor(options = {}) {
    this.gitCommand = options.gitCommand || 'git';
    this.workingDirectory = options.workingDirectory || process.cwd();
  }

  /**
   * Check if a submodule exists
   * @param {string} submoduleName - Name of the submodule
   * @returns {boolean} Whether submodule exists
   */
  async checkSubmoduleExists(submoduleName) {
    try {
      const output = execSync('git submodule status', {
        cwd: this.workingDirectory,
        encoding: 'utf8'
      });
      
      return output.includes(submoduleName);
    } catch (error) {
      return false;
    }
  }

  /**
   * Add git submodule
   * @param {Object} config - Submodule configuration
   * @returns {Object} Addition result
   */
  async addSubmodule(config) {
    const { repository, path: submodulePath, branch = 'main' } = config;
    const result = {
      success: false,
      message: null,
      error: null
    };

    try {
      const command = `git submodule add -b ${branch} ${repository} ${submodulePath}`;
      const output = execSync(command, {
        cwd: this.workingDirectory,
        encoding: 'utf8'
      });

      result.success = true;
      result.message = `Submodule added successfully: ${submodulePath}`;
      result.output = output;

    } catch (error) {
      result.error = error.message;
      result.message = `Failed to add submodule: ${error.message}`;
    }

    return result;
  }

  /**
   * Update existing submodule
   * @param {string} submoduleName - Name of submodule to update
   * @returns {Object} Update result
   */
  async updateSubmodule(submoduleName) {
    const result = {
      success: false,
      message: null,
      error: null
    };

    try {
      const command = `git submodule update --remote ${submoduleName}`;
      const output = execSync(command, {
        cwd: this.workingDirectory,
        encoding: 'utf8'
      });

      result.success = true;
      result.message = `Submodule updated successfully: ${submoduleName}`;
      result.output = output;

    } catch (error) {
      result.error = error.message;
      result.message = `Failed to update submodule: ${error.message}`;
    }

    return result;
  }

  /**
   * Initialize all submodules
   * @returns {Object} Initialization result
   */
  async initializeSubmodules() {
    const result = {
      success: false,
      message: null,
      error: null
    };

    try {
      // Initialize submodules
      execSync('git submodule init', {
        cwd: this.workingDirectory,
        encoding: 'utf8'
      });

      // Update submodules
      const output = execSync('git submodule update', {
        cwd: this.workingDirectory,
        encoding: 'utf8'
      });

      result.success = true;
      result.message = 'All submodules initialized successfully';
      result.output = output;

    } catch (error) {
      result.error = error.message;
      result.message = `Failed to initialize submodules: ${error.message}`;
    }

    return result;
  }

  /**
   * Get status of all submodules
   * @returns {Object} Submodule status information
   */
  async getSubmoduleStatus() {
    const result = {
      submodules: [],
      error: null
    };

    try {
      const output = execSync('git submodule status', {
        cwd: this.workingDirectory,
        encoding: 'utf8'
      });

      const lines = output.trim().split('\n').filter(line => line.trim());
      
      for (const line of lines) {
        const match = line.match(/^([-+ ]?)([a-f0-9]+) (.+?)(?: \((.+)\))?$/);
        if (match) {
          const [, statusChar, commit, name, branch] = match;
          
          let status = 'up-to-date';
          if (statusChar === '-') status = 'not-initialized';
          else if (statusChar === '+') status = 'different-commit';
          
          result.submodules.push({
            name: name.trim(),
            commit: commit,
            branch: branch || 'unknown',
            status: status
          });
        }
      }

    } catch (error) {
      result.error = error.message;
    }

    return result;
  }

  /**
   * Remove submodule
   * @param {string} submoduleName - Name of submodule to remove
   * @returns {Object} Removal result
   */
  async removeSubmodule(submoduleName) {
    const result = {
      success: false,
      message: null,
      error: null
    };

    try {
      // Remove from .gitmodules
      execSync(`git submodule deinit -f ${submoduleName}`, {
        cwd: this.workingDirectory
      });

      // Remove from .git/modules
      execSync(`rm -rf .git/modules/${submoduleName}`, {
        cwd: this.workingDirectory
      });

      // Remove from working tree
      execSync(`git rm -f ${submoduleName}`, {
        cwd: this.workingDirectory
      });

      result.success = true;
      result.message = `Submodule removed successfully: ${submoduleName}`;

    } catch (error) {
      result.error = error.message;
      result.message = `Failed to remove submodule: ${error.message}`;
    }

    return result;
  }
}

/**
 * Reference resolver with content extraction
 */
class ReferenceResolver {
  constructor(options = {}) {
    this.cache = new Map();
    this.maxCacheSize = options.maxCacheSize || 100;
    this.cacheEnabled = options.cacheEnabled !== false;
  }

  /**
   * Resolve reference and return content
   * @param {string} reference - Cross-repository reference
   * @param {Object} options - Resolution options
   * @returns {Object} Resolution result with content
   */
  async resolveReference(reference, options = {}) {
    const result = {
      success: false,
      reference: reference,
      content: null,
      parsedContent: null,
      resolvedPath: null,
      error: null
    };

    try {
      // Check cache first
      if (this.cacheEnabled && options.useCache) {
        const cached = this.cache.get(reference);
        if (cached && Date.now() - cached.timestamp < (options.cacheTtl || 300000)) {
          return { ...cached.result, fromCache: true };
        }
      }

      // Resolve path
      const crossRepoManager = new CrossRepositoryManager();
      const resolved = await crossRepoManager.resolveReference(reference, options);
      
      if (!resolved.success) {
        result.error = resolved.error;
        return result;
      }

      // Read content
      const content = await fs.readFile(resolved.localPath, 'utf8');
      
      result.success = true;
      result.content = content;
      result.resolvedPath = resolved.localPath;

      // Parse content if requested
      if (options.extractContent) {
        result.parsedContent = await this._parseContent(content, options.format);
      }

      // Resolve nested references if requested
      if (options.resolveNested) {
        result.resolvedContent = await this._resolveNestedReferences(
          content, 
          options,
          new Set([reference]) // Circular reference protection
        );
      }

      // Cache result
      if (this.cacheEnabled && options.useCache) {
        this._cacheResult(reference, result);
      }

    } catch (error) {
      result.error = error.message;
    }

    return result;
  }

  /**
   * Parse content based on format
   * @param {string} content - Raw content
   * @param {string} format - Content format (yaml, json, etc.)
   * @returns {Object} Parsed content
   * @private
   */
  async _parseContent(content, format) {
    try {
      switch (format?.toLowerCase()) {
        case 'yaml':
        case 'yml':
          return yaml.load(content);
        case 'json':
          return JSON.parse(content);
        default:
          return content;
      }
    } catch (error) {
      throw new Error(`Failed to parse content as ${format}: ${error.message}`);
    }
  }

  /**
   * Resolve nested references within content
   * @param {string} content - Content with potential references
   * @param {Object} options - Resolution options
   * @param {Set} visited - Visited references (circular protection)
   * @returns {string} Content with resolved references
   * @private
   */
  async _resolveNestedReferences(content, options, visited) {
    const referencePattern = /@[^:]+:[^/@]+(?:@[^/]+)?\/[^\s)]+/g;
    const references = content.match(referencePattern) || [];
    
    let resolvedContent = content;
    const maxDepth = options.maxDepth || 10;

    if (visited.size >= maxDepth) {
      throw new Error('Maximum nesting depth reached');
    }

    for (const ref of references) {
      if (visited.has(ref)) {
        throw new Error(`Circular reference detected: ${ref}`);
      }

      try {
        const nestedVisited = new Set(visited);
        nestedVisited.add(ref);

        const resolved = await this.resolveReference(ref, {
          ...options,
          resolveNested: false // Prevent infinite recursion
        });

        if (resolved.success) {
          resolvedContent = resolvedContent.replace(ref, resolved.content);
        }
      } catch (error) {
        console.warn(`Failed to resolve nested reference ${ref}: ${error.message}`);
      }
    }

    return resolvedContent;
  }

  /**
   * Cache resolution result
   * @param {string} reference - Reference key
   * @param {Object} result - Result to cache
   * @private
   */
  _cacheResult(reference, result) {
    // Implement LRU cache eviction
    if (this.cache.size >= this.maxCacheSize) {
      const firstKey = this.cache.keys().next().value;
      this.cache.delete(firstKey);
    }

    this.cache.set(reference, {
      result: { ...result },
      timestamp: Date.now()
    });
  }

  /**
   * Clear resolution cache
   */
  clearCache() {
    this.cache.clear();
  }
}

/**
 * Version compatibility checker
 */
class VersionCompatibilityChecker {
  constructor() {
    this.versionPattern = /^(\d+)\.(\d+)\.(\d+)(?:-([^+]+))?(?:\+(.+))?$/;
  }

  /**
   * Check if versions are compatible
   * @param {string} component - Component name
   * @param {string} version - Version to check
   * @param {Object} compatibilityRules - Compatibility rules
   * @returns {boolean} Whether versions are compatible
   */
  isCompatible(component, version, compatibilityRules) {
    const rules = compatibilityRules[component];
    if (!rules) return true; // No rules means compatible

    const versionNum = this.parseVersion(version);
    if (!versionNum.valid) return false;

    // Check minimum version
    if (rules.minVersion && this.compareVersions(version, rules.minVersion) < 0) {
      return false;
    }

    // Check maximum version
    if (rules.maxVersion && this.compareVersions(version, rules.maxVersion) > 0) {
      return false;
    }

    // Check explicit compatibility list
    if (rules.compatible && !rules.compatible.includes(version)) {
      return false;
    }

    // Check incompatible list
    if (rules.incompatible && rules.incompatible.includes(version)) {
      return false;
    }

    return true;
  }

  /**
   * Parse semantic version
   * @param {string} version - Version string
   * @returns {Object} Parsed version components
   */
  parseVersion(version) {
    const match = version.match(this.versionPattern);
    
    if (!match) {
      return { valid: false };
    }

    const [, major, minor, patch, prerelease, build] = match;
    
    return {
      valid: true,
      major: parseInt(major),
      minor: parseInt(minor),
      patch: parseInt(patch),
      prerelease: prerelease || null,
      build: build || null,
      original: version
    };
  }

  /**
   * Compare two versions
   * @param {string} version1 - First version
   * @param {string} version2 - Second version
   * @returns {number} -1 if v1 < v2, 0 if equal, 1 if v1 > v2
   */
  compareVersions(version1, version2) {
    const v1 = this.parseVersion(version1);
    const v2 = this.parseVersion(version2);

    if (!v1.valid || !v2.valid) {
      throw new Error('Invalid version format');
    }

    // Compare major.minor.patch
    const components = ['major', 'minor', 'patch'];
    for (const component of components) {
      if (v1[component] < v2[component]) return -1;
      if (v1[component] > v2[component]) return 1;
    }

    // Compare prerelease
    if (v1.prerelease && !v2.prerelease) return -1;
    if (!v1.prerelease && v2.prerelease) return 1;
    if (v1.prerelease && v2.prerelease) {
      if (v1.prerelease < v2.prerelease) return -1;
      if (v1.prerelease > v2.prerelease) return 1;
    }

    return 0;
  }

  /**
   * Check for breaking changes between versions
   * @param {string} fromVersion - Starting version
   * @param {string} toVersion - Target version
   * @param {string} changelogPath - Path to changelog file
   * @returns {Object} Breaking changes information
   */
  async checkBreakingChanges(fromVersion, toVersion, changelogPath) {
    const result = {
      hasBreakingChanges: false,
      changes: [],
      error: null
    };

    try {
      const changelog = await fs.readFile(changelogPath, 'utf8');
      const breakingPattern = /(?:breaking\s+change|breaking:|BREAKING)/gi;
      
      // Extract version sections
      const versionSections = this._extractVersionSections(changelog, fromVersion, toVersion);
      
      for (const section of versionSections) {
        if (breakingPattern.test(section)) {
          result.hasBreakingChanges = true;
          const changes = this._extractBreakingChanges(section);
          result.changes.push(...changes);
        }
      }

    } catch (error) {
      result.error = error.message;
    }

    return result;
  }

  /**
   * Extract version sections from changelog
   * @param {string} changelog - Changelog content
   * @param {string} fromVersion - Starting version
   * @param {string} toVersion - Ending version
   * @returns {Array} Version sections
   * @private
   */
  _extractVersionSections(changelog, fromVersion, toVersion) {
    const sections = [];
    const versionPattern = /## \[([^\]]+)\]/g;
    const lines = changelog.split('\n');
    
    let currentSection = '';
    let inTargetRange = false;
    
    for (const line of lines) {
      const versionMatch = line.match(versionPattern);
      
      if (versionMatch) {
        if (currentSection && inTargetRange) {
          sections.push(currentSection);
        }
        
        const version = versionMatch[1];
        inTargetRange = this.compareVersions(version, fromVersion) > 0 && 
                       this.compareVersions(version, toVersion) <= 0;
        
        currentSection = inTargetRange ? line + '\n' : '';
      } else if (inTargetRange) {
        currentSection += line + '\n';
      }
    }
    
    if (currentSection && inTargetRange) {
      sections.push(currentSection);
    }
    
    return sections;
  }

  /**
   * Extract breaking changes from section
   * @param {string} section - Changelog section
   * @returns {Array} Breaking changes
   * @private
   */
  _extractBreakingChanges(section) {
    const changes = [];
    const lines = section.split('\n');
    
    let inBreakingSection = false;
    for (const line of lines) {
      if (line.match(/breaking\s+change/i)) {
        inBreakingSection = true;
        continue;
      }
      
      if (inBreakingSection && line.trim().startsWith('-')) {
        changes.push(line.trim().substring(1).trim());
      }
      
      if (line.startsWith('###') && inBreakingSection) {
        inBreakingSection = false;
      }
    }
    
    return changes;
  }

  /**
   * Get version from package file
   * @param {string} packagePath - Path to package file
   * @returns {string} Version string
   */
  async getVersionFromPackage(packagePath) {
    try {
      const content = await fs.readFile(packagePath, 'utf8');
      const packageData = JSON.parse(content);
      return packageData.version;
    } catch (error) {
      throw new Error(`Failed to read version from ${packagePath}: ${error.message}`);
    }
  }
}

/**
 * Component cache manager for cross-repository components
 */
class ComponentCacheManager {
  constructor(options = {}) {
    this.cacheDir = options.cacheDir || path.join(process.cwd(), '.cross-repo-cache');
    this.maxSize = options.maxSize || 100; // MB
    this.ttl = options.ttl || 3600000; // 1 hour
  }

  /**
   * Cache component content
   * @param {Object} component - Component to cache
   * @returns {Object} Cache result
   */
  async cacheComponent(component) {
    const result = {
      cached: false,
      cacheKey: null,
      error: null
    };

    try {
      const cacheKey = this.generateCacheKey(component.reference, component.version);
      const cachePath = path.join(this.cacheDir, `${cacheKey}.json`);
      
      // Ensure cache directory exists
      await fs.mkdir(this.cacheDir, { recursive: true });
      
      const cacheData = {
        reference: component.reference,
        content: component.content,
        version: component.version,
        timestamp: Date.now(),
        metadata: component.metadata || {}
      };
      
      await fs.writeFile(cachePath, JSON.stringify(cacheData, null, 2));
      
      result.cached = true;
      result.cacheKey = cacheKey;
      
      // Clean cache if needed
      await this.clearCacheIfNeeded();

    } catch (error) {
      result.error = error.message;
    }

    return result;
  }

  /**
   * Get cached component
   * @param {string} cacheKey - Cache key
   * @returns {Object} Cached component or null
   */
  async getCachedComponent(cacheKey) {
    const result = {
      found: false,
      content: null,
      expired: false,
      error: null
    };

    try {
      const cachePath = path.join(this.cacheDir, `${cacheKey}.json`);
      
      // Check if file exists and get stats
      const stats = await fs.stat(cachePath);
      
      // Check expiration
      if (Date.now() - stats.mtime.getTime() > this.ttl) {
        result.expired = true;
        return result;
      }
      
      const cacheData = JSON.parse(await fs.readFile(cachePath, 'utf8'));
      
      result.found = true;
      result.content = cacheData.content;
      result.metadata = cacheData.metadata;
      result.timestamp = cacheData.timestamp;

    } catch (error) {
      if (error.code !== 'ENOENT') {
        result.error = error.message;
      }
    }

    return result;
  }

  /**
   * Generate cache key from reference and version
   * @param {string} reference - Cross-repository reference
   * @param {string} version - Component version
   * @returns {string} Cache key
   */
  generateCacheKey(reference, version = 'latest') {
    const data = `${reference}:${version}`;
    return crypto.createHash('md5').update(data).digest('hex');
  }

  /**
   * Clear cache if size limit exceeded
   */
  async clearCacheIfNeeded() {
    try {
      const files = await fs.readdir(this.cacheDir);
      let totalSize = 0;
      
      const fileStats = [];
      for (const file of files) {
        const filePath = path.join(this.cacheDir, file);
        const stats = await fs.stat(filePath);
        totalSize += stats.size;
        fileStats.push({ file, path: filePath, size: stats.size, mtime: stats.mtime });
      }
      
      // Convert maxSize from MB to bytes
      const maxSizeBytes = this.maxSize * 1024 * 1024;
      
      if (totalSize > maxSizeBytes) {
        // Sort by modification time (oldest first)
        fileStats.sort((a, b) => a.mtime - b.mtime);
        
        // Remove oldest files until under size limit
        let currentSize = totalSize;
        for (const fileStat of fileStats) {
          if (currentSize <= maxSizeBytes) break;
          
          await fs.unlink(fileStat.path);
          currentSize -= fileStat.size;
        }
      }
    } catch (error) {
      console.warn('Cache cleanup failed:', error.message);
    }
  }

  /**
   * Clear all cached components
   */
  async clearAllCache() {
    try {
      const files = await fs.readdir(this.cacheDir);
      
      for (const file of files) {
        const filePath = path.join(this.cacheDir, file);
        await fs.unlink(filePath);
      }
    } catch (error) {
      console.warn('Failed to clear cache:', error.message);
    }
  }
}

/**
 * Offline fallback manager
 */
class OfflineFallbackManager {
  constructor(options = {}) {
    this.fallbackDir = options.fallbackDir || path.join(process.cwd(), '.fallback-cache');
    this.enableNetworkCheck = options.enableNetworkCheck !== false;
    this.defaultTemplates = options.defaultTemplates || {};
  }

  /**
   * Check if system is in offline mode
   * @returns {boolean} Whether system is offline
   */
  async checkOfflineMode() {
    if (!this.enableNetworkCheck) return false;

    try {
      // Try to ping a reliable service
      execSync('ping -c 1 8.8.8.8', { timeout: 5000 });
      return false;
    } catch (error) {
      return true;
    }
  }

  /**
   * Get fallback content for reference
   * @param {string} reference - Cross-repository reference
   * @param {Object} options - Fallback options
   * @returns {Object} Fallback content result
   */
  async getFallbackContent(reference, options = {}) {
    const result = {
      success: false,
      content: null,
      source: null,
      error: null
    };

    try {
      const fallbackKey = this._generateFallbackKey(reference);
      const fallbackPath = path.join(this.fallbackDir, `${fallbackKey}.json`);
      
      // Try to read cached fallback
      try {
        const fallbackData = JSON.parse(await fs.readFile(fallbackPath, 'utf8'));
        
        result.success = true;
        result.content = fallbackData.content;
        result.source = 'fallback';
        result.metadata = fallbackData.metadata;
        
        return result;
      } catch (error) {
        // Fallback cache miss, try default template
      }
      
      // Use default template if available
      if (options.useDefaultTemplate) {
        const template = this._getDefaultTemplate(reference);
        if (template) {
          result.success = true;
          result.content = template;
          result.source = 'default-template';
          return result;
        }
      }
      
      result.error = 'No fallback content available';

    } catch (error) {
      result.error = error.message;
    }

    return result;
  }

  /**
   * Create fallback cache entry
   * @param {string} reference - Cross-repository reference
   * @param {string} content - Content to cache
   * @param {Object} metadata - Additional metadata
   */
  async createFallbackEntry(reference, content, metadata = {}) {
    try {
      await fs.mkdir(this.fallbackDir, { recursive: true });
      
      const fallbackKey = this._generateFallbackKey(reference);
      const fallbackPath = path.join(this.fallbackDir, `${fallbackKey}.json`);
      
      const fallbackData = {
        reference: reference,
        content: content,
        metadata: metadata,
        timestamp: Date.now()
      };
      
      await fs.writeFile(fallbackPath, JSON.stringify(fallbackData, null, 2));
    } catch (error) {
      console.warn('Failed to create fallback entry:', error.message);
    }
  }

  /**
   * Sync fallback cache when online
   * @returns {Object} Sync result
   */
  async syncFallbackCache() {
    const result = {
      synced: false,
      filesProcessed: 0,
      errors: [],
      error: null
    };

    try {
      const isOffline = await this.checkOfflineMode();
      if (isOffline) {
        result.error = 'Cannot sync while offline';
        return result;
      }

      const files = await fs.readdir(this.fallbackDir);
      const crossRepoManager = new CrossRepositoryManager();
      
      for (const file of files) {
        if (!file.endsWith('.json')) continue;
        
        try {
          const filePath = path.join(this.fallbackDir, file);
          const fallbackData = JSON.parse(await fs.readFile(filePath, 'utf8'));
          
          // Try to resolve current reference
          const resolved = await crossRepoManager.resolveReference(fallbackData.reference);
          
          if (resolved.success) {
            const currentContent = await fs.readFile(resolved.localPath, 'utf8');
            
            // Update fallback if content changed
            if (currentContent !== fallbackData.content) {
              await this.createFallbackEntry(
                fallbackData.reference,
                currentContent,
                fallbackData.metadata
              );
            }
          }
          
          result.filesProcessed++;
        } catch (error) {
          result.errors.push({ file, error: error.message });
        }
      }
      
      result.synced = true;

    } catch (error) {
      result.error = error.message;
    }

    return result;
  }

  /**
   * Generate fallback key from reference
   * @param {string} reference - Cross-repository reference
   * @returns {string} Fallback key
   * @private
   */
  _generateFallbackKey(reference) {
    return crypto.createHash('md5').update(reference).digest('hex');
  }

  /**
   * Get default template for reference
   * @param {string} reference - Cross-repository reference
   * @returns {string|null} Default template content
   * @private
   */
  _getDefaultTemplate(reference) {
    const parsed = new CrossRepositoryManager().parseReference(reference);
    
    if (!parsed.valid) return null;
    
    const filename = path.basename(parsed.path);
    const extension = path.extname(filename);
    
    // Return appropriate default template
    switch (extension) {
      case '.md':
        return '# Default Template\n\nThis is a default template used when the original reference is unavailable.\n';
      case '.yml':
      case '.yaml':
        return 'default: true\ntemplate: basic\n';
      case '.json':
        return '{"default": true, "template": "basic"}';
      default:
        return 'Default content for unavailable reference.';
    }
  }
}

module.exports = {
  CrossRepositoryManager,
  GitSubmoduleIntegration,
  ReferenceResolver,
  VersionCompatibilityChecker,
  ComponentCacheManager,
  OfflineFallbackManager
};