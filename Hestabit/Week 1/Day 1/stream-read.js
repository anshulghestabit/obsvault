const fs = require('fs');

const startTime = process.hrtime.bigint();
const startMemory = process.memoryUsage().rss;

const stream = fs.createReadStream('largefile.bin');

stream.on('data', () => {});

stream.on('end', () => {
  const endTime = process.hrtime.bigint();
  const endMemory = process.memoryUsage().rss;

  console.log("STREAM READ RESULTS");
  console.log("-------------------");
  console.log("Time (ms):", Number(endTime - startTime) / 1e6);
  console.log("Memory Used (MB):", (endMemory - startMemory) / (1024 * 1024));
});
