"""
remap_dataset.py
--------------------------------------------------
Meremap dataset hasil download Roboflow (GARBAGE-CLASSIFICATION-3-x,
6 kelas: BIODEGRADABLE, CARDBOARD, GLASS, METAL, PAPER, PLASTIC)
menjadi dataset 5 kategori sesuai tabel `waste_categories` di database
recynt_ai (plastik, organik, kertas, logam, kaca).

CARDBOARD dan PAPER digabung menjadi satu kelas "kertas".

Jalankan sekali saja di folder ai-service/:
    python remap_dataset.py

Setelah selesai, folder dataset/ akan siap dipakai langsung dengan
data.yaml yang sudah ada (5 kelas: plastik, organik, kertas, logam, kaca):
    yolo train data=data.yaml model=yolov8n.pt epochs=50

PERBAIKAN dari versi sebelumnya:
  1. Folder sumber di-auto-detect (tidak lagi hardcode nama persis),
     supaya tidak error kalau Roboflow kasih nama folder sedikit beda
     (mis. GARBAGE-CLASSIFICATION-3-2, -3, dst).
  2. Nama file dari split "test" yang digabung ke "train" diberi
     prefix supaya tidak menimpa diam-diam file dari split "train"
     yang kebetulan punya nama sama.
  3. Ditambahkan laporan jumlah gambar per KELAS BARU di akhir, supaya
     langsung kelihatan kalau ada kelas yang datanya terlalu sedikit
     (dataset imbalance) sebelum training dijalankan.
"""

from pathlib import Path
import shutil
import sys

# ---------------------------------------------------------------
# KONFIGURASI
# ---------------------------------------------------------------
# Pola nama folder hasil download Roboflow. Kalau nama persis
# "GARBAGE-CLASSIFICATION-3-2" tidak ketemu, script akan mencari
# folder lain yang cocok dengan pola di bawah ini.
SOURCE_DIR_EXACT = Path("GARBAGE-CLASSIFICATION-3-2")
SOURCE_DIR_GLOB_PATTERN = "GARBAGE-CLASSIFICATION-3-*"

# Folder tujuan (harus sama dengan yang dirujuk di data.yaml kamu)
DEST_DIR = Path("dataset")

# Urutan kelas LAMA persis seperti di data.yaml folder SOURCE_DIR.
# PENTING: cek ulang urutan ini di data.yaml hasil download Roboflow
# sebelum menjalankan script -- kalau urutannya beda, class id akan
# ketuker dan hasil remap jadi salah tanpa error apapun.
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

# Split yang mau digabungkan. "test" ikut digabung ke train supaya
# data trainingnya lebih banyak (boleh dihapus barisnya kalau tidak mau).
SPLIT_MAP = {
    "train": "train",
    "valid": "val",
    "test": "train",
}

IMAGE_EXTENSIONS = {".jpg", ".jpeg", ".png"}


def find_source_dir() -> Path:
    """Cari folder dataset hasil download Roboflow, toleran terhadap
    perbedaan nama versi (mis. -2, -3, dst)."""
    if SOURCE_DIR_EXACT.exists():
        return SOURCE_DIR_EXACT

    candidates = sorted(Path(".").glob(SOURCE_DIR_GLOB_PATTERN))
    candidates = [c for c in candidates if c.is_dir()]

    if len(candidates) == 1:
        print(f"Folder '{SOURCE_DIR_EXACT}' tidak ditemukan, memakai '{candidates[0]}' sebagai gantinya.\n")
        return candidates[0]
    elif len(candidates) > 1:
        raise SystemExit(
            f"Ditemukan beberapa folder yang cocok: {[str(c) for c in candidates]}\n"
            "Set SOURCE_DIR_EXACT di script ini ke folder yang benar, lalu jalankan ulang."
        )
    else:
        raise SystemExit(
            f"Folder sumber tidak ditemukan (dicoba: '{SOURCE_DIR_EXACT}' dan pola '{SOURCE_DIR_GLOB_PATTERN}'). "
            "Pastikan sudah menjalankan download_dataset.py di folder yang sama dengan script ini."
        )


def build_old_id_to_new_id():
    """Bikin mapping index lama (0..N-1) -> index baru (0..M-1)."""
    new_index = {name: i for i, name in enumerate(NEW_NAMES)}
    mapping = {}
    for old_id, old_name in enumerate(OLD_NAMES):
        new_name = NAME_MAP[old_name]
        mapping[old_id] = new_index[new_name]
    return mapping


def remap_label_file(src_label_path: Path, dst_label_path: Path, id_map: dict):
    """Baca file label YOLO lama, ganti class id sesuai mapping, simpan ke tujuan.
    Return list of new_class_id yang berhasil ditulis (untuk statistik)."""
    lines_out = []
    new_ids_written = []
    with open(src_label_path, "r") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            parts = line.split()
            old_class_id = int(parts[0])
            if old_class_id not in id_map:
                continue
            new_class_id = id_map[old_class_id]
            new_line = " ".join([str(new_class_id)] + parts[1:])
            lines_out.append(new_line)
            new_ids_written.append(new_class_id)

    if lines_out:
        dst_label_path.parent.mkdir(parents=True, exist_ok=True)
        with open(dst_label_path, "w") as f:
            f.write("\n".join(lines_out) + "\n")
        return new_ids_written
    return []


def unique_dest_name(dest_dir: Path, filename: str, prefix: str = "") -> str:
    """Kalau filename sudah ada di dest_dir, kasih prefix supaya tidak
    menimpa file yang sudah ada (mis. saat 'test' digabung ke 'train')."""
    candidate = prefix + filename if prefix else filename
    if not (dest_dir / candidate).exists():
        return candidate
    stem = Path(candidate).stem
    suffix = Path(candidate).suffix
    i = 1
    while (dest_dir / f"{stem}_{i}{suffix}").exists():
        i += 1
    return f"{stem}_{i}{suffix}"


def process_split(source_dir: Path, source_split: str, dest_split: str, id_map: dict, counters: dict, class_counts: dict):
    images_src = source_dir / source_split / "images"
    labels_src = source_dir / source_split / "labels"

    if not images_src.exists():
        print(f"Lewati '{source_split}' (folder tidak ditemukan: {images_src})")
        return

    images_dst = DEST_DIR / "images" / dest_split
    labels_dst = DEST_DIR / "labels" / dest_split
    images_dst.mkdir(parents=True, exist_ok=True)
    labels_dst.mkdir(parents=True, exist_ok=True)

    # Kalau split ini "menumpuk" ke dest split yang sudah dipakai split lain
    # (mis. test -> train setelah train -> train), beri prefix biar tidak
    # menimpa file yang namanya kebetulan sama.
    collision_prefix = f"{source_split}_" if source_split != dest_split else ""

    for img_path in sorted(images_src.iterdir()):
        if img_path.suffix.lower() not in IMAGE_EXTENSIONS:
            continue

        label_path = labels_src / (img_path.stem + ".txt")
        if not label_path.exists():
            counters["missing_label"] += 1
            continue

        new_img_name = unique_dest_name(images_dst, img_path.name, collision_prefix)
        new_label_name = Path(new_img_name).stem + ".txt"
        dst_label_path = labels_dst / new_label_name

        new_ids = remap_label_file(label_path, dst_label_path, id_map)

        if new_ids:
            shutil.copy2(img_path, images_dst / new_img_name)
            counters["copied"] += 1
            for cid in set(new_ids):  # hitung per gambar, bukan per objek
                class_counts[cid] += 1
        else:
            counters["empty_after_remap"] += 1


def main():
    source_dir = find_source_dir()
    id_map = build_old_id_to_new_id()

    print("Mapping kelas lama -> baru:")
    for old_id, old_name in enumerate(OLD_NAMES):
        new_id = id_map[old_id]
        print(f"  {old_id} {old_name:15s} -> {new_id} {NEW_NAMES[new_id]}")
    print()

    counters = {"copied": 0, "missing_label": 0, "empty_after_remap": 0}
    class_counts = {i: 0 for i in range(len(NEW_NAMES))}

    for source_split, dest_split in SPLIT_MAP.items():
        process_split(source_dir, source_split, dest_split, id_map, counters, class_counts)

    print("\nSelesai remap dataset:")
    print(f"  Gambar berhasil disalin       : {counters['copied']}")
    print(f"  Gambar tanpa file label       : {counters['missing_label']}")
    print(f"  Gambar dilewati (label kosong): {counters['empty_after_remap']}")

    print("\nJumlah gambar per kelas baru (cek keseimbangan data):")
    for i, name in enumerate(NEW_NAMES):
        print(f"  {name:10s}: {class_counts[i]} gambar")
    min_class = min(class_counts.values()) if class_counts else 0
    max_class = max(class_counts.values()) if class_counts else 0
    if max_class > 0 and min_class < max_class * 0.3:
        print(
            "\n  PERINGATAN: distribusi kelas cukup timpang "
            "(kelas terkecil < 30% dari kelas terbesar). "
            "Model kemungkinan akan lebih buruk mendeteksi kelas yang datanya sedikit."
        )

    print(f"\nDataset siap di folder: {DEST_DIR.resolve()}")
    print("Langkah selanjutnya: yolo train data=data.yaml model=yolov8n.pt epochs=50")


if __name__ == "__main__":
    main()