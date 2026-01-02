import os
import csv
import json
from pathlib import Path


def get_env_path(name: str) -> Path:
    v = os.environ.get(name, "")
    if not v:
        raise RuntimeError(f"Missing env var: {name}")
    return Path(v).resolve()


def main():
    out_dir = get_env_path("OUT_DIR")
    per_frame_csv = out_dir / "per_frame" / "occupancy_per_frame.csv"
    events_dir = out_dir / "events"
    events_dir.mkdir(parents=True, exist_ok=True)

    if not per_frame_csv.exists():
        raise FileNotFoundError(f"Missing per-frame CSV: {per_frame_csv}")

    # Simple temporal smoothing: require same assigned_track for N consecutive frames
    N = int(os.environ.get("EVENT_N_CONSEC", "3"))

    # Load rows
    rows = []
    with open(per_frame_csv, "r", encoding="utf-8") as f:
        r = csv.DictReader(f)
        for row in r:
            # normalize frame as int
            row["frame"] = int(row["frame"])
            # empty assigned becomes ""
            row["assigned_track"] = row.get("assigned_track", "") or ""
            # train id
            row["train_track_id"] = int(row["train_track_id"]) if row.get("train_track_id") not in ("", None) else None
            rows.append(row)

    # Group by train_track_id (simple MVP)
    events = []

    def emit_segment(track_label, train_id, start_frame, end_frame):
        # ARRIVAL near start (after N-1 frames)
        arrival_frame = start_frame + (N - 1)
        departure_frame = end_frame
        events.append({
            "event": "ARRIVAL",
            "state": "occupée",
            "track": track_label,
            "train_track_id": train_id,
            "start_frame": start_frame,
            "frame": arrival_frame
        })
        events.append({
            "event": "DEPARTURE",
            "state": "libre",
            "track": track_label,
            "train_track_id": train_id,
            "end_frame": end_frame,
            "frame": departure_frame
        })

    # Build segments per train
    by_train = {}
    for row in rows:
        tid = row["train_track_id"]
        if tid is None:
            continue
        by_train.setdefault(tid, []).append(row)

    for tid, tr_rows in by_train.items():
        tr_rows.sort(key=lambda x: x["frame"])

        # Build stable segments where assigned_track is constant for >= N frames
        current_track = None
        current_start = None
        count = 0
        last_frame = None

        def close_segment(end_frame):
            nonlocal current_track, current_start, count
            if current_track and current_start is not None and count >= N:
                emit_segment(current_track, tid, current_start, end_frame)

        for row in tr_rows:
            f = row["frame"]
            track = row["assigned_track"]

            if track == "":
                # treat as no assignment; close if we had a segment
                if current_track is not None:
                    close_segment(last_frame if last_frame is not None else f)
                current_track = None
                current_start = None
                count = 0
                last_frame = f
                continue

            if current_track is None:
                current_track = track
                current_start = f
                count = 1
            else:
                if track == current_track and (last_frame is None or f == last_frame + 1):
                    count += 1
                else:
                    # segment break
                    close_segment(last_frame if last_frame is not None else f)
                    current_track = track
                    current_start = f
                    count = 1

            last_frame = f

        # close last
        if current_track is not None and last_frame is not None:
            close_segment(last_frame)

    out_json = events_dir / "occupancy_events.json"
    out_jsonl = events_dir / "occupancy_events.jsonl"

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

    with open(out_jsonl, "w", encoding="utf-8") as f:
        for e in events:
            f.write(json.dumps(e, ensure_ascii=False) + "\n")

    print(f"✅ Events JSONL: {out_jsonl}")
    print(f"✅ Events JSON : {out_json}")
    print("Nb events:", len(events))
    if events[:5]:
        print("Sample:", events[:5])


if __name__ == "__main__":
    main()
