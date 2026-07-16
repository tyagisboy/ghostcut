import sys
import numpy as np
import cv2
from src.core.edge_quality_runtime import EdgeQualityRuntime
from src.core.alpha_quality_runtime import AlphaQualityRuntime
from src.core.mask_stability_runtime import MaskStabilityRuntime
from src.core.halo_spill_runtime import HaloSpillRuntime
from src.core.transparency_quality_runtime import TransparencyQualityRuntime
from src.core.region_consistency_runtime import RegionConsistencyRuntime
from src.core.failure_prediction_runtime import FailurePredictionRuntime
from src.core.confidence_heatmap_runtime import ConfidenceHeatmapRuntime
from src.core.local_repair_scheduler import LocalRepairScheduler

def run_v4_2_benchmarks():
    print("[*] Initializing Quality Intelligence v4.2 Benchmark Suite...")
    
    # 1. Create a dummy image and mask with target defects:
    # We create a 256x256 image with:
    # - Solid circle in center (foreground)
    # - 1 floating pixel component (speckle defect)
    # - 1 black hole inside circle (hole defect)
    h, w = 256, 256
    img_bgr = np.zeros((h, w, 3), dtype=np.uint8)
    # Draw green background to trigger color spill check
    img_bgr[:, :, 1] = 200 # Green background
    
    alpha_mask = np.zeros((h, w), dtype=np.uint8)
    cv2.circle(alpha_mask, (128, 128), 60, 255, -1)
    
    # Defect A: Speckle (floating pixels at top-left corner)
    alpha_mask[10:15, 10:15] = 255
    # Paint foreground pixels green-ish at the border to simulate color bleed spill
    cv2.circle(img_bgr, (128, 128), 60, (50, 180, 50), -1) # Green spill inside object
    
    # Defect B: Hole inside circle (black hole at center)
    alpha_mask[126:130, 126:130] = 0
    
    # Defect C: Jagged border (draw curvature spike)
    alpha_mask[128-40:128-20, 128-80:128-60] = 255
    
    print("[*] Evaluating quality indicators on defective mask...")
    
    # 2. Run Quality SDK checks
    edge_q = EdgeQualityRuntime().evaluate(img_bgr, alpha_mask)
    alpha_q = AlphaQualityRuntime().evaluate(img_bgr, alpha_mask)
    stability_q = MaskStabilityRuntime().evaluate(img_bgr, alpha_mask)
    halo_q = HaloSpillRuntime().evaluate(img_bgr, alpha_mask)
    trans_q = TransparencyQualityRuntime().evaluate(img_bgr, alpha_mask)
    cons_q = RegionConsistencyRuntime().evaluate(img_bgr, alpha_mask)
    fail_p = FailurePredictionRuntime().evaluate(img_bgr, alpha_mask)
    
    # 3. Verify defect detections
    # Mask stability should find both floating pixels and holes, pulling stability score down
    assert stability_q["quality_score"] < 1.0
    suggestions = stability_q["repair_suggestions"]
    strategies = [s["strategy"] for s in suggestions]
    assert "delete_speckle" in strategies
    assert "fill_hole" in strategies
    print("[OK] Mask stability properly isolated floating pixels and holes.")

    # Edge quality should find repair suggestions for jaggedness
    assert edge_q["quality_score"] < 1.0
    print("[OK] Edge quality isolated boundary jaggedness.")
    
    # 4. Fuse defect maps
    quality_results = {
        "edge_quality": edge_q,
        "alpha_quality": alpha_q,
        "mask_stability": stability_q,
        "halo_spill": halo_q,
        "transparency_quality": trans_q,
        "region_consistency": cons_q,
        "failure_prediction": fail_p
    }
    
    fusion_runtime = ConfidenceHeatmapRuntime()
    fused = fusion_runtime.fuse_heatmaps(h, w, quality_results)
    initial_score = fused["overall_score"]
    print(f"[*] Fused Initial Quality Score: {initial_score*100:.1f}%")
    
    # 5. Run Local Repair Scheduler to fix suggestions
    print("[*] Invoking Local Repair Scheduler...")
    all_suggestions = stability_q["repair_suggestions"]

        
    repair_scheduler = LocalRepairScheduler()
    repaired_mask, repair_log = repair_scheduler.execute_repairs(img_bgr, alpha_mask, all_suggestions)
    
    # 6. Verify corrections in repaired mask
    # A. Speckle should be gone (value at top left should be 0)
    assert np.all(repaired_mask[10:15, 10:15] == 0)
    print("[OK] Repaired mask: floating pixels successfully deleted.")
    
    # B. Hole should be filled (value at center should be 255)
    assert np.all(repaired_mask[126:130, 126:130] == 255)
    print("[OK] Repaired mask: inner hole successfully filled.")
    
    # 7. Evaluate repaired mask quality to verify improvement
    reconstructed_stability_q = MaskStabilityRuntime().evaluate(img_bgr, repaired_mask)
    # Stability score should now be 1.0 (all floating pixels and holes are gone!)
    assert reconstructed_stability_q["quality_score"] == 1.0
    print("[OK] Repaired mask stability quality score restored to 100.0%.")
    
    # Re-evaluate fused overall score
    reconstructed_results = {
        "edge_quality": EdgeQualityRuntime().evaluate(img_bgr, repaired_mask),
        "alpha_quality": AlphaQualityRuntime().evaluate(img_bgr, repaired_mask),
        "mask_stability": reconstructed_stability_q,
        "halo_spill": HaloSpillRuntime().evaluate(img_bgr, repaired_mask),
        "transparency_quality": TransparencyQualityRuntime().evaluate(img_bgr, repaired_mask),
        "region_consistency": RegionConsistencyRuntime().evaluate(img_bgr, repaired_mask),
        "failure_prediction": FailurePredictionRuntime().evaluate(img_bgr, repaired_mask)
    }
    
    fused_reconstructed = fusion_runtime.fuse_heatmaps(h, w, reconstructed_results)
    repaired_score = fused_reconstructed["overall_score"]
    print(f"[*] Repaired Fused Quality Score: {repaired_score*100:.1f}%")
    
    # Verify overall quality improved after localized repair
    assert repaired_score > initial_score
    print("[OK] Fused quality score successfully increased after localized repairs!")
    
    print("\n======================================")
    print("Quality Intelligence v4.2 benchmarks completed: ALL PASSED.")
    print("======================================")
    return True

if __name__ == "__main__":
    success = run_v4_2_benchmarks()
    sys.exit(0 if success else 1)
