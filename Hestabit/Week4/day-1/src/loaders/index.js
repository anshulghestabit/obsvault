const expressLoader = require('./express');
const mongooseLoader = require('./mongoose');
const routesLoader = require('./routes');
const Logger = require('../utils/logger');

module.exports = async ({ expressApp }) => {

  await mongooseLoader();
  Logger.info('DB connected');

  await expressLoader({ app: expressApp });
  Logger.info('Express configured');

  await routesLoader({ app: expressApp });
  Logger.info('Routes mounted');

};

