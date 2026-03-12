cat > DEPLOYMENT-NOTES.md <<'EOF'
# Deployment Notes

## Overview

This Day 5 project includes:

- background email queue using BullMQ
- request tracing using `X-Request-ID`
- structured logging using Winston
- Postman collection for API testing
- deploy-ready PM2 configuration
- `.env.example` for environment setup

---

## Prerequisites

- Node.js installed
- npm installed
- Redis installed and running

---

## Install Dependencies

```bash
npm install