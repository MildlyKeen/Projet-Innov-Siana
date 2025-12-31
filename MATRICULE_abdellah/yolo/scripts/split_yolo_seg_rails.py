import random, shutil
from pathlib import Path
from tqdm import tqdm

SEED = 42
TRAIN_RATIO = 0.80
VAL_RATIO   = 0.10
TEST_RATIO  = 0.10

SRC_IMAGES = Path("data_rails/images")
SRC_LABELS = Path("data_rails/labels_1class")

OUT_BASE = Path("1_datasets/segmentation_rails")
IMG_EXTS = {".jpg", ".jpeg", ".png", ".bmp", ".webp"}

def die(msg): raise SystemExit(f"❌ {msg}")

def list_images():
    if not SRC_IMAGES.exists(): die(f"Dossier introuvable: {SRC_IMAGES}")
    imgs = [p for p in SRC_IMAGES.iterdir() if p.suffix.lower() in IMG_EXTS]
    if not imgs: die("Aucune image trouvée.")
    return sorted(imgs)

def make_dirs():
    for split in ["train","val","test"]:
        (OUT_BASE/"images"/split).mkdir(parents=True, exist_ok=True)
        (OUT_BASE/"labels"/split).mkdir(parents=True, exist_ok=True)

def main():
    random.seed(SEED)
    imgs = list_images()

    pairs = []
    missing = []
    for img in imgs:
        lbl = SRC_LABELS / f"{img.stem}.txt"
        if lbl.exists(): pairs.append((img,lbl))
        else: missing.append(img.name)

    print(f"Images: {len(imgs)} | Paires: {len(pairs)} | Sans label: {len(missing)}")
    if len(pairs) < 10: die("Pas assez de données.")

    random.shuffle(pairs)
    n = len(pairs)
    n_train = int(n*TRAIN_RATIO)
    n_val = int(n*VAL_RATIO)
    train = pairs[:n_train]
    val = pairs[n_train:n_train+n_val]
    test = pairs[n_train+n_val:]

    if min(len(train),len(val),len(test)) == 0:
        die("Split vide, ajuste les ratios.")

    make_dirs()

    for split_name, split_pairs in [("train",train),("val",val),("test",test)]:
        for img,lbl in tqdm(split_pairs, desc=f"Copy {split_name}"):
            shutil.copy2(img, OUT_BASE/"images"/split_name/img.name)
            shutil.copy2(lbl, OUT_BASE/"labels"/split_name/lbl.name)

    print("✅ Split rails terminé.")

if __name__ == "__main__":
    main()
