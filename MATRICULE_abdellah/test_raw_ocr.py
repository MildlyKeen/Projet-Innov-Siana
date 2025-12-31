"""
Test OCR brut - voir TOUS les textes detectes sans filtrage
"""
import cv2
import os
import sys

# Fix encoding pour Windows
sys.stdout.reconfigure(encoding='utf-8')

from paddleocr import PaddleOCR

def test_raw_ocr():
    """Test OCR brut sans filtrage"""
    
    # Images à tester
    image_files = [f for f in os.listdir('.') if f.endswith('.jpg')][:5]
    
    print("="*60)
    print("TEST OCR BRUT (sans filtrage)")
    print("="*60)
    
    # Initialiser OCR
    print("\nInitialisation PaddleOCR...")
    ocr = PaddleOCR(use_angle_cls=True, lang='en')
    print("✓ OCR prêt\n")
    
    for i, img_file in enumerate(image_files):
        print(f"\n{'='*60}")
        print(f"Image {i+1}: {img_file}")
        print(f"{'='*60}")
        
        # Charger image
        img = cv2.imread(img_file)
        if img is None:
            print("  ✗ Erreur de chargement")
            continue
        
        print(f"  Résolution: {img.shape[1]}x{img.shape[0]}")
        
        # Convertir RGB
        img_rgb = cv2.cvtColor(img, cv2.COLOR_BGR2RGB)
        
        # OCR brut
        try:
            result = ocr.ocr(img_rgb)
            
            if result is None or len(result) == 0 or result[0] is None:
                print("  - Aucun texte détecté")
                continue
            
            print(f"  ✓ {len(result[0])} élément(s) détecté(s):\n")
            
            for j, line in enumerate(result[0]):
                print(f"    DEBUG - Structure de line: {type(line)}, length: {len(line)}")
                print(f"    DEBUG - line[0]: {type(line[0])}")
                print(f"    DEBUG - line[1]: {type(line[1])}, value: {line[1]}")
                
                bbox = line[0]
                text = line[1]
                conf = 1.0  # Par défaut si pas disponible
                
                # Position du bbox
                x_min = int(min(p[0] for p in bbox))
                y_min = int(min(p[1] for p in bbox))
                
                print(f"    {j+1}. Texte: '{text}'")
                print(f"       Confiance: {conf:.2%}")
                print(f"       Position: ({x_min}, {y_min})")
                print()
                
        except Exception as e:
            print(f"  ✗ Erreur OCR: {e}")
            import traceback
            traceback.print_exc()
    
    print(f"\n{'='*60}")
    print("ANALYSE COMPLÉTÉE")
    print(f"{'='*60}")
    print("\n💡 Observations:")
    print("  - Si vous voyez des numéros, ajustez le regex dans config.py")
    print("  - Si pas de texte, les images peuvent ne pas contenir de numéros visibles")
    print("  - Testez avec des images de meilleure qualité ou avec numéros plus grands")

if __name__ == "__main__":
    test_raw_ocr()
