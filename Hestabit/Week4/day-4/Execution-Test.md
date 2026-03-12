Absolutely. Here are two clean Markdown files you can use directly:

* `DAY4-README.md`
* `DAY5-README.md`

They focus on **how to run, test, and demonstrate** the deliverables.

---

# `DAY4-README.md`

````md
# Day 4 — Security, Validation, Rate Limiting, Hardening

## Overview

This project demonstrates backend API hardening using:

- request validation
- security headers
- CORS
- rate limiting
- NoSQL injection sanitization
- XSS sanitization
- HTTP parameter pollution protection
- payload size limits

## Deliverables

Completed deliverables:

- `src/middlewares/validate.js`
- `src/middlewares/security.js`
- `SECURITY-REPORT.md`

---

## Project Structure

```text
day-4/
├── package.json
├── package-lock.json
├── SECURITY-REPORT.md
└── src
    ├── app.js
    ├── server.js
    ├── middlewares
    │   ├── security.js
    │   └── validate.js
    └── routes
        └── test.routes.js
````

---

## Dependencies Used

* `express`
* `helmet`
* `cors`
* `express-rate-limit`
* `zod`
* `hpp`
* `express-mongo-sanitize`
* `xss-clean`

Install dependencies using:

```bash
npm install
```

---

## How to Run

Go to the Day 4 folder:

```bash
cd ~/Documents/obsvault/Hestabit/Week4/day-4
```

Start the server:

```bash
npm start
```

Expected output:

```text
Day 4 server running on port 3000
```

---

## Available Routes

### Health Check

```http
GET /api/health
```

### Validate User Payload

```http
POST /api/users
```

### Validate Product Payload

```http
POST /api/products
```

---

## Execution and Testing

## 1. Health Check

Run:

```bash
curl http://localhost:3000/api/health
```

Expected response:

```json
{
  "success": true,
  "message": "Day 4 security module is running"
}
```

---

## 2. Test Valid User Request

Run:

```bash
curl -X POST http://localhost:3000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "Anshul",
    "lastName": "Garg",
    "email": "anshul@example.com",
    "password": "secret123",
    "status": "active"
  }'
```

Expected response:

```json
{
  "success": true,
  "message": "User payload validated successfully",
  "data": {
    "firstName": "Anshul",
    "lastName": "Garg",
    "email": "anshul@example.com",
    "password": "secret123",
    "status": "active"
  }
}
```

---

## 3. Test Invalid User Request

Run:

```bash
curl -X POST http://localhost:3000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "A",
    "lastName": "",
    "email": "wrong-email",
    "password": "123"
  }'
```

Expected response:

```json
{
  "success": false,
  "message": "Validation failed",
  "code": "VALIDATION_ERROR"
}
```

This proves request validation is working.

---

## 4. Test Valid Product Request

Run:

```bash
curl -X POST http://localhost:3000/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "iPhone 15",
    "description": "Premium smartphone",
    "price": 79999,
    "category": "electronics",
    "tags": ["apple", "phone"],
    "rating": 4.7,
    "status": "active"
  }'
```

Expected response:

```json
{
  "success": true,
  "message": "Product payload validated successfully"
}
```

---

## 5. Test NoSQL Injection Prevention

Run:

```bash
curl -X POST http://localhost:3000/api/users \
  -H "Content-Type: application/json" \
  -d '{
    "firstName": "Anshul",
    "lastName": "Garg",
    "email": {"$gt": ""},
    "password": "secret123"
  }'
```

Expected result:

* request should fail
* unsafe Mongo operator input should not be accepted

---

## 6. Test XSS Handling

Run:

```bash
curl -X POST http://localhost:3000/api/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "<script>alert(1)</script>",
    "description": "<img src=x onerror=alert(1)>",
    "price": 1000,
    "category": "electronics"
  }'
```

Expected result:

* request is sanitized or safely handled
* no trusted script execution path is accepted

---

## 7. Test Parameter Pollution Protection

Run:

```bash
curl "http://localhost:3000/api/health?role=user&role=admin"
```

Expected result:

* duplicate query parameter abuse is mitigated by `hpp`

---

## 8. Test Rate Limiting

Run:

```bash
for i in {1..105}; do curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000/api/health; done
```

Expected result:

* after enough requests, server returns `429`

This proves rate limiting works.

---

## 9. Test Payload Size Limit

Run:

```bash
python3 - <<'PY'
import requests
big_text = "a" * 15000
resp = requests.post(
    "http://localhost:3000/api/products",
    json={
        "name": "Phone",
        "description": big_text,
        "price": 1000,
        "category": "electronics"
    }
)
print(resp.status_code)
print(resp.text)
PY
```

Expected result:

* oversized payload is rejected

---

## What to Show in Demo

Use this sequence during demonstration:

### 1. Show project structure

```bash
tree -L 3 -I "node_modules"
```

### 2. Start server

```bash
npm start
```

### 3. Show health route

```bash
curl http://localhost:3000/api/health
```

### 4. Show valid request

```bash
curl -X POST http://localhost:3000/api/users \
  -H "Content-Type: application/json" \
  -d '{"firstName":"Anshul","lastName":"Garg","email":"anshul@example.com","password":"secret123"}'
```

### 5. Show invalid request

```bash
curl -X POST http://localhost:3000/api/users \
  -H "Content-Type: application/json" \
  -d '{"firstName":"A","lastName":"","email":"wrong","password":"123"}'
```

### 6. Show rate limiting

```bash
for i in {1..105}; do curl -s -o /dev/null -w "%{http_code}\n" http://localhost:3000/api/health; done
```

### 7. Open `SECURITY-REPORT.md`

This shows manual security testing and results.

---

## Conclusion

Day 4 demonstrates:

* request validation
* secure middleware setup
* input sanitization
* rate limiting
* API hardening

This fulfills the Day 4 deliverables and execution requirements.

````
