"""
remap_dataset.py
--------------------------------------------------
Meremap dataset hasil download Roboflow (GARBAGE-CLASSIFICATION-3-2,
6 kelas: BIODEGRADABLE, CARDBOARD, GLASS, METAL, PAPER, PLASTIC)
menjadi dataset 5 kategori sesuai tabel `waste_categories` di database
recynt_ai (plastik, organik, kertas, logam, kaca).

CARDBOARD dan PAPER digabung menjadi satu kelas "kertas".

Jalankan sekali saja di folder ai-service/:
    python remap_dataset.py

Setelah selesai, folder dataset/ akan siap dipakai langsung dengan
data.yaml yang sudah ada (5 kelas: plastik, organik, kertas, logam, kaca):
    yolo train data=data.yaml model=yolov8n.pt epochs=50
"""

from pathlib import Path
import shutil

# ---------------------------------------------------------------
# KONFIGURASI
# ---------------------------------------------------------------
# Folder hasil download Roboflow (sesuaikan kalau nama foldernya beda)
SOURCE_DIR = Path("GARBAGE-CLASSIFICATION-3-2")

# Folder tujuan (harus sama dengan yang dirujuk di data.yaml kamu)
DEST_DIR = Path("dataset")

# Urutan kelas LAMA persis seperti di data.yaml folder SOURCE_DIR
OLD_NAMES = ["BIODEGRADABLE", "CARDBOARD", "GLASS", "METAL", "PAPER", "PLASTIC"]

# Urutan kelas BARU persis seperti di data.yaml training kamu
NEW_NAMES = ["plastik", "organik", "kertas", "logam", "kaca"]

# Pemetaan nama kelas lama -> nama kelas baru
NAME_MAP = {
    "BIODEGRADABLE": "organik",
    "CARDBOARD": "kertas",
    "GLASS": "kaca",
    "METAL": "logam",
    "PAPER": "kertas",
    "PLASTIC": "plastik",
}

# Split yang mau digabungkan. Roboflow biasanya punya train/valid/test;
# kita petakan train->train, valid->val. "test" ikut digabung ke train
# supaya data trainingnya lebih banyak (opsional, boleh dihapus barisnya
# kalau tidak mau ikutkan test).
SPLIT_MAP = {
    "train": "train",
    "valid": "val",
    "test": "train",
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def build_old_id_to_new_id():
    """Bikin mapping index lama (0-5) -> index baru (0-4)."""
    new_index = {name: i for i, name in enumerate(NEW_NAMES)}
    mapping = {}
    for old_id, old_name in enumerate(OLD_NAMES):
        new_name = NAME_MAP[old_name]
        mapping[old_id] = new_index[new_name]
    return mapping


def remap_label_file(src_label_path: Path, dst_label_path: Path, id_map: dict):
    """Baca file label YOLO lama, ganti class id sesuai mapping, simpan ke tujuan."""
    lines_out = []
    with open(src_label_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            old_class_id = int(parts[0])
            if old_class_id not in id_map:
                # kelas tidak dikenali, skip baris ini
                continue
            new_class_id = id_map[old_class_id]
            new_line = " ".join([str(new_class_id)] + parts[1:])
            lines_out.append(new_line)

    if lines_out:  # hanya tulis file kalau ada minimal 1 objek valid
        dst_label_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dst_label_path, "w") as f:
            f.write("\n".join(lines_out) + "\n")
        return True
    return False


def process_split(source_split: str, dest_split: str, id_map: dict, counters: dict):
    images_src = SOURCE_DIR / source_split / "images"
    labels_src = SOURCE_DIR / source_split / "labels"

    if not images_src.exists():
        print(f"Lewati '{source_split}' (folder tidak ditemukan: {images_src})")
        return

    images_dst = DEST_DIR / "images" / dest_split
    labels_dst = DEST_DIR / "labels" / dest_split
    images_dst.mkdir(parents=True, exist_ok=True)
    labels_dst.mkdir(parents=True, exist_ok=True)

    for img_path in sorted(images_src.iterdir()):
        if img_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        label_path = labels_src / (img_path.stem + ".txt")
        if not label_path.exists():
            counters["missing_label"] += 1
            continue

        dst_label_path = labels_dst / label_path.name
        has_valid_labels = remap_label_file(label_path, dst_label_path, id_map)

        if has_valid_labels:
            # copy gambar hanya kalau ada minimal 1 label valid setelah remap
            shutil.copy2(img_path, images_dst / img_path.name)
            counters["copied"] += 1
        else:
            counters["empty_after_remap"] += 1


def main():
    if not SOURCE_DIR.exists():
        raise SystemExit(
            f"Folder sumber '{SOURCE_DIR}' tidak ditemukan. "
            "Pastikan sudah menjalankan download_dataset.py dan nama foldernya sesuai."
        )

    id_map = build_old_id_to_new_id()

    print("Mapping kelas lama -> baru:")
    for old_id, old_name in enumerate(OLD_NAMES):
        new_id = id_map[old_id]
        print(f"  {old_id} {old_name:15s} -> {new_id} {NEW_NAMES[new_id]}")
    print()

    counters = {"copied": 0, "missing_label": 0, "empty_after_remap": 0}

    processed_dest_splits = set()
    for source_split, dest_split in SPLIT_MAP.items():
        process_split(source_split, dest_split, id_map, counters)
        processed_dest_splits.add(dest_split)

    print("\nSelesai remap dataset:")
    print(f"  Gambar berhasil disalin       : {counters['copied']}")
    print(f"  Gambar tanpa file label       : {counters['missing_label']}")
    print(f"  Gambar dilewati (label kosong): {counters['empty_after_remap']}")
    print(f"\nDataset siap di folder: {DEST_DIR.resolve()}")
    print("Langkah selanjutnya: yolo train data=data.yaml model=yolov8n.pt epochs=50")


if __name__ == "__main__":
    main()