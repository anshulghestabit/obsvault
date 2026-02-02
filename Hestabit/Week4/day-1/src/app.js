const express = require('express');
const config = require('./config');
const loaders = require('./loaders'); // Imports src/loaders/index.js
const Logger = require('./utils/logger');
const routes = require('./loaders/routes.js');
async function startServer() {
  const app = express();

  try {
    // Attempt to load everything
    await loaders({ expressApp: app });
    
    // If successful, start listening
    app.listen(config.port, () => {
      Logger.info(`Server listening on port: ${config.port}`);
      Logger.info('========================');
      Logger.info(`Server running: ${config.port}`);
      Logger.info(`Environment: ${config.env}`);
      Logger.info('Boot successful');
      Logger.info('========================');
    });

  } catch (err) {
    // IF IT CRASHES, PRINT THE ERROR HERE
    Logger.error('Error starting server: %o', err);
    process.exit(1);
  }
}

startServer();
