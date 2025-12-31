"""
RETRAITEMENT VIDÉO AVEC ANNOTATIONS
====================================
Utilise les annotations manuelles pour retraiter la vidéo
"""

import cv2
import json
import numpy as np
from matricule_detector import MatriculeDetector
import os

def process_video_with_annotations(video_path, annotations_file, output_path=None):
    """
    Retraite la vidéo en utilisant les annotations pour guider la détection
    """
    # Charger annotations
    with open(annotations_file, 'r') as f:
        data = json.load(f)
    
    annotations = data['annotations']
    annotated_frames = {ann['frame']: ann for ann in annotations}
    
    # Calculer la bbox moyenne des annotations valides
    valid_bboxes = [ann['bbox'] for ann in annotations if ann['bbox'][2] > 10 and ann['bbox'][3] > 10]
    
    if not valid_bboxes:
        print("❌ Aucune bbox valide trouvée dans les annotations")
        print("Les annotations ont toutes des dimensions trop petites")
        return
    
    # Moyenne des positions
    avg_x = int(np.mean([b[0] for b in valid_bboxes]))
    avg_y = int(np.mean([b[1] for b in valid_bboxes]))
    avg_w = int(np.mean([b[2] for b in valid_bboxes]))
    avg_h = int(np.mean([b[3] for b in valid_bboxes]))
    
    print(f"Bbox moyenne calculée: x={avg_x}, y={avg_y}, w={avg_w}, h={avg_h}")
    
    # Matricule attendu
    expected_matricule = annotations[0]['matricule']
    print(f"Matricule attendu: {expected_matricule}")
    
    # Charger le détecteur
    detector = MatriculeDetector()
    
    # Ouvrir la vidéo
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Impossible d'ouvrir la vidéo: {video_path}")
        return
    
    # Infos vidéo
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"\n{'='*70}")
    print(f"RETRAITEMENT VIDÉO")
    print(f"{'='*70}")
    print(f"Résolution: {width}x{height}")
    print(f"FPS: {fps}")
    print(f"Total frames: {total_frames}")
    print(f"{'='*70}\n")
    
    # Préparer sortie
    if output_path is None:
        output_path = "result_video_corrected.mp4"
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Traiter
    frame_idx = 0
    detections = []
    
    print("Traitement en cours...")
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_idx += 1
        
        # Utiliser la bbox moyenne pour extraire le ROI
        x, y, w, h = avg_x, avg_y, avg_w, avg_h
        
        # Vérifier que la bbox est dans les limites
        if x >= 0 and y >= 0 and x+w <= width and y+h <= height:
            # Extraire ROI
            roi = frame[y:y+h, x:x+w]
            
            if roi.size > 0:
                # Reconnaître
                recognition = detector.recognize_roi(roi)
                matricule = recognition['matricule']
                confidence = recognition['confidence']
                
                # Annoter
                cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 3)
                
                text = f"{matricule} ({confidence:.0f}%)"
                cv2.putText(frame, text, (x, y-10), 
                           cv2.FONT_HERSHEY_SIMPLEX, 1.0, (0, 255, 0), 3)
                
                # Statistiques
                if frame_idx % 10 == 0:
                    detections.append({
                        'frame': frame_idx,
                        'matricule': matricule,
                        'confidence': confidence
                    })
                    print(f"Frame {frame_idx}/{total_frames} - {matricule} ({confidence:.0f}%)")
        
        out.write(frame)
        
        if frame_idx % 30 == 0:
            progress = (frame_idx / total_frames) * 100
            print(f"Progression: {progress:.1f}%")
    
    cap.release()
    out.release()
    
    # Résultats
    print("\n" + "="*70)
    print("RÉSULTATS")
    print("="*70)
    
    if detections:
        from collections import Counter
        matricules = [d['matricule'] for d in detections]
        counter = Counter(matricules)
        most_common = counter.most_common(3)
        
        print(f"Détections: {len(detections)}")
        print(f"\nMatricules détectés:")
        for mat, count in most_common:
            percentage = (count / len(matricules)) * 100
            print(f"  {mat}: {count} fois ({percentage:.1f}%)")
        
        avg_conf = np.mean([d['confidence'] for d in detections])
        print(f"\nConfiance moyenne: {avg_conf:.1f}%")
        print(f"Matricule le plus probable: {most_common[0][0]}")
        
        if most_common[0][0] == expected_matricule:
            print(f"✓ Correspond au matricule attendu: {expected_matricule}")
        else:
            print(f"⚠ Différent du matricule attendu: {expected_matricule}")
    
    print(f"\n✓ Vidéo annotée: {output_path}")
    print("="*70)

if __name__ == "__main__":
    video_path = r"C:\Users\abdel\OneDrive\Documents\GitHub\Projet-Innov-Siana\MATRICULE_abdellah\video entrainement OCR.mp4"
    annotations_file = "video_annotations.json"
    
    if os.path.exists(annotations_file):
        process_video_with_annotations(video_path, annotations_file)
    else:
        print(f"❌ Fichier d'annotations non trouvé: {annotations_file}")
        print("Lancez d'abord: python annotate_video_multiple.py")
