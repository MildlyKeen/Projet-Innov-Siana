import json
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO


# -----------------------------
# CONFIG
# -----------------------------
MODEL_PATH = r"runs/detect/train5/weights/best.pt"  # ton modèle trains (1 classe)
SOURCE_VIDEO = r"8_inputs/video2.mp4"                         # <-- mets ton chemin vidéo
OUT_VIDEO = r"7_outputs/overlays/trains_track_overlay.mp4"
OUT_JSONL = r"7_outputs/predictions/trains_per_frame.jsonl"

IMGSZ = 640
CONF = 0.25
IOU = 0.45

# Tracking
TRACKER = "botsort.yaml"  # fourni avec Ultralytics
MAX_SLOTS = 6             # train1..train6


# -----------------------------
# UTILS
# -----------------------------
def bbox_center_x(b):
    x1, y1, x2, y2 = b
    return (x1 + x2) / 2.0

def rank_left_to_right(dets, max_slots=6):
    """
    dets: list dict {bbox:[x1,y1,x2,y2], conf, track_id}
    Ajoute rank_lr (1..6) et lr_label (train1..train6) selon x_center.
    """
    dets_sorted = sorted(dets, key=lambda d: bbox_center_x(d["bbox"]))
    dets_sorted = dets_sorted[:max_slots]
    for i, d in enumerate(dets_sorted, start=1):
        d["rank_lr"] = i
        d["lr_label"] = f"train{i}"
    return dets_sorted


def draw_box(img, bbox, text, thickness=2):
    x1, y1, x2, y2 = map(int, bbox)
    cv2.rectangle(img, (x1, y1), (x2, y2), (0, 255, 255), thickness)
    cv2.putText(img, text, (x1, max(25, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 255), 2)


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

    print("🚀 Train tracking inference:", MODEL_PATH)
    print("🎥 Source:", SOURCE_VIDEO)
    print("🧭 Tracker:", TRACKER)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # Tracking (IDs stables)
        results = model.track(
            frame,
            imgsz=IMGSZ,
            conf=CONF,
            iou=IOU,
            tracker=TRACKER,
            persist=True,
            verbose=False
        )
        r = results[0]

        dets = []
        # r.boxes contient les bbox détectées
        if r.boxes is not None and len(r.boxes) > 0:
            xyxy = r.boxes.xyxy.cpu().numpy()
            confs = r.boxes.conf.cpu().numpy()
            clss = r.boxes.cls.cpu().numpy().astype(int)

            # track id si dispo
            track_ids = None
            if getattr(r.boxes, "id", None) is not None:
                track_ids = r.boxes.id.cpu().numpy().astype(int)

            for i in range(len(xyxy)):
                # modèle 1 classe -> cls=0 normalement
                bbox = xyxy[i].tolist()
                det = {
                    "bbox": bbox,
                    "conf": float(confs[i]),
                    "class_id": int(clss[i]),
                    "track_id": int(track_ids[i]) if track_ids is not None else None,
                }
                dets.append(det)

        # Numérotation gauche->droite (train1..train6)
        dets_ranked = rank_left_to_right(dets, max_slots=MAX_SLOTS)

        # Overlay
        out = frame.copy()
        for d in dets_ranked:
            tid = d["track_id"]
            label = d["lr_label"]
            conf = d["conf"]
            txt = f"{label}  id={tid}  conf={conf:.2f}" if tid is not None else f"{label}  conf={conf:.2f}"
            draw_box(out, d["bbox"], txt)

        writer.write(out)

        # JSONL (backend)
        payload = {
            "frame": frame_idx,
            "trains_detected": len(dets_ranked),
            "trains": dets_ranked
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
