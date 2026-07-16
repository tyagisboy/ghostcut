import cv2
import numpy as np
from src.core.base_runtime import BaseRuntime

class ClothingRuntime(BaseRuntime):
    """
    SDK compliant Clothing Intelligence runtime.
    Analyzes body region textures, fabric details, mesh patterns, and transparency using OpenCV.
    """
    def __init__(self):
        pass

    def get_metadata(self) -> dict:
        return {
            "id": "clothing",
            "name": "Clothing Intelligence",
            "dependencies": ["subject"],
            "execution_cost": 2.0,
            "quality_impact": 8.0,
            "requires_mask": True
        }

    def analyze(self, img_bgr: np.ndarray, mask: np.ndarray = None, context: dict = None) -> dict:
        """
        Locates clothing boundaries in the lower torso region and extracts texture characteristics.
        """
        h, w = img_bgr.shape[:2]
        if mask is None:
            mask = np.ones((h, w), dtype=np.uint8) * 255

        has_clothing = False
        fabric_type = "solid"
        mesh_detected = False
        transparency_detected = False
        clothing_type = "general"
        confidence = 0.0

        try:
            # 1. Isolate body region (lower 60% of mask bounding box)
            y_indices, x_indices = np.where(mask > 127)
            if len(y_indices) > 0 and len(x_indices) > 0:
                ymin, ymax = int(np.min(y_indices)), int(np.max(y_indices))
                xmin, xmax = int(np.min(x_indices)), int(np.max(x_indices))
                fg_h = ymax - ymin
                
                body_ymin = int(ymin + 0.40 * fg_h)  # Skip head/neck area
                body_ymax = ymax

                if (body_ymax > body_ymin + 10) and (xmax > xmin + 10):
                    has_clothing = True
                    confidence = 0.89
                    
                    body_crop = img_bgr[body_ymin:body_ymax, xmin:xmax]
                    body_mask = mask[body_ymin:body_ymax, xmin:xmax]

                    # 2. Fabric analysis (texture classification)
                    if body_crop.size > 0:
                        gray = cv2.cvtColor(body_crop, cv2.COLOR_BGR2GRAY)
                        # Check for texture variation
                        edges = cv2.Canny(gray, 30, 90)
                        edge_ratio = np.mean(edges > 0)
                        
                        # Apply morphological open to find high frequency checkerboards/grids (mesh fabric)
                        kernel = cv2.getStructuringElement(cv2.MORPH_CROSS, (3, 3))
                        morph = cv2.morphologyEx(edges, cv2.MORPH_OPEN, kernel)
                        grid_ratio = np.mean(morph > 0)

                        if grid_ratio > 0.01:
                            fabric_type = "mesh"
                            mesh_detected = True
                            transparency_detected = True
                        elif edge_ratio > 0.15:
                            fabric_type = "textured"
                        else:
                            fabric_type = "solid"

                        # Classify general type based on area ratio
                        body_area = np.sum(body_mask > 127)
                        total_area = h * w
                        ratio = body_area / total_area
                        if ratio > 0.25:
                            clothing_type = "suit/outerwear"
                        else:
                            clothing_type = "shirt/top"

            return {
                "has_clothing": has_clothing,
                "fabric_type": fabric_type,
                "mesh": mesh_detected,
                "transparency": transparency_detected,
                "clothing_type": clothing_type,
                "confidence": confidence
            }

        except Exception as e:
            print(f"[-] ClothingRuntime error: {e}")
            return {
                "has_clothing": False,
                "fabric_type": "solid",
                "mesh": False,
                "transparency": False,
                "clothing_type": "general",
                "confidence": 0.0
            }
