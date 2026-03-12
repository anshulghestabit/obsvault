const Product = require('../models/Product');

class ProductRepository {
    async create(data) {
        return Product.create(data);
    }

    async findById(id) {
        return Product.findById(id);
    }

    async findWithQuery(filter, sort, skip, limit) {
        const [data, total] = await Promise.all([
            Product.find(filter)
                .sort(sort)
                .skip(skip)
                .limit(limit),
            Product.countDocuments(filter)
        ]);

        return { data, total };
    }

    async softDelete(id) {
        return Product.findByIdAndUpdate(
            id,
            { deletedAt: new Date() },
            { new: true }
        );
    }
}

module.exports = new ProductRepository();