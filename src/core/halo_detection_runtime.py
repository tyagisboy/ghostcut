import cv2
import numpy as np
from src.core.base_cognitive_runtime import BaseCognitiveRuntime

class HaloDetectionRuntime(BaseCognitiveRuntime):
    """
    GhostCut v8.5 Halo Detection Runtime.
    Localizes light, dark, and chroma background bleed halos along boundary contours.
    """
    def __init__(self):
        self.runtime_id = "halo_detection"

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
            defect_map = np.zeros((h, w), dtype=np.uint8)
            findings = []
            evidences = []
            
            # 1. Estimate background color dynamically from background region
            bg_mask = (alpha < 10)
            if np.sum(bg_mask) > 100:
                bg_color = np.median(img[bg_mask], axis=0)  # [B, G, R]
            else:
                # Fallback to corners
                corners = [img[0, 0], img[0, -1], img[-1, 0], img[-1, -1]]
                bg_color = np.median(corners, axis=0)
            
            # Store in context cache so LocalRepairRuntime can access it
            context.cache["detected_bg_color"] = bg_color
            
            # 2. Edge boundary ring (dilate 5px minus erode 5px around mask boundary)
            kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (5, 5))
            dilated = cv2.dilate(alpha, kernel)
            eroded = cv2.erode(alpha, kernel)
            boundary_mask = ((dilated > 0) & (eroded < 255)).astype(np.uint8) * 255
            
            boundary_pixels = np.sum(boundary_mask > 0)
            severity = 0.0
            
            if boundary_pixels >= 100:
                # Color distance check
                diff = img.astype(np.float32) - bg_color.astype(np.float32)
                dist_to_bg = np.sqrt(np.sum(diff**2, axis=2))
                
                # Check for bright background bleed (light/white halos)
                white_halo_mask = (boundary_mask > 0) & (dist_to_bg < 45.0) & (alpha > 50)
                white_halo_count = np.sum(white_halo_mask)
                
                # Check for color spill (chroma discrepancy)
                hsv = cv2.cvtColor(img, cv2.COLOR_BGR2HSV)
                hue = hsv[:, :, 0]
                sat = hsv[:, :, 1]
                spill_mask = (boundary_mask > 0) & (sat > 70) & ((hue > 30) & (hue < 90))
                spill_count = np.sum(spill_mask)
                
                defect_map[white_halo_mask] = 255
                defect_map[spill_mask] = 255
                
                halo_ratio = float(white_halo_count / boundary_pixels)
                spill_ratio = float(spill_count / boundary_pixels)
                
                severity = float(np.clip(1.8 * halo_ratio + 1.2 * spill_ratio, 0.0, 1.0))
                
                if severity > 0.05:
                    y_idx, x_idx = np.where(defect_map > 0)
                    if len(y_idx) > 0:
                        ymin, ymax = int(np.min(y_idx)), int(np.max(y_idx))
                        xmin, xmax = int(np.min(x_idx)), int(np.max(x_idx))
                        roi = [xmin, ymin, xmax - xmin, ymax - ymin]
                        
                        finding_id = f"halo_finding_{int(start)}"
                        findings.append({
                            "finding_id": finding_id,
                            "kind": "halo_chroma" if spill_ratio > halo_ratio else "halo_light",
                            "roi": roi,
                            "severity": severity,
                            "confidence": 0.95,
                            "evidence_ids": (finding_id + "_ev",),
                            "recommendation": "decontaminate" if spill_ratio > halo_ratio else "contract_matte"
                        })
                        
                        evidences.append({
                            "evidence_id": finding_id + "_ev",
                            "runtime_id": self.runtime_id,
                            "measurement": {
                                "halo_pixels": int(white_halo_count),
                                "spill_pixels": int(spill_count),
                                "halo_ratio": halo_ratio,
                                "spill_ratio": spill_ratio
                            },
                            "calibration_version": "v8.5",
                            "confidence": 0.95
                        })
                        
            context.cache["halo_detection_result"] = {
                "defect_map": defect_map,
                "severity": severity,
                "findings": findings,
                "evidences": evidences
            }
            
            dur = (time.time() - start) * 1000.0
            return RuntimeResult(
                runtime_id=self.runtime_id,
                observations=findings,
                evidence=evidences,
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
