const http = require("http");

const PORT = 3000;
const INSTANCE_NAME = process.env.INSTANCE_NAME || "unknown-server";

const server = http.createServer((req, res) => {
  if (req.url === "/api") {
    res.writeHead(200, { "Content-Type": "text/plain" });
    res.end(`Response from ${INSTANCE_NAME}\n`);
    return;
  }

  res.writeHead(200, { "Content-Type": "text/plain" });
  res.end(`Server running: ${INSTANCE_NAME}\n`);
});

server.listen(PORT, () => {
  console.log(`${INSTANCE_NAME} running on port ${PORT}`);
});