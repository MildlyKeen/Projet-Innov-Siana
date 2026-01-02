import argparse
import json
from pathlib import Path

import cv2
import numpy as np
from ultralytics import YOLO


def ensure_parent(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)


def to_py(x):
    if isinstance(x, (np.floating,)):
        return float(x)
    if isinstance(x, (np.integer,)):
        return int(x)
    if isinstance(x, (np.ndarray,)):
        return x.tolist()
    return x


def json_safe(obj):
    if isinstance(obj, dict):
        return {k: json_safe(v) for k, v in obj.items()}
    if isinstance(obj, list):
        return [json_safe(v) for v in obj]
    return to_py(obj)


def overlap_ratio(train_bbox, rail_bbox):
    tx1, ty1, tx2, ty2 = train_bbox
    rx1, ry1, rx2, ry2 = rail_bbox

    ix1 = max(tx1, rx1)
    iy1 = max(ty1, ry1)
    ix2 = min(tx2, rx2)
    iy2 = min(ty2, ry2)

    if ix2 <= ix1 or iy2 <= iy1:
        return 0.0

    inter = (ix2 - ix1) * (iy2 - iy1)
    train_area = max((tx2 - tx1) * (ty2 - ty1), 1.0)
    return float(inter / train_area)


def main():
    parser = argparse.ArgumentParser("M1 – Train & Rail detection")
    parser.add_argument("--video", required=True)
    parser.add_argument("--out-jsonl", required=True)
    parser.add_argument("--out-overlay", required=True)
    parser.add_argument("--trains-model", default="models/trains/best.pt")
    parser.add_argument("--rails-model", default="models/rails/best.pt")
    parser.add_argument("--conf", type=float, default=0.4)
    args = parser.parse_args()

    video_in = Path(args.video)
    out_jsonl = Path(args.out_jsonl)
    out_overlay = Path(args.out_overlay)
    ensure_parent(out_jsonl)
    ensure_parent(out_overlay)

    trains_model_path = Path(args.trains_model)
    rails_model_path = Path(args.rails_model)
    if not trains_model_path.exists():
        raise FileNotFoundError(f"Train model not found: {trains_model_path.resolve()}")
    if not rails_model_path.exists():
        raise FileNotFoundError(f"Rail model not found: {rails_model_path.resolve()}")

    trains_model = YOLO(str(trains_model_path))
    rails_model = YOLO(str(rails_model_path))

    cap = cv2.VideoCapture(str(video_in))
    if not cap.isOpened():
        raise RuntimeError(f"Cannot open video: {video_in.resolve()}")

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = 30.0

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    writer = cv2.VideoWriter(
        str(out_overlay),
        cv2.VideoWriter_fourcc(*"mp4v"),
        float(fps),
        (w, h),
    )
    if not writer.isOpened():
        cap.release()
        raise RuntimeError(f"Cannot open VideoWriter: {out_overlay.resolve()}")

    frame_idx = 0

    with open(out_jsonl, "w", encoding="utf-8") as f_out:
        while True:
            ret, frame = cap.read()
            if not ret:
                break

            rails_res = rails_model(frame, conf=args.conf, verbose=False)[0]
            rails = []
            for i, b in enumerate(rails_res.boxes.xyxy.cpu().numpy()):
                b = b.astype(float)
                rails.append({
                    "id": i + 1,
                    "label": f"voie{i+1}",
                    "bbox": b.tolist(),
                })
                cv2.rectangle(frame, (int(b[0]), int(b[1])), (int(b[2]), int(b[3])), (255, 0, 0), 2)

            trains_res = trains_model.track(frame, conf=args.conf, persist=True, verbose=False)[0]
            trains = []
            if trains_res.boxes.id is not None:
                boxes = trains_res.boxes.xyxy.cpu().numpy()
                tids = trains_res.boxes.id.cpu().numpy()
                confs = trains_res.boxes.conf.cpu().numpy()

                for box, tid, c in zip(boxes, tids, confs):
                    box = box.astype(float)
                    best_track = None
                    best_overlap = 0.0
                    for r in rails:
                        o = overlap_ratio(box, r["bbox"])
                        if o > best_overlap:
                            best_overlap = o
                            best_track = r["label"]

                    trains.append({
                        "track_id": int(tid),
                        "bbox": box.tolist(),
                        "confidence": float(c),
                        "assigned_track": best_track,
                        "overlap": round(float(best_overlap), 4),
                    })

                    cv2.rectangle(frame, (int(box[0]), int(box[1])), (int(box[2]), int(box[3])), (0, 255, 0), 2)

            record = {
                "frame": frame_idx,
                "time_sec": round(frame_idx / float(fps), 3),
                "rails": rails,
                "trains": trains,
            }

            f_out.write(json.dumps(json_safe(record), ensure_ascii=False) + "\n")
            writer.write(frame)

            frame_idx += 1
            if frame_idx % 100 == 0:
                print(f"Processed {frame_idx} frames...")

    cap.release()
    writer.release()

    print("✅ Done.")
    print("🧾 Frames JSONL:", out_jsonl.resolve())
    print("📹 Overlay:", out_overlay.resolve())


if __name__ == "__main__":
    main()
