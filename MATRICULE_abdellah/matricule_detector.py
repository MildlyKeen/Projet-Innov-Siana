"""
MODULE INTÉGRÉ DE DÉTECTION ET RECONNAISSANCE DE MATRICULES TGV
================================================================
Utilisation:
    from matricule_detector import MatriculeDetector
    
    detector = MatriculeDetector()
    result = detector.detect_and_recognize("path/to/image.jpg")
    print(f"Matricule: {result['matricule']}, Confiance: {result['confidence']:.1f}%")
"""

import cv2
import numpy as np
import pickle
import json
import os
from typing import Dict, Optional, List, Tuple

class MatriculeDetector:
    """
    Classe principale pour détecter et reconnaître les matricules TGV
    """
    
    def __init__(self, model_dir: Optional[str] = None):
        """
        Initialise le détecteur avec les modèles entraînés
        
        Args:
            model_dir: Répertoire contenant les modèles (par défaut: ./models)
        """
        if model_dir is None:
            model_dir = os.path.join(os.path.dirname(__file__), 'models')
        
        self.model_dir = model_dir
        self.model = None
        self.mappings = None
        self.region_detector = None
        self.annotations = {}
        
        self._load_models()
    
    def _load_models(self):
        """Charge tous les modèles nécessaires"""
        try:
            # Modèle de reconnaissance
            model_path = os.path.join(self.model_dir, 'matricule_rf_model.pkl')
            with open(model_path, 'rb') as f:
                self.model = pickle.load(f)
            
            # Mappings
            mapping_path = os.path.join(self.model_dir, 'matricule_mapping.pkl')
            with open(mapping_path, 'rb') as f:
                self.mappings = pickle.load(f)
            
            # Détecteur de région (optionnel)
            region_path = os.path.join(self.model_dir, 'region_detector.pkl')
            if os.path.exists(region_path):
                with open(region_path, 'rb') as f:
                    self.region_detector = pickle.load(f)
            
            # Annotations manuelles (optionnel)
            annotations_path = os.path.join(self.model_dir, 'matricule_annotations.json')
            if os.path.exists(annotations_path):
                with open(annotations_path, 'r') as f:
                    self.annotations = json.load(f)
            
            print("✓ Modèles chargés avec succès")
            
        except Exception as e:
            print(f"❌ Erreur chargement modèles: {e}")
            raise
    
    def preprocess_roi(self, roi: np.ndarray) -> np.ndarray:
        """
        Prétraite une ROI pour la reconnaissance
        
        Args:
            roi: Image ROI en couleur ou niveaux de gris
            
        Returns:
            ROI prétraitée et aplatie pour le modèle
        """
        # Convertir en niveaux de gris si nécessaire
        if len(roi.shape) == 3:
            gray = cv2.cvtColor(roi, cv2.COLOR_BGR2GRAY)
        else:
            gray = roi.copy()
        
        # Égalisation d'histogramme
        gray = cv2.equalizeHist(gray)
        
        # Redimensionner à taille fixe (160x80)
        resized = cv2.resize(gray, (160, 80))
        
        # Normaliser [0, 1]
        normalized = resized.astype('float32') / 255.0
        
        # Aplatir en vecteur 1D
        flattened = normalized.flatten().reshape(1, -1)
        
        return flattened
    
    def recognize_roi(self, roi: np.ndarray) -> Dict:
        """
        Reconnaît le matricule dans une ROI
        
        Args:
            roi: Image ROI contenant le matricule
            
        Returns:
            Dictionnaire avec matricule, confiance, et top 3 prédictions
        """
        # Prétraitement
        features = self.preprocess_roi(roi)
        
        # Prédiction
        pred_idx = self.model.predict(features)[0]
        matricule = self.mappings['idx_to_label'][pred_idx]
        
        # Probabilités
        probas = self.model.predict_proba(features)[0]
        confidence = probas[pred_idx] * 100
        
        # Top 3
        top3_idx = np.argsort(probas)[::-1][:3]
        top3 = [
            {
                'matricule': self.mappings['idx_to_label'][idx],
                'confidence': probas[idx] * 100
            }
            for idx in top3_idx
        ]
        
        return {
            'matricule': matricule,
            'confidence': confidence,
            'top3': top3
        }
    
    def detect_region_manual(self, image: np.ndarray, filename: str) -> Optional[Tuple[int, int, int, int]]:
        """
        Cherche une annotation manuelle pour cette image
        
        Args:
            image: Image complète
            filename: Nom du fichier image
            
        Returns:
            Bbox (x, y, w, h) ou None
        """
        if filename in self.annotations:
            bbox = self.annotations[filename]['bbox']
            return tuple(bbox)
        return None
    
    def detect_region_mser(self, image: np.ndarray) -> List[Tuple[int, int, int, int]]:
        """
        Détecte les régions candidates avec MSER
        
        Args:
            image: Image complète en couleur
            
        Returns:
            Liste de bboxes (x, y, w, h)
        """
        gray = cv2.cvtColor(image, cv2.COLOR_BGR2GRAY)
        
        # MSER
        mser = cv2.MSER_create()
        mser.setDelta(5)
        mser.setMinArea(100)
        mser.setMaxArea(5000)
        
        regions, _ = mser.detectRegions(gray)
        
        # Convertir en bboxes
        bboxes = []
        for region in regions:
            x, y, w, h = cv2.boundingRect(region)
            
            # Filtrer par ratio (matricules sont horizontaux)
            ratio = w / max(h, 1)
            if 1.5 < ratio < 6.0 and w > 30 and h > 15:
                bboxes.append((x, y, w, h))
        
        return bboxes
    
    def detect_and_recognize(
        self, 
        image_path: str, 
        use_manual: bool = True,
        use_mser: bool = True,
        visualize: bool = False
    ) -> Dict:
        """
        Détecte et reconnaît le matricule dans une image complète
        
        Args:
            image_path: Chemin vers l'image
            use_manual: Utiliser les annotations manuelles si disponibles
            use_mser: Utiliser MSER pour détecter les régions
            visualize: Sauvegarder une image annotée
            
        Returns:
            Dictionnaire avec résultats de détection et reconnaissance
        """
        # Charger l'image
        image = cv2.imread(image_path)
        if image is None:
            return {'error': f"Impossible de charger {image_path}"}
        
        filename = os.path.basename(image_path)
        result = {
            'filename': filename,
            'image_path': image_path,
            'bbox': None,
            'matricule': None,
            'confidence': 0.0,
            'method': None,
            'top3': []
        }
        
        # 1. Essayer annotation manuelle d'abord
        if use_manual:
            bbox = self.detect_region_manual(image, filename)
            if bbox is not None:
                x, y, w, h = bbox
                roi = image[y:y+h, x:x+w]
                recognition = self.recognize_roi(roi)
                
                result.update({
                    'bbox': bbox,
                    'method': 'manual_annotation',
                    **recognition
                })
                
                if visualize:
                    self._save_visualization(image, bbox, recognition, filename)
                
                return result
        
        # 2. Essayer MSER
        if use_mser:
            bboxes = self.detect_region_mser(image)
            
            if bboxes:
                # Tester chaque bbox et garder la meilleure
                best_result = None
                best_confidence = 0.0
                
                for bbox in bboxes:
                    x, y, w, h = bbox
                    roi = image[y:y+h, x:x+w]
                    recognition = self.recognize_roi(roi)
                    
                    if recognition['confidence'] > best_confidence:
                        best_confidence = recognition['confidence']
                        best_result = {
                            'bbox': bbox,
                            'method': 'mser_detection',
                            **recognition
                        }
                
                if best_result and best_confidence > 30:  # Seuil minimum
                    result.update(best_result)
                    
                    if visualize:
                        self._save_visualization(image, best_result['bbox'], best_result, filename)
                    
                    return result
        
        # Aucune détection réussie
        result['error'] = "Aucune région de matricule détectée"
        return result
    
    def _save_visualization(self, image: np.ndarray, bbox: Tuple, recognition: Dict, filename: str):
        """Sauvegarde une image annotée avec le résultat"""
        img_annotated = image.copy()
        x, y, w, h = bbox
        
        # Rectangle
        cv2.rectangle(img_annotated, (x, y), (x+w, y+h), (0, 255, 0), 2)
        
        # Texte
        text = f"{recognition['matricule']} ({recognition['confidence']:.1f}%)"
        cv2.putText(
            img_annotated, text, 
            (x, y-10), 
            cv2.FONT_HERSHEY_SIMPLEX, 
            0.7, (0, 255, 0), 2
        )
        
        # Sauvegarder
        output_name = f"result_{filename}"
        cv2.imwrite(output_name, img_annotated)
        print(f"✓ Visualisation sauvegardée: {output_name}")
    
    def test_on_image(self, image_path: str, true_matricule: Optional[str] = None) -> Dict:
        """
        Test complet sur une image avec affichage formaté
        
        Args:
            image_path: Chemin vers l'image
            true_matricule: Matricule réel (optionnel, pour validation)
            
        Returns:
            Résultats de la détection
        """
        print("="*70)
        print(f"TEST SUR: {os.path.basename(image_path)}")
        print("="*70)
        
        result = self.detect_and_recognize(image_path, visualize=True)
        
        if 'error' in result:
            print(f"\n❌ {result['error']}")
            return result
        
        # Affichage
        print(f"\n✓ Méthode: {result['method']}")
        print(f"✓ Bbox: x={result['bbox'][0]}, y={result['bbox'][1]}, "
              f"w={result['bbox'][2]}, h={result['bbox'][3]}")
        print(f"\n{'='*70}")
        print("RÉSULTAT:")
        print('='*70)
        print(f"Matricule détecté: {result['matricule']}")
        print(f"Confiance: {result['confidence']:.1f}%")
        
        if true_matricule:
            is_correct = result['matricule'] == true_matricule
            status = "✓ CORRECT" if is_correct else "✗ INCORRECT"
            print(f"\nVrai matricule: {true_matricule}")
            print(f"Status: {status}")
        
        print(f"\nTop 3 prédictions:")
        for i, pred in enumerate(result['top3'], 1):
            print(f"  {i}. {pred['matricule']}: {pred['confidence']:.1f}%")
        
        print('='*70)
        
        return result


# Fonction utilitaire pour utilisation rapide
def detect_matricule(image_path: str, true_matricule: Optional[str] = None) -> Dict:
    """
    Fonction rapide pour détecter un matricule
    
    Args:
        image_path: Chemin vers l'image
        true_matricule: Matricule réel (optionnel)
        
    Returns:
        Résultats de la détection
    """
    detector = MatriculeDetector()
    return detector.test_on_image(image_path, true_matricule)


if __name__ == "__main__":
    # Test rapide
    print("MODULE MATRICULE DETECTOR")
    print("Chargement des modèles...")
    
    detector = MatriculeDetector()
    print(f"✓ {len(detector.mappings['idx_to_label'])} matricules connus")
    print(f"✓ {len(detector.annotations)} annotations manuelles")
