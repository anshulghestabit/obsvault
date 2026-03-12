const express = require('express');
const { queueEmail } = require('../controllers/email.controller');

const router = express.Router();

router.post('/emails/queue', queueEmail);

router.get('/health', (req, res) => {
  res.status(200).json({
    success: true,
    message: 'Day 5 API is running',
    requestId: req.requestId
  });
});

module.exports = router;
