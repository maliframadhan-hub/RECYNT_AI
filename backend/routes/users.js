const express = require('express');
const router = express.Router();
const pool = require('../config/db');
const { verifyToken } = require('../middleware/auth');

// GET /api/users/me - profil user yang sedang login
router.get('/me', verifyToken, async (req, res) => {
  try {
    const [rows] = await pool.query(
      'SELECT id, fullname, username, email, points, role, created_at FROM users WHERE id = ?',
      [req.user.id]
    );
    if (rows.length === 0) {
      return res.status(404).json({ success: false, message: 'User tidak ditemukan.' });
    }
    res.json({ success: true, data: rows[0] });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: 'Terjadi kesalahan server.' });
  }
});

// GET /api/users/leaderboard - ranking user berdasarkan poin
router.get('/leaderboard', async (req, res) => {
  try {
    const [rows] = await pool.query(
      'SELECT id, fullname, username, points FROM users WHERE role = "user" ORDER BY points DESC LIMIT 20'
    );
    res.json({ success: true, data: rows });
  } catch (err) {
    console.error(err);
    res.status(500).json({ success: false, message: 'Terjadi kesalahan server.' });
  }
});

module.exports = router;