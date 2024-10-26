const User = require('../models/User')
const bcrypt = require('bcryptjs')
const jwt = require('jsonwebtoken')
const router = require('../routes/homeRoutes')

exports.searchUsers = async (req, res) => {
  const { searchWord } = req.body

  if (!searchWord) return res.status(400).json({error: 'Search word is not provided.'})
  
  try {
    const users = await User.find({
      $or: [
        {username: {$regex: searchWord, $options: 'i'}},
        {email: {$regex: searchWord, $options: 'i'}}
      ]
    }).select('-password')

    res.status(200).json(users)
  } catch (error) {
    res.status(500).json({error: 'Server error.'})
  }
}

module.exports = router