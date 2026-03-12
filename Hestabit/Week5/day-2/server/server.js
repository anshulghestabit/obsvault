const http = require("http");
const { MongoClient } = require("mongodb");

const PORT = 5000;
const MONGO_URL = process.env.MONGO_URL;

const server = http.createServer(async (req, res) => {
  if (req.url === "/api") {
    try {
      const client = new MongoClient(MONGO_URL);
      await client.connect();
      await client.db("mydb").command({ ping: 1 });
      await client.close();

      res.writeHead(200, {
        "Content-Type": "text/plain",
        "Access-Control-Allow-Origin": "*"
      });
      res.end("Client -> Server -> MongoDB connection successful");
    } catch (err) {
      res.writeHead(500, {
        "Content-Type": "text/plain",
        "Access-Control-Allow-Origin": "*"
      });
      res.end("MongoDB connection failed");
    }
    return;
  }

  res.writeHead(200, { "Content-Type": "text/plain" });
  res.end("Server is running");
});

server.listen(PORT, () => {
  console.log(`API server running on port ${PORT}`);
});