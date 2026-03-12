
---

# `DAY5-README.md`

```md
# Day 5 — Job Queues, Logging, API Documentation, Capstone

## Overview

This project demonstrates:

- async background jobs using BullMQ
- request tracing using `X-Request-ID`
- structured logging using Winston
- log file generation
- API documentation using a Postman collection
- deployment setup using PM2 configuration
- environment setup using `.env.example`

## Deliverables

Completed deliverables:

- `src/jobs/email.job.js`
- `src/utils/tracing.js`
- `src/logs/*.log`
- `postman/day5.postman_collection.json`
- `DEPLOYMENT-NOTES.md`
- `prod/ecosystem.config.js`
- `.env.example`

---

## Project Structure

```text
day-5/
├── .env.example
├── DEPLOYMENT-NOTES.md
├── package.json
├── package-lock.json
├── postman
│   └── day5.postman_collection.json
├── prod
│   └── ecosystem.config.js
└── src
    ├── app.js
    ├── server.js
    ├── controllers
    │   └── email.controller.js
    ├── jobs
    │   └── email.job.js
    ├── logs
    │   ├── app.log
    │   └── error.log
    ├── routes
    │   └── email.routes.js
    └── utils
        ├── logger.js
        └── tracing.js
````

---

## Dependencies Used

* `express`
* `bullmq`
* `ioredis`
* `winston`
* `uuid`

Install dependencies using:

```bash
npm install
```

---

## Prerequisites

BullMQ requires Redis.

Check Redis:

```bash
redis-cli ping
```

Expected output:

```text
PONG
```

If Redis is not running, start it:

```bash
redis-server
```

---

## Environment Setup

Create a `.env` file if needed using `.env.example`.

Example values:

```env
PORT=3000
REDIS_HOST=127.0.0.1
REDIS_PORT=6379
LOG_LEVEL=info
```

---

## How to Run

Go to the Day 5 folder:

```bash
cd ~/Documents/obsvault/Hestabit/Week4/day-5
```

Start the API server:

```bash
npm start
```

Expected behavior:

* server starts on port 3000
* incoming requests are logged
* request tracing is enabled
* logs are written to log files

---

## Available Routes

### Health Check

```http
GET /api/health
```

### Queue Email Job

```http
POST /api/emails/queue
```

---

## Execution and Testing

## 1. Check API Health

Run:

```bash
curl -i http://localhost:3000/api/health
```

Expected result:

* response status `200`
* body contains success message
* response header contains `X-Request-ID`

Example:

```json
{
  "success": true,
  "message": "Day 5 API is running",
  "requestId": "..."
}
```

This proves request tracing is active.

---

## 2. Queue a Normal Email Job

Run:

```bash
curl -X POST http://localhost:3000/api/emails/queue \
  -H "Content-Type: application/json" \
  -d '{
    "email": "test@example.com",
    "subject": "Welcome",
    "message": "This is a test email job"
  }'
```

Expected response:

```json
{
  "success": true,
  "message": "Email job queued successfully",
  "requestId": "...",
  "jobId": "..."
}
```

This proves:

* API receives request
* request ID is generated
* BullMQ job is added to queue

---

## 3. Queue a Retry Test Job

Run:

```bash
curl -X POST http://localhost:3000/api/emails/queue \
  -H "Content-Type: application/json" \
  -d '{
    "email": "retry@example.com",
    "subject": "Retry test",
    "message": "Force first attempt to fail",
    "failOnce": true
  }'
```

Expected result:

* first attempt fails intentionally
* BullMQ retries the job using backoff
* logs show failure and retry behavior

This proves retry and backoff are working.

---

## 4. Check Generated Logs

Run:

```bash
ls src/logs
cat src/logs/app.log
cat src/logs/error.log
```

Expected result:

* `app.log` contains incoming request and job queue logs
* `error.log` contains worker or retry errors if any occurred

This fulfills the log deliverable.

---

## 5. Verify Request Tracing

Health route:

```bash
curl -i http://localhost:3000/api/health
```

Look for:

```text
X-Request-ID: ...
```

Queue route:

```bash
curl -X POST http://localhost:3000/api/emails/queue \
  -H "Content-Type: application/json" \
  -d '{"email":"trace@example.com","subject":"Trace","message":"Trace test"}'
```

Then inspect logs:

```bash
cat src/logs/app.log
```

Expected result:

* same request ID appears in response and logs

This proves request tracing and log grouping are implemented.

---

## 6. PM2 Deployment Test

Run from Day 5 folder:

```bash
pm2 start prod/ecosystem.config.js
pm2 list
```

If PM2 is not installed globally, use:

```bash
npx pm2 start prod/ecosystem.config.js
npx pm2 list
```

Expected result:

* PM2 starts the Day 5 app using the provided config

This proves deployment configuration is ready.

---

## 7. Postman Collection

Collection file:

```text
postman/day5.postman_collection.json
```

It includes:

* health check
* queue email job
* retry test job

The collection uses:

```text
{{baseUrl}}
```

Default value:

```text
http://localhost:3000
```

This fulfills the API documentation deliverable.

---

## What to Show in Demo

Use this sequence during demonstration:

### 1. Show project structure

```bash
tree -L 3 -I "node_modules"
```

### 2. Show Redis is running

```bash
redis-cli ping
```

### 3. Start server

```bash
npm start
```

### 4. Show health check with tracing

```bash
curl -i http://localhost:3000/api/health
```

### 5. Queue normal email job

```bash
curl -X POST http://localhost:3000/api/emails/queue \
  -H "Content-Type: application/json" \
  -d '{"email":"test@example.com","subject":"Welcome","message":"This is a test email job"}'
```

### 6. Queue retry test job

```bash
curl -X POST http://localhost:3000/api/emails/queue \
  -H "Content-Type: application/json" \
  -d '{"email":"retry@example.com","subject":"Retry test","message":"Force first attempt to fail","failOnce":true}'
```

### 7. Show log files

```bash
cat src/logs/app.log
cat src/logs/error.log
```

### 8. Show deployment files

Open:

* `DEPLOYMENT-NOTES.md`
* `prod/ecosystem.config.js`
* `.env.example`

### 9. Show Postman collection

Open:

* `postman/day5.postman_collection.json`

---

## Notes

* This project uses a simulated email worker for queue demonstration.
* Actual SMTP integration is not required for this deliverable.
* The focus is on queue design, retry/backoff, tracing, logging, and deploy-readiness.

---

## Conclusion

Day 5 demonstrates:

* background job processing
* structured logging
* request tracing
* deploy-ready configuration
* API documentation support

This fulfills the Day 5 deliverables and execution requirements.

````

---

## Fast way to create them

From wherever you want these files saved:

```bash
cat > DAY4-README.md <<'EOF'
PASTE DAY 4 CONTENT HERE
EOF

cat > DAY5-README.md <<'EOF'
PASTE DAY 5 CONTENT HERE
EOF
````

If you want, I can also turn these into the exact filenames you should place inside your folders, like:

* `Hestabit/Week4/day-4/README.md`
* `Hestabit/Week4/day-5/README.md`

with the command blocks ready to paste.
