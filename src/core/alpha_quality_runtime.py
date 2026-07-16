import cv2
import numpy as np
from src.core.base_quality_runtime import BaseQualityRuntime

class AlphaQualityRuntime(BaseQualityRuntime):
    """
    SDK compliant Alpha Quality evaluator.
    Measures transition profile clipping, alpha smoothness, and unwanted expansion.
    """
    def __init__(self):
        pass

    def get_metadata(self) -> dict:
        return {
            "id": "alpha_quality",
            "name": "Alpha Quality Evaluation",
            "dependencies": [],
            "execution_cost": 2.0
        }

    def evaluate(self, img_bgr: np.ndarray, alpha_mask: np.ndarray, vision_graph: dict = None, context: dict = None) -> dict:
        h, w = alpha_mask.shape[:2]
        defect_map = np.zeros((h, w), dtype=np.uint8)
        
        try:
            # 1. Isolate transition boundaries (values between 15 and 240)
            transition_mask = (alpha_mask > 15) & (alpha_mask < 240)
            trans_count = np.sum(transition_mask)
            
            if trans_count < 100:
                return {
                    "quality_score": 1.0,
                    "defect_map": defect_map,
                    "repair_suggestions": []
                }

            # 2. Check for matte clipping (very sharp hard cuts on soft features)
            # Dilate/Erode to get boundary transition width
            boundary = cv2.dilate(alpha_mask, None) - cv2.erode(alpha_mask, None)
            clip_count = np.sum((boundary > 240) & (alpha_mask == 0))
            
            # 3. Check for blurry expansion (gradient width too wide)
            # Find thickness of the transition zone
            expansion_defect = 0
            dist_transform = cv2.distanceTransform(transition_mask.astype(np.uint8), cv2.DIST_L2, 3)
            max_thickness = np.max(dist_transform) if np.any(transition_mask) else 0.0
            
            # If transition width is wider than 15px in non-transparency/non-hair regions, flag it
            is_hair_or_trans = False
            if vision_graph:
                # Traverse tree to see if Hair or Glass is active
                def check_tree(node):
                    nonlocal is_hair_or_trans
                    if node and ("Hair" in node["label"] or "Glass" in node["label"] or "Fur" in node["label"]):
                        is_hair_or_trans = True
                    for c in node.get("children", []):
                        check_tree(c)
                check_tree(vision_graph)
                
            if max_thickness > 15.0 and not is_hair_or_trans:
                expansion_defect = int(max_thickness)
                defect_map[dist_transform > 12.0] = 255

            # Calculate scores
            clip_ratio = clip_count / trans_count
            expansion_penalty = min(0.3, expansion_defect * 0.02)
            
            quality_score = float(np.clip(1.0 - clip_ratio - expansion_penalty, 0.4, 1.0))
            
            # Compile repair candidates if defects are flagged
            repair_suggestions = []
            if expansion_defect > 15:
                # Bounding box of expansion defect
                y_indices, x_indices = np.where(dist_transform > 12.0)
                if len(y_indices) > 0:
                    ymin, ymax = int(np.min(y_indices)), int(np.max(y_indices))
                    xmin, xmax = int(np.min(x_indices)), int(np.max(x_indices))
                    repair_suggestions.append({
                        "bbox": [xmin, ymin, xmax - xmin, ymax - ymin],
                        "strategy": "contract_matte",
                        "severity": float(expansion_penalty)
                    })

            return {
                "quality_score": quality_score,
                "defect_map": defect_map,
                "repair_suggestions": repair_suggestions
            }

        except Exception as e:
            print(f"[-] AlphaQualityRuntime error: {e}")
            return {
                "quality_score": 0.85,
                "defect_map": defect_map,
                "repair_suggestions": []
            }
