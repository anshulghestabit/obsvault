const Product = require('../models/Product');

class ProductRepository {

  // CREATE
  async create(data) {
    return Product.create(data);
  }

  // READ: By ID
  async findById(id) {
    return Product.findById(id);
  }

  // READ: All (with pagination)
  async findPaginated(page = 1, limit = 10, filter = {}) {

    const skip = (page - 1) * limit;

    return Product.find(filter)
      .sort({ createdAt: -1 })
      .skip(skip)
      .limit(limit);
  }

  // READ: By Status (optimized by index)
  async findByStatus(status, page = 1, limit = 10) {

    const skip = (page - 1) * limit;

    return Product.find({ status })
      .sort({ createdAt: -1 })
      .skip(skip)
      .limit(limit);
  }

  // UPDATE
  async update(id, data) {
    return Product.findByIdAndUpdate(
      id,
      data,
      { new: true, runValidators: true }
    );
  }

  // DELETE (Hard delete for now)
  async delete(id) {
    return Product.findByIdAndDelete(id);
  }

  // COUNT (for pagination meta)
  async count(filter = {}) {
    return Product.countDocuments(filter);
  }

}

module.exports = new ProductRepository();

