const jwt = require('jsonwebtoken')

exports.verifyToken = (req, res, next) => {
  const token = req.headers['authorization']?.split(' ')[1]
  if (!token) return res.status(403).json({error: 'Access denied'})
  
  try {
    const verified = jwt.verify(token, process.env.JWT_SECRET)
    req.user = verified
    next()
  } catch (error) {
    res.status(400).json({error: 'Invalid token.'})
  }
}
