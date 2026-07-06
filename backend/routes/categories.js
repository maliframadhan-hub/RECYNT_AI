const express = require('express');
const router = express.Router();
const pool = require('../config/db');

// GET /api/categories - semua kategori sampah
router.get('/', async (req, res) => {
  try {
    const [rows] = await pool.query('SELECT * FROM waste_categories ORDER BY category_name ASC');
    res.json({ success: true, data: rows });
  } catch (err) {
    console.error('CATEGORIES ERROR:', err.message);
    res.status(500).json({ success: false, message: 'Terjadi kesalahan server.' });
  }
});

module.exports = router;