# Query Engine Documentation

## Overview
This document describes the advanced query engine implemented in the Product API. The query engine supports dynamic search, filtering, sorting, pagination, and soft deletes.

## Features

### 1. **Dynamic Search (Regex)**
Search across product names and descriptions using regular expressions.

**Syntax:**
```
GET /api/v1/products?search=<search_term>
```

**Example:**
```bash
# Search for products with "laptop" in name or description
GET /api/v1/products?search=laptop

# Search is case-insensitive
GET /api/v1/products?search=MacBook
```

**Implementation:**
- Uses MongoDB regex with case-insensitive flag (`$options: 'i'`)
- Searches both `name` and `description` fields using `$or` operator

---

### 2. **Advanced Filtering**

#### Basic Filtering
Filter by exact field values.

**Example:**
```bash
# Filter by category
GET /api/v1/products?category=electronics

# Filter by multiple fields
GET /api/v1/products?category=electronics&stock=10
```

#### Range Filtering
Use comparison operators for numeric fields.

**Operators:**
- `gte` - Greater than or equal to
- `gt` - Greater than
- `lte` - Less than or equal to
- `lt` - Less than

**Example:**
```bash
# Products with price >= 100
GET /api/v1/products?price[gte]=100

# Products with price between 100 and 500
GET /api/v1/products?price[gte]=100&price[lte]=500

# Products with stock less than 10
GET /api/v1/products?stock[lt]=10
```

**Implementation:**
- Query parameters are parsed and converted to MongoDB operators
- Example: `price[gte]=100` becomes `{ price: { $gte: 100 } }`

---

### 3. **Sorting**

Sort results by one or multiple fields.

**Syntax:**
```
GET /api/v1/products?sort=<field1>,<field2>
```

**Sorting Order:**
- Ascending: field name (e.g., `price`)
- Descending: field name with minus prefix (e.g., `-price`)

**Examples:**
```bash
# Sort by price ascending
GET /api/v1/products?sort=price

# Sort by price descending
GET /api/v1/products?sort=-price

# Sort by category (asc) then price (desc)
GET /api/v1/products?sort=category,-price

# Default: Sort by creation date descending
GET /api/v1/products
```

---

### 4. **Pagination**

Control the number of results and navigate through pages.

**Parameters:**
- `page` - Page number (default: 1)
- `limit` - Number of results per page (default: 10)

**Syntax:**
```
GET /api/v1/products?page=<page_number>&limit=<items_per_page>
```

**Examples:**
```bash
# Get first 10 products (default)
GET /api/v1/products

# Get page 2 with 20 items per page
GET /api/v1/products?page=2&limit=20

# Get page 3 with 5 items per page
GET /api/v1/products?page=3&limit=5
```

**Response Format:**
```json
{
  "status": "success",
  "results": 10,
  "total": 145,
  "page": 2,
  "totalPages": 15,
  "data": [...]
}
```

---

### 5. **Field Limiting**

Select only specific fields to be returned in the response.

**Syntax:**
```
GET /api/v1/products?fields=<field1>,<field2>
```

**Examples:**
```bash
# Get only name and price
GET /api/v1/products?fields=name,price

# Get name, price, and category
GET /api/v1/products?fields=name,price,category
```

**Default:**
- All fields are returned except `__v` (Mongoose version key)

---

### 6. **Soft Delete**

Products are not physically deleted from the database. Instead, they are marked as deleted.

**Implementation:**
- `isDeleted` flag (boolean)
- `deletedAt` timestamp

**Behavior:**
- Deleted products are automatically excluded from all query results
- Pre-query middleware filters out `isDeleted: true` documents

**Example:**
```bash
# Delete a product (soft delete)
DELETE /api/v1/products/507f1f77bcf86cd799439011

# This product will no longer appear in GET queries
GET /api/v1/products
```

---

## Complex Query Examples

### Example 1: Combined Search and Filter
```bash
# Search for "laptop" in electronics category with price >= 500
GET /api/v1/products?search=laptop&category=electronics&price[gte]=500
```

### Example 2: Filter, Sort, and Paginate
```bash
# Electronics under $1000, sorted by price, page 2 with 20 items
GET /api/v1/products?category=electronics&price[lt]=1000&sort=price&page=2&limit=20
```

### Example 3: Range Filter with Field Limiting
```bash
# Products between $100-500, return only name and price
GET /api/v1/products?price[gte]=100&price[lte]=500&fields=name,price
```

### Example 4: Multi-field Sort with Search
```bash
# Search "phone", sort by category (asc) then price (desc)
GET /api/v1/products?search=phone&sort=category,-price
```

---

## API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/products` | Get all products (with query options) |
| GET | `/api/v1/products/:id` | Get single product by ID |
| POST | `/api/v1/products` | Create new product |
| PATCH | `/api/v1/products/:id` | Update product |
| DELETE | `/api/v1/products/:id` | Soft delete product |

---

## Error Handling

All errors follow a consistent format:

**Development Mode:**
```json
{
  "status": "fail",
  "error": { /* full error object */ },
  "message": "Product not found",
  "stack": "Error: Product not found\n    at ..."
}
```

**Production Mode:**
```json
{
  "status": "fail",
  "message": "Product not found"
}
```

**Common Error Codes:**
- `400` - Bad Request (validation errors)
- `404` - Not Found
- `500` - Internal Server Error

---

## Performance Notes

1. **Indexing**: Consider adding indexes on frequently queried fields (e.g., `category`, `price`)
2. **Pagination**: Always use pagination for large datasets
3. **Field Limiting**: Use field limiting to reduce payload size when you don't need all fields
4. **Regex Performance**: Search queries with regex can be slow on large datasets; consider using text indexes for better performance

---

## Future Enhancements

- Text search indexes for faster search
- Full-text search capabilities
- AND/OR logical operators for complex filters
- Aggregation pipelines for analytics
- Caching for frequently accessed queries
