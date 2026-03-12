class ApiError extends Error {
    constructor(message, code = 'INTERNAL_ERROR', statusCode = 500) {
        super(message);
        this.code = code;
        this.statusCode = statusCode;
    }
}

module.exports = ApiError;