/**
 * UV Tool Integration for Enhanced Create-Specs System
 * 
 * Provides comprehensive Python project management capabilities using UV tool:
 * - Environment management and virtual environments
 * - Package installation and dependency resolution
 * - Testing framework integration
 * - Development server and debugging support
 * - Deployment and distribution management
 * - Performance optimization and monitoring
 */

const fs = require('fs').promises;
const path = require('path');
const { execSync, spawn } = require('child_process');

/**
 * UV Tool Manager for Python project operations
 */
class UVToolManager {
  constructor(options = {}) {
    this.uvCommand = options.uvCommand || 'uv';
    this.projectRoot = options.projectRoot || process.cwd();
    this.verbose = options.verbose || false;
  }

  /**
   * Check if UV tool is installed and available
   * @returns {Object} Installation status and version info
   */
  async checkUVInstallation() {
    try {
      const version = execSync(`${this.uvCommand} --version`, { encoding: 'utf8' }).trim();
      
      return {
        installed: true,
        version: version,
        available: true,
        message: `UV tool is available: ${version}`
      };
    } catch (error) {
      return {
        installed: false,
        version: null,
        available: false,
        message: 'UV tool is not installed. Install with: curl -LsSf https://astral.sh/uv/install.sh | sh',
        installCommand: 'curl -LsSf https://astral.sh/uv/install.sh | sh'
      };
    }
  }

  /**
   * Initialize UV project structure
   * @param {Object} projectConfig - Project configuration
   * @returns {Object} Initialization results
   */
  async initializeProject(projectConfig) {
    const { projectName, pythonVersion, dependencies = [] } = projectConfig;
    
    try {
      // Create pyproject.toml configuration
      const pyprojectConfig = this.generatePyprojectToml({
        projectName,
        pythonVersion,
        dependencies
      });

      // Write pyproject.toml
      await fs.writeFile(
        path.join(this.projectRoot, 'pyproject.toml'),
        pyprojectConfig,
        'utf8'
      );

      // Initialize UV project
      const initResult = execSync(`${this.uvCommand} init --python ${pythonVersion}`, {
        cwd: this.projectRoot,
        encoding: 'utf8'
      });

      // Create virtual environment
      const venvResult = await this.createVirtualEnvironment();

      return {
        success: true,
        message: 'UV project initialized successfully',
        pyprojectCreated: true,
        virtualEnvironment: venvResult,
        initOutput: initResult
      };

    } catch (error) {
      return {
        success: false,
        error: error.message,
        message: 'Failed to initialize UV project'
      };
    }
  }

  /**
   * Create virtual environment using UV
   * @param {Object} options - Environment options
   * @returns {Object} Environment creation results
   */
  async createVirtualEnvironment(options = {}) {
    const { pythonVersion = '3.11', name = '.venv' } = options;

    try {
      const command = `${this.uvCommand} venv ${name} --python ${pythonVersion}`;
      const result = execSync(command, {
        cwd: this.projectRoot,
        encoding: 'utf8'
      });

      return {
        created: true,
        path: path.join(this.projectRoot, name),
        pythonVersion: pythonVersion,
        activationCommand: this.getActivationCommand(name),
        message: `Virtual environment created: ${name}`,
        output: result
      };

    } catch (error) {
      return {
        created: false,
        error: error.message,
        message: 'Failed to create virtual environment'
      };
    }
  }

  /**
   * Install dependencies using UV
   * @param {Array} dependencies - List of dependencies to install
   * @param {Object} options - Installation options
   * @returns {Object} Installation results
   */
  async installDependencies(dependencies, options = {}) {
    const { dev = false, upgrade = false } = options;
    
    try {
      const results = [];

      for (const dependency of dependencies) {
        const flags = [];
        if (dev) flags.push('--dev');
        if (upgrade) flags.push('--upgrade');

        const command = `${this.uvCommand} add ${flags.join(' ')} ${dependency}`;
        const result = execSync(command, {
          cwd: this.projectRoot,
          encoding: 'utf8'
        });

        results.push({
          dependency,
          installed: true,
          output: result
        });
      }

      return {
        success: true,
        installed: dependencies.length,
        results: results,
        message: `Successfully installed ${dependencies.length} dependencies`
      };

    } catch (error) {
      return {
        success: false,
        error: error.message,
        message: 'Failed to install dependencies'
      };
    }
  }

  /**
   * Run tests using UV and pytest
   * @param {Object} testConfig - Test configuration
   * @returns {Object} Test execution results
   */
  async runTests(testConfig = {}) {
    const {
      testPath = 'tests/',
      coverage = true,
      verbose = false,
      parallel = true,
      pattern = null
    } = testConfig;

    try {
      // Build test command
      const testArgs = [];
      if (coverage) testArgs.push('--cov=src', '--cov-report=html', '--cov-report=term');
      if (verbose) testArgs.push('-v');
      if (parallel) testArgs.push('-n', 'auto');
      if (pattern) testArgs.push('-k', pattern);

      testArgs.push(testPath);

      const command = `${this.uvCommand} run pytest ${testArgs.join(' ')}`;
      
      return new Promise((resolve, reject) => {
        const testProcess = spawn(this.uvCommand, ['run', 'pytest', ...testArgs], {
          cwd: this.projectRoot,
          stdio: ['inherit', 'pipe', 'pipe']
        });

        let stdout = '';
        let stderr = '';

        testProcess.stdout.on('data', (data) => {
          stdout += data.toString();
          if (this.verbose) process.stdout.write(data);
        });

        testProcess.stderr.on('data', (data) => {
          stderr += data.toString();
          if (this.verbose) process.stderr.write(data);
        });

        testProcess.on('close', (code) => {
          const result = {
            success: code === 0,
            exitCode: code,
            stdout: stdout,
            stderr: stderr,
            coverage: coverage,
            testPath: testPath
          };

          if (code === 0) {
            result.message = 'All tests passed successfully';
            result.coverageReport = coverage ? this.parseCoverageOutput(stdout) : null;
          } else {
            result.message = `Tests failed with exit code ${code}`;
            result.failures = this.parseTestFailures(stdout);
          }

          resolve(result);
        });

        testProcess.on('error', (error) => {
          reject({
            success: false,
            error: error.message,
            message: 'Failed to run tests'
          });
        });
      });

    } catch (error) {
      return {
        success: false,
        error: error.message,
        message: 'Failed to execute test command'
      };
    }
  }

  /**
   * Run development server or application
   * @param {Object} serverConfig - Server configuration
   * @returns {Object} Server process information
   */
  async runDevelopmentServer(serverConfig = {}) {
    const {
      module = 'src.main',
      port = 8000,
      host = '127.0.0.1',
      reload = true,
      debug = true
    } = serverConfig;

    try {
      const args = ['run', 'python', '-m', module];
      
      // Add server-specific arguments if it's a web framework
      if (serverConfig.framework === 'fastapi' || serverConfig.framework === 'uvicorn') {
        args.push('--host', host, '--port', port.toString());
        if (reload) args.push('--reload');
      }

      const serverProcess = spawn(this.uvCommand, args, {
        cwd: this.projectRoot,
        stdio: 'inherit',
        env: {
          ...process.env,
          DEBUG: debug ? '1' : '0',
          DEVELOPMENT: '1'
        }
      });

      return {
        success: true,
        pid: serverProcess.pid,
        host: host,
        port: port,
        module: module,
        message: `Development server started on ${host}:${port}`,
        process: serverProcess
      };

    } catch (error) {
      return {
        success: false,
        error: error.message,
        message: 'Failed to start development server'
      };
    }
  }

  /**
   * Debug Python application
   * @param {Object} debugConfig - Debug configuration
   * @returns {Object} Debug session information
   */
  async debugApplication(debugConfig = {}) {
    const {
      module = 'src.main',
      args = [],
      debugger = 'pdb',
      port = 5678
    } = debugConfig;

    try {
      const debugArgs = ['run'];

      // Configure debugger
      if (debugger === 'debugpy') {
        debugArgs.push('python', '-m', 'debugpy', '--listen', `0.0.0.0:${port}`, '--wait-for-client', '-m', module);
      } else if (debugger === 'pdb') {
        debugArgs.push('python', '-m', 'pdb', '-m', module);
      } else {
        debugArgs.push('python', '-m', module);
      }

      debugArgs.push(...args);

      const debugProcess = spawn(this.uvCommand, debugArgs, {
        cwd: this.projectRoot,
        stdio: 'inherit',
        env: {
          ...process.env,
          DEBUG: '1',
          PYTHONPATH: path.join(this.projectRoot, 'src')
        }
      });

      return {
        success: true,
        pid: debugProcess.pid,
        debugger: debugger,
        port: debugger === 'debugpy' ? port : null,
        module: module,
        message: `Debug session started for ${module}`,
        process: debugProcess
      };

    } catch (error) {
      return {
        success: false,
        error: error.message,
        message: 'Failed to start debug session'
      };
    }
  }

  /**
   * Build and deploy package
   * @param {Object} deployConfig - Deployment configuration
   * @returns {Object} Deployment results
   */
  async buildAndDeploy(deployConfig = {}) {
    const {
      buildType = 'wheel',
      outputDir = 'dist/',
      repository = 'pypi',
      publish = false
    } = deployConfig;

    try {
      const results = {
        build: null,
        publish: null
      };

      // Build package
      const buildCommand = `${this.uvCommand} build --out-dir ${outputDir}`;
      const buildResult = execSync(buildCommand, {
        cwd: this.projectRoot,
        encoding: 'utf8'
      });

      results.build = {
        success: true,
        output: buildResult,
        outputDir: outputDir,
        message: 'Package built successfully'
      };

      // Publish if requested
      if (publish) {
        const publishCommand = `${this.uvCommand} publish --repository ${repository} ${outputDir}*`;
        const publishResult = execSync(publishCommand, {
          cwd: this.projectRoot,
          encoding: 'utf8'
        });

        results.publish = {
          success: true,
          output: publishResult,
          repository: repository,
          message: 'Package published successfully'
        };
      }

      return {
        success: true,
        ...results,
        message: publish ? 'Package built and published successfully' : 'Package built successfully'
      };

    } catch (error) {
      return {
        success: false,
        error: error.message,
        message: 'Failed to build/deploy package'
      };
    }
  }

  /**
   * Generate pyproject.toml configuration
   * @param {Object} config - Project configuration
   * @returns {string} pyproject.toml content
   * @private
   */
  generatePyprojectToml(config) {
    const { projectName, pythonVersion, dependencies = [] } = config;

    return `[build-system]
requires = ["hatchling"]
build-backend = "hatchling.build"

[project]
name = "${projectName}"
version = "0.1.0"
description = "Enhanced specification implementation"
readme = "README.md"
requires-python = ">=${pythonVersion}"
dependencies = [
${dependencies.map(dep => `    "${dep}",`).join('\n')}
]

[project.optional-dependencies]
dev = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-xdist>=3.0.0",
    "black>=23.0.0",
    "ruff>=0.1.0",
    "mypy>=1.0.0",
]
test = [
    "pytest>=7.0.0",
    "pytest-cov>=4.0.0",
    "pytest-mock>=3.0.0",
]
debug = [
    "debugpy>=1.6.0",
    "ipdb>=0.13.0",
]

[tool.pytest.ini_options]
testpaths = ["tests"]
python_files = ["test_*.py", "*_test.py"]
python_classes = ["Test*"]
python_functions = ["test_*"]
addopts = [
    "--strict-markers",
    "--strict-config",
    "--disable-warnings",
    "-ra",
]

[tool.coverage.run]
source = ["src"]
branch = true

[tool.coverage.report]
exclude_lines = [
    "pragma: no cover",
    "def __repr__",
    "raise AssertionError",
    "raise NotImplementedError",
]

[tool.black]
line-length = 88
target-version = ["py311"]

[tool.ruff]
line-length = 88
target-version = "py311"
select = ["E", "F", "W", "I", "N", "UP", "B", "C4", "PL"]

[tool.mypy]
python_version = "${pythonVersion}"
warn_return_any = true
warn_unused_configs = true
disallow_untyped_defs = true
`;
  }

  /**
   * Get virtual environment activation command
   * @param {string} venvName - Virtual environment name
   * @returns {string} Activation command
   * @private
   */
  getActivationCommand(venvName) {
    const platform = process.platform;
    
    if (platform === 'win32') {
      return `${venvName}\\Scripts\\activate`;
    } else {
      return `source ${venvName}/bin/activate`;
    }
  }

  /**
   * Parse coverage output for reporting
   * @param {string} stdout - Test output
   * @returns {Object} Coverage information
   * @private
   */
  parseCoverageOutput(stdout) {
    const coverageMatch = stdout.match(/TOTAL\s+\d+\s+\d+\s+(\d+)%/);
    const coverage = coverageMatch ? parseInt(coverageMatch[1]) : null;

    return {
      percentage: coverage,
      htmlReport: 'htmlcov/index.html',
      available: coverage !== null
    };
  }

  /**
   * Parse test failures from output
   * @param {string} stdout - Test output
   * @returns {Array} List of failures
   * @private
   */
  parseTestFailures(stdout) {
    const failures = [];
    const failurePattern = /FAILED\s+([^\s]+)\s+-\s+(.+)/g;
    let match;

    while ((match = failurePattern.exec(stdout)) !== null) {
      failures.push({
        test: match[1],
        reason: match[2]
      });
    }

    return failures;
  }
}

/**
 * UV Integration for Enhanced Create-Specs Workflow
 */
class UVCreateSpecsIntegration {
  constructor() {
    this.uvManager = new UVToolManager();
  }

  /**
   * Setup UV environment for new spec implementation
   * @param {Object} specData - Specification data
   * @returns {Object} Setup results
   */
  async setupSpecEnvironment(specData) {
    const { moduleName, specName, pythonVersion = '3.11' } = specData;
    
    try {
      // Check UV installation
      const uvStatus = await this.uvManager.checkUVInstallation();
      if (!uvStatus.installed) {
        return {
          success: false,
          message: uvStatus.message,
          installCommand: uvStatus.installCommand
        };
      }

      // Determine project dependencies based on module type
      const dependencies = this.getModuleDependencies(moduleName);

      // Initialize UV project
      const projectConfig = {
        projectName: `${moduleName}-${specName}`,
        pythonVersion: pythonVersion,
        dependencies: dependencies
      };

      const initResult = await this.uvManager.initializeProject(projectConfig);
      
      if (!initResult.success) {
        return initResult;
      }

      // Install development and testing dependencies
      const devDependencies = [
        'pytest>=7.0.0',
        'pytest-cov>=4.0.0',
        'pytest-xdist>=3.0.0',
        'black>=23.0.0',
        'ruff>=0.1.0'
      ];

      const devInstall = await this.uvManager.installDependencies(devDependencies, { dev: true });

      return {
        success: true,
        uvVersion: uvStatus.version,
        projectInitialized: initResult.success,
        dependenciesInstalled: devInstall.success,
        virtualEnvironment: initResult.virtualEnvironment,
        message: `UV environment setup complete for ${moduleName}/${specName}`,
        nextSteps: [
          'Run tests: uv run pytest',
          'Start development: uv run python -m src.main',
          'Format code: uv run black src/ tests/',
          'Lint code: uv run ruff check src/ tests/'
        ]
      };

    } catch (error) {
      return {
        success: false,
        error: error.message,
        message: 'Failed to setup UV environment'
      };
    }
  }

  /**
   * Get dependencies based on module type
   * @param {string} moduleName - Module name
   * @returns {Array} List of dependencies
   * @private
   */
  getModuleDependencies(moduleName) {
    const dependencyMap = {
      'authentication': ['bcrypt>=4.0.0', 'pyjwt>=2.8.0', 'cryptography>=41.0.0'],
      'api': ['fastapi>=0.104.0', 'uvicorn>=0.24.0', 'pydantic>=2.4.0'],
      'database': ['sqlalchemy>=2.0.0', 'alembic>=1.12.0', 'psycopg2-binary>=2.9.0'],
      'web-scraping': ['requests>=2.31.0', 'beautifulsoup4>=4.12.0', 'scrapy>=2.11.0'],
      'data-processing': ['pandas>=2.1.0', 'numpy>=1.25.0', 'openpyxl>=3.1.0'],
      'visualization': ['plotly>=5.17.0', 'matplotlib>=3.8.0', 'seaborn>=0.13.0'],
      'ai-ml': ['scikit-learn>=1.3.0', 'torch>=2.1.0', 'transformers>=4.35.0'],
      'testing': ['pytest>=7.4.0', 'pytest-mock>=3.12.0', 'factory-boy>=3.3.0']
    };

    return dependencyMap[moduleName] || ['requests>=2.31.0', 'pydantic>=2.4.0'];
  }

  /**
   * Generate UV-specific task additions for task_summary.md
   * @param {Object} specData - Specification data
   * @returns {string} UV task section
   */
  generateUVTaskSection(specData) {
    const { moduleName, specName } = specData;

    return `## UV Tool Integration

### Development Environment Setup
\`\`\`bash
# Initialize UV project
uv init --python 3.11

# Create virtual environment
uv venv

# Install dependencies
uv add ${this.getModuleDependencies(moduleName).join(' ')}

# Install development dependencies
uv add --dev pytest pytest-cov black ruff mypy
\`\`\`

### Development Workflow
\`\`\`bash
# Run tests with coverage
uv run pytest --cov=src --cov-report=html

# Format code
uv run black src/ tests/

# Lint code
uv run ruff check src/ tests/

# Type checking
uv run mypy src/

# Run development server (if applicable)
uv run python -m src.main
\`\`\`

### Testing and Quality Assurance
\`\`\`bash
# Run specific test pattern
uv run pytest -k "test_${specName.replace(/-/g, '_')}"

# Run tests in parallel
uv run pytest -n auto

# Generate coverage report
uv run pytest --cov=src --cov-report=html --cov-report=term

# Performance profiling
uv run python -m cProfile -o profile.stats src/main.py
\`\`\`

### Debugging Support
\`\`\`bash
# Debug with pdb
uv run python -m pdb src/main.py

# Debug with debugpy (VS Code integration)
uv run python -m debugpy --listen 5678 --wait-for-client src/main.py

# Interactive debugging with ipdb
uv run python -c "import ipdb; ipdb.set_trace(); import src.main"
\`\`\`

### Deployment Preparation
\`\`\`bash
# Build package
uv build

# Check package
uv run python -m twine check dist/*

# Publish to PyPI (when ready)
uv publish --repository pypi
\`\`\`

### Performance Monitoring
\`\`\`bash
# Memory profiling
uv run python -m memory_profiler src/main.py

# Line profiling
uv run kernprof -l -v src/main.py

# Benchmark testing
uv run python -m pytest tests/performance/ --benchmark-only
\`\`\``;
  }
}

module.exports = {
  UVToolManager,
  UVCreateSpecsIntegration
};