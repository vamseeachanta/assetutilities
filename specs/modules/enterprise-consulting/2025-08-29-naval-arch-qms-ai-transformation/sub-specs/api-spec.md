# API Specification

This is the API specification for the spec detailed in @.agent-os/specs/2025-08-29-naval-arch-qms-ai-transformation/spec.md

> Created: 2025-08-29
> Version: 1.0.0

## Core QMS APIs

### Document Management Endpoints

#### POST /api/v1/documents/upload
**Purpose:** Upload new documents with automatic classification and metadata extraction
**Parameters:** 
- file: multipart/form-data (required)
- projectId: string (required)
- documentType: string (optional)
- tags: array[string] (optional)
**Response:** 
```json
{
  "documentId": "uuid",
  "classification": "technical-drawing|report|correspondence",
  "extractedMetadata": {
    "title": "string",
    "author": "string",
    "projectPhase": "string",
    "discipline": "string"
  },
  "suggestedLocation": "path/to/folder",
  "complianceStatus": "compliant|non-compliant|review-required"
}
```
**Errors:** 400 (invalid file), 413 (file too large), 500 (processing error)

#### GET /api/v1/documents/search
**Purpose:** Intelligent search across all project documents
**Parameters:**
- query: string (required)
- projectId: string (optional)
- dateRange: {from: date, to: date} (optional)
- documentType: string (optional)
- limit: integer (default: 50)
**Response:** 
```json
{
  "results": [{
    "documentId": "uuid",
    "title": "string",
    "relevanceScore": 0.95,
    "snippet": "...matching text...",
    "metadata": {}
  }],
  "totalCount": 150,
  "facets": {
    "documentTypes": {},
    "projects": {},
    "authors": {}
  }
}
```
**Errors:** 400 (invalid query), 429 (rate limit)

### Project Management Endpoints

#### GET /api/v1/projects/{projectId}/dashboard
**Purpose:** Real-time project status with AI-generated insights
**Parameters:** 
- projectId: string (required)
- includeForecasts: boolean (default: true)
**Response:**
```json
{
  "projectId": "string",
  "status": "on-track|at-risk|delayed",
  "completion": 65,
  "milestones": [{
    "name": "string",
    "dueDate": "date",
    "status": "string",
    "riskLevel": "low|medium|high"
  }],
  "aiInsights": {
    "predictedCompletion": "date",
    "riskFactors": ["string"],
    "recommendations": ["string"]
  },
  "resources": {
    "utilization": 85,
    "bottlenecks": ["string"]
  }
}
```
**Errors:** 404 (project not found), 403 (unauthorized)

#### POST /api/v1/projects/{projectId}/quality-gate
**Purpose:** Submit work for quality gate approval
**Parameters:**
- projectId: string (required)
- gateId: string (required)
- documents: array[documentId] (required)
- comments: string (optional)
**Response:**
```json
{
  "submissionId": "uuid",
  "status": "pending|approved|rejected",
  "reviewers": ["string"],
  "estimatedReviewTime": "2 hours",
  "complianceCheck": {
    "passed": true,
    "issues": []
  }
}
```
**Errors:** 400 (missing documents), 409 (gate already passed)

## AI Service APIs

### Design Generation Endpoints

#### POST /api/v1/ai/hull-generation
**Purpose:** Generate parametric hull form based on requirements
**Parameters:**
```json
{
  "vesselType": "tanker|container|bulk-carrier|passenger",
  "length": 250.0,
  "beam": 40.0,
  "draft": 15.0,
  "speed": 18.5,
  "dwt": 50000,
  "optimizationGoals": ["fuel-efficiency", "cargo-capacity"],
  "constraints": {
    "maxDraft": 16.0,
    "portRestrictions": ["string"]
  }
}
```
**Response:**
```json
{
  "generationId": "uuid",
  "hullForms": [{
    "modelId": "uuid",
    "performance": {
      "resistance": 1250.5,
      "stability": "compliant",
      "capacity": 55000
    },
    "downloadUrl": "string",
    "format": "iges|step|obj"
  }],
  "optimizationReport": "url",
  "processingTime": 45.2
}
```
**Errors:** 400 (invalid parameters), 503 (AI service unavailable)

#### POST /api/v1/ai/compliance-check
**Purpose:** Automated regulatory compliance verification
**Parameters:**
```json
{
  "designId": "uuid",
  "regulations": ["IMO", "DNV-GL", "ABS"],
  "vesselClass": "string",
  "operatingRegion": "string"
}
```
**Response:**
```json
{
  "complianceId": "uuid",
  "overallStatus": "compliant|non-compliant|conditional",
  "details": [{
    "regulation": "IMO MARPOL Annex I",
    "status": "compliant",
    "checkedItems": 45,
    "issues": [],
    "recommendations": []
  }],
  "certificateReady": true,
  "documentationRequired": ["string"]
}
```
**Errors:** 404 (design not found), 422 (unsupported regulation)

### Analysis Automation Endpoints

#### POST /api/v1/ai/stability-analysis
**Purpose:** Automated intact and damage stability calculations
**Parameters:**
```json
{
  "modelId": "uuid",
  "loadingConditions": [{
    "name": "Full Load Departure",
    "weights": [{}],
    "tanks": [{}]
  }],
  "damageScenarios": ["standard", "enhanced"],
  "regulations": ["IMO"]
}
```
**Response:**
```json
{
  "analysisId": "uuid",
  "results": {
    "intact": {
      "gm": 2.45,
      "gmRequired": 1.50,
      "status": "pass",
      "criteria": [{}]
    },
    "damage": {
      "survivability": "compliant",
      "scenarios": [{}]
    }
  },
  "report": "url",
  "visualizations": ["url"]
}
```
**Errors:** 400 (invalid model), 504 (analysis timeout)

### Knowledge Management Endpoints

#### GET /api/v1/ai/similar-projects
**Purpose:** Find similar past projects using AI matching
**Parameters:**
- vesselType: string (required)
- specifications: object (required)
- limit: integer (default: 5)
**Response:**
```json
{
  "similarProjects": [{
    "projectId": "string",
    "similarity": 0.89,
    "vesselName": "string",
    "keySpecs": {},
    "lessonsLearned": ["string"],
    "performance": {
      "budget": "on-target",
      "schedule": "delayed-10%"
    }
  }]
}
```
**Errors:** 404 (no similar projects found)

#### POST /api/v1/ai/extract-lessons
**Purpose:** Extract lessons learned from project documents
**Parameters:**
- projectId: string (required)
- documentIds: array[string] (optional)
**Response:**
```json
{
  "extractionId": "uuid",
  "lessons": [{
    "category": "design|construction|testing",
    "lesson": "string",
    "impact": "high|medium|low",
    "applicability": ["vessel-types"],
    "source": "documentId"
  }],
  "recommendations": ["string"],
  "addedToKnowledgeBase": true
}
```
**Errors:** 404 (project not found), 500 (extraction failed)

## Integration APIs

### CAD System Integration

#### POST /api/v1/integration/cad/sync
**Purpose:** Synchronize design data from CAD systems
**Parameters:**
```json
{
  "system": "napa|rhino|autocad",
  "projectId": "string",
  "modelPath": "string",
  "syncType": "full|incremental"
}
```
**Response:**
```json
{
  "syncId": "uuid",
  "status": "completed|in-progress|failed",
  "itemsSynced": 145,
  "conflicts": [],
  "lastSync": "timestamp"
}
```
**Errors:** 401 (authentication failed), 503 (CAD system unavailable)

### Classification Society Integration

#### POST /api/v1/integration/class/submit
**Purpose:** Submit designs for classification society review
**Parameters:**
```json
{
  "society": "dnv|abs|lr|bv",
  "projectId": "string",
  "submissionType": "preliminary|final",
  "documents": ["documentId"]
}
```
**Response:**
```json
{
  "submissionId": "uuid",
  "societyReference": "string",
  "status": "submitted|under-review|approved|rejected",
  "expectedResponse": "date",
  "trackingUrl": "string"
}
```
**Errors:** 400 (missing required documents), 503 (society system unavailable)

## Authentication and Security

All API endpoints require authentication via JWT tokens:
```
Authorization: Bearer <token>
```

Rate limiting:
- Standard tier: 100 requests/minute
- Premium tier: 1000 requests/minute
- AI endpoints: 10 requests/minute

Response headers include:
- X-RateLimit-Limit
- X-RateLimit-Remaining
- X-RateLimit-Reset

## Webhook Events

The system can send webhooks for various events:

```json
{
  "event": "document.uploaded|project.milestone|quality.gate|ai.complete",
  "timestamp": "ISO-8601",
  "data": {
    "projectId": "string",
    "userId": "string",
    "details": {}
  }
}
```

Webhook configuration via:
POST /api/v1/webhooks/subscribe