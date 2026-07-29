import os
import sys
import cv2
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from src.core.alpha_engine.alpha_context import AlphaContext
from src.core.alpha_engine.alpha_result import AlphaResult
from src.core.alpha_engine.alpha_region import AlphaRegion
from src.core.alpha_engine.alpha_policy import AlphaPolicy
from src.core.alpha_engine.boundary_solver import AdaptiveBoundarySolver
from src.core.alpha_engine.quality_analyzer import AlphaQualityAnalyzer
from src.core.alpha_engine.alpha_cache import AlphaCache

class AlphaEngine:
    """
    APF/AIE v7.0 Core Unified Alpha Intelligence Engine.
    Executes boundary solvers, applies matting parameters, and runs quality analyzers.
    """
    def __init__(self):
        self.boundary_solver = AdaptiveBoundarySolver()
        self.quality_analyzer = AlphaQualityAnalyzer()
        self.policy_manager = AlphaPolicy()
        self.cache = AlphaCache()
        
        self.last_quality_metrics = None

    def execute(self, context: AlphaContext) -> AlphaResult:
        """
        Coordinates the alpha compilation loop.
        """
        img = context.img_bgr
        mask = context.mask
        
        # 1. Match active regions inside perception state
        p_graph = getattr(context, "perception_graph", {})
        if isinstance(p_graph, dict):
            regions = p_graph.get("regions", ["skin", "hair"])
        else:
            regions = ["skin", "hair"]
        primary_region = regions[0] if (isinstance(regions, list) and len(regions) > 0) else "skin"
        policy = self.policy_manager.get_policy(primary_region.capitalize())
        
        # Execute ViTMatte transformer refinement if available and processing mode demands high detail
        has_run_vitmatte = False
        if hasattr(self, "vitmatte_func") and self.vitmatte_func is not None:
            processing_mode = getattr(context, "processing_mode", "fast")
            material_maps = getattr(context, "material_maps", None)
            hair_prob = material_maps[:, :, 1] if material_maps is not None else None
            has_hair_detail = np.any(hair_prob > 0.15) if hair_prob is not None else True
            
            if processing_mode in ["quality", "ultra"] or has_hair_detail:
                try:
                    w_detail = getattr(context, "w_detail", None)
                    vit_mask = self.vitmatte_func(img, mask, w_detail)
                    if vit_mask is not None:
                        refined_alpha = vit_mask
                        has_run_vitmatte = True
                except Exception as vm_err:
                    print(f"[-] ViTMatte execution error inside AlphaEngine: {vm_err}")
        
        if not has_run_vitmatte:
            if hasattr(self, "matting_func") and self.matting_func is not None:
                # Extract dynamically routed parameters from context with safe fallbacks
                fg_thresh = getattr(context, "fg_thresh", 240)
                bg_thresh = getattr(context, "bg_thresh", 40)
                erode_size = getattr(context, "erode_size", 3)
                preserve_transparency = getattr(context, "preserve_transparency", False)
                sharpness = getattr(context, "sharpness", 0)
                focus_thresh = getattr(context, "focus_thresh", 0.0)
                w_detail = getattr(context, "w_detail", None)
                disable_quality_loop = getattr(context, "disable_quality_loop", False)
                radius_field = getattr(context, "radius_field", None)
                material_maps = getattr(context, "material_maps", None)
                
                refined_alpha = self.matting_func(
                    img, mask, fg_thresh, bg_thresh, erode_size,
                    preserve_transparency, sharpness, focus_thresh,
                    w_detail, disable_quality_loop, radius_field, material_maps
                )
            else:
                # Fallback simulator path for mock execution compatibility / AIE integration tests
                trimap = self.boundary_solver.solve_boundary(img, mask, primary_region)
                refined_alpha = mask.copy()
                transition_mask = (trimap == 128)
                
                if np.any(transition_mask):
                    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
                    # Normalize gray values in transition zone
                    guide_vals = gray[transition_mask].astype(np.float32) / 255.0
                    
                    # Smoothness policy scaling
                    smooth_coeff = policy.get("smoothness", 0.5)
                    blend = smooth_coeff * guide_vals + (1.0 - smooth_coeff) * 0.5
                    
                    refined_alpha[transition_mask] = (blend * 255.0).astype(np.uint8)
            
        # 4. Generate region alpha maps and confidence mapping
        region_alphas = {primary_region: refined_alpha.copy()}
        alpha_conf = np.ones_like(refined_alpha, dtype=np.float32) * float(policy.get("edge_gradient_scale", 1.0) / 2.0)
        
        # 5. Measure quality matrix benchmarks against initial mask
        self.last_quality_metrics = self.quality_analyzer.analyze_quality(refined_alpha, mask)
        
        return AlphaResult(
            alpha=refined_alpha,
            region_alphas=region_alphas,
            alpha_confidence=alpha_conf
        )
