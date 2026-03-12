Here are both files, cleaned up for your current Day 3 project.

First move the README out of `src` if you haven’t already:

```bash
mv src/Readme.md README.md 2>/dev/null || true
```

Then create both files.

## `README.md`

````md
# Day 3 — High-Performance REST API + Advanced Query Engine

## Overview

This project is a Product API built using Node.js, Express, and MongoDB.

It demonstrates:

- Controller → Service → Repository architecture
- Dynamic filters
- Sorting
- Pagination
- Soft delete
- Centralized error handling
- Structured error responses

---

## Project Structure

```text
.
├── package.json
├── package-lock.json
├── README.md
├── QUERY-ENGINE-DOC.md
└── src
    ├── app.js
    ├── config
    │   └── index.js
    ├── controllers
    │   └── product.controller.js
    ├── loaders
    │   └── db.js
    ├── middlewares
    │   └── error.middleware.js
    ├── models
    │   └── Product.js
    ├── repositories
    │   └── product.repository.js
    ├── routes
    │   └── product.routes.js
    ├── server.js
    ├── services
    │   └── product.service.js
    └── utils
        └── api-error.js
````

---

## Features Implemented

### 1. Dynamic Search Engine

Supports:

* search
* minPrice
* maxPrice
* tags
* sort
* page
* limit

### 2. Filtering + Sorting + Pagination

The API supports:

* filtering by price range
* filtering by tags
* searching by product name, description, and category
* sorting by fields such as `price` or `createdAt`
* pagination using `page` and `limit`

### 3. Soft Delete

Instead of permanently deleting a product, the API sets the `deletedAt` field.

### 4. Centralized Error Handling

All errors are handled by `error.middleware.js`.

Error format:

```json
{
  "success": false,
  "message": "Product not found",
  "code": "PRODUCT_NOT_FOUND",
  "timestamp": "2026-03-12T09:00:00.000Z",
  "path": "/api/products/123"
}
```

---

## How to Run

### Install dependencies

```bash
npm install
```

### Start the server

```bash
npm start
```

Expected output:

```text
MongoDB connected for Day 3
Server running on port 3000
```

---

## API Testing

### 1. Seed Sample Products

```bash
curl -X POST http://localhost:3000/api/products/seed
```

Expected response:

```json
{
  "success": true,
  "message": "Sample products inserted"
}
```

---

### 2. Get All Products

```bash
curl "http://localhost:3000/api/products"
```

This returns all active, non-deleted products with pagination metadata.

---

### 3. Dynamic Query Example

```bash
curl "http://localhost:3000/api/products?search=phone&minPrice=1000&maxPrice=90000&sort=price:desc&tags=apple,samsung&page=1&limit=5"
```

Observed result in testing:

* iPhone 15 returned
* Samsung Galaxy S24 returned
* results sorted by `price:desc`
* total matched records = 2

This proves:

* search works
* price filtering works
* tags filter works
* sorting works
* pagination works

---

### 4. Soft Delete Example

Delete a product using a real product ID:

```bash
curl -X DELETE http://localhost:3000/api/products/69b27accf7959f811f6c9991
```

Expected response:

```json
{
  "success": true,
  "message": "Product soft deleted successfully"
}
```

---

### 5. Verify Deleted Product is Hidden

```bash
curl "http://localhost:3000/api/products"
```

This excludes soft-deleted products by default.

---

### 6. Include Deleted Products

```bash
curl "http://localhost:3000/api/products?includeDeleted=true"
```

This includes products whose `deletedAt` is not null.

---

### 7. Error Handling Example

Deleting the same product again returns structured error output:

```bash
curl -X DELETE http://localhost:3000/api/products/69b27accf7959f811f6c9991
```

Expected error response:

```json
{
  "success": false,
  "message": "Product already deleted",
  "code": "PRODUCT_ALREADY_DELETED",
  "timestamp": "2026-03-12T09:00:00.000Z",
  "path": "/api/products/69b27accf7959f811f6c9991"
}
```

This proves:

* typed errors work
* centralized error middleware works
* global error response format works

---

## Architecture Flow

This project follows:

```text
Route -> Controller -> Service -> Repository -> Model
```

### Route

Maps API endpoints to controller methods.

### Controller

Handles request and response.

### Service

Contains query engine logic, filters, sorting, pagination, and soft delete rules.

### Repository

Handles MongoDB queries.

### Model

Defines schema and database index.

---

## Requirements Mapping

### Deliverables Completed

* `controllers/product.controller.js`
* `services/product.service.js`
* `middlewares/error.middleware.js`
* `QUERY-ENGINE-DOC.md`

### Exercise Coverage

#### Dynamic search engine

Implemented using regex search on:

* name
* description
* category

#### Filtering + sorting + pagination

Implemented using query parameters:

* `search`
* `minPrice`
* `maxPrice`
* `tags`
* `sort`
* `page`
* `limit`

#### Soft delete

Implemented using `deletedAt`

#### Include deleted

Implemented using:

```http
GET /api/products?includeDeleted=true
```

#### Global error format

Implemented in centralized middleware.

---

## Conclusion

This Day 3 project demonstrates a modular Product API with:

* layered architecture
* dynamic query engine
* soft delete support
* centralized error handling

It fulfills the Day 3 requirements for advanced REST API design and query handling.

````

---
