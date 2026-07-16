import numpy as np

class BaseQualityRuntime:
    """
    Abstract Base Class defining the Quality Intelligence SDK Contract.
    Evaluates segmentation/matting quality metrics, outputs defect heatmaps,
    and returns localized repair instructions.
    """
    def initialize(self, config: dict) -> None:
        """
        Optional initialization logic.
        """
        pass

    def get_metadata(self) -> dict:
        """
        Returns metadata for quality evaluation tracking:
        - id: Unique quality runtime ID
        - name: Friendly name for GUI
        - dependencies: List of required quality runtimes
        - execution_cost: CPU complexity weight (1.0 = low, 10.0 = high)
        """
        raise NotImplementedError("Quality runtimes must implement get_metadata method.")

    def evaluate(self, img_bgr: np.ndarray, alpha_mask: np.ndarray, vision_graph: dict = None, context: dict = None) -> dict:
        """
        Main evaluation entrypoint.
        Returns:
            quality_score: float (0.0 = total failure, 1.0 = flawless quality)
            defect_map: np.ndarray (spatial representation of defects: 0 = perfect, 255 = critical error)
            repair_suggestions: list of dicts detailing crop locations and recommended strategies
        """
        raise NotImplementedError("Quality runtimes must implement evaluate method.")
