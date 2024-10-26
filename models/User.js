const mongoose = require('mongoose')


const emailRegex = /^[^\s@]+@[^\s@]+\.[^\s@]+$/;

const userSchema = new mongoose.Schema({
  username: {
    type: String,
    required: true,
    maxlength: 50
  },
  email: {
    type: String,
    required: true,
    unique: true,
    match: emailRegex
  },
  password: {
    type: String,
    required: true,
    minLength: 8
  },
  picture: {
    type: String,
    default: process.env.SERVER_URL + '/api/media/default_picture.png'
  },
  online: {
    type: Boolean,
    default: false
  },
  joinDate: {
    type: Date,
    default: Date.now
  }
})

const User = mongoose.model('User', userSchema)

module.exports = User
