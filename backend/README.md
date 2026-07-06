# 🌱 RECYNT AI — Recycle Intelligent Waste Detection System

Sistem deteksi & klasifikasi sampah berbasis AI (YOLOv8), terdiri dari:
- **Website** (HTML/CSS/JS)
- **Backend API** (Node.js + Express + MySQL)
- **AI Service** (Python + FastAPI + YOLOv8)
- **Aplikasi Mobile** (Flutter + Dart)

```
recynt-ai/
├── database/          → file SQL skema database
├── backend/            → REST API (Node.js + Express)
├── ai-service/          → Model deteksi YOLOv8 (Python + FastAPI)
├── website/            → Landing page + dashboard web
└── mobile/recynt_ai_app/ → Aplikasi Flutter
```

---

## 🧰 PRASYARAT (install dulu sebelum mulai)

| Tools | Kegunaan | Link |
|---|---|---|
| **Visual Studio Code** | Code editor | https://code.visualstudio.com |
| **Node.js (LTS)** | Menjalankan backend | https://nodejs.org |
| **Python 3.10+** | Menjalankan AI service | https://python.org |
| **XAMPP / Laragon / MySQL Server** | Database MySQL/MariaDB | https://www.apachefriends.org |
| **Flutter SDK** | Membangun aplikasi mobile | https://docs.flutter.dev/get-started/install |
| **Git** (opsional) | Version control | https://git-scm.com |

Ekstensi VS Code yang disarankan:
- Flutter (Dart-Code.flutter)
- ES7+ React/JS snippets (opsional)
- Thunder Client / REST Client (untuk uji API)
- Live Server (untuk menjalankan website statis)

---

## 🗂️ LANGKAH 1 — Membuat Folder Project

1. Buka **Visual Studio Code**.
2. Buka Terminal (`Ctrl + \``) lalu jalankan:
   ```bash
   mkdir recynt-ai
   cd recynt-ai
   code .
   ```
3. Buat struktur folder berikut (bisa lewat Explorer VS Code atau terminal):
   ```bash
   mkdir database backend ai-service website mobile
   ```
4. Salin seluruh file dari paket project yang sudah dibuatkan (folder `database/`,
   `backend/`, `ai-service/`, `website/`, `mobile/`) ke dalam folder `recynt-ai` ini.

---

## 🗄️ LANGKAH 2 — Setup Database MySQL

1. Jalankan **XAMPP / Laragon**, aktifkan modul **MySQL**.
2. Buka **phpMyAdmin** (`http://localhost/phpmyadmin`) atau gunakan client MySQL
   seperti HeidiSQL / DBeaver / terminal `mysql`.
3. Import file `database/recynt_ai.sql`:
   - Via phpMyAdmin: klik **Import** → pilih file `recynt_ai.sql` → **Go**.
   - Via terminal:
     ```bash
     mysql -u root -p < database/recynt_ai.sql
     ```
4. Pastikan database `recynt_ai` dan 6 tabel berikut sudah terbentuk:
   `users`, `waste_categories`, `detections`, `eco_points`, `recycling_tips`, `carbon_impact`.

---

## ⚙️ LANGKAH 3 — Menjalankan Backend (Node.js + Express)

1. Buka terminal baru di VS Code, arahkan ke folder backend:
   ```bash
   cd backend
   npm install
   ```
2. Salin file environment:
   ```bash
   copy .env.example .env      # Windows
   cp .env.example .env        # Mac/Linux
   ```
3. Buka `.env`, sesuaikan `DB_USER`, `DB_PASSWORD` dengan MySQL Anda
   (default XAMPP: user `root`, password kosong).
4. Buat akun admin default (password otomatis ter-hash):
   ```bash
   npm run seed
   ```
5. Jalankan server:
   ```bash
   npm run dev
   ```
6. Jika berhasil akan muncul:
   ```
   ✅ Berhasil terkoneksi ke database MySQL: recynt_ai
   🚀 RECYNT AI Backend berjalan di http://localhost:5000
   ```
7. Tes di browser: buka `http://localhost:5000/api/health`

---

## 🤖 LANGKAH 4 — Menjalankan AI Service (YOLOv8)

1. Buka terminal baru:
   ```bash
   cd ai-service
   python -m venv venv
   venv\Scripts\activate        # Windows
   source venv/bin/activate     # Mac/Linux
   pip install -r requirements.txt
   ```
2. Siapkan model (baca `ai-service/README.md` untuk panduan training lengkap).
   Untuk mulai cepat (model umum, belum spesifik sampah):
   ```bash
   mkdir model
   python -c "from ultralytics import YOLO; YOLO('yolov8n.pt').save('model/best.pt')"
   ```
3. Jalankan service:
   ```bash
   uvicorn app:app --host 0.0.0.0 --port 8000 --reload
   ```
4. Tes di browser: buka `http://127.0.0.1:8000/docs` (Swagger UI interaktif).

> 📌 **Penting**: agar hasil deteksi akurat mengenali kategori sampah asli
> (plastik, kertas, logam, dll), Anda **wajib melatih model custom** menggunakan
> dataset sampah. Panduan lengkap ada di `ai-service/README.md`.

---

## 🌐 LANGKAH 5 — Menjalankan Website

1. Di VS Code, klik kanan pada `website/index.html` → **Open with Live Server**
   (jika ekstensi Live Server terpasang), atau buka langsung file tersebut di browser.
2. Pastikan `backend` (Langkah 3) sudah berjalan di port `5000`, karena website
   mengambil data lewat `http://localhost:5000/api`.
3. Alur pengujian:
   - Buka `index.html` → klik **Daftar** → buat akun baru.
   - Login di `login.html` → otomatis diarahkan ke `dashboard.html`.
   - Di dashboard, unggah foto sampah untuk mencoba fitur deteksi.

> Jika URL backend berbeda (misalnya beda port), ubah baris
> `window.RECYNT_API_BASE` di file `website/js/main.js`.

---

## 📱 LANGKAH 6 — Menjalankan Aplikasi Mobile (Flutter)

1. Pastikan Flutter SDK sudah terpasang & terverifikasi:
   ```bash
   flutter doctor
   ```
2. Buka folder aplikasi di VS Code:
   ```bash
   cd mobile/recynt_ai_app
   code .
   ```
3. Install dependencies:
   ```bash
   flutter pub get
   ```
4. **Sesuaikan URL backend** di file `lib/services/api_service.dart`:
   - Emulator Android → `http://10.0.2.2:5000/api` (default, sudah diatur)
   - Emulator iOS → `http://127.0.0.1:5000/api`
   - HP fisik (WiFi satu jaringan) → `http://<IP_LOKAL_KOMPUTER>:5000/api`
     (cek IP lokal dengan `ipconfig` di Windows atau `ifconfig` di Mac/Linux)
5. Jalankan aplikasi (pastikan emulator/HP sudah terhubung):
   ```bash
   flutter run
   ```
6. Alur pengujian di aplikasi:
   - Splash screen → Login/Register.
   - Setelah login → tab **Ringkasan** menampilkan poin & statistik.
   - Tab **Deteksi** → ambil foto/pilih dari galeri → otomatis dikirim ke AI service.
   - Tab **Riwayat** → menampilkan histori deteksi.
   - Tab **Profil** → info akun & tombol keluar.

---

## 🔗 Ringkasan Alur Data (End-to-End)

```
[Kamera Mobile / Upload Web]
        │
        ▼
[Backend Node.js] ── multer (terima file gambar)
        │
        ▼
[AI Service Python] ── YOLOv8 mendeteksi & klasifikasi
        │
        ▼
[Backend Node.js] ── simpan hasil ke MySQL (detections, eco_points)
        │
        ▼
[Website / Mobile App] ── tampilkan hasil, riwayat, dan poin
```

---

## 🧪 Troubleshooting Umum

| Masalah | Solusi |
|---|---|
| `❌ Gagal terkoneksi ke database` | Cek `.env`, pastikan service MySQL aktif |
| Website tidak menampilkan data | Pastikan backend berjalan di `localhost:5000` |
| Deteksi gagal / timeout | Pastikan `ai-service` (port 8000) sedang berjalan |
| Flutter tidak bisa akses backend | Gunakan `10.0.2.2` untuk emulator Android, bukan `localhost` |
| CORS error di browser | Backend sudah mengaktifkan `cors()` secara default, pastikan tidak diubah |
| Model YOLO salah klasifikasi | Latih ulang model dengan dataset sampah nyata (lihat `ai-service/README.md`) |

---

## 🚀 Pengembangan Selanjutnya (Opsional)
- Tambahkan fitur upload foto profil.
- Tambahkan halaman admin untuk kelola kategori & tips.
- Deploy backend ke layanan seperti Railway/Render, AI service ke server dengan GPU.
- Deploy website ke Vercel/Netlify, build APK Flutter (`flutter build apk`) untuk distribusi.

---

**Tim Satu Asa · Politeknik Negeri Medan**
RECYNT AI — Recycle Intelligent Waste Detection System
