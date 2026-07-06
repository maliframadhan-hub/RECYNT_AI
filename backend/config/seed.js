// Script untuk membuat / memperbarui akun admin default dengan password ter-hash bcrypt
// Jalankan dengan: npm run seed

const bcrypt = require('bcryptjs');
const pool = require('./db');

async function seed() {
  try {
    const hashedPassword = await bcrypt.hash('admin123', 10);

    const [existing] = await pool.query('SELECT id FROM users WHERE username = ?', ['admin']);

    if (existing.length > 0) {
      await pool.query('UPDATE users SET password = ? WHERE username = ?', [hashedPassword, 'admin']);
      console.log('✅ Password admin berhasil diperbarui.');
    } else {
      await pool.query(
        'INSERT INTO users (fullname, username, email, password, points, role) VALUES (?, ?, ?, ?, 0, ?)',
        ['Administrator', 'admin', 'admin@recynt.ai', hashedPassword, 'admin']
      );
      console.log('✅ Akun admin berhasil dibuat.');
    }

    console.log('👉 Username : admin');
    console.log('👉 Password : admin123');
    process.exit(0);
  } catch (err) {
    console.error('❌ Gagal seeding:', err.message);
    process.exit(1);
  }
}

seed();
