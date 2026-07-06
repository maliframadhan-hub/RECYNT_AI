const jwt = require('jsonwebtoken');
require('dotenv').config();

if (!process.env.JWT_SECRET) {
  console.error('❌ ENV JWT_SECRET belum diisi di .env — wajib untuk login & verifikasi token.');
  process.exit(1);
}

// Middleware wajib login (dipakai di route yang butuh user login)
function verifyToken(req, res, next) {
  const authHeader = req.headers['authorization'];

  if (!authHeader || !authHeader.startsWith('Bearer ')) {
    return res.status(401).json({
      success: false,
      message: 'Token tidak ditemukan. Silakan login kembali.'
    });
  }

  const token = authHeader.split(' ')[1];

  if (!token) {
    return res.status(401).json({
      success: false,
      message: 'Format token tidak valid.'
    });
  }

  try {
    const decoded = jwt.verify(token, process.env.JWT_SECRET);
    req.user = decoded; // { id, username, role, ... }
    next();
  } catch (err) {
    if (err.name === 'TokenExpiredError') {
      return res.status(401).json({ success: false, message: 'Sesi login sudah habis, silakan login ulang.' });
    }
    return res.status(401).json({ success: false, message: 'Token tidak valid.' });
  }
}

// Middleware opsional: hanya untuk admin
function requireAdmin(req, res, next) {
  if (!req.user || req.user.role !== 'admin') {
    return res.status(403).json({ success: false, message: 'Akses ditolak. Khusus admin.' });
  }
  next();
}

module.exports = { verifyToken, requireAdmin };