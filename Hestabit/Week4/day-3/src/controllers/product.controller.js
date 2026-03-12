
const productService = require('../services/product.service');

class ProductController {
    async getProducts(req, res, next) {
        try {
            const result = await productService.getProducts(req.query);
            res.status(200).json({
                success: true,
                ...result
            });
        } catch (error) {
            next(error);
        }
    }

    async deleteProduct(req, res, next) {
        try {
            const result = await productService.deleteProduct(req.params.id);
            res.status(200).json({
                success: true,
                message: 'Product soft deleted successfully',
                data: result
            });
        } catch (error) {
            next(error);
        }
    }

    async seedProducts(req, res, next) {
        try {
            const result = await productService.seedProducts();
            res.status(201).json({
                success: true,
                ...result
            });
        } catch (error) {
            next(error);
        }
    }
}

module.exports = new ProductController();