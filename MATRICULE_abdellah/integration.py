"""
Integration Interface for Train Detection + OCR Pipeline
Combines segmentation, detection (from Membre 1) and OCR
"""

import cv2
import numpy as np
from typing import List, Dict, Tuple, Optional
from preprocessing import VideoPreprocessor
from ocr_module import TrainOCR
import config


class TrainDetectionOCRPipeline:
    """
    Unified pipeline integrating detection and OCR
    """
    
    def __init__(self):
        """Initialize all components"""
        self.preprocessor = VideoPreprocessor()
        self.ocr = TrainOCR()
        self.frame_count = 0
    
    def process_frame(self, frame: np.ndarray,
                     detections: Optional[List[Dict]] = None) -> Tuple[np.ndarray, List[Dict]]:
        """
        Process a single frame with full pipeline
        
        Args:
            frame: Input video frame
            detections: Optional detections from Membre 1
                       Format: [{'bbox': (x,y,w,h), 'class': 'train', 'confidence': 0.95}, ...]
        
        Returns:
            Tuple of (annotated_frame, ocr_results)
        """
        self.frame_count += 1
        
        # Step 1: Preprocess frame
        preprocessed = self.preprocessor.preprocess_frame(frame)
        
        # Step 2: Get detections (if not provided, use simple detection)
        if detections is None:
            from preprocessing import detect_train_region
            bboxes = detect_train_region(preprocessed)
            detections = [{'bbox': bbox, 'class': 'train', 'confidence': 1.0} 
                         for bbox in bboxes]
        
        # Step 3: Filter detections by confidence
        valid_detections = [
            d for d in detections 
            if d.get('confidence', 0) >= config.MIN_DETECTION_CONFIDENCE
        ]
        
        # Step 4: Extract bounding boxes
        bboxes = [d['bbox'] for d in valid_detections]
        
        # Step 5: Run OCR on each detection
        ocr_results = self.ocr.batch_process(preprocessed, bboxes)
        
        # Step 6: Annotate frame
        annotated = self._annotate_frame(frame.copy(), ocr_results)
        
        return annotated, ocr_results
    
    def _annotate_frame(self, frame: np.ndarray, 
                       ocr_results: List[Dict]) -> np.ndarray:
        """
        Draw annotations on frame
        
        Args:
            frame: Original frame
            ocr_results: OCR detection results
        
        Returns:
            Annotated frame
        """
        for result in ocr_results:
            x, y, w, h = result['bbox']
            wagon_id = result['wagon_id']
            confidence = result['confidence']
            
            # Draw bounding box
            cv2.rectangle(
                frame, (x, y), (x + w, y + h),
                config.ANNOTATION_COLOR,
                config.ANNOTATION_THICKNESS
            )
            
            # Prepare text
            label = f"{wagon_id} ({confidence:.2f})"
            
            # Calculate text size for background
            (text_w, text_h), baseline = cv2.getTextSize(
                label,
                cv2.FONT_HERSHEY_SIMPLEX,
                config.FONT_SCALE,
                config.ANNOTATION_THICKNESS
            )
            
            # Draw text background
            cv2.rectangle(
                frame,
                (x, y - text_h - 10),
                (x + text_w, y),
                config.ANNOTATION_COLOR,
                -1
            )
            
            # Draw text
            cv2.putText(
                frame,
                label,
                (x, y - 5),
                cv2.FONT_HERSHEY_SIMPLEX,
                config.FONT_SCALE,
                (0, 0, 0),  # Black text
                config.ANNOTATION_THICKNESS
            )
        
        return frame
    
    def process_video(self, input_path: str, output_path: str,
                     detection_callback=None) -> Dict:
        """
        Process entire video file
        
        Args:
            input_path: Path to input video
            output_path: Path to save annotated video
            detection_callback: Optional function to provide detections per frame
                              Signature: callback(frame, frame_number) -> List[Dict]
        
        Returns:
            Statistics dict
        """
        # Open video
        cap = cv2.VideoCapture(input_path)
        if not cap.isOpened():
            raise ValueError(f"Cannot open video: {input_path}")
        
        # Get video properties
        fps = int(cap.get(cv2.CAP_PROP_FPS))
        width = int(cap.get(cv2.CAP_PROP_FRAME_WIDTH))
        height = int(cap.get(cv2.CAP_PROP_FRAME_HEIGHT))
        total_frames = int(cap.get(cv2.CAP_PROP_FRAME_COUNT))
        
        # Create video writer
        fourcc = cv2.VideoWriter_fourcc(*config.OUTPUT_VIDEO_CODEC)
        out = cv2.VideoWriter(output_path, fourcc, fps, (width, height))
        
        # Statistics
        stats = {
            'total_frames': total_frames,
            'processed_frames': 0,
            'total_detections': 0,
            'unique_wagons': set()
        }
        
        print(f"Processing video: {input_path}")
        print(f"Resolution: {width}x{height}, FPS: {fps}, Frames: {total_frames}")
        
        frame_num = 0
        while True:
            ret, frame = cap.read()
            if not ret:
                break
            
            frame_num += 1
            
            # Get detections if callback provided
            detections = None
            if detection_callback is not None:
                detections = detection_callback(frame, frame_num)
            
            # Process frame
            annotated, ocr_results = self.process_frame(frame, detections)
            
            # Update statistics
            stats['processed_frames'] += 1
            stats['total_detections'] += len(ocr_results)
            for result in ocr_results:
                stats['unique_wagons'].add(result['wagon_id'])
            
            # Write frame
            out.write(annotated)
            
            # Progress
            if frame_num % 30 == 0:
                progress = (frame_num / total_frames) * 100
                print(f"Progress: {progress:.1f}% ({frame_num}/{total_frames})", end='\r')
        
        # Cleanup
        cap.release()
        out.release()
        
        # Finalize stats
        stats['unique_wagons'] = list(stats['unique_wagons'])
        
        print(f"\nProcessing complete!")
        print(f"Total detections: {stats['total_detections']}")
        print(f"Unique wagons: {len(stats['unique_wagons'])}")
        
        return stats
    
    def reset(self):
        """Reset pipeline state"""
        self.preprocessor.reset()
        self.frame_count = 0


class DetectionOCRInterface:
    """
    Interface for Membre 3 (Fusion & Logique Métier)
    Provides clean API for integration
    """
    
    def __init__(self):
        self.pipeline = TrainDetectionOCRPipeline()
    
    def detect_and_read(self, frame: np.ndarray,
                       detections: Optional[List[Dict]] = None) -> List[Dict]:
        """
        Main interface method: detect trains and read wagon IDs
        
        Args:
            frame: Input frame
            detections: Optional pre-computed detections
        
        Returns:
            List of results with wagon_id, confidence, bbox
        """
        _, ocr_results = self.pipeline.process_frame(frame, detections)
        return ocr_results
    
    def get_preprocessed_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Get preprocessed frame for other modules
        
        Args:
            frame: Input frame
        
        Returns:
            Preprocessed frame
        """
        return self.pipeline.preprocessor.preprocess_frame(frame)
    
    def export_results(self, results: List[Dict], output_path: str):
        """
        Export results to file for Membre 3
        
        Args:
            results: OCR results
            output_path: Path to save results (JSON or CSV)
        """
        import json
        
        # Convert to serializable format
        export_data = []
        for result in results:
            export_data.append({
                'wagon_id': result['wagon_id'],
                'confidence': float(result['confidence']),
                'bbox': list(result['bbox']),
                'raw_text': result.get('raw_text', '')
            })
        
        # Save as JSON
        with open(output_path, 'w') as f:
            json.dump(export_data, f, indent=2)
        
        print(f"Results exported to: {output_path}")
