const express = require('express');
const router = express.Router();
const pool = require('../config/db');

// GET /api/carbon - semua data estimasi pengurangan CO2 per kategori
router.get('/', async (req, res) => {
  try {
    const [rows] = await pool.query(
      `SELECT ci.id, ci.co2_reduction, wc.category_name
       FROM carbon_impact ci
       LEFT JOIN waste_categories wc ON ci.category_id = wc.id`
    );
    res.json({ success: true, data: rows });
  } catch (err) {
    console.error('CARBON ERROR:', err.message);
    res.status(500).json({ success: false, message: 'Terjadi kesalahan server.' });
  }
});

// GET /api/carbon/total - total CO2 yang sudah dihemat user login
router.get('/total', require('../middleware/auth').verifyToken, async (req, res) => {
  try {
    const [rows] = await pool.query(
      'SELECT COALESCE(SUM(carbon_saved), 0) AS total_carbon_saved FROM detections WHERE user_id = ?',
      [req.user.id]
    );
    res.json({ success: true, data: rows[0] });
  } catch (err) {
    console.error('CARBON TOTAL ERROR:', err.message);
    res.status(500).json({ success: false, message: 'Terjadi kesalahan server.' });
  }
});

module.exports = router;