const express = require('express')
const router = express.Router()
const mailController = require('../controllers/mailController')

router.post('/send-registration-link', mailController.sendRegistrationLink)

module.exports = router