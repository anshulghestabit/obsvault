const app = require('./app');
const connectDB = require('./loaders/db');
const config = require('./config');

async function startServer() {
    await connectDB();

    app.listen(config.port, () => {
        console.log(`Server running on port ${config.port}`);
    });
}

startServer();