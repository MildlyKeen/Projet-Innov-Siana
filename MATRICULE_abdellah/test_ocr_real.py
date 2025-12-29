"""
Test du pipeline OCR sur les vraies images de trains
"""
import cv2
import os
import sys
from pathlib import Path

# Vérifier si les modules sont installés
try:
    from preprocessing import VideoPreprocessor
    from ocr_module import TrainOCR
    from integration import DetectionOCRInterface
    print("✓ Modules importés avec succès\n")
except ImportError as e:
    print(f"Erreur d'import: {e}")
    print("Veuillez installer les dépendances: pip install -r requirements.txt")
    sys.exit(1)

def test_ocr_on_images(num_images=5):
    """Tester l'OCR sur quelques images"""
    
    # Lister les images
    image_files = [f for f in os.listdir('.') if f.endswith(('.jpg', '.jpeg', '.png'))]
    
    if not image_files:
        print("Aucune image trouvée!")
        return
    
    print(f"{'='*60}")
    print(f"TEST OCR SUR {min(num_images, len(image_files))} IMAGES")
    print(f"{'='*60}\n")
    
    # Initialiser l'interface (cela peut prendre du temps pour télécharger les modèles)
    print("Initialisation de l'OCR (peut prendre 1-2 minutes au premier lancement)...")
    try:
        interface = DetectionOCRInterface()
        print("✓ OCR initialisé\n")
    except Exception as e:
        print(f"Erreur d'initialisation: {e}")
        print("\nPour installer PaddleOCR:")
        print("  pip install paddleocr paddlepaddle")
        return
    
    # Tester sur quelques images
    results_summary = []
    
    for i, img_file in enumerate(image_files[:num_images]):
        print(f"\n{'='*60}")
        print(f"Image {i+1}/{num_images}: {img_file}")
        print(f"{'='*60}")
        
        # Charger l'image
        frame = cv2.imread(img_file)
        if frame is None:
            print(f"  ✗ Impossible de charger l'image")
            continue
        
        print(f"  Résolution: {frame.shape[1]}x{frame.shape[0]}")
        
        try:
            # Détecter et lire
            ocr_results = interface.detect_and_read(frame)
            
            if ocr_results:
                print(f"  ✓ {len(ocr_results)} numéro(s) détecté(s):")
                for j, result in enumerate(ocr_results):
                    print(f"     {j+1}. Wagon ID: {result['wagon_id']}")
                    print(f"        Confiance: {result['confidence']:.2%}")
                    print(f"        Position: {result['bbox']}")
                    if 'raw_text' in result:
                        print(f"        Texte brut: {result['raw_text']}")
                
                results_summary.append({
                    'file': img_file,
                    'count': len(ocr_results),
                    'ids': [r['wagon_id'] for r in ocr_results]
                })
            else:
                print(f"  - Aucun numéro détecté")
                results_summary.append({
                    'file': img_file,
                    'count': 0,
                    'ids': []
                })
            
            # Sauvegarder l'image annotée
            preprocessor = interface.pipeline.preprocessor
            annotated = interface.pipeline._annotate_frame(frame.copy(), ocr_results)
            output_file = f"test_result_{i+1}_{Path(img_file).stem}.jpg"
            cv2.imwrite(output_file, annotated)
            print(f"  💾 Sauvegardé: {output_file}")
            
        except Exception as e:
            print(f"  ✗ Erreur: {e}")
            import traceback
            traceback.print_exc()
    
    # Résumé final
    print(f"\n{'='*60}")
    print("RÉSUMÉ DES TESTS")
    print(f"{'='*60}")
    
    total_detections = sum(r['count'] for r in results_summary)
    images_with_detections = sum(1 for r in results_summary if r['count'] > 0)
    
    print(f"Images testées: {len(results_summary)}")
    print(f"Images avec détections: {images_with_detections}")
    print(f"Total de numéros détectés: {total_detections}")
    
    if total_detections > 0:
        print(f"\nNuméros trouvés:")
        all_ids = []
        for r in results_summary:
            all_ids.extend(r['ids'])
        unique_ids = set(all_ids)
        for wagon_id in unique_ids:
            count = all_ids.count(wagon_id)
            print(f"  - {wagon_id} ({count}x)")
    
    print(f"\n{'='*60}")
    print("PROCHAINES ÉTAPES")
    print(f"{'='*60}")
    
    if total_detections == 0:
        print("❌ Aucun numéro détecté. Raisons possibles:")
        print("   1. Les images ne contiennent pas de numéros visibles")
        print("   2. Le pattern regex est trop strict (config.py)")
        print("   3. Les numéros sont dans un format non standard")
        print("   4. La qualité d'image nécessite plus de prétraitement")
        print("\n💡 Recommandations:")
        print("   - Vérifiez manuellement si les images ont des numéros")
        print("   - Ajustez WAGON_ID_PATTERN dans config.py")
        print("   - Réduisez OCR_CONFIDENCE_THRESHOLD dans config.py")
    else:
        print("✅ Détections réussies!")
        print("\n💡 Pour améliorer:")
        print("   - Ajustez le pattern regex selon les formats trouvés")
        print("   - Optimisez les paramètres de prétraitement")
        print("   - Testez sur plus d'images")
    
    return results_summary

if __name__ == "__main__":
    import sys
    
    # Nombre d'images à tester (défaut: 5)
    num_images = int(sys.argv[1]) if len(sys.argv) > 1 else 5
    
    test_ocr_on_images(num_images)
