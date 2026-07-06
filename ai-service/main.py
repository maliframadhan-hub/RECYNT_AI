"""
RECYNT AI - Waste Detection API
--------------------------------
Backend FastAPI yang menjalankan model YOLOv8 untuk mendeteksi
jenis sampah dari gambar (kamera / upload) yang dikirim frontend.

Endpoint utama:
    POST /detect  -> menerima file gambar, mengembalikan
                     { "category_name": str, "confidence": float }

Deploy: lihat README.md untuk panduan deploy ke Railway (HTTPS publik).
"""

import io
import os
import logging
from typing import Optional

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from PIL import Image
from ultralytics import YOLO

# ---------------------------------------------------------------
# LOGGING
# ---------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("recynt-ai")

# ---------------------------------------------------------------
# KONFIGURASI (bisa di-override lewat Environment Variables)
# ---------------------------------------------------------------
# MODEL_PATH: path ke file bobot model kamu (.pt).
#   - Default "yolov8n.pt" = model umum (COCO) hanya untuk TES KONEKSI,
#     hasil deteksinya BUKAN kategori sampah yang akurat.
#   - Ganti ke model hasil training kamu sendiri, misal "model/best.pt",
#     lalu set ENV MODEL_PATH=model/best.pt di platform hosting.
MODEL_PATH = os.getenv("MODEL_PATH", "yolov8n.pt")

# Ambang batas confidence minimum agar deteksi dianggap valid
CONF_THRESHOLD = float(os.getenv("CONF_THRESHOLD", "0.4"))

# Domain yang diizinkan mengakses API ini (CORS).
# Untuk produksi, ganti "*" dengan domain Vercel kamu, contoh:
#   ALLOWED_ORIGINS=https://recynt-ai.vercel.app
ALLOWED_ORIGINS = os.getenv("ALLOWED_ORIGINS", "*").split(",")

# ---------------------------------------------------------------
# APP
# ---------------------------------------------------------------
app = FastAPI(
    title="RECYNT AI - Waste Detection API",
    description="API deteksi jenis sampah menggunakan YOLOv8",
    version="1.0.0",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# ---------------------------------------------------------------
# LOAD MODEL (sekali saat server start)
# ---------------------------------------------------------------
logger.info(f"Memuat model YOLO dari: {MODEL_PATH}")
try:
    model = YOLO(MODEL_PATH)
    logger.info("Model berhasil dimuat.")
except Exception as e:
    logger.error(f"Gagal memuat model: {e}")
    model = None

# ---------------------------------------------------------------
# MAPPING nama kelas hasil model -> key yang dipakai frontend
# (harus cocok dengan CATEGORY_INFO di scan.html)
# Sesuaikan key kiri dengan nama kelas asli dari model kamu.
# ---------------------------------------------------------------
CLASS_NAME_MAP = {
    # --- plastik ---
    "plastic": "plastik",
    "plastik": "plastik",
    "bottle": "plastik",  # asumsi sementara utk model COCO (yolov8n.pt) -> botol plastik
 
    # --- kertas ---
    "paper": "kertas",
    "cardboard": "kertas",
    "kertas": "kertas",
 
    # --- logam ---
    "metal": "logam",
    "can": "logam",
    "logam": "logam",
 
    # --- kaca ---
    "glass": "kaca",
    "kaca": "kaca",
 
    # --- organik ---
    "organic": "organik",
    "biological": "organik",
    "organik": "organik",
}


# ---------------------------------------------------------------
# ROUTES
# ---------------------------------------------------------------
@app.get("/")
def root():
    """Health check dasar - cek apakah API hidup."""
    return {
        "status": "ok",
        "service": "RECYNT AI Detection API",
        "model_loaded": model is not None,
        "model_path": MODEL_PATH,
    }


@app.get("/health")
def health():
    """Endpoint health check untuk monitoring platform hosting."""
    if model is None:
        raise HTTPException(status_code=503, detail="Model belum siap.")
    return {"status": "healthy"}


@app.post("/detect")
async def detect(file: UploadFile = File(...)):
    """
    Terima gambar, jalankan inferensi YOLOv8, kembalikan kategori
    sampah dengan confidence tertinggi.
    """
    if model is None:
        raise HTTPException(
            status_code=503,
            detail="Model AI belum siap di server. Coba lagi sebentar.",
        )

    if not file.content_type or not file.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="File harus berupa gambar (JPG/PNG).")

    # Baca & decode gambar
    try:
        contents = await file.read()
        image = Image.open(io.BytesIO(contents)).convert("RGB")
    except Exception:
        raise HTTPException(
            status_code=400,
            detail="Gambar tidak dapat dibaca. Pastikan format JPG/PNG valid.",
        )

    # Jalankan inferensi
    try:
        results = model.predict(image, conf=CONF_THRESHOLD, verbose=False)
    except Exception as e:
        logger.error(f"Error saat inferensi: {e}")
        raise HTTPException(status_code=500, detail="Terjadi kesalahan saat memproses gambar oleh model AI.")

    if not results or len(results) == 0:
        return JSONResponse({"category_name": None, "confidence": 0})

    boxes = results[0].boxes

    if boxes is None or len(boxes) == 0:
        # Tidak ada objek terdeteksi di atas threshold
        return JSONResponse({"category_name": None, "confidence": 0})

    # Ambil deteksi dengan confidence tertinggi
    best_idx = int(boxes.conf.argmax().item())
    best_conf = float(boxes.conf[best_idx].item())
    best_cls_id = int(boxes.cls[best_idx].item())
    raw_label = str(model.names.get(best_cls_id, best_cls_id)).lower()

    mapped_label = CLASS_NAME_MAP.get(raw_label, raw_label)

    logger.info(f"Deteksi: {raw_label} -> {mapped_label} (confidence={best_conf:.3f})")

    return JSONResponse(
        {
            "category_name": mapped_label,
            "confidence": round(best_conf, 4),
            "raw_label": raw_label,  # untuk debugging, boleh diabaikan frontend
        }
    )


if __name__ == "__main__":
    import uvicorn

    port = int(os.getenv("PORT", "8000"))
    uvicorn.run("main:app", host="0.0.0.0", port=port, reload=False)