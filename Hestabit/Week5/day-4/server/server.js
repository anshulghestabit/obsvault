const http = require("http");

const PORT = 3000;

const server = http.createServer((req, res) => {
    if (req.url === "/api") {
        res.writeHead(200, { "Content-Type": "text/plain" });
        res.end("HTTPS reverse proxy is working\n");
        return;
    }

    res.writeHead(200, { "Content-Type": "text/plain" });
    res.end("Backend server is running\n");
});

server.listen(PORT, () => {
    console.log(`Server running on port ${PORT}`);
});