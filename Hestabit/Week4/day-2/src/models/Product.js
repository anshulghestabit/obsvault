const mongoose = require('mongoose');

const productSchema = new mongoose.Schema(
  {
    name: {
      type: String,
      required: true,
      trim: true
    },
    description: {
      type: String,
      trim: true,
      default: ''
    },
    price: {
      type: Number,
      required: true,
      min: 0
    },
    category: {
      type: String,
      required: true,
      trim: true,
      lowercase: true
    },
    tags: [
      {
        type: String,
        trim: true,
        lowercase: true
      }
    ],
    rating: {
      type: Number,
      min: 0,
      max: 5,
      default: 0
    },
    status: {
      type: String,
      enum: ['active', 'inactive'],
      default: 'active'
    }
  },
  {
    timestamps: true,
    toJSON: { virtuals: true },
    toObject: { virtuals: true }
  }
);

productSchema.virtual('ratingLabel').get(function () {
  if (this.rating >= 4.5) return 'Excellent';
  if (this.rating >= 3.5) return 'Good';
  if (this.rating >= 2.5) return 'Average';
  return 'Low';
});

productSchema.index({ status: 1, createdAt: -1 });

module.exports = mongoose.model('Product', productSchema);
