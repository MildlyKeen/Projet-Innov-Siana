from typing import Dict, Any, Optional
import cv2

from src.preprocessing.contrast_enhancement import enhance_for_ocr
from src.ocr.ocr_engine import run_ocr
from src.ocr.postprocess import clean_text
from src.ocr.regex_validation import is_valid_loco_number

def crop_roi_fixed(frame_bgr, roi):
    """
    roi = (x1, y1, x2, y2) en pixels.
    """
    x1, y1, x2, y2 = roi
    h, w = frame_bgr.shape[:2]
    x1 = max(0, min(w-1, x1))
    x2 = max(0, min(w, x2))
    y1 = max(0, min(h-1, y1))
    y2 = max(0, min(h, y2))
    return frame_bgr[y1:y2, x1:x2], (x1, y1, x2, y2)

def compute_score(item, frame_shape):
    """
    Calcule un score métier pour un candidat OCR.
    item: {text, confidence, bbox}
    frame_shape: (h, w)
    """
    h, w = frame_shape

    x1, y1, x2, y2 = item["bbox"]
    bw = x2 - x1
    bh = y2 - y1
    box_area = bw * bh

    # centre du bbox
    cx = (x1 + x2) / 2
    cy = (y1 + y2) / 2

    # centre de l'image
    img_cx = w / 2
    img_cy = h / 2

    # distance normalisée au centre
    dist_center = ((cx - img_cx) ** 2 + (cy - img_cy) ** 2) ** 0.5
    dist_center_norm = dist_center / ((img_cx ** 2 + img_cy ** 2) ** 0.5)

    score = (
        1.5 * item["confidence"]      # OCR sûr
        + 0.000001 * box_area         # numéro bien visible
        + (1 - dist_center_norm)      # proche du centre
    )

    return score


def pick_best_candidate(items, frame_shape, conf_min=0.5):
    best = None
    best_score = -1

    for it in items:
        if it["confidence"] < conf_min:
            continue

        # on accepte 3 à 5 chiffres
        if not it["text"].isdigit():
            continue
        if not (3 <= len(it["text"]) <= 5):
            continue

        score = compute_score(it, frame_shape)

        if score > best_score:
            best_score = score
            best = {
                "text": it["text"],
                "confidence": it["confidence"],
                "bbox": it["bbox"],
                "score": round(score, 3)
            }

    return best


def run_ocr_pipeline(frame_bgr, meta: Dict[str, Any], roi):
    """
    Retour standardisé pour M3:
    {
      meta, roi,
      best: {text, confidence, bbox} ou None,
      all: liste brute OCR (nettoyée)
    }
    """
    roi_img, roi_xy = crop_roi_fixed(frame_bgr, roi)
    gray = enhance_for_ocr(roi_img)
    raw = run_ocr(gray)

    # normalise bbox (bbox est relative à ROI -> on la remet dans coord globales)
    x1, y1, _, _ = roi_xy
    all_items = []
    for it in raw:
        bx1, by1, bx2, by2 = it["bbox"]
        all_items.append({
            "text": clean_text(it["text"]),
            "confidence": it["confidence"],
            "bbox": [bx1 + x1, by1 + y1, bx2 + x1, by2 + y1]
        })

    h, w = frame_bgr.shape[:2]
    best = pick_best_candidate(all_items, (h, w))


    return {
        "meta": meta,
        "roi": list(roi_xy),
        "best": best,
        "all": all_items
    }

def draw_result(frame_bgr, result):
    """
    Dessine ROI + best bbox + texte.
    """
    out = frame_bgr.copy()
    rx1, ry1, rx2, ry2 = result["roi"]
    cv2.rectangle(out, (rx1, ry1), (rx2, ry2), (0, 255, 255), 2)

    best = result.get("best")
    if best:
        x1, y1, x2, y2 = best["bbox"]
        cv2.rectangle(out, (x1, y1), (x2, y2), (0, 255, 0), 2)
        label = f'{best["text"]} ({best["confidence"]:.2f})'
        cv2.putText(out, label, (x1, max(20, y1-10)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0,255,0), 2, cv2.LINE_AA)
    return out
