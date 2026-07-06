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
"""

import argparse
import random
import shutil
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

    copy_pairs(train_pairs, dest_dir / "images" / "train", dest_dir / "labels" / "train")
    copy_pairs(val_pairs, dest_dir / "images" / "val", dest_dir / "labels" / "val")

    print("\nSelesai membagi dataset:")
    print(f"  Total pasangan gambar+label : {len(pairs)}")
    print(f"  Train                       : {len(train_pairs)}")
    print(f"  Val                         : {len(val_pairs)}")
    print(f"\nDataset siap di: {dest_dir.resolve()}")
    print("Langkah selanjutnya: yolo train data=data.yaml model=yolov8n.pt epochs=50")


if __name__ == "__main__":
    main()