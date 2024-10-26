const express = require('express')
const dotenv = require('dotenv')
const cors = require('cors')
const connectDB = require('./config/db')
const authRoutes = require('./routes/authRoutes')
const mailRoutes = require('./routes/mailRoutes')


dotenv.config()

const app = express()
app.use(cors())
app.use(express.json())

connectDB()

app.use('/api/auth', authRoutes)
app.use('/api/mail', mailRoutes)

const PORT = process.env.PORT || 5000
app.listen(PORT, () => {
  console.log('Server is running on port: ', PORT)
})