# M1_M2_M3/run_pipeline.py
import os
import sys
import shutil
import subprocess
import argparse
from pathlib import Path


def ensure_dir(p: Path):
    p.mkdir(parents=True, exist_ok=True)


def run(cmd, cwd: Path, extra_env: dict | None = None):
    env = os.environ.copy()
    if extra_env:
        env.update(extra_env)

    print("\n🟦 RUN:", " ".join(map(str, cmd)))
    subprocess.run(list(map(str, cmd)), check=True, cwd=str(cwd), env=env)


def check_exists(p: Path, label: str):
    if not p.exists():
        raise RuntimeError(f"❌ {label} manquant: {p}")
    print(f"✅ {label} OK: {p}")


def safe_stage_copy(src: Path, dst: Path):
    """
    Copy src -> dst, but avoid WinError 32 when dst is locked by another process.
    If dst already exists, we keep it and do not overwrite.
    """
    if dst.exists():
        print(f"ℹ️ Video already staged: {dst}")
        return

    ensure_dir(dst.parent)
    try:
        shutil.copy2(src, dst)
        print(f"✅ Video staged: {dst}")
    except PermissionError as e:
        # If file is locked or being used, fall back to "do nothing" if dst exists.
        if dst.exists():
            print(f"⚠️ Cannot overwrite staged video (in use). Keeping existing: {dst}")
            return
        raise e


def preflight(ROOT: Path, PY: Path, M1: Path, M2: Path, M3: Path):
    check_exists(PY, "Python venv global")

    # --- M1 script + models
    m1_script = M1 / "5_inference" / "scripts" / "infer_trains_and_rails_with_history.py"
    check_exists(m1_script, "Script M1")

    trains_model = M1 / "models" / "trains" / "best.pt"
    rails_model = M1 / "models" / "rails" / "best.pt"
    check_exists(trains_model, "Model trains (M1/models/trains/best.pt)")
    check_exists(rails_model, "Model rails  (M1/models/rails/best.pt)")

    # --- M2 module
    check_exists(M2 / "src", "Dossier M2/src (imports)")
    check_exists(M2 / "src" / "integration" / "run_on_video.py", "M2 src/integration/run_on_video.py")

    # --- M3 scripts
    check_exists(M3 / "scripts" / "run_m3_pipeline.py", "M3 scripts/run_m3_pipeline.py")
    for s in [
        "run_fusion_on_jsonl.py",
        "make_events_from_csv.py",
        "enrich_events_with_ocr.py",
        "export_backend_payload.py",
    ]:
        check_exists(M3 / "scripts" / s, f"M3 scripts/{s}")


def main():
    parser = argparse.ArgumentParser(description="Smart Yard — Pipeline global unifié (M1 → M2 → M3)")
    parser.add_argument("video", nargs="?", default=None, help="Chemin de la vidéo (mode full pipeline).")
    parser.add_argument("--m3-only", action="store_true", help="N'exécute que M3 à partir des outputs existants M1+M2.")
    parser.add_argument("--m1-jsonl", default=None, help="Chemin vers trains_rails_per_frame.jsonl (si --m3-only).")
    parser.add_argument("--m2-ocr", default=None, help="Chemin vers ocr_results.json (si --m3-only).")
    parser.add_argument("--camera-id", default="cam_01", help="camera_id transmis à M2/M3")
    parser.add_argument("--fps", type=float, default=30.0, help="FPS assumé pour M3 (timings).")
    parser.add_argument("--conf", type=float, default=0.4, help="Seuil de confiance YOLO (M1).")
    args = parser.parse_args()

    ROOT = Path(__file__).resolve().parent

    # Global venv python
    PY = ROOT / "venv" / "Scripts" / "python.exe"

    # Members roots
    M1 = ROOT / "M1"
    M2 = ROOT / "M2"
    M3 = ROOT / "M3"

    # Unified IO
    INPUTS_VIDEOS = ROOT / "inputs" / "videos"
    OUTPUTS = ROOT / "outputs"
    ensure_dir(INPUTS_VIDEOS)
    ensure_dir(OUTPUTS)

    # Outputs folders
    out_m1_frames = OUTPUTS / "m1" / "frames"
    out_m1_overlays = OUTPUTS / "m1" / "overlays"
    out_m2 = OUTPUTS / "m2"
    out_m3 = OUTPUTS / "m3"
    out_backend = OUTPUTS / "backend"

    for p in [out_m1_frames, out_m1_overlays, out_m2, out_m3, out_backend]:
        ensure_dir(p)

    # Preflight (checks code + models + scripts)
    preflight(ROOT, PY, M1, M2, M3)

    # ------------------------------------------------------------
    # MODE: M3 ONLY (no M1, no M2)
    # ------------------------------------------------------------
    if args.m3_only:
        # Existing inputs
        m1_jsonl = Path(args.m1_jsonl).resolve() if args.m1_jsonl else (out_m1_frames / "trains_rails_per_frame.jsonl").resolve()
        m2_events_out = Path(args.m2_ocr).resolve() if args.m2_ocr else (out_m2 / "ocr_results.json").resolve()

        check_exists(m1_jsonl, "M1 output JSONL (existing)")
        check_exists(m2_events_out, "M2 OCR events JSON (existing)")

        m3_script = M3 / "scripts" / "run_m3_pipeline.py"
        check_exists(m3_script, "M3 runner")

        env_m3 = {"PYTHONPATH": str(M3)}
        run(
            [
                str(PY),
                str(m3_script),
                "--m1-jsonl", str(m1_jsonl),
                "--m2-ocr", str(m2_events_out),
                "--out-dir", str(out_m3),
                "--camera-id", args.camera_id,
                "--fps", str(args.fps),
            ],
            cwd=ROOT,
            extra_env=env_m3
        )

        m3_payload = out_m3 / "events" / "backend_payload.json"
        check_exists(m3_payload, "M3 backend payload")

        final_payload = out_backend / "backend_payload.json"
        shutil.copy2(m3_payload, final_payload)
        check_exists(final_payload, "Final backend payload")

        print("\n✅ M3-only OK.")
        print("📦 Payload backend final:", final_payload)
        return

    # ------------------------------------------------------------
    # MODE: FULL PIPELINE (M1 → M2 → M3)
    # ------------------------------------------------------------
    if not args.video:
        parser.error("video is required unless --m3-only is used")

    # Resolve input video (absolute)
    video_arg = Path(args.video)
    if not video_arg.is_absolute():
        video_arg = (ROOT / video_arg).resolve()

    if not video_arg.exists():
        raise FileNotFoundError(f"❌ Vidéo introuvable: {video_arg}")

    # Stage video into inputs/videos
    staged_video = INPUTS_VIDEOS / video_arg.name
    safe_stage_copy(video_arg, staged_video)

    print("🚀 Smart Yard — Pipeline global unifié (M1 → M2 → M3)")
    print("🎞️ Video source :", staged_video)

    # ------------------------------------------------------------
    # 1) M1 — detection rails + trains
    # ------------------------------------------------------------
    m1_script = M1 / "5_inference" / "scripts" / "infer_trains_and_rails_with_history.py"
    m1_jsonl = out_m1_frames / "trains_rails_per_frame.jsonl"
    m1_overlay = out_m1_overlays / "trains_rails_overlay.mp4"

    run(
        [
            str(PY),
            str(m1_script.relative_to(M1)),
            "--video", str(staged_video),
            "--out-jsonl", str(m1_jsonl),
            "--out-overlay", str(m1_overlay),
            "--conf", str(args.conf),
        ],
        cwd=M1,
        extra_env={"SMARTYARD_ROOT": str(ROOT)}
    )
    check_exists(m1_jsonl, "M1 output JSONL")

    # ------------------------------------------------------------
    # 2) M2 — OCR (module)
    # ------------------------------------------------------------
    m2_events_out = out_m2 / "ocr_results.json"
    m2_video_out = out_m2 / "ocr_annotated.mp4"

    env_m2 = {
        "PYTHONPATH": str(M2),      # indispensable: import src.*
        "SMARTYARD_ROOT": str(ROOT)
    }

    # IMPORTANT: ROI passed as 4 ints to avoid argparse issues with negative values
    run(
        [
            str(PY),
            "-m", "src.integration.run_on_video",
            "--root", str(ROOT),
            "--video", str(staged_video),
            "--events-out", str(m2_events_out),
            "--video-out", str(m2_video_out),
            "--camera-id", args.camera_id,
            "--roi", "-90", "99", "1975", "903",
            "--window", "7",
            "--min-votes", "3",
            "--print-every", "60",
        ],
        cwd=M2,
        extra_env=env_m2
    )
    check_exists(m2_events_out, "M2 OCR events JSON")

    # ------------------------------------------------------------
    # 3) M3 — fusion + events + backend payload
    # ------------------------------------------------------------
    m3_script = M3 / "scripts" / "run_m3_pipeline.py"
    env_m3 = {"PYTHONPATH": str(M3)}  # import src.fusion.*
    run(
        [
            str(PY),
            str(m3_script),
            "--m1-jsonl", str(m1_jsonl),
            "--m2-ocr", str(m2_events_out),
            "--out-dir", str(out_m3),
            "--camera-id", args.camera_id,
            "--fps", str(args.fps),
        ],
        cwd=ROOT,
        extra_env=env_m3
    )

    m3_payload = out_m3 / "events" / "backend_payload.json"
    check_exists(m3_payload, "M3 backend payload")

    final_payload = out_backend / "backend_payload.json"
    shutil.copy2(m3_payload, final_payload)
    check_exists(final_payload, "Final backend payload")

    print("\n🎉 PIPELINE GLOBAL TERMINÉ")
    print("📦 Payload backend final:", final_payload)
    print("📁 Outputs root:", OUTPUTS)


if __name__ == "__main__":
    main()
