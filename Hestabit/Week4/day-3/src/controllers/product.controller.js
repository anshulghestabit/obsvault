const productService = require('../services/product.service');
const { AppError } = require('../middlewares/error.middleware');

class ProductController {
    async createProduct(req, res, next) {
        try {
            const product = await productService.createProduct(req.body);
            res.status(201).json({
                status: 'success',
                data: product
            });
        } catch (error) {
            next(error);
        }
    }

    async getProducts(req, res, next) {
        try {
            const result = await productService.getProducts(req.query);
            res.status(200).json({
                status: 'success',
                ...result
            });
        } catch (error) {
            next(error);
        }
    }

    async getProductById(req, res, next) {
        try {
            const product = await productService.getProductById(req.params.id);
            res.status(200).json({
                status: 'success',
                data: product
            });
        } catch (error) {
            next(error);
        }
    }

    async updateProduct(req, res, next) {
        try {
            const product = await productService.updateProduct(req.params.id, req.body);
            res.status(200).json({
                status: 'success',
                data: product
            });
        } catch (error) {
            next(error);
        }
    }

    async deleteProduct(req, res, next) {
        try {
            await productService.deleteProduct(req.params.id);
            res.status(204).json({
                status: 'success',
                data: null
            });
        } catch (error) {
            next(error);
        }
    }
}

module.exports = new ProductController();
