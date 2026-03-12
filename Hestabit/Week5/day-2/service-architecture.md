# Service Architecture

## Overview
This project uses Docker Compose to run a multi-container application with three services:

- **client** → React frontend
- **server** → Node.js backend API
- **mongo** → MongoDB database

## Services

### Client
The client is a React application exposed on port `3000`.

### Server
The server is a Node.js application exposed on port `5000`.
It connects to MongoDB using the connection string:

`mongodb://mongo:27017/mydb`

### MongoDB
MongoDB runs in its own container using the official `mongo:6` image.

## Networking
Docker Compose creates a default shared network for all services.
Because of this, the server connects to MongoDB using the service name `mongo` as the hostname.

## Volumes
A named volume `mongo-data` is mounted to:

`/data/db`

This ensures MongoDB data persists across container restarts.

## Logs
Logs can be viewed using:

```bash
docker compose logs
docker compose logs client
docker compose logs server
docker compose logs mongo