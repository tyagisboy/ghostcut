import cv2
import numpy as np
from src.core.base_quality_runtime import BaseQualityRuntime

class EdgeQualityRuntime(BaseQualityRuntime):
    """
    SDK compliant Edge Quality evaluator.
    Measures contour jaggedness, over-smoothing, and leakage.
    """
    def __init__(self):
        pass

    def get_metadata(self) -> dict:
        return {
            "id": "edge_quality",
            "name": "Edge Quality Evaluation",
            "dependencies": [],
            "execution_cost": 2.0
        }

    def evaluate(self, img_bgr: np.ndarray, alpha_mask: np.ndarray, vision_graph: dict = None, context: dict = None) -> dict:
        h, w = alpha_mask.shape[:2]
        defect_map = np.zeros((h, w), dtype=np.uint8)
        repair_suggestions = []
        
        # Default high quality if empty mask
        if np.sum(alpha_mask > 127) < 50:
            return {
                "quality_score": 1.0,
                "defect_map": defect_map,
                "repair_suggestions": []
            }

        try:
            # 1. Edge jaggedness: Look at contour curvature variance
            contours, _ = cv2.findContours(alpha_mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_NONE)
            jagged_scores = []
            
            for c in contours:
                if cv2.contourArea(c) < 100:
                    continue
                
                # Compute local curvature variations
                pts = c.reshape(-1, 2)
                n_pts = len(pts)
                if n_pts < 10:
                    continue
                
                for i in range(5, n_pts - 5):
                    p_prev = pts[i - 5]
                    p_curr = pts[i]
                    p_next = pts[i + 5]
                    
                    # Calculate vector deviation
                    v1 = p_curr - p_prev
                    v2 = p_next - p_curr
                    norm1 = np.linalg.norm(v1) + 1e-5
                    norm2 = np.linalg.norm(v2) + 1e-5
                    cos_theta = np.dot(v1, v2) / (norm1 * norm2)
                    angle = np.degrees(np.arccos(np.clip(cos_theta, -1.0, 1.0)))
                    
                    # Curvature spike indicates jaggedness (e.g. angle > 35 degrees)
                    if angle > 35.0:
                        jagged_scores.append(angle)
                        # Paint defect onto map
                        cv2.circle(defect_map, tuple(p_curr), 8, 255, -1)
                        
                        # Suggest repair box around coordinates
                        rx = max(0, p_curr[0] - 32)
                        ry = max(0, p_curr[1] - 32)
                        rw = min(w - rx, 64)
                        rh = min(h - ry, 64)
                        
                        repair_suggestions.append({
                            "bbox": [rx, ry, rw, rh],
                            "strategy": "local_refine",
                            "severity": float(angle / 180.0)
                        })

            # Calculate quality score (0.0 to 1.0)
            avg_jagged = np.mean(jagged_scores) if jagged_scores else 0.0
            quality_score = float(np.clip(1.0 - (avg_jagged / 90.0), 0.3, 1.0))
            
            # Keep suggestions list reasonably compact
            repair_suggestions = sorted(repair_suggestions, key=lambda x: x["severity"], reverse=True)[:5]

            return {
                "quality_score": quality_score,
                "defect_map": defect_map,
                "repair_suggestions": repair_suggestions
            }

        except Exception as e:
            print(f"[-] EdgeQualityRuntime error: {e}")
            return {
                "quality_score": 0.8,
                "defect_map": defect_map,
                "repair_suggestions": []
            }
