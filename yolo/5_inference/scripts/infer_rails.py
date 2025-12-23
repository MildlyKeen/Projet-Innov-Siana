import json
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO


# -----------------------------
# CONFIG
# -----------------------------
MODEL_PATH = r"runs/segment/train2/weights/best.onnx"   # rails onnx
SOURCE_VIDEO = r"8_inputs/video.mp4"                             # <-- mets ton chemin
OUT_VIDEO = r"7_outputs/overlays/rails_overlay.mp4"
OUT_JSONL = r"7_outputs/predictions/rails_per_frame.jsonl"

IMGSZ = 640
CONF = 0.25

EXPECTED_RAILS = 6      # voies attendues (1..6)
MIN_AREA = 800          # filtre bruit (à ajuster)
CONNECTIVITY = 8        # 4 ou 8


# -----------------------------
# UTILS
# -----------------------------
def rank_rails_from_mask(mask_bin, expected=6, min_area=800):
    """
    mask_bin: np.uint8 (H,W) valeurs 0/255
    Retour: liste de voies triées gauche->droite avec {rank,label,cx,bbox,area}
    """
    num, labels, stats, centroids = cv2.connectedComponentsWithStats(
        mask_bin, connectivity=CONNECTIVITY
    )

    comps = []
    for i in range(1, num):  # 0 = background
        area = stats[i, cv2.CC_STAT_AREA]
        if area < min_area:
            continue
        cx, cy = centroids[i]
        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]
        comps.append(
            {"id": i, "cx": float(cx), "cy": float(cy), "bbox": [int(x), int(y), int(x+w), int(y+h)], "area": int(area)}
        )

    # tri gauche->droite
    comps.sort(key=lambda c: c["cx"])

    # si trop de composantes (bruit), garder les plus grandes
    if len(comps) > expected:
        comps = sorted(comps, key=lambda c: c["area"], reverse=True)[:expected]
        comps.sort(key=lambda c: c["cx"])

    # assigner voie1..voie6
    for k, c in enumerate(comps, start=1):
        c["rank"] = k
        c["label"] = f"voie{k}"
    return comps


def overlay_mask(frame, mask_bin):
    """Superpose un masque binaire sur l'image (simple)."""
    overlay = frame.copy()
    # couleur fixe (vert) - tu peux changer si tu veux
    overlay[mask_bin > 0] = (0, 255, 0)
    return cv2.addWeighted(frame, 0.65, overlay, 0.35, 0)


# -----------------------------
# MAIN
# -----------------------------
def main():
    model = YOLO(MODEL_PATH)

    cap = cv2.VideoCapture(SOURCE_VIDEO)
    if not cap.isOpened():
        raise RuntimeError(f"Impossible d'ouvrir la vidéo: {SOURCE_VIDEO}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    Path(OUT_VIDEO).parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(OUT_VIDEO, fourcc, fps, (w, h))

    Path(OUT_JSONL).parent.mkdir(parents=True, exist_ok=True)
    fjson = open(OUT_JSONL, "w", encoding="utf-8")

    frame_idx = 0

    print("🚀 Inference rails ONNX:", MODEL_PATH)
    print("🎥 Source:", SOURCE_VIDEO)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Ultralytics inference
        results = model.predict(frame, imgsz=IMGSZ, conf=CONF, verbose=False)
        r = results[0]

        # Construire masque binaire global (union des instances)
        mask_bin = np.zeros((frame.shape[0], frame.shape[1]), dtype=np.uint8)

        if r.masks is not None and r.masks.data is not None:
            # r.masks.data: (n, mask_h, mask_w) float/0-1
            masks = r.masks.data.cpu().numpy()
            # resize masks to frame size if needed
            for m in masks:
                m_resized = cv2.resize(m, (frame.shape[1], frame.shape[0]), interpolation=cv2.INTER_NEAREST)
                mask_bin[m_resized > 0.5] = 255

        # Numérotation voies gauche->droite
        rails = rank_rails_from_mask(mask_bin, expected=EXPECTED_RAILS, min_area=MIN_AREA)

        # Overlay + dessin bbox voies
        out = overlay_mask(frame, mask_bin)
        for rail in rails:
            x1, y1, x2, y2 = rail["bbox"]
            cv2.rectangle(out, (x1, y1), (x2, y2), (255, 255, 255), 2)
            cv2.putText(out, rail["label"], (x1, max(20, y1-10)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)

        writer.write(out)

        # JSONL (backend)
        payload = {
            "frame": frame_idx,
            "rails_detected": len(rails),
            "rails": [
                {"rank": r["rank"], "label": r["label"], "cx": r["cx"], "bbox": r["bbox"], "area": r["area"]}
                for r in rails
            ]
        }
        fjson.write(json.dumps(payload, ensure_ascii=False) + "\n")

        frame_idx += 1
        if frame_idx % 50 == 0:
            print(f"Processed {frame_idx} frames...")

    cap.release()
    writer.release()
    fjson.close()

    print("✅ Done.")
    print("📹 Overlay video:", OUT_VIDEO)
    print("🧾 JSONL:", OUT_JSONL)


if __name__ == "__main__":
    main()
