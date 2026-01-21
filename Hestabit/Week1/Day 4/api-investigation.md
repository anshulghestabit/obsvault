# API Forensic Analysis

## 1. Pagination
The API uses limit and skip parameters.
limit=5 restricts the result array to 5 items.
skip=10 bypasses the first 10 items, returning IDs 11 to 15.

## 2. Headers
Removing the User-Agent did not block the request, indicating the API is permissive.
Adding a fake Authorization header did not trigger a 401/403 error, suggesting public endpoints ignore auth headers.

## 3. Caching
The server provides an ETag in the response headers.
When sending the If-None-Match header with the captured ETag, the server returns status 304 Not Modified.
This confirms the server supports client-side caching to save bandwidth.
