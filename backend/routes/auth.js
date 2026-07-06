const express = require('express');
const router = express.Router();
const bcrypt = require('bcryptjs');
const jwt = require('jsonwebtoken');
const pool = require('../config/db');
require('dotenv').config();

/* =========================================================
   REGISTER
========================================================= */
router.post('/register', async (req, res) => {
  try {
    const { fullname, username, email, password } = req.body;

    if (!fullname || !username || !email || !password) {
      return res.status(400).json({
        success: false,
        message: 'Semua field wajib diisi.'
      });
    }

    if (password.length < 6) {
      return res.status(400).json({
        success: false,
        message: 'Password minimal 6 karakter.'
      });
    }

    const [existing] = await pool.query(
      'SELECT id FROM users WHERE username = ? OR email = ? LIMIT 1',
      [username, email]
    );

    if (existing.length > 0) {
      return res.status(409).json({
        success: false,
        message: 'Username atau email sudah terdaftar.'
      });
    }

    const hashed = await bcrypt.hash(password, 10);

    const [result] = await pool.query(
      `INSERT INTO users (fullname, username, email, password, points, role)
       VALUES (?, ?, ?, ?, 0, 'user')`,
      [fullname, username, email, hashed]
    );

    return res.status(201).json({
      success: true,
      message: 'Registrasi berhasil. Silakan login.',
      data: {
        id: result.insertId,
        username,
        email
      }
    });

  } catch (err) {
    console.error('REGISTER ERROR:', err);
    return res.status(500).json({
      success: false,
      message: err.message
    });
  }
});


/* =========================================================
   LOGIN (FIXED + MORE ROBUST)
========================================================= */
router.post('/login', async (req, res) => {
  try {
    const { username, password } = req.body;

    if (!username || !password) {
      return res.status(400).json({
        success: false,
        message: 'Username/email dan password wajib diisi.'
      });
    }

    const [rows] = await pool.query(
      `SELECT * FROM users 
       WHERE username = ? OR email = ? 
       LIMIT 1`,
      [username, username]
    );

    if (!rows || rows.length === 0) {
      return res.status(401).json({
        success: false,
        message: 'User tidak ditemukan.'
      });
    }

    const user = rows[0];

    if (!user.password) {
      return res.status(500).json({
        success: false,
        message: 'Data user rusak (password kosong).'
      });
    }

    const match = await bcrypt.compare(password, user.password);

    if (!match) {
      return res.status(401).json({
        success: false,
        message: 'Password salah.'
      });
    }

    if (!process.env.JWT_SECRET) {
      return res.status(500).json({
        success: false,
        message: 'JWT_SECRET belum diset di .env'
      });
    }

    const token = jwt.sign(
      {
        id: user.id,
        username: user.username,
        role: user.role
      },
      process.env.JWT_SECRET,
      { expiresIn: process.env.JWT_EXPIRES_IN || '7d' }
    );

    return res.json({
      success: true,
      message: 'Login berhasil.',
      token,
      user: {
        id: user.id,
        fullname: user.fullname,
        username: user.username,
        email: user.email,
        points: user.points || 0,
        role: user.role || 'user'
      }
    });

  } catch (err) {
    console.error('LOGIN ERROR FULL:', err);

    return res.status(500).json({
      success: false,
      message: 'Terjadi kesalahan server.',
      error: err.message
    });
  }
});

module.exports = router;