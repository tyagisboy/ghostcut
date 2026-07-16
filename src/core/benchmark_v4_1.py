import sys
import numpy as np
from src.core.image_profile import ImageProfile
from src.core.runtime_registry import RuntimeRegistry
from src.core.runtime_scheduler import RuntimeScheduler
from src.core.vision_graph import VisionGraph
from src.core.regional_recipe import RegionalRecipeEngine

class MockRecipe:
    def __init__(self):
        self.bg_thresh = 15
        self.fg_thresh = 240
        self.erode_size = 5
        self.sharpness = 2
        self.preserve_transparency = False
        self.focus_thresh = 10
        self.decontaminate = False

def run_v4_1_benchmarks():
    print("[*] Initializing Vision Intelligence v4.1 Benchmark Suite...")
    
    registry = RuntimeRegistry()
    scheduler = RuntimeScheduler(registry)
    
    # Check that all new runtimes exist in registry
    expected_runtimes = ["face", "eye", "clothing", "animal_anatomy", "plant", "product_geometry"]
    for r_id in expected_runtimes:
        assert registry.get_runtime(r_id) is not None, f"Runtime '{r_id}' was not registered!"
    print("[OK] All 6 new Vision Intelligence runtimes registered successfully.")

    # 1. Test Dynamic Pipeline Selection on Portraits (Human)
    print("\n[*] Evaluating Portrait dynamic execution plan...")
    plan_portrait = scheduler.get_execution_plan("Studio Portrait", ["Human"])
    plan = plan_portrait["plan"]
    skipped = plan_portrait["skipped"]
    
    # Must include human-specific runtimes
    assert "face" in plan
    assert "eye" in plan
    assert "clothing" in plan
    assert "hair" in plan
    # Must skip animal/plant/product runtimes
    assert "fur" not in plan
    assert "animal_anatomy" not in plan
    assert "plant" not in plan
    assert "product_geometry" not in plan
    assert plan_portrait["cpu_savings_percent"] > 0.0
    print(f"[OK] Portrait plan verified: {len(plan)} active modules, skipped: {skipped}")
    print(f"     Calculated CPU Savings: {plan_portrait['cpu_savings_percent']:.1f}%")

    # 2. Test Dynamic Pipeline Selection on Products
    print("\n[*] Evaluating Product dynamic execution plan...")
    plan_product = scheduler.get_execution_plan("Product", ["Product"])
    plan_p = plan_product["plan"]
    assert "product_geometry" in plan_p
    assert "face" not in plan_p
    assert "eye" not in plan_p
    assert "clothing" not in plan_p
    assert "hair" not in plan_p
    assert "fur" not in plan_p
    assert "animal_anatomy" not in plan_p
    assert "plant" not in plan_p
    print(f"[OK] Product plan verified. Skipped: {plan_product['skipped']}")
    print(f"     Calculated CPU Savings: {plan_product['cpu_savings_percent']:.1f}%")

    # 3. Test VisionGraph Construction (Hierarchical tree structural check)
    print("\n[*] Constructing VisionGraph hierarchy...")
    profile = ImageProfile(
        scene="Studio Portrait",
        subject=["Human"],
        materials={"Hair": 0.45, "Skin": 0.3},
        confidence={"initial_segmentation": 0.95, "Human": 0.98}
    )
    
    # Simulate executed context
    h, w = 256, 256
    dummy_mask = np.ones((h, w), dtype=np.uint8) * 255
    dummy_img = np.zeros((h, w, 3), dtype=np.uint8)
    
    context = {
        "face": {
            "has_face": True,
            "face_box": [50, 20, 100, 100],
            "beard": True,
            "ears": True,
            "neck": True,
            "pose": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
            "confidence": 0.95
        },
        "eye": {
            "has_eyes": True,
            "reflections": True,
            "glasses": True,
            "blink_state": "open",
            "confidence": 0.92
        },
        "clothing": {
            "has_clothing": True,
            "clothing_type": "shirt",
            "fabric_type": "mesh",
            "mesh": True,
            "transparency": True,
            "confidence": 0.90
        },
        "hair": {
            "hair_type": "curly",
            "backlit": False
        }
    }
    
    # Force flyaway in attributes
    profile.hair_fur["has_hair"] = True
    profile.hair_fur["hair_flyaway_score"] = 0.6
    profile.confidence["fused_hair"] = 0.94
    
    v_graph_builder = VisionGraph()
    vision_graph_dict = v_graph_builder.build_graph(profile, context)
    
    # Verify hierarchical relationships
    assert vision_graph_dict["label"] == "Scene: Studio Portrait"
    subjects_nodes = vision_graph_dict["children"]
    assert len(subjects_nodes) == 1
    
    human_node = subjects_nodes[0]
    assert human_node["label"] == "Human"
    
    child_labels = [c["label"] for c in human_node["children"]]
    assert "Face" in child_labels
    assert "Clothing (shirt)" in child_labels
    assert "Hair" in child_labels
    
    # Face children
    face_node = [c for c in human_node["children"] if c["label"] == "Face"][0]
    face_child_labels = [c["label"] for c in face_node["children"]]
    assert "Eyes" in face_child_labels
    
    # Eyes children (Glasses)
    eyes_node = [c for c in face_node["children"] if c["label"] == "Eyes"][0]
    eyes_child_labels = [c["label"] for c in eyes_node["children"]]
    assert "Glasses" in eyes_child_labels
    
    print("[OK] VisionGraph hierarchy structure verified successfully!")

    # 4. Test Recipe Engine v3 (Hierarchical parameter overrides inheritance)
    print("\n[*] Verifying Recipe Engine v3 overrides...")
    global_recipe = MockRecipe()
    
    # Mock region graph with nodes corresponding to regions
    mock_region_graph = {
        "nodes": [
            {"id": 1, "label": "Hair"},
            {"id": 2, "label": "Skin"},
            {"id": 3, "label": "Glass"},
            {"id": 4, "label": "Fabric"}
        ]
    }
    
    reg_engine = RegionalRecipeEngine()
    policies = reg_engine.compile_regional_policies(mock_region_graph, global_recipe, vision_graph=vision_graph_dict)
    
    # Assert overrides based on VisionGraph attributes:
    # 1. Hair has flyaways -> erode_size increased from 9 to 12
    assert policies[1]["erode_size"] == 12
    # 2. Face neck region has beard -> beard present on skin -> skin erode_size increased from 2 to 4
    # (Since context simulated face beard as True, Face node has beard attribute, skin policy gets overridden)
    assert policies[2]["erode_size"] == 4
    # 3. Glasses node present -> Glass region gets preserve_transparency = True and fg_thresh = 220
    assert policies[3]["preserve_transparency"] is True
    assert policies[3]["fg_thresh"] == 220
    # 4. Clothing has mesh/transparency -> Fabric region gets preserve_transparency = True
    assert policies[4]["preserve_transparency"] is True
    
    print("[OK] Recipe Engine v3 override rules executed and validated successfully!")
    print("\n======================================")
    print("Vision Intelligence v4.1 benchmarks completed: ALL PASSED.")
    print("======================================")
    return True

if __name__ == "__main__":
    success = run_v4_1_benchmarks()
    sys.exit(0 if success else 1)
