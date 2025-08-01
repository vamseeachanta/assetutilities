# API Specification

> **Module:** authentication
> **Sub-Agent:** security-authentication
> **AI Context:** API endpoints for user-auth-system

This is the API specification for the spec detailed in @specs/modules/authentication/user-auth-system/spec.md

> Created: 2025-08-01
> Version: 1.0.0

## API Overview

```mermaid
sequenceDiagram
    participant Client
    participant AuthAPI as Authentication API
    participant AuthService as Auth Service
    participant Database
    participant EmailService as Email Service
    
    Client->>AuthAPI: POST /api/auth/register
    AuthAPI->>AuthService: Register user
    AuthService->>Database: Store user
    AuthService->>EmailService: Send verification
    AuthAPI-->>Client: {success, message}
    
    Client->>AuthAPI: GET /api/auth/verify/:token
    AuthAPI->>AuthService: Verify email
    AuthService->>Database: Update verification status
    AuthAPI-->>Client: {success, redirect}
    
    Client->>AuthAPI: POST /api/auth/login
    AuthAPI->>AuthService: Authenticate
    AuthService->>Database: Validate credentials
    AuthAPI-->>Client: {token, user}
```

## Authentication Endpoints

### POST /api/auth/register

**Purpose:** Register a new user account with email verification
**Authentication:** None required

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123",
  "firstName": "John",
  "lastName": "Doe"
}
```

**Response (201 Created):**
```json
{
  "success": true,
  "message": "Registration successful. Please check your email to verify your account.",
  "userId": 123
}
```

**Errors:**
- `400 Bad Request`: Invalid email format or password requirements
- `409 Conflict`: Email already registered
- `500 Internal Server Error`: Server error during registration

### POST /api/auth/login

**Purpose:** Authenticate user and create session
**Authentication:** None required

**Request Body:**
```json
{
  "email": "user@example.com",
  "password": "securePassword123"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
  "user": {
    "id": 123,
    "email": "user@example.com",
    "emailVerified": true,
    "profile": {
      "firstName": "John",
      "lastName": "Doe"
    }
  },
  "expiresAt": "2025-08-02T10:00:00Z"
}
```

**Errors:**
- `400 Bad Request`: Missing email or password
- `401 Unauthorized`: Invalid credentials
- `403 Forbidden`: Account not verified
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error during authentication

### POST /api/auth/logout

**Purpose:** Invalidate user session
**Authentication:** Bearer token required

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Logged out successfully"
}
```

**Errors:**
- `401 Unauthorized`: Invalid or expired token
- `500 Internal Server Error`: Server error during logout

### GET /api/auth/verify/:token

**Purpose:** Verify user email address
**Authentication:** None required

**Parameters:**
- `token`: Email verification token from registration email

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Email verified successfully",
  "redirectUrl": "/login"
}
```

**Errors:**
- `400 Bad Request`: Invalid token format
- `404 Not Found`: Token not found or expired
- `410 Gone`: Token already used
- `500 Internal Server Error`: Server error during verification

## Password Reset Endpoints

### POST /api/auth/forgot-password

**Purpose:** Request password reset email
**Authentication:** None required

**Request Body:**
```json
{
  "email": "user@example.com"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "If an account with that email exists, a password reset link has been sent."
}
```

**Note:** Returns success even for non-existent emails to prevent email enumeration

**Errors:**
- `400 Bad Request`: Invalid email format
- `429 Too Many Requests`: Rate limit exceeded
- `500 Internal Server Error`: Server error

### POST /api/auth/reset-password

**Purpose:** Reset password using reset token
**Authentication:** None required

**Request Body:**
```json
{
  "token": "reset-token-from-email",
  "newPassword": "newSecurePassword123"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Password reset successfully"
}
```

**Errors:**
- `400 Bad Request`: Invalid token or password requirements not met
- `404 Not Found`: Token not found or expired
- `410 Gone`: Token already used
- `500 Internal Server Error`: Server error

## Profile Management Endpoints

### GET /api/auth/profile

**Purpose:** Get current user profile
**Authentication:** Bearer token required

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Response (200 OK):**
```json
{
  "success": true,
  "user": {
    "id": 123,
    "email": "user@example.com",
    "emailVerified": true,
    "profile": {
      "firstName": "John",
      "lastName": "Doe",
      "bio": "Software developer"
    },
    "createdAt": "2025-07-01T10:00:00Z",
    "updatedAt": "2025-08-01T15:30:00Z"
  }
}
```

**Errors:**
- `401 Unauthorized`: Invalid or expired token
- `500 Internal Server Error`: Server error

### PUT /api/auth/profile

**Purpose:** Update user profile
**Authentication:** Bearer token required

**Headers:**
```
Authorization: Bearer eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...
```

**Request Body:**
```json
{
  "firstName": "John",
  "lastName": "Smith",
  "bio": "Senior software developer"
}
```

**Response (200 OK):**
```json
{
  "success": true,
  "message": "Profile updated successfully",
  "user": {
    "id": 123,
    "email": "user@example.com",
    "profile": {
      "firstName": "John",
      "lastName": "Smith",
      "bio": "Senior software developer"
    },
    "updatedAt": "2025-08-01T16:00:00Z"
  }
}
```

**Errors:**
- `400 Bad Request`: Invalid profile data
- `401 Unauthorized`: Invalid or expired token
- `500 Internal Server Error`: Server error

## Rate Limiting

### Authentication Endpoints
- **Registration:** 5 requests per hour per IP
- **Login:** 5 failed attempts per 15 minutes per IP
- **Password Reset:** 3 requests per hour per IP

### Rate Limit Headers
```
X-RateLimit-Limit: 5
X-RateLimit-Remaining: 4
X-RateLimit-Reset: 1625097600
```

### Rate Limit Exceeded Response (429)
```json
{
  "error": "Rate limit exceeded",
  "message": "Too many requests. Please try again later.",
  "retryAfter": 900
}
```

## Security Headers

All API responses include security headers:
```
Content-Type: application/json
X-Content-Type-Options: nosniff
X-Frame-Options: DENY
X-XSS-Protection: 1; mode=block
Strict-Transport-Security: max-age=31536000; includeSubDomains
```

## Error Response Format

Standard error response structure:
```json
{
  "error": "error_code",
  "message": "Human-readable error message",
  "details": {
    "field": "Specific field error message"
  },
  "timestamp": "2025-08-01T10:00:00Z",
  "path": "/api/auth/login"
}
```

## Authentication Middleware

### JWT Token Validation
- **Header Format:** `Authorization: Bearer <token>`
- **Token Expiration:** 24 hours
- **Token Refresh:** Not implemented (future enhancement)
- **Token Blacklisting:** Logout adds token to blacklist

### Protected Route Example
```javascript
// Middleware usage
app.get('/api/auth/profile', authenticateToken, getUserProfile);

function authenticateToken(req, res, next) {
  const authHeader = req.headers['authorization'];
  const token = authHeader && authHeader.split(' ')[1];
  
  if (!token) {
    return res.status(401).json({ error: 'Access token required' });
  }
  
  jwt.verify(token, process.env.JWT_SECRET, (err, user) => {
    if (err) {
      return res.status(403).json({ error: 'Invalid or expired token' });
    }
    req.user = user;
    next();
  });
}
```