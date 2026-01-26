# Smart Yard — M3 (Fusion + événements)

Ce module fusionne les sorties **M1** et **M2** pour produire des événements d’occupation de voies et un payload backend.

---

## 1) Entrées attendues

```
M3/inputs/from_member1/
├─ trains_rails_per_frame.jsonl
├─ trains_per_frame.jsonl
└─ rails_per_frame.jsonl

M3/inputs/from_member2/
└─ ocr_results.json
```

Le pipeline consomme surtout :

- `trains_rails_per_frame.jsonl` (M1)
- `ocr_results.json` (M2)

---

## 2) Structure utile

```
M3/
├─ configs/
├─ inputs/
├─ outputs/
│  ├─ per_frame/
│  ├─ events/
│  └─ overlays/
├─ scripts/
│  ├─ run_m3_pipeline.py
│  ├─ run_fusion_on_jsonl.py
│  ├─ make_events_from_csv.py
│  ├─ enrich_events_with_ocr.py
│  └─ export_backend_payload.py
├─ src/
│  ├─ fusion/
│  └─ api/
└─ requirements.txt
```

---

## 3) Exécution (pipeline complet M3)

```bash
python scripts/run_m3_pipeline.py ^
  --m1-jsonl ..\outputs\m1\frames\trains_rails_per_frame.jsonl ^
  --m2-ocr ..\outputs\m2\ocr_results.json ^
  --out-dir ..\outputs\m3 ^
  --camera-id cam_01 ^
  --fps 30
```

Le script orchestre :

1. fusion par frame → `outputs/m3/per_frame/occupancy_per_frame.csv`
2. événements temporels → `outputs/m3/events/occupancy_events.json`
3. enrichissement OCR → `outputs/m3/events/occupancy_segments_with_ocr.json`
4. payload backend → `outputs/m3/events/backend_payload.json`

---

## 4) Format d’événement final (extrait)

```json
{
  "event_id": "261ef9dbefde",
  "event_type": "TRACK_OCCUPANCY",
  "state": "OCCUPIED",
  "track_label": "voie2",
  "track_id": 2,
  "train_track_id": 1,
  "train_number": "40034",
  "camera_id": "cam_01",
  "arrival_frame": 0,
  "departure_frame": 230,
  "arrival_time_sec": 0.0,
  "departure_time_sec": 7.667,
  "duration_sec": 7.667
}
```


