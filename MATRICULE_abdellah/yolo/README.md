
# Guide de prise en main du projet **Smart Yard**

Ce notebook pédagogique présente la structure du dépôt et décrit comment utiliser les scripts fournis pour entraîner, valider et exploiter les modèles de détection et de segmentation utilisés dans le projet Smart Yard.  
Il est conçu comme un document de prise en main pour un nouveau développeur ou un évaluateur technique.


## Sommaire

1. [Structure du projet](#Structure)
2. [Rôle de chaque dossier et fichiers clés](#Roles)
3. [Préparation des données et entraînement des modèles](#Entrainement)
   - [Détection des trains](#Detection)
   - [Segmentation des voies](#Segmentation)
4. [Validation et tests](#Validation)
5. [Scripts d’inférence](#Inference)
   - [Script d’inférence des voies (rails)](#InfRails)
   - [Script d’inférence des trains](#InfTrains)
   - [Script combiné trains + rails](#InfCombi)
6. [Historique d’occupation des voies](#Historique)


## 1. Structure du projet {#Structure}

L’arborescence du dépôt est organisée pour séparer clairement les données brutes, les jeux de données préparés, les configurations, les entraînements, les modèles et les scripts d’inférence. Ci‑dessous, un extrait de l’arborescence principale avec les dossiers clés.  
Le code suivant parcourt le répertoire racine (`/home/oai/share` dans le dépôt fourni) et affiche les premiers niveaux de dossiers pour donner un aperçu compact.  

*Exécutez la cellule de code si vous travaillez dans un environnement Jupyter pour obtenir la vue actualisée ; sinon, reportez‑vous à l’extrait textuel ci‑dessous.*


import os

def print_tree(path, prefix='', depth=0, max_depth=2):
    # Affiche l'arborescence limitée à max_depth niveaux.
    if depth > max_depth:
        return
    try:
        items = sorted(os.listdir(path))
    except Exception as e:
        print(f"[Erreur lors du listing de {path}: {e}]")
        return
    for i, name in enumerate(items):
        branch = '└── ' if i == len(items) - 1 else '├── '
        print(prefix + branch + name)
        new_path = os.path.join(path, name)
        if os.path.isdir(new_path):
            new_prefix = prefix + ('    ' if i == len(items) - 1 else '│   ')
            print_tree(new_path, new_prefix, depth + 1, max_depth)

# affiche la racine du projet (ajustez le chemin si nécessaire)
print_tree('.', max_depth=2)


Un aperçu des dossiers importants :

- **0_raw/** : contient les données brutes ou des fichiers vides (`.gitkeep`) servant de placeholder pour versionner le dossier.

- **1_datasets/** : jeux de données préparés pour l’entraînement.
  - **detection_trains/** : images et labels pour la détection des trains en format YOLO, divisés en `train/`, `val/` et `test/`.
  - **segmentation_rails/** : images et labels pour la segmentation des voies (rails), divisés en `train/`, `val/` et `test/`.

- **2_configs/** : fichiers de configuration YAML décrivant les jeux de données (chemins et noms de classes).  
  - `yolo/data_trains.yaml` définit le jeu de données de détection avec une seule classe `train`.
  - `yolo/data_rails.yaml` (ou `data_rails_1class.yaml`) définit le jeu de données de segmentation avec une classe `voie`.

- **3_training/** : dossiers créés par les entraînements Ultralytics (`runs/detect/...`, `runs/segment/...`) et éventuellement des checkpoints.

- **4_models/** : modèles entraînés et exportés. On y dépose les fichiers `best.pt` et `best.onnx` pour la détection et la segmentation.

- **5_inference/** : scripts d’inférence et, le cas échéant, des échantillons.
  - **scripts/** contient les scripts Python d’inférence : `infer_rails.py`, `infer_trains.py`, `infer_trains_and_rails.py` et `infer_trains_and_rails_with_history.py`.
  - **samples/** peut contenir des exemples de vidéos d’entrée pour tester les scripts.

- **6_evaluation/** : rapports et graphiques produits lors de l’évaluation des modèles.

- **7_outputs/** : résultats des scripts d’inférence.  
  - **7_outputs/overlays/** : vidéos annotées (fichiers MP4).  
  - **7_outputs/predictions/** : fichiers JSONL et CSV contenant les prédictions et/ou l’historique d’occupation des voies pour chaque frame.

- **8_inputs/** : peut contenir des fichiers d’entrée temporaires (par exemple des vidéos de test).  

- **data_trains/** et **data_rails/** : jeux de données d’origine (images + labels) avant préparation.  
  Ces dossiers servent de sources pour générer les jeux de données dans `1_datasets`.

- **yolo11s.pt** et **yolo11s-seg.pt** : poids pré‑entraînés fournis par Ultralytics, utilisés comme point de départ pour l’entraînement des modèles de détection (YOLOv11) et de segmentation (YOLOv11‑seg).

- **video.mp4**, **video2.mp4** : vidéos d’exemple pour tester les modèles.


## 2. Rôle de chaque dossier et fichiers clés {#Roles}

Le dépôt suit une structure hiérarchique visant à organiser les données, la configuration, l’entraînement et l’exploitation des modèles.

### Dossiers de données

- **0_raw/** : réservé aux données brutes initiales. Un fichier `.gitkeep` y est présent pour maintenir le dossier dans le système de version.

- **data_trains/** et **data_rails/** : dossiers d’images et de labels annotés initialement.  
  * `data_trains/images/` et `data_trains/labels/` contiennent les images de trains et les fichiers d’annotations YOLO (format segmentation) pour la détection des trains.  
  * `data_rails/images/` et `data_rails/labels/` contiennent les images et annotations (polygones) des voies pour la segmentation.  
  Ces jeux ont été traités pour générer les sous‑jeux utilisables par YOLO.

- **1_datasets/** : jeux de données préparés pour l’entraînement.
  - **detection_trains/images/** et **detection_trains/labels/** : contiennent les images et labels destinés à l’entraînement (train), à la validation (val) et au test (test).  
    Les labels ont été convertis du format segmentation (polygones) vers le format détection (boîtes englobantes) et toutes les classes ont été remappées sur un identifiant unique `0` (`train`).  
    La répartition typique est 80 % pour l’entraînement, 10 % pour la validation et 10 % pour le test.
  - **segmentation_rails/images/** et **segmentation_rails/labels/** : contiennent les images et masques pour la segmentation des voies.  
    Toutes les classes de voies ont été remappées en une seule classe `0` (`voie`).

### Dossiers de configuration

- **2_configs/yolo/** et **2_configs/segmentation/** : YAML décrivant les jeux de données. Ces fichiers sont utilisés par Ultralytics pour charger les données et associer les indices de classe à des noms lisibles.  

### Dossiers d’entraînement

- **3_training/runs/** : dossiers générés automatiquement par Ultralytics lors de l’entraînement (`runs/detect/trainX/` et `runs/segment/trainY/`). On y trouve les logs, les courbes d’apprentissage et les fichiers `weights/best.pt` et `weights/last.pt` pour chaque entraînement.  
- **3_training/checkpoints/** (facultatif) : peut contenir des copies sauvegardées des modèles à différentes étapes.

### Dossiers de modèles

- **4_models/detection/** : recopie finale des modèles de détection (poids en `.pt` et versions exportées en `.onnx` pour le backend).

- **4_models/segmentation/** : recopie finale des modèles de segmentation.

- **4_models/exports/** : versions exportées (`.onnx`, `.json`, etc.) prêtes pour l’inférence hors Python.

### Dossiers d’inférence

- **5_inference/scripts/** : scripts Python réalisant l’inférence sur des images ou des vidéos.  
  Ces scripts chargent les modèles, appliquent la détection ou la segmentation, produisent des vidéos annotées et génèrent des fichiers JSON/CSV décrivant les prédictions et l’occupation des voies.

- **5_inference/samples/** : exemples de vidéos d’entrée permettant de tester les scripts.

### Dossiers d’évaluation et de sortie

- **6_evaluation/** : rapports, métriques et figures générés lors de la validation des modèles.

- **7_outputs/** : résultats des scripts d’inférence.  
  - **7_outputs/overlays/** : vidéos annotées (fichiers MP4).  
  - **7_outputs/predictions/** : fichiers JSONL et CSV contenant les prédictions et/ou l’historique d’occupation des voies pour chaque frame.

### Fichiers utilitaires

- **rename.py** : script utilitaire pour renommer des fichiers ou adapter la structure des labels (par exemple, conversion des polygones en boîtes).

- **requirements.txt** : liste des dépendances Python nécessaires (par exemple `ultralytics`, `opencv-python`, `numpy`, etc.).  
  Exécutez `pip install -r requirements.txt` pour installer l’environnement.

- **yolo11s.pt** / **yolo11s-seg.pt** : poids pré‑entraînés de la famille Ultralytics YOLOv11 servant de base pour les entraînements de détection et de segmentation.

- **video.mp4**, **video2.mp4** : vidéos d’exemple pour tester les modèles.



## 3. Préparation des données et entraînement des modèles {#Entrainement}

Cette section décrit la transformation des données brutes en jeux exploitables par les modèles et explique comment lancer l’entraînement.

### Préparation des données

1. **Récupération des données brutes** : les images annotées se trouvent dans `data_trains` et `data_rails`. Les fichiers `.txt` contiennent des polygones (YOLO‑segmentation).  
2. **Conversion des labels** : pour la détection des trains, les polygones ont été convertis en boîtes englobantes et toutes les classes ont été fusionnées en une seule classe `train`. Les scripts `convert_seg_to_det.py` et `remap_labels_to_one_class.py` automatisent cette étape. Pour la segmentation des voies, toutes les classes `voie1..voie6` ont été remappées sur un identifiant unique `0` (`voie`).  
3. **Répartition train/val/test** : les scripts `split_yolo_detection.py` et `split_yolo_seg_rails.py` créent la répartition 80/10/10 en copiant les fichiers dans `1_datasets/detection_trains` et `1_datasets/segmentation_rails`.
4. **Création des YAML de configuration** : les fichiers `2_configs/yolo/data_trains.yaml` et `2_configs/yolo/data_rails_1class.yaml` décrivent les chemins (`path`, `train`, `val`, `test`) et les noms de classes. Exemple :

```yaml
# 2_configs/yolo/data_trains.yaml
path: 1_datasets/detection_trains
train: images/train
val: images/val
test: images/test
names:
  0: train
```

```yaml
# 2_configs/yolo/data_rails_1class.yaml
path: 1_datasets/segmentation_rails
train: images/train
val: images/val
test: images/test
names:
  0: voie
```

Ces fichiers sont passés à Ultralytics pour charger les jeux.


### 3.1 Entraînement du modèle de détection des trains {#Detection}

1. **Installation de la bibliothèque Ultralytics** :

```bash
pip install ultralytics opencv-python numpy
```

2. **Lancement de l’entraînement** :

Utilisez la commande `ultralytics detect train` (ou `yolo detect train` selon la version) pour entraîner le modèle sur les données préparées :

```bash
# depuis la racine du projet
ultralytics detect train   model=yolo11s.pt   data=2_configs/yolo/data_trains.yaml   epochs=60   imgsz=640   batch=8   name=train_trains_1class
```

- **model** : poids pré‑entraînés servant de point de départ (`yolo11s.pt`).
- **data** : chemin vers le fichier YAML décrivant les données.
- **epochs** : nombre d’époques (60 dans notre cas). Le temps d’entraînement dépend du matériel (GPU recommandé).  
- **imgsz** : taille des images (640×640).  
- **batch** : taille du lot.  
- **name** : nom du run ; un dossier `runs/detect/{name}/` sera créé.

3. **Sorties de l’entraînement** : Ultralytics crée un dossier `runs/detect/<nom>/` avec :
   - `weights/best.pt` et `weights/last.pt` : meilleurs poids et derniers poids.
   - `results.png` : courbes de perte et de métriques.
   - `confusion_matrix.png` : matrice de confusion.

4. **Remarque sur les classes** : dans ce projet, toutes les classes `train1..train6` ont été fusionnées car la numérotation gauche‑droite est appliquée après l’inférence. Un apprentissage multi‑classes sur des rangs spatiaux n’est pas recommandé.


### 3.2 Entraînement du modèle de segmentation des voies {#Segmentation}

1. **Remappage des labels** : toutes les classes `voie1..voie6` ont été fusionnées en une seule classe `voie`. Le script `remap_rails_seg_to_one_class.py` réalise cette opération automatiquement.

2. **Répartition train/val/test** : le script `split_yolo_seg_rails.py` copie les images et masques dans `1_datasets/segmentation_rails` avec la répartition souhaitée.

3. **Entraînement YOLO segmentation** :

```bash
ultralytics segment train   model=yolo11s-seg.pt   data=2_configs/yolo/data_rails_1class.yaml   epochs=60   imgsz=640   batch=8   name=train_rails_1class
```

4. **Sorties de l’entraînement** : le dossier `runs/segment/<nom>/` contient les poids (`best.pt`, `last.pt`), les courbes de perte et des images de prédiction.

5. **Exportation ONNX** :

Pour intégrer le modèle dans un backend sans PyTorch, exportez le modèle en ONNX :

```bash
yolo export model=runs/segment/<nom>/weights/best.pt format=onnx opset=12
```

Le fichier `best.onnx` sera généré et placé dans le même dossier.


## 4. Validation et tests {#Validation}

Après l’entraînement, il est essentiel de mesurer la performance des modèles sur le jeu de test. Ultralytics propose des commandes `val` et `predict` :

- **Évaluation quantitative** :

```bash
# Détection des trains
ultralytics detect val   model=runs/detect/train_trains_1class/weights/best.pt   data=2_configs/yolo/data_trains.yaml   split=test

# Segmentation des voies
yolo segment val   model=runs/segment/train_rails_1class/weights/best.pt   data=2_configs/yolo/data_rails_1class.yaml   split=test
```

Les résultats affichent la précision, le rappel et les mAP (moyennes de la précision) et génèrent un dossier `runs/detect/val*` ou `runs/segment/val*` avec des images d’exemple.

- **Évaluation qualitative** : visualiser les prédictions sur des images ou vidéos :

```bash
# Visualiser la détection des trains sur le jeu test
ultralytics detect predict   model=runs/detect/train_trains_1class/weights/best.pt   source=1_datasets/detection_trains/images/test   save=True

# Visualiser la segmentation des rails sur une vidéo
yolo segment predict   model=runs/segment/train_rails_1class/weights/best.onnx   source=video.mp4   save=True
```

Des fichiers annotés seront sauvegardés dans `runs/detect/predict*` ou `runs/segment/predict*`.


## 5. Scripts d’inférence {#Inference}

Les scripts d’inférence fournis dans `5_inference/scripts/` permettent d’utiliser les modèles entraînés pour traiter des vidéos et produire des sorties structurées. Ils reposent sur les bibliothèques Ultralytics et OpenCV. Voici un résumé de leur fonctionnement.


### 5.1 Inférence des voies (rails) {#InfRails}

Le script `infer_rails.py` charge un modèle de segmentation (`best.onnx`) et applique la segmentation à chaque frame d’une vidéo.  

- **Entrées** :
  - `MODEL_PATH` : chemin vers le modèle de segmentation (`runs/segment/train_rails_1class/weights/best.onnx`).
  - `SOURCE_VIDEO` : chemin de la vidéo d’entrée (ex. `video.mp4`).
  - Paramètres optionnels : taille d’image (`IMGSZ`), seuil de confiance (`CONF`), seuil du masque (`MASK_THRESH`).

- **Traitement** :
  1. Chargement du modèle via `YOLO(MODEL_PATH)`.
  2. Parcours de la vidéo image par image avec OpenCV.
  3. Inférence pour récupérer les masques prédits (`r.masks.data`), création d’un masque binaire global (`mask_bin`).
  4. Détection des **rails** par composantes connexes : on applique `cv2.connectedComponentsWithStats` sur `mask_bin` pour identifier chaque rail.
  5. Tri des rails de gauche à droite en fonction de la coordonnée `x` de leur centre. Chaque rail se voit attribuer un rang `voie1` à `voie6`.
  6. Sauvegarde de la vidéo annotée dans `7_outputs/overlays/rails_overlay.mp4` et d’un fichier JSONL pour chaque frame dans `7_outputs/predictions/rails_per_frame.jsonl`.

- **Sorties** :
  - Vidéo annotée (overlay) : rails colorés en vert et numérotés.
  - Fichier JSONL par frame : indique combien de rails ont été détectés, leurs coordonnées et l’ordre gauche→droite.  

Par exemple :

```json
{
  "frame": 42,
  "rails_detected": 6,
  "rails": [
    {"rank": 1, "label": "voie1", "bbox": [x1, y1, x2, y2], "cx": 120.3, "area": 50456},
    …
  ]
}
```

Ce script facilite l’intégration de la segmentation dans un backend sans nécessiter PyTorch.


### 5.2 Inférence des trains {#InfTrains}

Le script `infer_trains.py` réalise la détection et le suivi des trains à partir d’un modèle de détection YOLOv11 (`best.pt`).  
Il utilise l’algorithme **BoT‑SORT** pour attribuer un identifiant (`track_id`) à chaque train et garantir la persistance d’un train d’une frame à l’autre.

- **Entrées** :
  - `MODEL_PATH` : chemin vers le modèle de détection (`runs/detect/train_trains_1class/weights/best.pt`).
  - `SOURCE_VIDEO` : vidéo d’entrée.
  - Paramètres : taille d’image (`IMGSZ`), seuil de confiance (`CONF`), seuil d’IoU (`IOU`), chemin vers le fichier de configuration du tracker (`botsort.yaml`).

- **Traitement** :
  1. Chargement du modèle via `YOLO(MODEL_PATH)`.
  2. Parcours de la vidéo et appel à `model.track()` pour obtenir les boîtes (`boxes.xyxy`), les scores (`boxes.conf`), les classes (`boxes.cls`) et les identifiants de suivi (`boxes.id`).
  3. Calcul du centre X des boîtes et tri de gauche à droite pour attribuer un rang (`train1` à `train6`). Ce rang est indépendant de la classe car toutes les classes ont été fusionnées.
  4. Sauvegarde d’une vidéo annotée (`trains_track_overlay.mp4`) et d’un fichier JSONL (`trains_per_frame.jsonl`) contenant pour chaque frame les boîtes, les scores, les identifiants de suivi et les rangs gauche→droite.

- **Sorties** :
  - Vidéo overlay montrant les boîtes des trains, leur identifiant et leur rang gauche→droite.
  - Fichier JSONL listant les trains et leurs propriétés pour chaque frame.

Ce script ne gère pas les rails : il se concentre uniquement sur la détection et le tracking des trains.


### 5.3 Script combiné trains + rails {#InfCombi}

Le script `infer_trains_and_rails_with_history.py` combine la détection des trains et la segmentation des rails pour fournir une compréhension complète de la scène.  
Il associe chaque train détecté à la voie sur laquelle il se trouve et construit un historique d’occupation.

- **Entrées** :
  - `TRAINS_MODEL` : modèle de détection des trains (`best.pt`).
  - `RAILS_MODEL` : modèle de segmentation des rails (`best.onnx`).
  - `SOURCE_VIDEO` : vidéo à analyser.

- **Étapes principales** :

  1. **Segmentation des rails** : on applique le modèle de segmentation sur chaque frame pour obtenir un masque binaire. Les composantes connexes de ce masque sont analysées pour identifier jusqu’à six rails, triés de gauche à droite.

  2. **Détection des trains + tracking** : on détecte les trains via `model.track()` et on récupère les identifiants de suivi (`track_id`). Les trains sont triés de gauche à droite afin de leur attribuer les labels `train1..train6`.

  3. **Association train→voie** : pour chaque train, on prend le point bas‑centre de sa boîte englobante et on regarde dans la matrice de composantes pour déterminer sur quelle voie il se trouve.  
     Si le point tombe en dehors du masque, aucune voie n’est attribuée (`None`).

  4. **Historique d’occupation** : le script garde en mémoire l’ancienne voie associée à chaque train et génère un événement lorsque le train change de voie.  
     Cela permet de produire des statistiques comme la durée passée sur chaque voie et d’exporter un historique en fin de traitement.

- **Sorties** :

  - **Vidéo annotée** (`trains_rails_overlay.mp4`) : chaque rail est coloré en vert et numéroté, chaque train est entouré d’une boîte colorée avec son identifiant, son rang (`train3` par exemple) et la voie sur laquelle il se trouve (`voie2`).  
  - **Fichier `trains_rails_per_frame.jsonl`** : pour chaque frame, la liste des rails détectés et des trains avec leur voie associée et leur rang gauche→droite.  
  - **Fichier `occupancy_per_frame.csv`** : un enregistrement tabulaire précisant, pour chaque frame, si une voie est occupée et par quels `track_id`.  
  - **Fichier `occupancy_events.csv` et `occupancy_events.jsonl`** : un historique des événements, c’est‑à‑dire les moments où un train entre ou quitte une voie, avec les timestamps et la durée passée sur la voie précédente.  

Ce script constitue la base d’un système de supervision : il fournit une vision temps réel de l’occupation des voies et une traçabilité historique.


## 6. Export de l’historique d’occupation {#Historique}

L’historique d’occupation est utile pour analyser la durée de stationnement des trains sur chaque voie et détecter d’éventuels conflits (deux trains sur la même voie).  
Le script combiné génère :

- **occupancy_per_frame.csv** : fichier avec une ligne par voie et par frame. Il contient l’horodatage (`time_s`), le nom de la voie, un indicateur `occupied` (0/1) et la liste des `track_id` des trains présents.  

- **occupancy_events.csv** : fichier listant les transitions de voie pour chaque train. Pour chaque événement, on a :
  - l’identifiant du train (`track_id`),
  - la voie quittée (`from_voie`),
  - la voie rejointe (`to_voie`),
  - la frame et l’horodatage de début et de fin,
  - la durée passée sur la voie précédente.

Ces fichiers peuvent être analysés dans un tableur ou un script Python pour extraire des statistiques (par exemple la voie la plus utilisée ou le temps d’occupation moyen par train).


## Conclusion

Ce notebook a présenté la structure du dépôt Smart Yard, le rôle des dossiers et fichiers, les étapes de préparation des données, l’entraînement des modèles de détection et de segmentation, la validation, ainsi que les scripts d’inférence et l’export de l’historique d’occupation.  
En suivant ces indications, un nouveau développeur ou un évaluateur peut reproduire l’ensemble du pipeline, du traitement des données brutes jusqu’à l’exploitation des modèles en production.
