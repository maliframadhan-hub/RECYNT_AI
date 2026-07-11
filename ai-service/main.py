"""
main.py - RECYNT AI Service
=====================================================
FastAPI service untuk deteksi/klasifikasi jenis sampah
menggunakan model YOLOv8 yang dilatih dengan data.yaml
(kelas: plastik, organik, kertas, logam, kaca).

Jalankan setelah training selesai (best.pt tersedia):
    uvicorn main:app --reload --host 0.0.0.0 --port 8000

Model default dicari di:
    runs/detect/train/weights/best.pt
Bisa dioverride lewat environment variable MODEL_PATH.

Endpoint:
    GET  /health           -> cek service & model siap atau belum
    GET  /classes          -> daftar kelas & mapping id database
    POST /predict          -> upload 1 gambar, dapatkan SEMUA hasil deteksi (detail)
    POST /detect            -> upload 1 gambar, dapatkan HANYA deteksi confidence
                               tertinggi dalam format ringkas {category_name, confidence, ...}
                               (dipakai oleh frontend scan.html)
=====================================================
"""

import io
import os
import logging
from typing import List

from fastapi import FastAPI, File, UploadFile, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from PIL import Image

from ultralytics import YOLO

# ---------------------------------------------------------------
# Konfigurasi
# ---------------------------------------------------------------
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("recynt-ai")

# BASE_DIR = folder tempat main.py ini berada (bukan folder tempat kamu
# menjalankan perintah `uvicorn`). Ini penting supaya path model tetap benar
# meskipun working directory berubah, misalnya saat Uvicorn --reload
# me-restart proses, atau saat main.py dijalankan dari lokasi lain.
BASE_DIR = os.path.dirname(os.path.abspath(__file__))

DEFAULT_MODEL_PATH = os.path.join(BASE_DIR, "runs", "detect", "train", "weights", "best.pt")
MODEL_PATH = os.getenv("MODEL_PATH", DEFAULT_MODEL_PATH)
CONF_THRESHOLD = float(os.getenv("CONF_THRESHOLD", "0.4"))

# Mapping nama kelas YOLO (index mulai 0) -> id waste_categories di DB (mulai 1)
# Harus selalu sinkron dengan urutan `names` pada data.yaml
CLASS_TO_DB_ID = {
    "plastik": 1,
    "organik": 2,
    "kertas": 3,
    "logam": 4,
    "kaca": 5,
}

ALLOWED_CONTENT_TYPES = {"image/jpeg", "image/png", "image/jpg", "image/webp"}

# ---------------------------------------------------------------
# App & Model
# ---------------------------------------------------------------
app = FastAPI(
    title="RECYNT AI Service",
    description="Service deteksi jenis sampah (plastik, organik, kertas, logam, kaca) berbasis YOLOv8",
    version="1.0.0",
)

# Sesuaikan origins dengan domain frontend/backend kamu di production
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

model: YOLO | None = None


@app.on_event("startup")
def load_model() -> None:
    """Load model YOLO sekali saat service start, bukan setiap request."""
    global model
    if not os.path.exists(MODEL_PATH):
        logger.warning(
            "Model tidak ditemukan di '%s' (BASE_DIR='%s'). Pastikan file "
            "best.pt sudah ditaruh di runs/detect/train/weights/best.pt, "
            "atau set environment variable MODEL_PATH ke lokasi yang benar.",
            MODEL_PATH,
            BASE_DIR,
        )
        return
    logger.info("Memuat model dari %s ...", MODEL_PATH)
    model = YOLO(MODEL_PATH)
    logger.info("Model berhasil dimuat. Kelas: %s", model.names)


# ---------------------------------------------------------------
# Schemas
# ---------------------------------------------------------------
class Detection(BaseModel):
    class_name: str
    waste_category_id: int
    confidence: float
    bbox: List[float]  # [x1, y1, x2, y2]


class PredictResponse(BaseModel):
    filename: str
    detections: List[Detection]
    count: int


class DetectResponse(BaseModel):
    """
    Format sederhana khusus untuk frontend scan.html:
    hanya mengembalikan SATU deteksi dengan confidence tertinggi.
    Kalau tidak ada objek terdeteksi, category_name akan null.
    """
    category_name: str | None
    confidence: float
    waste_category_id: int | None
    bbox: List[float] | None


# ---------------------------------------------------------------
# Routes
# ---------------------------------------------------------------
@app.get("/health")
def health():
    return {
        "status": "ok",
        "model_loaded": model is not None,
        "model_path": MODEL_PATH,
    }


@app.get("/classes")
def get_classes():
    return {"classes": CLASS_TO_DB_ID}


def run_inference(image: Image.Image) -> List[Detection]:
    """Jalankan YOLO inference dan kembalikan list Detection terurut dari
    confidence tertinggi ke terendah. Dipakai bersama oleh /predict dan /detect."""
    results = model.predict(image, conf=CONF_THRESHOLD, verbose=False)
    result = results[0]

    detections: List[Detection] = []
    for box in result.boxes:
        cls_idx = int(box.cls[0])
        class_name = model.names[cls_idx]
        confidence = float(box.conf[0])
        x1, y1, x2, y2 = [float(v) for v in box.xyxy[0]]

        detections.append(
            Detection(
                class_name=class_name,
                waste_category_id=CLASS_TO_DB_ID.get(class_name, -1),
                confidence=round(confidence, 4),
                bbox=[round(x1, 2), round(y1, 2), round(x2, 2), round(y2, 2)],
            )
        )

    detections.sort(key=lambda d: d.confidence, reverse=True)
    return detections


async def _read_and_validate_image(file: UploadFile) -> Image.Image:
    if model is None:
        raise HTTPException(
            status_code=503,
            detail=(
                f"Model belum siap. Pastikan file model ada di '{MODEL_PATH}' "
                "lalu restart service."
            ),
        )

    if file.content_type not in ALLOWED_CONTENT_TYPES:
        raise HTTPException(
            status_code=400,
            detail=f"Tipe file '{file.content_type}' tidak didukung. Gunakan JPG/PNG/WEBP.",
        )

    try:
        raw_bytes = await file.read()
        return Image.open(io.BytesIO(raw_bytes)).convert("RGB")
    except Exception:
        raise HTTPException(status_code=400, detail="Gagal membaca file gambar.")


@app.post("/predict", response_model=PredictResponse)
async def predict(file: UploadFile = File(...)):
    image = await _read_and_validate_image(file)
    detections = run_inference(image)

    return PredictResponse(
        filename=file.filename,
        detections=detections,
        count=len(detections),
    )


@app.post("/detect", response_model=DetectResponse)
async def detect(file: UploadFile = File(...)):
    """
    Versi ringkas khusus untuk frontend (scan.html): hanya mengembalikan
    SATU deteksi dengan confidence tertinggi, dalam format
    {category_name, confidence, waste_category_id, bbox}.
    Kalau tidak ada objek yang terdeteksi sama sekali, category_name = null.
    """
    image = await _read_and_validate_image(file)
    detections = run_inference(image)

    if not detections:
        return DetectResponse(
            category_name=None,
            confidence=0.0,
            waste_category_id=None,
            bbox=None,
        )

    top = detections[0]
    return DetectResponse(
        category_name=top.class_name,
        confidence=top.confidence,
        waste_category_id=top.waste_category_id,
        bbox=top.bbox,
    )


if __name__ == "__main__":
    import uvicorn

    # Railway/Render/hosting cloud lain assign port secara dinamis lewat
    # environment variable PORT. Kalau tidak ada (misal jalan di lokal),
    # fallback ke 8000 seperti biasa.
    port = int(os.getenv("PORT", "8000"))

    # reload_excludes: folder dataset & runs biasanya besar dan sering
    # ditulis (cache, weights, log gambar). Kalau tidak dikecualikan,
    # Uvicorn bisa salah kira ada perubahan kode lalu restart proses
    # sendiri -> model jadi ke-unload dan /health balik model_loaded=false.
    # reload=True HANYA untuk development lokal — jangan aktif di production.
    is_dev = os.getenv("ENV", "development") == "development"
    uvicorn.run(
        "main:app",
        host="0.0.0.0",
        port=port,
        reload=is_dev,
        reload_excludes=["dataset/*", "runs/*", "*.pt", "*.cache"] if is_dev else None,
    )