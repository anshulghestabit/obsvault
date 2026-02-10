const http = require("http");

const PORT = 3000;

const server = http.createServer((req, res) => {
  console.log("Received request:", req.method, req.url);

  res.writeHead(200, { "Content-Type": "text/plain" });
  res.end("Hello from inside a Docker container\n");
});

server.listen(PORT, () => {
  console.log(`Server running on port ${PORT}`);
});

