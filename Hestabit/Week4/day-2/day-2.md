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
