import cv2
import numpy as np
from src.core.base_cognitive_runtime import BaseCognitiveRuntime

class LocalRepairRuntime(BaseCognitiveRuntime):
    """
    GhostCut v8.5 Local Repair Runtime.
    Performs transactional, bounded local alpha repairs (contraction, decontamination)
    and verifies metric gains before committing.
    """
    def __init__(self):
        self.runtime_id = "local_repair"

    def get_metadata(self) -> dict:
        return {
            "id": self.runtime_id,
            "version": "8.5",
            "dependencies": ["quality_intelligence"],
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
            repaired_alpha = alpha.copy()
            
            # Fetch findings from quality intelligence
            report = context.cache.get("quality_report", {})
            findings = report.get("findings", [])
            
            # Fetch detected background color
            bg_color = context.cache.get("detected_bg_color")
            if bg_color is None:
                # Fallback to corners
                corners = [img[0, 0], img[0, -1], img[-1, 0], img[-1, -1]]
                bg_color = np.median(corners, axis=0)
                
            repair_records = []
            
            for idx, finding in enumerate(findings):
                kind = finding.get("kind")
                roi = finding.get("roi")
                rec = finding.get("recommendation")
                severity = finding.get("severity", 0.5)
                
                if not roi or len(roi) != 4:
                    continue
                    
                rx, ry, rw, rh = map(int, roi)
                rx, ry = max(0, rx), max(0, ry)
                rw, rh = min(w - rx, rw), min(h - ry, rh)
                
                if rw <= 0 or rh <= 0:
                    continue
                    
                # Transactional stage: take snapshot
                snapshot = repaired_alpha[ry:ry+rh, rx:rx+rw].copy()
                img_crop = img[ry:ry+rh, rx:rx+rw]
                
                # Calculate distance to background color locally
                diff_crop = img_crop.astype(np.float32) - bg_color.astype(np.float32)
                dist_crop = np.sqrt(np.sum(diff_crop**2, axis=2))
                
                # Apply operator
                repaired_crop = snapshot.copy()
                operator = "none"
                params = {}
                
                # Check background brightness
                is_bright_bg = (np.mean(bg_color) > 200.0)
                
                # Fetch material maps for detail-aware preservation
                material_maps = context.cache.get("material_maps")
                if material_maps is not None:
                    mat_crop = material_maps[ry:ry+rh, rx:rx+rw]
                    # Indices: 1=Hair, 2=Fur, 8=Lace, 9=Feather
                    protection = mat_crop[:, :, 1] + mat_crop[:, :, 2] + mat_crop[:, :, 8] + mat_crop[:, :, 9]
                    protection = np.clip(protection, 0.0, 1.0)
                else:
                    protection = np.zeros(snapshot.shape, dtype=np.float32)
                
                if rec == "contract_matte" or kind == "halo_light" or (is_bright_bg and (rec == "decontaminate" or kind == "halo_chroma")):
                    # Material-aware alpha contraction
                    erode_iter = 3 if is_bright_bg else 2
                    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
                    
                    eroded_hair = cv2.erode(snapshot, kernel, iterations=1)
                    eroded_hard = cv2.erode(snapshot, kernel, iterations=erode_iter)
                    
                    # Blend: 1-pixel erosion for hair/detail (protection=1.0), full erosion for skin/clothing (protection=0.0)
                    repaired_crop = (eroded_hair.astype(np.float32) * protection + 
                                     eroded_hard.astype(np.float32) * (1.0 - protection)).astype(np.uint8)
                    operator = "material_aware_contraction"
                    params = {"erode_iterations_hard": erode_iter, "erode_iterations_hair": 1}
                    
                elif rec == "decontaminate" or kind == "halo_chroma":
                    # Color spill: erode and smooth transition zone
                    kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (3, 3))
                    eroded = cv2.erode(snapshot, kernel, iterations=1)
                    smoothed = cv2.GaussianBlur(eroded, (3, 3), 0)
                    repaired_crop = cv2.addWeighted(snapshot, 0.3, smoothed, 0.7, 0)
                    
                    # Protect hair details even in smoothing
                    repaired_crop = (snapshot.astype(np.float32) * protection + 
                                     repaired_crop.astype(np.float32) * (1.0 - protection)).astype(np.uint8)
                    operator = "color_spill_regularization"
                    params = {"smooth_ksize": 3}
                    
                # Verification step: measure halo/bleed pixels before vs after using dynamic threshold
                defect_threshold = 120.0 if is_bright_bg else 60.0
                defect_pixels_before = np.sum((snapshot > 15) & (dist_crop < defect_threshold))
                defect_pixels_after = np.sum((repaired_crop > 15) & (dist_crop < defect_threshold))
                
                # Decision logic: Accept only if defect count decreases OR if it is regularization
                accepted = False
                if operator == "color_spill_regularization" or defect_pixels_after < defect_pixels_before or defect_pixels_before == 0:
                    repaired_alpha[ry:ry+rh, rx:rx+rw] = repaired_crop
                    accepted = True
                    outcome = f"COMMIT ({operator}: {defect_pixels_before} -> {defect_pixels_after})"
                else:
                    outcome = f"ROLLBACK (No improvement: {defect_pixels_before} -> {defect_pixels_after})"
                    
                repair_records.append({
                    "index": idx + 1,
                    "bbox": [rx, ry, rw, rh],
                    "strategy": rec,
                    "operator": operator,
                    "parameters": params,
                    "accepted": accepted,
                    "outcome": outcome
                })
                
            # Update the global alpha in cache
            context.cache["alpha"] = repaired_alpha
            context.cache["repair_records"] = repair_records
            
            dur = (time.time() - start) * 1000.0
            return RuntimeResult(
                runtime_id=self.runtime_id,
                observations=[],
                evidence=[],
                confidence=1.0,
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
