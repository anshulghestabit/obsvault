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
        status: {
            type: String,
            enum: ['active', 'inactive'],
            default: 'active'
        },
        rating: {
            type: Number,
            min: 0,
            max: 5,
            default: 0
        },
        deletedAt: {
            type: Date,
            default: null
        }
    },
    {
        timestamps: true
    }
);

productSchema.index({ status: 1, createdAt: -1 });

module.exports = mongoose.model('Product', productSchema);