const http = require("http");
const { MongoClient } = require("mongodb");

const PORT = 5000;
const MONGO_URL = process.env.MONGO_URL;

const server = http.createServer(async (req, res) => {
  try {
    const client = new MongoClient(MONGO_URL);
    await client.connect();
    await client.close();

    res.writeHead(200);
    res.end("Connected to MongoDB\n");
  } catch (err) {
    res.writeHead(500);
    res.end("MongoDB connection failed\n");
  }
});

server.listen(PORT, () => {
  console.log(`API server running on port ${PORT}`);
});

