# Train Wagon OCR Pipeline 🚂

Pipeline complet de détection et reconnaissance automatique des numéros d'identification des wagons de train via OCR.

## 📋 Vue d'ensemble

Ce projet implémente un système de reconnaissance de caractères (OCR) pour identifier automatiquement les numéros de wagons à partir de flux vidéo. Il combine :

- **Prétraitement vidéo** : Correction de perspective, stabilisation, amélioration d'image
- **OCR** : Extraction de texte avec PaddleOCR
- **Validation** : Filtrage par regex et score de confiance
- **Intégration** : Interface unifiée pour la fusion avec détection (Membre 1)

## 🛠️ Installation

### Prérequis

- Python 3.8 ou supérieur
- Caméra (optionnel, pour démo temps réel)
- GPU (optionnel, pour accélérer l'OCR)

### Étapes d'installation

1. **Cloner ou télécharger le projet**

```bash
cd MATRICULE
```

2. **Créer un environnement virtuel (recommandé)**

```bash
python -m venv venv
venv\Scripts\activate  # Windows
# ou
source venv/bin/activate  # Linux/Mac
```

3. **Installer les dépendances**

```bash
pip install -r requirements.txt
```

**Note** : La première exécution téléchargera automatiquement les modèles PaddleOCR (~100MB).

## 🚀 Utilisation

### 1. Traitement d'une vidéo

```bash
python demo.py --video input_video.mp4 --output output_annotated.mp4
```

### 2. Traitement d'une image

```bash
python demo.py --image train_photo.jpg --output result.jpg
```

### 3. Démonstration en temps réel (webcam)

```bash
python demo.py --webcam
```

Appuyez sur `q` pour quitter.

## ⚙️ Configuration

Modifiez `config.py` pour ajuster les paramètres :

### Paramètres OCR

```python
OCR_CONFIDENCE_THRESHOLD = 0.7  # Seuil de confiance minimum
OCR_LANGUAGE = 'en'             # Langue ('en', 'fr', etc.)
USE_GPU = False                 # Activer GPU si disponible
```

### Format des numéros de wagon

Adaptez le pattern regex selon votre format :

```python
# Exemples de formats
WAGON_ID_PATTERN = r'^[A-Z0-9]{2,4}[-\s]?\d{4,6}$'  # Format: AB-12345
# WAGON_ID_PATTERN = r'^\d{6,8}$'                   # Format: 12345678
# WAGON_ID_PATTERN = r'^[A-Z]{2}\d{4}$'             # Format: AB1234
```

### Prétraitement

```python
PERSPECTIVE_CORRECTION_ENABLED = True  # Correction de perspective
STABILIZATION_ENABLED = True           # Stabilisation vidéo
CONTRAST_ENHANCEMENT = True            # Amélioration du contraste
```

## 📁 Structure du projet

```
MATRICULE/
│
├── config.py              # Configuration globale
├── preprocessing.py       # Pipeline de prétraitement vidéo
├── ocr_module.py         # Module OCR avec PaddleOCR
├── integration.py        # Interface d'intégration
├── demo.py               # Scripts de démonstration
├── requirements.txt      # Dépendances Python
└── README.md            # Documentation
```

## 🔌 Intégration avec l'équipe

### Pour Membre 1 (Détection)

Fournissez les détections au format :

```python
detections = [
    {
        'bbox': (x, y, w, h),      # Bounding box
        'class': 'train',          # Classe
        'confidence': 0.95         # Score de confiance
    },
    # ... autres détections
]
```

### Pour Membre 3 (Fusion & Logique Métier)

Utilisez l'interface `DetectionOCRInterface` :

```python
from integration import DetectionOCRInterface

# Initialiser
interface = DetectionOCRInterface()

# Traiter un frame
results = interface.detect_and_read(frame, detections)

# Exporter les résultats
interface.export_results(results, 'output_results.json')
```

Format de sortie :

```json
[
  {
    "wagon_id": "AB-12345",
    "confidence": 0.89,
    "bbox": [100, 200, 300, 150],
    "raw_text": "AB-12345"
  }
]
```

## 🎯 Pipeline complet

```python
from integration import TrainDetectionOCRPipeline

# Initialiser le pipeline
pipeline = TrainDetectionOCRPipeline()

# Traiter un frame
annotated_frame, ocr_results = pipeline.process_frame(frame, detections)

# Traiter une vidéo complète
stats = pipeline.process_video('input.mp4', 'output.mp4')
```

## 🧪 Exemples de code

### Exemple 1 : Traitement basique

```python
import cv2
from integration import DetectionOCRInterface

# Charger une image
frame = cv2.imread('train_image.jpg')

# Initialiser l'interface
interface = DetectionOCRInterface()

# Détecter et lire
results = interface.detect_and_read(frame)

# Afficher les résultats
for result in results:
    print(f"Wagon: {result['wagon_id']}, Confiance: {result['confidence']:.2f}")
```

### Exemple 2 : Intégration avec détection existante

```python
import cv2
from integration import TrainDetectionOCRPipeline

# Votre fonction de détection (Membre 1)
def your_detection_function(frame):
    # ... votre code de détection ...
    return detections  # Liste de dicts avec bbox, class, confidence

# Pipeline
pipeline = TrainDetectionOCRPipeline()

# Traiter vidéo
cap = cv2.VideoCapture('input.mp4')

while True:
    ret, frame = cap.read()
    if not ret:
        break
    
    # Obtenir détections
    detections = your_detection_function(frame)
    
    # Ajouter OCR
    annotated, ocr_results = pipeline.process_frame(frame, detections)
    
    # Afficher
    cv2.imshow('Result', annotated)
    if cv2.waitKey(1) & 0xFF == ord('q'):
        break

cap.release()
cv2.destroyAllWindows()
```

### Exemple 3 : Personnalisation du prétraitement

```python
from preprocessing import VideoPreprocessor
import cv2

preprocessor = VideoPreprocessor()
frame = cv2.imread('image.jpg')

# Définir des points de perspective personnalisés
# Format: [top-left, top-right, bottom-right, bottom-left]
perspective_points = np.float32([
    [150, 100],  # Top-left
    [650, 100],  # Top-right
    [700, 500],  # Bottom-right
    [100, 500]   # Bottom-left
])

# Appliquer le prétraitement
processed = preprocessor.preprocess_frame(frame, perspective_points)
```

## 🐛 Dépannage

### Problème : OCR ne détecte rien

- Vérifiez la qualité de l'image (résolution, luminosité)
- Réduisez `OCR_CONFIDENCE_THRESHOLD` dans config.py
- Activez/désactivez les options de prétraitement
- Testez avec `CONTRAST_ENHANCEMENT = True`

### Problème : Mauvaises détections

- Ajustez le pattern regex `WAGON_ID_PATTERN`
- Vérifiez les corrections de caractères dans `ocr_module.py::clean_text()`
- Augmentez `ROI_EXPANSION_FACTOR` pour capturer plus de contexte

### Problème : Performance lente

- Activez le GPU : `USE_GPU = True`
- Réduisez la résolution vidéo
- Désactivez la stabilisation : `STABILIZATION_ENABLED = False`
- Utilisez un échantillonnage de frames (traiter 1 frame sur N)

### Problème : Installation PaddleOCR échoue

```bash
# Essayez d'installer manuellement
pip install paddlepaddle -i https://mirror.baidu.com/pypi/simple
pip install paddleocr

# Alternative : utilisez EasyOCR
pip install easyocr
# Décommentez le code EasyOCR dans ocr_module.py
```

## 📊 Optimisations possibles

### Performance

- **Détection de mouvement** : Ne traiter que les frames avec changements
- **Tracking** : Suivre les wagons détectés pour éviter OCR redondant
- **Batch processing** : Traiter plusieurs ROIs en parallèle

### Précision

- **Post-traitement** : Vérification croisée avec base de données
- **Consensus temporel** : Voter sur plusieurs frames pour un même wagon
- **Fine-tuning** : Réentraîner PaddleOCR sur vos données spécifiques

### Code

```python
# Exemple : Détection de mouvement
class MotionBasedProcessor:
    def __init__(self):
        self.prev_gray = None
    
    def has_significant_motion(self, frame):
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        if self.prev_gray is None:
            self.prev_gray = gray
            return True
        
        # Calculer différence
        diff = cv2.absdiff(self.prev_gray, gray)
        motion_score = np.mean(diff)
        
        self.prev_gray = gray
        return motion_score > 10  # Seuil ajustable
```

## 📝 Formats de sortie

### JSON (par défaut)

```json
[
  {
    "wagon_id": "SNCF-123456",
    "confidence": 0.92,
    "bbox": [150, 200, 300, 100],
    "raw_text": "SNCF 123456"
  }
]
```

### CSV (à implémenter si besoin)

```python
import csv

def export_to_csv(results, output_path):
    with open(output_path, 'w', newline='') as f:
        writer = csv.DictWriter(f, fieldnames=['wagon_id', 'confidence', 'bbox_x', 'bbox_y', 'bbox_w', 'bbox_h'])
        writer.writeheader()
        for r in results:
            x, y, w, h = r['bbox']
            writer.writerow({
                'wagon_id': r['wagon_id'],
                'confidence': r['confidence'],
                'bbox_x': x, 'bbox_y': y, 'bbox_w': w, 'bbox_h': h
            })
```

## 🔗 Ressources

- [PaddleOCR Documentation](https://github.com/PaddlePaddle/PaddleOCR)
- [OpenCV Documentation](https://docs.opencv.org/)
- [Regex Tutorial](https://regex101.com/)

## 👥 Collaboration

Ce module fait partie d'un projet plus large :

- **Membre 1** : Segmentation & Détection YOLOv8
- **Membre 2** (vous) : Prétraitement & OCR
- **Membre 3** : Fusion & Logique Métier

## 📄 Licence

Ce projet est développé dans un cadre académique/professionnel.

## 🤝 Support

Pour toute question ou problème :
1. Vérifiez la section Dépannage
2. Consultez les exemples de code
3. Ajustez les paramètres dans config.py

---

**Bon développement ! 🚀**
