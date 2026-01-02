
# Smart Yard – Pipeline Unifié M1_M2_M3

Ce dépôt contient le **pipeline complet Smart Yard**, intégrant les travaux des **trois membres (M1, M2, M3)** dans une architecture **unifiée, robuste et prête pour l’intégration backend**.

Le pipeline permet, à partir d’une **vidéo de site ferroviaire**, de :

- détecter les **rails** et les **trains** (M1),
- reconnaître les **matricules des trains par OCR** (M2),
- fusionner les informations et générer des **événements temporels exploitables par un backend** (M3).

L’ensemble est orchestré par un **point d’entrée unique** : `run_pipeline.py`.

---

## 1. Architecture générale

```

M1_M2_M3/
│
├─ run_pipeline.py          # Orchestrateur global (point d’entrée)
├─ venv/                    # Environnement Python global (recommandé)
│
├─ inputs/
│  └─ videos/               # Vidéos d’entrée (source unique)
│
├─ outputs/
│  ├─ m1/                   # Sorties M1 (détection)
│  │  ├─ frames/
│  │  │  └─ trains_rails_per_frame.jsonl
│  │  └─ overlays/
│  │     └─ trains_rails_overlay.mp4
│  │
│  ├─ m2/                   # Sorties M2 (OCR)
│  │  ├─ ocr_results.json
│  │  └─ ocr_annotated.mp4
│  │
│  ├─ m3/                   # Sorties M3 (fusion & événements)
│  │  ├─ per_frame/
│  │  │  └─ occupancy_per_frame.csv
│  │  └─ events/
│  │     ├─ occupancy_events.json
│  │     ├─ occupancy_segments_with_ocr.json
│  │     └─ backend_payload.json
│  │
│  └─ backend/
│     └─ backend_payload.json   # Payload final prêt pour le backend
│
├─ M1/                       # Détection trains & rails
├─ M2/                       # OCR matricules
└─ M3/                       # Fusion & génération d’événements

````

---

## 2. Rôle de chaque module

### 🔹 Membre 1 – Détection (M1)
- Détecte les **trains** et les **rails** sur chaque frame.
- Associe chaque train à une voie par **overlap spatial**.
- Produit :
  - un fichier **JSONL par frame** (`trains_rails_per_frame.jsonl`),
  - une **vidéo annotée**.

### 🔹 Membre 2 – OCR (M2)
- Applique un **OCR** sur une région d’intérêt (ROI) de la vidéo.
- Utilise une **validation temporelle** pour stabiliser les matricules.
- Produit :
  - une liste d’événements OCR (`ocr_results.json`),
  - une vidéo annotée OCR.

### 🔹 Membre 3 – Fusion & Événements (M3)
- Fusionne les sorties M1 + M2.
- Détecte les **occupations de voies** (ARRIVAL / DEPARTURE).
- Enrichit avec les **matricules OCR**.
- Génère un **payload final backend-ready**.

---

## 3. Prérequis

### Python
- Python **3.10+** recommandé
- Un **seul environnement virtuel global** (`venv/`) est utilisé pour tout le pipeline.

### Librairies principales
- `opencv-python`
- `ultralytics`
- `numpy`
- `torch`
- `easyocr` / `pytesseract` (selon M2)
- autres dépendances internes aux modules

---

## 4. Installation

### 1️⃣ Créer l’environnement virtuel
```bash
python -m venv venv
````

### 2️⃣ Activer l’environnement

* **Windows**

```bash
venv\Scripts\activate
```

* **Linux / macOS**

```bash
source venv/bin/activate
```

### 3️⃣ Installer les dépendances

```bash
pip install -r requirements.txt
```

*(ou installer les dépendances nécessaires aux modules M1, M2, M3)*

---

## 5. Exécution du pipeline

### ▶️ Mode complet (M1 → M2 → M3)

À partir d’une vidéo source :

```bash
python run_pipeline.py inputs/videos/cam1_1.mp4
```

Ce mode :

1. copie la vidéo dans `inputs/videos/`,
2. exécute M1,
3. exécute M2,
4. exécute M3,
5. génère le payload final dans :

```
outputs/backend/backend_payload.json
```

---

### ▶️ Mode M3 uniquement (test / debug)

Permet de **tester M3 seul**, sans relancer M1 et M2.

```bash
python run_pipeline.py --m3-only
```

Ou avec chemins explicites :

```bash
python run_pipeline.py --m3-only \
  --m1-jsonl outputs/m1/frames/trains_rails_per_frame.jsonl \
  --m2-ocr outputs/m2/ocr_results.json
```

---

## 6. Format de sortie backend

Le fichier final :

```
outputs/backend/backend_payload.json
```

Contient une liste d’événements du type :

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

Ce format est **directement exploitable par un backend temps réel** (dashboard, API, monitoring).

---

## 7. Bonnes pratiques & remarques

* Toujours utiliser `inputs/videos/` comme **source unique** de vidéos.
* Toujours consommer les résultats depuis `outputs/`.
* Le pipeline est **déterministe** : une même vidéo → mêmes sorties.
* Le mode `--m3-only` est fortement recommandé pour le debug.
* Les chemins sont **absolus ou résolus depuis la racine** pour éviter toute ambiguïté.

---

## 8. Auteur & contexte

Projet réalisé dans le cadre d’un **projet Smart Yard – Vision & IA**,
avec une architecture modulaire par membres, puis **fusionnée dans un pipeline industriel unifié**.

---

## 9. Statut

✅ Pipeline fonctionnel
✅ M1, M2, M3 intégrés
✅ Backend payload prêt
🚀 Prêt pour démonstration et intégration backend
