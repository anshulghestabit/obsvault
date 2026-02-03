const router = require('express').Router();
const userCtrl = require('../controllers/user.controller');
router.post('/users', userCtrl.create);
module.exports = router;

