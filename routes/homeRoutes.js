const express = require('express')
const { verifyToken } = require('../middleware/homeMiddleware')
const router = express.Router()

router.get('/search', verifyToken, homeController.searchUsers)

module.exports = router