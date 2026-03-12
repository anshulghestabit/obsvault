const express = require('express');
const productController = require('../controllers/product.controller');

const router = express.Router();

router.get('/products', productController.getProducts);
router.delete('/products/:id', productController.deleteProduct);
router.post('/products/seed', productController.seedProducts);

module.exports = router;