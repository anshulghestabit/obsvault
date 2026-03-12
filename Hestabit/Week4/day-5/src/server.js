const app = require('./app');
const logger = require('./utils/logger');

const PORT = process.env.PORT || 3000;

app.listen(PORT, () => {
  logger.info({
    message: `Day 5 server running on port ${PORT}`
  });
});
