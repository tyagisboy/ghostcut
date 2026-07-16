import sys
import os
import numpy as np
import cv2

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.core.runtime_registry import RuntimeRegistry
from src.core.runtime_scheduler import RuntimeScheduler
from src.core.execution_context import ExecutionContext
from src.core.confidence_validator import ConfidenceValidator

def generate_portrait_image() -> np.ndarray:
    # 256x256 BGR image with skin color block to trigger skin ratio > 0.04
    img = np.zeros((256, 256, 3), dtype=np.uint8)
    # Skin tone is typically around YCrCb ranges
    img[64:192, 64:192] = [120, 150, 200]  # Skin-like BGR
    return img

def generate_plant_image() -> np.ndarray:
    # 256x256 BGR image dominated by green to trigger green ratio > 0.15
    img = np.zeros((256, 256, 3), dtype=np.uint8)
    img[32:224, 32:224] = [20, 210, 20]  # Strong green BGR
    return img

def generate_pet_image() -> np.ndarray:
    # Pet: high high-frequency texture (high Laplacian variance)
    img = np.random.randint(0, 255, (256, 256, 3), dtype=np.uint8)
    return img

def run_category_smoke_test(name: str, img: np.ndarray):
    print(f"[*] Running smoke test for category: '{name}'")
    registry = RuntimeRegistry()
    registry.validate_registry()  # Ensure registry validation passes
    
    context = ExecutionContext(img_bgr=img)
    
    # Execute scene intelligence
    scene_runtime = registry.get_runtime("scene")()
    scene_res = scene_runtime.execute(context)
    
    assert scene_res.runtime_id == "scene"
    assert len(scene_res.observations) > 0
    print(f"  [+] Scene classified as: '{scene_res.observations[0]}' with {scene_res.confidence*100:.1f}% confidence")
    
    # Store scene metrics in context cache
    raw_res = scene_runtime.observe(img)[0]
    context.cache["scene_metrics"] = raw_res["metrics"]
    
    # Execute subject intelligence
    subj_runtime = registry.get_runtime("subject")()
    subj_res = subj_runtime.execute(context)
    assert subj_res.runtime_id == "subject"
    
    # Verify Confidence consistency check
    from src.core.belief_graph import BeliefGraph
    from src.core.recipe_engine import AdaptiveRecipeEngine
    from src.core.image_profile import ImageProfile
    
    bg_runtime = registry.get_runtime("background")()
    bg_res = bg_runtime.observe(img, context=context)[0]
    
    profile = ImageProfile(
        scene=scene_res.observations[0],
        subject=subj_runtime.observe(img, context=context)[0]["subjects"],
        background=bg_res,
        confidence={"initial_segmentation": float(scene_res.confidence), "overall": 1.0}
    )
    
    recipe_engine = AdaptiveRecipeEngine()
    recipe = recipe_engine.compile_recipe(profile, {})
    
    validator = ConfidenceValidator()
    val_out = validator.validate_beliefs(context.belief_graph, recipe)
    
    print(f"  [+] Confidence Validator Warnings: {val_out['warnings']}")
    print(f"  [+] Confidence Validator Corrections: {val_out['corrections']}")
    print(f"  [OK] Smoke test for '{name}' completed successfully.")

def main():
    print("======================================")
    print("Running GhostCut v5.0.1 Smoke Tests")
    print("======================================")
    
    # 1. Portrait
    portrait_img = generate_portrait_image()
    run_category_smoke_test("Portrait", portrait_img)
    
    # 2. Plant
    plant_img = generate_plant_image()
    run_category_smoke_test("Plant", plant_img)
    
    # 3. Pet
    pet_img = generate_pet_image()
    run_category_smoke_test("Pet", pet_img)
    
    # 4. Product / Generic
    generic_img = np.ones((256, 256, 3), dtype=np.uint8) * 128
    run_category_smoke_test("Product", generic_img)

    print("\n======================================")
    print("All GhostCut Smoke Tests Passed.")
    print("======================================")

if __name__ == "__main__":
    main()
