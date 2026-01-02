import os, json
import cv2

from src.integration.ocr_pipeline import run_ocr_pipeline, draw_result

def main():
    input_dir = "data/raw/images"
    out_img_dir = "data/processed/enhanced"
    out_json = "data/processed/ocr_results.json"

    os.makedirs(out_img_dir, exist_ok=True)

    # ROI “premier essai” (à ajuster selon tes images)
    # Ici: bande centrale sur l'avant du train (à affiner ensuite)
    # Tu vas l'ajuster après 10 tests.
    ROI = (-90, 99, 1975, 903)
  # x1,y1,x2,y2

    results = []
    for name in sorted(os.listdir(input_dir)):
        if not name.lower().endswith((".png", ".jpg", ".jpeg")):
            continue
        path = os.path.join(input_dir, name)
        frame = cv2.imread(path)
        if frame is None:
            continue

        meta = {"source": name}
        r = run_ocr_pipeline(frame, meta, ROI)
        results.append(r)

        annotated = draw_result(frame, r)
        cv2.imwrite(os.path.join(out_img_dir, name), annotated)

        print(name, "=>", r["best"])

    with open(out_json, "w", encoding="utf-8") as f:
        json.dump(results, f, ensure_ascii=False, indent=2)

    print("Saved:", out_json)

if __name__ == "__main__":
    main()
