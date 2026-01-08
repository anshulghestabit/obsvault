const fs = require("fs");

console.time("buffer");

const startMem = process.memoryUsage().rss;

fs.readFile("logs/largefile.bin", (err, data) => {
  if (err) throw err;

  const endMem = process.memoryUsage().rss;

  console.timeEnd("buffer");
  console.log("Memory used (MB):", (endMem - startMem) / 1024 / 1024);
});

