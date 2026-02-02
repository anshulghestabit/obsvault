const router = require('express').Router();

// Test route
router.get('/test', (req, res) => {
  res.json({ ok: true, message: 'API working' });
});

module.exports = router;
