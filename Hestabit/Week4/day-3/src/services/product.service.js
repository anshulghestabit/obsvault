const productRepository = require('../repositories/product.repository');
const ApiError = require('../utils/api-error');

class ProductService {
    buildQuery(queryParams) {
        const {
            search,
            minPrice,
            maxPrice,
            tags,
            includeDeleted
        } = queryParams;

        const filter = {};

        if (includeDeleted !== 'true') {
            filter.deletedAt = null;
        }

        if (search) {
            filter.$or = [
                { name: { $regex: search, $options: 'i' } },
                { description: { $regex: search, $options: 'i' } },
                { category: { $regex: search, $options: 'i' } }
            ];
        }

        if (minPrice || maxPrice) {
            filter.price = {};
            if (minPrice) filter.price.$gte = Number(minPrice);
            if (maxPrice) filter.price.$lte = Number(maxPrice);
        }

        if (tags) {
            const tagList = tags.split(',').map(tag => tag.trim().toLowerCase());
            filter.tags = { $in: tagList };
        }

        return filter;
    }

    buildSort(sortParam) {
        if (!sortParam) return { createdAt: -1 };

        const [field, order] = sortParam.split(':');
        return {
            [field]: order === 'asc' ? 1 : -1
        };
    }

    async getProducts(queryParams) {
        const page = Number(queryParams.page) || 1;
        const limit = Number(queryParams.limit) || 10;
        const skip = (page - 1) * limit;

        const filter = this.buildQuery(queryParams);
        const sort = this.buildSort(queryParams.sort);

        const { data, total } = await productRepository.findWithQuery(
            filter,
            sort,
            skip,
            limit
        );

        return {
            data,
            meta: {
                total,
                page,
                limit,
                totalPages: Math.ceil(total / limit)
            }
        };
    }

    async deleteProduct(id) {
        const product = await productRepository.findById(id);

        if (!product) {
            throw new ApiError('Product not found', 'PRODUCT_NOT_FOUND', 404);
        }

        if (product.deletedAt) {
            throw new ApiError('Product already deleted', 'PRODUCT_ALREADY_DELETED', 400);
        }

        return productRepository.softDelete(id);
    }

    async seedProducts() {
        const sampleProducts = [
            {
                name: 'iPhone 15',
                description: 'Premium smartphone',
                price: 79999,
                category: 'electronics',
                tags: ['apple', 'phone'],
                rating: 4.7,
                status: 'active'
            },
            {
                name: 'Samsung Galaxy S24',
                description: 'Android flagship phone',
                price: 69999,
                category: 'electronics',
                tags: ['samsung', 'phone'],
                rating: 4.5,
                status: 'active'
            },
            {
                name: 'Noise Smartwatch',
                description: 'Affordable smartwatch',
                price: 4999,
                category: 'wearables',
                tags: ['watch', 'smart'],
                rating: 4.0,
                status: 'active'
            }
        ];

        for (const item of sampleProducts) {
            await productRepository.create(item);
        }

        return { message: 'Sample products inserted' };
    }
}

module.exports = new ProductService();