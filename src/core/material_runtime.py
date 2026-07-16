import cv2
import numpy as np
from src.core.base_runtime import BaseRuntime
from src.core.material import MaterialClassifier

class MaterialRuntime(BaseRuntime):
    """
    SDK compliant Material Intelligence analyzer.
    """
    def __init__(self):
        self.classifier = MaterialClassifier()

    def initialize(self, config: dict) -> None:
        pass

    def get_metadata(self) -> dict:
        return {
            "id": "material",
            "name": "Material Intelligence",
            "dependencies": ["subject"],
            "execution_cost": 2.5,
            "quality_impact": 8.0,
            "requires_mask": True
        }

    def analyze(self, img_bgr: np.ndarray, mask: np.ndarray, features: dict = None, subjects: list = None, context: dict = None) -> dict:

        """
        Executes pixel-wise material analysis.
        Filters materials hierarchically based on subject list.
        Returns maps of shape (H, W, 12) and summary scores.
        """
        try:
            prob_maps, scores = self.classifier.compute_material_maps(img_bgr, mask)
            
            # Retrieve subjects list for hierarchical filtering
            if subjects is None and features is not None:
                subjects = features.get("subjects")
                
            if subjects:
                allowed_materials = set()
                for subj in subjects:
                    if subj == "Human":
                        allowed_materials.update(["Skin", "Hair", "Fabric", "Glass", "Plastic", "Metal", "Leather", "Lace"])
                    elif subj == "Animal":
                        allowed_materials.update(["Fur", "Skin", "Leather", "Feather", "Metal"])
                    elif subj == "Plant":
                        allowed_materials.update(["Fabric", "Glass", "Plastic"])
                    elif subj == "Product":
                        allowed_materials.update(["Fabric", "Glass", "Plastic", "Metal", "Leather", "Lace"])
                    elif subj == "Mixed":
                        allowed_materials = None
                        break
                
                if allowed_materials is not None:
                    # Filter maps and scores
                    for idx, mat in enumerate(self.classifier.materials):
                        if mat not in allowed_materials:
                            scores[mat] = 0.0
                            prob_maps[:, :, idx] = 0.0
            
            return {
                "maps": prob_maps,
                "scores": scores
            }
        except Exception as e:
            h, w = mask.shape[:2]
            # Fallback
            prob_maps = np.zeros((h, w, 12), dtype=np.float32)
            prob_maps[:, :, 3] = (mask.astype(np.float32) / 255.0)  # Fabric fallback
            scores = {m: 0.0 for m in self.classifier.materials}
            scores["Fabric"] = 1.0
            return {
                "maps": prob_maps,
                "scores": scores
            }


    def validate(self) -> list:
        return []
