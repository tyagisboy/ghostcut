import numpy as np

class AlphaContext:
    """
    Immutable input state holding initial values required by AIE matting solvers.
    """
    def __init__(self, img_bgr: np.ndarray, mask: np.ndarray, perception_graph: dict = None, confidence_maps: dict = None, quality_maps: dict = None):
        self.img_bgr = img_bgr
        self.mask = mask
        self.perception_graph = perception_graph if perception_graph is not None else {}
        self.confidence_maps = confidence_maps if confidence_maps is not None else {}
        self.quality_maps = quality_maps if quality_maps is not None else {}
