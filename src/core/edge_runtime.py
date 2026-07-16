import cv2
import numpy as np
from src.core.base_runtime import BaseRuntime
from src.core.edge import EdgeClassifier

class EdgeRuntime(BaseRuntime):
    """
    SDK compliant Edge Intelligence analyzer.
    """
    def __init__(self):
        self.classifier = EdgeClassifier()

    def initialize(self, config: dict) -> None:
        pass

    def get_metadata(self) -> dict:
        return {
            "id": "edge",
            "name": "Edge Intelligence",
            "dependencies": ["material"],
            "execution_cost": 2.0,
            "quality_impact": 8.0,
            "requires_mask": True
        }

    def analyze(self, img_bgr: np.ndarray, mask: np.ndarray, material_maps: np.ndarray = None, context: dict = None) -> dict:

        """
        Generates pixel-wise edge classification map.
        """
        try:
            edge_map = self.classifier.classify_edges(img_bgr, mask, material_maps)
            # Summarize classes present
            classes_present = []
            for val in range(10):
                if np.any(edge_map == val):
                    classes_present.append(self.classifier.edge_classes[val])
            return {
                "edge_map": edge_map,
                "classes": classes_present
            }
        except Exception as e:
            h, w = mask.shape[:2]
            return {
                "edge_map": np.full((h, w), 1, dtype=np.int8),  # Default all Soft
                "classes": ["Soft"]
            }

    def validate(self) -> list:
        return []
