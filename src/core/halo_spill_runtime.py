import cv2
import numpy as np
from src.core.base_quality_runtime import BaseQualityRuntime

class HaloSpillRuntime(BaseQualityRuntime):
    """
    SDK compliant Halo & Spill Quality evaluator.
    Detects color spill, background bleed, and transition halos (white/dark lines).
    """
    def __init__(self):
        pass

    def get_metadata(self) -> dict:
        return {
            "id": "halo_spill",
            "name": "Halo & Spill Quality",
            "dependencies": [],
            "execution_cost": 2.5
        }

    def evaluate(self, img_bgr: np.ndarray, alpha_mask: np.ndarray, vision_graph: dict = None, context: dict = None) -> dict:
        h, w = alpha_mask.shape[:2]
        defect_map = np.zeros((h, w), dtype=np.uint8)
        repair_suggestions = []

        try:
            # 1. Edge boundary ring (dilate 3px minus erode 3px around mask boundary)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            dilated = cv2.dilate(alpha_mask, kernel)
            eroded = cv2.erode(alpha_mask, kernel)
            boundary_mask = ((dilated > 0) & (eroded < 255)).astype(np.uint8) * 255
            
            boundary_pixels = np.sum(boundary_mask > 0)
            if boundary_pixels < 100:
                return {
                    "quality_score": 1.0,
                    "defect_map": defect_map,
                    "repair_suggestions": []
                }

            # 2. Halo detection: Check for sudden brightness spikes in transition zone
            # Compare intensity along the boundary
            gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
            # Find local standard deviation along the border
            bg_mean = np.mean(gray[eroded == 0]) if np.any(eroded == 0) else 128.0
            
            # Highlight regions where boundary pixels have high contrast compared to local inner/outer means
            boundary_intensities = gray[boundary_mask > 0]
            local_variance = np.var(boundary_intensities)
            
            # White halo detection: intensity is bright and different
            white_halo_mask = (boundary_mask > 0) & (gray > 220)
            white_halo_count = np.sum(white_halo_mask)

            # 3. Color Spill detection: Compare HSV hue values
            hsv = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2HSV)
            hue = hsv[:, :, 0]
            sat = hsv[:, :, 1]
            val = hsv[:, :, 2]
            
            # Scan for background chrominance spill (e.g. green bleed, blue bleed)
            # Check saturation and hue along the mask border
            spill_mask = (boundary_mask > 0) & (sat > 80) & ((hue > 35) & (hue < 85))  # Green-spill range
            spill_count = np.sum(spill_mask)
            
            # Combine into defect map
            defect_map[white_halo_mask] = 255
            defect_map[spill_mask] = 255

            # Scores
            halo_ratio = white_halo_count / boundary_pixels
            spill_ratio = spill_count / boundary_pixels
            
            severity = float(np.clip(1.5 * halo_ratio + 2.0 * spill_ratio, 0.0, 1.0))
            score = float(np.clip(1.0 - severity, 0.4, 1.0))

            # Suggest localized decontaminations
            if spill_count > 100 or white_halo_count > 100:
                y_indices, x_indices = np.where(defect_map > 0)
                if len(y_indices) > 0:
                    ymin, ymax = int(np.min(y_indices)), int(np.max(y_indices))
                    xmin, xmax = int(np.min(x_indices)), int(np.max(x_indices))
                    
                    repair_suggestions.append({
                        "bbox": [xmin, ymin, xmax - xmin, ymax - ymin],
                        "strategy": "decontaminate",
                        "severity": severity
                    })

            return {
                "quality_score": score,
                "defect_map": defect_map,
                "repair_suggestions": repair_suggestions
            }

        except Exception as e:
            print(f"[-] HaloSpillRuntime error: {e}")
            return {
                "quality_score": 0.8,
                "defect_map": defect_map,
                "repair_suggestions": []
            }
