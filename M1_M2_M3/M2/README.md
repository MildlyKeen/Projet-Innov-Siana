

# Smart Yard – Membre 2  
## OCR & Prétraitement Vidéo pour l’identification des numéros de rames

---

## 1. Objectif du module

Ce dépôt correspond au travail du **Membre 2** du projet *Smart Yard*.  
Son objectif est d’assurer **la lecture fiable des numéros de rames ferroviaires** à partir de flux vidéo ou d’images, et de fournir une **brique OCR robuste, stable et intégrable** dans le système global.

Le module prend en entrée :
- des **images** ou des **vidéos** de trains,
- et produit en sortie :
  - des **résultats OCR filtrés et validés**,
  - des **images / vidéos annotées** pour démonstration,
  - des **événements JSON exploitables** par les autres membres (fusion IA / backend).

---

## 2. Principe général de fonctionnement

Le pipeline OCR repose sur les idées suivantes :

1. **OCR ciblé** (et non sur toute l’image brute)
2. **Réduction intelligente du bruit** grâce à un ROI (Region Of Interest)
3. **Scoring métier** pour choisir le bon numéro parmi plusieurs candidats
4. **Validation temporelle** sur plusieurs frames (vidéo)
5. **Sorties propres et explicables**

👉 L’objectif n’est pas seulement de lire du texte, mais **d’identifier un numéro de rame de manière fiable**.

---

## 3. Structure du dossier (TRÈS IMPORTANT)

```

smart-yard-member2/
│
├── data/
│   ├── raw/
│   │   ├── images/              # Images brutes (tests image par image)
│   │   └── videos/              # Vidéos brutes (tests réels)
│   │
│   ├── processed/
│   │   ├── enhanced/            # Images annotées (OCR + ROI)
│   │   ├── temporal_annotated/  # Images annotées avec validation temporelle
│   │   ├── ocr_results.json     # Résultats OCR image par image
│   │   └── ocr_events.json      # Événements métier (sortie finale)
│
├── demos/
│   └── ocr_demo_annotated.mp4   # Vidéo MP4 annotée (livrable démo)
│
├── src/
│   ├── ocr/
│   │   ├── ocr_engine.py        # Interface OCR (PaddleOCR / EasyOCR)
│   │   ├── postprocess.py       # Nettoyage des prédictions
│   │   └── regex_validation.py  # Validation structurelle (formats autorisés)
│   │
│   ├── preprocessing/
│   │   ├── contrast.py          # Ajustement contraste/luminosité (si utilisé)
│   │   ├── perspective.py       # Correction de perspective (optionnel)
│   │   └── stabilization.py     # Stabilisation (optionnel)
│   │
│   └── integration/
│       ├── ocr_pipeline.py          # Pipeline OCR principal
│       ├── temporal_validator.py    # Validation temporelle des matricules
│       ├── run_on_images.py         # Tests OCR sur images
│       ├── run_temporal_on_images.py# Simulation vidéo à partir d’images
│       ├── run_on_video.py          # Tests OCR sur vidéo réelle
│       └── learn_roi_from_results.py# Apprentissage automatique du ROI
│
├── tests/                        # (optionnel) tests unitaires
├── requirements.txt
└── README.md

````

👉 **Règle d’or** :  
- `raw/` = données d’entrée  
- `processed/` = résultats générés  
- `src/` = logique métier (aucune donnée dedans)

---

## 4. Installation et prérequis

### 4.1 Créer un environnement virtuel
```bash
python -m venv .venv
source .venv/bin/activate   # Linux/Mac
.venv\Scripts\activate      # Windows
````

### 4.2 Installer les dépendances

```bash
pip install -r requirements.txt
```

Dépendances principales :

* `opencv-python`
* `paddleocr`
* `numpy`
* `torch` (CPU suffisant)

---

## 5. Comprendre le pipeline OCR

### 5.1 OCR brut

Le moteur OCR détecte **tous les textes** visibles dans la zone analysée.

### 5.2 Filtrage structurel

On conserve uniquement :

* des chaînes numériques,
* de longueur raisonnable (ex : 3 à 5 chiffres),
* avec une confiance minimale.

### 5.3 Scoring métier

Chaque candidat reçoit un score basé sur :

* la confiance OCR,
* la taille du bounding box,
* la proximité du centre de l’image.

👉 Cela permet de **choisir le bon numéro sans forcer un format rigide**.

### 5.4 Validation temporelle

Sur une vidéo, le numéro :

* doit apparaître **plusieurs fois sur des frames consécutives**,
* avant d’être déclaré comme valide.

👉 Cela élimine les faux positifs et les erreurs ponctuelles.

---

## 6. Comment lancer des tests (GUIDE PAS À PAS)

---

### 6.1 Test OCR sur images (sans temporalité)

1. Mettre des images dans :

```
data/raw/images/
```

2. Lancer :

```bash
python -m src.integration.run_on_images
```

3. Résultats :

* images annotées → `data/processed/enhanced/`
* résultats OCR → `data/processed/ocr_results.json`

---

### 6.2 Apprendre automatiquement le ROI (recommandé)

Après les tests image :

```bash
python -m src.integration.learn_roi_from_results
```

👉 Le script affiche un ROI optimal à partir des détections réelles.
Ce ROI doit ensuite être **reporté dans les scripts de test**.

---

### 6.3 Simulation vidéo à partir d’images

Utile si on n’a pas encore de vidéo réelle.

```bash
python -m src.integration.run_temporal_on_images
```

Résultats :

* images annotées temporellement
* stabilisation du matricule visible
* possibilité de créer une vidéo MP4

---

### 6.4 Test sur vidéo réelle (RECOMMANDÉ)

1. Mettre une vidéo dans :

```
data/raw/videos/test.mp4
```

2. Lancer :

```bash
python -m src.integration.run_on_video
```

3. Résultats :

* vidéo annotée → `demos/ocr_demo_annotated.mp4`
* événements JSON → `data/processed/ocr_events.json`

---

## 7. Format de sortie (IMPORTANT POUR LA FUSION)

### 7.1 Exemple d’événement généré

```json
{
  "event": "TRAIN_ID_STABLE",
  "train_number": "40034",
  "frame_index": 186,
  "time_sec": 6.2,
  "camera_id": "cam_01"
}
```

👉 C’est **ce format** qui est transmis au module de fusion (Membre 3).

---

## 8. Bonnes pratiques & conseils

* Ne jamais décider sur **une seule frame**
* Toujours préférer :

  * validation temporelle
  * scoring explicable
* Le ROI peut être recalculé si :

  * la caméra change
  * l’angle de vue évolue
* Le module est **volontairement indépendant** :

  * pas de dépendance directe à YOLO ou segmentation

---

## 9. État du livrable (Membre 2)

✔ OCR fonctionnel
✔ Filtrage & scoring métier
✔ ROI appris automatiquement
✔ Validation temporelle
✔ Tests images & vidéos
✔ Vidéo annotée de démonstration
✔ Sortie JSON prête pour intégration

👉 Le travail du **Membre 2 est complet et prêt pour la fusion**.

---

## 10. Contact / Transmission

Ce module est conçu pour être :

* compris par un **nouvel arrivant**
* intégré sans modification lourde
* utilisé comme brique OCR indépendante

Pour la fusion :
➡️ fournir uniquement :

* `ocr_pipeline.py`
* `temporal_validator.py`
* le format d’événement JSON


