"""
TEST DE DÉTECTION DE MATRICULES SUR VIDÉO
==========================================
Traite une vidéo frame par frame et détecte les matricules

Usage:
    python test_video.py                              # Traite "video entrainement OCR.mp4"
    python test_video.py chemin/vers/video.mp4        # Traite une vidéo spécifique
"""

import sys
import os
import cv2
import numpy as np
from matricule_detector import MatriculeDetector
from collections import Counter

def process_video(video_path: str, output_path: str = None, skip_frames: int = 5):
    """
    Traite une vidéo et détecte les matricules
    
    Args:
        video_path: Chemin vers la vidéo
        output_path: Chemin de sortie (optionnel)
        skip_frames: Ne traiter qu'une frame sur N (pour accélérer)
    """
    # Vérifier existence
    if not os.path.exists(video_path):
        print(f"❌ Vidéo non trouvée: {video_path}")
        return
    
    # Charger le détecteur
    print("Chargement du détecteur...")
    detector = MatriculeDetector()
    
    # Ouvrir la vidéo
    cap = cv2.VideoCapture(video_path)
    if not cap.isOpened():
        print(f"❌ Impossible d'ouvrir la vidéo: {video_path}")
        return
    
    # Informations vidéo
    fps = int(cap.get(cv2.CAP_PROP_FPS))
    width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
    height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
    total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
    
    print(f"\n{'='*70}")
    print(f"TRAITEMENT VIDÉO: {os.path.basename(video_path)}")
    print(f"{'='*70}")
    print(f"Résolution: {width}x{height}")
    print(f"FPS: {fps}")
    print(f"Total frames: {total_frames}")
    print(f"Durée: {total_frames/fps:.1f}s")
    print(f"Skip: 1 frame sur {skip_frames}")
    print(f"{'='*70}\n")
    
    # Préparer sortie vidéo
    if output_path is None:
        output_path = f"result_{os.path.basename(video_path)}"
    
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
    
    # Statistiques
    detections = []
    matricules_found = []
    frame_idx = 0
    processed_frames = 0
    
    print("Traitement en cours...")
    print("-" * 70)
    
    while True:
        ret, frame = cap.read()
        if not ret:
            break
        
        frame_idx += 1
        
        # Traiter seulement certaines frames
        if frame_idx % skip_frames != 0:
            out.write(frame)
            continue
        
        processed_frames += 1
        
        # Sauvegarder temporairement la frame
        temp_frame_path = "temp_frame.jpg"
        cv2.imwrite(temp_frame_path, frame)
        
        # Détecter le matricule
        result = detector.detect_and_recognize(temp_frame_path, use_manual=False, use_mser=True, visualize=False)
        
        # Annoter la frame
        if 'error' not in result and result['matricule']:
            x, y, w, h = result['bbox']
            matricule = result['matricule']
            confidence = result['confidence']
            
            # Rectangle vert
            cv2.rectangle(frame, (x, y), (x+w, y+h), (0, 255, 0), 2)
            
            # Texte
            text = f"{matricule} ({confidence:.0f}%)"
            cv2.putText(frame, text, (x, y-10), cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 255, 0), 2)
            
            # Enregistrer
            detections.append({
                'frame': frame_idx,
                'time': frame_idx / fps,
                'matricule': matricule,
                'confidence': confidence
            })
            matricules_found.append(matricule)
            
            # Afficher
            if processed_frames % 10 == 0:
                print(f"Frame {frame_idx}/{total_frames} - Matricule: {matricule} ({confidence:.0f}%)")
        
        # Écrire la frame annotée
        out.write(frame)
        
        # Progress bar
        if frame_idx % 30 == 0:
            progress = (frame_idx / total_frames) * 100
            print(f"Progression: {progress:.1f}% ({frame_idx}/{total_frames} frames)")
    
    # Nettoyer
    cap.release()
    out.release()
    if os.path.exists("temp_frame.jpg"):
        os.remove("temp_frame.jpg")
    
    # Résultats
    print("\n" + "="*70)
    print("RÉSULTATS")
    print("="*70)
    print(f"Frames traitées: {processed_frames}/{total_frames}")
    print(f"Détections: {len(detections)}")
    
    if matricules_found:
        # Matricule le plus fréquent
        counter = Counter(matricules_found)
        most_common = counter.most_common(3)
        
        print(f"\nMatricules détectés:")
        for matricule, count in most_common:
            percentage = (count / len(matricules_found)) * 100
            print(f"  {matricule}: {count} fois ({percentage:.1f}%)")
        
        print(f"\nMatricule le plus probable: {most_common[0][0]}")
        
        # Confiance moyenne
        avg_confidence = np.mean([d['confidence'] for d in detections])
        print(f"Confiance moyenne: {avg_confidence:.1f}%")
        
        # Timeline des détections
        print(f"\nDétections par intervalle:")
        for i in range(0, int(total_frames / fps) + 1, 5):
            detections_in_interval = [d for d in detections if i <= d['time'] < i+5]
            if detections_in_interval:
                matricules_in_interval = [d['matricule'] for d in detections_in_interval]
                most_common_in_interval = Counter(matricules_in_interval).most_common(1)[0]
                print(f"  {i:3d}-{i+5:3d}s: {most_common_in_interval[0]} ({most_common_in_interval[1]} détections)")
    else:
        print("\n❌ Aucun matricule détecté")
    
    print(f"\n✓ Vidéo annotée sauvegardée: {output_path}")
    print("="*70)

def main():
    # Arguments
    if len(sys.argv) > 1:
        video_path = sys.argv[1]
    else:
        video_path = r"C:\Users\abdel\OneDrive\Documents\GitHub\Projet-Innov-Siana\MATRICULE_abdellah\video entrainement OCR.mp4"
    
    # Skip frames (optionnel)
    skip_frames = int(sys.argv[2]) if len(sys.argv) > 2 else 5
    
    # Traiter
    process_video(video_path, skip_frames=skip_frames)

if __name__ == "__main__":
    main()
