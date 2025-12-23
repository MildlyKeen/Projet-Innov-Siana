from pathlib import Path

SRC = Path("data_trains/labels")
OUT = Path("data_trains/labels_det")  # nouveau dossier (on ne détruit rien)
OUT.mkdir(parents=True, exist_ok=True)

def clamp(v):
    return max(0.0, min(1.0, v))

converted = 0
skipped = 0

for f in sorted(SRC.glob("*.txt")):
    text = f.read_text(encoding="utf-8", errors="ignore").strip()
    if not text:
        (OUT / f.name).write_text("", encoding="utf-8")
        skipped += 1
        continue

    out_lines = []
    for line in text.splitlines():
        parts = line.strip().split()
        if len(parts) < 7:
            # pas une ligne seg exploitable
            continue

        cls = parts[0]
        coords = list(map(float, parts[1:]))

        xs = coords[0::2]
        ys = coords[1::2]

        xmin, xmax = min(xs), max(xs)
        ymin, ymax = min(ys), max(ys)

        # bbox YOLO detect
        x_center = (xmin + xmax) / 2
        y_center = (ymin + ymax) / 2
        w = (xmax - xmin)
        h = (ymax - ymin)

        out_lines.append(
            f"{cls} {clamp(x_center):.6f} {clamp(y_center):.6f} {clamp(w):.6f} {clamp(h):.6f}"
        )

    (OUT / f.name).write_text("\n".join(out_lines) + ("\n" if out_lines else ""), encoding="utf-8")
    converted += 1

print(f"✅ Converted files: {converted}")
print(f"⚠️ Empty/skipped: {skipped}")
print(f"📁 Output labels: {OUT}")
