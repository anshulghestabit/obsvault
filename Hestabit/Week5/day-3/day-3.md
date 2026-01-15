# DAY 3 — NGINX Reverse Proxy + Load Balancing

### Topics
* NGINX inside Docker
* Routing to internal containers
* Multiple backend replicas

### Exercise
* Run **two instances** of backend
* Use NGINX as reverse proxy: `/api` → `backend-service:3000`
* Enable round-robin load balancing

### Output
* `nginx.conf`
* `reverse-proxy-readme.md`
