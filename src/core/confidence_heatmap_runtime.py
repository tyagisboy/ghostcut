import numpy as np
import cv2
from src.core.base_quality_runtime import BaseQualityRuntime

class ConfidenceHeatmapRuntime(BaseQualityRuntime):
    """
    Fuses all spatial defect maps (edge, alpha, spill, stability, transparency)
    into a unified Quality Heatmap and compiles the Repair Priority Map.
    """
    def __init__(self):
        pass

    def get_metadata(self) -> dict:
        return {
            "id": "confidence_heatmap",
            "name": "Confidence Heatmap Fusion",
            "dependencies": [],
            "execution_cost": 1.0
        }

    def evaluate(self, img_bgr: np.ndarray, alpha_mask: np.ndarray, vision_graph: dict = None, context: dict = None) -> dict:
        """
        Consolidates defect maps from previous quality checks.
        """
        pass

    def fuse_heatmaps(self, h: int, w: int, quality_results: dict) -> dict:
        """
        Combines spatial maps from evaluated runtimes.
        """
        overall_heatmap = np.zeros((h, w), dtype=np.float32)
        repair_priority_map = np.zeros((h, w), dtype=np.uint8)

        # Retrieve individual defect maps
        # 1. Edge defects
        if "edge_quality" in quality_results:
            overall_heatmap += 0.3 * quality_results["edge_quality"].get("defect_map", 0.0)
            
        # 2. Alpha transitions
        if "alpha_quality" in quality_results:
            overall_heatmap += 0.3 * quality_results["alpha_quality"].get("defect_map", 0.0)
            
        # 3. Floating speckles / holes
        if "mask_stability" in quality_results:
            overall_heatmap += 0.2 * quality_results["mask_stability"].get("defect_map", 0.0)
            
        # 4. White/dark halos and color spills
        if "halo_spill" in quality_results:
            overall_heatmap += 0.4 * quality_results["halo_spill"].get("defect_map", 0.0)
            
        # 5. Missing glass/metal transparency
        if "transparency_quality" in quality_results:
            overall_heatmap += 0.4 * quality_results["transparency_quality"].get("defect_map", 0.0)

        # Clip values to standard range
        overall_heatmap = np.clip(overall_heatmap, 0.0, 255.0).astype(np.uint8)

        # Compile repair priority map: prioritizes boundaries showing defects
        # Priority is scaled higher in high-value detail areas
        repair_priority_map[overall_heatmap > 50] = 127
        repair_priority_map[overall_heatmap > 150] = 255

        # Calculate average overall quality score from fused result
        mean_defect = np.mean(overall_heatmap)
        overall_score = float(np.clip(1.0 - (mean_defect / 180.0), 0.3, 1.0))

        return {
            "overall_score": overall_score,
            "overall_heatmap": overall_heatmap,
            "repair_priority_map": repair_priority_map
        }
