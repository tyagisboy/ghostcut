import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))
from src.core.image_profile import ImageProfile
from src.core.recipe_engine import AdaptiveRecipeEngine

def run_synthetic_benchmarks():
    """
    Simulates various image profiles and validates if the AdaptiveRecipeEngine compiles
    the expected recipe characteristics.
    """
    print("[*] Initializing Synthetic Benchmark Profile Runner...")
    
    # Phase 9: Test Semantic Validation rules
    from src.core.semantic_validation_runtime import SemanticValidationRuntime
    validator = SemanticValidationRuntime()
    
    # Case A: Human -> Fur=False
    p_human_fur = ImageProfile(
        scene="Studio Portrait",
        subject=["Human"],
        materials={"Skin": 0.3, "Fur": 0.25},
        hair_fur={"has_fur": True, "fur_type": "short"}
    )
    val_p = validator.validate_profile(p_human_fur)
    assert val_p.hair_fur["has_fur"] is False
    assert val_p.hair_fur["fur_type"] == "none"
    assert val_p.materials["Fur"] == 0.0
    assert "Human -> Fur=False" in val_p.rules_fired
    print("[OK] Semantic Validation rule 'Human -> Fur=False' validated successfully!")
    
    # Case B: Plant -> Skin=False
    p_plant_skin = ImageProfile(
        scene="Product",
        subject=["Plant"],
        materials={"Skin": 0.4}
    )
    val_p = validator.validate_profile(p_plant_skin)
    assert val_p.materials["Skin"] == 0.0
    assert "Plant -> Skin=False" in val_p.rules_fired
    print("[OK] Semantic Validation rule 'Plant -> Skin=False' validated successfully!")
    
    # Case C: Product -> Hair=False
    p_prod_hair = ImageProfile(
        scene="Product",
        subject=["Product"],
        materials={"Hair": 0.3},
        hair_fur={"has_hair": True}
    )
    val_p = validator.validate_profile(p_prod_hair)
    assert val_p.hair_fur["has_hair"] is False
    assert val_p.materials["Hair"] == 0.0
    assert "Product -> Hair=False" in val_p.rules_fired
    print("[OK] Semantic Validation rule 'Product -> Hair=False' validated successfully!")
    
    engine = AdaptiveRecipeEngine()
    
    # Define synthetic profiles to test
    profiles = [
        {
            "name": "Backlit Curly Hair Portrait",
            "profile": ImageProfile(
                scene="Studio Portrait",
                subject=["Human"],
                materials={"Hair": 0.45, "Skin": 0.2},
                lighting={"backlit": True, "ambient_brightness": 180.0}
            ),
            "expected": {
                "apply_matting": True,
                "decontaminate": True,
                "preserve_transparency": False,
                "processing_mode": ["quality", "ultra"]  # support fallback on CPU
            }
        },
        {
            "name": "Standard Product Packshot",
            "profile": ImageProfile(
                scene="Product",
                subject=["Product"],
                materials={"Fabric": 0.8}
            ),
            "expected": {
                "model_name": "birefnet-general-lite",
                "apply_matting": True,
                "decontaminate": False
            }
        },
        {
            "name": "Transparent Wine Glass",
            "profile": ImageProfile(
                scene="Product",
                subject=["Product"],
                materials={"Glass": 0.6}
            ),
            "expected": {
                "preserve_transparency": True,
                "processing_mode": "quality"
            }
        }
    ]
    
    passed = 0
    total = len(profiles)
    
    for idx, prof in enumerate(profiles):
        print(f"\n[Test {idx+1}/{total}] Running profile: '{prof['name']}'...")
        recipe = engine.compile_recipe(prof["profile"])
        
        # Verify conditions
        issues = []
        for key, expected_val in prof["expected"].items():
            actual_val = getattr(recipe, key)
            if isinstance(expected_val, list):
                if actual_val not in expected_val:
                    issues.append(f"Expected parameter '{key}' to be one of {expected_val}, got '{actual_val}'")
            else:
                if actual_val != expected_val:
                    issues.append(f"Expected parameter '{key}' to be '{expected_val}', got '{actual_val}'")
                    
        if not issues:
            print(f"[OK] Profile '{prof['name']}' successfully validated!")
            passed += 1
        else:
            print(f"[FAIL] Profile '{prof['name']}' validation failures:")
            for issue in issues:
                print(f"  - {issue}")
                
    print(f"\n======================================")
    print(f"Synthetic Benchmark Results: {passed}/{total} profiles passed.")
    print(f"======================================")
    
    return passed == total

if __name__ == "__main__":
    success = run_synthetic_benchmarks()
    sys.exit(0 if success else 1)

