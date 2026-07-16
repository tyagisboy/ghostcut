import cv2
import numpy as np
from src.core.base_runtime import BaseRuntime
from src.core.intelligence import classify_hair_type

class HairRuntime(BaseRuntime):
    """
    SDK compliant Hair Intelligence analyzer (v2).
    """
    def __init__(self):
        pass

    def initialize(self, config: dict) -> None:
        pass

    def get_metadata(self) -> dict:
        return {
            "id": "hair",
            "name": "Hair Intelligence Engine",
            "dependencies": ["material"],
            "execution_cost": 3.0,
            "quality_impact": 9.0,
            "requires_mask": True
        }

    def analyze(self, img_bgr: np.ndarray, mask: np.ndarray, features: dict = None, context: dict = None) -> dict:

        """
        Extracts hair curl types, backlit highlight flags, transparency, density, and other v3 parameters.
        """
        try:
            if mask is None or np.count_nonzero(mask > 20) == 0:
                return {
                    "hair_type": "general", "curl_level": 0.0, "strand_thickness": "medium",
                    "flyaway_probability": 0.0, "backlit": False,
                    "length": "short", "density": 0.0, "curl_level_score": 0.0, "strand_width": "medium",
                    "flyaway_score": 0.0, "transparency_score": 0.0, "wetness": 0.0, "frizz": 0.0,
                    "volume": 0.0, "backlit_probability": 0.0, "confidence": 0.0
                }

            if features is None:
                features = {}
            hair_type = classify_hair_type(img_bgr, mask, features)
            
            # Map hair type to curl and thickness
            curl_level = 0.0
            strand_width = "medium"
            if hair_type in ["straight", "wavy"]:
                curl_level = 0.2
                strand_width = "thick"
            elif hair_type in ["loose_curl", "tight_curl"]:
                curl_level = 0.7
                strand_width = "medium"
            elif hair_type in ["afro", "frizzy"]:
                curl_level = 1.0
                strand_width = "fine"
            elif hair_type == "flyaway":
                curl_level = 0.4
                strand_width = "fine"

            # Image processing calculations
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            lap = cv2.Laplacian(gray, cv2.CV_32F)
            lap_abs = np.abs(lap)
            
            hair_pixels = mask > 50
            if np.count_nonzero(hair_pixels) > 0:
                mean_lap_hair = float(np.mean(lap_abs[hair_pixels]))
                mean_val = float(np.mean(gray[hair_pixels]))
                std_val = float(np.std(gray[hair_pixels]))
                var_lap_hair = float(np.var(lap[hair_pixels]))
            else:
                mean_lap_hair = 0.0
                mean_val = 128.0
                std_val = 50.0
                var_lap_hair = 0.0

            # 1. Length estimation
            y_indices, _ = np.where(mask > 20)
            if len(y_indices) > 0:
                total_span = y_indices.max() - y_indices.min() + 1
                hair_y_indices, _ = np.where(mask > 80)
                if len(hair_y_indices) > 0:
                    hair_span = hair_y_indices.max() - hair_y_indices.min() + 1
                    ratio = hair_span / max(1, total_span)
                    if ratio > 0.6:
                        length = "long"
                    elif ratio > 0.3:
                        length = "medium"
                    else:
                        length = "short"
                else:
                    length = "short"
            else:
                length = "short"

            # 2. Density
            density = float(np.clip(mean_lap_hair / 40.0, 0.1, 1.0))

            # 3. Flyaway score
            canny = cv2.Canny(gray, 30, 100)
            kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
            dilated = cv2.dilate(mask, kernel)
            outer_zone = ((dilated > 50) & (mask < 20)).astype(np.uint8)
            outer_edges = np.count_nonzero(canny[outer_zone > 0]) if np.count_nonzero(outer_zone) > 0 else 0
            flyaway_score = float(np.clip(outer_edges / 300.0, 0.05, 0.95))
            if hair_type == "flyaway":
                flyaway_score = max(flyaway_score, 0.9)

            # 4. Transparency score
            transition_zone = (dilated > 50) & (mask > 10) & (mask < 240)
            transparency_score = float(np.mean(mask[transition_zone] / 255.0)) if np.count_nonzero(transition_zone) > 0 else 0.2

            # 5. Wetness
            wetness = float(np.clip((120.0 - mean_val) / 100.0 * (40.0 - std_val) / 40.0, 0.0, 1.0))
            if hair_type == "wet":
                wetness = max(wetness, 0.8)

            # 6. Frizz
            frizz = float(np.clip((var_lap_hair - 500) / 3000.0, 0.1, 1.0))
            if hair_type == "frizzy":
                frizz = max(frizz, 0.85)

            # 7. Volume
            total_mask_count = np.count_nonzero(mask > 10)
            volume = float(np.clip(np.count_nonzero(mask > 50) / max(1, total_mask_count), 0.1, 1.0))

            # 8. Backlit probability
            backlit_probability = 0.95 if hair_type == "backlit" else (0.75 if (mean_val > 180 and std_val < 30) else 0.1)

            # 9. Confidence
            confidence = float(np.clip(density * 1.2, 0.4, 0.98))

            return {
                "hair_type": hair_type,
                "curl_level": curl_level,
                "strand_thickness": strand_width,
                "flyaway_probability": flyaway_score,
                "backlit": (hair_type == "backlit"),
                
                # Upgraded v3 fields
                "length": length,
                "density": density,
                "curl_level_score": curl_level,
                "strand_width": strand_width,
                "flyaway_score": flyaway_score,
                "transparency_score": transparency_score,
                "wetness": wetness,
                "frizz": frizz,
                "volume": volume,
                "backlit_probability": backlit_probability,
                "confidence": confidence
            }
        except Exception as e:
            return {
                "hair_type": "general", "curl_level": 0.0, "strand_thickness": "medium",
                "flyaway_probability": 0.0, "backlit": False,
                "length": "medium", "density": 0.0, "curl_level_score": 0.0, "strand_width": "medium",
                "flyaway_score": 0.0, "transparency_score": 0.0, "wetness": 0.0, "frizz": 0.0,
                "volume": 0.0, "backlit_probability": 0.0, "confidence": 0.0
            }

    def validate(self) -> list:
        return []

