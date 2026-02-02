const mongoose = require('mongoose');
const config = require('../config');

module.exports = async function () {
  const connection = await mongoose.connect(config.databaseURL, {
    // These options ensure stable connection
    serverSelectionTimeoutMS: 5000, 
  });
  
  console.log(`DB Loaded:`);
  return connection.connection.db;
};
