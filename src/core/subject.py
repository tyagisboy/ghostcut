import cv2
import numpy as np

from src.core.base_runtime import BaseRuntime

class SubjectIntelligence(BaseRuntime):
    """
    Identifies multiple simultaneous subjects inside the image.
    Supported subject types: Human, Animal, Product, Plant, Mixed
    """
    def __init__(self):
        pass

    def get_metadata(self) -> dict:
        return {
            "id": "subject",
            "name": "Subject Intelligence",
            "dependencies": ["scene"],
            "execution_cost": 1.2,
            "quality_impact": 8.0,
            "requires_mask": False
        }

    def analyze(self, img_bgr, metrics=None, context=None):

        """
        Detects subject flags based on image features.
        """
        subjects = []
        confidences = {}
        
        # 1. Cheap metrics extraction if not provided
        if metrics is None:
            from src.core.scenario import classify_scenario
            _, _, metrics = classify_scenario(img_bgr)
            
        skin_ratio = metrics.get("skin_ratio", 0.0)
        lap_var = metrics.get("laplacian_var", 0.0)
        
        # Human detection
        if skin_ratio > 0.03:
            subjects.append("Human")
            confidences["Human"] = float(np.clip(skin_ratio * 10.0, 0.5, 1.0))
            
        # Animal detection
        if lap_var > 1300.0 and skin_ratio < 0.05:
            subjects.append("Animal")
            confidences["Animal"] = 0.85
            
        # Plant detection
        small = cv2.resize(img_bgr, (128, 128))
        green_mask = cv2.inRange(small, np.array([0, 55, 0]), np.array([100, 255, 100]))
        green_ratio = float(np.count_nonzero(green_mask)) / green_mask.size
        if green_ratio > 0.15:
            subjects.append("Plant")
            confidences["Plant"] = 0.80
            
        # Product detection
        if not subjects or (len(subjects) == 1 and subjects[0] == "Plant"):
            subjects.append("Product")
            confidences["Product"] = 0.75
            
        # Mixed check
        if len(subjects) > 1:
            subjects.append("Mixed")
            confidences["Mixed"] = 0.90
            
        return {
            "subjects": subjects,
            "confidence": confidences
        }
