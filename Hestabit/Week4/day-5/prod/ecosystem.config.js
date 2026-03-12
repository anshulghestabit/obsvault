module.exports = {
  apps: [
    {
      name: 'day5-api',
      script: 'src/server.js',
      instances: 1,
      exec_mode: 'fork',
      env: {
        PORT: 3000,
        REDIS_HOST: '127.0.0.1',
        REDIS_PORT: 6379,
        LOG_LEVEL: 'info'
      }
    }
  ]
};
