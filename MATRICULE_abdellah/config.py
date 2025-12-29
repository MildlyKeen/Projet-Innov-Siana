"""
Configuration file for Train OCR Pipeline
"""

# OCR Configuration
OCR_CONFIDENCE_THRESHOLD = 0.7  # Minimum confidence score for OCR results
OCR_LANGUAGE = 'en'  # Language for OCR (change to 'fr' if needed)
USE_GPU = False  # Set to True if GPU is available

# Wagon ID Format
# Example: Adjust regex pattern based on your wagon ID format
# Common formats: "XXXX-1234", "AB-12345", etc.
WAGON_ID_PATTERN = r'^[A-Z0-9]{2,4}[-\s]?\d{4,6}$'

# Preprocessing Configuration
# Perspective correction
PERSPECTIVE_CORRECTION_ENABLED = True
TARGET_WIDTH = 800
TARGET_HEIGHT = 600

# Stabilization (for video only, disable for static images)
STABILIZATION_ENABLED = False
STABILIZATION_SMOOTHING_RADIUS = 50

# Image enhancement
CONTRAST_ENHANCEMENT = True
BRIGHTNESS_ADJUSTMENT = True
CLAHE_CLIP_LIMIT = 2.0
CLAHE_TILE_SIZE = (8, 8)

# Detection Integration
MIN_DETECTION_CONFIDENCE = 0.5
ROI_EXPANSION_FACTOR = 1.2  # Expand detection bbox by 20%

# Video Output
OUTPUT_VIDEO_FPS = 30
OUTPUT_VIDEO_CODEC = 'mp4v'
ANNOTATION_COLOR = (0, 255, 0)  # Green
ANNOTATION_THICKNESS = 2
FONT_SCALE = 0.8
