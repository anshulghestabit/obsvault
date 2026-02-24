const Product = require('../models/Product');

class ProductRepository {
  async create(data) {
    try {
      return await Product.create(data);
    } catch (error) {
      throw error;
    }
  }

  async findById(id) {
    try {
      return await Product.findById(id).populate('owner').lean();
    } catch (error) {
      throw error;
    }
  }

  async findPaginated(filter = {}, options = {}) {
    try {
      const { page = 1, limit = 10, sort = { createdAt: -1 } } = options;
      const skip = (page - 1) * limit;

      const [data, total] = await Promise.all([
        Product.find(filter)
          .sort(sort)
          .skip(skip)
          .limit(limit)
          .populate('owner')
          .lean(),
        Product.countDocuments(filter)
      ]);

      return {
        data,
        total,
        page,
        totalPages: Math.ceil(total / limit)
      };
    } catch (error) {
      throw error;
    }
  }

  async update(id, data) {
    try {
      return await Product.findByIdAndUpdate(id, data, {
        new: true,
        runValidators: true
      }).lean();
    } catch (error) {
      throw error;
    }
  }

  async delete(id) {
    try {
      return await Product.findByIdAndDelete(id).lean();
    } catch (error) {
      throw error;
    }
  }
}

module.exports = new ProductRepository();
