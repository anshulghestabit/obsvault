const { z } = require('zod');

const userSchema = z.object({
    firstName: z.string().trim().min(2, 'First name must be at least 2 characters'),
    lastName: z.string().trim().min(2, 'Last name must be at least 2 characters'),
    email: z.email('Invalid email format').trim().toLowerCase(),
    password: z.string().min(6, 'Password must be at least 6 characters'),
    status: z.enum(['active', 'inactive']).optional()
});

const productSchema = z.object({
    name: z.string().trim().min(2, 'Product name must be at least 2 characters'),
    description: z.string().trim().optional().default(''),
    price: z.number().nonnegative('Price must be non-negative'),
    category: z.string().trim().min(2, 'Category is required').toLowerCase(),
    tags: z.array(z.string().trim().toLowerCase()).optional(),
    rating: z.number().min(0, 'Rating must be at least 0').max(5, 'Rating cannot exceed 5').optional(),
    status: z.enum(['active', 'inactive']).optional()
});

function validate(schema) {
    return (req, res, next) => {
        try {
            const parsedData = schema.parse(req.body);
            req.body = parsedData;
            next();
        } catch (error) {
            return res.status(400).json({
                success: false,
                message: 'Validation failed',
                code: 'VALIDATION_ERROR',
                errors: error.issues || [],
                timestamp: new Date().toISOString(),
                path: req.originalUrl
            });
        }
    };
}

module.exports = {
    validate,
    userSchema,
    productSchema
};