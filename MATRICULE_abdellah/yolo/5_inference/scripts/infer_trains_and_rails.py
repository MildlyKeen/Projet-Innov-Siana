import json
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO

# -----------------------------
# CONFIG
# -----------------------------
TRAINS_MODEL = r"runs/detect/train5/weights/best.pt"
RAILS_MODEL  = r"runs/segment/train2/weights/best.onnx"

SOURCE_VIDEO = r"video.mp4"  # <-- change ce chemin

OUT_VIDEO = r"7_outputs/overlays/trains_rails_overlay.mp4"
OUT_JSONL = r"7_outputs/predictions/trains_rails_per_frame.jsonl"

IMGSZ_TRAINS = 640
IMGSZ_RAILS  = 640
CONF_TRAINS  = 0.25
CONF_RAILS   = 0.25
IOU_TRAINS   = 0.45

TRACKER = "botsort.yaml"

EXPECTED_RAILS = 6
MIN_AREA_RAIL  = 1200     # ajuste si trop de “bruit”
MASK_THRESH    = 0.5      # seuil mask (0.35–0.6 selon qualité)
POINT_OFFSET_PX = 2       # point bas-centre = y2 - 2px


# -----------------------------
# UTILS
# -----------------------------
def bbox_center_x(b):
    x1, y1, x2, y2 = b
    return (x1 + x2) / 2.0

def rank_left_to_right(items, key_fn, max_slots=None, label_prefix=""):
    """
    items: list dict
    key_fn: function(item)->float
    ajoute rank_lr 1..N + label f"{prefix}{rank}"
    """
    items_sorted = sorted(items, key=key_fn)
    if max_slots is not None:
        items_sorted = items_sorted[:max_slots]
    for i, it in enumerate(items_sorted, start=1):
        it["rank_lr"] = i
        it["lr_label"] = f"{label_prefix}{i}" if label_prefix else str(i)
    return items_sorted

def connected_components_rails(mask_bin, expected=6, min_area=1200):
    """
    mask_bin: uint8 0/255
    retourne: list rails [{rank,label,cx,bbox,area,comp_id}]
    """
    num, labels, stats, centroids = cv2.connectedComponentsWithStats(mask_bin, connectivity=8)

    comps = []
    for i in range(1, num):
        area = stats[i, cv2.CC_STAT_AREA]
        if area < min_area:
            continue
        cx, cy = centroids[i]
        x = stats[i, cv2.CC_STAT_LEFT]
        y = stats[i, cv2.CC_STAT_TOP]
        w = stats[i, cv2.CC_STAT_WIDTH]
        h = stats[i, cv2.CC_STAT_HEIGHT]
        comps.append({
            "comp_id": i,
            "cx": float(cx),
            "cy": float(cy),
            "bbox": [int(x), int(y), int(x+w), int(y+h)],
            "area": int(area),
        })

    # tri par x
    comps.sort(key=lambda c: c["cx"])

    # si trop de composantes (bruit), garder les plus grandes puis re-trier
    if len(comps) > expected:
        comps = sorted(comps, key=lambda c: c["area"], reverse=True)[:expected]
        comps.sort(key=lambda c: c["cx"])

    # assign ranks voie1..voie6
    for k, c in enumerate(comps, start=1):
        c["rank"] = k
        c["label"] = f"voie{k}"
    return comps, labels  # labels = image des composantes (H,W) avec id

def find_rail_for_point(cc_labels, rails_list, x, y):
    """
    cc_labels: matrice HxW des composantes (id)
    rails_list: list avec comp_id + label
    retourne label voieK ou None
    """
    h, w = cc_labels.shape[:2]
    x = int(np.clip(x, 0, w - 1))
    y = int(np.clip(y, 0, h - 1))

    comp_id = int(cc_labels[y, x])
    if comp_id == 0:
        return None

    for r in rails_list:
        if r["comp_id"] == comp_id:
            return r["label"]
    return None

def overlay_mask(frame, mask_bin):
    overlay = frame.copy()
    overlay[mask_bin > 0] = (0, 255, 0)
    return cv2.addWeighted(frame, 0.65, overlay, 0.35, 0)

def draw_box(img, bbox, text, color=(0, 255, 255), thickness=2):
    x1, y1, x2, y2 = map(int, bbox)
    cv2.rectangle(img, (x1, y1), (x2, y2), color, thickness)
    cv2.putText(img, text, (x1, max(25, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, color, 2)

def draw_rail_bbox(img, rail):
    x1, y1, x2, y2 = rail["bbox"]
    cv2.rectangle(img, (x1, y1), (x2, y2), (255, 255, 255), 2)
    cv2.putText(img, rail["label"], (x1, max(25, y1 - 8)),
                cv2.FONT_HERSHEY_SIMPLEX, 0.7, (255, 255, 255), 2)


# -----------------------------
# MAIN
# -----------------------------
def main():
    trains_model = YOLO(TRAINS_MODEL)
    rails_model = YOLO(RAILS_MODEL)

    cap = cv2.VideoCapture(SOURCE_VIDEO)
    if not cap.isOpened():
        raise RuntimeError(f"Impossible d'ouvrir la vidéo: {SOURCE_VIDEO}")

    fps = cap.get(cv2.CAP_PROP_FPS) or 25.0
    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    Path(OUT_VIDEO).parent.mkdir(parents=True, exist_ok=True)
    writer = cv2.VideoWriter(OUT_VIDEO, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))

    Path(OUT_JSONL).parent.mkdir(parents=True, exist_ok=True)
    fjson = open(OUT_JSONL, "w", encoding="utf-8")

    frame_idx = 0
    print("🚀 MODELS")
    print("  trains:", TRAINS_MODEL)
    print("  rails :", RAILS_MODEL)
    print("🎥 SOURCE:", SOURCE_VIDEO)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        # -----------------------------
        # 1) RAILS segmentation -> mask_bin
        # -----------------------------
        rr = rails_model.predict(frame, imgsz=IMGSZ_RAILS, conf=CONF_RAILS, verbose=False)[0]
        mask_bin = np.zeros((h, w), dtype=np.uint8)

        if rr.masks is not None and rr.masks.data is not None:
            masks = rr.masks.data.cpu().numpy()  # (n, mh, mw)
            for m in masks:
                m_resized = cv2.resize(m, (w, h), interpolation=cv2.INTER_NEAREST)
                mask_bin[m_resized > MASK_THRESH] = 255

        rails_list, cc_labels = connected_components_rails(mask_bin, expected=EXPECTED_RAILS, min_area=MIN_AREA_RAIL)

        # -----------------------------
        # 2) TRAINS detect + track
        # -----------------------------
        tr = trains_model.track(
            frame,
            imgsz=IMGSZ_TRAINS,
            conf=CONF_TRAINS,
            iou=IOU_TRAINS,
            tracker=TRACKER,
            persist=True,
            verbose=False
        )[0]

        trains = []
        if tr.boxes is not None and len(tr.boxes) > 0:
            xyxy = tr.boxes.xyxy.cpu().numpy()
            confs = tr.boxes.conf.cpu().numpy()
            track_ids = None
            if getattr(tr.boxes, "id", None) is not None:
                track_ids = tr.boxes.id.cpu().numpy().astype(int)

            for i in range(len(xyxy)):
                bbox = xyxy[i].tolist()
                tid = int(track_ids[i]) if track_ids is not None else None

                # point bas-centre
                x1, y1, x2, y2 = bbox
                px = (x1 + x2) / 2.0
                py = y2 - POINT_OFFSET_PX

                voie = find_rail_for_point(cc_labels, rails_list, px, py)

                trains.append({
                    "bbox": bbox,
                    "conf": float(confs[i]),
                    "track_id": tid,
                    "point": [float(px), float(py)],
                    "voie": voie
                })

        # numérotation gauche->droite train1..train6
        trains_ranked = rank_left_to_right(
            trains,
            key_fn=lambda d: bbox_center_x(d["bbox"]),
            max_slots=EXPECTED_RAILS,  # souvent 6
            label_prefix="train"
        )

        # -----------------------------
        # 3) Overlay
        # -----------------------------
        out = overlay_mask(frame, mask_bin)

        # rails bbox + labels
        for r in rails_list:
            draw_rail_bbox(out, r)

        # trains bbox + association voie
        for t in trains_ranked:
            tid = t["track_id"]
            voie = t["voie"] if t["voie"] is not None else "aucune"
            txt = f"{t['lr_label']} id={tid} conf={t['conf']:.2f} -> {voie}"
            draw_box(out, t["bbox"], txt)

            # point bas-centre
            px, py = map(int, t["point"])
            cv2.circle(out, (px, py), 4, (0, 0, 255), -1)

        writer.write(out)

        # -----------------------------
        # 4) JSONL per frame
        # -----------------------------
        payload = {
            "frame": frame_idx,
            "rails_detected": len(rails_list),
            "rails": [
                {"rank": r["rank"], "label": r["label"], "bbox": r["bbox"], "cx": r["cx"], "area": r["area"]}
                for r in rails_list
            ],
            "trains_detected": len(trains_ranked),
            "trains": trains_ranked
        }
        fjson.write(json.dumps(payload, ensure_ascii=False) + "\n")

        frame_idx += 1
        if frame_idx % 50 == 0:
            print(f"Processed {frame_idx} frames...")

    cap.release()
    writer.release()
    fjson.close()
    print("✅ Done.")
    print("📹 Overlay:", OUT_VIDEO)
    print("🧾 JSONL :", OUT_JSONL)


if __name__ == "__main__":
    main()
