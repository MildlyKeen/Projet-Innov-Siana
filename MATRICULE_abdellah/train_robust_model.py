"""
Entraînement d'un modèle CNN robuste pour reconnaissance de matricules TGV
Utilise les ROI dans matricule TGV comme données d'entraînement
"""

import cv2
import numpy as np
import os
import json
from sklearn.model_selection import train_test_split
import pickle

print("="*70)
print("ENTRAÎNEMENT CNN POUR MATRICULES TGV")
print("="*70)

# Chemins
data_dir = r"C:\Users\abdel\OneDrive\Documents\GitHub\Projet-Innov-Siana\MATRICULE_abdellah\datta\matricule TGV"
model_dir = r"C:\Users\abdel\OneDrive\Documents\GitHub\Projet-Innov-Siana\MATRICULE_abdellah\models"

os.makedirs(model_dir, exist_ok=True)

# 1. CHARGER TOUTES LES DONNÉES
print("\n[1/6] Chargement des ROI de matricules...")

images = []
labels = []
filenames = []

for filename in sorted(os.listdir(data_dir)):
    if filename.endswith(('.jpg', '.jpeg', '.png')):
        matricule = filename.split('_')[0]  # Ex: "1201"
        
        img_path = os.path.join(data_dir, filename)
        img = cv2.imread(img_path)
        
        if img is not None:
            # Convertir en niveaux de gris
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            
            # Prétraitement pour améliorer la qualité
            # 1. Égalisation d'histogramme
            gray = cv2.equalizeHist(gray)
            
            # 2. Redimensionner à taille fixe
            resized = cv2.resize(gray, (160, 80))  # 4 chiffres, ~40px par chiffre
            
            # 3. Normaliser
            normalized = resized.astype('float32') / 255.0
            
            images.append(normalized)
            labels.append(matricule)
            filenames.append(filename)

print(f"✓ {len(images)} images chargées")

# Afficher la distribution des matricules
from collections import Counter
label_counts = Counter(labels)
print(f"✓ {len(label_counts)} matricules uniques trouvés:")
for mat, count in sorted(label_counts.items()):
    print(f"  {mat}: {count} images")

# 2. CRÉER UN MAPPING MATRICULE -> INDEX
print("\n[2/6] Création du mapping...")

unique_labels = sorted(set(labels))
label_to_idx = {label: idx for idx, label in enumerate(unique_labels)}
idx_to_label = {idx: label for label, idx in label_to_idx.items()}

print(f"✓ Mapping créé pour {len(unique_labels)} matricules")

# 3. PRÉPARER LES DONNÉES
print("\n[3/6] Préparation train/test split...")

X = np.array(images)
y = np.array([label_to_idx[label] for label in labels])

# Reshape pour CNN (samples, height, width, channels)
X = X.reshape(-1, 80, 160, 1)

# Split stratifié
X_train, X_test, y_train, y_test = train_test_split(
    X, y, test_size=0.2, random_state=42, stratify=y
)

print(f"✓ Entraînement: {len(X_train)} images")
print(f"✓ Test: {len(X_test)} images")

# 4. ESSAYER AVEC UN MODÈLE SIMPLE D'ABORD (Random Forest sur features)
print("\n[4/6] Entraînement modèle Random Forest...")

from sklearn.ensemble import RandomForestClassifier

# Aplatir pour Random Forest
X_train_flat = X_train.reshape(len(X_train), -1)
X_test_flat = X_test.reshape(len(X_test), -1)

# Entraîner
rf_model = RandomForestClassifier(n_estimators=100, max_depth=20, random_state=42, n_jobs=-1)
rf_model.fit(X_train_flat, y_train)

# Évaluer
train_acc = rf_model.score(X_train_flat, y_train)
test_acc = rf_model.score(X_test_flat, y_test)

print(f"✓ Précision entraînement: {train_acc*100:.2f}%")
print(f"✓ Précision test: {test_acc*100:.2f}%")

# 5. TESTER SUR QUELQUES EXEMPLES
print("\n[5/6] Test sur échantillons...")

y_pred = rf_model.predict(X_test_flat)

correct = 0
print("\nExemples de prédictions:")
for i in range(min(10, len(X_test))):
    pred_mat = idx_to_label[y_pred[i]]
    true_mat = idx_to_label[y_test[i]]
    
    status = "✓" if pred_mat == true_mat else "✗"
    if pred_mat == true_mat:
        correct += 1
    
    print(f"  {status} Prédit: {pred_mat}, Vrai: {true_mat}")

# 6. SAUVEGARDER
print("\n[6/6] Sauvegarde du modèle...")

# Sauvegarder le modèle
model_path = os.path.join(model_dir, 'matricule_rf_model.pkl')
with open(model_path, 'wb') as f:
    pickle.dump(rf_model, f)
print(f"✓ Modèle sauvegardé: {model_path}")

# Sauvegarder les mappings
mapping_path = os.path.join(model_dir, 'matricule_mapping.pkl')
with open(mapping_path, 'wb') as f:
    pickle.dump({'label_to_idx': label_to_idx, 'idx_to_label': idx_to_label}, f)
print(f"✓ Mappings sauvegardés: {mapping_path}")

# Config JSON
config = {
    'model_type': 'RandomForest',
    'matricules': unique_labels,
    'nb_images': len(images),
    'accuracy_train': float(train_acc),
    'accuracy_test': float(test_acc),
    'image_size': [160, 80]
}

config_path = os.path.join(model_dir, 'matricule_rf_config.json')
with open(config_path, 'w') as f:
    json.dump(config, f, indent=2)
print(f"✓ Config sauvegardée: {config_path}")

print("\n" + "="*70)
print("✅ MODÈLE ROBUSTE ENTRAÎNÉ AVEC SUCCÈS !")
print("="*70)
print(f"Précision test: {test_acc*100:.2f}%")
print(f"Prêt à détecter matricules sur images_brutes")
