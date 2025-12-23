import json
import csv
from pathlib import Path
from collections import defaultdict

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

# Sorties "par frame"
OUT_JSONL_FRAMES = r"7_outputs/predictions/trains_rails_per_frame.jsonl"
OUT_CSV_FRAMES   = r"7_outputs/predictions/occupancy_per_frame.csv"

# Sorties "par événement" (changements voie<->train)
OUT_JSONL_EVENTS = r"7_outputs/predictions/occupancy_events.jsonl"
OUT_CSV_EVENTS   = r"7_outputs/predictions/occupancy_events.csv"

IMGSZ_TRAINS = 640
IMGSZ_RAILS  = 640
CONF_TRAINS  = 0.25
CONF_RAILS   = 0.25
IOU_TRAINS   = 0.45

TRACKER = "botsort.yaml"

EXPECTED_RAILS = 6
MIN_AREA_RAIL  = 1200     # ajuste si bruit
MASK_THRESH    = 0.5      # 0.35–0.6 selon masque
POINT_OFFSET_PX = 2       # point bas-centre = y2 - 2px


# -----------------------------
# UTILS
# -----------------------------
def bbox_center_x(b):
    x1, y1, x2, y2 = b
    return (x1 + x2) / 2.0

def rank_left_to_right(items, key_fn, max_slots=None, label_prefix=""):
    items_sorted = sorted(items, key=key_fn)
    if max_slots is not None:
        items_sorted = items_sorted[:max_slots]
    for i, it in enumerate(items_sorted, start=1):
        it["rank_lr"] = i
        it["lr_label"] = f"{label_prefix}{i}" if label_prefix else str(i)
    return items_sorted

def connected_components_rails(mask_bin, expected=6, min_area=1200):
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

    comps.sort(key=lambda c: c["cx"])

    if len(comps) > expected:
        comps = sorted(comps, key=lambda c: c["area"], reverse=True)[:expected]
        comps.sort(key=lambda c: c["cx"])

    for k, c in enumerate(comps, start=1):
        c["rank"] = k
        c["label"] = f"voie{k}"
    return comps, labels

def find_rail_for_point(cc_labels, rails_list, x, y):
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
# HISTORIQUE (EVENTS)
# -----------------------------
def open_writers():
    Path(OUT_JSONL_FRAMES).parent.mkdir(parents=True, exist_ok=True)
    Path(OUT_VIDEO).parent.mkdir(parents=True, exist_ok=True)

    f_frames = open(OUT_JSONL_FRAMES, "w", encoding="utf-8")
    f_events = open(OUT_JSONL_EVENTS, "w", encoding="utf-8")

    csv_frames = open(OUT_CSV_FRAMES, "w", newline="", encoding="utf-8")
    csv_events = open(OUT_CSV_EVENTS, "w", newline="", encoding="utf-8")

    frames_writer = csv.writer(csv_frames)
    events_writer = csv.writer(csv_events)

    # CSV headers
    frames_writer.writerow(["frame", "time_s", "voie", "occupied", "train_track_ids"])
    events_writer.writerow(["event", "track_id", "from_voie", "to_voie", "start_frame", "end_frame", "start_time_s", "end_time_s", "duration_s"])

    return f_frames, f_events, csv_frames, csv_events, frames_writer, events_writer


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

    writer = cv2.VideoWriter(OUT_VIDEO, cv2.VideoWriter_fourcc(*"mp4v"), fps, (w, h))
    f_frames, f_events, csv_frames, csv_events, frames_writer, events_writer = open_writers()

    # Mémoire d'événements par train (track_id)
    # last_voie[track_id] = voie actuelle (ou None)
    last_voie = {}
    # event_start_frame[track_id] = frame où la voie courante a commencé
    event_start_frame = {}

    frame_idx = 0
    print("🚀 MODELS")
    print("  trains:", TRAINS_MODEL)
    print("  rails :", RAILS_MODEL)
    print("🎥 SOURCE:", SOURCE_VIDEO)

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        t_s = frame_idx / float(fps)

        # 1) Rails seg -> mask_bin + rails_list
        rr = rails_model.predict(frame, imgsz=IMGSZ_RAILS, conf=CONF_RAILS, verbose=False)[0]
        mask_bin = np.zeros((h, w), dtype=np.uint8)

        if rr.masks is not None and rr.masks.data is not None:
            masks = rr.masks.data.cpu().numpy()
            for m in masks:
                m_resized = cv2.resize(m, (w, h), interpolation=cv2.INTER_NEAREST)
                mask_bin[m_resized > MASK_THRESH] = 255

        rails_list, cc_labels = connected_components_rails(mask_bin, expected=EXPECTED_RAILS, min_area=MIN_AREA_RAIL)

        # 2) Trains detect+track
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

        # Numérotation gauche->droite (train1..train6) - utile si tu en as besoin
        trains_ranked = rank_left_to_right(
            trains,
            key_fn=lambda d: bbox_center_x(d["bbox"]),
            max_slots=EXPECTED_RAILS,
            label_prefix="train"
        )

        # 3) Construire l'occupation par voie (frame)
        # occupancy_map["voie1"] = [track_id1, track_id2, ...]
        occupancy_map = {f"voie{i}": [] for i in range(1, EXPECTED_RAILS + 1)}
        for t in trains_ranked:
            if t["voie"] in occupancy_map and t["track_id"] is not None:
                occupancy_map[t["voie"]].append(t["track_id"])

        # Écrire le CSV par frame
        for voie, ids in occupancy_map.items():
            frames_writer.writerow([
                frame_idx, f"{t_s:.3f}", voie,
                1 if len(ids) > 0 else 0,
                ";".join(map(str, ids))
            ])

        # Écrire le JSONL par frame (utile backend)
        payload_frame = {
            "frame": frame_idx,
            "time_s": t_s,
            "rails_detected": len(rails_list),
            "rails": [{"rank": r["rank"], "label": r["label"], "bbox": r["bbox"]} for r in rails_list],
            "trains": trains_ranked,
            "occupancy": {voie: ids for voie, ids in occupancy_map.items()},
        }
        f_frames.write(json.dumps(payload_frame, ensure_ascii=False) + "\n")

        # 4) Générer des événements d'occupation (quand un train change de voie)
        for t in trains_ranked:
            tid = t["track_id"]
            if tid is None:
                continue

            current_voie = t["voie"]  # peut être None si pas sur rail

            if tid not in last_voie:
                # première apparition
                last_voie[tid] = current_voie
                event_start_frame[tid] = frame_idx
            else:
                prev_voie = last_voie[tid]
                if current_voie != prev_voie:
                    # on clôt l'événement précédent
                    start_f = event_start_frame.get(tid, frame_idx)
                    end_f = frame_idx - 1
                    start_t = start_f / float(fps)
                    end_t = end_f / float(fps)
                    dur = max(0.0, end_t - start_t)

                    event = {
                        "event": "voie_change",
                        "track_id": tid,
                        "from_voie": prev_voie,
                        "to_voie": current_voie,
                        "start_frame": start_f,
                        "end_frame": end_f,
                        "start_time_s": start_t,
                        "end_time_s": end_t,
                        "duration_s": dur,
                    }
                    f_events.write(json.dumps(event, ensure_ascii=False) + "\n")
                    events_writer.writerow([
                        event["event"], tid,
                        prev_voie, current_voie,
                        start_f, end_f,
                        f"{start_t:.3f}", f"{end_t:.3f}", f"{dur:.3f}"
                    ])

                    # nouveau segment
                    last_voie[tid] = current_voie
                    event_start_frame[tid] = frame_idx

        # 5) Overlay vidéo
        out = overlay_mask(frame, mask_bin)
        for r in rails_list:
            draw_rail_bbox(out, r)

        for t in trains_ranked:
            tid = t["track_id"]
            voie = t["voie"] if t["voie"] is not None else "aucune"
            txt = f"{t['lr_label']} id={tid} conf={t['conf']:.2f} -> {voie}"
            draw_box(out, t["bbox"], txt)
            px, py = map(int, t["point"])
            cv2.circle(out, (px, py), 4, (0, 0, 255), -1)

        writer.write(out)

        frame_idx += 1
        if frame_idx % 50 == 0:
            print(f"Processed {frame_idx} frames...")

    # Clôturer les événements en cours (fin vidéo)
    last_frame = frame_idx - 1
    for tid, prev_voie in last_voie.items():
        start_f = event_start_frame.get(tid, None)
        if start_f is None:
            continue
        end_f = last_frame
        start_t = start_f / float(fps)
        end_t = end_f / float(fps)
        dur = max(0.0, end_t - start_t)
        event = {
            "event": "end_of_video",
            "track_id": tid,
            "from_voie": prev_voie,
            "to_voie": None,
            "start_frame": start_f,
            "end_frame": end_f,
            "start_time_s": start_t,
            "end_time_s": end_t,
            "duration_s": dur,
        }
        f_events.write(json.dumps(event, ensure_ascii=False) + "\n")
        events_writer.writerow([
            event["event"], tid, prev_voie, None,
            start_f, end_f, f"{start_t:.3f}", f"{end_t:.3f}", f"{dur:.3f}"
        ])

    cap.release()
    writer.release()
    f_frames.close()
    f_events.close()
    csv_frames.close()
    csv_events.close()

    print("✅ Done.")
    print("📹 Overlay:", OUT_VIDEO)
    print("🧾 Frames JSONL:", OUT_JSONL_FRAMES)
    print("📊 Frames CSV  :", OUT_CSV_FRAMES)
    print("🧾 Events JSONL:", OUT_JSONL_EVENTS)
    print("📊 Events CSV  :", OUT_CSV_EVENTS)


if __name__ == "__main__":
    main()
