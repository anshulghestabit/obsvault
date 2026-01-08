const os = require('os');

console.log("System Introspection Report");
console.log("---------------------------");

console.log("OS:", os.platform());
console.log("Architecture:", os.arch());
console.log("CPU Cores:", os.cpus().length);
console.log("Total Memory:", (os.totalmem() / (1024 ** 3)).toFixed(2), "GB");
console.log("System Uptime:", (os.uptime() / 3600).toFixed(2), "hours");
console.log("Current Logged User:", os.userInfo().username);
console.log("Node Path:", process.execPath);
