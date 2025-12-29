"""
OCR Module for Train Wagon Identification
Uses PaddleOCR with confidence filtering and regex validation
"""

import cv2
import numpy as np
import re
from typing import List, Tuple, Optional, Dict
from paddleocr import PaddleOCR
import config


class TrainOCR:
    """
    OCR system for reading wagon identification numbers
    """
    
    def __init__(self):
        """Initialize PaddleOCR"""
        # PaddleOCR 3.x initialization
        try:
            self.ocr = PaddleOCR(lang=config.OCR_LANGUAGE)
        except Exception as e:
            print(f"Warning: PaddleOCR init error: {e}")
            # Fallback to minimal config
            self.ocr = PaddleOCR()
        
        # Compile regex pattern for wagon ID validation
        self.wagon_pattern = re.compile(config.WAGON_ID_PATTERN)
    
    def extract_text(self, image: np.ndarray) -> List[Tuple[List, str, float]]:
        """
        Extract text from image using OCR
        
        Args:
            image: Input image (BGR format)
        
        Returns:
            List of (bbox, text, confidence) tuples
        """
        # PaddleOCR expects RGB
        if len(image.shape) == 3 and image.shape[2] == 3:
            image_rgb = cv2.cvtColor(image, cv2.COLOR_BGR2RGB)
        else:
            image_rgb = image
        
        try:
            # PaddleOCR 3.x uses predict() instead of ocr()
            result = self.ocr.predict(input=image_rgb)
            
            if result is None:
                return []
            
            detections = []
            
            # PaddleOCR 3.x returns different structure
            # Try to extract text detections from result
            if hasattr(result, 'json') and result.json:
                # New API returns structured result
                for item in result.json:
                    try:
                        if 'text' in item and 'score' in item:
                            # Extract bbox if available
                            bbox = item.get('bbox', [[0,0],[100,0],[100,50],[0,50]])
                            text = item['text']
                            confidence = item['score']
                            detections.append((bbox, text, confidence))
                    except Exception as parse_error:
                        print(f"OCR Parse Error: {parse_error}")
                        continue
            
            return detections
        
        except Exception as e:
            print(f"OCR Error: {e}")
            # Try fallback for older API
            try:
                result_old = self.ocr.ocr(image_rgb)
                if result_old and len(result_old) > 0 and result_old[0]:
                    detections = []
                    for line in result_old[0]:
                        if isinstance(line, (list, tuple)) and len(line) >= 2:
                            bbox = line[0]
                            text_info = line[1]
                            if isinstance(text_info, (tuple, list)) and len(text_info) >= 2:
                                detections.append((bbox, text_info[0], text_info[1]))
                    return detections
            except:
                pass
            return []
    
    def validate_wagon_id(self, text: str) -> bool:
        """
        Validate if text matches expected wagon ID format
        
        Args:
            text: Text to validate
        
        Returns:
            True if valid wagon ID
        """
        # Remove extra whitespace
        text = text.strip().upper()
        
        # Check against regex pattern
        return bool(self.wagon_pattern.match(text))
    
    def clean_text(self, text: str) -> str:
        """
        Clean and normalize OCR output
        
        Args:
            text: Raw OCR text
        
        Returns:
            Cleaned text
        """
        # Remove special characters except hyphen and space
        text = re.sub(r'[^A-Z0-9\-\s]', '', text.upper())
        
        # Normalize whitespace
        text = ' '.join(text.split())
        
        # Common OCR corrections
        corrections = {
            'O': '0',  # Letter O to zero
            'I': '1',  # Letter I to one
            'S': '5',  # S to 5 (in numbers context)
            'B': '8',  # B to 8 (in numbers context)
        }
        
        # Apply corrections to numeric parts
        parts = text.split('-') if '-' in text else [text]
        cleaned_parts = []
        
        for i, part in enumerate(parts):
            if i > 0 and part.isdigit():  # Numeric part (after prefix)
                for old, new in corrections.items():
                    part = part.replace(old, new)
            cleaned_parts.append(part)
        
        return '-'.join(cleaned_parts)
    
    def process_roi(self, image: np.ndarray, 
                   bbox: Tuple[int, int, int, int]) -> Optional[Dict]:
        """
        Process a region of interest (ROI) for wagon ID
        
        Args:
            image: Full frame
            bbox: Bounding box (x, y, w, h)
        
        Returns:
            Dict with wagon_id, confidence, bbox if successful, None otherwise
        """
        x, y, w, h = bbox
        
        # Expand ROI slightly
        expansion = config.ROI_EXPANSION_FACTOR
        x_exp = max(0, int(x - w * (expansion - 1) / 2))
        y_exp = max(0, int(y - h * (expansion - 1) / 2))
        w_exp = min(image.shape[1] - x_exp, int(w * expansion))
        h_exp = min(image.shape[0] - y_exp, int(h * expansion))
        
        # Extract ROI
        roi = image[y_exp:y_exp+h_exp, x_exp:x_exp+w_exp]
        
        if roi.size == 0:
            return None
        
        # Preprocess ROI for better OCR
        roi = self._preprocess_roi(roi)
        
        # Extract text
        detections = self.extract_text(roi)
        
        # Filter and validate results
        best_result = None
        best_confidence = 0.0
        
        for bbox_ocr, text, confidence in detections:
            if confidence < config.OCR_CONFIDENCE_THRESHOLD:
                continue
            
            # Clean text
            cleaned_text = self.clean_text(text)
            
            # Validate format
            if self.validate_wagon_id(cleaned_text):
                if confidence > best_confidence:
                    best_confidence = confidence
                    best_result = {
                        'wagon_id': cleaned_text,
                        'confidence': confidence,
                        'bbox': (x, y, w, h),
                        'raw_text': text
                    }
        
        return best_result
    
    def _preprocess_roi(self, roi: np.ndarray) -> np.ndarray:
        """
        Additional preprocessing for OCR ROI
        
        Args:
            roi: Region of interest
        
        Returns:
            Preprocessed ROI
        """
        try:
            # Convert to grayscale
            if len(roi.shape) == 3:
                gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
            else:
                gray = roi
            
            # Simple contrast enhancement
            clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8,8))
            enhanced = clahe.apply(gray)
            
            # Convert back to BGR for OCR
            preprocessed = cv2.cvtColor(enhanced, cv2.COLOR_GRAY2BGR)
            
            return preprocessed
        except Exception as e:
            print(f"Preprocess ROI error: {e}")
            return roi
    
    def batch_process(self, image: np.ndarray,
                     bboxes: List[Tuple[int, int, int, int]]) -> List[Dict]:
        """
        Process multiple ROIs in a single frame
        
        Args:
            image: Full frame
            bboxes: List of bounding boxes
        
        Returns:
            List of detection results
        """
        results = []
        
        for bbox in bboxes:
            result = self.process_roi(image, bbox)
            if result is not None:
                results.append(result)
        
        return results


# Alternative: EasyOCR implementation (commented out)
"""
from easyocr import Reader

class TrainOCREasy:
    def __init__(self):
        self.reader = Reader([config.OCR_LANGUAGE], gpu=config.USE_GPU)
    
    def extract_text(self, image):
        results = self.reader.readtext(image)
        detections = []
        for bbox, text, confidence in results:
            detections.append((bbox, text, confidence))
        return detections
"""
