/**
 * Enhanced Spec Creation Workflow Components
 * 
 * Core components for the enhanced create-specs system including:
 * - Prompt capture and summarization
 * - Module identification and classification  
 * - Executive summary generation with business impact
 * - Mermaid diagram generation for different spec types
 * - Task summary template system
 * - Complete workflow orchestration
 */

const fs = require('fs').promises;
const path = require('path');
const { UVCreateSpecsIntegration } = require('./uv-integration');

/**
 * Captures user prompts and generates intelligent summaries with key features extraction
 */
class PromptCapture {
  constructor() {
    this.keywordPatterns = {
      authentication: ['auth', 'login', 'register', 'password', 'jwt', 'token', 'session', 'security'],
      ecommerce: ['product', 'cart', 'shop', 'order', 'payment', 'checkout', 'inventory', 'catalog'],
      payment: ['payment', 'billing', 'invoice', 'credit card', 'paypal', 'stripe', 'transaction'],
      api: ['api', 'endpoint', 'rest', 'graphql', 'service', 'integration', 'webhook'],
      database: ['database', 'sql', 'migration', 'schema', 'query', 'data', 'storage'],
      ui: ['ui', 'interface', 'component', 'frontend', 'react', 'vue', 'angular', 'html'],
      admin: ['admin', 'dashboard', 'management', 'control panel', 'settings', 'configuration']
    };
  }

  /**
   * Captures and summarizes user prompt with key feature extraction
   * @param {string} userPrompt - The original user prompt
   * @returns {object} Structured prompt analysis
   */
  captureAndSummarize(userPrompt) {
    const cleanPrompt = this._cleanPrompt(userPrompt);
    const summary = this._generateSummary(cleanPrompt);
    const keyFeatures = this._extractKeyFeatures(cleanPrompt);
    const userStories = this._extractUserStories(cleanPrompt);

    return {
      originalPrompt: userPrompt,
      summary,
      keyFeatures,
      userStories,
      wordCount: userPrompt.split(' ').length,
      complexity: this._assessComplexity(keyFeatures, userStories)
    };
  }

  /**
   * Clean the prompt by removing special characters and normalizing text
   * @private
   */
  _cleanPrompt(prompt) {
    return prompt
      .replace(/[^\w\s\-,.]/g, ' ') // Remove special chars except basic punctuation
      .replace(/\s+/g, ' ') // Normalize whitespace
      .trim()
      .toLowerCase();
  }

  /**
   * Generate intelligent summary of the prompt
   * @private
   */
  _generateSummary(cleanPrompt) {
    const sentences = cleanPrompt.split(/[.!?]+/).filter(s => s.trim().length > 0);
    
    if (sentences.length <= 2) {
      return cleanPrompt;
    }

    // Extract key sentences containing main actions/objects
    const keySentences = sentences.filter(sentence => {
      const words = sentence.trim().split(' ');
      return words.some(word => 
        ['create', 'implement', 'build', 'develop', 'system', 'service', 'application'].includes(word)
      );
    });

    const summary = keySentences.length > 0 ? keySentences.slice(0, 2).join('. ') : sentences.slice(0, 2).join('. ');
    
    // Limit summary length
    if (summary.length > 200) {
      return summary.substring(0, 197) + '...';
    }
    
    return summary.charAt(0).toUpperCase() + summary.slice(1);
  }

  /**
   * Extract key features from the prompt
   * @private
   */
  _extractKeyFeatures(cleanPrompt) {
    const features = [];
    const words = cleanPrompt.split(' ');
    
    // Look for feature patterns
    const featurePatterns = [
      /(\w+)\s+(system|service|feature|functionality|component)/g,
      /(login|register|authentication|payment|checkout|cart|dashboard)/g,
      /(\w+)\s+(management|processing|integration|validation)/g
    ];

    featurePatterns.forEach(pattern => {
      let match;
      while ((match = pattern.exec(cleanPrompt)) !== null) {
        const feature = match[0].trim();
        if (feature.length > 3 && !features.includes(feature)) {
          features.push(feature);
        }
      }
    });

    // If no patterns found, extract noun phrases
    if (features.length === 0) {
      const nounPhrases = this._extractNounPhrases(words);
      features.push(...nounPhrases.slice(0, 5));
    }

    return features.slice(0, 8); // Limit to 8 features
  }

  /**
   * Extract user stories from prompt
   * @private
   */
  _extractUserStories(cleanPrompt) {
    const stories = [];
    
    // Look for user action patterns
    const userActionPatterns = [
      /users?\s+(should|can|need|want|will)\s+(.+?)(?:\.|,|$)/g,
      /(register|login|create|manage|view|edit|delete|update)\s+(.+?)(?:\.|,|$)/g
    ];

    userActionPatterns.forEach(pattern => {
      let match;
      while ((match = pattern.exec(cleanPrompt)) !== null) {
        const story = match[0].trim();
        if (story.length > 10 && !stories.includes(story)) {
          stories.push(story);
        }
      }
    });

    // Fallback: create stories from key features
    if (stories.length === 0) {
      const features = this._extractKeyFeatures(cleanPrompt);
      features.slice(0, 3).forEach(feature => {
        stories.push(`Users should be able to use ${feature}`);
      });
    }

    return stories.slice(0, 5); // Limit to 5 stories
  }

  /**
   * Extract noun phrases from words
   * @private
   */
  _extractNounPhrases(words) {
    const phrases = [];
    const commonNouns = ['system', 'service', 'application', 'feature', 'component', 'module', 'interface'];
    
    for (let i = 0; i < words.length - 1; i++) {
      if (commonNouns.includes(words[i + 1])) {
        const phrase = `${words[i]} ${words[i + 1]}`;
        if (!phrases.includes(phrase)) {
          phrases.push(phrase);
        }
      }
    }
    
    return phrases;
  }

  /**
   * Assess prompt complexity
   * @private
   */
  _assessComplexity(keyFeatures, userStories) {
    const featureCount = keyFeatures.length;
    const storyCount = userStories.length;
    
    if (featureCount >= 6 || storyCount >= 4) {
      return 'High';
    } else if (featureCount >= 3 || storyCount >= 2) {
      return 'Medium';
    } else {
      return 'Low';
    }
  }
}

/**
 * Identifies appropriate module classification for specs
 */
class ModuleIdentifier {
  constructor() {
    this.moduleKeywords = {
      'authentication': {
        keywords: ['auth', 'login', 'register', 'password', 'jwt', 'token', 'session', 'security', 'user', 'signin', 'signup'],
        weight: 1.0
      },
      'e-commerce': {
        keywords: ['ecommerce', 'shop', 'store', 'product', 'cart', 'order', 'checkout', 'inventory', 'catalog', 'payment'],
        weight: 0.9
      },
      'payment': {
        keywords: ['payment', 'billing', 'invoice', 'credit', 'paypal', 'stripe', 'transaction', 'refund', 'subscription'],
        weight: 0.95
      },
      'api': {
        keywords: ['api', 'endpoint', 'rest', 'graphql', 'service', 'integration', 'webhook', 'microservice'],
        weight: 0.8
      },
      'ai-ml': {
        keywords: ['machine learning', 'ai', 'neural', 'model', 'prediction', 'recommendation', 'algorithm', 'training'],
        weight: 0.85
      },
      'admin': {
        keywords: ['admin', 'dashboard', 'management', 'control', 'configuration', 'settings', 'panel'],
        weight: 0.7
      },
      'ui-ux': {
        keywords: ['ui', 'ux', 'interface', 'component', 'frontend', 'react', 'vue', 'angular', 'design'],
        weight: 0.6
      },
      'database': {
        keywords: ['database', 'sql', 'migration', 'schema', 'query', 'storage', 'data'],
        weight: 0.75
      },
      'notification': {
        keywords: ['notification', 'email', 'sms', 'push', 'alert', 'message'],
        weight: 0.8
      },
      'reporting': {
        keywords: ['report', 'analytics', 'dashboard', 'chart', 'graph', 'visualization', 'metrics'],
        weight: 0.7
      }
    };
  }

  /**
   * Identify the most appropriate module for spec content
   * @param {object} specContent - Parsed spec content with summary and features
   * @returns {object} Module identification result
   */
  identifyModule(specContent) {
    const text = `${specContent.summary} ${specContent.keyFeatures.join(' ')}`.toLowerCase();
    const scores = {};

    // Calculate scores for each module
    Object.entries(this.moduleKeywords).forEach(([moduleName, config]) => {
      let score = 0;
      let matchCount = 0;

      config.keywords.forEach(keyword => {
        const regex = new RegExp(`\\b${keyword}\\b`, 'gi');
        const matches = (text.match(regex) || []).length;
        if (matches > 0) {
          score += matches * config.weight;
          matchCount++;
        }
      });

      scores[moduleName] = {
        score: score,
        matchCount: matchCount,
        confidence: Math.min(score / 10, 1.0) // Normalize to 0-1
      };
    });

    // Find the best match
    const bestMatch = Object.entries(scores).reduce((best, [moduleName, data]) => {
      if (data.score > best.score) {
        return { moduleName, ...data };
      }
      return best;
    }, { moduleName: 'product', score: 0, confidence: 0 });

    // Generate reasoning
    const reasoning = bestMatch.score > 0 
      ? `Identified as '${bestMatch.moduleName}' based on ${bestMatch.matchCount} keyword matches with confidence ${(bestMatch.confidence * 100).toFixed(1)}%`
      : 'No strong module indicators found, using fallback module "product"';

    return {
      moduleName: bestMatch.moduleName,
      confidence: bestMatch.confidence,
      reasoning: reasoning,
      allScores: scores
    };
  }
}

/**
 * Generates executive summaries with business impact analysis
 */
class ExecutiveSummaryGenerator {
  constructor() {
    this.impactTemplates = {
      'authentication': {
        businessImpact: 'Improves security and user trust while reducing support overhead for account-related issues',
        userValue: 'Users gain secure, seamless access to system features with reliable account management',
        technicalValue: 'Provides robust security foundation for application features and user data protection'
      },
      'payment': {
        businessImpact: 'Directly enables revenue generation and improves customer conversion rates',
        userValue: 'Users can complete transactions securely with multiple payment options',
        technicalValue: 'Integrates secure payment processing with proper financial data handling and compliance'
      },
      'e-commerce': {
        businessImpact: 'Creates comprehensive sales platform to drive revenue growth and market expansion',
        userValue: 'Users get intuitive shopping experience with product discovery and easy purchasing',
        technicalValue: 'Builds scalable product management and order processing systems'
      },
      'api': {
        businessImpact: 'Enables system integration and third-party partnerships for business growth',
        userValue: 'Users benefit from seamless data access and integration with external services',
        technicalValue: 'Provides standardized interfaces for system interoperability and data exchange'
      },
      'admin': {
        businessImpact: 'Reduces operational costs and improves system management efficiency',
        userValue: 'Administrators get powerful tools for system oversight and user management',
        technicalValue: 'Centralizes system configuration and monitoring capabilities'
      },
      'ai-ml': {
        businessImpact: 'Provides competitive advantage through intelligent automation and insights',
        userValue: 'Users receive personalized experiences and intelligent recommendations',
        technicalValue: 'Implements machine learning infrastructure for data-driven decision making'
      }
    };

    this.effortFactors = {
      'authentication': 0.8, // Well-established patterns
      'payment': 0.9, // Complex but standard
      'e-commerce': 1.0, // Comprehensive system
      'api': 0.7, // Standardized approaches
      'admin': 0.6, // CRUD-heavy
      'ai-ml': 1.2, // Complex and experimental
      'ui-ux': 0.5, // Mostly frontend
      'database': 0.4, // Schema design
      'notification': 0.6, // Integration-focused
      'reporting': 0.7 // Data processing
    };
  }

  /**
   * Generate executive summary with business impact analysis
   * @param {object} specContent - Spec content with module and features
   * @returns {object} Executive summary with impact analysis
   */
  generate(specContent) {
    const moduleName = specContent.moduleName || 'product';
    const template = this.impactTemplates[moduleName] || this._generateGenericImpact(specContent);
    
    const implementationEffort = this._assessImplementationEffort(specContent);
    const businessValue = this._assessBusinessValue(specContent);
    const technicalRisk = this._assessTechnicalRisk(specContent);

    return {
      businessImpact: template.businessImpact,
      userValue: template.userValue,
      technicalValue: template.technicalValue,
      implementationEffort: implementationEffort,
      businessValue: businessValue,
      technicalRisk: technicalRisk,
      recommendation: this._generateRecommendation(implementationEffort, businessValue, technicalRisk)
    };
  }

  /**
   * Generate generic impact for unknown modules
   * @private
   */
  _generateGenericImpact(specContent) {
    return {
      businessImpact: `Enhances system capabilities and supports business objectives through ${specContent.summary}`,
      userValue: 'Users benefit from improved functionality and enhanced user experience',
      technicalValue: 'Adds valuable capabilities to the technical architecture and system functionality'
    };
  }

  /**
   * Assess implementation effort based on complexity indicators
   * @private
   */
  _assessImplementationEffort(specContent) {
    const moduleName = specContent.moduleName || 'product';
    const baseEffort = this.effortFactors[moduleName] || 0.5;
    const keyFeatures = specContent.keyFeatures || [];
    const complexity = specContent.complexity || 'Medium';

    let effortMultiplier = 1.0;
    
    // Adjust based on feature count
    if (keyFeatures.length >= 8) {
      effortMultiplier *= 1.5;
    } else if (keyFeatures.length >= 5) {
      effortMultiplier *= 1.2;
    }

    // Adjust based on complexity
    if (complexity === 'High') {
      effortMultiplier *= 1.3;
    } else if (complexity === 'Low') {
      effortMultiplier *= 0.8;
    }

    const finalEffort = baseEffort * effortMultiplier;

    if (finalEffort >= 1.0) return 'High';
    if (finalEffort >= 0.6) return 'Medium';
    return 'Low';
  }

  /**
   * Assess business value
   * @private
   */
  _assessBusinessValue(specContent) {
    const highValueModules = ['payment', 'e-commerce', 'authentication', 'ai-ml'];
    const moduleName = specContent.moduleName || 'product';
    
    if (highValueModules.includes(moduleName)) {
      return 'High';
    }
    
    const keyFeatures = specContent.keyFeatures || [];
    if (keyFeatures.length >= 5) {
      return 'Medium';
    }
    
    return 'Medium';
  }

  /**
   * Assess technical risk
   * @private
   */
  _assessTechnicalRisk(specContent) {
    const highRiskModules = ['ai-ml', 'payment'];
    const mediumRiskModules = ['e-commerce', 'api'];
    const moduleName = specContent.moduleName || 'product';
    
    if (highRiskModules.includes(moduleName)) {
      return 'High';
    }
    if (mediumRiskModules.includes(moduleName)) {
      return 'Medium';
    }
    return 'Low';
  }

  /**
   * Generate implementation recommendation
   * @private
   */
  _generateRecommendation(effort, value, risk) {
    if (value === 'High' && risk === 'Low') {
      return 'Highly recommended - high value with manageable risk';
    }
    if (effort === 'Low' && value === 'Medium') {
      return 'Good quick win - low effort with solid value';
    }
    if (risk === 'High') {
      return 'Proceed with caution - conduct thorough technical planning';
    }
    return 'Standard implementation approach recommended';
  }
}

/**
 * Generates Mermaid diagrams based on spec type and content
 */
class MermaidDiagramGenerator {
  constructor() {
    this.diagramTemplates = {
      'authentication': this._generateAuthenticationDiagram.bind(this),
      'e-commerce': this._generateEcommerceDiagram.bind(this),
      'payment': this._generatePaymentDiagram.bind(this),
      'api': this._generateAPIDiagram.bind(this),
      'admin': this._generateAdminDiagram.bind(this),
      'ai-ml': this._generateAIMLDiagram.bind(this),
      'database': this._generateDatabaseDiagram.bind(this),
      'ui-ux': this._generateUIUXDiagram.bind(this)
    };
  }

  /**
   * Generate appropriate Mermaid diagram for spec content
   * @param {object} specContent - Spec content with module and features
   * @returns {object} Diagram type and content
   */
  generateDiagram(specContent) {
    const moduleName = specContent.moduleName || 'product';
    const generator = this.diagramTemplates[moduleName] || this._generateGenericDiagram.bind(this);
    
    const result = generator(specContent);
    
    return {
      diagramType: result.type,
      diagram: result.content,
      description: result.description || `${moduleName} system diagram`
    };
  }

  /**
   * Generate authentication flow diagram
   * @private
   */
  _generateAuthenticationDiagram(specContent) {
    return {
      type: 'sequenceDiagram',
      content: `sequenceDiagram
    participant User
    participant AuthService
    participant Database
    participant EmailService
    
    User->>AuthService: Register Account
    AuthService->>Database: Store User Data
    AuthService->>EmailService: Send Verification
    EmailService-->>User: Verification Email
    
    User->>AuthService: Verify Email
    AuthService->>Database: Update Status
    AuthService-->>User: Account Verified
    
    User->>AuthService: Login Request
    AuthService->>Database: Validate Credentials
    AuthService-->>User: JWT Token
    
    User->>AuthService: Access Protected Resource
    AuthService->>AuthService: Validate Token
    AuthService-->>User: Resource Data`,
      description: 'Authentication system user flow'
    };
  }

  /**
   * Generate e-commerce system diagram
   * @private
   */
  _generateEcommerceDiagram(specContent) {
    return {
      type: 'graph',
      content: `graph TD
    A[Product Catalog] --> B[Product Details]
    B --> C[Add to Cart]
    C --> D[Shopping Cart]
    D --> E[Checkout Process]
    E --> F[Payment Processing]
    F --> G[Order Confirmation]
    G --> H[Order Management]
    H --> I[Shipping]
    I --> J[Delivery]
    
    K[Inventory Management] --> A
    L[User Authentication] --> C
    M[Payment Gateway] --> F
    N[Email Service] --> G`,
      description: 'E-commerce system flow'
    };
  }

  /**
   * Generate payment processing diagram
   * @private
   */
  _generatePaymentDiagram(specContent) {
    return {
      type: 'sequenceDiagram',
      content: `sequenceDiagram
    participant Customer
    participant PaymentService
    participant PaymentGateway
    participant Bank
    participant Database
    
    Customer->>PaymentService: Initiate Payment
    PaymentService->>PaymentGateway: Process Payment
    PaymentGateway->>Bank: Authorize Transaction
    Bank-->>PaymentGateway: Authorization Result
    PaymentGateway-->>PaymentService: Payment Status
    PaymentService->>Database: Record Transaction
    PaymentService-->>Customer: Payment Confirmation`,
      description: 'Payment processing flow'
    };
  }

  /**
   * Generate API system diagram
   * @private
   */
  _generateAPIDiagram(specContent) {
    return {
      type: 'sequenceDiagram',
      content: `sequenceDiagram
    participant Client
    participant API Gateway
    participant AuthService
    participant BusinessLogic
    participant Database
    
    Client->>API Gateway: API Request
    API Gateway->>AuthService: Validate Token
    AuthService-->>API Gateway: Auth Result
    API Gateway->>BusinessLogic: Process Request
    BusinessLogic->>Database: Data Operation
    Database-->>BusinessLogic: Data Result
    BusinessLogic-->>API Gateway: Response Data
    API Gateway-->>Client: API Response`,
      description: 'API system architecture'
    };
  }

  /**
   * Generate admin dashboard diagram
   * @private
   */
  _generateAdminDiagram(specContent) {
    return {
      type: 'graph',
      content: `graph TD
    A[Admin Login] --> B[Dashboard]
    B --> C[User Management]
    B --> D[System Settings]
    B --> E[Analytics]
    B --> F[Content Management]
    
    C --> G[View Users]
    C --> H[Edit Users]
    C --> I[User Permissions]
    
    D --> J[Configuration]
    D --> K[Security Settings]
    
    E --> L[Reports]
    E --> M[Metrics]`,
      description: 'Admin dashboard structure'
    };
  }

  /**
   * Generate AI/ML system diagram
   * @private
   */
  _generateAIMLDiagram(specContent) {
    return {
      type: 'graph',
      content: `graph TD
    A[Data Collection] --> B[Data Preprocessing]
    B --> C[Feature Engineering]
    C --> D[Model Training]
    D --> E[Model Validation]
    E --> F[Model Deployment]
    F --> G[Prediction Service]
    G --> H[Results Processing]
    
    I[Data Storage] --> A
    J[Model Registry] --> D
    K[Monitoring] --> G
    L[Feedback Loop] --> B`,
      description: 'AI/ML pipeline architecture'
    };
  }

  /**
   * Generate database schema diagram
   * @private
   */
  _generateDatabaseDiagram(specContent) {
    return {
      type: 'erDiagram',
      content: `erDiagram
    USER {
        int id PK
        string email UK
        string password_hash
        timestamp created_at
    }
    
    PROFILE {
        int id PK
        int user_id FK
        string first_name
        string last_name
    }
    
    SESSION {
        int id PK
        int user_id FK
        string token UK
        timestamp expires_at
    }
    
    USER ||--|| PROFILE : has
    USER ||--o{ SESSION : creates`,
      description: 'Database schema relationships'
    };
  }

  /**
   * Generate UI/UX component diagram
   * @private
   */
  _generateUIUXDiagram(specContent) {
    return {
      type: 'graph',
      content: `graph TD
    A[App Shell] --> B[Header]
    A --> C[Navigation]
    A --> D[Main Content]
    A --> E[Footer]
    
    B --> F[Logo]
    B --> G[User Menu]
    
    C --> H[Primary Nav]
    C --> I[Secondary Nav]
    
    D --> J[Page Content]
    D --> K[Sidebar]
    
    J --> L[Components]
    L --> M[Forms]
    L --> N[Tables]
    L --> O[Modals]`,
      description: 'UI component structure'
    };
  }

  /**
   * Generate generic system diagram
   * @private
   */
  _generateGenericDiagram(specContent) {
    const features = specContent.keyFeatures || ['Feature 1', 'Feature 2'];
    const nodes = features.map((feature, index) => {
      const nodeId = String.fromCharCode(65 + index); // A, B, C, etc.
      return `${nodeId}[${feature}]`;
    }).join('\n    ');
    
    const connections = features.map((_, index) => {
      if (index < features.length - 1) {
        const current = String.fromCharCode(65 + index);
        const next = String.fromCharCode(65 + index + 1);
        return `${current} --> ${next}`;
      }
      return '';
    }).filter(conn => conn).join('\n    ');

    return {
      type: 'graph',
      content: `graph TD
    ${nodes}
    
    ${connections}`,
      description: 'Generic system flow'
    };
  }
}

/**
 * Generates task summary templates with cross-repository references
 */
class TaskSummaryTemplate {
  constructor() {
    this.templateSections = {
      header: this._generateHeader.bind(this),
      executiveSummary: this._generateExecutiveSummary.bind(this),
      filesChanged: this._generateFilesChanged.bind(this),
      implementationLogic: this._generateImplementationLogic.bind(this),
      wayForward: this._generateWayForward.bind(this)
    };
  }

  /**
   * Generate complete task summary template
   * @param {object} specContent - Spec content with all required data
   * @returns {string} Complete task summary markdown
   */
  generate(specContent) {
    const sections = Object.values(this.templateSections).map(generator => generator(specContent));
    return sections.join('\n\n');
  }

  /**
   * Generate header section
   * @private
   */
  _generateHeader(specContent) {
    const today = new Date().toISOString().split('T')[0];
    const subAgent = this._determineSubAgent(specContent.moduleName);
    
    return `# Task Summary

> **Module:** ${specContent.moduleName || 'product'}
> **Spec:** ${specContent.specName || 'unnamed-spec'}
> **Sub-Agent:** ${subAgent}
> **AI Context:** Implementation tracking for ${specContent.specName || 'spec'}

This task summary tracks the implementation progress for the spec detailed in @specs/modules/${specContent.moduleName || 'product'}/${specContent.specName || 'unnamed-spec'}/spec.md

> Created: ${today}
> Status: Ready for Implementation`;
  }

  /**
   * Generate executive summary section
   * @private
   */
  _generateExecutiveSummary(specContent) {
    const executiveSummary = specContent.executiveSummary || {};
    const effort = executiveSummary.implementationEffort || 'Medium';
    const complexityNote = effort === 'High' ? 'High complexity implementation requiring careful planning and phased approach.' :
                          effort === 'Low' ? 'Straightforward implementation with minimal dependencies.' :
                          'Standard complexity implementation following established patterns.';

    return `## Executive Summary

### Business Impact
${executiveSummary.businessImpact || 'Enhances system capabilities and supports business objectives.'}

### Implementation Approach
${complexityNote} This spec focuses on ${specContent.summary || 'system functionality'} with emphasis on quality and maintainability.

### Key Deliverables
- Core functionality implementation following spec requirements
- Comprehensive test coverage for all components
- Documentation updates and integration guides
- Performance validation and optimization

### Success Metrics
- All acceptance criteria met and validated
- Test coverage above 90% for new components
- Performance benchmarks within acceptable ranges
- Successful integration with existing system components`;
  }

  /**
   * Generate files changed section
   * @private
   */
  _generateFilesChanged(specContent) {
    return `## Files Changed

### Implementation Files
\`\`\`
specs/modules/${specContent.moduleName || 'product'}/${specContent.specName || 'unnamed-spec'}/
├── spec.md (requirements)
├── sub-specs/
│   ├── technical-spec.md
│   ├── api-spec.md (if applicable)
│   ├── database-schema.md (if applicable)
│   └── tests.md
├── tasks.md
└── task_summary.md (this file)

src/modules/${specContent.moduleName || 'product'}/
├── core implementation files
└── utilities and helpers

tests/modules/${specContent.moduleName || 'product'}/${specContent.specName || 'unnamed-spec'}/
├── unit/
├── integration/
└── e2e/

docs/modules/${specContent.moduleName || 'product'}/
└── updated documentation
\`\`\`

### Cross-Repository Integration
This implementation utilizes the enhanced create-specs workflow from:
\`@github:assetutilities/src/modules/agent-os/enhanced-create-specs/enhanced_create_specs_workflow.md\`

### Python Development Environment
This Python project uses UV tool for package management and development workflow:
- **Environment**: UV virtual environment with Python 3.11+
- **Testing**: pytest with coverage reporting
- **Code Quality**: black formatting and ruff linting
- **Debugging**: debugpy and pdb integration
- **Deployment**: UV build and publish capabilities`;
  }

  /**
   * Generate implementation logic section
   * @private
   */
  _generateImplementationLogic(specContent) {
    const approach = this._determineImplementationApproach(specContent);
    
    return `## Implementation Logic

### Architecture Approach
${approach.architecture}

### Key Implementation Decisions
${approach.decisions.map(decision => `- ${decision}`).join('\n')}

### Technical Considerations
${approach.considerations.map(consideration => `- ${consideration}`).join('\n')}

### Quality Assurance
- Test-driven development approach with comprehensive coverage
- Code review process for all changes
- Performance testing and optimization
- Security validation for all components
- Documentation review and updates`;
  }

  /**
   * Generate way forward section
   * @private
   */
  _generateWayForward(specContent) {
    return `## Way Forward

### Next Steps
1. **Implementation Phase**
   - Begin with Task 1 from tasks.md
   - Follow test-driven development approach
   - Regular progress reviews and adjustments

2. **Quality Validation**
   - Comprehensive testing at each milestone
   - Performance benchmarking
   - Security review process

3. **Integration & Deployment**
   - System integration testing
   - Documentation finalization
   - Deployment preparation and rollout

### Success Criteria
- [ ] All tasks from tasks.md completed successfully
- [ ] Test coverage above 90% for new functionality
- [ ] Performance requirements met
- [ ] Documentation updated and reviewed
- [ ] Successful integration with existing systems

### Risk Mitigation
- Regular checkpoint reviews to catch issues early
- Modular implementation approach for easier debugging
- Comprehensive testing strategy to prevent regressions
- Clear rollback procedures if issues arise

---

*Generated using Agent OS Enhanced Create-Specs workflow*
*Cross-repository reference: @github:assetutilities/src/modules/agent-os/enhanced-create-specs/*`;
  }

  /**
   * Determine appropriate sub-agent based on module
   * @private
   */
  _determineSubAgent(moduleName) {
    const subAgentMap = {
      'authentication': 'security-authentication',
      'payment': 'financial-payment',
      'e-commerce': 'business-ecommerce',
      'api': 'integration-api',
      'admin': 'management-admin',
      'ai-ml': 'intelligence-aiml',
      'ui-ux': 'interface-design',
      'database': 'data-storage',
      'notification': 'communication-notification',
      'reporting': 'analytics-reporting'
    };
    
    return subAgentMap[moduleName] || 'general-development';
  }

  /**
   * Determine implementation approach based on spec content
   * @private
   */
  _determineImplementationApproach(specContent) {
    const moduleName = specContent.moduleName || 'product';
    const complexity = specContent.complexity || 'Medium';
    
    const approaches = {
      'authentication': {
        architecture: 'Security-first architecture with JWT token management, bcrypt password hashing, and comprehensive session handling.',
        decisions: [
          'Use JWT tokens for stateless authentication',
          'Implement bcrypt for secure password hashing',
          'Create modular service layer for extensibility',
          'Add comprehensive rate limiting and security headers'
        ],
        considerations: [
          'Security best practices throughout implementation',
          'Proper error handling without information leakage',
          'Scalable session management approach',
          'Integration with existing user management systems'
        ]
      },
      'payment': {
        architecture: 'PCI-compliant payment processing with secure transaction handling and comprehensive audit trails.',
        decisions: [
          'Implement secure payment gateway integration',
          'Use tokenization for sensitive payment data',
          'Create comprehensive transaction logging',
          'Add fraud detection and prevention measures'
        ],
        considerations: [
          'PCI compliance requirements',
          'Financial data security and encryption',
          'Transaction atomicity and rollback procedures',
          'Integration with accounting and reporting systems'
        ]
      },
      'e-commerce': {
        architecture: 'Microservices-oriented architecture with separated concerns for catalog, cart, and order management.',
        decisions: [
          'Implement modular product catalog system',
          'Create scalable shopping cart management',
          'Design comprehensive order processing workflow',
          'Add inventory management integration'
        ],
        considerations: [
          'Scalability for high transaction volumes',
          'Integration with payment and shipping services',
          'Product data management and search capabilities',
          'Customer experience optimization'
        ]
      }
    };
    
    const defaultApproach = {
      architecture: 'Modular architecture following established patterns with clear separation of concerns.',
      decisions: [
        'Follow existing codebase patterns and conventions',
        'Implement comprehensive error handling',
        'Create modular components for reusability',
        'Add appropriate logging and monitoring'
      ],
      considerations: [
        'Integration with existing system components',
        'Performance optimization and scalability',
        'Maintainability and code quality',
        'User experience and accessibility'
      ]
    };
    
    return approaches[moduleName] || defaultApproach;
  }
}

/**
 * Main workflow orchestrator that coordinates all components
 */
class EnhancedSpecWorkflow {
  constructor() {
    this.promptCapture = new PromptCapture();
    this.moduleIdentifier = new ModuleIdentifier();
    this.executiveSummaryGenerator = new ExecutiveSummaryGenerator();
    this.mermaidGenerator = new MermaidDiagramGenerator();
    this.taskSummaryTemplate = new TaskSummaryTemplate();
    this.uvIntegration = new UVCreateSpecsIntegration();
  }

  /**
   * Execute the complete enhanced spec creation workflow
   * @param {string} userPrompt - The user's initial prompt
   * @param {object} options - Additional options for workflow execution
   * @returns {object} Complete workflow results
   */
  async execute(userPrompt, options = {}) {
    try {
      // Step 1: Capture and analyze prompt
      const promptAnalysis = this.promptCapture.captureAndSummarize(userPrompt);
      
      // Step 2: Identify module classification
      const moduleResult = this.moduleIdentifier.identifyModule(promptAnalysis);
      
      // Step 3: Generate executive summary
      const executiveSummary = this.executiveSummaryGenerator.generate({
        ...promptAnalysis,
        moduleName: moduleResult.moduleName
      });
      
      // Step 4: Generate Mermaid diagram
      const diagram = this.mermaidGenerator.generateDiagram({
        ...promptAnalysis,
        moduleName: moduleResult.moduleName
      });
      
      // Step 5: Create spec name
      const specName = this._generateSpecName(promptAnalysis, moduleResult.moduleName);
      
      // Step 6: Prepare complete spec content
      const completeSpecContent = {
        ...promptAnalysis,
        moduleName: moduleResult.moduleName,
        specName: specName,
        executiveSummary: executiveSummary,
        diagram: diagram,
        moduleConfidence: moduleResult.confidence,
        moduleReasoning: moduleResult.reasoning
      };
      
      // Step 7: Create directory structure
      await this._createDirectoryStructure(moduleResult.moduleName, specName);
      
      // Step 8: Generate and write all spec files
      const filesCreated = await this._createSpecFiles(completeSpecContent);
      
      // Step 9: Setup UV environment if this is a Python project
      let uvSetup = null;
      if (this._isPythonProject(completeSpecContent)) {
        uvSetup = await this.uvIntegration.setupSpecEnvironment({
          moduleName: moduleResult.moduleName,
          specName: specName,
          pythonVersion: '3.11'
        });
      }
      
      return {
        specCreated: true,
        moduleName: moduleResult.moduleName,
        specName: specName,
        filesCreated: filesCreated,
        promptAnalysis: promptAnalysis,
        executiveSummary: executiveSummary,
        diagram: diagram,
        confidence: moduleResult.confidence,
        uvEnvironment: uvSetup
      };
      
    } catch (error) {
      throw new Error(`Enhanced spec workflow failed: ${error.message}`);
    }
  }

  /**
   * Generate appropriate spec name from prompt analysis
   * @private
   */
  _generateSpecName(promptAnalysis, moduleName) {
    const summary = promptAnalysis.summary.toLowerCase();
    
    // Extract key terms for spec name
    const keyTerms = [];
    
    // Look for common spec patterns
    const patterns = [
      /(\w+)\s+system/g,
      /(\w+)\s+service/g,
      /(\w+)\s+management/g,
      /(\w+)\s+processing/g
    ];
    
    patterns.forEach(pattern => {
      let match;
      while ((match = pattern.exec(summary)) !== null) {
        keyTerms.push(match[1]);
      }
    });
    
    // If no patterns found, use key features
    if (keyTerms.length === 0) {
      keyTerms.push(...promptAnalysis.keyFeatures.slice(0, 2).map(feature => 
        feature.split(' ')[0].toLowerCase()
      ));
    }
    
    // Fallback based on module name
    if (keyTerms.length === 0) {
      keyTerms.push(moduleName.replace('-', ''));
    }
    
    const baseName = keyTerms.slice(0, 3).join('-');
    return `${baseName}-system`;
  }

  /**
   * Create directory structure for module and spec
   * @private
   */
  async _createDirectoryStructure(moduleName, specName) {
    const basePaths = [
      `specs/modules/${moduleName}/${specName}`,
      `specs/modules/${moduleName}/${specName}/sub-specs`,
      `docs/modules/${moduleName}`,
      `src/modules/${moduleName}`,
      `tests/modules/${moduleName}/${specName}/unit`,
      `tests/modules/${moduleName}/${specName}/integration`,
      `tests/modules/${moduleName}/${specName}/e2e`
    ];
    
    for (const dirPath of basePaths) {
      await fs.mkdir(dirPath, { recursive: true });
    }
  }

  /**
   * Create all spec files
   * @private
   */
  async _createSpecFiles(specContent) {
    const filesCreated = [];
    
    // Create main spec.md
    const specMd = this._generateSpecMd(specContent);
    await this._writeFile(`specs/modules/${specContent.moduleName}/${specContent.specName}/spec.md`, specMd);
    filesCreated.push('spec.md');
    
    // Create technical-spec.md
    const technicalSpec = this._generateTechnicalSpec(specContent);
    await this._writeFile(`specs/modules/${specContent.moduleName}/${specContent.specName}/sub-specs/technical-spec.md`, technicalSpec);
    filesCreated.push('technical-spec.md');
    
    // Create tests.md
    const testsSpec = this._generateTestsSpec(specContent);
    await this._writeFile(`specs/modules/${specContent.moduleName}/${specContent.specName}/sub-specs/tests.md`, testsSpec);
    filesCreated.push('tests.md');
    
    // Create tasks.md
    const tasksSpec = this._generateTasksSpec(specContent);
    await this._writeFile(`specs/modules/${specContent.moduleName}/${specContent.specName}/tasks.md`, tasksSpec);
    filesCreated.push('tasks.md');
    
    // Create task_summary.md
    let taskSummary = this.taskSummaryTemplate.generate(specContent);
    
    // Add UV integration section if this is a Python project
    if (this._isPythonProject(specContent)) {
      const uvTaskSection = this.uvIntegration.generateUVTaskSection(specContent);
      taskSummary = taskSummary.replace(
        '---\n\n*Generated using Agent OS Enhanced Create-Specs workflow*',
        uvTaskSection + '\n\n---\n\n*Generated using Agent OS Enhanced Create-Specs workflow*'
      );
    }
    
    await this._writeFile(`specs/modules/${specContent.moduleName}/${specContent.specName}/task_summary.md`, taskSummary);
    filesCreated.push('task_summary.md');
    
    // Conditionally create API spec if needed
    if (this._needsApiSpec(specContent)) {
      const apiSpec = this._generateApiSpec(specContent);
      await this._writeFile(`specs/modules/${specContent.moduleName}/${specContent.specName}/sub-specs/api-spec.md`, apiSpec);
      filesCreated.push('api-spec.md');
    }
    
    // Conditionally create database schema if needed
    if (this._needsDatabaseSpec(specContent)) {
      const dbSpec = this._generateDatabaseSpec(specContent);
      await this._writeFile(`specs/modules/${specContent.moduleName}/${specContent.specName}/sub-specs/database-schema.md`, dbSpec);
      filesCreated.push('database-schema.md');
    }
    
    return filesCreated;
  }

  /**
   * Write file with error handling
   * @private
   */
  async _writeFile(filePath, content) {
    try {
      await fs.writeFile(filePath, content, 'utf8');
    } catch (error) {
      throw new Error(`Failed to write file ${filePath}: ${error.message}`);
    }
  }

  /**
   * Generate main spec.md content
   * @private
   */
  _generateSpecMd(specContent) {
    const today = new Date().toISOString().split('T')[0];
    const subAgent = this.taskSummaryTemplate._determineSubAgent(specContent.moduleName);
    
    return `# Spec Requirements Document

> **Module:** ${specContent.moduleName}
> **Spec:** ${specContent.specName}
> **Sub-Agent:** ${subAgent}
> **AI Context:** ${specContent.summary}

> Spec: ${specContent.specName}
> Created: ${today}
> Status: Planning

## Prompt Summary

**Original Request:** ${specContent.originalPrompt}

**Summary:** ${specContent.summary}

## Executive Summary

### Business Impact
${specContent.executiveSummary.businessImpact}

### User Value
${specContent.executiveSummary.userValue}

### Technical Value
${specContent.executiveSummary.technicalValue}

### Implementation Assessment
- **Effort:** ${specContent.executiveSummary.implementationEffort}
- **Business Value:** ${specContent.executiveSummary.businessValue}
- **Technical Risk:** ${specContent.executiveSummary.technicalRisk}
- **Recommendation:** ${specContent.executiveSummary.recommendation}

## System Overview

\`\`\`mermaid
${specContent.diagram.diagram}
\`\`\`

*${specContent.diagram.description}*

## User Stories

${specContent.userStories.map((story, index) => `### Story ${index + 1}

${story}

**Acceptance Criteria:**
- User can successfully complete the described action
- System provides appropriate feedback and error handling
- Security and validation requirements are met`).join('\n\n')}

## Spec Scope

${specContent.keyFeatures.map((feature, index) => `${index + 1}. **${feature}** - Core functionality for ${feature.toLowerCase()}`).join('\n')}

## Out of Scope

- Advanced analytics and reporting features (future enhancement)
- Mobile application development (separate project)
- Third-party integrations beyond core requirements
- Advanced customization options (future consideration)

## Expected Deliverable

1. Fully functional ${specContent.summary} with all core features implemented
2. Comprehensive test coverage ensuring reliability and security
3. Complete documentation including API documentation and user guides
4. Integration with existing system components and data flows

## Spec Documentation

- Tasks: @specs/modules/${specContent.moduleName}/${specContent.specName}/tasks.md
- Technical Specification: @specs/modules/${specContent.moduleName}/${specContent.specName}/sub-specs/technical-spec.md
- Tests Specification: @specs/modules/${specContent.moduleName}/${specContent.specName}/sub-specs/tests.md${this._needsApiSpec(specContent) ? `
- API Specification: @specs/modules/${specContent.moduleName}/${specContent.specName}/sub-specs/api-spec.md` : ''}${this._needsDatabaseSpec(specContent) ? `
- Database Schema: @specs/modules/${specContent.moduleName}/${specContent.specName}/sub-specs/database-schema.md` : ''}

---

*Module Classification: ${specContent.moduleName} (confidence: ${(specContent.moduleConfidence * 100).toFixed(1)}%)*
*${specContent.moduleReasoning}*`;
  }

  /**
   * Generate technical specification
   * @private
   */
  _generateTechnicalSpec(specContent) {
    const today = new Date().toISOString().split('T')[0];
    
    return `# Technical Specification

> **Module:** ${specContent.moduleName}
> **Sub-Agent:** ${this.taskSummaryTemplate._determineSubAgent(specContent.moduleName)}
> **AI Context:** Technical implementation for ${specContent.specName}

This is the technical specification for the spec detailed in @specs/modules/${specContent.moduleName}/${specContent.specName}/spec.md

> Created: ${today}
> Version: 1.0.0

## Technical Requirements

${specContent.keyFeatures.map(feature => `- **${feature}:** Implement ${feature.toLowerCase()} with proper error handling and validation`).join('\n')}
- **Security:** Implement appropriate security measures for all data handling
- **Performance:** Ensure responsive performance for all user interactions
- **Scalability:** Design for horizontal scaling and increased load

## Implementation Approach

### Architecture Pattern
${this._getArchitecturePattern(specContent.moduleName)}

### Technology Stack
- **Backend Framework:** Node.js with Express or similar
- **Database:** PostgreSQL for relational data
- **Authentication:** JWT tokens with bcrypt password hashing
- **Testing:** Jest for unit testing, Supertest for API testing
- **Documentation:** OpenAPI/Swagger for API documentation

### Security Considerations
- Input validation and sanitization for all user inputs
- Proper authentication and authorization mechanisms
- Secure password storage using bcrypt
- Rate limiting to prevent abuse
- HTTPS enforcement and secure headers

## Component Design

### Core Components
${specContent.keyFeatures.map(feature => `- **${feature} Service:** Handles ${feature.toLowerCase()} business logic`).join('\n')}
- **Validation Service:** Handles input validation and sanitization
- **Security Service:** Manages authentication and authorization
- **Database Service:** Handles data persistence and retrieval

### Integration Points
- External APIs (if applicable)
- Database connections and transactions
- Email service integration (if needed)
- File storage system (if applicable)

## Quality Requirements

### Performance
- Response time < 200ms for standard operations
- Database queries optimized with proper indexing
- Caching strategy for frequently accessed data

### Reliability
- 99.9% uptime requirement
- Graceful error handling and recovery
- Comprehensive logging and monitoring
- Automated backup and recovery procedures

### Security
- Data encryption in transit and at rest
- Regular security audits and updates
- Compliance with relevant security standards
- Proper access controls and permissions

---

*Generated using Agent OS Enhanced Create-Specs workflow*`;
  }

  /**
   * Generate tests specification
   * @private
   */
  _generateTestsSpec(specContent) {
    const today = new Date().toISOString().split('T')[0];
    
    return `# Tests Specification

> **Module:** ${specContent.moduleName}
> **Sub-Agent:** ${this.taskSummaryTemplate._determineSubAgent(specContent.moduleName)}
> **AI Context:** Test coverage for ${specContent.specName}

This is the tests coverage details for the spec detailed in @specs/modules/${specContent.moduleName}/${specContent.specName}/spec.md

> Created: ${today}
> Version: 1.0.0

## Test Coverage Strategy

\`\`\`mermaid
graph TD
    A[Unit Tests] --> B[Integration Tests]
    B --> C[End-to-End Tests]
    
    A --> D[Service Layer Tests]
    A --> E[Utility Function Tests]
    A --> F[Validation Tests]
    
    B --> G[API Endpoint Tests]
    B --> H[Database Integration Tests]
    B --> I[External Service Integration]
    
    C --> J[Complete User Workflows]
    C --> K[Cross-System Integration]
\`\`\`

## Unit Tests

### Location
- **Base Path:** \`tests/modules/${specContent.moduleName}/${specContent.specName}/unit/\`

### Test Coverage
${specContent.keyFeatures.map(feature => `#### ${feature} Tests
- Should handle valid ${feature.toLowerCase()} operations
- Should validate input parameters properly
- Should handle error conditions gracefully
- Should return appropriate response formats`).join('\n\n')}

## Integration Tests

### Location
- **Base Path:** \`tests/modules/${specContent.moduleName}/${specContent.specName}/integration/\`

### Database Integration Tests
- Database connection and transaction handling
- Data persistence and retrieval operations
- Constraint validation and foreign key relationships
- Migration and rollback procedures

### API Integration Tests
- Request/response handling for all endpoints
- Authentication and authorization flows
- Error response formats and status codes
- Rate limiting and security measures

## End-to-End Tests

### Location
- **Base Path:** \`tests/modules/${specContent.moduleName}/${specContent.specName}/e2e/\`

### Complete Workflow Tests
${specContent.userStories.map((story, index) => `#### Workflow ${index + 1}: ${story.split('.')[0]}
- Complete user workflow from start to finish
- All system interactions and validations
- Error handling and recovery scenarios
- Performance and load testing`).join('\n\n')}

## Mock Requirements

### External Service Mocks
- Database connections for isolated testing
- External API services and responses
- File system operations and storage
- Email and notification services

### Test Data Management
- Fixture data for consistent testing
- Database seeding and cleanup procedures
- Test environment configuration
- Data validation and integrity checks

## Performance Tests

### Load Testing
- Concurrent user simulation
- Database performance under load
- Memory usage and resource optimization
- Response time benchmarking

## Test Coverage Requirements

### Coverage Targets
- **Unit Tests:** 95% code coverage
- **Integration Tests:** 90% API endpoint coverage
- **E2E Tests:** 100% critical user flow coverage
- **Performance Tests:** All major workflows benchmarked

---

*Generated using Agent OS Enhanced Create-Specs workflow*`;
  }

  /**
   * Generate tasks specification
   * @private
   */
  _generateTasksSpec(specContent) {
    const today = new Date().toISOString().split('T')[0];
    const subAgent = this.taskSummaryTemplate._determineSubAgent(specContent.moduleName);
    
    return `# Spec Tasks

> **Module:** ${specContent.moduleName}
> **Spec:** ${specContent.specName}
> **Sub-Agent:** ${subAgent}
> **AI Context:** Implementation tasks for ${specContent.specName}

These are the tasks to be completed for the spec detailed in @specs/modules/${specContent.moduleName}/${specContent.specName}/spec.md

> Created: ${today}
> Status: Ready for Implementation

## Module Setup Tasks

- [ ] 0. **Module Structure Verification**
  - [ ] 0.1 Verify module directories exist (src/modules/${specContent.moduleName}/, docs/modules/${specContent.moduleName}/)
  - [ ] 0.2 Create ${subAgent} sub-agent configuration
  - [ ] 0.3 Update module index files and documentation

## Implementation Tasks

${specContent.keyFeatures.map((feature, index) => {
  const taskNum = index + 1;
  const taskName = feature.replace(/\b\w/g, l => l.toUpperCase());
  
  return `- [ ] ${taskNum}. **${taskName}**
  - [ ] ${taskNum}.1 Write tests for ${feature.toLowerCase()} in tests/modules/${specContent.moduleName}/${specContent.specName}/
  - [ ] ${taskNum}.2 Implement ${feature.toLowerCase()} core functionality
  - [ ] ${taskNum}.3 Add input validation and error handling
  - [ ] ${taskNum}.4 Create integration tests for ${feature.toLowerCase()}
  - [ ] ${taskNum}.5 Update module documentation in docs/modules/${specContent.moduleName}/
  - [ ] ${taskNum}.6 Verify all ${feature.toLowerCase()} tests pass`;
}).join('\n\n')}

## Integration Tasks

- [ ] ${specContent.keyFeatures.length + 1}. **System Integration**
  - [ ] ${specContent.keyFeatures.length + 1}.1 Write integration tests for complete system
  - [ ] ${specContent.keyFeatures.length + 1}.2 Integrate all components and verify compatibility
  - [ ] ${specContent.keyFeatures.length + 1}.3 Test cross-system integration points
  - [ ] ${specContent.keyFeatures.length + 1}.4 Validate security and performance requirements
  - [ ] ${specContent.keyFeatures.length + 1}.5 Complete end-to-end testing
  - [ ] ${specContent.keyFeatures.length + 1}.6 Verify all integration tests pass

## Documentation and Deployment Tasks

- [ ] ${specContent.keyFeatures.length + 2}. **Documentation and Deployment**
  - [ ] ${specContent.keyFeatures.length + 2}.1 Complete task_summary.md with implementation details
  - [ ] ${specContent.keyFeatures.length + 2}.2 Create user documentation and API guides
  - [ ] ${specContent.keyFeatures.length + 2}.3 Update all cross-references and module documentation
  - [ ] ${specContent.keyFeatures.length + 2}.4 Verify all tests pass and coverage requirements are met
  - [ ] ${specContent.keyFeatures.length + 2}.5 Update repository module index with new functionality

---

*Generated using Agent OS Enhanced Create-Specs workflow*`;
  }

  /**
   * Check if spec needs API specification
   * @private
   */
  _needsApiSpec(specContent) {
    const apiModules = ['authentication', 'payment', 'e-commerce', 'api'];
    const apiKeywords = ['api', 'endpoint', 'service', 'integration', 'webhook'];
    
    return apiModules.includes(specContent.moduleName) || 
           apiKeywords.some(keyword => 
             specContent.summary.toLowerCase().includes(keyword) ||
             specContent.keyFeatures.some(feature => feature.toLowerCase().includes(keyword))
           );
  }

  /**
   * Check if spec needs database specification
   * @private
   */
  _needsDatabaseSpec(specContent) {
    const dbModules = ['authentication', 'payment', 'e-commerce', 'database'];
    const dbKeywords = ['database', 'storage', 'data', 'user', 'account', 'record'];
    
    return dbModules.includes(specContent.moduleName) || 
           dbKeywords.some(keyword => 
             specContent.summary.toLowerCase().includes(keyword) ||
             specContent.keyFeatures.some(feature => feature.toLowerCase().includes(keyword))
           );
  }

  /**
   * Generate API specification
   * @private
   */
  _generateApiSpec(specContent) {
    const today = new Date().toISOString().split('T')[0];
    
    return `# API Specification

> **Module:** ${specContent.moduleName}
> **Sub-Agent:** ${this.taskSummaryTemplate._determineSubAgent(specContent.moduleName)}
> **AI Context:** API endpoints for ${specContent.specName}

This is the API specification for the spec detailed in @specs/modules/${specContent.moduleName}/${specContent.specName}/spec.md

> Created: ${today}
> Version: 1.0.0

## API Overview

\`\`\`mermaid
sequenceDiagram
    participant Client
    participant API
    participant Service
    participant Database
    
    Client->>API: Request
    API->>Service: Process
    Service->>Database: Query
    Database-->>Service: Data
    Service-->>API: Response
    API-->>Client: Result
\`\`\`

## Endpoints

${specContent.keyFeatures.map(feature => `### ${feature} Endpoints

**POST /api/${specContent.moduleName}/${feature.toLowerCase().replace(/\s+/g, '-')}**
- **Purpose:** Create new ${feature.toLowerCase()}
- **Authentication:** Required
- **Request Body:** JSON with ${feature.toLowerCase()} data
- **Response:** Created ${feature.toLowerCase()} with ID

**GET /api/${specContent.moduleName}/${feature.toLowerCase().replace(/\s+/g, '-')}/:id**
- **Purpose:** Retrieve specific ${feature.toLowerCase()}
- **Authentication:** Required
- **Response:** ${feature} details

**PUT /api/${specContent.moduleName}/${feature.toLowerCase().replace(/\s+/g, '-')}/:id**
- **Purpose:** Update ${feature.toLowerCase()}
- **Authentication:** Required
- **Request Body:** JSON with updated data
- **Response:** Updated ${feature.toLowerCase()}

**DELETE /api/${specContent.moduleName}/${feature.toLowerCase().replace(/\s+/g, '-')}/:id**
- **Purpose:** Delete ${feature.toLowerCase()}
- **Authentication:** Required
- **Response:** Deletion confirmation`).join('\n\n')}

## Authentication

- **Type:** Bearer token (JWT)
- **Header:** Authorization: Bearer <token>
- **Token Expiration:** 24 hours
- **Refresh:** Automatic refresh on valid requests

## Error Handling

### Standard Error Response
\`\`\`json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {},
  "timestamp": "2025-08-01T10:00:00Z"
}
\`\`\`

### HTTP Status Codes
- **200:** Success
- **201:** Created
- **400:** Bad Request
- **401:** Unauthorized
- **403:** Forbidden
- **404:** Not Found
- **429:** Too Many Requests
- **500:** Internal Server Error

---

*Generated using Agent OS Enhanced Create-Specs workflow*`;
  }

  /**
   * Generate database specification
   * @private
   */
  _generateDatabaseSpec(specContent) {
    const today = new Date().toISOString().split('T')[0];
    
    return `# Database Schema

> **Module:** ${specContent.moduleName}
> **Sub-Agent:** ${this.taskSummaryTemplate._determineSubAgent(specContent.moduleName)}
> **AI Context:** Database schema for ${specContent.specName}

This is the database schema implementation for the spec detailed in @specs/modules/${specContent.moduleName}/${specContent.specName}/spec.md

> Created: ${today}
> Version: 1.0.0

## Schema Overview

\`\`\`mermaid
erDiagram
    MAIN_ENTITY {
        bigserial id PK
        varchar name
        text description
        timestamp created_at
        timestamp updated_at
    }
    
    RELATED_ENTITY {
        bigserial id PK
        bigint main_entity_id FK
        varchar type
        timestamp created_at
    }
    
    MAIN_ENTITY ||--o{ RELATED_ENTITY : has
\`\`\`

## Tables

### Primary Tables
${specContent.keyFeatures.map(feature => `#### ${feature.replace(/\s+/g, '_').toLowerCase()}_table
\`\`\`sql
CREATE TABLE ${feature.replace(/\s+/g, '_').toLowerCase()}_table (
    id BIGSERIAL PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    description TEXT,
    status VARCHAR(50) DEFAULT 'active',
    created_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP,
    updated_at TIMESTAMP DEFAULT CURRENT_TIMESTAMP
);
\`\`\``).join('\n\n')}

## Indexes

### Performance Indexes
\`\`\`sql
-- Primary search indexes
${specContent.keyFeatures.map(feature => 
  `CREATE INDEX idx_${feature.replace(/\s+/g, '_').toLowerCase()}_name ON ${feature.replace(/\s+/g, '_').toLowerCase()}_table(name);`
).join('\n')}

-- Timestamp indexes for filtering
${specContent.keyFeatures.map(feature => 
  `CREATE INDEX idx_${feature.replace(/\s+/g, '_').toLowerCase()}_created ON ${feature.replace(/\s+/g, '_').toLowerCase()}_table(created_at);`
).join('\n')}
\`\`\`

## Migration Scripts

### Initial Migration
\`\`\`sql
-- Create all tables and indexes
-- Run migration scripts in order
-- Validate schema integrity
\`\`\`

## Data Integrity

### Constraints
- Primary key constraints on all tables
- Foreign key relationships properly defined
- NOT NULL constraints on required fields
- Check constraints for data validation

### Backup Strategy
- Daily automated backups
- Point-in-time recovery capability
- Cross-region backup replication
- Regular backup validation testing

---

*Generated using Agent OS Enhanced Create-Specs workflow*`;
  }

  /**
   * Get architecture pattern for module type
   * @private
   */
  _getArchitecturePattern(moduleName) {
    const patterns = {
      'authentication': 'Security-layered architecture with separate authentication, authorization, and session management layers',
      'payment': 'Event-sourced architecture with transaction logging and audit trails for financial compliance',
      'e-commerce': 'Microservices architecture with separated product, cart, order, and inventory services',
      'api': 'RESTful API architecture with standardized request/response patterns and middleware layers',
      'admin': 'CRUD-based architecture with role-based access control and administrative workflows',
      'ai-ml': 'Pipeline architecture with data processing, model training, and inference stages'
    };
    
    return patterns[moduleName] || 'Layered architecture with clear separation between presentation, business logic, and data access layers';
  }

  /**
   * Determine if this is a Python project that needs UV integration
   * @param {Object} specContent - Spec content
   * @returns {boolean} Whether this is a Python project
   * @private
   */
  _isPythonProject(specContent) {
    const pythonModules = [
      'authentication', 'api', 'database', 'web-scraping', 
      'data-processing', 'visualization', 'ai-ml', 'testing'
    ];
    
    const pythonKeywords = ['python', 'django', 'flask', 'fastapi', 'pandas', 'numpy', 'pytest'];
    
    // Check if module is typically Python-based
    if (pythonModules.includes(specContent.moduleName)) {
      return true;
    }
    
    // Check if summary or features mention Python technologies
    const allText = `${specContent.summary} ${specContent.keyFeatures.join(' ')}`.toLowerCase();
    return pythonKeywords.some(keyword => allText.includes(keyword));
  }
}

module.exports = {
  PromptCapture,
  ModuleIdentifier,
  ExecutiveSummaryGenerator,
  MermaidDiagramGenerator,
  TaskSummaryTemplate,
  EnhancedSpecWorkflow
};