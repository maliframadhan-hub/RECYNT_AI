const express = require('express');
const cors = require('cors');
const path = require('path');
require('dotenv').config();

const authRoutes = require('./routes/auth');
const userRoutes = require('./routes/users');
const detectionRoutes = require('./routes/detections');
const categoryRoutes = require('./routes/categories');
const tipRoutes = require('./routes/tips');
const carbonRoutes = require('./routes/carbon');
const ecopointRoutes = require('./routes/ecopoints');

const app = express();

app.use(cors());
app.use(express.json());
app.use(express.urlencoded({ extended: true }));

// Folder statis untuk gambar hasil upload deteksi
app.use('/uploads', express.static(path.join(__dirname, 'uploads')));

// Routes API
app.use('/api/auth', authRoutes);
app.use('/api/users', userRoutes);
app.use('/api/detections', detectionRoutes);
app.use('/api/categories', categoryRoutes);
app.use('/api/tips', tipRoutes);
app.use('/api/carbon', carbonRoutes);
app.use('/api/ecopoints', ecopointRoutes);

// Health check
app.get('/api/health', (req, res) => {
  res.json({ success: true, message: 'RECYNT AI Backend berjalan dengan baik 🌱' });
});

const PORT = process.env.PORT || 5000;
app.listen(PORT, () => {
  console.log(`🚀 RECYNT AI Backend berjalan di http://localhost:${PORT}`);
});
