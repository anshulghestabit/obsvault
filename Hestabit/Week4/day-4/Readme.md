# Security Report

## Overview

This project implements security and validation controls for Day 4 requirements.

Implemented deliverables:

- `middlewares/validate.js`
- `middlewares/security.js`
- `SECURITY-REPORT.md`

Security controls added:

- Helmet security headers
- CORS policy
- Rate limiting
- Payload size limits
- NoSQL injection sanitization
- XSS sanitization
- HTTP parameter pollution protection
- Request body validation using Zod

---

## Files

### `middlewares/validate.js`
Implements request validation for:
- User payload
- Product payload

Validation includes:
- required fields
- email format checking
- password length
- numeric constraints
- enum validation
- string trimming and lowercase transformation

### `middlewares/security.js`
Implements:
- `helmet()`
- `cors()`
- `express-rate-limit`
- `express.json({ limit: '10kb' })`
- `express-mongo-sanitize`
- `xss-clean`
- `hpp()`

---

## Vulnerabilities Tested and Results

### 1. NoSQL Injection
#### Test
Sent payload containing MongoDB operators such as:

```json
{
  "email": { "$gt": "" }
}