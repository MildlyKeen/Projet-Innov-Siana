import os
import json
import time
import argparse
from pathlib import Path

import cv2

from src.integration.ocr_pipeline import run_ocr_pipeline, draw_result
from src.integration.temporal_validator import TemporalMatriculeValidator


def parse_roi(roi_str: str):
    parts = [p.strip() for p in roi_str.split(",")]
    if len(parts) != 4:
        raise ValueError("ROI must have 4 integers: x1,y1,x2,y2")
    return tuple(int(p) for p in parts)


def ensure_parent(p: Path):
    p.parent.mkdir(parents=True, exist_ok=True)


def resolve_path(p: Path, root: Path | None):
    if p.is_absolute():
        return p
    if root is not None:
        return (root / p).resolve()
    return (Path.cwd() / p).resolve()


def main():
    parser = argparse.ArgumentParser(description="M2 — OCR on video (module-friendly).")

    parser.add_argument("--root", type=str, default=os.environ.get("SMARTYARD_ROOT", ""))
    parser.add_argument("--video", type=str, default=os.environ.get("VIDEO_IN", ""))
    parser.add_argument("--events-out", type=str, default=os.environ.get("OCR_OUT", ""))
    parser.add_argument("--video-out", type=str, default=os.environ.get("VIDEO_OUT", ""))

    parser.add_argument("--camera-id", type=str, default=os.environ.get("CAMERA_ID", "cam_01"))
    parser.add_argument("--roi", nargs=4, type=int, metavar=("X1", "Y1", "X2", "Y2"), default=[-90, 99, 1975, 903],)
    parser.add_argument("--window", type=int, default=int(os.environ.get("WINDOW", "7")))
    parser.add_argument("--min-votes", type=int, default=int(os.environ.get("MIN_VOTES", "3")))
    parser.add_argument("--fallback-fps", type=float, default=float(os.environ.get("FALLBACK_FPS", "10")))
    parser.add_argument("--print-every", type=int, default=int(os.environ.get("PRINT_EVERY", "60")))

    args = parser.parse_args()

    root = Path(args.root).resolve() if args.root else None
    if not args.video:
        raise RuntimeError("Missing --video (or VIDEO_IN env var).")

    video_in = resolve_path(Path(args.video), root)

    events_out = resolve_path(Path(args.events_out), root) if args.events_out else resolve_path(Path("outputs/m2/ocr_results.json"), root)
    video_out = resolve_path(Path(args.video_out), root) if args.video_out else resolve_path(Path("outputs/m2/ocr_annotated.mp4"), root)

    ROI = tuple(args.roi)

    ensure_parent(events_out)
    ensure_parent(video_out)

    cap = cv2.VideoCapture(str(video_in))
    if not cap.isOpened():
        raise RuntimeError(
            "Impossible d'ouvrir la vidéo.\n"
            f"- video_in: {video_in}\n"
            f"- exists?: {video_in.exists()}\n"
            f"- cwd: {Path.cwd()}\n"
            "➡️ Fix: pass an ABSOLUTE path to --video, or use --root and a relative path."
        )

    fps = cap.get(cv2.CAP_PROP_FPS)
    if not fps or fps <= 0:
        fps = args.fallback_fps

    w = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    h = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))

    writer = cv2.VideoWriter(
        str(video_out),
        cv2.VideoWriter_fourcc(*"mp4v"),
        float(fps),
        (w, h)
    )
    if not writer.isOpened():
        cap.release()
        raise RuntimeError(f"Impossible d'écrire la vidéo de sortie: {video_out}")

    validator = TemporalMatriculeValidator(window=args.window, min_votes=args.min_votes)

    events = []
    last_stable_text = None
    frame_idx = 0
    t0 = time.time()

    while True:
        ret, frame = cap.read()
        if not ret:
            break

        result = run_ocr_pipeline(frame, {"frame_index": frame_idx}, ROI)
        validator.update(result.get("best"))
        stable = validator.get_stable()

        annotated = draw_result(frame, result)

        if stable and isinstance(stable, dict) and "text" in stable:
            txt = str(stable["text"])
            cv2.putText(annotated, f"STABLE: {txt}", (30, 60),
                        cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)

            if txt != last_stable_text:
                events.append({
                    "event": "TRAIN_ID_STABLE",
                    "train_number": txt,
                    "frame_index": frame_idx,
                    "time_sec": round(frame_idx / float(fps), 3),
                    "camera_id": args.camera_id
                })
                last_stable_text = txt

        writer.write(annotated)

        if args.print_every > 0 and frame_idx % args.print_every == 0:
            print(f"[{frame_idx}] best={result.get('best')} stable={stable}")

        frame_idx += 1

    cap.release()
    writer.release()

    with open(events_out, "w", encoding="utf-8") as f:
        json.dump(events, f, ensure_ascii=False, indent=2)

    print(f"✅ Video saved: {video_out}")
    print(f"✅ Events saved: {events_out}")
    print(f"Frames: {frame_idx} | FPS: {fps:.2f} | Time: {time.time() - t0:.1f}s")


if __name__ == "__main__":
    main()
