
# Smart Yard — Pipeline unifié (M1_M2_M3_with_backend)

Ce dépôt regroupe le pipeline complet **Smart Yard** : détection rails + trains (M1), OCR des matricules (M2), fusion spatio‑temporelle et génération d’événements backend (M3).  
Point d’entrée unique : `run_pipeline.py`.

---

## 1) Structure du dépôt (vue utile)

```
M1_M2_M3_with_backend/
├─ run_pipeline.py          # Orchestrateur global
├─ requirements.txt         # (vide) -> utilisez les requirements des modules
├─ inputs/
│  └─ videos/               # Vidéos sources (staging)
├─ outputs/
│  ├─ m1/                   # Sorties M1 (JSONL + overlay)
│  ├─ m2/                   # Sorties M2 (OCR JSON + overlay)
│  ├─ m3/                   # Sorties M3 (CSV + JSON events)
│  └─ backend/              # Payload final backend
├─ M1/                      # Détection rails/trains + modèles
├─ M2/                      # OCR + stabilisation temporelle
└─ M3/                      # Fusion + événements
```

---

## 2) Rôle des modules

- **M1** : détecte rails + trains par frame, assigne une voie, exporte un JSONL + une vidéo overlay.
- **M2** : OCR sur ROI + stabilisation temporelle, exporte un JSON d’événements OCR + vidéo annotée.
- **M3** : fusionne M1/M2, génère événements d’occupation + payload backend.

---

## 3) Prérequis

- **Python 3.10+** recommandé.
- Les dépendances sont gérées par module :
  - `M1/requirements.txt`
  - `M2/requirements.txt`
  - `M3/requirements.txt` (actuellement vide)

---

## 4) Installation rapide

```bash
python -m venv venv
venv\Scripts\activate   # Windows
# source venv/bin/activate  # Linux/macOS

pip install -r M1/requirements.txt
pip install -r M2/requirements.txt
```

---

## 5) Exécuter le pipeline

### Mode complet (M1 → M2 → M3)

```bash
python run_pipeline.py inputs/videos/cam1_1.mp4
```

Ce mode :
1. stage la vidéo dans `inputs/videos/`,
2. exécute M1,
3. exécute M2,
4. exécute M3,
5. copie le payload final dans `outputs/backend/backend_payload.json`.

### Mode M3 uniquement (debug / relance)

```bash
python run_pipeline.py --m3-only
```

Ou en explicitant les chemins :

```bash
python run_pipeline.py --m3-only ^
  --m1-jsonl outputs/m1/frames/trains_rails_per_frame.jsonl ^
  --m2-ocr outputs/m2/ocr_results.json
```

Options utiles :

- `--camera-id cam_01`
- `--fps 30`
- `--conf 0.4`

---

## 6) Sorties principales

```
outputs/m1/frames/trains_rails_per_frame.jsonl
outputs/m1/overlays/trains_rails_overlay.mp4
outputs/m2/ocr_results.json
outputs/m2/ocr_annotated.mp4
outputs/m3/per_frame/occupancy_per_frame.csv
outputs/m3/events/occupancy_events.json
outputs/m3/events/occupancy_segments_with_ocr.json
outputs/m3/events/backend_payload.json
outputs/backend/backend_payload.json
```

---

## 7) Notes d’usage

- Utiliser `inputs/videos/` comme source vidéo unique (le pipeline peut copier la vidéo si besoin).
- Les chemins sont résolus depuis la racine du dépôt.
- Pour rejouer uniquement la fusion, utilisez `--m3-only`.
