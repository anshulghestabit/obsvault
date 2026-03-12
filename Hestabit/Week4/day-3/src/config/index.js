module.exports = {
    port: process.env.PORT || 3000,
    database: {
        uri: process.env.MONGO_URI || 'mongodb://127.0.0.1:27017/week4_day3_db',
        options: {}
    }
};