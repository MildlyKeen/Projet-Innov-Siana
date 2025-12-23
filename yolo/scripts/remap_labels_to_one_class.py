from pathlib import Path

SRC = Path("data_trains/labels_det")  # tes labels bbox (après conversion seg->bbox)
OUT = Path("data_trains/labels_1class")
OUT.mkdir(parents=True, exist_ok=True)

for f in SRC.glob("*.txt"):
    lines = f.read_text(encoding="utf-8", errors="ignore").strip().splitlines()
    new_lines = []
    for line in lines:
        parts = line.strip().split()
        if len(parts) != 5:
            continue
        # force class -> 0
        parts[0] = "0"
        new_lines.append(" ".join(parts))
    (OUT / f.name).write_text("\n".join(new_lines) + ("\n" if new_lines else ""), encoding="utf-8")

print("✅ Remap terminé ->", OUT)
