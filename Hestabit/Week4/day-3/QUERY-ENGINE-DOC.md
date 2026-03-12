What to show in demo

Use these in order:


Start app
npm start
Seed products
curl -X POST http://localhost:3000/api/products/seed
Run dynamic query
curl "http://localhost:3000/api/products?search=phone&minPrice=1000&maxPrice=90000&sort=price:desc&tags=apple,samsung&page=1&limit=5"
Soft delete a real product
curl -X DELETE http://localhost:3000/api/products/69b27accf7959f811f6c9991
Show hidden by default
curl "http://localhost:3000/api/products"
Show included deleted
curl "http://localhost:3000/api/products?includeDeleted=true"




## `QUERY-ENGINE-DOC.md`

```md
# Query Engine Documentation

## Overview

This Product API supports dynamic filtering, sorting, pagination, and soft delete.

Base route:

`/api/products`

---

## Supported Query Parameters

### 1. Search
Searches across:
- product name
- description
- category

Uses case-insensitive regex matching.

Example:

`GET /api/products?search=phone`

---

### 2. Price Filtering

Supported query parameters:
- `minPrice`
- `maxPrice`

Example:

`GET /api/products?minPrice=1000&maxPrice=90000`

---

### 3. Tag Filtering

Tags are passed as comma-separated values.

Example:

`GET /api/products?tags=apple,samsung`

This returns products whose tags match any of the provided values.

---

### 4. Sorting

Format:

`sort=field:order`

Examples:
- `sort=price:asc`
- `sort=price:desc`
- `sort=createdAt:desc`

Default sort is:

`createdAt:desc`

---

### 5. Pagination

Supported parameters:
- `page`
- `limit`

Example:

`GET /api/products?page=1&limit=10`

Response contains pagination metadata:
- total
- page
- limit
- totalPages

---

### 6. Soft Delete

Deleting a product does not remove it from the database permanently.

Instead, it updates:

```js
deletedAt = new Date()
````

Example:

`DELETE /api/products/:id`

---

### 7. Include Deleted Products

By default, deleted products are excluded from results.

To include them:

`GET /api/products?includeDeleted=true`

---

## Query Logic Summary

### Search Logic

The service builds a MongoDB filter using `$or` with regex conditions on:

* `name`
* `description`
* `category`

### Price Logic

If `minPrice` or `maxPrice` is provided, the query applies:

* `$gte`
* `$lte`

### Tag Logic

If `tags` is provided, it is split into an array and matched using:

```js
{ tags: { $in: tagList } }
```

### Deleted Filter Logic

If `includeDeleted` is not `true`, the service adds:

```js
{ deletedAt: null }
```

### Sort Logic

The API parses:

```text
field:order
```

and converts it into a MongoDB sort object.

Example:

```text
price:desc
```

becomes:

```js
{ price: -1 }
```

---

## Example Query

`GET /api/products?search=phone&minPrice=1000&maxPrice=90000&sort=price:desc&tags=apple,samsung&page=1&limit=5`

This query:

* searches for products related to `phone`
* filters products within a price range
* matches products tagged with apple or samsung
* sorts by price in descending order
* returns page 1 with 5 results per page

---

## Error Format

All API errors follow this format:

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

## Tested Behaviors

The following behaviors were tested:

1. normal product listing
2. filtered search using `search`, `minPrice`, `maxPrice`, and `tags`
3. sorting by price descending
4. pagination metadata in response
5. soft delete using `DELETE /api/products/:id`
6. hidden deleted products in normal listing
7. showing deleted products using `includeDeleted=true`
8. structured error when deleting an already deleted product

---

## Conclusion

The query engine provides a flexible and production-style API interface for product search and retrieval.

It supports:

* dynamic filtering
* sorting
* pagination
* soft delete visibility control
* centralized error reporting

````
