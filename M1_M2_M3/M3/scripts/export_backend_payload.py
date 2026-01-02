import os
import json
import hashlib
from pathlib import Path
from datetime import datetime, timezone


def get_env_path(name: str) -> Path:
    v = os.environ.get(name, "")
    if not v:
        raise RuntimeError(f"Missing env var: {name}")
    return Path(v).resolve()


def short_id(*parts: str) -> str:
    h = hashlib.sha256("|".join(parts).encode("utf-8")).hexdigest()
    return h[:12]


def main():
    out_dir = get_env_path("OUT_DIR")
    segments_path = out_dir / "events" / "occupancy_segments_with_ocr.json"
    out_payload = out_dir / "events" / "backend_payload.json"

    if not segments_path.exists():
        raise FileNotFoundError(f"Missing segments file: {segments_path}")

    fps = float(os.environ.get("FPS", "30"))
    now_iso = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")

    with open(segments_path, "r", encoding="utf-8") as f:
        segments = json.load(f)

    payload = []
    for s in segments:
        track_label = s.get("track")
        train_track_id = s.get("train_track_id")
        train_number = s.get("train_number")
        camera_id = s.get("camera_id", "cam_01")
        arrival_frame = int(s.get("arrival_frame", 0))
        departure_frame = int(s.get("departure_frame", arrival_frame))

        duration_frames = max(departure_frame - arrival_frame, 0)

        arrival_time = round(arrival_frame / fps, 3)
        departure_time = round(departure_frame / fps, 3)
        duration_sec = round(duration_frames / fps, 3)

        # track_id mapping: "voie1"->1, "voie2"->2 else None
        track_id = None
        if isinstance(track_label, str) and track_label.startswith("voie"):
            try:
                track_id = int(track_label.replace("voie", ""))
            except Exception:
                track_id = None

        event_id = short_id(camera_id, str(track_label), str(train_track_id), str(arrival_frame), str(departure_frame))

        payload.append({
            "event_id": event_id,
            "event_type": "TRACK_OCCUPANCY",
            "state": "OCCUPIED",
            "track_label": track_label,
            "track_id": track_id,
            "train_track_id": train_track_id,
            "train_number": train_number,
            "camera_id": camera_id,
            "arrival_frame": arrival_frame,
            "departure_frame": departure_frame,
            "duration_frames": duration_frames,
            "arrival_time_sec": arrival_time,
            "departure_time_sec": departure_time,
            "duration_sec": duration_sec,
            "generated_at": now_iso,
            "pipeline": {
                "member": "member3",
                "version": "m3_fusion_v1",
                "fps_assumed": fps
            }
        })

    with open(out_payload, "w", encoding="utf-8") as f:
        json.dump(payload, f, ensure_ascii=False, indent=2)

    print(f"✅ Backend payload saved: {out_payload}")
    print("Nb records:", len(payload))
    if payload[:1]:
        print("Sample:", payload[0])


if __name__ == "__main__":
    main()
