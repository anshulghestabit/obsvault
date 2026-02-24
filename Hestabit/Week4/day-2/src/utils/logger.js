const winston = require('winston');
const path = require('path');
const config = require('../config');

const { combine, timestamp, errors, json, printf } = winston.format;

const consoleFormat = printf(({ level, message, timestamp, stack }) => {
  return `${timestamp} [${level.toUpperCase()}] ${stack || message}`;
});

class Logger {
  constructor() {
    this.logger = winston.createLogger({
      level: config.logLevel,
      format: combine(
        timestamp(),
        errors({ stack: true }),
        json()
      ),
      transports: [
        new winston.transports.File({
          filename: path.join(__dirname, '../logs/error.log'),
          level: 'error'
        }),
        new winston.transports.File({
          filename: path.join(__dirname, '../logs/combined.log')
        })
      ]
    });

    if (config.nodeEnv !== 'production') {
      this.logger.add(
        new winston.transports.Console({
          format: combine(timestamp(), consoleFormat)
        })
      );
    }
  }

  info(message, meta = {}) {
    this.logger.info(message, meta);
  }

  error(message, meta = {}) {
    this.logger.error(message, meta);
  }

  warn(message, meta = {}) {
    this.logger.warn(message, meta);
  }
}

module.exports = new Logger();
