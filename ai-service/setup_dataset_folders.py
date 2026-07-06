"""
setup_dataset_folders.py
--------------------------------------------------
Membuat struktur folder dataset kosong untuk training YOLOv8.

Jalankan sekali di root folder ai-service/:
    python setup_dataset_folders.py

Setelah folder dibuat, kamu tinggal:
  1. Taruh foto sampah ke dataset/images/train (dan sebagian ke images/val)
  2. Anotasi tiap foto pakai LabelImg / CVAT dalam format YOLO
  3. Simpan hasil anotasi (.txt) ke dataset/labels/train dan labels/val
     dengan NAMA FILE SAMA seperti gambarnya (beda ekstensi saja).
     Contoh: images/train/botol001.jpg -> labels/train/botol001.txt
"""

import os

FOLDERS = [
    "dataset/images/train",
    "dataset/images/val",
    "dataset/labels/train",
    "dataset/labels/val",
]


def main():
    for folder in FOLDERS:
        os.makedirs(folder, exist_ok=True)
        # buat file .gitkeep supaya folder kosong tetap ke-track di git
        gitkeep_path = os.path.join(folder, ".gitkeep")
        if not os.path.exists(gitkeep_path):
            with open(gitkeep_path, "w") as f:
                f.write("")
        print(f"OK  -> {folder}")

    print("\nStruktur folder dataset berhasil dibuat.")
    print("Selanjutnya:")
    print("  1. Masukkan foto ke dataset/images/train dan dataset/images/val")
    print("  2. Anotasi dengan LabelImg (format YOLO) -> simpan .txt di dataset/labels/...")
    print("  3. Jalankan: yolo train data=data.yaml model=yolov8n.pt epochs=50")


if __name__ == "__main__":
    main()