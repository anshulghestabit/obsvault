const User = require('../models/User');

class UserRepository {
  async create(data) {
    return User.create(data);
  }

  async findById(id) {
    return User.findById(id);
  }

  async findPaginated(page = 1, limit = 10) {
    const skip = (page - 1) * limit;

    const [data, total] = await Promise.all([
      User.find({})
          .sort({ createdAt: -1 })
          .skip(skip)
          .limit(limit),
      User.countDocuments({})
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
    return User.findByIdAndUpdate(id, updateData, {
      new: true,
      runValidators: true
    });
  }

  async delete(id) {
    return User.findByIdAndDelete(id);
  }
}

module.exports = new UserRepository();