import cv2
import numpy as np
from src.core.base_quality_runtime import BaseQualityRuntime

class FailurePredictionRuntime(BaseQualityRuntime):
    """
    SDK compliant Failure Prediction runtime.
    Predicts spatial regions likely to contain artifacts based on image complexity and subject flags.
    """
    def __init__(self):
        pass

    def get_metadata(self) -> dict:
        return {
            "id": "failure_prediction",
            "name": "Failure Prediction Runtime",
            "dependencies": [],
            "execution_cost": 1.0
        }

    def evaluate(self, img_bgr: np.ndarray, alpha_mask: np.ndarray, vision_graph: dict = None, context: dict = None) -> dict:
        h, w = alpha_mask.shape[:2]
        failure_prob_map = np.zeros((h, w), dtype=np.uint8)
        
        # Default risk variables
        bg_complexity_high = False
        has_thin_structures = False
        has_reflective_metals = False
        
        if context and "background" in context:
            bg_complexity_high = (context["background"].get("complexity") == "high")
            
        if vision_graph:
            def traverse(node):
                nonlocal has_thin_structures, has_reflective_metals
                if node:
                    if "Hair" in node["label"] or "Plant" in node["label"]:
                        has_thin_structures = True
                    if "Reflective" in node["label"] or "Metal" in node["label"]:
                        has_reflective_metals = True
                for child in node.get("children", []):
                    traverse(child)
            traverse(vision_graph)

        try:
            # Determine risky boundaries
            boundary = cv2.dilate(alpha_mask, None) - cv2.erode(alpha_mask, None)
            
            # Map spatial failure probability
            # Base probability is higher at boundaries
            failure_prob_map[boundary > 0] = 100
            
            # Increase probability if risk factors are present
            if bg_complexity_high:
                failure_prob_map[boundary > 0] = 180
            if has_thin_structures:
                # Thin structure borders are extra volatile
                failure_prob_map[boundary > 0] = 220
            if has_reflective_metals:
                # Reflective edges often leak color spill
                failure_prob_map[boundary > 0] = 200

            # Compute estimated overall grade
            avg_prob = np.mean(failure_prob_map[boundary > 0]) if np.any(boundary) else 0.0
            
            if avg_prob < 80:
                grade = "A"
                strategy = "default"
            elif avg_prob < 150:
                grade = "B"
                strategy = "local_refine"
            elif avg_prob < 210:
                grade = "C"
                strategy = "local_refine_and_decontaminate"
            else:
                grade = "D"
                strategy = "global_reprocess"

            return {
                "quality_score": float(np.clip(1.0 - (avg_prob / 255.0), 0.1, 1.0)),
                "failure_probability_map": failure_prob_map,
                "quality_grade": grade,
                "suggested_repair_strategy": strategy
            }

        except Exception as e:
            print(f"[-] FailurePredictionRuntime error: {e}")
            return {
                "quality_score": 0.8,
                "failure_probability_map": failure_prob_map,
                "quality_grade": "B",
                "suggested_repair_strategy": "default"
            }
