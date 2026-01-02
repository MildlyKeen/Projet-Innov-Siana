Voici le contenu **réécrit exactement** au format **Markdown (.md)**, sans modification :



````md
# Smart Yard — Membre 3  
## Fusion spatio-temporelle voie ↔ rame et génération d’événements métier

---

## 1. Rôle du Membre 3 dans le projet Smart Yard

Le **Membre 3** est responsable de la **fusion spatio-temporelle** entre :

- les **détections de rames** issues du Membre 1 (vision / tracking),
- les **détections de voies ferroviaires** issues du Membre 1 (segmentation / détection),
- les **identifiants de rames (OCR)** produits par le Membre 2.

Son objectif est de transformer des **données brutes par frame** en **événements métier stables**, décrivant :

- quelle **voie** est occupée,
- par **quelle rame**,
- pendant **quelle durée**,
- sous un format directement exploitable par un **backend applicatif** ou un **tableau de bord**.

---

## 2. Entrées et dépendances

### 2.1 Entrées du Membre 1 (Vision & Tracking)

📁 `inputs/from_member1/`

- `trains_per_frame.jsonl`  
  → détections de trains par frame (bbox, track_id, confiance)

- `rails_per_frame.jsonl`  
  → détections de voies par frame (label voie, bbox, surface)

Ces fichiers constituent la **source de vérité spatiale**.

---

### 2.2 Entrées du Membre 2 (OCR)

📁 `inputs/from_member2/`

- `ocr_results.json`

Ce fichier contient des événements OCR **déjà stabilisés** du type :

```json
{
  "event": "TRAIN_ID_STABLE",
  "train_number": "40034",
  "frame_index": 197,
  "time_sec": 3.28,
  "camera_id": "cam_01"
}
````

👉 Le Membre 3 **ne refait pas l’OCR**, il exploite ces événements stables.

---

## 3. Structure du projet

```
member3_fusion_clean/
├─ README.md
├─ requirements.txt
├─ configs/
│  └─ fusion.yaml
├─ inputs/
│  ├─ from_member1/
│  │  ├─ rails_per_frame.jsonl
│  │  ├─ trains_per_frame.jsonl
│  │  └─ trains_rails_per_frame.jsonl
│  └─ from_member2/
│     └─ ocr_results.json
├─ src/
│  ├─ fusion/
│  │  ├─ fusion.py          # association voie ↔ rame (overlap)
│  │  ├─ overlap.py         # calcul de recouvrement métier
│  │  ├─ temporal.py        # arrivée / départ / fusion temporelle
│  │  └─ io.py              # lecture & normalisation JSONL
│  └─ api/
│     └─ app.py             # (optionnel) API interne
├─ scripts/
│  ├─ run_fusion_on_jsonl.py
│  ├─ make_events_from_csv.py
│  ├─ enrich_events_with_ocr.py
│  └─ export_backend_payload.py
├─ outputs/
│  └─ events/
│     ├─ occupancy_segments_with_ocr.json
│     └─ backend_payload.json
└─ tests/
```

---

## 4. Principe de fonctionnement

### 4.1 Association voie ↔ rame (fusion spatiale)

* Le recouvrement est calculé entre :

  * la **partie basse de la bbox du train** (roues / bogies),
  * et la bbox de la voie.
* Le ratio utilisé est :

```
intersection(bas_train, voie) / aire(bas_train)
```

Cette métrique est plus pertinente métier qu’un IoU classique.

---

### 4.2 Logique temporelle (fusion temporelle)

Les décisions ne sont **jamais prises sur une seule frame**.

Règles principales :

* une **arrivée** est déclarée après N frames consécutives (N=3),
* un **départ** est déclaré après M frames d’absence (M=8),
* une tolérance aux trous (occlusion) est appliquée,
* les segments proches sont **fusionnés**,
* les micro-occupations sont supprimées.

Résultat : des **segments d’occupation stables**.

---

### 4.3 Intégration OCR

Pour chaque segment d’occupation :

* les événements OCR `TRAIN_ID_STABLE` sont recherchés
* dans une fenêtre temporelle autour du segment,
* le numéro de rame le plus fréquent est associé.

👉 L’OCR est intégré **au niveau segment**, pas frame par frame.

---

## 5. Pipeline d’exécution

### Étape 1 — Fusion spatiale par frame

```bash
python -m scripts.run_fusion_on_jsonl
```

Produit :

* `outputs/per_frame/occupancy_per_frame.csv`

---

### Étape 2 — Événements temporels (arrivée / départ)

```bash
python -m scripts.make_events_from_csv
```

Produit :

* `outputs/events/occupancy_events.json`

---

### Étape 3 — Enrichissement OCR

```bash
python -m scripts.enrich_events_with_ocr
```

Produit :

* `outputs/events/occupancy_segments_with_ocr.json`

---

### Étape 4 — Export backend final

```bash
python -m scripts.export_backend_payload
```

Produit :

* `outputs/events/backend_payload.json`

---

## 6. Format backend final

Exemple :

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
  "duration_frames": 230,
  "arrival_time_sec": 0.0,
  "departure_time_sec": 7.667,
  "duration_sec": 7.667,
  "generated_at": "2026-01-01T22:06:00Z",
  "pipeline": {
    "member": "member3",
    "version": "m3_fusion_v1",
    "fps_assumed": 30.0
  }
}
```

Ce format est :

* stable,
* traçable,
* directement consommable par un backend ou une base de données.

---

## 7. Limites et hypothèses

* Le FPS est supposé connu (30 fps par défaut).
* Une seule caméra est considérée (extension multi-cam possible).
* Les voies sont modélisées par bboxes (masques possibles en extension).
* Les événements OCR doivent être stabilisés en amont (Membre 2).

---

## 8. Conclusion

Le module du **Membre 3** transforme des sorties IA hétérogènes en **événements métier cohérents**, robustes et exploitables.

Il constitue le **pont logique** entre :

* la vision par ordinateur,
* l’identification OCR,
* et les systèmes décisionnels en aval.

Ce livrable est prêt pour :

* intégration backend,
* démonstration,
* évaluation académique ou industrielle.


