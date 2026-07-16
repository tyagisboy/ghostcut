import numpy as np
from src.core.image_profile import ImageProfile
from src.core.evidence_graph import EvidenceGraph
from src.core.belief_graph import BeliefGraph

class ExecutionContext:
    """
    Immutable-like shared context carrying state variables
    throughout the cognitive vision runtime execution.
    """
    def __init__(self, img_bgr: np.ndarray, profile: ImageProfile = None, hardware: dict = None, evidence_graph: EvidenceGraph = None, belief_graph: BeliefGraph = None, telemetry = None):
        self.img_bgr = img_bgr
        self.profile = profile
        self.hardware = hardware if hardware is not None else {}
        self.evidence_graph = evidence_graph if evidence_graph is not None else EvidenceGraph()
        self.belief_graph = belief_graph if belief_graph is not None else BeliefGraph()
        self.telemetry = telemetry
        self.cache = {}
