const User = require('../models/User');

class UserRepository {
  async create(data) {
    try {
      const user = await User.create(data);
      return user;
    } catch (error) {
      throw error;
    }
  }

  async findById(id) {
    try {
      return await User.findById(id).lean();
    } catch (error) {
      throw error;
    }
  }

  async findPaginated(filter = {}, options = {}) {
    try {
      const { page = 1, limit = 10, sort = { createdAt: -1 } } = options;

      const skip = (page - 1) * limit;

      const [data, total] = await Promise.all([
        User.find(filter)
          .sort(sort)
          .skip(skip)
          .limit(limit)
          .lean(),
        User.countDocuments(filter)
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
      return await User.findByIdAndUpdate(id, data, {
        new: true,
        runValidators: true
      }).lean();
    } catch (error) {
      throw error;
    }
  }

  async delete(id) {
    try {
      return await User.findByIdAndDelete(id).lean();
    } catch (error) {
      throw error;
    }
  }
}

module.exports = new UserRepository();
