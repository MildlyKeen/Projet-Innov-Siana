import os
import cv2

from src.integration.ocr_pipeline import run_ocr_pipeline, draw_result
from src.integration.temporal_validator import TemporalMatriculeValidator

def main():
    input_dir = "data/raw/images"
    out_dir = "data/processed/temporal_annotated"
    os.makedirs(out_dir, exist_ok=True)

    
    video_out = "demos/ocr_demo_annotated.mp4"
    os.makedirs("demos", exist_ok=True)

    fourcc = cv2.VideoWriter_fourcc(*"mp4v")
    fps = 10  # tu peux mettre 15 si tu veux
    writer = None

    # ✅ Mets ici TON ROI optimal (celui que tu as appris)
    ROI = (-90, 99, 1975, 903)  # <-- remplace par ton ROI optimal

    # ✅ Fenêtre temporelle: 5 images, au moins 2 votes (pondérés)
    validator = TemporalMatriculeValidator(window=5, min_votes=2)

    images = sorted([f for f in os.listdir(input_dir) if f.lower().endswith((".png",".jpg",".jpeg"))])

    last_stable = None

    for i, name in enumerate(images):
        path = os.path.join(input_dir, name)
        frame = cv2.imread(path)
        if frame is None:
            continue

        meta = {"source": name, "frame_index": i}
        result = run_ocr_pipeline(frame, meta, ROI)

        # best = dict ou None
        validator.update(result["best"])
        stable = validator.get_stable()

        # Affichage console clair
        print(f"[{i:04d}] {name} | best={result['best']} | stable={stable}")

        # Annoter image et écrire "stable" dessus si présent
        annotated = draw_result(frame, result)

        if stable:
            text = f"STABLE: {stable['text']} (score={stable['score']})"
            cv2.putText(annotated, text, (30, 60), cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 0, 255), 3)

        # init writer une seule fois avec la taille de la 1ère frame
        if writer is None:
            h, w = annotated.shape[:2]
            writer = cv2.VideoWriter(video_out, fourcc, fps, (w, h))

        writer.write(annotated)

        cv2.imwrite(os.path.join(out_dir, name), annotated)

        # Optionnel : éviter d’imprimer le même stable 50 fois
        if stable and stable != last_stable:
            print("✅ MATRICULE CONFIRME:", stable)
            last_stable = stable

        if writer is not None:
            writer.release()
        print("✅ Video saved:", video_out)

    print("Done. Images annotées:", out_dir)

if __name__ == "__main__":
    main()
