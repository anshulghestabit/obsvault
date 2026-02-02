const routes = require('../routes');

module.exports = ({ app }) => {
  app.use('/api', routes);

  return app;
};

