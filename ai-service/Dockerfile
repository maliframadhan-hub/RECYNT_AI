# ---------------------------------------------------------------
# RECYNT AI Backend - Dockerfile
# ---------------------------------------------------------------
FROM python:3.11-slim

WORKDIR /app

# Dependency sistem yang dibutuhkan OpenCV/Ultralytics
RUN apt-get update && apt-get install -y --no-install-recommends \
    libgl1 \
    libglib2.0-0 \
    && rm -rf /var/lib/apt/lists/*

# Install dependency Python dulu (memanfaatkan cache layer Docker)
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Salin seluruh kode backend (termasuk folder model/ jika ada)
COPY . .

# Railway/Render menyuntikkan variabel PORT secara otomatis.
# Default 8000 dipakai kalau dijalankan secara lokal.
ENV PORT=8000
EXPOSE 8000

# JSON-form + shell eksplisit, agar variabel $PORT tetap terbaca
# sekaligus menghindari warning JSONArgsRecommended dari Docker.
CMD ["sh", "-c", "uvicorn main:app --host 0.0.0.0 --port ${PORT}"]