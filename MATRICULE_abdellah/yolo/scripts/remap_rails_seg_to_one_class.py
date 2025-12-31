from pathlib import Path

SRC = Path("data_rails/labels")        # labels YOLO-seg actuels
OUT = Path("data_rails/labels_1class") # sortie
OUT.mkdir(parents=True, exist_ok=True)

for f in SRC.glob("*.txt"):
    lines = f.read_text(encoding="utf-8", errors="ignore").strip().splitlines()
    new_lines = []
    for line in lines:
        parts = line.strip().split()
        if len(parts) < 7:
            continue
        parts[0] = "0"  # force classe 0
        new_lines.append(" ".join(parts))
    (OUT / f.name).write_text("\n".join(new_lines) + ("\n" if new_lines else ""), encoding="utf-8")

print("✅ Rails remappés en 1 classe ->", OUT)
