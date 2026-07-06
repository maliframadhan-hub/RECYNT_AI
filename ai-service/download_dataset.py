"""
Download dataset GARBAGE CLASSIFICATION 3 dari Roboflow.
Dataset ini: 10.464 gambar, 7 kelas (PAPER, PLASTIC, GLASS, METAL,
CARDBOARD, CLOTH, BIODEGRADABLE) - jauh lebih layak untuk training
dibanding dataset 94-gambar-1-kelas yang dicoba sebelumnya.

Jalankan sekali saja: python download_dataset.py

CATATAN: cek nomor versi (project.version(X)) persis dari kode yang
ditampilkan Roboflow saat kamu klik "Download Dataset" -> "YOLOv8" di:
https://universe.roboflow.com/material-identification/garbage-classification-3

PENTING: API key TIDAK ditulis langsung di file ini. Key dibaca dari
file .env (lihat ROBOFLOW_API_KEY di file .env), supaya key tidak
ikut ter-upload kalau project ini di-push ke GitHub.
"""

import os
from dotenv import load_dotenv

# Baca isi file .env (harus ada baris ROBOFLOW_API_KEY=... di sana)
load_dotenv()

from roboflow import Roboflow

api_key = os.getenv("ROBOFLOW_API_KEY")
if not api_key:
    raise ValueError(
        "ROBOFLOW_API_KEY tidak ditemukan. "
        "Pastikan file .env sudah dibuat di folder ai-service/ "
        "dan berisi baris: ROBOFLOW_API_KEY=api_key_kamu"
    )

rf = Roboflow(api_key=api_key)
project = rf.workspace("material-identification").project("garbage-classification-3")
version = project.version(2)   # cek nomor versi persis dari halaman Roboflow
dataset = version.download("yolov8")

print("\nDataset berhasil didownload ke folder:", dataset.location)
print("Cek isi data.yaml di folder itu sebelum lanjut training.")