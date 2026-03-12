const Product = require('../models/Product');

class ProductRepository {
  async create(data) {
    return Product.create(data);
  }

  async findById(id) {
    return Product.findById(id);
  }

  async findPaginated(page = 1, limit = 10) {
    const skip = (page - 1) * limit;

    const [data, total] = await Promise.all([
      Product.find({})
          .sort({ createdAt: -1 })
          .skip(skip)
          .limit(limit),
      Product.countDocuments({})
    ]);

    return {
      data,
      total,
      page,
      limit,
      totalPages: Math.ceil(total / limit)
    };
  }

  async update(id, updateData) {
    return Product.findByIdAndUpdate(id, updateData, {
      new: true,
      runValidators: true
    });
  }

  async delete(id) {
    return Product.findByIdAndDelete(id);
  }
}

module.exports = new ProductRepository();