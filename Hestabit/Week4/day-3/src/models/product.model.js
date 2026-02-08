const mongoose = require('mongoose');

const productSchema = new mongoose.Schema({
    name: {
        type: String,
        required: [true, 'Please provide a product name'],
        trim: true
    },
    price: {
        type: Number,
        required: [true, 'Please provide a product price']
    },
    description: {
        type: String,
        trim: true
    },
    category: {
        type: String,
        required: [true, 'Please provide a product category'],
        enum: ['electronics', 'clothing', 'books', 'home', 'other'],
        default: 'other'
    },
    stock: {
        type: Number,
        default: 0
    },
    isDeleted: {
        type: Boolean,
        default: false,
        select: false // Hide by default
    },
    deletedAt: {
        type: Date,
        default: null
    }
}, {
    timestamps: true,
    toJSON: { virtuals: true },
    toObject: { virtuals: true }
});

// Middleware to exclude soft-deleted documents from find queries
productSchema.pre(/^find/, function () {
    // this refers to the query object
    this.find({ isDeleted: { $ne: true } });
});

const Product = mongoose.model('Product', productSchema);

module.exports = Product;
