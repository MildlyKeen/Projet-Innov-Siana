"""
NETTOYAGE DU PROJET
===================
Supprime les fichiers temporaires et inutiles
"""

import os
import shutil

def cleanup_project():
    """Supprime les fichiers inutiles"""
    
    base_dir = r"C:\Users\abdel\OneDrive\Documents\GitHub\Projet-Innov-Siana\MATRICULE_abdellah"
    
    # Fichiers à garder (essentiels)
    keep_files = {
        # Modules principaux
        'matricule_detector.py',  # Module principal intégré
        'test_matricule.py',      # Test sur images
        'test_video.py',          # Test sur vidéos
        'train_robust_model.py',  # Entraînement
        'augment_data.py',        # Augmentation données
        'extract_video_rois.py',  # Extraction ROIs
        'annotate_video_tk.py',   # Outil annotation
        'reprocess_video.py',     # Traitement vidéo
        
        # Modules OCR originaux
        'config.py',
        'preprocessing.py',
        'ocr_module.py',
        'integration.py',
        
        # Documentation
        'README.md',
        'requirements.txt',
        'PROJET_FINALISE.md',
        'RAPPORT_LIVRAISON.md',
        
        # Vidéos importantes
        'video entrainement OCR.mp4',
        'result_video_corrected.mp4',
        'video_annotations.json',
        
        # Config web
        'package.json',
        'vite.config.js',
        'eslint.config.js',
        'index.html',
    }
    
    # Dossiers à garder
    keep_dirs = {
        '.venv', 'datta', 'models', 'src', 'public', 'yolo', '__pycache__'
    }
    
    # Fichiers à supprimer (patterns)
    delete_patterns = [
        'annotate_tool.py',
        'annotate_tool_web.py',
        'annotate_video.py',
        'annotate_video_multiple.py',
        'annotate_video_simple.py',
        'annotate_video_web.py',
        'annotate_manual_coords.py',
        
        'test_boraq.py',
        'test_digit_boraq.py',
        'test_easyocr.py',
        'test_final.py',
        'test_final_pipeline.py',
        'test_installation.py',
        'test_model_boraq.py',
        'test_ocr_real.py',
        'test_raw_ocr.py',
        'test_robust_boraq.py',
        'test_simple_boraq.py',
        'test_ultra_simple.py',
        'test_video_frame.py',
        'test_with_annotation.py',
        
        'train_digit_model.py',
        'train_matricule_model.py',
        'train_model_custom.py',
        'train_region_detector.py',
        
        'extract_annotated_rois.py',
        'extract_early_frames.py',
        'extract_frames.py',
        'extract_more_frames.py',
        
        'analyze_data.py',
        'check_annotations.py',
        'detect_and_recognize.py',
        'find_1207.py',
        'show_1207_training.py',
        
        'demo.py',
        'demo_pro.py',
        'DEMARRAGE_RAPIDE.py',
        'examples.py',
        
        # Images temporaires
        'boraq_*.jpg',
        'digit_*.jpg',
        'roi_*.jpg',
        'train_*.jpg',
        'result_boraq.jpeg',
        'result_frame_*.jpg',
        'result_images*.jpg',
        'result_les-trains*.jpg',
        
        # Ancienne vidéo
        'result_video entrainement OCR.mp4',
    ]
    
    # Dossiers temporaires
    delete_dirs = [
        'video_frames',
        'video_frames_annotate',
    ]
    
    print("\n" + "="*70)
    print("NETTOYAGE DU PROJET")
    print("="*70)
    print(f"Dossier: {base_dir}\n")
    
    deleted_files = 0
    deleted_dirs = 0
    
    # Supprimer fichiers
    print("Fichiers à supprimer:")
    for pattern in delete_patterns:
        if '*' in pattern:
            # Pattern avec wildcard
            import glob
            matches = glob.glob(os.path.join(base_dir, pattern))
            for filepath in matches:
                if os.path.isfile(filepath):
                    try:
                        os.remove(filepath)
                        print(f"  ✓ {os.path.basename(filepath)}")
                        deleted_files += 1
                    except Exception as e:
                        print(f"  ❌ {os.path.basename(filepath)}: {e}")
        else:
            filepath = os.path.join(base_dir, pattern)
            if os.path.exists(filepath):
                try:
                    os.remove(filepath)
                    print(f"  ✓ {pattern}")
                    deleted_files += 1
                except Exception as e:
                    print(f"  ❌ {pattern}: {e}")
    
    # Supprimer dossiers
    print("\nDossiers à supprimer:")
    for dirname in delete_dirs:
        dirpath = os.path.join(base_dir, dirname)
        if os.path.exists(dirpath):
            try:
                shutil.rmtree(dirpath)
                print(f"  ✓ {dirname}/")
                deleted_dirs += 1
            except Exception as e:
                print(f"  ❌ {dirname}/: {e}")
    
    print("\n" + "="*70)
    print(f"✓ Nettoyage terminé!")
    print(f"  {deleted_files} fichiers supprimés")
    print(f"  {deleted_dirs} dossiers supprimés")
    print("="*70)
    
    print("\nFichiers essentiels conservés:")
    print("  - matricule_detector.py (module principal)")
    print("  - test_matricule.py (test images)")
    print("  - test_video.py (test vidéos)")
    print("  - train_robust_model.py (entraînement)")
    print("  - annotate_video_tk.py (annotation)")
    print("  - result_video_corrected.mp4 (résultat final)")
    print("  - models/ (modèles entraînés)")
    print("  - datta/ (données)")

if __name__ == "__main__":
    response = input("Êtes-vous sûr de vouloir supprimer les fichiers inutiles? (oui/non): ")
    if response.lower() in ['oui', 'o', 'yes', 'y']:
        cleanup_project()
    else:
        print("Nettoyage annulé")
