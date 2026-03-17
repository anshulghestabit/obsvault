#!/usr/bin/env bash
set -e

echo "Stopping old stack..."
docker compose -f docker-compose.prod.yml --env-file .env down

echo "Building and starting production stack..."
docker compose -f docker-compose.prod.yml --env-file .env up -d --build

echo "Running containers:"
docker compose -f docker-compose.prod.yml --env-file .env ps