import numpy as np

class AlphaResult:
    """
    Holds outcomes compiled by the Unified Alpha Intelligence Engine.
    """
    def __init__(self, alpha: np.ndarray, region_alphas: dict = None, alpha_confidence: np.ndarray = None):
        self.alpha = alpha
        self.region_alphas = region_alphas if region_alphas is not None else {}
        self.alpha_confidence = alpha_confidence if alpha_confidence is not None else np.ones_like(alpha, dtype=np.float32)
