"""
EXTRACTION DES ROI DE LA VIDÉO POUR ENTRAÎNEMENT
=================================================
Extrait les ROIs annotées de la vidéo et les ajoute au dataset d'entraînement
"""

import cv2
import json
import os

def extract_video_rois(video_path, annotations_file, output_dir):
    """Extrait les ROIs annotées et les sauvegarde"""
    
    # Charger annotations
    with open(annotations_file, 'r') as f:
        data = json.load(f)
    
    annotations = data['annotations']
    video_name = os.path.splitext(os.path.basename(video_path))[0]
    
    print("\n" + "="*70)
    print("EXTRACTION DES ROI DE LA VIDÉO")
    print("="*70)
    print(f"Vidéo: {video_name}")
    print(f"Annotations: {len(annotations)}")
    print("="*70 + "\n")
    
    os.makedirs(output_dir, exist_ok=True)
    
    cap = cv2.VideoCapture(video_path)
    extracted_count = 0
    
    for ann in annotations:
        frame_num = ann['frame']
        bbox = ann['bbox']
        matricule = ann['matricule']
        
        # Charger la frame
        cap.set(cv2.CAP_PROP_POS_FRAMES, frame_num)
        ret, frame = cap.read()
        
        if not ret:
            print(f"❌ Impossible de charger frame {frame_num}")
            continue
        
        # Extraire ROI
        x, y, w, h = bbox
        roi = frame[y:y+h, x:x+w]
        
        if roi.size == 0:
            print(f"❌ ROI vide pour frame {frame_num}")
            continue
        
        # Sauvegarder avec le format: XXXX_video_frameNN.jpg
        output_filename = f"{matricule}_video_frame{frame_num:03d}.jpg"
        output_path = os.path.join(output_dir, output_filename)
        
        cv2.imwrite(output_path, roi)
        extracted_count += 1
        
        print(f"✓ Extrait: {output_filename} ({w}x{h})")
    
    cap.release()
    
    print("\n" + "="*70)
    print(f"✓ {extracted_count} ROI extraites dans {output_dir}/")
    print("Réentraînez le modèle avec: python train_robust_model.py")
    print("="*70)

if __name__ == "__main__":
    video_path = r"C:\Users\abdel\OneDrive\Documents\GitHub\Projet-Innov-Siana\MATRICULE_abdellah\video entrainement OCR.mp4"
    annotations_file = "video_annotations.json"
    output_dir = r"C:\Users\abdel\OneDrive\Documents\GitHub\Projet-Innov-Siana\MATRICULE_abdellah\datta\matricule TGV"
    
    if os.path.exists(annotations_file):
        extract_video_rois(video_path, annotations_file, output_dir)
    else:
        print(f"❌ Fichier d'annotations non trouvé: {annotations_file}")
