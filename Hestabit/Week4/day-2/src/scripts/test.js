const mongoose = require('mongoose');
const connectDB = require('../loaders/db');
const User = require('../models/User');
const Product = require('../models/Product');
const userRepository = require('../repositories/user.repository');
const productRepository = require('../repositories/product.repository');

async function run() {
  try {
    await connectDB();

    await User.deleteMany({});
    await Product.deleteMany({});

    console.log('\n--- Creating User ---');
    const user = await userRepository.create({
      firstName: 'Anshul',
      lastName: 'Garg',
      email: 'ANSHUL@example.com',
      password: 'secret123',
      status: 'active'
    });

    console.log('User created:', {
      id: user._id.toString(),
      fullName: user.fullName,
      email: user.email,
      passwordHashed: user.password !== 'secret123',
      status: user.status
    });

    console.log('\n--- Creating Product ---');
    const product = await productRepository.create({
      name: 'iPhone 15',
      description: 'Premium smartphone',
      price: 79999,
      category: 'Electronics',
      tags: ['Apple', 'Phone', 'Premium'],
      rating: 4.7,
      status: 'active'
    });

    console.log('Product created:', {
      id: product._id.toString(),
      name: product.name,
      category: product.category,
      rating: product.rating,
      ratingLabel: product.ratingLabel
    });

    console.log('\n--- Find User By ID ---');
    const foundUser = await userRepository.findById(user._id);
    console.log({
      id: foundUser._id.toString(),
      fullName: foundUser.fullName,
      email: foundUser.email
    });

    console.log('\n--- Find Product By ID ---');
    const foundProduct = await productRepository.findById(product._id);
    console.log({
      id: foundProduct._id.toString(),
      name: foundProduct.name,
      ratingLabel: foundProduct.ratingLabel
    });

    console.log('\n--- Paginated Users ---');
    const paginatedUsers = await userRepository.findPaginated(1, 10);
    console.log({
      total: paginatedUsers.total,
      page: paginatedUsers.page,
      totalPages: paginatedUsers.totalPages
    });

    console.log('\n--- Paginated Products ---');
    const paginatedProducts = await productRepository.findPaginated(1, 10);
    console.log({
      total: paginatedProducts.total,
      page: paginatedProducts.page,
      totalPages: paginatedProducts.totalPages
    });

    console.log('\n--- Update User ---');
    const updatedUser = await userRepository.update(user._id, {
      status: 'inactive'
    });
    console.log({
      id: updatedUser._id.toString(),
      status: updatedUser.status
    });

    console.log('\n--- Update Product ---');
    const updatedProduct = await productRepository.update(product._id, {
      price: 74999
    });
    console.log({
      id: updatedProduct._id.toString(),
      price: updatedProduct.price
    });

    console.log('\n--- Delete User ---');
    const deletedUser = await userRepository.delete(user._id);
    console.log({
      id: deletedUser._id.toString(),
      email: deletedUser.email
    });

    console.log('\n--- Delete Product ---');
    const deletedProduct = await productRepository.delete(product._id);
    console.log({
      id: deletedProduct._id.toString(),
      name: deletedProduct.name
    });

    console.log('\nDay 2 test completed successfully.');
  } catch (error) {
    console.error('Day 2 test failed:', error);
  } finally {
    await mongoose.connection.close();
    process.exit(0);
  }
}

run();
