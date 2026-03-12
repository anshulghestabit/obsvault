const express = require('express');
const helmet = require('helmet');
const cors = require('cors');
const rateLimit = require('express-rate-limit');
const hpp = require('hpp');

const limiter = rateLimit({
  windowMs: 15 * 60 * 1000,
  max: 100,
  standardHeaders: true,
  legacyHeaders: false,
  message: {
    success: false,
    message: 'Too many requests, please try again later',
    code: 'RATE_LIMIT_EXCEEDED'
  }
});

function sanitizeStrings(value) {
  if (typeof value === 'string') {
    return value
      .replace(/<script.*?>.*?<\/script>/gi, '')
      .replace(/<.*?on\\w+=".*?".*?>/gi, '')
      .replace(/javascript:/gi, '');
  }

  if (Array.isArray(value)) {
    return value.map(sanitizeStrings);
  }

  if (value && typeof value === 'object') {
    const sanitized = {};
    for (const key of Object.keys(value)) {
      sanitized[key] = sanitizeStrings(value[key]);
    }
    return sanitized;
  }

  return value;
}

function bodySanitizer(req, res, next) {
  if (req.body) {
    req.body = sanitizeStrings(req.body);
  }
  next();
}

function applySecurity(app) {
  app.use(helmet());

  app.use(cors({
    origin: '*',
    methods: ['GET', 'POST', 'PUT', 'PATCH', 'DELETE'],
    allowedHeaders: ['Content-Type', 'Authorization']
  }));

  app.use(express.json({ limit: '10kb' }));

  app.use(bodySanitizer);

  app.use(hpp());

  app.use(limiter);
}

module.exports = {
  applySecurity
};
