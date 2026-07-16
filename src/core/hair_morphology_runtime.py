import cv2
import numpy as np
from dataclasses import dataclass, field
from typing import Literal

from src.core.base_cognitive_runtime import BaseCognitiveRuntime

@dataclass(frozen=True)
class HairPolicyRecommendation:
    alpha_mode: Literal['cluster_preserve', 'strand_preserve', 'continuous', 'conservative']
    trimap_half_width_px: tuple[float, float]
    guided_radius_px: tuple[float, float]
    alpha_expansion_limit_px: float
    alpha_contraction_limit_px: float
    decontamination_strength: tuple[float, float]
    sharpening_strength: tuple[float, float]
    repair_priority: float
    protected_mask_weight: float
    rationale: list[str] = field(default_factory=list)

class HairMorphologyRuntime(BaseCognitiveRuntime):
    """
    GhostCut v8.5 Hair Morphology Runtime.
    Characterizes candidate hair regions for production quality intelligence policy compiler.
    """
    def __init__(self):
        self.runtime_id = "hair_morphology"

    def get_metadata(self) -> dict:
        return {
            "id": self.runtime_id,
            "version": "8.5",
            "dependencies": ["hair", "edge"],
            "execution_cost": 4.0
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
        
        # Preconditions check
        img = context.img_bgr
        alpha = getattr(context, "alpha", None)
        if alpha is None and "alpha" in context.cache:
            alpha = context.cache["alpha"]
        if alpha is None:
            # Fallback to mask if alpha is not yet computed/cached
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
            # Estimate morphology metrics
            result = self._analyze_morphology(img, alpha, context)
            
            # Pack findings/evidence
            from src.core.alpha_engine.alpha_result import Finding, Evidence
            finding_id = f"hair_morph_roi_{int(start)}"
            
            finding = {
                "finding_id": finding_id,
                "kind": "low_confidence" if result["evidence_confidence"] < 0.5 else "transition_mismatch",
                "roi": result["roi"],
                "severity": 1.0 - result["evidence_confidence"],
                "confidence": result["evidence_confidence"],
                "evidence_ids": (finding_id + "_ev",),
                "recommendation": str(result["policy_recommendation"].alpha_mode)
            }
            
            evidence = {
                "evidence_id": finding_id + "_ev",
                "runtime_id": self.runtime_id,
                "measurement": {
                    "density": result["density"],
                    "curl_score": result["curl_score"],
                    "strand_width_px": result["strand_width_px"],
                    "orientation_coherence": result["orientation_coherence"],
                    "flyaway_score": result["flyaway_score"],
                    "transparency_score": result["transparency_score"]
                },
                "calibration_version": "v8.5",
                "confidence": result["evidence_confidence"]
            }
            
            # Store in context cache
            context.cache["hair_morphology_result"] = result
            
            dur = (time.time() - start) * 1000.0
            return RuntimeResult(
                runtime_id=self.runtime_id,
                observations=[finding],
                evidence=[evidence],
                confidence=result["evidence_confidence"],
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

    def _analyze_morphology(self, img: np.ndarray, alpha: np.ndarray, context) -> dict:
        h, w = alpha.shape[:2]
        
        # 1. Estimate ROI bounds around active hair transitions
        gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
        transition = ((alpha > 15) & (alpha < 240)).astype(np.uint8) * 255
        
        y_idx, x_idx = np.where(transition > 0)
        if len(y_idx) > 0:
            ymin, ymax = int(np.min(y_idx)), int(np.max(y_idx))
            xmin, xmax = int(np.min(x_idx)), int(np.max(x_idx))
            roi = [xmin, ymin, xmax - xmin, ymax - ymin]
        else:
            roi = [0, 0, w, h]
            
        # 2. Extract Sobel gradients for orientation/coherence/curl
        sobel_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        
        mag, angle = cv2.cartToPolar(sobel_x, sobel_y, angleInDegrees=True)
        
        # Local stats inside transition zone
        if len(y_idx) > 0:
            local_mags = mag[y_idx, x_idx]
            local_angles = angle[y_idx, x_idx]
            
            density = float(np.sum(local_mags > 25.0) / len(y_idx))
            
            # Curl is angle variance
            curl_score = float(np.var(local_angles) / 10000.0)
            curl_score = min(1.0, max(0.0, curl_score))
            
            # Orientation coherence: check alignment strength
            orientation_coherence = float(np.sum(local_mags > 40.0) / (np.sum(local_mags > 10.0) + 1e-5))
            orientation_coherence = min(1.0, max(0.0, orientation_coherence))
            
            # Flyaways are isolated low-alpha high frequency details
            flyaway_score = float(np.sum((alpha[y_idx, x_idx] < 120) & (local_mags > 30.0)) / len(y_idx))
            flyaway_score = min(1.0, max(0.0, flyaway_score))
            
            transparency_score = float(np.sum((alpha[y_idx, x_idx] > 30) & (alpha[y_idx, x_idx] < 180)) / len(y_idx))
            transparency_score = min(1.0, max(0.0, transparency_score))
        else:
            density = 0.0
            curl_score = 0.0
            orientation_coherence = 0.0
            flyaway_score = 0.0
            transparency_score = 0.0
            
        evidence_conf = float(density * 0.4 + orientation_coherence * 0.4 + 0.2)
        evidence_conf = min(1.0, max(0.0, evidence_conf))
        
        # Decide Policy
        if flyaway_score > 0.4:
            alpha_mode = "strand_preserve"
            trimap_width = (8.0, 12.0)
            decon_strength = (0.8, 0.95)
        elif density > 0.6:
            alpha_mode = "cluster_preserve"
            trimap_width = (4.0, 8.0)
            decon_strength = (0.5, 0.75)
        else:
            alpha_mode = "conservative"
            trimap_width = (2.0, 4.0)
            decon_strength = (0.1, 0.3)
            
        policy = HairPolicyRecommendation(
            alpha_mode=alpha_mode,
            trimap_half_width_px=trimap_width,
            guided_radius_px=(3.0, 7.0),
            alpha_expansion_limit_px=2.0 if alpha_mode == "cluster_preserve" else 8.0,
            alpha_contraction_limit_px=4.0,
            decontamination_strength=decon_strength,
            sharpening_strength=(0.0, 0.2),
            repair_priority=float(0.8 if alpha_mode == "strand_preserve" else 0.4),
            protected_mask_weight=0.9,
            rationale=[f"Selected {alpha_mode} mode based on density={density:.2f}, flyaways={flyaway_score:.2f}"]
        )
        
        return {
            "roi": roi,
            "density": density,
            "curl_score": curl_score,
            "strand_width_px": 2.5 if density > 0.3 else None,
            "orientation_coherence": orientation_coherence,
            "flyaway_score": flyaway_score,
            "transparency_score": transparency_score,
            "evidence_confidence": evidence_conf,
            "policy_recommendation": policy
        }
