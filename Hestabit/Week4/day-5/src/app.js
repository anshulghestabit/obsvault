const express = require('express');
const tracingMiddleware = require('./utils/tracing');
const emailRoutes = require('./routes/email.routes');
const logger = require('./utils/logger');

const app = express();

app.use(express.json({ limit: '10kb' }));
app.use(tracingMiddleware);

app.use((req, res, next) => {
  logger.info({
    message: 'Incoming request',
    requestId: req.requestId,
    method: req.method,
    path: req.originalUrl
  });
  next();
});

app.use('/api', emailRoutes);

module.exports = app;
