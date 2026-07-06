const express = require('express');
const router = express.Router();
const multer = require('multer');
const path = require('path');
const fs = require('fs');
const FormData = require('form-data');
const axios = require('axios');
const pool = require('../config/db');
const { verifyToken } = require('../middleware/auth');
require('dotenv').config();

// Wajib ada, kalau tidak: langsung ketahuan saat server start, bukan saat request masuk
if (!process.env.AI_SERVICE_URL) {
  console.error('❌ ENV AI_SERVICE_URL belum diisi di .env — wajib untuk fitur deteksi AI.');
  console.error('   Contoh: AI_SERVICE_URL=http://localhost:8000');
  process.exit(1);
}
const AI_SERVICE_URL = process.env.AI_SERVICE_URL.replace(/\/+$/, ''); // buang trailing slash

// Pastikan folder upload tersedia
const uploadDir = path.join(__dirname, '..', 'uploads');
if (!fs.existsSync(uploadDir)) fs.mkdirSync(uploadDir, { recursive: true });

const storage = multer.diskStorage({
  destination: (req, file, cb) => cb(null, uploadDir),
  filename: (req, file, cb) => {
    const unique = Date.now() + '-' + Math.round(Math.random() * 1e9);
    cb(null, unique + path.extname(file.originalname || ''));
  }
});

const upload = multer({
  storage,
  limits: { fileSize: 8 * 1024 * 1024 }, // max 8MB
  fileFilter: (req, file, cb) => {
    const allowed = ['image/jpeg', 'image/png', 'image/jpg', 'image/webp'];
    if (!allowed.includes(file.mimetype)) {
      return cb(new Error('Format file tidak didukung. Gunakan JPG, PNG, atau WEBP.'));
    }
    cb(null, true);
  }
});

// Bungkus multer supaya errornya (fileFilter / fileSize) balik jadi JSON rapi,
// bukan HTML error default Express
function uploadSingleImage(req, res, next) {
  const handler = upload.single('image');
  handler(req, res, (err) => {
    if (err instanceof multer.MulterError) {
      if (err.code === 'LIMIT_FILE_SIZE') {
        return res.status(400).json({ success: false, message: 'Ukuran gambar maksimal 8MB.' });
      }
      return res.status(400).json({ success: false, message: `Upload error: ${err.message}` });
    } else if (err) {
      return res.status(400).json({ success: false, message: err.message });
    }
    next();
  });
}

const POINTS_PER_DETECTION = 10;

// ---------------------------------------------------------
// POST /api/detections
// ---------------------------------------------------------
router.post('/', verifyToken, uploadSingleImage, async (req, res) => {
  if (!req.file) {
    return res.status(400).json({ success: false, message: 'Gambar wajib diunggah (field name: "image").' });
  }

  let conn;
  const uploadedFilePath = req.file.path;

  try {
    // 1) Kirim gambar ke AI Service (Python FastAPI + YOLOv8)
    let aiResponse;
    try {
      const form = new FormData();
      form.append('file', fs.createReadStream(uploadedFilePath));

      aiResponse = await axios.post(`${AI_SERVICE_URL}/detect`, form, {
        headers: form.getHeaders(),
        timeout: 30000
      });
    } catch (aiErr) {
      // Bedakan jenis errornya biar ketahuan pasti dari mana
      let message = 'Gagal terhubung ke AI service.';
      if (aiErr.code === 'ECONNREFUSED') {
        message = `AI service tidak merespons di ${AI_SERVICE_URL}. Pastikan service Python (uvicorn) sudah dijalankan.`;
      } else if (aiErr.code === 'ECONNABORTED') {
        message = 'AI service terlalu lama merespons (timeout 30 detik).';
      } else if (aiErr.response) {
        message = `AI service mengembalikan error: ${aiErr.response.status} ${JSON.stringify(aiErr.response.data)}`;
      }
      console.error('AI SERVICE ERROR:', aiErr.message);
      fs.unlink(uploadedFilePath, () => {});
      return res.status(502).json({ success: false, message });
    }

    const { category_name, confidence } = aiResponse.data || {};

    if (!category_name) {
      fs.unlink(uploadedFilePath, () => {});
      return res.status(422).json({ success: false, message: 'Objek sampah tidak terdeteksi pada gambar.' });
    }

    conn = await pool.getConnection();
    await conn.beginTransaction();

    // 2) Cari category_id berdasarkan nama kategori hasil deteksi
    const [catRows] = await conn.query(
      'SELECT id FROM waste_categories WHERE category_name = ? LIMIT 1',
      [category_name]
    );
    const category_id = catRows.length > 0 ? catRows[0].id : null;

    // 3) Ambil estimasi CO2 reduction untuk kategori tersebut
    let carbon_saved = 0;
    if (category_id) {
      const [carbonRows] = await conn.query(
        'SELECT co2_reduction FROM carbon_impact WHERE category_id = ? LIMIT 1',
        [category_id]
      );
      if (carbonRows.length > 0) carbon_saved = carbonRows[0].co2_reduction;
    }

    // 4) Simpan hasil deteksi
    const [detResult] = await conn.query(
      `INSERT INTO detections (user_id, category_id, image_path, confidence, carbon_saved)
       VALUES (?, ?, ?, ?, ?)`,
      [req.user.id, category_id, req.file.filename, confidence, carbon_saved]
    );

    // 5) Tambahkan eco points
    await conn.query(
      'INSERT INTO eco_points (user_id, points, activity) VALUES (?, ?, ?)',
      [req.user.id, POINTS_PER_DETECTION, `Deteksi sampah: ${category_name}`]
    );
    await conn.query('UPDATE users SET points = points + ? WHERE id = ?', [POINTS_PER_DETECTION, req.user.id]);

    await conn.commit();

    res.status(201).json({
      success: true,
      message: 'Deteksi berhasil.',
      data: {
        id: detResult.insertId,
        category_name,
        confidence,
        carbon_saved,
        points_earned: POINTS_PER_DETECTION,
        image_url: `/uploads/${req.file.filename}`
      }
    });
  } catch (err) {
    if (conn) {
      try { await conn.rollback(); } catch (_) {}
    }
    fs.unlink(uploadedFilePath, () => {});
    console.error('DETECTION DB ERROR:', err.message);
    res.status(500).json({ success: false, message: 'Gagal menyimpan hasil deteksi ke database.' });
  } finally {
    if (conn) conn.release();
  }
});

// ---------------------------------------------------------
// GET /api/detections/history
// ---------------------------------------------------------
router.get('/history', verifyToken, async (req, res) => {
  try {
    const [rows] = await pool.query(
      `SELECT d.id, d.image_path, d.confidence, d.carbon_saved, d.detected_at, wc.category_name
       FROM detections d
       LEFT JOIN waste_categories wc ON d.category_id = wc.id
       WHERE d.user_id = ?
       ORDER BY d.detected_at DESC`,
      [req.user.id]
    );
    res.json({ success: true, data: rows });
  } catch (err) {
    console.error('HISTORY ERROR:', err.message);
    res.status(500).json({ success: false, message: 'Terjadi kesalahan server.' });
  }
});

module.exports = router;