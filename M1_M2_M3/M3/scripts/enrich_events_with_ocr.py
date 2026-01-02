import os
import json
from pathlib import Path


def get_env_path(name: str) -> Path:
    v = os.environ.get(name, "")
    if not v:
        raise RuntimeError(f"Missing env var: {name}")
    return Path(v).resolve()


def main():
    out_dir = get_env_path("OUT_DIR")
    m2_ocr = get_env_path("M2_OCR")

    events_json = out_dir / "events" / "occupancy_events.json"
    out_segments = out_dir / "events" / "occupancy_segments_with_ocr.json"

    if not events_json.exists():
        raise FileNotFoundError(f"Missing events file: {events_json}")
    if not m2_ocr.exists():
        raise FileNotFoundError(f"Missing OCR file: {m2_ocr}")

    camera_id = os.environ.get("CAMERA_ID", "cam_01")

    # Load OCR stable events (list of {frame_index, train_number})
    with open(m2_ocr, "r", encoding="utf-8") as f:
        ocr_events = json.load(f)

    # Build an index: for each frame, best train_number (simple)
    # We will use last-known train_number when within [arrival, departure].
    ocr_events_sorted = sorted(ocr_events, key=lambda x: x.get("frame_index", 0))

    def number_in_interval(start_f, end_f):
        best = None
        for e in ocr_events_sorted:
            fi = e.get("frame_index", -1)
            if fi < start_f:
                continue
            if fi > end_f:
                break
            best = e.get("train_number") or best
        return best

    with open(events_json, "r", encoding="utf-8") as f:
        events = json.load(f)

    # Convert ARRIVAL/DEPARTURE pairs -> segments
    segments = []
    # naive: pair by (track, train_track_id) in sequence
    pending = {}
    for e in events:
        key = (e.get("track"), e.get("train_track_id"))
        if e.get("event") == "ARRIVAL":
            pending[key] = e
        elif e.get("event") == "DEPARTURE" and key in pending:
            arr = pending.pop(key)
            start_frame = int(arr.get("start_frame", arr.get("frame", 0)))
            end_frame = int(e.get("end_frame", e.get("frame", start_frame)))

            train_number = number_in_interval(start_frame, end_frame)

            segments.append({
                "track": arr.get("track"),
                "train_track_id": arr.get("train_track_id"),
                "train_number": train_number,
                "arrival_frame": start_frame,
                "departure_frame": end_frame,
                "camera_id": camera_id,
            })

    with open(out_segments, "w", encoding="utf-8") as f:
        json.dump(segments, f, ensure_ascii=False, indent=2)

    print(f"✅ Final segments with OCR: {out_segments}")
    print("Nb segments:", len(segments))
    if segments[:1]:
        print("Sample:", segments[0])


if __name__ == "__main__":
    main()
