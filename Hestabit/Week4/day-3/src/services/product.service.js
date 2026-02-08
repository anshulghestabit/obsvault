const Product = require('../models/product.model');
const { AppError } = require('../middlewares/error.middleware');

class ProductService {
    async createProduct(data) {
        return await Product.create(data);
    }

    async getProducts(query) {
        // 1. Filtering
        const queryObj = { ...query };
        const excludedFields = ['page', 'sort', 'limit', 'fields', 'search'];
        excludedFields.forEach(el => delete queryObj[el]);

        // Advanced filtering: gte, gt, lte, lt
        let queryStr = JSON.stringify(queryObj);
        queryStr = queryStr.replace(/\b(gte|gt|lte|lt)\b/g, match => `$${match}`);

        let filter = JSON.parse(queryStr);

        // Search query (regex on name or description)
        if (query.search) {
            filter.$or = [
                { name: { $regex: query.search, $options: 'i' } },
                { description: { $regex: query.search, $options: 'i' } }
            ];
        }

        let queryBuilder = Product.find(filter);

        // 2. Sorting
        if (query.sort) {
            const sortBy = query.sort.split(',').join(' ');
            queryBuilder = queryBuilder.sort(sortBy);
        } else {
            queryBuilder = queryBuilder.sort('-createdAt');
        }

        // 3. Field limiting
        if (query.fields) {
            const fields = query.fields.split(',').join(' ');
            queryBuilder = queryBuilder.select(fields);
        } else {
            queryBuilder = queryBuilder.select('-__v');
        }

        // 4. Pagination
        const page = parseInt(query.page, 10) || 1;
        const limit = parseInt(query.limit, 10) || 10;
        const skip = (page - 1) * limit;

        queryBuilder = queryBuilder.skip(skip).limit(limit);

        // Execute query
        const products = await queryBuilder;
        const count = await Product.countDocuments(filter);

        return {
            results: products.length,
            total: count,
            page,
            totalPages: Math.ceil(count / limit),
            data: products
        };
    }

    async getProductById(id) {
        const product = await Product.findById(id);
        if (!product) {
            throw new AppError('Product not found', 404);
        }
        return product;
    }

    async updateProduct(id, data) {
        const product = await Product.findByIdAndUpdate(id, data, {
            new: true,
            runValidators: true
        });
        if (!product) {
            throw new AppError('Product not found', 404);
        }
        return product;
    }

    async deleteProduct(id) {
        // Soft delete
        const product = await Product.findByIdAndUpdate(id, {
            isDeleted: true,
            deletedAt: Date.now()
        }, { new: true });

        if (!product) {
            throw new AppError('Product not found', 404);
        }
        return product; // Or return null/void
    }
}

module.exports = new ProductService();
