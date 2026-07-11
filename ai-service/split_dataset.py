"""
split_dataset.py
--------------------------------------------------
Berguna kalau kamu sudah punya kumpulan foto + file anotasi (.txt)
tercampur dalam SATU folder (misal setelah selesai labeling di
LabelImg), dan ingin otomatis dibagi ke struktur:

    dataset/images/train, dataset/images/val
    dataset/labels/train, dataset/labels/val

Cara pakai:
    1. Taruh semua gambar (.jpg/.png) DAN file label (.txt) hasil
       LabelImg dalam satu folder, misal: raw_data/
       raw_data/
         botol001.jpg
         botol001.txt
         kardus002.jpg
         kardus002.txt
         ...

    2. Jalankan:
       python split_dataset.py --source raw_data --val_ratio 0.2

    3. Script akan otomatis menyalin file ke dataset/images/train,
       dataset/images/val, dataset/labels/train, dataset/labels/val
       sesuai rasio yang ditentukan (default 20% untuk validasi).

PERBAIKAN dari versi sebelumnya:
  1. Ditambahkan guard supaya folder 'train' tidak berakhir kosong
     kalau dataset kecil dan val_ratio terlalu besar (script akan
     berhenti dengan pesan jelas, bukan lanjut diam-diam dengan
     dataset training kosong).
  2. Ditambahkan laporan distribusi kelas (dari class id di baris
     pertama tiap file label) supaya kelihatan kalau ada kelas yang
     datanya jauh lebih sedikit dari yang lain sebelum training.
"""

import argparse
import random
import shutil
from collections import Counter
from pathlib import Path

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def find_image_label_pairs(source_dir: Path):
    """Cari pasangan (gambar, label) yang punya nama file sama."""
    pairs = []
    missing_label = []

    for img_path in sorted(source_dir.iterdir()):
        if img_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue
        label_path = img_path.with_suffix(".txt")
        if label_path.exists():
            pairs.append((img_path, label_path))
        else:
            missing_label.append(img_path.name)

    return pairs, missing_label


def split_pairs(pairs, val_ratio: float, seed: int = 42):
    random.Random(seed).shuffle(pairs)
    val_count = max(1, int(len(pairs) * val_ratio)) if pairs else 0
    val_pairs = pairs[:val_count]
    train_pairs = pairs[val_count:]
    return train_pairs, val_pairs


def copy_pairs(pairs, images_dst: Path, labels_dst: Path):
    images_dst.mkdir(parents=True, exist_ok=True)
    labels_dst.mkdir(parents=True, exist_ok=True)
    for img_path, label_path in pairs:
        shutil.copy2(img_path, images_dst / img_path.name)
        shutil.copy2(label_path, labels_dst / label_path.name)


def count_class_ids(pairs):
    """Hitung berapa kali tiap class id muncul di seluruh file label
    (satu gambar bisa mengandung beberapa objek/kelas)."""
    counter = Counter()
    for _, label_path in pairs:
        with open(label_path, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                class_id = line.split()[0]
                counter[class_id] += 1
    return counter


def main():
    parser = argparse.ArgumentParser(description="Split dataset gambar+label ke folder train/val")
    parser.add_argument("--source", type=str, required=True, help="Folder sumber berisi gambar + file .txt label")
    parser.add_argument("--dest", type=str, default="dataset", help="Folder tujuan dataset (default: dataset)")
    parser.add_argument("--val_ratio", type=float, default=0.2, help="Proporsi data untuk validasi (default: 0.2)")
    args = parser.parse_args()

    source_dir = Path(args.source)
    dest_dir = Path(args.dest)

    if not source_dir.exists():
        raise SystemExit(f"Folder sumber '{source_dir}' tidak ditemukan.")

    if not (0 < args.val_ratio < 1):
        raise SystemExit("--val_ratio harus di antara 0 dan 1 (contoh: 0.2 untuk 20%).")

    pairs, missing_label = find_image_label_pairs(source_dir)

    if missing_label:
        print(f"PERINGATAN: {len(missing_label)} gambar tidak punya file label (.txt) dan akan dilewati:")
        for name in missing_label[:10]:
            print(f"  - {name}")
        if len(missing_label) > 10:
            print(f"  ... dan {len(missing_label) - 10} lainnya")

    if not pairs:
        raise SystemExit("Tidak ada pasangan gambar+label yang valid ditemukan. Pastikan sudah selesai labeling.")

    train_pairs, val_pairs = split_pairs(pairs, args.val_ratio)

    if not train_pairs:
        raise SystemExit(
            f"Dataset terlalu kecil ({len(pairs)} gambar) untuk val_ratio={args.val_ratio}: "
            "folder 'train' akan kosong. Kecilkan --val_ratio atau tambah data dulu."
        )
    if not val_pairs:
        print(
            "PERINGATAN: folder 'val' kosong (dataset terlalu kecil). "
            "yolo train tetap bisa jalan tapi tanpa validasi yang berarti."
        )

    copy_pairs(train_pairs, dest_dir / "images" / "train", dest_dir / "labels" / "train")
    copy_pairs(val_pairs, dest_dir / "images" / "val", dest_dir / "labels" / "val")

    print("\nSelesai membagi dataset:")
    print(f"  Total pasangan gambar+label : {len(pairs)}")
    print(f"  Train                       : {len(train_pairs)}")
    print(f"  Val                         : {len(val_pairs)}")

    class_counts = count_class_ids(pairs)
    if class_counts:
        print("\nDistribusi class id di seluruh data (cek keseimbangan sebelum training):")
        for class_id, count in sorted(class_counts.items()):
            print(f"  class {class_id}: {count} objek")

    print(f"\nDataset siap di: {dest_dir.resolve()}")
    print("Langkah selanjutnya: yolo train data=data.yaml model=yolov8n.pt epochs=50")


if __name__ == "__main__":
    main()