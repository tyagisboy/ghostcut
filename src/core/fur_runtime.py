import cv2
import numpy as np

from src.core.base_runtime import BaseRuntime

class FurRuntime(BaseRuntime):
    """
    SDK compliant Fur Intelligence analyzer (v2).
    """
    def __init__(self):
        pass

    def initialize(self, config: dict) -> None:
        pass

    def get_metadata(self) -> dict:
        return {
            "id": "fur",
            "name": "Fur Intelligence Engine",
            "dependencies": ["material"],
            "execution_cost": 3.0,
            "quality_impact": 9.0,
            "requires_mask": True
        }

    def analyze(self, img_bgr: np.ndarray, mask: np.ndarray, features: dict = None, context: dict = None) -> dict:

        """
        Analyzes fur details: fur length, density, fluffiness, whiskers, undercoat, transparency, and confidence.
        """
        try:
            if mask is None or np.count_nonzero(mask > 20) == 0:
                return {
                    "fur_type": "none", "whiskers": False, "dense": False,
                    "fur_length": "none", "density": 0.0, "fluffiness": 0.0,
                    "fur_whiskers": False, "undercoat": 0.0, "transparency": 0.0,
                    "confidence": 0.0
                }

            h, w = mask.shape[:2]
            small_mask = cv2.resize(mask, (128, 128))
            small_img = cv2.resize(img_bgr, (128, 128))
            gray = cv2.cvtColor(small_img, cv2.COLOR_BGR2GRAY)
            
            # Laplacian variance
            lap = cv2.Laplacian(gray, cv2.CV_32F)
            lap_var = np.var(lap[small_mask > 20]) if np.count_nonzero(small_mask > 20) > 0 else 0.0
            
            # Estimate fur type based on texture variance
            if lap_var > 2200.0:
                fur_type = "long"
                fur_length = "long"
            elif lap_var > 1000.0:
                fur_type = "short"
                fur_length = "medium"
            else:
                fur_type = "fine"
                fur_length = "short"
                
            # Whiskers detection
            whiskers_detected = False
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (11, 11))
            dilated = cv2.dilate(small_mask, kernel)
            outer_zone = ((dilated > 50) & (small_mask < 20)).astype(np.uint8)
            
            fluffiness = 0.2
            if np.count_nonzero(outer_zone) > 0:
                local_std = cv2.boxFilter(np.abs(lap), -1, (7, 7))
                max_std = np.max(local_std[outer_zone > 0])
                if max_std > 35.0:
                    whiskers_detected = True
                fluffiness = float(np.clip(np.mean(local_std[outer_zone > 0]) / 30.0, 0.05, 0.95))
            
            # Density
            density = float(np.clip(lap_var / 2500.0, 0.1, 1.0))
            
            # Undercoat
            eroded = cv2.erode(small_mask, kernel)
            if np.count_nonzero(eroded > 100) > 0:
                undercoat = float(np.clip(np.var(gray[eroded > 100]) / 2000.0, 0.0, 1.0))
            else:
                undercoat = 0.0
                
            # Transparency
            trans_zone = (small_mask > 30) & (small_mask < 225)
            transparency = float(np.clip(np.count_nonzero(trans_zone) / max(1, np.count_nonzero(small_mask > 20)), 0.0, 1.0))
            
            # Confidence
            confidence = float(np.clip(0.5 + density * 0.5, 0.5, 0.95))
                    
            return {
                "fur_type": fur_type,
                "whiskers": whiskers_detected,
                "dense": (lap_var > 1200.0),
                
                # Upgraded v3 fields
                "fur_length": fur_length,
                "density": density,
                "fluffiness": fluffiness,
                "fur_whiskers": whiskers_detected,
                "undercoat": undercoat,
                "transparency": transparency,
                "confidence": confidence
            }
        except Exception as e:
            return {
                "fur_type": "none", "whiskers": False, "dense": False,
                "fur_length": "none", "density": 0.0, "fluffiness": 0.0,
                "fur_whiskers": False, "undercoat": 0.0, "transparency": 0.0,
                "confidence": 0.0
            }

    def validate(self) -> list:
        return []

