import numpy as np

class BaseRuntime:
    """
    Abstract Base Class defining the Plugin Interface for all GhostCut Intelligence Runtimes.
    """
    def initialize(self, config: dict) -> None:
        """
        Optional initialization logic.
        """
        pass

    def get_metadata(self) -> dict:
        """
        Returns runtime metadata for scheduling and dependency sorting:
        - id: Unique string identifier
        - name: Friendly name for UI logs
        - dependencies: List of runtime IDs this runtime depends on
        - execution_cost: CPU complexity weight (1.0 = low, 10.0 = high)
        - quality_impact: Importance to output quality (1.0 = minor, 10.0 = critical)
        - requires_mask: Bool indicating if mask is required for analysis (post-inference only)
        """
        raise NotImplementedError("Runtimes must implement get_metadata method.")

    def analyze(self, img_bgr: np.ndarray, mask: np.ndarray = None, context: dict = None) -> dict:
        """
        Orchestrates runtime feature estimation.
        - context: Dictionary storing results of preceding runtimes in the pipeline.
        """
        raise NotImplementedError("Runtimes must implement analyze method.")

    def validate(self) -> list:
        """
        Returns list of health check warnings.
        """
        return []
