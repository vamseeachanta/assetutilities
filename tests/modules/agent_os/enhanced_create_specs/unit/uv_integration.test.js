/**
 * Unit Tests for UV Tool Integration
 * 
 * Tests the UV tool integration including:
 * - UV installation detection and validation
 * - Virtual environment creation and management
 * - Dependency installation and resolution
 * - Testing framework integration
 * - Development server and debugging support
 * - Package building and deployment
 */

const { describe, it, expect, beforeEach, afterEach, jest } = require('@jest/globals');
const { execSync, spawn } = require('child_process');
const fs = require('fs').promises;

// Mock dependencies
jest.mock('child_process');
jest.mock('fs', () => ({
  promises: {
    writeFile: jest.fn(),
    readFile: jest.fn(),
    mkdir: jest.fn(),
    access: jest.fn()
  }
}));

// Import the modules we'll be testing
const {
  UVToolManager,
  UVCreateSpecsIntegration
} = require('../../../../../src/modules/agent-os/enhanced-create-specs/uv-integration');

describe('UV Tool Integration', () => {
  let mockExecSync;
  let mockSpawn;
  let mockFs;

  beforeEach(() => {
    mockExecSync = require('child_process').execSync;
    mockSpawn = require('child_process').spawn;
    mockFs = require('fs').promises;
    
    jest.clearAllMocks();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('UVToolManager', () => {
    let uvManager;

    beforeEach(() => {
      uvManager = new UVToolManager();
    });

    describe('checkUVInstallation', () => {
      it('should detect UV installation when available', async () => {
        mockExecSync.mockReturnValue('uv 0.1.35');

        const result = await uvManager.checkUVInstallation();

        expect(result.installed).toBe(true);
        expect(result.version).toBe('uv 0.1.35');
        expect(result.available).toBe(true);
        expect(result.message).toContain('UV tool is available');
      });

      it('should handle UV not installed', async () => {
        mockExecSync.mockImplementation(() => {
          throw new Error('Command not found');
        });

        const result = await uvManager.checkUVInstallation();

        expect(result.installed).toBe(false);
        expect(result.available).toBe(false);
        expect(result.message).toContain('UV tool is not installed');
        expect(result.installCommand).toContain('curl -LsSf');
      });

      it('should use custom UV command if specified', async () => {
        const customUvManager = new UVToolManager({ uvCommand: '/usr/local/bin/uv' });
        mockExecSync.mockReturnValue('uv 0.1.35');

        await customUvManager.checkUVInstallation();

        expect(mockExecSync).toHaveBeenCalledWith('/usr/local/bin/uv --version', { encoding: 'utf8' });
      });
    });

    describe('initializeProject', () => {
      beforeEach(() => {
        mockFs.writeFile.mockResolvedValue();
        mockExecSync.mockReturnValue('UV project initialized');
      });

      it('should initialize UV project with correct configuration', async () => {
        const projectConfig = {
          projectName: 'test-project',
          pythonVersion: '3.11',
          dependencies: ['requests>=2.31.0', 'pydantic>=2.4.0']
        };

        const result = await uvManager.initializeProject(projectConfig);

        expect(result.success).toBe(true);
        expect(result.pyprojectCreated).toBe(true);
        expect(mockFs.writeFile).toHaveBeenCalledWith(
          expect.stringContaining('pyproject.toml'),
          expect.stringContaining('test-project'),
          'utf8'
        );
        expect(mockExecSync).toHaveBeenCalledWith(
          'uv init --python 3.11',
          expect.any(Object)
        );
      });

      it('should handle initialization errors gracefully', async () => {
        mockExecSync.mockImplementation(() => {
          throw new Error('Python version not found');
        });

        const projectConfig = {
          projectName: 'test-project',
          pythonVersion: '3.12'
        };

        const result = await uvManager.initializeProject(projectConfig);

        expect(result.success).toBe(false);
        expect(result.error).toContain('Python version not found');
      });

      it('should generate correct pyproject.toml content', async () => {
        const projectConfig = {
          projectName: 'auth-system',
          pythonVersion: '3.11',
          dependencies: ['bcrypt>=4.0.0', 'pyjwt>=2.8.0']
        };

        await uvManager.initializeProject(projectConfig);

        const writeCall = mockFs.writeFile.mock.calls[0];
        const pyprojectContent = writeCall[1];

        expect(pyprojectContent).toContain('name = "auth-system"');
        expect(pyprojectContent).toContain('requires-python = ">=3.11"');
        expect(pyprojectContent).toContain('"bcrypt>=4.0.0",');
        expect(pyprojectContent).toContain('"pyjwt>=2.8.0",');
        expect(pyprojectContent).toContain('[tool.pytest.ini_options]');
      });
    });

    describe('createVirtualEnvironment', () => {
      it('should create virtual environment with default settings', async () => {
        mockExecSync.mockReturnValue('Virtual environment created');

        const result = await uvManager.createVirtualEnvironment();

        expect(result.created).toBe(true);
        expect(result.pythonVersion).toBe('3.11');
        expect(result.path).toContain('.venv');
        expect(result.activationCommand).toContain('source .venv/bin/activate');
        expect(mockExecSync).toHaveBeenCalledWith(
          'uv venv .venv --python 3.11',
          expect.any(Object)
        );
      });

      it('should create virtual environment with custom settings', async () => {
        mockExecSync.mockReturnValue('Virtual environment created');

        const options = {
          pythonVersion: '3.12',
          name: 'custom-venv'
        };

        const result = await uvManager.createVirtualEnvironment(options);

        expect(result.created).toBe(true);
        expect(result.pythonVersion).toBe('3.12');
        expect(result.path).toContain('custom-venv');
        expect(mockExecSync).toHaveBeenCalledWith(
          'uv venv custom-venv --python 3.12',
          expect.any(Object)
        );
      });

      it('should handle Windows activation command', async () => {
        const originalPlatform = process.platform;
        Object.defineProperty(process, 'platform', { value: 'win32' });
        
        mockExecSync.mockReturnValue('Virtual environment created');

        const result = await uvManager.createVirtualEnvironment();

        expect(result.activationCommand).toContain('.venv\\Scripts\\activate');

        Object.defineProperty(process, 'platform', { value: originalPlatform });
      });
    });

    describe('installDependencies', () => {
      it('should install dependencies successfully', async () => {
        mockExecSync.mockReturnValue('Package installed successfully');

        const dependencies = ['requests>=2.31.0', 'fastapi>=0.104.0'];
        const result = await uvManager.installDependencies(dependencies);

        expect(result.success).toBe(true);
        expect(result.installed).toBe(2);
        expect(result.results).toHaveLength(2);
        expect(mockExecSync).toHaveBeenCalledTimes(2);
        expect(mockExecSync).toHaveBeenCalledWith(
          'uv add  requests>=2.31.0',
          expect.any(Object)
        );
      });

      it('should install dev dependencies with correct flags', async () => {
        mockExecSync.mockReturnValue('Dev package installed');

        const dependencies = ['pytest>=7.0.0'];
        const options = { dev: true, upgrade: true };
        
        const result = await uvManager.installDependencies(dependencies, options);

        expect(result.success).toBe(true);
        expect(mockExecSync).toHaveBeenCalledWith(
          'uv add --dev --upgrade pytest>=7.0.0',
          expect.any(Object)
        );
      });

      it('should handle installation failures', async () => {
        mockExecSync.mockImplementation(() => {
          throw new Error('Package not found');
        });

        const dependencies = ['nonexistent-package'];
        const result = await uvManager.installDependencies(dependencies);

        expect(result.success).toBe(false);
        expect(result.error).toContain('Package not found');
      });
    });

    describe('runTests', () => {
      let mockTestProcess;

      beforeEach(() => {
        mockTestProcess = {
          stdout: { on: jest.fn() },
          stderr: { on: jest.fn() },
          on: jest.fn()
        };
        mockSpawn.mockReturnValue(mockTestProcess);
      });

      it('should run tests with default configuration', async () => {
        mockTestProcess.on.mockImplementation((event, callback) => {
          if (event === 'close') {
            callback(0); // Success exit code
          }
        });

        const resultPromise = uvManager.runTests();
        
        // Simulate test completion
        const closeCallback = mockTestProcess.on.mock.calls.find(call => call[0] === 'close')[1];
        closeCallback(0);

        const result = await resultPromise;

        expect(result.success).toBe(true);
        expect(result.exitCode).toBe(0);
        expect(mockSpawn).toHaveBeenCalledWith(
          'uv',
          ['run', 'pytest', '--cov=src', '--cov-report=html', '--cov-report=term', '-v', '-n', 'auto', 'tests/'],
          expect.any(Object)
        );
      });

      it('should handle test failures', async () => {
        const resultPromise = uvManager.runTests();
        
        // Simulate test failure
        const closeCallback = mockTestProcess.on.mock.calls.find(call => call[0] === 'close')[1];
        closeCallback(1);

        const result = await resultPromise;

        expect(result.success).toBe(false);
        expect(result.exitCode).toBe(1);
        expect(result.message).toContain('Tests failed with exit code 1');
      });

      it('should run tests with custom configuration', async () => {
        const testConfig = {
          testPath: 'tests/unit/',
          coverage: false,
          verbose: true,
          parallel: false,
          pattern: 'test_auth'
        };

        mockTestProcess.on.mockImplementation((event, callback) => {
          if (event === 'close') callback(0);
        });

        const resultPromise = uvManager.runTests(testConfig);
        const closeCallback = mockTestProcess.on.mock.calls.find(call => call[0] === 'close')[1];
        closeCallback(0);

        await resultPromise;

        expect(mockSpawn).toHaveBeenCalledWith(
          'uv',
          ['run', 'pytest', '-v', '-k', 'test_auth', 'tests/unit/'],
          expect.any(Object)
        );
      });
    });

    describe('runDevelopmentServer', () => {
      let mockServerProcess;

      beforeEach(() => {
        mockServerProcess = {
          pid: 12345
        };
        mockSpawn.mockReturnValue(mockServerProcess);
      });

      it('should start development server with default settings', async () => {
        const result = await uvManager.runDevelopmentServer();

        expect(result.success).toBe(true);
        expect(result.pid).toBe(12345);
        expect(result.host).toBe('127.0.0.1');
        expect(result.port).toBe(8000);
        expect(mockSpawn).toHaveBeenCalledWith(
          'uv',
          ['run', 'python', '-m', 'src.main'],
          expect.objectContaining({
            env: expect.objectContaining({
              DEBUG: '1',
              DEVELOPMENT: '1'
            })
          })
        );
      });

      it('should start FastAPI server with uvicorn settings', async () => {
        const serverConfig = {
          framework: 'fastapi',
          port: 3000,
          host: '0.0.0.0',
          reload: true
        };

        const result = await uvManager.runDevelopmentServer(serverConfig);

        expect(result.success).toBe(true);
        expect(result.port).toBe(3000);
        expect(result.host).toBe('0.0.0.0');
        expect(mockSpawn).toHaveBeenCalledWith(
          'uv',
          ['run', 'python', '-m', 'src.main', '--host', '0.0.0.0', '--port', '3000', '--reload'],
          expect.any(Object)
        );
      });
    });

    describe('debugApplication', () => {
      let mockDebugProcess;

      beforeEach(() => {
        mockDebugProcess = {
          pid: 54321
        };
        mockSpawn.mockReturnValue(mockDebugProcess);
      });

      it('should start debug session with pdb', async () => {
        const result = await uvManager.debugApplication();

        expect(result.success).toBe(true);
        expect(result.debugger).toBe('pdb');
        expect(result.pid).toBe(54321);
        expect(mockSpawn).toHaveBeenCalledWith(
          'uv',
          ['run', 'python', '-m', 'pdb', '-m', 'src.main'],
          expect.any(Object)
        );
      });

      it('should start debug session with debugpy', async () => {
        const debugConfig = {
          debugger: 'debugpy',
          port: 5678,
          module: 'src.app'
        };

        const result = await uvManager.debugApplication(debugConfig);

        expect(result.success).toBe(true);
        expect(result.debugger).toBe('debugpy');
        expect(result.port).toBe(5678);
        expect(mockSpawn).toHaveBeenCalledWith(
          'uv',
          ['run', 'python', '-m', 'debugpy', '--listen', '0.0.0.0:5678', '--wait-for-client', '-m', 'src.app'],
          expect.any(Object)
        );
      });
    });

    describe('buildAndDeploy', () => {
      it('should build package successfully', async () => {
        mockExecSync.mockReturnValue('Package built successfully');

        const result = await uvManager.buildAndDeploy();

        expect(result.success).toBe(true);
        expect(result.build.success).toBe(true);
        expect(result.publish).toBeNull();
        expect(mockExecSync).toHaveBeenCalledWith(
          'uv build --out-dir dist/',
          expect.any(Object)
        );
      });

      it('should build and publish package', async () => {
        mockExecSync.mockReturnValue('Success');

        const deployConfig = {
          publish: true,
          repository: 'testpypi'
        };

        const result = await uvManager.buildAndDeploy(deployConfig);

        expect(result.success).toBe(true);
        expect(result.build.success).toBe(true);
        expect(result.publish.success).toBe(true);
        expect(result.publish.repository).toBe('testpypi');
        expect(mockExecSync).toHaveBeenCalledTimes(2);
      });

      it('should handle build failures', async () => {
        mockExecSync.mockImplementation(() => {
          throw new Error('Build failed');
        });

        const result = await uvManager.buildAndDeploy();

        expect(result.success).toBe(false);
        expect(result.error).toContain('Build failed');
      });
    });
  });

  describe('UVCreateSpecsIntegration', () => {
    let uvIntegration;

    beforeEach(() => {
      uvIntegration = new UVCreateSpecsIntegration();
      
      // Mock UVToolManager methods
      uvIntegration.uvManager.checkUVInstallation = jest.fn();
      uvIntegration.uvManager.initializeProject = jest.fn();
      uvIntegration.uvManager.installDependencies = jest.fn();
    });

    describe('setupSpecEnvironment', () => {
      it('should setup complete UV environment for authentication spec', async () => {
        // Mock successful UV operations
        uvIntegration.uvManager.checkUVInstallation.mockResolvedValue({
          installed: true,
          version: 'uv 0.1.35'
        });

        uvIntegration.uvManager.initializeProject.mockResolvedValue({
          success: true,
          virtualEnvironment: { created: true, path: '.venv' }
        });

        uvIntegration.uvManager.installDependencies.mockResolvedValue({
          success: true
        });

        const specData = {
          moduleName: 'authentication',
          specName: 'user-auth-system',
          pythonVersion: '3.11'
        };

        const result = await uvIntegration.setupSpecEnvironment(specData);

        expect(result.success).toBe(true);
        expect(result.projectInitialized).toBe(true);
        expect(result.dependenciesInstalled).toBe(true);
        expect(result.nextSteps).toContain('Run tests: uv run pytest');
        expect(result.nextSteps).toContain('Format code: uv run black src/ tests/');
      });

      it('should handle UV not installed', async () => {
        uvIntegration.uvManager.checkUVInstallation.mockResolvedValue({
          installed: false,
          message: 'UV tool is not installed',
          installCommand: 'curl -LsSf https://astral.sh/uv/install.sh | sh'
        });

        const specData = {
          moduleName: 'api',
          specName: 'rest-api'
        };

        const result = await uvIntegration.setupSpecEnvironment(specData);

        expect(result.success).toBe(false);
        expect(result.message).toContain('UV tool is not installed');
        expect(result.installCommand).toContain('curl -LsSf');
      });

      it('should setup environment with module-specific dependencies', async () => {
        uvIntegration.uvManager.checkUVInstallation.mockResolvedValue({
          installed: true,
          version: 'uv 0.1.35'
        });

        uvIntegration.uvManager.initializeProject.mockResolvedValue({
          success: true,
          virtualEnvironment: { created: true }
        });

        uvIntegration.uvManager.installDependencies.mockResolvedValue({
          success: true
        });

        const specData = {
          moduleName: 'api',
          specName: 'rest-endpoints'
        };

        await uvIntegration.setupSpecEnvironment(specData);

        // Check that API-specific dependencies were used
        const initCall = uvIntegration.uvManager.initializeProject.mock.calls[0][0];
        expect(initCall.dependencies).toContain('fastapi>=0.104.0');
        expect(initCall.dependencies).toContain('uvicorn>=0.24.0');
        expect(initCall.dependencies).toContain('pydantic>=2.4.0');
      });
    });

    describe('getModuleDependencies', () => {
      it('should return authentication dependencies', () => {
        const deps = uvIntegration.getModuleDependencies('authentication');
        
        expect(deps).toContain('bcrypt>=4.0.0');
        expect(deps).toContain('pyjwt>=2.8.0');
        expect(deps).toContain('cryptography>=41.0.0');
      });

      it('should return API dependencies', () => {
        const deps = uvIntegration.getModuleDependencies('api');
        
        expect(deps).toContain('fastapi>=0.104.0');
        expect(deps).toContain('uvicorn>=0.24.0');
        expect(deps).toContain('pydantic>=2.4.0');
      });

      it('should return database dependencies', () => {
        const deps = uvIntegration.getModuleDependencies('database');
        
        expect(deps).toContain('sqlalchemy>=2.0.0');
        expect(deps).toContain('alembic>=1.12.0');
        expect(deps).toContain('psycopg2-binary>=2.9.0');
      });

      it('should return default dependencies for unknown modules', () => {
        const deps = uvIntegration.getModuleDependencies('unknown-module');
        
        expect(deps).toContain('requests>=2.31.0');
        expect(deps).toContain('pydantic>=2.4.0');
      });
    });

    describe('generateUVTaskSection', () => {
      it('should generate comprehensive UV task section', () => {
        const specData = {
          moduleName: 'authentication',
          specName: 'user-auth-system'
        };

        const section = uvIntegration.generateUVTaskSection(specData);

        expect(section).toContain('## UV Tool Integration');
        expect(section).toContain('### Development Environment Setup');
        expect(section).toContain('uv init --python 3.11');
        expect(section).toContain('uv add bcrypt>=4.0.0 pyjwt>=2.8.0');
        expect(section).toContain('### Development Workflow');
        expect(section).toContain('uv run pytest --cov=src');
        expect(section).toContain('### Testing and Quality Assurance');
        expect(section).toContain('uv run pytest -k "test_user_auth_system"');
        expect(section).toContain('### Debugging Support');
        expect(section).toContain('uv run python -m debugpy');
        expect(section).toContain('### Deployment Preparation');
        expect(section).toContain('uv build');
      });

      it('should handle spec names with hyphens correctly', () => {
        const specData = {
          moduleName: 'api',
          specName: 'rest-api-endpoints'
        };

        const section = uvIntegration.generateUVTaskSection(specData);

        expect(section).toContain('uv run pytest -k "test_rest_api_endpoints"');
      });
    });
  });

  describe('Integration Tests', () => {
    it('should complete full UV setup workflow', async () => {
      const uvIntegration = new UVCreateSpecsIntegration();
      
      // Mock all UV operations
      uvIntegration.uvManager.checkUVInstallation = jest.fn().mockResolvedValue({
        installed: true,
        version: 'uv 0.1.35'
      });

      uvIntegration.uvManager.initializeProject = jest.fn().mockResolvedValue({
        success: true,
        virtualEnvironment: { created: true, path: '.venv' }
      });

      uvIntegration.uvManager.installDependencies = jest.fn().mockResolvedValue({
        success: true
      });

      const specData = {
        moduleName: 'e-commerce',
        specName: 'product-catalog',
        pythonVersion: '3.11'
      };

      const result = await uvIntegration.setupSpecEnvironment(specData);

      expect(result.success).toBe(true);
      expect(uvIntegration.uvManager.checkUVInstallation).toHaveBeenCalled();
      expect(uvIntegration.uvManager.initializeProject).toHaveBeenCalledWith(
        expect.objectContaining({
          projectName: 'e-commerce-product-catalog',
          pythonVersion: '3.11'
        })
      );
      expect(uvIntegration.uvManager.installDependencies).toHaveBeenCalledWith(
        expect.arrayContaining(['pytest>=7.0.0', 'black>=23.0.0']),
        { dev: true }
      );
    });
  });
});