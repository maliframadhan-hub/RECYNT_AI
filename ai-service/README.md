# RECYNT AI — Backend (FastAPI + YOLOv8)

Backend ini menyediakan endpoint `/detect` yang dipakai `scan.html` untuk
mendeteksi jenis sampah dari gambar. Panduan ini menjelaskan cara deploy
agar bisa diakses publik (bukan cuma `127.0.0.1`) sehingga cocok dipasangkan
dengan frontend yang di-deploy ke Vercel.

## 1. Siapkan model kamu (opsional tapi disarankan)

Secara default, `main.py` memakai `yolov8n.pt` (model umum COCO) hanya
supaya server bisa langsung jalan untuk tes koneksi — hasil deteksinya
BUKAN kategori sampah yang akurat.

Kalau kamu punya model hasil training sendiri:
1. Taruh file `.pt` di folder `model/`, misal `model/best.pt`.
2. Saat deploy, set environment variable:
   ```
   MODEL_PATH=model/best.pt
   ```
3. Sesuaikan `CLASS_NAME_MAP` di `main.py` dengan nama kelas dari model
   kamu (harus dipetakan ke salah satu: `plastik`, `kertas`, `logam`,
   `kaca`, `organik`, `elektronik`, `anorganik`, `b3`).

## 2. Deploy ke Railway (rekomendasi — paling gampang)

1. Push folder `backend/` ini ke repo GitHub (boleh repo sendiri atau
   subfolder dari repo utama proyekmu).
2. Buka [railway.app](https://railway.app) → login dengan GitHub.
3. **New Project → Deploy from GitHub repo** → pilih repo kamu.
4. Kalau `main.py` ada di dalam subfolder (misal `backend/`), buka
   **Settings → Root Directory** dan isi `backend`.
5. Railway otomatis mendeteksi `Dockerfile` dan mem-build container.
6. Setelah build selesai, buka **Settings → Networking → Generate Domain**.
   Kamu akan mendapat URL publik HTTPS, contoh:
   ```
   https://recynt-api-production.up.railway.app
   ```
7. (Opsional) Tambahkan environment variable di tab **Variables**:
   - `MODEL_PATH` = `model/best.pt` (kalau pakai model custom)
   - `CONF_THRESHOLD` = `0.4`
   - `ALLOWED_ORIGINS` = `https://nama-app-kamu.vercel.app`

### Alternatif platform lain
Dockerfile ini juga langsung kompatibel dengan **Render** dan **Fly.io**
kalau kamu ingin coba platform lain — caranya serupa: hubungkan repo,
platform build dari Dockerfile, lalu kamu dapat URL publik HTTPS.

## 3. Tes backend sudah hidup

Buka di browser:
```
https://<url-railway-kamu>/docs
```
Kalau muncul halaman Swagger UI FastAPI, backend sudah berjalan dengan
benar.

## 4. Sambungkan ke frontend (scan.html)

Di `scan.html`, ubah baris:
```javascript
const AI_API = "http://127.0.0.1:8000/detect";
```
menjadi:
```javascript
const AI_API = "https://<url-railway-kamu>/detect";
```
**Wajib `https://`** — kalau frontend di Vercel pakai HTTPS tapi backend
masih `http://`, browser akan memblokir request (mixed content).

## 5. Perketat CORS (setelah domain Vercel final)

Setelah tahu domain final Vercel kamu, set environment variable di
Railway:
```
ALLOWED_ORIGINS=https://nama-app-kamu.vercel.app
```
lalu redeploy. Ini mencegah domain lain memanggil API kamu secara bebas.

## Troubleshooting

| Gejala | Kemungkinan penyebab |
|---|---|
| `Failed to fetch` di browser | Backend belum jalan / URL masih `127.0.0.1` / mixed content HTTP vs HTTPS |
| CORS error di console | `ALLOWED_ORIGINS` belum mencakup domain frontend kamu |
| Response lambat pertama kali | Cold start platform (server "bangun" dari sleep) — normal di free tier |
| `category_name: null` | Confidence deteksi di bawah `CONF_THRESHOLD`, atau tidak ada objek dikenali — coba foto lebih jelas/terang |
| Error 500 saat `/detect` | Cek logs di dashboard Railway — biasanya path `MODEL_PATH` salah atau file model tidak ikut ter-upload |