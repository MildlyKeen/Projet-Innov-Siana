import os
import json
from pathlib import Path
import csv


def get_env_path(name: str) -> Path:
    v = os.environ.get(name, "")
    if not v:
        raise RuntimeError(f"Missing env var: {name}")
    return Path(v).resolve()


def read_jsonl(path: Path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if line:
                yield json.loads(line)


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
    return inter / train_area


def main():
    m1_jsonl = get_env_path("M1_JSONL")
    out_dir = get_env_path("OUT_DIR")
    per_frame_dir = out_dir / "per_frame"
    per_frame_dir.mkdir(parents=True, exist_ok=True)

    out_csv = per_frame_dir / "occupancy_per_frame.csv"

    rows = []
    for rec in read_jsonl(m1_jsonl):
        frame = int(rec.get("frame", -1))
        rails = rec.get("rails", []) or []
        trains = rec.get("trains", []) or []

        # For each train instance, decide assigned track:
        for t in trains:
            tid = t.get("track_id")
            bbox = t.get("bbox")
            conf = t.get("confidence")
            assigned = t.get("assigned_track", None)
            ov = t.get("overlap", None)

            # If M1 didn't assign (or assigned None), compute quickly here
            if (assigned is None or ov is None) and bbox and rails:
                best_track = None
                best_ov = 0.0
                for r in rails:
                    rb = r.get("bbox")
                    lbl = r.get("label")
                    if rb and lbl:
                        o = overlap_ratio(bbox, rb)
                        if o > best_ov:
                            best_ov = o
                            best_track = lbl
                assigned = best_track
                ov = round(best_ov, 4)

            rows.append({
                "frame": frame,
                "train_track_id": int(tid) if tid is not None else "",
                "train_conf": float(conf) if conf is not None else "",
                "train_bbox": json.dumps(bbox, ensure_ascii=False) if bbox is not None else "",
                "assigned_track": assigned if assigned is not None else "",
                "overlap": float(ov) if ov is not None else "",
            })

    # Write CSV
    with open(out_csv, "w", newline="", encoding="utf-8") as f:
        w = csv.DictWriter(
            f,
            fieldnames=["frame", "train_track_id", "train_conf", "train_bbox", "assigned_track", "overlap"],
        )
        w.writeheader()
        for r in rows:
            w.writerow(r)

    print(f"✅ Wrote: {out_csv}")
    if rows[:5]:
        print("Sample:", rows[:5])


if __name__ == "__main__":
    main()
