const express = require('express')
const router = express.Router()
const mailController = require('../controllers/mailController')

router.post('/sendRegistrationLink', mailController.sendRegistrationLink)

module.exports = router