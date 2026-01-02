import argparse
import os
import subprocess
import sys
from pathlib import Path


def run(cmd, cwd: Path, extra_env=None):
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)

    print("\n🟦 RUN:", " ".join(map(str, cmd)))
    subprocess.run(list(map(str, cmd)), check=True, cwd=str(cwd), env=env)


def check(path: Path, label: str):
    if not path.exists():
        raise RuntimeError(f"❌ {label} manquant: {path}")
    print(f"✅ {label} OK: {path}")


def main():
    parser = argparse.ArgumentParser(description="M3 — Fusion + événements backend")
    parser.add_argument("--m1-jsonl", required=True)
    parser.add_argument("--m2-ocr", required=True)
    parser.add_argument("--out-dir", required=True)
    parser.add_argument("--camera-id", default="cam_01")
    parser.add_argument("--fps", type=float, default=30.0)
    args = parser.parse_args()

    ROOT = Path(__file__).resolve().parent.parent  # dossier M3
    SCRIPTS = ROOT / "scripts"

    m1_jsonl = Path(args.m1_jsonl).resolve()
    m2_ocr = Path(args.m2_ocr).resolve()
    out_dir = Path(args.out_dir).resolve()

    if not m1_jsonl.exists():
        raise FileNotFoundError(f"M1 JSONL introuvable: {m1_jsonl}")
    if not m2_ocr.exists():
        raise FileNotFoundError(f"M2 OCR introuvable: {m2_ocr}")

    per_frame = out_dir / "per_frame"
    events = out_dir / "events"
    per_frame.mkdir(parents=True, exist_ok=True)
    events.mkdir(parents=True, exist_ok=True)

    # Check internal scripts
    needed = [
        SCRIPTS / "run_fusion_on_jsonl.py",
        SCRIPTS / "make_events_from_csv.py",
        SCRIPTS / "enrich_events_with_ocr.py",
        SCRIPTS / "export_backend_payload.py",
    ]
    for s in needed:
        if not s.exists():
            raise FileNotFoundError(f"Missing M3 script: {s}")

    env = {
        "PYTHONPATH": str(ROOT),
        "M1_JSONL": str(m1_jsonl),
        "M2_OCR": str(m2_ocr),
        "OUT_DIR": str(out_dir),
        "CAMERA_ID": args.camera_id,
        "FPS": str(args.fps),
    }

    print("🚀 Démarrage pipeline M3")
    print("M1 JSONL:", m1_jsonl)
    print("M2 OCR  :", m2_ocr)
    print("OUT DIR :", out_dir)

    run([sys.executable, str(SCRIPTS / "run_fusion_on_jsonl.py")], cwd=ROOT, extra_env=env)
    check(per_frame / "occupancy_per_frame.csv", "occupancy_per_frame.csv")

    run([sys.executable, str(SCRIPTS / "make_events_from_csv.py")], cwd=ROOT, extra_env=env)
    check(events / "occupancy_events.json", "occupancy_events.json")

    run([sys.executable, str(SCRIPTS / "enrich_events_with_ocr.py")], cwd=ROOT, extra_env=env)
    check(events / "occupancy_segments_with_ocr.json", "occupancy_segments_with_ocr.json")

    run([sys.executable, str(SCRIPTS / "export_backend_payload.py")], cwd=ROOT, extra_env=env)
    check(events / "backend_payload.json", "backend_payload.json")

    print("\n🎉 Pipeline M3 terminé avec succès")


if __name__ == "__main__":
    main()
