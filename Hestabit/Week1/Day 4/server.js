const http = require('node:http');
const url = require('node:url');

const server = http.createServer((req, res) => {
    const parsedUrl = url.parse(req.url, true);
    const path = parsedUrl.pathname;

    if (path === '/echo') {
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify(req.headers));
    } else if (path === '/slow') {
        const ms = Number.parseInt(parsedUrl.query.ms) || 1000;
        setTimeout(() => {
            res.writeHead(200, { 'Content-Type': 'text/plain' });
            res.end(`Response delayed by ${ms}ms`);
        }, ms);
    } else if (path === '/cache') {
        res.writeHead(200, {
            'Content-Type': 'text/plain',
            'Cache-Control': 'public, max-age=60',
            'ETag': '"test-etag-123"'
        });
        res.end('cached response');
    } else {
        res.writeHead(404, { 'Content-Type': 'text/plain' });
        res.end('Not Found');
    }
});

server.listen(3000, () => {
    console.log('Server running on port 3000');
});
