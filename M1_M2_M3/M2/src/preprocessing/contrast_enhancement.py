import cv2
import numpy as np

def enhance_for_ocr(bgr):
    """Améliore légèrement l'image pour OCR (grayscale + CLAHE + sharpen doux)."""
    gray = cv2.cvtColor(bgr, cv2.COLOR_BGR2GRAY)

    # CLAHE (contraste local)
    clahe = cv2.createCLAHE(clipLimit=2.0, tileGridSize=(8, 8))
    eq = clahe.apply(gray)

    # Sharpen doux
    kernel = np.array([[0, -1, 0],
                       [-1, 5, -1],
                       [0, -1, 0]], dtype=np.float32)
    sharp = cv2.filter2D(eq, -1, kernel)

    return sharp
