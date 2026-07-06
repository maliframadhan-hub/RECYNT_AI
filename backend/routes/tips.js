const express = require('express');
const router = express.Router();
const pool = require('../config/db');

// GET /api/tips - semua tips daur ulang (opsional filter ?category_id=)
router.get('/', async (req, res) => {
  try {
    const { category_id } = req.query;
    let query = `
      SELECT rt.id, rt.title, rt.description, wc.category_name
      FROM recycling_tips rt
      LEFT JOIN waste_categories wc ON rt.category_id = wc.id
    `;
    const params = [];
    if (category_id) {
      query += ' WHERE rt.category_id = ?';
      params.push(category_id);
    }
    const [rows] = await pool.query(query, params);
    res.json({ success: true, data: rows });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: 'Terjadi kesalahan server.' });
  }
});

module.exports = router;