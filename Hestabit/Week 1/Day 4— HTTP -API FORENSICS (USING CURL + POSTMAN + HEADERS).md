## **DAY 4 
### Learning Outcomes

- Headers
    
- Pagination
    
- ETag caching
    
- Understanding request–response cycle
    

---

### Tasks

1. **Perform DNS lookup and traceroute**
    

`nslookup dummyjson.com traceroute dummyjson.com`

---

2. **Using CURL**
    

`curl https://dummyjson.com/products?limit=5&skip=10`

---

3. **Modify headers**
    

- Remove `User-Agent`
    
- Send fake `Authorization` header
    
- Capture differences
    

Example:

`curl -H "Authorization: Bearer FAKE_TOKEN" https://dummyjson.com/products`

---

4. **Observe caching**
    

- Get response `ETag`
    
- Re-send request using:
    

`curl -H "If-None-Match: <etag>" https://dummyjson.com/products`

- Expect **304 Not Modified**
    

---

5. **Build a small Node HTTP server with endpoints**
    

- `/echo` → return headers
    
- `/slow?ms=3000` → delay response by query param
    
- `/cache` → return cache headers
    

---

### Deliverables

|Deliverable|Format|
|---|---|
|`curl-lab.txt`|Requests + responses|
|`api-investigation.md`|Analysis (pagination + headers + caching)|
|`server.js`|Node server|
|`screenshots`|For POSTMAN requests|

---

If you want next:

- Extract **Day 5**
    
- Walk through **Day 4 step-by-step on Ubuntu**
    
- Generate **server.js**
    
- Convert entire Week 1 into **one structured study plan**
    

Just tell me 👍