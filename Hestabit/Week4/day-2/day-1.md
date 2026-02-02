# WEEK 4 — ADVANCED BACKEND ENGINEERING
(Node.js + Express + MongoDB + API Architecture + Security + Scalability)

### WEEK 4 ADVANCED OBJECTIVES
Interns will learn:
* Professional backend architecture
* Clean, layered API design (Controller → Service → Repository → Model)
* Database modeling with indexing + performance tuning
* Security + sanitization + rate limiting
* Error boundaries + global exception handling
* Logging, monitoring & request tracing
* Async job queues
* Real-world API documentation & Postman Collections

---

# DAY 1 — NODE + PROJECT ARCHITECTURE

### Learning Outcomes:
* Node internals
* Layered architecture
* Config management
* Professional folder structure

### Mandatory Folder Structure (No shortcuts)
```text
src/
  config/
  loaders/
  models/
  routes/
  controllers/
  services/
  repositories/
  middlewares/
  utils/
  jobs/
  logs/
```

### Topics to Learn
* Event loop phases
* Node clustering
* Config loader + environment isolation
* Express advanced bootstrapping

### Exercise (Hard)
Build:
1. **App loader** (loads Express, middlewares, DB, routes in order)
2. **Config loader** supporting: `.env.local`, `.env.dev`, `.env.prod`
3. **Startup logs** using Winston/Pino

### Deliverables:
* `/src/loaders/app.js`
* `/src/loaders/db.js`
* `/src/utils/logger.js`
* `ARCHITECTURE.md`
