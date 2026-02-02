const express = require('express');
const cors = require('cors');
const helmet = require('helmet');

module.exports = async ({ app }) => {
  // 1. Health Checks
  app.get('/status', (req, res) => {
    res.status(200).end();
  });

  // 2. Useful Middleware
  app.enable('trust proxy');
  app.use(cors());
  app.use(helmet());
  app.use(express.json());

  // Return the app
  return app;
};
