const User = require('../models/User')
const bcrypt = require('bcryptjs')
const jwt = require('jsonwebtoken')

exports.registerUser = async (req, res) => {
  const { username, email, password } = req.body

  if (!username || !email || !password) return res.status(400).json({error: 'Please fill in the fields.'}) 
    
  try {
    const hashedPassword = await bcrypt.hash(password, 10)
    const newUser = new User({
      username: username,
      email: email,
      password: hashedPassword
    })
    await newUser.save()
    res.status(201).json({ message: 'User registered successfully.' })
  } catch (error) {
    if (error.name === 'ValidationError') {
      return res.status(400).json({ error: error.errors })
    }
    res.status(500).json({error: error.message})
  }
}
  
exports.loginUser = async (req, res) => {
  const { email, password } = req.body
  
  if (!email || !password) return res.status(400).json({error: 'Please fill in the fields.'}) 
  
  try {
    const user = await User.findOne({ email })
    if (!user) return res.status(404).json({message: 'User not found.'})
    
    const isMatch = await bcrypt.compare(password, user.password)
    if (!isMatch) return res.status(400).json({error: 'Invalid credentials.'})

    const token = jwt.sign({ id: user._id }, process.env.JWT_SECRET, {expiresIn: '1h'})
    res.status(200).json({ token })
  } catch (error) {
    res.status(500).json({error: error.message})
  }
}

exports.getUserProfile = async (req, res) => {
  try {
    const user = await User.findById(req.user.id).select('-password')
    if (!user) return res.status(404).json({ error: 'User not found.' })

    res.status(200).json(user)
  } catch (error) {
    res.status(500).json({error: error.message})
  }
}