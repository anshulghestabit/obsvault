# Day 3 - Product API

## Overview
A high-performance REST API with advanced query engine capabilities including dynamic search, filtering, sorting, pagination, and soft deletes.

## Features
✅ **Controller → Service → Repository architecture**
✅ **Advanced Query Engine** (see QUERY-ENGINE-DOC.md for details)
✅ **Soft Delete** with `isDeleted` flag and `deletedAt` timestamp
✅ **Global Error Handling** with typed errors and custom error codes
✅ **MongoDB integration** with Mongoose
✅ **Security** with Helmet and CORS

## Project Structure
```
day-3/
├── src/
│   ├── app.js                          # Application entry point
│   ├── config/
│   │   └── database.js                 # MongoDB connection
│   ├── controllers/
│   │   └── product.controller.js       # Product endpoints
│   ├── services/
│   │   └── product.service.js          # Business logic & query engine
│   ├── models/
│   │   └── product.model.js            # Product schema
│   ├── routes/
│   │   └── product.routes.js           # Route definitions
│   ├── middlewares/
│   │   └── error.middleware.js         # Global error handler
│   └── utils/
├── .env                                 # Environment variables
├── package.json
└── QUERY-ENGINE-DOC.md                 # Query engine documentation
```

## Installation

1. Install dependencies:
```bash
npm install
```

2. Configure environment variables in `.env`:
```env
NODE_ENV=development
PORT=3000
MONGODB_URI=mongodb://localhost:27017/products-db
```

3. Make sure MongoDB is running on your system

## Running the Application

### Development mode:
```bash
npm run dev
```

### Production mode:
```bash
npm start
```

The server will start on `http://localhost:3000`

## API Endpoints

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | `/api/v1/products` | Get all products (with query options) |
| GET | `/api/v1/products/:id` | Get single product by ID |
| POST | `/api/v1/products` | Create new product |
| PATCH | `/api/v1/products/:id` | Update product |
| DELETE | `/api/v1/products/:id` | Soft delete product |

## Query Options

See `QUERY-ENGINE-DOC.md` for comprehensive documentation.

**Quick Examples:**

```bash
# Search
GET /api/v1/products?search=laptop

# Filter by category
GET /api/v1/products?category=electronics

# Price range
GET /api/v1/products?price[gte]=100&price[lte]=500

# Sort
GET /api/v1/products?sort=-price

# Pagination
GET /api/v1/products?page=2&limit=20

# Combined
GET /api/v1/products?search=phone&category=electronics&price[lt]=1000&sort=price&page=1&limit=10
```

## Example Usage

### Create a product:
```bash
curl -X POST http://localhost:3000/api/v1/products \
  -H "Content-Type: application/json" \
  -d '{
    "name": "MacBook Pro",
    "price": 1999,
    "description": "16-inch laptop",
    "category": "electronics",
    "stock": 50
  }'
```

### Get all products with filters:
```bash
curl "http://localhost:3000/api/v1/products?category=electronics&price[gte]=500&sort=-price"
```

### Update a product:
```bash
curl -X PATCH http://localhost:3000/api/v1/products/<product_id> \
  -H "Content-Type: application/json" \
  -d '{"price": 1799}'
```

### Delete a product (soft delete):
```bash
curl -X DELETE http://localhost:3000/api/v1/products/<product_id>
```

## Architecture

### Controller → Service → Repository Pattern

**Controllers** (`product.controller.js`):
- Handle HTTP requests and responses
- Validate input (basic)
- Call service layer
- Handle errors with try-catch

**Services** (`product.service.js`):
- Contain business logic
- Implement query engine
- Interact with models/repositories
- Throw custom errors

**Models** (`product.model.js`):
- Define data schema
- Mongoose model definition
- Schema validation
- Pre-query middleware for soft deletes

## Error Handling

All errors are handled by the global error middleware and return consistent formats:

```json
{
  "status": "fail",
  "message": "Product not found"
}
```

Custom `AppError` class for operational errors with status codes.

## Technologies Used

- **Express.js** - Web framework
- **MongoDB** - Database
- **Mongoose** - ODM
- **Helmet** - Security headers
- **CORS** - Cross-origin resource sharing
- **dotenv** - Environment configuration
