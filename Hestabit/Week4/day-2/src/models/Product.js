const mongoose = require('mongoose');

const productSchema = new mongoose.Schema({

  name: {
    type: String,
    required: true
  },

  price: {
    type: Number,
    min: 0,
    required: true
  },

  tags: [{
    type: String
  }],

  rating: {
    type: Number,
    min: 0,
    max: 5,
    default: 0
  },

  status: {
    type: String,
    default: 'active'
  }

}, {
  timestamps: true
});

productSchema.index({
  status: 1,
  createdAt: -1
});

module.exports = mongoose.model('Product', productSchema);

