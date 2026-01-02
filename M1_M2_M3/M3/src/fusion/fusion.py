from src.fusion.io import load_rails_per_frame, load_trains_per_frame
from src.fusion.overlap import overlap_bottom_train_covered_by_rail


def assign_track_to_train(train, rails, threshold=0.70):
    """
    rails: list of {"label","bbox",...}
    Retourne:
      - (label, best_overlap) si >= threshold
      - (None, best_overlap) sinon
    """
    best_label = None
    best_ov = 0.0

    for r in rails:
        ov = overlap_bottom_train_covered_by_rail(train["bbox"], r["bbox"], bottom_frac=0.35)
        if ov > best_ov:
            best_ov = ov
            best_label = r.get("label")

    if best_ov >= threshold:
        return best_label, best_ov
    return None, best_ov

def fuse(trains_jsonl, rails_jsonl, threshold=0.70):
    rails_by_frame = load_rails_per_frame(rails_jsonl)
    trains_by_frame = load_trains_per_frame(trains_jsonl)

    results = []  # per-frame association

    frames = sorted(set(rails_by_frame.keys()) | set(trains_by_frame.keys()))
    for frame in frames:
        rails = rails_by_frame.get(frame, [])
        trains = trains_by_frame.get(frame, [])

        for t in trains:
            label, ov = assign_track_to_train(t, rails, threshold=threshold)
            results.append({
                "frame": frame,
                "track_id": t.get("track_id"),
                "train_bbox": t.get("bbox"),
                "train_conf": t.get("conf"),
                "assigned_track": label,   # ex "voie1"
                "overlap": round(float(ov), 4),
            })
    return results
