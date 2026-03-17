````md
# Week 5 Demo

## Day 1 — Docker Fundamentals + Linux Internals

### Go to project
```bash
cd ~/Documents/obsvault/Hestabit/Week5/day-1
````

### Build image

```bash
docker build -t day-1 .
```

### Run container

```bash
docker run -d -p 3000:3000 --name day-1container day-1
```

### Show running container

```bash
docker ps
```

### Enter container

```bash
docker exec -it day-1container /bin/sh
```

### Commands inside container

```bash
ls
ps aux
```

### Show logs

```bash
docker logs day-1container
```

### What to say

* Day 1 demonstrates a Node app inside a Docker container.
* I explored the container like a Linux server using `docker exec`.
* I verified files, processes, and logs inside the container.

---

## Day 2 — Docker Compose + Multi-Container Apps

### Go to project

```bash
cd ~/Documents/obsvault/Hestabit/Week5/day-2
```

### Start stack

```bash
docker compose down -v
docker compose up -d --build
```

### Show running services

```bash
docker compose ps
```

### Show backend working

```bash
curl http://localhost:5000/api
```

### Show logs

```bash
docker compose logs server --tail 20
docker compose logs client --tail 20
docker compose logs mongo --tail 20
```

### Open frontend

```bash
xdg-open http://localhost:4000
```

### What to say

* Day 2 uses Docker Compose to run React, Node, and MongoDB together.
* The server connects to MongoDB using container networking.
* MongoDB uses a named volume for persistence.

---

## Day 3 — NGINX Reverse Proxy + Load Balancing

### Go to project

```bash
cd ~/Documents/obsvault/Hestabit/Week5/day-3
```

### Start stack

```bash
docker compose down -v
docker compose up -d --build
```

### Show running services

```bash
docker compose ps
```

### Test load balancing

```bash
curl http://localhost:8080/api
curl http://localhost:8080/api
curl http://localhost:8080/api
curl http://localhost:8080/api
```

### Show NGINX config

```bash
cat nginx/nginx.conf
```

### What to say

* Day 3 uses NGINX as a reverse proxy.
* Requests to `/api` are routed to two backend instances.
* NGINX distributes requests using round-robin load balancing.

---

## Day 4 — SSL + Self-Signed + mkcert + HTTPS

### Go to project

```bash
cd ~/Documents/obsvault/Hestabit/Week5/day-4
```

### Start stack

```bash
docker compose down -v
docker compose up -d --build
```

### Show running services

```bash
docker compose ps
```

### Show HTTP to HTTPS redirect

```bash
curl -I http://localhost:8081
```

### Show HTTPS working

```bash
curl -k https://localhost:8443
curl -k https://localhost:8443/api
```

### Open in browser

```bash
xdg-open https://localhost:8443
```

### Show certificate details

```bash
openssl x509 -in certs/localhost.pem -text -noout | grep -E "Issuer:|Subject:|DNS:|IP Address:"
```

### What to say

* Day 4 adds HTTPS termination at NGINX.
* I generated a local certificate using `mkcert`.
* HTTP redirects to HTTPS and the reverse proxy works over HTTPS.

---

## Day 5 — CI-Style Deployment Automation + Capstone

### Go to project

```bash
cd ~/Documents/obsvault/Hestabit/Week5/day-5
```

### Start production stack

```bash
docker compose -f docker-compose.prod.yml --env-file .env down
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
```

### Show running services

```bash
docker compose -f docker-compose.prod.yml --env-file .env ps
```

### Show HTTP to HTTPS redirect

```bash
curl -I http://localhost:8085
```

### Show backend API working

```bash
curl -k https://localhost:8445/api
```

### Show health endpoint

```bash
curl -k https://localhost:8445/health
```

### Open app in browser

```bash
xdg-open https://localhost:8445
```

### Show deploy script

```bash
cat deploy.sh
```

### Show production compose file

```bash
cat docker-compose.prod.yml
```

### Show environment file

```bash
cat .env
```

### What to say

* Day 5 is the capstone production-style deployment.
* It uses `.env`, healthchecks, restart policy, HTTPS, and a deployment script.
* The stack is fully working through NGINX reverse proxy with HTTPS.

---

# Full Demo Flow

## Day 1

```bash
cd ~/Documents/obsvault/Hestabit/Week5/day-1 && \
docker build -t day-1 . && \
docker run -d -p 3000:3000 --name day-1container day-1 && \
docker ps && \
docker logs day-1container
```

## Day 2

```bash
cd ~/Documents/obsvault/Hestabit/Week5/day-2 && \
docker compose down -v && \
docker compose up -d --build && \
docker compose ps && \
curl http://localhost:5000/api
```

## Day 3

```bash
cd ~/Documents/obsvault/Hestabit/Week5/day-3 && \
docker compose down -v && \
docker compose up -d --build && \
docker compose ps && \
curl http://localhost:8080/api && \
echo && \
curl http://localhost:8080/api && \
echo && \
curl http://localhost:8080/api
```

## Day 4

```bash
cd ~/Documents/obsvault/Hestabit/Week5/day-4 && \
docker compose down -v && \
docker compose up -d --build && \
docker compose ps && \
curl -I http://localhost:8081 && \
echo && \
curl -k https://localhost:8443/api
```

## Day 5

```bash
cd ~/Documents/obsvault/Hestabit/Week5/day-5 && \
docker compose -f docker-compose.prod.yml --env-file .env down && \
docker compose -f docker-compose.prod.yml --env-file .env up -d --build && \
docker compose -f docker-compose.prod.yml --env-file .env ps && \
curl -I http://localhost:8085 && \
echo && \
curl -k https://localhost:8445/api && \
echo && \
curl -k https://localhost:8445/health
```

---

# Minimal Instructor Sequence

```bash
cd ~/Documents/obsvault/Hestabit/Week5/day-1
docker ps
docker logs day-1container

cd ~/Documents/obsvault/Hestabit/Week5/day-2
docker compose ps
curl http://localhost:5000/api

cd ~/Documents/obsvault/Hestabit/Week5/day-3
docker compose ps
curl http://localhost:8080/api
curl http://localhost:8080/api

cd ~/Documents/obsvault/Hestabit/Week5/day-4
docker compose ps
curl -I http://localhost:8081
curl -k https://localhost:8443/api

cd ~/Documents/obsvault/Hestabit/Week5/day-5
docker compose -f docker-compose.prod.yml --env-file .env ps
curl -I http://localhost:8085
curl -k https://localhost:8445/api
curl -k https://localhost:8445/health
xdg-open https://localhost:8445
```

```
```
