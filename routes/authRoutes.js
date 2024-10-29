const express = require('express')
const router = express.Router()
const authController = require('../controllers/authController')
const { verifyToken } = require('../middleware/authMiddleware')


router.post('/register', authController.registerUser)
router.post('/login', authController.loginUser)
router.post('/getUserProfile', verifyToken, authController.getUserProfile)


module.exports = router