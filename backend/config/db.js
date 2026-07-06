const mysql = require("mysql2/promise");
require("dotenv").config();

// ==========================================
// Validasi Environment Variable
// ==========================================
const requiredEnv = [
  "DB_HOST",
  "DB_PORT",
  "DB_USER",
  "DB_NAME",
];

const missing = requiredEnv.filter(
  (key) => !process.env[key] || process.env[key].trim() === ""
);

if (missing.length > 0) {
  console.error("\n❌ Missing Environment Variables:");
  missing.forEach((key) => console.error(`   • ${key}`));
  console.error("\nPastikan Environment Variables sudah diisi.");
  process.exit(1);
}

// ==========================================
// MySQL Pool
// ==========================================
const pool = mysql.createPool({
  host: process.env.DB_HOST,
  port: parseInt(process.env.DB_PORT, 10),

  user: process.env.DB_USER,
  password: process.env.DB_PASSWORD || "",
  database: process.env.DB_NAME,

  waitForConnections: true,
  connectionLimit: 10,
  queueLimit: 0,

  charset: "utf8mb4",

  connectTimeout: 10000,

  enableKeepAlive: true,
  keepAliveInitialDelay: 0
});

// ==========================================
// Test Connection
// ==========================================
async function testConnection() {
  try {
    const connection = await pool.getConnection();

    console.log("\n======================================");
    console.log("✅ MySQL Connected Successfully");
    console.log("======================================");
    console.log(`Host     : ${process.env.DB_HOST}`);
    console.log(`Port     : ${process.env.DB_PORT}`);
    console.log(`Database : ${process.env.DB_NAME}`);
    console.log(`User     : ${process.env.DB_USER}`);
    console.log("======================================\n");

    connection.release();
  } catch (err) {
    console.error("\n======================================");
    console.error("❌ DATABASE CONNECTION FAILED");
    console.error("======================================");
    console.error("Message :", err.message);

    if (err.code) {
      console.error("Code    :", err.code);
    }

    console.error("======================================\n");

    process.exit(1);
  }
}

testConnection();

module.exports = pool;