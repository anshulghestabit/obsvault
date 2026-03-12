module.exports = (error, req, res, next) => {
    const statusCode = error.statusCode || 500;
    const code = error.code || 'INTERNAL_ERROR';
    const message = error.message || 'Something went wrong';

    res.status(statusCode).json({
        success: false,
        message,
        code,
        timestamp: new Date().toISOString(),
        path: req.originalUrl
    });
};