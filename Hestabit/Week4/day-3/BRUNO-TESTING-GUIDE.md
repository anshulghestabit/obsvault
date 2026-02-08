

## 📝 Complete Testing Workflow

### Step 1: Create Your First Product ✅

**Request:** `Create Product`

1. Click on "Create Product" in the left sidebar
2. You should see this JSON in the Body tab:
```json
{
  "name": "MacBook Pro 16",
  "price": 2499,
  "description": "High-performance laptop for professionals",
  "category": "electronics",
  "stock": 25
}
```
3. Click **Send** (or press Ctrl+Enter)
4. You should get a **201 Created** response with the new product including an `_id`

**Example Response:**
```json
{
  "status": "success",
  "data": {
    "_id": "67a1b2c3d4e5f6g7h8i9j0k1",  ← COPY THIS ID!
    "name": "MacBook Pro 16",
    "price": 2499,
    "description": "High-performance laptop for professionals",
    "category": "electronics",
    "stock": 25,
    "createdAt": "2026-02-08T14:30:00.000Z",
    "updatedAt": "2026-02-08T14:30:00.000Z"
  }
}
```

**👉 IMPORTANT:** Copy the `_id` value from the response! You'll need it for the next steps.

---

### Step 2: Get All Products ✅

**Request:** `Get All Products`

1. Click on "Get All Products"
2. Click **Send**
3. You should see all products in the database (including the one you just created)

**Example Response:**
```json
{
  "status": "success",
  "results": 1,
  "total": 1,
  "page": 1,
  "totalPages": 1,
  "data": [
    {
      "_id": "67a1b2c3d4e5f6g7h8i9j0k1",
      "name": "MacBook Pro 16",
      "price": 2499,
      ...
    }
  ]
}
```

---

### Step 3: Get Product by ID ✅

**Request:** `Get Product by ID`

**⚠️ This is where you had the error!**

1. Click on "Get Product by ID"
2. Look at the URL tab - you'll see: `http://localhost:3000/api/v1/products/PRODUCT_ID_HERE`
3. **Replace `PRODUCT_ID_HERE` with the actual `_id` you copied from Step 1**
4. The URL should look like: `http://localhost:3000/api/v1/products/67a1b2c3d4e5f6g7h8i9j0k1`
5. Click **Send**

**Example Response:**
```json
{
  "status": "success",
  "data": {
    "_id": "67a1b2c3d4e5f6g7h8i9j0k1",
    "name": "MacBook Pro 16",
    ...
  }
}
```

---

### Step 4: Update Product ✅

**Request:** `Update Product`

1. Click on "Update Product"
2. **Replace `PRODUCT_ID_HERE` in the URL** with your actual product ID
3. Modify the JSON body with the fields you want to update:
```json
{
  "price": 2299,
  "stock": 30
}
```
4. Click **Send**
5. You should get the updated product back

**Example Response:**
```json
{
  "status": "success",
  "data": {
    "_id": "67a1b2c3d4e5f6g7h8i9j0k1",
    "name": "MacBook Pro 16",
    "price": 2299,      ← Updated!
    "stock": 30,        ← Updated!
    ...
  }
}
```

---

### Step 5: Create More Products (for testing queries) ✅

Create a few more products with different categories and prices:

**Product 2:**
```json
{
  "name": "Gaming Mouse",
  "price": 49,
  "description": "RGB gaming mouse",
  "category": "electronics",
  "stock": 50
}
```

**Product 3:**
```json
{
  "name": "Python Programming Book",
  "price": 45,
  "description": "Learn Python from scratch",
  "category": "books",
  "stock": 100
}
```

**Product 4:**
```json
{
  "name": "iPhone 15 Pro",
  "price": 999,
  "description": "Latest iPhone model",
  "category": "electronics",
  "stock": 20
}
```

---

## 🔍 Testing Query Features

Now that you have multiple products, test the query features:

### 6. Search Products ✅

**Request:** `Search Products`

Default search: `?search=laptop`

**Try these variations:**
- Change "laptop" to "python" in the query params
- Search for "phone"
- Search for "gaming"

The search looks in both `name` and `description` fields!

---

### 7. Filter by Category ✅

**Request:** `Filter by Category`

Default: `?category=electronics`

**Try these:**
- Change to `category=books`
- Change to `category=clothing`

---

### 8. Filter by Price Range ✅

**Request:** `Filter by Price Range`

Default: `?price[gte]=500&price[lte]=2000`

**Try these:**
- `price[gte]=0&price[lte]=100` (under $100)
- `price[gte]=1000` (over $1000)
- `price[lt]=50` (less than $50)

---

### 9. Sort Products ✅

**Request:** `Sort Products`

Default: `?sort=-price` (price high to low)

**Try these:**
- `sort=price` (price low to high)
- `sort=name` (alphabetically)
- `sort=-createdAt` (newest first)
- `sort=category,-price` (by category, then price desc)

---

### 10. Pagination ✅

**Request:** `Pagination`

Default: `?page=1&limit=10`

**Try these:**
- `page=1&limit=2` (2 items per page)
- `page=2&limit=2` (next page)

**Response shows:**
```json
{
  "results": 2,
  "total": 4,
  "page": 1,
  "totalPages": 2,
  "data": [...]
}
```

---

### 11. Complex Query ✅

**Request:** `Complex Query`

This combines ALL features:
```
?search=laptop&category=electronics&price[gte]=500&price[lte]=3000&sort=-price&page=1&limit=5
```

**Try modifying:**
- Change search term
- Change category
- Adjust price range
- Change sort order
- Adjust pagination

---

### 12. Delete Product (Soft Delete) ✅

**Request:** `Delete Product`

⚠️ **Important:** This is a SOFT delete!

1. **Replace `PRODUCT_ID_HERE`** with an actual product ID
2. Click **Send**
3. You'll get a **204 No Content** response
4. Now run "Get All Products" again - the deleted product won't appear!
5. But it's still in the database (just marked as deleted)

---

## 🎯 Quick Reference: All Endpoints

| Request | Method | What It Does |
|---------|--------|--------------|
| Create Product | POST | Add a new product |
| Get All Products | GET | List all products (with queries) |
| Get Product by ID | GET | Get single product |
| Update Product | PATCH | Modify a product |
| Delete Product | DELETE | Soft delete a product |
| Search Products | GET | Search by name/description |
| Filter by Category | GET | Filter by category |
| Filter by Price Range | GET | Filter by price |
| Sort Products | GET | Sort results |
| Pagination | GET | Paginate results |
| Complex Query | GET | Combine all features |

---

## 💡 Pro Tips

### Tip 1: Save Product IDs
When you create a product, copy its `_id` and paste it in a text file. You'll need these IDs for testing.

### Tip 2: Use Bruno Variables
You can create environment variables in Bruno:
1. Click the gear icon
2. Create a variable called `productId`
3. Set its value to an actual ID
4. Use `{{productId}}` in your URLs instead of the placeholder

### Tip 3: Combining Query Parameters
You can combine ANY query parameters:
```
?search=laptop&category=electronics&price[gte]=500&sort=-price&page=1&limit=10
```

---

## 🐛 Common Errors & Solutions

### Error: "PRODUCT_ID_HERE is not a valid ObjectId"
**Solution:** Replace the placeholder with an actual product `_id`

### Error: "Product not found" (404)
**Solution:** The ID doesn't exist or was soft-deleted. Use "Get All Products" to get valid IDs

### Error: "Please provide a product name" (400)
**Solution:** Missing required fields. Make sure you include `name`, `price`, and `category`

### Error: "connect ECONNREFUSED"
**Solution:** Server isn't running. Run `npm start` in the terminal

### Error: Category validation failed
**Solution:** Category must be one of: electronics, clothing, books, home, other

---

## ✅ Testing Checklist

- [ ] Create a product
- [ ] Get all products
- [ ] Get product by ID (with real ID!)
- [ ] Update a product
- [ ] Create 3-4 more products
- [ ] Test search
- [ ] Test category filter
- [ ] Test price range filter
- [ ] Test sorting
- [ ] Test pagination
- [ ] Test complex query
- [ ] Soft delete a product
- [ ] Verify deleted product doesn't appear in Get All

---

## 🎉 You're Done!

Once you complete all steps, you've successfully tested the entire API with all its advanced query features!
