# Service Architecture

## Overview
This application is deployed using Docker Compose and consists of three containerized services.

## Services
- Client: React application running inside a Docker container on port 3000
- Server: Node.js API running inside a Docker container on port 5000
- Database: MongoDB container for data persistence

## Networking
Docker Compose creates a shared network for all services.
The server connects to MongoDB using the hostname `mongo`.

## Volumes
MongoDB uses a named volume (mongo-data) to persist data across container restarts.

## Startup
All services are started together using `docker compose up -d`.
Service dependencies are defined using `depends_on`.

