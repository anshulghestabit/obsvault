const mongoose = require('mongoose');

const userSchema = new mongoose.Schema({

  name: {
    type: String,
    required: true,
    trim: true
  },

  email: {
    type: String,
    required: true,
    unique: true,
    lowercase: true
  },

  password: {
    type: String,
    required: true,
    minlength: 6
  },

  status: {
    type: String,
    default: 'active'
  }

}, {
  timestamps: true
});
userSchema.pre('save', function () {

  if (!this.isModified('password')) return;

  this.password = 'hashed_' + this.password;

});
userSchema.pre('save', function () {

  if (!this.isModified('password')) return;

  this.password = 'hashed_' + this.password;

});

module.exports = mongoose.model('User', userSchema);

