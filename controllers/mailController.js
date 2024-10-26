const nodemailer = require('nodemailer')

const transporter = nodemailer.createTransport({
  service: 'Gmail',
  auth: {
    user: process.env.SMTP_USER,
    pass: process.env.SMTP_PASS
  }
})

exports.sendRegistrationLink = async (req, res) => {
  const { email } = req.body

  const registrationLink = `${process.env.CLIENT_URL}/register?email=${encodeURIComponent(email)}`

  const mailOptions = {
    from: process.env.SMTP_MAIL,
    to: email,
    subject: 'Registration Link',
    text: `Click this link to register: ${registrationLink}`,
    html: '<p>Click this link to register: <a href={registrationLink}>Get Link</a></p>',
  }

  try {
    await transporter.sendMail(mailOptions)
    res.status(200).json({message: 'Registration link sent successfully.'})
  } catch (error) {
    res.status(500).json({error: 'Failed to send email.'})
  }
}
