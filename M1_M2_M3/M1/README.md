
# Smart Yard — M1 (Détection rails + trains)

Ce module contient **l’inférence M1** : détection des rails et des trains par frame, attribution d’une voie, export JSONL + vidéo overlay.

---

## 1) Structure utile

```
M1/
├─ 5_inference/
│  └─ scripts/
│     ├─ infer_rails.py
│     ├─ infer_trains.py
│     └─ infer_trains_and_rails_with_history.py
├─ models/
│  ├─ rails/best.pt
│  └─ trains/best.pt
├─ 7_outputs/               # (legacy/local)
├─ 8_inputs/                # (legacy/local)
└─ requirements.txt
```

---

## 2) Prérequis

```bash
pip install -r requirements.txt
```

Modèles attendus :

- `models/trains/best.pt`
- `models/rails/best.pt`

---

## 3) Script principal (rails + trains)

```bash
python 5_inference/scripts/infer_trains_and_rails_with_history.py ^
  --video ..\inputs\videos\cam1_1.mp4 ^
  --out-jsonl ..\outputs\m1\frames\trains_rails_per_frame.jsonl ^
  --out-overlay ..\outputs\m1\overlays\trains_rails_overlay.mp4 ^
  --conf 0.4
```

Sorties :

- JSONL par frame : rails + trains + voie assignée
- MP4 overlay

---

## 4) Scripts unitaires

### Détection trains uniquement

```bash
python 5_inference/scripts/infer_trains.py --video <video> --out-jsonl <jsonl> --out-overlay <mp4>
```

### Détection rails uniquement

```bash
python 5_inference/scripts/infer_rails.py --video <video> --out-jsonl <jsonl> --out-overlay <mp4>
```

---

## 5) Format JSONL (extrait)

```json
{
  "frame": 12,
  "time_sec": 0.4,
  "rails": [
    {"id": 1, "label": "voie1", "bbox": [x1, y1, x2, y2]}
  ],
  "trains": [
    {"track_id": 3, "bbox": [x1, y1, x2, y2], "confidence": 0.87, "assigned_track": "voie2", "overlap": 0.42}
  ]
}
```
