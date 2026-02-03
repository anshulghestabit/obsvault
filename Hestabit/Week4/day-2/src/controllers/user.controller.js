const repo = require('../repositories/user.repository');

exports.create = async (req, res) => {

  const user = await repo.create(req.body);

  res.json(user);
};

