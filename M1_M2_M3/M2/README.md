
# Smart Yard — M2 (OCR matricules)

Module OCR du pipeline Smart Yard : lecture des matricules sur vidéo, filtrage + stabilisation temporelle, export d’événements JSON.

---

## 1) Structure utile

```
M2/
├─ data/
│  ├─ raw/
│  │  ├─ images/
│  │  └─ videos/
│  └─ processed/
│     ├─ enhanced/
│     ├─ temporal_annotated/
│     ├─ frames/
│     ├─ ocr_results.json
│     └─ ocr_events.json
├─ demos/
│  └─ ocr_demo_annotated.mp4
├─ src/
│  ├─ integration/          # run_on_images.py, run_on_video.py, ...
│  ├─ ocr/                  # moteur OCR + postprocess
│  └─ preprocessing/        # options de prétraitement
├─ tests/
└─ requirements.txt
```

---

## 2) Installation

```bash
pip install -r requirements.txt
```

---

## 3) OCR sur vidéo (commande principale)

```bash
python -m src.integration.run_on_video ^
  --root .. ^
  --video inputs/videos/cam1_1.mp4 ^
  --events-out outputs/m2/ocr_results.json ^
  --video-out outputs/m2/ocr_annotated.mp4 ^
  --camera-id cam_01 ^
  --roi -90 99 1975 903 ^
  --window 7 ^
  --min-votes 3
```

Notes :

- `--roi` attend **4 entiers** : `x1 y1 x2 y2`.
- Si `--events-out` / `--video-out` ne sont pas fournis, la sortie va par défaut dans `outputs/m2/`.

---

## 4) OCR sur images

```bash
python -m src.integration.run_on_images
```

Sorties :

- `data/processed/enhanced/`
- `data/processed/ocr_results.json`

---

## 5) ROI automatique (à partir des résultats)

```bash
python -m src.integration.learn_roi_from_results
```

Le script propose un ROI optimal à reporter ensuite dans les tests vidéo.

---

## 6) Format d’événement OCR (export)

```json
{
  "event": "TRAIN_ID_STABLE",
  "train_number": "40034",
  "frame_index": 186,
  "time_sec": 6.2,
  "camera_id": "cam_01"
}
```

Ce format est celui consommé par **M3**.


