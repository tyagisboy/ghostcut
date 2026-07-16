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
        h, w = mask.shape[:2]
        
        # 1. Match active regions inside perception state
        regions = context.perception_graph.get("regions", ["skin", "hair"])
        primary_region = regions[0] if regions else "skin"
        
        # 2. Resolve boundary zones
        trimap = self.boundary_solver.solve_boundary(img, mask, primary_region)
        
        # 3. Apply policies to build composite refined alpha
        policy = self.policy_manager.get_policy(primary_region.capitalize())
        
        # Simulating matting compilation math using boundary solver and texture details
        # For transition zone (128), we apply a local soft guide blend
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
