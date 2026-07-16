import cv2
import numpy as np
from src.core.base_quality_runtime import BaseQualityRuntime

class TransparencyQualityRuntime(BaseQualityRuntime):
    """
    SDK compliant Transparency Quality evaluator.
    Validates transparent/semi-transparent regions (e.g. Glass, Lace, Fabric Mesh)
    against the alpha mask to ensure transparency isn't clipped to solid opaque.
    """
    def __init__(self):
        pass

    def get_metadata(self) -> dict:
        return {
            "id": "transparency_quality",
            "name": "Transparency Quality",
            "dependencies": [],
            "execution_cost": 1.5
        }

    def evaluate(self, img_bgr: np.ndarray, alpha_mask: np.ndarray, vision_graph: dict = None, context: dict = None) -> dict:
        h, w = alpha_mask.shape[:2]
        defect_map = np.zeros((h, w), dtype=np.uint8)
        repair_suggestions = []

        # Find transparent nodes in VisionGraph
        transparent_nodes = []
        if vision_graph:
            def traverse(node):
                if node and ("Glass" in node["label"] or "Glasses" in node["label"] or "mesh" in node.get("attributes", {}).get("fabric_type", "")):
                    transparent_nodes.append(node)
                for child in node.get("children", []):
                    traverse(child)
            traverse(vision_graph)

        if not transparent_nodes:
            # If no transparency nodes scheduled, return perfect score
            return {
                "quality_score": 1.0,
                "defect_map": defect_map,
                "repair_suggestions": []
            }

        try:
            total_defect_score = 0.0
            for node in transparent_nodes:
                # Approximate bounding box from node attributes or context
                # E.g., for "Glasses", it is inside the face box
                bbox = [int(w * 0.3), int(h * 0.2), int(w * 0.4), int(h * 0.15)] # default fallback
                if node["label"] == "Glasses" and context and "face" in context:
                    fb = context["face"].get("face_box")
                    if fb:
                        bbox = [fb[0], fb[1] + int(fb[3] * 0.2), fb[2], int(fb[3] * 0.3)]
                elif "clothing" in context:
                    # Fabric transparency
                    bbox = [0, int(h * 0.45), w, int(h * 0.5)]

                bx, by, bw, bh = bbox
                bx, by = max(0, bx), max(0, by)
                bw, bh = min(w - bx, bw), min(h - by, bh)

                if bw > 10 and bh > 10:
                    crop = alpha_mask[by:by+bh, bx:bx+bw]
                    # Expected transparent region should contain values in the range 20-230
                    solid_pixels = np.sum(crop > 245)
                    total_pixels = crop.size
                    
                    solid_ratio = solid_pixels / total_pixels
                    # If over 80% is solid opaque inside a designated transparent area, flag a defect!
                    if solid_ratio > 0.8:
                        defect_map[by:by+bh, bx:bx+bw] = 255
                        total_defect_score += 0.25
                        
                        repair_suggestions.append({
                            "bbox": [bx, by, bw, bh],
                            "strategy": "restore_transparency",
                            "severity": float(solid_ratio)
                        })

            score = float(np.clip(1.0 - total_defect_score, 0.4, 1.0))
            return {
                "quality_score": score,
                "defect_map": defect_map,
                "repair_suggestions": repair_suggestions
            }

        except Exception as e:
            print(f"[-] TransparencyQualityRuntime error: {e}")
            return {
                "quality_score": 0.85,
                "defect_map": defect_map,
                "repair_suggestions": []
            }
