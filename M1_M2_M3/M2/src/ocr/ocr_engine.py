from typing import Dict, Any, List, Tuple
import numpy as np
import easyocr

# Reader global (évite de le recharger à chaque frame)
_READER = None

def get_reader():
    global _READER
    if _READER is None:
        # lang 'en' suffit pour chiffres/latin
        _READER = easyocr.Reader(['en'], gpu=False)
    return _READER

def run_ocr(gray_img: np.ndarray) -> List[Dict[str, Any]]:
    """
    Exécute OCR sur une image en niveaux de gris.
    Retourne une liste d'items: {text, confidence, bbox}
    bbox = [x1,y1,x2,y2] (rectangle englobant)
    """
    reader = get_reader()
    results = reader.readtext(gray_img)

    out = []
    for (bbox, text, conf) in results:
        # bbox = [[x,y],[x,y],[x,y],[x,y]]
        xs = [p[0] for p in bbox]
        ys = [p[1] for p in bbox]
        x1, y1, x2, y2 = int(min(xs)), int(min(ys)), int(max(xs)), int(max(ys))
        out.append({
            "text": text,
            "confidence": float(conf),
            "bbox": [x1, y1, x2, y2],
        })
    return out
