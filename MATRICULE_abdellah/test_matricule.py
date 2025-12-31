"""
SCRIPT DE TEST SIMPLE POUR MATRICULES
======================================
Utilise le module intégré matricule_detector.py pour tester n'importe quelle image

Usage:
    python test_matricule.py                          # Test sur boraq.jpeg par défaut
    python test_matricule.py chemin/vers/image.jpg    # Test sur image spécifique
    python test_matricule.py boraq.jpeg 1207          # Test avec validation
"""

import sys
import os
from matricule_detector import MatriculeDetector

def main():
    # Arguments
    if len(sys.argv) > 1:
        image_name = sys.argv[1]
    else:
        image_name = "boraq.jpeg"
    
    # Matricule attendu (optionnel)
    true_matricule = sys.argv[2] if len(sys.argv) > 2 else None
    
    # Chemin complet
    if os.path.isabs(image_name):
        image_path = image_name
    else:
        # Chercher dans images_brutes
        images_dir = r"C:\Users\abdel\OneDrive\Documents\GitHub\Projet-Innov-Siana\MATRICULE_abdellah\datta\images_brutes"
        image_path = os.path.join(images_dir, image_name)
    
    # Vérifier existence
    if not os.path.exists(image_path):
        print(f"❌ Image non trouvée: {image_path}")
        print(f"\nUtilisation:")
        print(f"  python test_matricule.py                          # Test sur boraq.jpeg")
        print(f"  python test_matricule.py image.jpg                # Test sur image.jpg")
        print(f"  python test_matricule.py image.jpg 1207           # Test avec validation")
        return
    
    # Créer le détecteur et tester
    detector = MatriculeDetector()
    result = detector.test_on_image(image_path, true_matricule)
    
    # Retourner code de sortie
    if 'error' in result:
        sys.exit(1)
    elif true_matricule and result['matricule'] != true_matricule:
        sys.exit(1)
    else:
        sys.exit(0)

if __name__ == "__main__":
    main()
