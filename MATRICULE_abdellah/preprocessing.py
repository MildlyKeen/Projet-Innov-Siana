"""
Image Preprocessing Pipeline for Train OCR
Handles perspective correction, stabilization, and image enhancement
"""

import cv2
import numpy as np
from typing import Tuple, Optional, List
import config


class VideoPreprocessor:
    """
    Preprocessing pipeline for train video streams
    """
    
    def __init__(self):
        self.prev_frame = None
        self.transform_matrix = None
        
        # Initialize CLAHE for contrast enhancement
        if config.CONTRAST_ENHANCEMENT:
            self.clahe = cv2.createCLAHE(
                clipLimit=config.CLAHE_CLIP_LIMIT,
                tileGridSize=config.CLAHE_TILE_SIZE
            )
    
    def correct_perspective(self, frame: np.ndarray, 
                          src_points: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Correct perspective distortion in the frame
        
        Args:
            frame: Input image
            src_points: Source points for perspective transform (4 points)
                       If None, uses automatic detection
        
        Returns:
            Perspective-corrected image
        """
        if not config.PERSPECTIVE_CORRECTION_ENABLED:
            return frame
        
        h, w = frame.shape[:2]
        
        if src_points is None:
            # Default: assume tracks are in the middle section
            # Adjust these based on your camera setup
            src_points = np.float32([
                [w * 0.2, h * 0.4],  # Top-left
                [w * 0.8, h * 0.4],  # Top-right
                [w * 0.9, h * 0.9],  # Bottom-right
                [w * 0.1, h * 0.9]   # Bottom-left
            ])
        
        # Define destination points (rectangular view)
        dst_points = np.float32([
            [0, 0],
            [config.TARGET_WIDTH, 0],
            [config.TARGET_WIDTH, config.TARGET_HEIGHT],
            [0, config.TARGET_HEIGHT]
        ])
        
        # Calculate perspective transform matrix
        matrix = cv2.getPerspectiveTransform(src_points, dst_points)
        self.transform_matrix = matrix
        
        # Apply transformation
        corrected = cv2.warpPerspective(
            frame, matrix,
            (config.TARGET_WIDTH, config.TARGET_HEIGHT)
        )
        
        return corrected
    
    def stabilize_frame(self, frame: np.ndarray) -> np.ndarray:
        """
        Stabilize video frame to reduce camera shake
        
        Args:
            frame: Input frame
        
        Returns:
            Stabilized frame
        """
        if not config.STABILIZATION_ENABLED:
            return frame
        
        if self.prev_frame is None:
            self.prev_frame = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
            return frame
        
        # Convert current frame to grayscale
        gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
        
        # Detect feature points
        prev_pts = cv2.goodFeaturesToTrack(
            self.prev_frame,
            maxCorners=200,
            qualityLevel=0.01,
            minDistance=30,
            blockSize=3
        )
        
        if prev_pts is None:
            self.prev_frame = gray
            return frame
        
        # Calculate optical flow
        curr_pts, status, _ = cv2.calcOpticalFlowPyrLK(
            self.prev_frame, gray, prev_pts, None
        )
        
        # Filter valid points
        idx = np.where(status == 1)[0]
        if len(idx) < 10:
            self.prev_frame = gray
            return frame
        
        prev_pts = prev_pts[idx]
        curr_pts = curr_pts[idx]
        
        # Estimate affine transform
        transform = cv2.estimateAffinePartial2D(prev_pts, curr_pts)[0]
        
        if transform is not None:
            # Apply stabilization transform
            h, w = frame.shape[:2]
            stabilized = cv2.warpAffine(frame, transform, (w, h))
            self.prev_frame = gray
            return stabilized
        
        self.prev_frame = gray
        return frame
    
    def enhance_image(self, frame: np.ndarray) -> np.ndarray:
        """
        Enhance image contrast and brightness for better OCR
        
        Args:
            frame: Input frame
        
        Returns:
            Enhanced frame
        """
        # Convert to LAB color space
        lab = cv2.cvtColor(frame, cv2.COLOR_BGR2LAB)
        l, a, b = cv2.split(lab)
        
        # Apply CLAHE to L channel
        if config.CONTRAST_ENHANCEMENT:
            l = self.clahe.apply(l)
        
        # Merge channels
        enhanced_lab = cv2.merge([l, a, b])
        enhanced = cv2.cvtColor(enhanced_lab, cv2.COLOR_LAB2BGR)
        
        # Optional brightness adjustment
        if config.BRIGHTNESS_ADJUSTMENT:
            hsv = cv2.cvtColor(enhanced, cv2.COLOR_BGR2HSV)
            h, s, v = cv2.split(hsv)
            
            # Adaptive brightness based on mean luminance
            mean_v = np.mean(v)
            if mean_v < 100:  # Dark image
                v = cv2.add(v, 30)
            elif mean_v > 200:  # Bright image
                v = cv2.subtract(v, 20)
            
            enhanced_hsv = cv2.merge([h, s, v])
            enhanced = cv2.cvtColor(enhanced_hsv, cv2.COLOR_HSV2BGR)
        
        return enhanced
    
    def preprocess_frame(self, frame: np.ndarray,
                        perspective_points: Optional[np.ndarray] = None) -> np.ndarray:
        """
        Complete preprocessing pipeline
        
        Args:
            frame: Input frame
            perspective_points: Optional perspective correction points
        
        Returns:
            Fully preprocessed frame
        """
        # Step 1: Stabilization
        frame = self.stabilize_frame(frame)
        
        # Step 2: Perspective correction
        frame = self.correct_perspective(frame, perspective_points)
        
        # Step 3: Enhancement
        frame = self.enhance_image(frame)
        
        return frame
    
    def reset(self):
        """Reset preprocessor state"""
        self.prev_frame = None
        self.transform_matrix = None


def detect_train_region(frame: np.ndarray) -> List[Tuple[int, int, int, int]]:
    """
    Simple train region detection using edge detection
    Returns list of bounding boxes (x, y, w, h)
    
    Note: This is a placeholder. Actual detection should come from Membre 1.
    """
    gray = cv2.cvtColor(frame, cv2.COLOR_BGR2GRAY)
    edges = cv2.Canny(gray, 50, 150)
    
    # Find contours
    contours, _ = cv2.findContours(edges, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
    
    bboxes = []
    for contour in contours:
        x, y, w, h = cv2.boundingRect(contour)
        # Filter by size (adjust thresholds)
        if w > 100 and h > 50 and w < frame.shape[1] * 0.8:
            bboxes.append((x, y, w, h))
    
    return bboxes
