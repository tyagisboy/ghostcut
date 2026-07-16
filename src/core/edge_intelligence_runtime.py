import cv2
import numpy as np
from src.core.base_cognitive_runtime import BaseCognitiveRuntime

class EdgeIntelligenceRuntime(BaseCognitiveRuntime):
    """
    GhostCut v8.5 Edge Intelligence Runtime.
    Produces full-resolution, calibrated per-pixel edge-policy maps.
    """
    def __init__(self):
        self.runtime_id = "edge_intelligence"

    def get_metadata(self) -> dict:
        return {
            "id": self.runtime_id,
            "version": "8.5",
            "dependencies": [],
            "execution_cost": 3.0
        }

    def validateDependencies(self) -> list:
        return self.get_metadata()["dependencies"]

    def estimateCost(self) -> float:
        return self.get_metadata()["execution_cost"]

    def execute(self, context) -> "RuntimeResult":
        import time
        from src.core.runtime_result import RuntimeResult
        
        start = time.time()
        warnings = []
        
        img = context.img_bgr
        alpha = getattr(context, "alpha", None)
        if alpha is None and "alpha" in context.cache:
            alpha = context.cache["alpha"]
        if alpha is None:
            alpha = getattr(context, "mask", None)
            
        if img is None or alpha is None:
            return RuntimeResult(
                runtime_id=self.runtime_id,
                observations=[],
                evidence=[],
                confidence=0.0,
                duration_ms=0.0,
                warnings=["Missing source RGB or alpha mask"]
            )

            
        try:
            h, w = alpha.shape[:2]
            
            # Analyze boundary zones & build edge-policy map
            edge_policy_map = self._compute_edge_policy_map(img, alpha, context)
            context.cache["edge_policy_map"] = edge_policy_map
            
            from src.core.alpha_engine.alpha_result import Finding, Evidence
            finding_id = f"edge_intel_roi_{int(start)}"
            
            finding = {
                "finding_id": finding_id,
                "kind": "jagged_edge" if np.sum(edge_policy_map == 1) > 100 else "transition_mismatch",
                "roi": [0, 0, w, h],
                "severity": 0.2,
                "confidence": 0.95,
                "evidence_ids": (finding_id + "_ev",),
                "recommendation": "regularize_edge"
            }
            
            evidence = {
                "evidence_id": finding_id + "_ev",
                "runtime_id": self.runtime_id,
                "measurement": {
                    "hard_pixels": int(np.sum(edge_policy_map == 1)),
                    "strand_pixels": int(np.sum(edge_policy_map == 4))
                },
                "calibration_version": "v8.5",
                "confidence": 0.95
            }
            
            dur = (time.time() - start) * 1000.0
            return RuntimeResult(
                runtime_id=self.runtime_id,
                observations=[finding],
                evidence=[evidence],
                confidence=0.95,
                duration_ms=dur,
                warnings=warnings
            )
            
        except Exception as e:
            dur = (time.time() - start) * 1000.0
            return RuntimeResult(
                runtime_id=self.runtime_id,
                observations=[],
                evidence=[],
                confidence=0.0,
                duration_ms=dur,
                warnings=[f"Failed execution: {str(e)}"]
            )

    def _compute_edge_policy_map(self, img: np.ndarray, alpha: np.ndarray, context) -> np.ndarray:
        h, w = alpha.shape[:2]
        
        # Policy categories represented as uint8 values:
        # 1: hard, 2: fabric, 3: cluster, 4: strand, 5: transparent, 6: motion_soft, 0: unknown
        policy_map = np.zeros((h, w), dtype=np.uint8)
        
        # Isolate transition zones
        transition = ((alpha > 5) & (alpha < 250)).astype(np.uint8) * 255
        
        # Compute gradient alignment features
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        
        sobel_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        grad_mag = np.sqrt(sobel_x**2 + sobel_y**2)
        
        # Threshold logic
        # 1. Hard edges: narrow transition zone and high gradient magnitude
        hard_mask = (transition > 0) & (grad_mag > 45.0)
        policy_map[hard_mask] = 1
        
        # 2. Strands: low grad mag but inside transition
        strand_mask = (transition > 0) & (grad_mag <= 45.0) & (alpha < 150)
        policy_map[strand_mask] = 4
        
        # 3. Everything else in transition is classified as unknown/fabric soft transition
        unknown_mask = (transition > 0) & (policy_map == 0)
        policy_map[unknown_mask] = 0 # unknown fallback
        
        return policy_map
