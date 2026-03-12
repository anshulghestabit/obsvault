const express = require('express');
const { validate, userSchema, productSchema } = require('../middlewares/validate');

const router = express.Router();

router.post('/users', validate(userSchema), (req, res) => {
    res.status(201).json({
        success: true,
        message: 'User payload validated successfully',
        data: req.body
    });
});

router.post('/products', validate(productSchema), (req, res) => {
    res.status(201).json({
        success: true,
        message: 'Product payload validated successfully',
        data: req.body
    });
});

router.get('/health', (req, res) => {
    res.status(200).json({
        success: true,
        message: 'Day 4 security module is running'
    });
});

module.exports = router;