import json

def read_jsonl(path):
    with open(path, "r", encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            yield json.loads(line)

def load_rails_per_frame(path):
    """
    Retour: dict frame_idx -> list of rails
    rail = {"label":..., "bbox":[...], "rank":..., "area":...}
    """
    out = {}
    for row in read_jsonl(path):
        frame = row["frame"]
        out[frame] = row.get("rails", [])
    return out

def load_trains_per_frame(path):
    """
    Retour: dict frame_idx -> list of trains
    train = {"track_id":..., "bbox":[...], "conf":...}
    """
    out = {}
    for row in read_jsonl(path):
        frame = row["frame"]
        out[frame] = row.get("trains", [])
    return out
