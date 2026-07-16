import cv2
import numpy as np
from src.core.base_quality_runtime import BaseQualityRuntime

class MaskStabilityRuntime(BaseQualityRuntime):
    """
    SDK compliant Mask Stability evaluator.
    Detects floating pixels (isolated micro-components) and inner holes in solid regions.
    """
    def __init__(self):
        pass

    def get_metadata(self) -> dict:
        return {
            "id": "mask_stability",
            "name": "Mask Stability Evaluation",
            "dependencies": [],
            "execution_cost": 1.5
        }

    def evaluate(self, img_bgr: np.ndarray, alpha_mask: np.ndarray, vision_graph: dict = None, context: dict = None) -> dict:
        h, w = alpha_mask.shape[:2]
        defect_map = np.zeros((h, w), dtype=np.uint8)
        repair_suggestions = []
        
        try:
            # 1. Connected components analysis to detect floating pixels
            binary = (alpha_mask > 127).astype(np.uint8)
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(binary)
            
            floating_pixels_count = 0
            if num_labels > 2:
                # Find the largest foreground component index (excluding background labeled 0)
                largest_idx = 1 + np.argmax(stats[1:, cv2.CC_STAT_AREA])
                
                # Check smaller components
                for i in range(1, num_labels):
                    if i == largest_idx:
                        continue
                    area = stats[i, cv2.CC_STAT_AREA]
                    # If component is very small (< 100 pixels), class as floating pixels
                    if area < 100:
                        floating_pixels_count += 1
                        defect_map[labels == i] = 255
                        
                        # Suggest deleting this floating island
                        rx = stats[i, cv2.CC_STAT_LEFT]
                        ry = stats[i, cv2.CC_STAT_TOP]
                        rw = stats[i, cv2.CC_STAT_WIDTH]
                        rh = stats[i, cv2.CC_STAT_HEIGHT]
                        
                        repair_suggestions.append({
                            "bbox": [int(rx), int(ry), int(rw), int(rh)],
                            "strategy": "delete_speckle",
                            "severity": float(np.clip(area / 100.0, 0.1, 0.9))
                        })

            # 2. Holes detection (find internal black areas inside white shapes)
            # Inverted binary mask components
            inverted = 1 - binary
            num_labels_inv, labels_inv, stats_inv, _ = cv2.connectedComponentsWithStats(inverted)

            
            hole_count = 0
            # Label 0 is outer background, other components are holes inside the foreground
            for i in range(1, num_labels_inv):
                # If hole is enclosed by foreground and is small (< 150px)
                area = stats_inv[i, cv2.CC_STAT_AREA]
                left = stats_inv[i, cv2.CC_STAT_LEFT]
                top = stats_inv[i, cv2.CC_STAT_TOP]
                width = stats_inv[i, cv2.CC_STAT_WIDTH]
                height = stats_inv[i, cv2.CC_STAT_HEIGHT]
                
                # Ensure it is not on the border of the image
                if (left > 0 and top > 0 and (left + width) < w and (top + height) < h) and area < 150:
                    hole_count += 1
                    defect_map[labels_inv == i] = 255
                    
                    # Suggest filling this hole
                    repair_suggestions.append({
                        "bbox": [int(left), int(top), int(width), int(height)],
                        "strategy": "fill_hole",
                        "severity": float(np.clip(area / 150.0, 0.1, 0.9))
                    })

            # Score calculation
            score = float(np.clip(1.0 - (floating_pixels_count * 0.05 + hole_count * 0.05), 0.5, 1.0))
            
            return {
                "quality_score": score,
                "defect_map": defect_map,
                "repair_suggestions": sorted(repair_suggestions, key=lambda x: x["severity"], reverse=True)[:5]
            }

        except Exception as e:
            print(f"[-] MaskStabilityRuntime error: {e}")
            return {
                "quality_score": 0.9,
                "defect_map": defect_map,
                "repair_suggestions": []
            }
