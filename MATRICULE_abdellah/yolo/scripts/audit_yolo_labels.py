from pathlib import Path

LBL_DIR = Path("data_trains/labels")
MAX_SHOW = 5

def is_seg_line(parts):
    # seg: class + au moins 6 coords (3 points => 6 nombres) => len >= 1+6 = 7
    return len(parts) >= 7

def is_det_line(parts):
    # detect: class x y w h => len == 5
    return len(parts) == 5

seg_files = 0
det_files = 0
mixed_files = 0
empty_files = 0

examples_seg = []
examples_det = []

for f in sorted(LBL_DIR.glob("*.txt")):
    text = f.read_text(encoding="utf-8", errors="ignore").strip()
    if not text:
        empty_files += 1
        continue

    has_seg = False
    has_det = False

    for line in text.splitlines():
        parts = line.strip().split()
        if len(parts) < 2:
            continue
        if is_det_line(parts):
            has_det = True
        if is_seg_line(parts):
            has_seg = True

    if has_seg and not has_det:
        seg_files += 1
        if len(examples_seg) < MAX_SHOW:
            examples_seg.append(f.name)
    elif has_det and not has_seg:
        det_files += 1
        if len(examples_det) < MAX_SHOW:
            examples_det.append(f.name)
    else:
        mixed_files += 1

total = seg_files + det_files + mixed_files + empty_files
print(f"Total labels: {total}")
print(f"Seg-only    : {seg_files} (ex: {examples_seg})")
print(f"Det-only    : {det_files} (ex: {examples_det})")
print(f"Mixed       : {mixed_files}")
print(f"Empty       : {empty_files}")
