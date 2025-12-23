import os
import random
import shutil
import time
from pathlib import Path
from tqdm import tqdm


# -------------------------
# CONFIG (modifie si besoin)
# -------------------------
SEED = 42
TRAIN_RATIO = 0.80
VAL_RATIO   = 0.10
TEST_RATIO  = 0.10

# Dossier source (tes annotations copiées)
SRC_IMAGES = Path("data_trains/images")
SRC_LABELS = Path("data_trains/labels_1class")



# Dossier de sortie (splits)
OUT_BASE = Path("1_datasets/detection_trains")

# Extensions images acceptées
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}


def die(msg: str):
    raise SystemExit(f"\n❌ {msg}\n")


def ensure_ratios():
    total = TRAIN_RATIO + VAL_RATIO + TEST_RATIO
    if abs(total - 1.0) > 1e-9:
        die(f"Les ratios doivent faire 1.0. Actuel = {total}")


def list_images(folder: Path):
    if not folder.exists():
        die(f"Dossier introuvable: {folder}")
    imgs = [p for p in folder.iterdir() if p.suffix.lower() in IMG_EXTS]
    if not imgs:
        die(f"Aucune image trouvée dans: {folder}")
    return sorted(imgs)


def match_labels(images):
    """
    Exige un fichier label .txt par image (même nom).
    """
    ok_pairs = []
    missing_labels = []
    for img in images:
        lbl = SRC_LABELS / (img.stem + ".txt")
        if lbl.exists():
            ok_pairs.append((img, lbl))
        else:
            missing_labels.append(img.name)

    # labels orphelins
    label_files = sorted([p for p in SRC_LABELS.iterdir() if p.suffix.lower() == ".txt"])
    img_stems = set([img.stem for img in images])
    orphan_labels = [p.name for p in label_files if p.stem not in img_stems]

    return ok_pairs, missing_labels, orphan_labels


def make_dirs():
    for split in ["train", "val", "test"]:
        (OUT_BASE / "images" / split).mkdir(parents=True, exist_ok=True)
        (OUT_BASE / "labels" / split).mkdir(parents=True, exist_ok=True)


def safe_copy(src: Path, dst: Path, retries: int = 5, delay: float = 0.25):
    """
    Copie robuste Windows: évite certains locks (WinError 32) en réessayant.
    Copie binaire (sans copy2) => moins de problèmes de métadonnées.
    """
    last_err = None
    for attempt in range(1, retries + 1):
        try:
            dst.parent.mkdir(parents=True, exist_ok=True)
            with open(src, "rb") as fsrc:
                with open(dst, "wb") as fdst:
                    shutil.copyfileobj(fsrc, fdst, length=1024 * 1024)
            return
        except PermissionError as e:
            last_err = e
            time.sleep(delay * attempt)  # backoff progressif
    raise last_err


def copy_pairs(pairs, split_name):
    img_out = OUT_BASE / "images" / split_name
    lbl_out = OUT_BASE / "labels" / split_name
    for img, lbl in tqdm(pairs, desc=f"Copy {split_name}", unit="img"):
        safe_copy(img, img_out / img.name)
        safe_copy(lbl, lbl_out / lbl.name)

def main():
    ensure_ratios()
    random.seed(SEED)

    images = list_images(SRC_IMAGES)
    pairs, missing_labels, orphan_labels = match_labels(images)

    print(f"\n📦 Images trouvées: {len(images)}")
    print(f"✅ Paires image+label: {len(pairs)}")
    if missing_labels:
        print(f"⚠️ Images sans label: {len(missing_labels)} (ex: {missing_labels[:5]})")
    if orphan_labels:
        print(f"⚠️ Labels sans image: {len(orphan_labels)} (ex: {orphan_labels[:5]})")

    if len(pairs) < 10:
        die("Pas assez de paires image/label pour un split fiable.")

    # shuffle
    random.shuffle(pairs)

    n = len(pairs)
    n_train = int(n * TRAIN_RATIO)
    n_val = int(n * VAL_RATIO)
    n_test = n - n_train - n_val

    train_pairs = pairs[:n_train]
    val_pairs = pairs[n_train:n_train + n_val]
    test_pairs = pairs[n_train + n_val:]

    print(f"\n🔀 Split:")
    print(f"  train: {len(train_pairs)}")
    print(f"  val  : {len(val_pairs)}")
    print(f"  test : {len(test_pairs)}")

    # sécurité: aucun split vide
    if min(len(train_pairs), len(val_pairs), len(test_pairs)) == 0:
        die("Un des splits est vide. Ajuste les ratios ou ajoute plus de données.")

    make_dirs()
    copy_pairs(train_pairs, "train")
    copy_pairs(val_pairs, "val")
    copy_pairs(test_pairs, "test")

    print("\n✅ Split YOLO terminé.")
    print("📍 Résultat : 1_datasets/detection_trains/images/{train,val,test} + labels/{train,val,test}")


if __name__ == "__main__":
    main()
