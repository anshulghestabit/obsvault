````md
# Day 5 Demo

## Go to project
```bash
cd ~/Documents/obsvault/Hestabit/Week5/day-5
````

## Start production stack

```bash
docker compose -f docker-compose.prod.yml --env-file .env down
docker compose -f docker-compose.prod.yml --env-file .env up -d --build
```

## Show running containers

```bash
docker compose -f docker-compose.prod.yml --env-file .env ps
```

## Show HTTP to HTTPS redirect

```bash
curl -I http://localhost:8085
```

## Show backend API working

```bash
curl -k https://localhost:8445/api
```

## Show health endpoint working

```bash
curl -k https://localhost:8445/health
```

## Open app in browser

```bash
xdg-open https://localhost:8445
```

## Show logs

```bash
docker compose -f docker-compose.prod.yml --env-file .env logs --tail 20
```

## Show deploy script

```bash
cat deploy.sh
```

## Show nginx config

```bash
cat nginx/nginx.conf
```

## Show production compose file

```bash
cat docker-compose.prod.yml
```

## Show environment file

```bash
cat .env
```

## Full instant demo sequence

```bash
cd ~/Documents/obsvault/Hestabit/Week5/day-5 && \
docker compose -f docker-compose.prod.yml --env-file .env down && \
docker compose -f docker-compose.prod.yml --env-file .env up -d --build && \
docker compose -f docker-compose.prod.yml --env-file .env ps && \
curl -I http://localhost:8085 && \
echo && \
curl -k https://localhost:8445/api && \
echo && \
curl -k https://localhost:8445/health && \
echo && \
xdg-open https://localhost:8445
```

## What to say during demo

* This is the Day 5 production-style Docker deployment.
* I am using `docker-compose.prod.yml` with `.env`.
* The stack has frontend, backend, and NGINX reverse proxy with HTTPS.
* HTTP redirects to HTTPS.
* Healthchecks are configured.
* Restart policy is configured.
* Deployment is automated using `deploy.sh`.
* The app is working end-to-end in the browser and through API checks.

```
```
