const User = require('../models/User');

class UserRepository {

  create(data) {
    return User.create(data);
  }

  findById(id) {
    return User.findById(id);
  }

  findByEmail(email) {
    return User.findOne({ email });
  }

  findPaginated(page = 1, limit = 10) {
    return User.find()
      .skip((page - 1) * limit)
      .limit(limit);
  }

  update(id, data) {
    return User.findByIdAndUpdate(id, data, { new: true });
  }

  delete(id) {
    return User.findByIdAndDelete(id);
  }

}

module.exports = new UserRepository();

