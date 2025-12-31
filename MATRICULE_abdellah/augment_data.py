"""
AUGMENTATION DES DONNÉES POUR 1203
===================================
Crée des variations des ROIs existantes pour augmenter le dataset
"""

import cv2
import numpy as np
import os

def augment_image(img, idx):
    """Crée plusieurs variations d'une image"""
    variations = []
    
    # Original
    variations.append((img.copy(), f"orig_{idx}"))
    
    # Rotation légère (-5 à +5 degrés)
    for angle in [-3, 3]:
        M = cv2.getRotationMatrix2D((img.shape[1]//2, img.shape[0]//2), angle, 1.0)
        rotated = cv2.warpAffine(img, M, (img.shape[1], img.shape[0]))
        variations.append((rotated, f"rot{angle}_{idx}"))
    
    # Ajustement luminosité
    for beta in [-20, 20]:
        adjusted = cv2.convertScaleAbs(img, alpha=1.0, beta=beta)
        variations.append((adjusted, f"bright{beta}_{idx}"))
    
    # Flou léger
    blurred = cv2.GaussianBlur(img, (3, 3), 0)
    variations.append((blurred, f"blur_{idx}"))
    
    # Contraste
    for alpha in [0.9, 1.1]:
        contrast = cv2.convertScaleAbs(img, alpha=alpha, beta=0)
        variations.append((contrast, f"contrast{int(alpha*10)}_{idx}"))
    
    # Bruit
    noise = np.random.normal(0, 5, img.shape).astype(np.uint8)
    noisy = cv2.add(img, noise)
    variations.append((noisy, f"noise_{idx}"))
    
    return variations

def augment_matricule_1203(input_dir, output_dir, matricule="1203"):
    """Augmente les images du matricule 1203"""
    
    print("\n" + "="*70)
    print("AUGMENTATION DES DONNÉES POUR", matricule)
    print("="*70)
    
    # Trouver toutes les images de 1203
    images_1203 = []
    for filename in os.listdir(input_dir):
        if filename.startswith(f"{matricule}_") and filename.endswith(('.jpg', '.jpeg', '.png')):
            images_1203.append(filename)
    
    print(f"Trouvé {len(images_1203)} images de {matricule}")
    
    if len(images_1203) == 0:
        print(f"❌ Aucune image trouvée pour {matricule}")
        return 0
    
    os.makedirs(output_dir, exist_ok=True)
    
    total_generated = 0
    
    for i, filename in enumerate(images_1203):
        img_path = os.path.join(input_dir, filename)
        img = cv2.imread(img_path)
        
        if img is None:
            continue
        
        print(f"\nAugmentation de {filename}:")
        
        # Créer variations
        variations = augment_image(img, i)
        
        for aug_img, suffix in variations:
            output_filename = f"{matricule}_aug_{suffix}.jpg"
            output_path = os.path.join(output_dir, output_filename)
            cv2.imwrite(output_path, aug_img)
            total_generated += 1
            print(f"  ✓ {output_filename}")
    
    print("\n" + "="*70)
    print(f"✓ {total_generated} images augmentées générées dans {output_dir}/")
    print(f"Total pour {matricule}: {len(images_1203)} originales + {total_generated} augmentées = {len(images_1203) + total_generated}")
    print("="*70)
    
    return total_generated

if __name__ == "__main__":
    input_dir = r"C:\Users\abdel\OneDrive\Documents\GitHub\Projet-Innov-Siana\MATRICULE_abdellah\datta\matricule TGV"
    output_dir = input_dir  # Sauvegarder dans le même dossier
    
    count = augment_matricule_1203(input_dir, output_dir)
    
    if count > 0:
        print("\nMaintenant réentraînez le modèle:")
        print("  python train_robust_model.py")
        print("\nLe modèle aura beaucoup plus d'exemples de 1203!")
