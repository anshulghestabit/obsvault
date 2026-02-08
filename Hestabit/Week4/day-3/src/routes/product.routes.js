const express = require('express');
const productController = require('../controllers/product.controller');

const router = express.Router();

router
    .route('/')
    .get(productController.getProducts.bind(productController))
    .post(productController.createProduct.bind(productController));

router
    .route('/:id')
    .get(productController.getProductById.bind(productController))
    .patch(productController.updateProduct.bind(productController))
    .delete(productController.deleteProduct.bind(productController));

module.exports = router;
