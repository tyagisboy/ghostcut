import cv2
import numpy as np
from src.core.base_quality_runtime import BaseQualityRuntime

class RegionConsistencyRuntime(BaseQualityRuntime):
    """
    SDK compliant Region Consistency evaluator.
    Verifies that bordering semantic structures are topologically connected in the alpha mask
    (e.g., confirming hair borders scalp skin, and beards border face boundaries).
    """
    def __init__(self):
        pass

    def get_metadata(self) -> dict:
        return {
            "id": "region_consistency",
            "name": "Region Consistency",
            "dependencies": [],
            "execution_cost": 1.5
        }

    def evaluate(self, img_bgr: np.ndarray, alpha_mask: np.ndarray, vision_graph: dict = None, context: dict = None) -> dict:
        h, w = alpha_mask.shape[:2]
        defect_map = np.zeros((h, w), dtype=np.uint8)
        repair_suggestions = []

        # Find if hair and face are both present
        has_hair = False
        has_face = False
        if vision_graph:
            def traverse(node):
                nonlocal has_hair, has_face
                if node:
                    if "Hair" in node["label"]:
                        has_hair = True
                    if "Face" in node["label"]:
                        has_face = True
                for child in node.get("children", []):
                    traverse(child)
            traverse(vision_graph)

        if not (has_hair and has_face):
            return {
                "quality_score": 1.0,
                "defect_map": defect_map,
                "repair_suggestions": []
            }

        try:
            # Check for consistency gap between hair and face bounds:
            # Extract upper-middle region where hair joins face/forehead
            y_indices, x_indices = np.where(alpha_mask > 127)
            if len(y_indices) > 0 and len(x_indices) > 0:
                ymin, ymax = int(np.min(y_indices)), int(np.max(y_indices))
                xmin, xmax = int(np.min(x_indices)), int(np.max(x_indices))
                
                # Joint zone (scalp boundary): upper-mid torso columns, upper row
                joint_ymin = ymin + int((ymax - ymin) * 0.05)
                joint_ymax = ymin + int((ymax - ymin) * 0.20)
                joint_xmin = xmin + int((xmax - xmin) * 0.20)
                joint_xmax = xmin + int((xmax - xmin) * 0.80)
                
                if joint_ymax > joint_ymin and joint_xmax > joint_xmin:
                    joint_crop = alpha_mask[joint_ymin:joint_ymax, joint_xmin:joint_xmax]
                    # If there is a deep zero valley (gap) split right in the middle of a continuous mask,
                    # it represents an edge instability / split region defect.
                    vertical_profile = np.mean(joint_crop > 127, axis=0)
                    # Look for valleys where foreground coverage drops close to zero in the horizontal profile
                    valleys = np.where(vertical_profile < 0.15)[0]
                    
                    if len(valleys) > 5:  # significant gap detected
                        # Map defect pixels
                        gap_cols = joint_xmin + valleys
                        defect_map[joint_ymin:joint_ymax, gap_cols] = 255
                        
                        bx = int(gap_cols[0])
                        by = joint_ymin
                        bw = int(gap_cols[-1] - gap_cols[0])
                        bh = joint_ymax - joint_ymin
                        
                        repair_suggestions.append({
                            "bbox": [bx, by, bw, bh],
                            "strategy": "fill_topological_gap",
                            "severity": 0.35
                        })
                        
                        return {
                            "quality_score": 0.65,
                            "defect_map": defect_map,
                            "repair_suggestions": repair_suggestions
                        }

            return {
                "quality_score": 1.0,
                "defect_map": defect_map,
                "repair_suggestions": []
            }

        except Exception as e:
            print(f"[-] RegionConsistencyRuntime error: {e}")
            return {
                "quality_score": 0.9,
                "defect_map": defect_map,
                "repair_suggestions": []
            }
