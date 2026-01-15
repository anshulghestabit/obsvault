-- ==========================================
-- HELPER FUNCTIONS
-- ==========================================

local function create_dir(path)
    local cmd
    if package.config:sub(1,1) == "\\" then
        cmd = 'if not exist "' .. path .. '" mkdir "' .. path .. '"'
    else
        cmd = 'mkdir -p "' .. path .. '"'
    end
    os.execute(cmd)
end

local function write_file(path, content)
    local file = io.open(path, "w")
    if file then
        file:write(content)
        file:close()
    else
        print("Error writing file: " .. path)
    end
end

-- ==========================================
-- WEEK 2 CONTENT (Frontend Fundamentals)
-- ==========================================

local w2_day1 = [[
# Week 2 — Frontend Fundamentals (HTML + CSS + JavaScript)

### Objective:
Enable you to build responsive UI layouts and manipulate DOM with JavaScript using ES6 concepts.

### Week-2 Topics

**HTML**
* Semantic HTML5 structure
* `<header>` `<footer>` `<nav>` `<main>` `<section>` `<article>`
* Forms, validation, accessibility basics
* `<canvas>` & media (`video`, `audio`)

**CSS / Styling**
* CSS Selectors (attribute, sibling, nth-child)
* Box model, specificity, units (`rem`, `vw`, `vh`)
* Flexbox, Grid (2D layouts)
* Responsive design (mobile-first, media queries)
* Animations, transitions

**JavaScript (ES6+)**
* Variables `let` vs `const`
* Arrays/objects (`map`, `filter`, `reduce`)
* Arrow functions / destructuring / spread operator
* DOM manipulation
* Event listeners
* Modular JS: splitting code into functions/modules

---

# DAY 1 – HTML5 + Semantic Layout

### Learning Outcomes:
* Understand page structure
* Master semantic tags and responsive layout scaffolding

### Topic & Activity
| Topic | Activity |
| :--- | :--- |
| **HTML Fundamentals** | tags / structure / metadata |
| **Semantic HTML5** | Build semantic layout (no `<div>` allowed) |
| **Forms & media** | Build form (input, select, validation) and embed media |
| **Accessibility** | ARIA labels, alt text, tab index |
| **Documentation** | Write README with learnings |

### Exercise:
Build a **Blog Page** using only semantic HTML, no CSS.
**Image for reference:**
https://designhooks.com/wp-content/uploads/2020/05/full-template-551-stand-blog-scaled.jpg

### Deliverable:
`blog.html`
]]

local w2_day2 = [[
# DAY 2 – CSS Layout Mastery (Flexbox + Grid)

### Learning Outcomes:
* Modern responsive layout using Flexbox & CSS Grid

### Topic & Activity
| Topic | Activity |
| :--- | :--- |
| **CSS Selectors & Specificity** | selector challenges |
| **Flexbox** | Build navbar + hero section |
| **CSS Grid** | Product grid layout (2/3/4 col based on width) |
| **Responsive approach** | Convert desktop → mobile-first |

### Exercise:
Replicate a **UI screenshot given by mentor** using Flex/Grid.
**Image for Reference:**
https://cdn.mos.cms.futurecdn.net/gnvkfwLFzB7yGtbTjzqURA.jpg

### Deliverable:
`index.html` + `style.css` + screenshots of comparison
]]

local w2_day3 = [[
# DAY 3 – JavaScript ES6 + DOM Manipulation

### Learning Outcomes:
* Modern JS (ES6) + manipulating DOM without frameworks

### Topic & Activity
| Topic | Activity |
| :--- | :--- |
| **Variables/functions** | `let`/`const`, arrow functions |
| **Arrays/objects** | `map`, `filter`, `reduce` mini-challenges |
| **DOM manipulation** | build navbar toggle, dropdown, modal |
| **Event listeners** | build counter + key events |

### Exercise:
Build an **interactive FAQ accordion** using JS (click to expand).
**Reference:**
https://codeconvey.com/wp-content/uploads/2020/02/responsive-accordion-pure-css.png.webp

### Deliverable:
`/js-dom-practice/*`
]]

local w2_day4 = [[
# DAY 4 – JS Utilities + LocalStorage Mini-Project

### Learning Outcomes:
* Modular JS functions
* LocalStorage persistence

### Topic & Activity
| Topic | Activity |
| :--- | :--- |
| **Debugging DevTools** | breakpoints, watch |
| **Custom JS utilities** | `debounce`, `throttle`, `groupBy` |
| **LocalStorage project** | Build Todo app (persist on refresh) |
| **Error handling** | try/catch + error boundary folder (`logs/errors.md`) |

### Exercise:
Build **Todo App with LocalStorage persistence**
(Add → Edit → Delete → Persist after refresh)

### Deliverable:
`todo-app/`
]]

local w2_day5 = [[
# DAY 5 – Capstone UI + JS Project

### Learning Outcomes:
Combine everything from HTML + CSS + JS into a working UI

### Project: Build a mini “E-commerce product listing page”

**Requirements:**
* Use fetch API: `https://dummyjson.com/products`
* Display product cards (title, image, price)
* Search bar (filter products)
* Sort (high → low price)
* Mobile responsive layout

**Image for Reference:**
https://codehim.com/wp-content/uploads/2021/09/bootstrap-5-ecommerce-product-list-navbar-and-hover-effects.png

### Activity & Output
| Activity | Output |
| :--- | :--- |
| **Project setup** | folder + planning |
| **UI using HTML + CSS** | skeleton ready |
| **JS fetch + rendering + search** | functional UI |
| **Final touches** | proper layout |

### Deliverables:
* Repo: `week2-frontend`
* Pages inside repo:
  * `/index.html`
  * `/products.html`
* README containing **screenshots + what you learned**
]]

-- ==========================================
-- WEEK 3 CONTENT (Next.js + Tailwind)
-- ==========================================

local w3_intro = [[
# Week 3: Advance Frontend (Next.js + TailwindCSS)

### Objective:
Train interns to build modern, production-grade frontends using:
* Next.js fundamentals (App Router / Pages / Routing / Layouts / Image optimization / SSR vs CSR basics)
* TailwindCSS (utility-first design + responsive components + reusable design system)

### Week-3 Topics

**Next.js Fundamentals**
* File-based routing
* `app/` directory structure (Next 15+)
* Layouts & nested layouts
* Page navigation (`Link`, `useRouter`)
* Static vs client components (`"use client"`)
* Image optimization (`next/image`)
* Fonts optimization (`next/font`)
* Metadata & SEO tags (`<Head />` or `metadata` config)

**TailwindCSS Fundamentals + Design System**
* Utility-first styling
* Responsive design (`sm`, `md`, `lg`, `xl`)
* Flexbox + Grid using Tailwind
* Spacing system (`p-x`, `m-x`, `gap-x`)
* Typography system
* Custom theme config in `tailwind.config.js`
* Component composition mindset (atoms → molecules → sections → pages)

**Component Architecture + UI Thinking**
* Reusable component system

**Folder structure:**
```text
/components
/app
/styles
```
---

]]

local w3_day1 = w3_intro .. [[
# DAY 1 — TailwindCSS + UI System Basics

### Topics:
* Install Tailwind in Next.js
* Utility classes, spacing, colors, fonts
* Custom theme configuration

### Exercise:
Build a **Dashboard Layout skeleton** (header + sidebar)
**Image for reference (Create header and Sidebar only):**
https://assets.startbootstrap.com/img/meta/products/twitter/twitter-image-sb-admin.png

### Output:
* `/app/layout.jsx`
* `/components/ui/Navbar.jsx`
* `/components/ui/Sidebar.jsx`
]]

local w3_day2 = [[
# DAY 2 — Tailwind Advanced + Component Library

### Topics:
* Flex + Grid with Tailwind
* Components mindset (atomic design)
* Reusable components with props

### Exercise:
Build a component library in:
`/components/ui/`
* `Button.jsx`
* `Input.jsx`
* `Card.jsx`
* `Badge.jsx`
* `Modal.jsx`

**Image for reference (Build the full layout using reusable components, reusing the Day-1 UI):**
https://assets.startbootstrap.com/img/meta/products/twitter/twitter-image-sb-admin.png

### Output:
* `/components/ui/*`
* `UI-COMPONENT-DOCS.md` (Usage examples)
]]

local w3_day3 = [[
# DAY 3 — Next.js Routing + Layout System

### Topics:
* Next.js routing (`app/page.js`, `/about/page.js`, `/dashboard/page.js`)
* Nested layouts
* Shared navigation across pages
* Difference: Client Component vs Server Component

### Exercise:
Build a multi-page structure:
* `/` (landing page)
* `/about`
* `/dashboard`
* `/dashboard/profile`

**Image for reference (Use Day 2 UI + static pages):**
https://assets.startbootstrap.com/img/meta/products/twitter/twitter-image-sb-admin.png

### Output:
* Folder structure working with nested layouts
]]

local w3_day4 = [[
# DAY 4 — Dynamic UI + Image Optimization

### Topics:
* `next/image` (optimized image rendering)
* Responsive images + optimization
* Typography & SEO improvements
* Animations using Tailwind + Framer Motion (optional)

### Exercise:
Build a **responsive landing page** (like SaaS product page)

**Sections:**
* Hero section
* Features grid
* Testimonials (cards)
* Footer

**Image for reference:**
https://assets.startbootstrap.com/img/meta/products/twitter/twitter-image-sb-admin.png

### Output:
* `/app/page.jsx`
* `screenshots/landing-page.png`
]]

local w3_day5 = [[
# DAY 5 — Capstone Mini Project (No backend)

### Project:
Build a **Full Multi-Page UI** in Next.js + Tailwind, no backend.

**Pages:**
```text
/login              (static form)
/dashboard          (cards and widgets UI)
/dashboard/users    (table listing mocked data)
/dashboard/profile
```

### Design references:
* Login: https://img.freepik.com/free-vector/simple-white-login-form_1017-7984.jpg
* Dashboard: Use Day 4 exercise.
* Users: https://demos.themeselection.com/jetship-laravel-starter-kit/documentation/image/guide/user-table.png
* Profile: https://www.gravitykit.com/wp-content/uploads/2023/10/CleanShot-2025-06-26-at-12.53.16@2x-1024x503.png.webp

### Mandatory:
* Component reuse from `/components/ui`
* Clean routing structure
* Mobile responsive UI

### Output:
* Project repo: `week3-next-tailwind-frontend`
* `README.md` must include: Screenshots, Folder structure, Components list, Lessons learned
]]

-- ==========================================
-- WEEK 4 CONTENT (Backend)
-- ==========================================

local w4_intro = [[
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

]]

local w4_day1 = w4_intro .. [[
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
]]

local w4_day2 = [[
# DAY 2 - DATABASE MODELING + INDEXING + ADVANCED CRUD

### Learning Outcomes:
* Designing real schemas
* Mongoose hooks, indexes, virtual fields
* Repository pattern

### Topics
* Embedded vs Referenced schema
* TTL indexes
* Sparse + compound indexes
* Pagination strategies (skip/limit vs cursor)

### Exercise
Build **User & Product** schemas with:
* Pre-save hook, Virtual fields, Compound index, Validation
* Implement repository pattern: `create`, `findById`, `findPaginated`, `update`, `delete`

### Deliverables:
* `/models/User.js`
* `/models/Product.js`
* `/repositories/user.repository.js`
* `/repositories/product.repository.js`
* Index analysis screenshot
]]

local w4_day3 = [[
# DAY 3 — HIGH-PERFORMANCE REST API + ADV QUERY ENGINE

### Learning Outcomes:
* Build complex, production APIs
* Dynamic filters, sorting, soft delete
* Error boundaries

### Topics
* Controller → Service → Repository flow
* Complex filters
* Soft deletes (flag + timestamp)
* Advanced error handling (Typed errors, Error codes)

### Exercise
Build **Product API** with:
* Dynamic search engine (regex + OR/AND)
* Filtering + sorting + pagination
* Soft delete
* Global error formats

### Deliverables:
* `/controllers/product.controller.js`
* `/services/product.service.js`
* `/middlewares/error.middleware.js`
* `QUERY-ENGINE-DOC.md`
]]

local w4_day4 = [[
# DAY 4 — SECURITY, VALIDATION, RATE LIMITING, HARDENING

### Learning Outcomes:
* Secure & sanitize APIs
* Request validation
* Rate limiting

### Topics:
* Preventing NoSQL Injection, XSS, Parameter pollution
* JOI / Zod validation
* Helmet + CORS
* Rate limiting

### Exercise
1. Build validation schema for User + Product.
2. Add global rate limiting, CORS, Helmet, Payload limits.
3. Write security test cases.

### Deliverables:
* `/middlewares/validate.js`
* `/middlewares/security.js`
* `SECURITY-REPORT.md`
]]

local w4_day5 = [[
# DAY 5 — JOB QUEUES + LOGGING + API DOCUMENTATION + CAPSTONE

### Learning Outcomes:
* Async background jobs
* Structured logging
* Postman documentation

### Topics:
* Job queue (BullMQ/Redis)
* Logging patterns (correlation IDs)
* Request tracing
* API documentation

### Exercise
Implement:
1. **Background job** (Email/Report)
2. **Request tracing** (`X-Request-ID`)
3. **API Documentation** (Swagger/Postman)
4. **Deploy-ready folder**

### Deliverables:
* `/jobs/email.job.js`
* `/utils/tracing.js`
* `/logs/*.log`
* Postman Collection Export
* `DEPLOYMENT-NOTES.md`
]]

-- ==========================================
-- WEEK 5 CONTENT (Docker)
-- ==========================================

local w5_intro = [[
# Week 5: Server Side Foundations with Docker & DevOps Basics

### Objective:
Help interns understand **how production servers work**, using Docker to simulate deployment environments locally.

### Week-5 Topics

---

]]

local w5_day1 = w5_intro .. [[
# DAY 1 — Docker Fundamentals + Linux Internals

### Topics
* Images, containers, volumes, networks
* Basic container OS operations
* Dockerfile basics

### Exercise
* Container running Node app
* Enter container (like SSH): `docker exec -it <container> /bin/sh`
* Explore: `ls`, `ps`, `top`, logs

### Output
* `Dockerfile`
* `linux-in-container.md`
]]

local w5_day2 = [[
# DAY 2 — Docker Compose + Multi-Container Apps

### Topics
* Docker networking
* Volumes for persistent storage
* Compose for multiple services

### Exercise
Deploy **client (React) + server (Node) + MongoDB** using:
`docker compose up -d`

### Output
* `docker-compose.yml`
* `service-architecture.md`
]]

local w5_day3 = [[
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
]]

local w5_day4 = [[
# DAY 4 — SSL + Self-Signed + mkcert + HTTPS

### Topics
* SSL/TLS fundamentals
* Setting certs inside container
* HTTPS termination at NGINX

### Exercise
* Generate self-signed cert using `mkcert`
* Force redirect HTTP → HTTPS
* Confirm lock icon in browser

### Output
* Certificates + `ssl-setup.md`
* HTTPS working screenshot
]]

local w5_day5 = [[
# DAY 5 — CI-Style Deployment Automation + Capstone

### Capstone
Deploy a **full-stack app** in Docker with reverse proxy + HTTPS

**Checklist:**
* `docker-compose.prod.yml`
* Secrets in `.env`
* Healthcheck
* Container restart policy
* Deployment script

### Output
* Fully working application stack
* `production-guide.md`
]]

-- ==========================================
-- WEEK 6 CONTENT (ML Engineering)
-- ==========================================

local w6_intro = [[
# WEEK 6 — MACHINE LEARNING ENGINEERING
(Data Science + Feature Engineering + Model Building + Deployment + Monitoring)

### WEEK 6 OBJECTIVES
Interns will learn:
* Professional ML pipeline architecture
* Clean, modular ML system design
* Advanced feature engineering
* Model optimization + regularization
* Training pipeline orchestration
* Model evaluation + explainability
* Model deployment + monitoring

---

]]

local w6_day1 = w6_intro .. [[
# DAY 1 — DATA PIPELINE + EDA + PROJECT ARCHITECTURE

### Learning Outcomes:
* ML project architecture
* Dataset versioning
* EDA
* Data preprocessing pipelines

### Mandatory Folder Structure (No shortcuts)
```text
src/
  data/
  notebooks/
  features/
  pipelines/
  models/
  training/
  evaluation/
  deployment/
  monitoring/
  utils/
```

### Exercise
Build a **data loader + EDA pipeline** that:
1. Loads dataset
2. Cleans data
3. Creates processed csv
4. Generates EDA report (Correlation, Distributions, Missing values)

### Deliverables
* `/pipelines/data_pipeline.py`
* `/notebooks/EDA.ipynb`
* `DATA-REPORT.md`
]]

local w6_day2 = [[
# DAY 2 — FEATURE ENGINEERING + FEATURE SELECTION

### Learning Outcomes:
* Create meaningful features
* Encoding strategies
* Feature selection techniques

### Topics
* Categorical encoding
* Numerical feature transformations
* Text vectorization
* Feature selection (Correlation, Mutual Info, RFE)

### Exercise
Build a feature engineering pipeline that:
* Encodes features
* Normalizes features
* Generates 10+ new features
* Applies feature selection

### Deliverables
* `/features/build_features.py`
* `/features/feature_selector.py`
* `FEATURE-ENGINEERING-DOC.md`
]]

local w6_day3 = [[
# DAY 3 — MODEL BUILDING + ADVANCED TRAINING PIPELINE

### Learning Outcomes:
* Multi-model training
* Cross-validation
* Overfitting control

### Exercise
Create a unified training pipeline that:
* Trains 4 models (Logistic, Random Forest, XGBoost, Neural Network)
* Performs 5-fold cross-validation
* Outputs metrics (Accuracy, Precision, Recall, F1, ROC-AUC)

### Deliverables
* `/training/train.py`
* `/models/best_model.pkl`
* `MODEL-COMPARISON.md`
]]

local w6_day4 = [[
# DAY 4 — HYPERPARAMETER TUNING + EXPLAINABILITY + ERROR ANALYSIS

### Learning Outcomes:
* Optimize a model
* Interpret model decisions
* Deep error analysis

### Exercise
Implement:
* Hyperparameter tuning (Optuna/GridSearch)
* Generate: SHAP summary plot, Feature importance, Error analysis heatmap

### Deliverables
* `/training/tuning.py`
* `/evaluation/shap_analysis.py`
* `MODEL-INTERPRETATION.md`
]]

local w6_day5 = [[
# DAY 5 — MODEL DEPLOYMENT + MONITORING + MLOPS CONCEPTS (CAPSTONE)

### Learning Outcomes:
* Deploy real ML systems
* Monitor drift

### Exercise (Capstone)
Deploy model as an API (FastAPI/Flask):
* POST `/predict`
* Add: Logging, Request ID, Input validation, Versioning

### Deliverables
* `/deployment/api.py`
* `/deployment/Dockerfile`
* `/monitoring/drift_checker.py`
* `DEPLOYMENT-NOTES.md`
]]

-- ==========================================
-- WEEK 7 CONTENT (GenAI)
-- ==========================================

local w7_intro = [[
# WEEK 7 — GENAI & MULTIMODAL RAG ENGINEERING
(Text RAG + Image RAG + SQL Question Answering + Hybrid Retrieval + Local LLMs)

### USE CASE: Enterprise Knowledge Intelligence System
Interns will build an enterprise-grade GenAI system that can:
* Answer questions from internal documents
* Retrieve & reason over images
* Query structured data using natural language → SQL

### OBJECTIVES
* RAG architecture
* Local LLM setup or API integration
* Hybrid retrieval
* Multimodal embeddings
* SQL-based QA

---

]]

local w7_day1 = w7_intro .. [[
# DAY 1 — LOCAL RAG SYSTEM + PIPELINE ARCHITECTURE

### Learning Outcomes
* RAG architecture
* Local LLM inference
* Embedding generation
* Document chunking

### Mandatory Folder Structure
```text
src/
  data/
  embeddings/
  vectorstore/
  retriever/
  generator/
  pipelines/
  prompts/
  models/
  evaluation/
  utils/
```

### Exercise
Build a local ingestion & chunking pipeline:
* Load PDFs/TXT/CSV
* Clean & Chunk
* Generate embeddings
* Store in Vector DB (FAISS/Qdrant)

### Deliverables
* `/pipelines/ingest.py`
* `/embeddings/embedder.py`
* `/vectorstore/index.faiss`
* `RAG-ARCHITECTURE.md`
]]

local w7_day2 = [[
# DAY 2 — ADVANCED RETRIEVAL + CONTEXT ENGINEERING

### Learning Outcomes
* Improve retrieval accuracy
* Hybrid retrieval
* Context ranking

### Exercise
Build an advanced retriever that supports:
* Keyword fallback
* Reranking
* Deduplication
* Traceable context sources

### Deliverables
* `/retriever/hybrid_retriever.py`
* `/retriever/reranker.py`
* `RETRIEVAL-STRATEGIES.md`
]]

local w7_day3 = [[
# DAY 3 — IMAGE-RAG (MULTIMODAL RAG)

### Learning Outcomes
* Handle images inside RAG
* Vision embeddings
* OCR + Captioning

### Exercise
Build an **Image RAG pipeline**:
* Ingest PNG/JPG/PDF
* Generate OCR Text + CLIP embeddings + Captions
* Query modes: Text→Image, Image→Image, Image→Text

### Deliverables
* `/pipelines/image_ingest.py`
* `/embeddings/clip_embedder.py`
* `MULTIMODAL-RAG.md`
]]

local w7_day4 = [[
# DAY 4 — SQL QUESTION ANSWERING SYSTEM

### Learning Outcomes
* Text → SQL → Answer
* Schema-aware reasoning

### Exercise
Build a **SQL-QA Engine**:
* Generate SQL using LLM
* Validate SQL
* Execute on DB
* Summarize results

### Deliverables
* `/pipelines/sql_pipeline.py`
* `/generator/sql_generator.py`
* `SQL-QA-DOC.md`
]]

local w7_day5 = [[
# DAY 5 — ADVANCED RAG + MEMORY + EVALUATION (CAPSTONE)

### Learning Outcomes
* Conversational memory
* Hallucination detection
* Faithfulness scoring

### Exercise (Capstone)
Build a complete system with endpoints: `/ask`, `/ask-image`, `/ask-sql`
* Add: Memory, Refinement loop, Logging, Streamlit UI

### Deliverables
* `/deployment/app.py`
* `/evaluation/rag_eval.py`
* `DEPLOYMENT-NOTES.md`
]]

-- ==========================================
-- WEEK 8 CONTENT (LLM Fine-Tuning)
-- ==========================================

local w8_intro = [[
# WEEK 8 — LLM FINE-TUNING, QUANTISATION & OPTIMISED INFERENCE

### OBJECTIVES
* LLM internals
* Parameter-efficient fine-tuning (LoRA / QLoRA)
* Quantisation (8-bit, 4-bit, GGUF)
* Inference optimization
* Deployment

### MODELS (Mandatory)
Phi-2, Mistral 7B, TinyLlama, or Qwen

---

]]

local w8_day1 = w8_intro .. [[
# DAY 1 — LLM ARCHITECTURE + DATA PREP FOR FINE-TUNING

### Learning Outcomes
* LLM anatomy
* Tokenization
* Instruction tuning

### Exercise
Build your **instruction tuning dataset**:
* 3 types: QA, Reasoning, Extraction
* 1,000 samples (Clean + curated)
* JSONL format

### Deliverables
* `/data/train.jsonl`
* `/utils/data_cleaner.py`
* `DATASET-ANALYSIS.md`
]]

local w8_day2 = [[
# DAY 2 — PARAMETER-EFFICIENT FINE-TUNING (LoRA / QLoRA)

### Learning Outcomes
* Fine-tune LLM on Colab
* LoRA / QLoRA

### Exercise
Fine-tune model using **QLoRA** with:
* `r=16`, `lr=2e-4`, 4-bit loading
* Verify loss optimizing and adapter weights saved

### Deliverables
* `/notebooks/lora_train.ipynb`
* `/adapters/adapter_model.bin`
* `TRAINING-REPORT.md`
]]

local w8_day3 = [[
# DAY 3 — QUANTISATION (8-bit → 4-bit → GGUF)

### Learning Outcomes
* Quantisation trade-offs
* GGUF & llama.cpp

### Exercise
Convert model to:
* 8-bit
* 4-bit
* GGUF

### Deliverables
* `/quantized/model.gguf`
* `QUANTISATION-REPORT.md`
]]

local w8_day4 = [[
# DAY 4 — INFERENCE OPTIMISATION + BENCHMARKING

### Learning Outcomes
* Speed up inference
* Batching & Streaming

### Exercise
Test inference using Base vs Fine-tuned vs Quantised.
Measure Tokens/sec, VRAM, Latency.

### Deliverables
* `/benchmarks/results.csv`
* `BENCHMARK-REPORT.md`
]]

local w8_day5 = [[
# DAY 5 — CAPSTONE: BUILD & DEPLOY LOCAL LLM API

### Learning Outcomes
* LLM as local microservice
* Production ready

### Exercise (Capstone)
Build `POST /generate` and `POST /chat`.
Features: Quantised model, Infinite chat, Templating, Logs.

### Deliverables
* `/deploy/app.py`
* `/DOCKERFILE`
* `FINAL-REPORT.md`
]]

-- ==========================================
-- MAIN GENERATION LOGIC
-- ==========================================

local all_weeks = {
    Week2 = { w2_day1, w2_day2, w2_day3, w2_day4, w2_day5 },
    Week3 = { w3_day1, w3_day2, w3_day3, w3_day4, w3_day5 },
    Week4 = { w4_day1, w4_day2, w4_day3, w4_day4, w4_day5 },
    Week5 = { w5_day1, w5_day2, w5_day3, w5_day4, w5_day5 },
    Week6 = { w6_day1, w6_day2, w6_day3, w6_day4, w6_day5 },
    Week7 = { w7_day1, w7_day2, w7_day3, w7_day4, w7_day5 },
    Week8 = { w8_day1, w8_day2, w8_day3, w8_day4, w8_day5 },
}

print("Starting generation for Week 2 to Week 8...")

for week_name, days in pairs(all_weeks) do
    local week_dir = week_name
    create_dir(week_dir)
    print("Processing " .. week_name)
    
    for i, content in ipairs(days) do
        local day_name = "day-" .. i
        local day_dir = week_dir .. "/" .. day_name
        create_dir(day_dir)
        
        local file_path = day_dir .. "/" .. day_name .. ".md"
        write_file(file_path, content)
    end
end

print("Structure generated successfully!")

