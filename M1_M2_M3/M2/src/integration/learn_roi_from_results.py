import json

JSON_PATH = "data/processed/ocr_results.json"
MARGIN = 0.15  # 15 % de marge

def main():
    with open(JSON_PATH, "r", encoding="utf-8") as f:
        data = json.load(f)

    xs1, ys1, xs2, ys2 = [], [], [], []

    for item in data:
        best = item.get("best")
        if best is None:
            continue

        x1, y1, x2, y2 = best["bbox"]
        xs1.append(x1)
        ys1.append(y1)
        xs2.append(x2)
        ys2.append(y2)

    if not xs1:
        print("Aucun matricule valide trouvé.")
        return

    min_x1, max_x2 = min(xs1), max(xs2)
    min_y1, max_y2 = min(ys1), max(ys2)

    w = max_x2 - min_x1
    h = max_y2 - min_y1

    roi = (
        int(min_x1 - MARGIN * w),
        int(min_y1 - MARGIN * h),
        int(max_x2 + MARGIN * w),
        int(max_y2 + MARGIN * h),
    )

    print("ROI appris à partir des données :")
    print(f"ROI = {roi}")

if __name__ == "__main__":
    main()
