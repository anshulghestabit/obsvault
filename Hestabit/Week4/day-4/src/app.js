const express = require('express');
const { applySecurity } = require('./middlewares/security');
const testRoutes = require('./routes/test.routes');

const app = express();

applySecurity(app);

app.use('/api', testRoutes);

module.exports = app;