"""
Version professionnelle du pipeline OCR avec visualisation avancee
Conforme aux specifications du cahier des charges Membre 2
"""
import cv2
import numpy as np
from typing import List, Dict, Tuple
import os
from preprocessing import VideoPreprocessor
from ocr_module import TrainOCR
import config


class ProfessionalOCRPipeline:
    """Pipeline OCR professionnel avec visualisation avancee"""
    
    def __init__(self):
        self.preprocessor = VideoPreprocessor()
        self.ocr = TrainOCR()
        self.frame_count = 0
        self.total_detections = 0
        self.detection_history = []
        
    def add_professional_overlay(self, frame: np.ndarray, 
                                 ocr_results: List[Dict],
                                 frame_num: int,
                                 fps: int,
                                 processing_info: Dict) -> np.ndarray:
        """Ajouter overlay professionnel sur la frame"""
        overlay = frame.copy()
        h, w = frame.shape[:2]
        
        # 1. Barre d'information superieure (fond semi-transparent)
        cv2.rectangle(overlay, (0, 0), (w, 100), (0, 0, 0), -1)
        frame = cv2.addWeighted(frame, 0.7, overlay, 0.3, 0)
        
        # Titre
        cv2.putText(frame, "PIPELINE OCR - DETECTION NUMEROS WAGONS", 
                   (20, 35), cv2.FONT_HERSHEY_DUPLEX, 1.2, (0, 255, 0), 3)
        
        # Informations frame
        info_text = f"Frame: {frame_num} | FPS: {fps} | Detections: {len(ocr_results)}"
        cv2.putText(frame, info_text, (20, 70), 
                   cv2.FONT_HERSHEY_SIMPLEX, 0.8, (255, 255, 255), 2)
        
        # 2. Panel lateral droit avec statistiques
        panel_x = w - 350
        cv2.rectangle(frame, (panel_x, 0), (w, h), (0, 0, 0), -1)
        frame = cv2.addWeighted(frame, 0.85, overlay, 0.15, 0)
        
        # Titre panel
        cv2.putText(frame, "STATISTIQUES", (panel_x + 20, 40),
                   cv2.FONT_HERSHEY_DUPLEX, 0.7, (0, 255, 255), 2)
        
        y_pos = 80
        
        # Statistiques
        stats = [
            f"Total detect: {self.total_detections}",
            f"Wagons uniques: {len(set(self.detection_history))}",
            f"",
            "PREPROCESSING:",
            f"Perspective: {'ON' if config.PERSPECTIVE_CORRECTION_ENABLED else 'OFF'}",
            f"Stabilisation: {'ON' if config.STABILIZATION_ENABLED else 'OFF'}",
            f"Enhancement: {'ON' if config.CONTRAST_ENHANCEMENT else 'OFF'}",
            f"",
            "OCR:",
            f"Confiance min: {config.OCR_CONFIDENCE_THRESHOLD:.0%}",
            f"Langue: {config.OCR_LANGUAGE}",
        ]
        
        for stat in stats:
            if stat == "":
                y_pos += 15
                continue
            color = (255, 255, 255) if not stat.startswith(('PREPROCESSING', 'OCR')) else (0, 255, 255)
            cv2.putText(frame, stat, (panel_x + 20, y_pos),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.5, color, 1)
            y_pos += 25
        
        # 3. Detections actuelles (si presentes)
        if ocr_results:
            y_pos += 20
            cv2.putText(frame, "DETECTIONS:", (panel_x + 20, y_pos),
                       cv2.FONT_HERSHEY_DUPLEX, 0.6, (0, 255, 0), 2)
            y_pos += 30
            
            for i, result in enumerate(ocr_results[:5]):  # Max 5
                wagon_id = result['wagon_id']
                conf = result['confidence']
                text = f"{wagon_id}"
                cv2.putText(frame, text, (panel_x + 25, y_pos),
                           cv2.FONT_HERSHEY_SIMPLEX, 0.6, (0, 255, 0), 2)
                y_pos += 25
                
                # Barre de confiance
                bar_width = int(250 * conf)
                cv2.rectangle(frame, (panel_x + 25, y_pos - 8), 
                            (panel_x + 25 + bar_width, y_pos + 2),
                            (0, 255, 0), -1)
                cv2.rectangle(frame, (panel_x + 25, y_pos - 8), 
                            (panel_x + 275, y_pos + 2),
                            (100, 100, 100), 1)
                y_pos += 15
        
        # 4. Annotations sur l'image pour chaque detection
        for result in ocr_results:
            x, y, w_box, h_box = result['bbox']
            wagon_id = result['wagon_id']
            conf = result['confidence']
            
            # Rectangle autour de la detection
            cv2.rectangle(frame, (x, y), (x + w_box, y + h_box), (0, 255, 0), 3)
            
            # Label avec fond
            label = f"{wagon_id} ({conf:.0%})"
            (text_w, text_h), baseline = cv2.getTextSize(
                label, cv2.FONT_HERSHEY_SIMPLEX, 0.8, 2)
            
            cv2.rectangle(frame, (x, y - text_h - 15), 
                         (x + text_w + 10, y), (0, 255, 0), -1)
            cv2.putText(frame, label, (x + 5, y - 8),
                       cv2.FONT_HERSHEY_SIMPLEX, 0.8, (0, 0, 0), 2)
            
            # Indicateur de confiance (cercle)
            color = (0, 255, 0) if conf > 0.8 else (0, 255, 255) if conf > 0.6 else (0, 165, 255)
            cv2.circle(frame, (x + w_box - 15, y + 15), 10, color, -1)
        
        # 5. Barre de progression en bas
        progress = (frame_num / processing_info.get('total_frames', frame_num)) if processing_info.get('total_frames') else 0
        bar_width = int(w * progress)
        cv2.rectangle(frame, (0, h - 10), (bar_width, h), (0, 255, 0), -1)
        cv2.rectangle(frame, (0, h - 10), (w, h), (255, 255, 255), 2)
        
        # 6. Watermark
        cv2.putText(frame, "OCR Pipeline v1.0 - Membre 2", (20, h - 20),
                   cv2.FONT_HERSHEY_SIMPLEX, 0.5, (150, 150, 150), 1)
        
        return frame
    
    def process_video_professional(self, input_path: str, output_path: str) -> Dict:
        """Traiter video avec sortie professionnelle"""
        
        print("\n" + "="*70)
        print("PIPELINE OCR PROFESSIONNEL - TRAITEMENT VIDEO")
        print("="*70)
        
        # Ouvrir video
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"Impossible d'ouvrir: {input_path}")
        
        # Proprietes video
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        print(f"\nVideo d'entree: {input_path}")
        print(f"Resolution: {width}x{height} | FPS: {fps} | Frames: {total_frames}")
        
        # Creer video de sortie
        fourcc = cv2.VideoWriter_fourcc(*'mp4v')
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # Statistiques
        stats = {
            'total_frames': total_frames,
            'processed_frames': 0,
            'total_detections': 0,
            'unique_wagons': set()
        }
        
        print("\nTraitement en cours...")
        print("-" * 70)
        
        frame_num = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_num += 1
            self.frame_count = frame_num
            
            # Pretraitement
            preprocessed = self.preprocessor.preprocess_frame(frame)
            
            # Detection simple des regions (en attendant YOLO du Membre 1)
            from preprocessing import detect_train_region
            bboxes = detect_train_region(preprocessed)
            
            # OCR sur les regions detectees
            ocr_results = []
            for bbox in bboxes[:10]:  # Limite a 10 regions max
                result = self.ocr.process_roi(preprocessed, bbox)
                if result:
                    ocr_results.append(result)
                    self.total_detections += 1
                    stats['total_detections'] += 1
                    stats['unique_wagons'].add(result['wagon_id'])
                    self.detection_history.append(result['wagon_id'])
            
            # Ajouter overlay professionnel
            frame_annotated = self.add_professional_overlay(
                frame, ocr_results, frame_num, fps, stats)
            
            # Ecrire frame
            out.write(frame_annotated)
            stats['processed_frames'] += 1
            
            # Afficher progression
            if frame_num % 30 == 0:
                progress = (frame_num / total_frames) * 100
                print(f"Progression: {progress:.1f}% ({frame_num}/{total_frames}) | "
                      f"Detections: {stats['total_detections']}", end='\r')
        
        # Cleanup
        cap.release()
        out.release()
        
        # Statistiques finales
        stats['unique_wagons'] = list(stats['unique_wagons'])
        
        print("\n" + "-" * 70)
        print("\n✓ TRAITEMENT TERMINE!")
        print(f"\n  Frames traitees: {stats['processed_frames']}/{total_frames}")
        print(f"  Detections totales: {stats['total_detections']}")
        print(f"  Wagons uniques: {len(stats['unique_wagons'])}")
        
        if stats['unique_wagons']:
            print(f"\n  Numeros detectes:")
            for wagon_id in stats['unique_wagons']:
                count = self.detection_history.count(wagon_id)
                print(f"    - {wagon_id} ({count}x)")
        
        print(f"\n  Video de sortie: {output_path}")
        print("="*70 + "\n")
        
        return stats


def main():
    """Point d'entree principal"""
    import sys
    
    if len(sys.argv) < 3:
        print("Usage: python demo_pro.py <video_input> <video_output>")
        sys.exit(1)
    
    input_video = sys.argv[1]
    output_video = sys.argv[2]
    
    # Creer pipeline
    pipeline = ProfessionalOCRPipeline()
    
    # Traiter
    try:
        stats = pipeline.process_video_professional(input_video, output_video)
    except Exception as e:
        print(f"\nERREUR: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


if __name__ == "__main__":
    main()
