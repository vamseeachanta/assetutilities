/**
 * Unit Tests for Enhanced Spec Creation Workflow
 * 
 * Tests the core functionality of the enhanced create-specs system including:
 * - Prompt capture and summary functionality
 * - Module identification and classification
 * - Executive summary generation with business impact
 * - Mermaid diagram generation for different spec types
 * - Task summary template system
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
    stat: jest.fn()
  }
}));

// Import the modules we'll be testing (these will be implemented)
const {
  PromptCapture,
  ModuleIdentifier,
  ExecutiveSummaryGenerator,
  MermaidDiagramGenerator,
  TaskSummaryTemplate,
  EnhancedSpecWorkflow
} = require('../../../../../src/modules/agent-os/enhanced-create-specs/workflow-components');

describe('Enhanced Spec Creation Workflow', () => {
  let mockFs;
  
  beforeEach(() => {
    mockFs = require('fs').promises;
    jest.clearAllMocks();
  });

  afterEach(() => {
    jest.restoreAllMocks();
  });

  describe('PromptCapture', () => {
    let promptCapture;

    beforeEach(() => {
      promptCapture = new PromptCapture();
    });

    it('should capture user prompt and generate summary', () => {
      const userPrompt = "I need to implement a user authentication system with JWT tokens, password reset functionality, and email verification for a web application.";
      
      const result = promptCapture.captureAndSummarize(userPrompt);
      
      expect(result).toHaveProperty('originalPrompt', userPrompt);
      expect(result).toHaveProperty('summary');
      expect(result.summary).toContain('authentication');
      expect(result.summary).toContain('JWT');
      expect(result.summary.length).toBeLessThan(userPrompt.length);
    });

    it('should extract key features from prompt', () => {
      const userPrompt = "Create an e-commerce system with product catalog, shopping cart, payment processing, and order management.";
      
      const result = promptCapture.captureAndSummarize(userPrompt);
      
      expect(result).toHaveProperty('keyFeatures');
      expect(result.keyFeatures).toContain('product catalog');
      expect(result.keyFeatures).toContain('shopping cart');
      expect(result.keyFeatures).toContain('payment processing');
      expect(result.keyFeatures).toContain('order management');
    });

    it('should identify user stories from prompt', () => {
      const userPrompt = "Users should be able to register accounts, login securely, and reset their passwords if forgotten.";
      
      const result = promptCapture.captureAndSummarize(userPrompt);
      
      expect(result).toHaveProperty('userStories');
      expect(result.userStories).toHaveLength(3);
      expect(result.userStories[0]).toMatch(/register accounts/);
      expect(result.userStories[1]).toMatch(/login securely/);
      expect(result.userStories[2]).toMatch(/reset.*passwords/);
    });

    it('should handle empty or minimal prompts gracefully', () => {
      const userPrompt = "Simple task";
      
      const result = promptCapture.captureAndSummarize(userPrompt);
      
      expect(result).toHaveProperty('originalPrompt', userPrompt);
      expect(result).toHaveProperty('summary');
      expect(result).toHaveProperty('keyFeatures');
      expect(result).toHaveProperty('userStories');
    });
  });

  describe('ModuleIdentifier', () => {
    let moduleIdentifier;

    beforeEach(() => {
      moduleIdentifier = new ModuleIdentifier();
    });

    it('should identify authentication module from spec content', () => {
      const specContent = {
        summary: "User authentication system with JWT tokens and password reset",
        keyFeatures: ["user registration", "login", "password reset", "JWT tokens"]
      };
      
      const result = moduleIdentifier.identifyModule(specContent);
      
      expect(result.moduleName).toBe('authentication');
      expect(result.confidence).toBeGreaterThan(0.8);
      expect(result.reasoning).toContain('authentication');
    });

    it('should identify e-commerce module from spec content', () => {
      const specContent = {
        summary: "E-commerce platform with product catalog and shopping cart",
        keyFeatures: ["product catalog", "shopping cart", "payment processing", "inventory"]
      };
      
      const result = moduleIdentifier.identifyModule(specContent);
      
      expect(result.moduleName).toBe('e-commerce');
      expect(result.confidence).toBeGreaterThan(0.7);
    });

    it('should identify payment module from spec content', () => {
      const specContent = {
        summary: "Payment processing system with multiple payment methods",
        keyFeatures: ["credit card processing", "PayPal integration", "refunds", "billing"]
      };
      
      const result = moduleIdentifier.identifyModule(specContent);
      
      expect(result.moduleName).toBe('payment');
      expect(result.confidence).toBeGreaterThan(0.8);
    });

    it('should fallback to product module for unclassified specs', () => {
      const specContent = {
        summary: "Generic application feature",
        keyFeatures: ["some feature", "another feature"]
      };
      
      const result = moduleIdentifier.identifyModule(specContent);
      
      expect(result.moduleName).toBe('product');
      expect(result.confidence).toBeLessThan(0.5);
      expect(result.reasoning).toContain('fallback');
    });

    it('should handle AI/ML related specs', () => {
      const specContent = {
        summary: "Machine learning model for recommendation system",
        keyFeatures: ["neural networks", "data processing", "model training", "predictions"]
      };
      
      const result = moduleIdentifier.identifyModule(specContent);
      
      expect(result.moduleName).toBe('ai-ml');
      expect(result.confidence).toBeGreaterThan(0.7);
    });
  });

  describe('ExecutiveSummaryGenerator', () => {
    let executiveSummaryGenerator;

    beforeEach(() => {
      executiveSummaryGenerator = new ExecutiveSummaryGenerator();
    });

    it('should generate executive summary with business impact', () => {
      const specContent = {
        summary: "User authentication system with security features",
        keyFeatures: ["secure login", "password encryption", "session management"],
        moduleName: "authentication"
      };
      
      const result = executiveSummaryGenerator.generate(specContent);
      
      expect(result).toHaveProperty('businessImpact');
      expect(result).toHaveProperty('userValue');
      expect(result).toHaveProperty('technicalValue');
      expect(result).toHaveProperty('implementationEffort');
      expect(result.businessImpact).toContain('security');
      expect(result.userValue).toContain('users');
    });

    it('should assess implementation effort correctly', () => {
      const complexSpec = {
        summary: "Complex e-commerce platform with multiple integrations",
        keyFeatures: ["product catalog", "payment processing", "inventory", "shipping", "analytics", "admin dashboard"],
        moduleName: "e-commerce"
      };
      
      const result = executiveSummaryGenerator.generate(complexSpec);
      
      expect(result.implementationEffort).toBe('High');
    });

    it('should assess simple specs as low effort', () => {
      const simpleSpec = {
        summary: "Simple contact form with validation",
        keyFeatures: ["form validation", "email sending"],
        moduleName: "product"
      };
      
      const result = executiveSummaryGenerator.generate(simpleSpec);
      
      expect(result.implementationEffort).toBe('Low');
    });

    it('should generate different impact assessments for different modules', () => {
      const authSpec = {
        summary: "Authentication system",
        keyFeatures: ["login", "security"],
        moduleName: "authentication"
      };
      
      const paymentSpec = {
        summary: "Payment processing",
        keyFeatures: ["credit cards", "billing"],
        moduleName: "payment"
      };
      
      const authResult = executiveSummaryGenerator.generate(authSpec);
      const paymentResult = executiveSummaryGenerator.generate(paymentSpec);
      
      expect(authResult.businessImpact).not.toBe(paymentResult.businessImpact);
      expect(authResult.technicalValue).toContain('security');
      expect(paymentResult.technicalValue).toContain('revenue');
    });
  });

  describe('MermaidDiagramGenerator', () => {
    let mermaidGenerator;

    beforeEach(() => {
      mermaidGenerator = new MermaidDiagramGenerator();
    });

    it('should generate authentication flow diagram', () => {
      const specContent = {
        moduleName: "authentication",
        keyFeatures: ["user registration", "login", "password reset"]
      };
      
      const result = mermaidGenerator.generateDiagram(specContent);
      
      expect(result.diagramType).toBe('sequenceDiagram');
      expect(result.diagram).toContain('sequenceDiagram');
      expect(result.diagram).toContain('User');
      expect(result.diagram).toContain('AuthService');
      expect(result.diagram).toContain('register');
      expect(result.diagram).toContain('login');
    });

    it('should generate e-commerce system diagram', () => {
      const specContent = {
        moduleName: "e-commerce",
        keyFeatures: ["product catalog", "shopping cart", "checkout"]
      };
      
      const result = mermaidGenerator.generateDiagram(specContent);
      
      expect(result.diagramType).toBe('graph');
      expect(result.diagram).toContain('graph TD');
      expect(result.diagram).toContain('Product');
      expect(result.diagram).toContain('Cart');
      expect(result.diagram).toContain('Checkout');
    });

    it('should generate database schema diagram for data-heavy specs', () => {
      const specContent = {
        moduleName: "product",
        keyFeatures: ["user management", "data storage", "reporting"],
        hasDatabase: true
      };
      
      const result = mermaidGenerator.generateDiagram(specContent);
      
      expect(result.diagramType).toBe('erDiagram');
      expect(result.diagram).toContain('erDiagram');
    });

    it('should generate API flow diagram for API specs', () => {
      const specContent = {
        moduleName: "api",
        keyFeatures: ["REST endpoints", "data validation", "response formatting"]
      };
      
      const result = mermaidGenerator.generateDiagram(specContent);
      
      expect(result.diagramType).toBe('sequenceDiagram');
      expect(result.diagram).toContain('API');
      expect(result.diagram).toContain('Client');
    });

    it('should handle unknown module types with generic diagram', () => {
      const specContent = {
        moduleName: "unknown",
        keyFeatures: ["feature 1", "feature 2"]
      };
      
      const result = mermaidGenerator.generateDiagram(specContent);
      
      expect(result.diagramType).toBe('graph');
      expect(result.diagram).toContain('graph TD');
    });
  });

  describe('TaskSummaryTemplate', () => {
    let taskSummaryTemplate;

    beforeEach(() => {
      taskSummaryTemplate = new TaskSummaryTemplate();
    });

    it('should generate task summary template with all required sections', () => {
      const specContent = {
        moduleName: "authentication",
        specName: "user-auth-system",
        executiveSummary: {
          businessImpact: "Improves security",
          implementationEffort: "Medium"
        }
      };
      
      const result = taskSummaryTemplate.generate(specContent);
      
      expect(result).toContain('# Task Summary');
      expect(result).toContain('## Executive Summary');
      expect(result).toContain('## Files Changed');
      expect(result).toContain('## Implementation Logic');
      expect(result).toContain('## Way Forward');
      expect(result).toContain('authentication');
      expect(result).toContain('user-auth-system');
    });

    it('should include module and spec metadata', () => {
      const specContent = {
        moduleName: "e-commerce",
        specName: "product-catalog",
        subAgent: "inventory-management"
      };
      
      const result = taskSummaryTemplate.generate(specContent);
      
      expect(result).toContain('> **Module:** e-commerce');
      expect(result).toContain('> **Spec:** product-catalog');
      expect(result).toContain('> **Sub-Agent:** inventory-management');
    });

    it('should include cross-repository reference', () => {
      const specContent = {
        moduleName: "authentication",
        specName: "user-auth-system"
      };
      
      const result = taskSummaryTemplate.generate(specContent);
      
      expect(result).toContain('@github:assetutilities/');
      expect(result).toContain('enhanced_create_specs_workflow.md');
    });

    it('should handle different implementation efforts', () => {
      const highEffortSpec = {
        moduleName: "complex",
        specName: "big-feature",
        executiveSummary: {
          implementationEffort: "High"
        }
      };
      
      const result = taskSummaryTemplate.generate(highEffortSpec);
      
      expect(result).toContain('High complexity');
    });
  });

  describe('EnhancedSpecWorkflow Integration', () => {
    let workflow;

    beforeEach(() => {
      workflow = new EnhancedSpecWorkflow();
      mockFs.mkdir.mockResolvedValue();
      mockFs.writeFile.mockResolvedValue();
      mockFs.readFile.mockResolvedValue('{}');
      mockFs.access.mockResolvedValue();
    });

    it('should execute complete workflow for user prompt', async () => {
      const userPrompt = "Create a user authentication system with JWT tokens and password reset functionality.";
      
      const result = await workflow.execute(userPrompt);
      
      expect(result).toHaveProperty('specCreated', true);
      expect(result).toHaveProperty('moduleName', 'authentication');
      expect(result).toHaveProperty('specName');
      expect(result).toHaveProperty('filesCreated');
      expect(result.filesCreated).toContain('spec.md');
      expect(result.filesCreated).toContain('task_summary.md');
    });

    it('should create proper directory structure', async () => {
      const userPrompt = "Payment processing system";
      
      await workflow.execute(userPrompt);
      
      expect(mockFs.mkdir).toHaveBeenCalledWith(
        expect.stringContaining('specs/modules/payment'),
        { recursive: true }
      );
      expect(mockFs.mkdir).toHaveBeenCalledWith(
        expect.stringContaining('docs/modules/payment'),
        { recursive: true }
      );
      expect(mockFs.mkdir).toHaveBeenCalledWith(
        expect.stringContaining('src/modules/payment'),
        { recursive: true }
      );
    });

    it('should write all required spec files', async () => {
      const userPrompt = "User authentication system";
      
      await workflow.execute(userPrompt);
      
      expect(mockFs.writeFile).toHaveBeenCalledWith(
        expect.stringContaining('spec.md'),
        expect.stringContaining('# Spec Requirements Document')
      );
      expect(mockFs.writeFile).toHaveBeenCalledWith(
        expect.stringContaining('task_summary.md'),
        expect.stringContaining('# Task Summary')
      );
    });

    it('should handle workflow errors gracefully', async () => {
      mockFs.mkdir.mockRejectedValue(new Error('Permission denied'));
      
      const userPrompt = "Test system";
      
      await expect(workflow.execute(userPrompt)).rejects.toThrow('Permission denied');
    });

    it('should generate appropriate sub-specs based on module type', async () => {
      const userPrompt = "API service with database integration";
      
      const result = await workflow.execute(userPrompt);
      
      expect(result.filesCreated).toContain('technical-spec.md');
      expect(result.filesCreated).toContain('api-spec.md');
      expect(result.filesCreated).toContain('database-schema.md');
    });
  });

  describe('Error Handling and Edge Cases', () => {
    it('should handle very long prompts', () => {
      const promptCapture = new PromptCapture();
      const longPrompt = 'A'.repeat(10000) + " authentication system";
      
      const result = promptCapture.captureAndSummarize(longPrompt);
      
      expect(result.summary.length).toBeLessThan(1000);
      expect(result.summary).toContain('authentication');
    });

    it('should handle prompts with special characters', () => {
      const promptCapture = new PromptCapture();
      const specialPrompt = "Create system with @#$%^&*() special chars & emojis 🚀";
      
      const result = promptCapture.captureAndSummarize(specialPrompt);
      
      expect(result).toHaveProperty('summary');
      expect(result.summary).not.toContain('🚀'); // Emojis filtered out
    });

    it('should handle multilingual prompts', () => {
      const moduleIdentifier = new ModuleIdentifier();
      const multilingualContent = {
        summary: "Sistema de autenticación de usuarios",
        keyFeatures: ["login", "registro", "contraseñas"]
      };
      
      const result = moduleIdentifier.identifyModule(multilingualContent);
      
      expect(result.moduleName).toBe('authentication');
    });

    it('should validate generated mermaid diagrams', () => {
      const mermaidGenerator = new MermaidDiagramGenerator();
      const specContent = {
        moduleName: "authentication",
        keyFeatures: ["login", "register"]
      };
      
      const result = mermaidGenerator.generateDiagram(specContent);
      
      // Basic mermaid syntax validation
      expect(result.diagram).toMatch(/^(graph|sequenceDiagram|erDiagram)/);
      expect(result.diagram).not.toContain('undefined');
      expect(result.diagram).not.toContain('null');
    });
  });
});