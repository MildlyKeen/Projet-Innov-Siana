"""
Train a simple SVM on matricule patches.
Labels are the first four digits of each filename in the dataset folder.
"""

import argparse
import json
from pathlib import Path
from typing import Dict, List, Tuple

import cv2
import numpy as np

DATA_DIR_DEFAULT = Path("datta") / "matricule TGV"
MODEL_PATH_DEFAULT = Path("models") / "matricule_svm.yml"
LABEL_MAP_DEFAULT = Path("models") / "matricule_labels.json"
IMAGE_SIZE = (128, 32)  # width, height


def extract_label(path: Path) -> str:
    name = path.stem
    return name[:4]


def preprocess_image(path: Path) -> np.ndarray:
    img = cv2.imread(str(path))
    if img is None:
        raise ValueError(f"Cannot read image: {path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    gray = cv2.equalizeHist(gray)
    resized = cv2.resize(gray, IMAGE_SIZE, interpolation=cv2.INTER_AREA)
    blur = cv2.GaussianBlur(resized, (3, 3), 0)
    _, thresh = cv2.threshold(blur, 0, 255, cv2.THRESH_BINARY + cv2.THRESH_OTSU)
    feature = thresh.astype(np.float32).flatten() / 255.0
    return feature


def load_dataset(data_dir: Path) -> Tuple[np.ndarray, np.ndarray, Dict[int, str]]:
    image_paths = sorted(list(data_dir.glob("*.jpg")) + list(data_dir.glob("*.png")))
    if not image_paths:
        raise ValueError(f"No images found in {data_dir}")

    labels: List[str] = []
    features: List[np.ndarray] = []

    for path in image_paths:
        label = extract_label(path)
        feature = preprocess_image(path)
        labels.append(label)
        features.append(feature)

    unique_labels = sorted(set(labels))
    label_to_idx = {label: idx for idx, label in enumerate(unique_labels)}
    idx_to_label = {idx: label for label, idx in label_to_idx.items()}

    y = np.array([label_to_idx[l] for l in labels], dtype=np.int32)
    X = np.vstack(features).astype(np.float32)
    return X, y, idx_to_label


def train_svm(X: np.ndarray, y: np.ndarray) -> cv2.ml_SVM:
    svm = cv2.ml.SVM_create()
    svm.setType(cv2.ml.SVM_C_SVC)
    svm.setKernel(cv2.ml.SVM_LINEAR)
    svm.setC(1.0)
    svm.train(X, cv2.ml.ROW_SAMPLE, y)
    return svm


def evaluate(svm: cv2.ml_SVM, X: np.ndarray, y: np.ndarray) -> float:
    _, preds = svm.predict(X)
    preds = preds.ravel().astype(int)
    return float((preds == y).mean())


def ensure_dir(path: Path) -> None:
    path.mkdir(parents=True, exist_ok=True)


def split_dataset(X: np.ndarray, y: np.ndarray, train_ratio: float = 0.8) -> Tuple[np.ndarray, np.ndarray, np.ndarray, np.ndarray]:
    n = len(X)
    idx = np.random.permutation(n)
    split = int(n * train_ratio)
    train_idx, test_idx = idx[:split], idx[split:]
    return X[train_idx], X[test_idx], y[train_idx], y[test_idx]


def main():
    parser = argparse.ArgumentParser(description="Train SVM on matricule patches")
    parser.add_argument("--data-dir", type=Path, default=DATA_DIR_DEFAULT, help="Folder with matricule images")
    parser.add_argument("--model-out", type=Path, default=MODEL_PATH_DEFAULT, help="Path to save the trained SVM")
    parser.add_argument("--label-map", type=Path, default=LABEL_MAP_DEFAULT, help="Path to save label index map")
    parser.add_argument("--train-ratio", type=float, default=0.8, help="Train split ratio")
    args = parser.parse_args()

    X, y, idx_to_label = load_dataset(args.data_dir)
    X_train, X_test, y_train, y_test = split_dataset(X, y, train_ratio=args.train_ratio)

    svm = train_svm(X_train, y_train)
    train_acc = evaluate(svm, X_train, y_train)
    test_acc = evaluate(svm, X_test, y_test) if len(y_test) > 0 else float('nan')

    ensure_dir(args.model_out.parent)
    svm.save(str(args.model_out))
    with open(args.label_map, "w") as f:
        json.dump({"idx_to_label": idx_to_label}, f, indent=2)

    print(f"Images: {len(X)} | Classes: {len(idx_to_label)}")
    print(f"Train accuracy: {train_acc:.3f}")
    if len(y_test) > 0:
        print(f"Test accuracy:  {test_acc:.3f}")
    print(f"Model saved to: {args.model_out}")
    print(f"Label map saved to: {args.label_map}")


if __name__ == "__main__":
    main()
