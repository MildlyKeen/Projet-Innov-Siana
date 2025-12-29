"""
Script pour analyser les données disponibles
"""
import cv2
import os
from pathlib import Path

def analyze_images():
    """Analyser les images de trains"""
    
    # Lister toutes les images
    image_files = [f for f in os.listdir('.') if f.endswith(('.jpg', '.jpeg', '.png'))]
    
    print(f"{'='*60}")
    print(f"ANALYSE DES DONNÉES")
    print(f"{'='*60}\n")
    
    print(f"Nombre total d'images: {len(image_files)}\n")
    
    # Analyser quelques images
    print("Analyse d'un échantillon d'images:\n")
    
    resolutions = {}
    total_size = 0
    
    for i, img_file in enumerate(image_files[:10]):
        img = cv2.imread(img_file)
        if img is not None:
            h, w, c = img.shape
            size_mb = os.path.getsize(img_file) / (1024*1024)
            total_size += size_mb
            
            resolution = f"{w}x{h}"
            resolutions[resolution] = resolutions.get(resolution, 0) + 1
            
            # Analyser luminosité moyenne
            gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
            brightness = gray.mean()
            
            print(f"{i+1}. {img_file[:40]:40}")
            print(f"   Résolution: {w}x{h}, Luminosité: {brightness:.1f}, Taille: {size_mb:.2f} MB")
    
    print(f"\n{'='*60}")
    print("STATISTIQUES")
    print(f"{'='*60}")
    print(f"Taille moyenne: {total_size/min(10, len(image_files)):.2f} MB")
    print(f"\nRésolutions trouvées:")
    for res, count in sorted(resolutions.items(), key=lambda x: x[1], reverse=True):
        print(f"  - {res}: {count} images")
    
    print(f"\n{'='*60}")
    print("RECOMMANDATIONS")
    print(f"{'='*60}")
    print("1. Tester le pipeline OCR sur quelques images")
    print("2. Vérifier si les numéros de wagons sont visibles")
    print("3. Ajuster le pattern regex dans config.py selon les vrais formats")
    print("4. Optimiser les paramètres de prétraitement")
    
    return image_files

if __name__ == "__main__":
    analyze_images()
