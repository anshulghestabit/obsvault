const dotenv = require('dotenv');

// Load the .env file
const envFound = dotenv.config();

if (envFound.error) {
  // CRITICAL: If .env is missing, the app should crash immediately.
  throw new Error("Couldn't find .env file");
}

module.exports = {
  port: parseInt(process.env.PORT, 10),
  databaseURL: process.env.MONGO_URI,
  // We use this to switch between 'dev' and 'prod' modes
  nodeEnv: process.env.NODE_ENV || 'development',
  logs:{
    level: process.env.LOG_LEVEL || 'info',
  },
};
