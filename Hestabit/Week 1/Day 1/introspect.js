const os = require('os');

// Helper to format bytes to GB
const toGB = (bytes) => (bytes / (1024 ** 3)).toFixed(2) + ' GB';

// Helper to format uptime
const formatUptime = (sec) => {
    const h = Math.floor(sec / 3600);
    const m = Math.floor((sec % 3600) / 60);
    return `${h}h ${m}m`;
};

console.log("--- System Introspection ---");
console.log(`OS: ${os.type()} ${os.release()}`);
console.log(`Architecture: ${os.arch()}`);
console.log(`CPU Cores: ${os.cpus().length}`);
console.log(`Total Memory: ${toGB(os.totalmem())}`);
console.log(`System Uptime: ${formatUptime(os.uptime())}`);
console.log(`Current Logged User: ${os.userInfo().username}`);
console.log(`Node Path: ${process.execPath}`);
