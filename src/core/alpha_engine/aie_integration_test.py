import os
import sys
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from src.core.alpha_engine.alpha_context import AlphaContext
from src.core.alpha_engine.alpha_engine import AlphaEngine
from src.core.alpha_engine.alpha_region import AlphaRegion
from src.core.alpha_engine.alpha_policy import AlphaPolicy

def test_alpha_engine_execution():
    print("[*] Testing AIE AlphaEngine execution...")
    dummy_img = np.zeros((256, 256, 3), dtype=np.uint8)
    dummy_img[64:192, 64:192] = [200, 180, 150]  # Foreground block
    
    dummy_mask = np.zeros((256, 256), dtype=np.uint8)
    dummy_mask[64:192, 64:192] = 255
    
    context = AlphaContext(
        img_bgr=dummy_img,
        mask=dummy_mask,
        perception_graph={"regions": ["hair", "skin"]}
    )
    
    engine = AlphaEngine()
    res = engine.execute(context)
    
    assert res.alpha is not None
    assert "hair" in res.region_alphas
    assert res.alpha_confidence is not None
    
    print("  [+] Alpha Result generated. Target alpha shape:", res.alpha.shape)
    print("  [+] Alpha Engine quality metrics:", engine.last_quality_metrics)
    assert engine.last_quality_metrics["quality_grade"] in ["A", "B", "C"]

def test_boundary_solver():
    print("[*] Testing Adaptive Boundary Solver texture gradients...")
    from src.core.alpha_engine.boundary_solver import AdaptiveBoundarySolver
    solver = AdaptiveBoundarySolver()
    
    dummy_img = np.zeros((256, 256, 3), dtype=np.uint8)
    dummy_mask = np.zeros((256, 256), dtype=np.uint8)
    dummy_mask[100:150, 100:150] = 255
    
    trimap = solver.solve_boundary(dummy_img, dummy_mask, "hair")
    assert np.any(trimap == 128)  # Transition zone
    assert np.any(trimap == 255)  # Foreground zone
    print("  [+] Trimap resolved transition zones successfully.")

def main():
    print("======================================")
    print("Running GhostCut AIE v7.0 Unit Tests")
    print("======================================")
    
    test_alpha_engine_execution()
    test_boundary_solver()
    
    print("\n======================================")
    print("All AIE v7.0 Unit Tests Passed.")
    print("======================================")

if __name__ == "__main__":
    main()
