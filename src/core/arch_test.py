import sys
import os
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.core.policies import POLICIES
from src.core.scenario import classify_scenario
from src.core.material import MaterialClassifier
from src.core.edge import EdgeClassifier
from src.core.radius import AdaptiveRadiusFieldGenerator
from src.core.confidence import ConfidenceEngine
from src.core.recipe import RecipeEngine

# v2 Modules
from src.core.image_profile import ImageProfile
from src.core.scene import SceneIntelligence
from src.core.subject import SubjectIntelligence
from src.core.background import BackgroundIntelligence
from src.core.recipe_engine import AdaptiveRecipeEngine
from src.core.region_graph import SubjectRegionGraph
from src.core.material_runtime import MaterialRuntime
from src.core.hair_runtime import HairRuntime
from src.core.fur_runtime import FurRuntime
from src.core.edge_runtime import EdgeRuntime
from src.core.regional_recipe import RegionalRecipeEngine

def test_configuration_validation():
    """
    Validates that POLICIES structure contains all essential properties.
    """
    print("[*] Testing configuration validation...")
    
    # 1. Scenarios
    scenarios = [
        "Studio Portrait", "Outdoor Portrait", "Backlit Portrait", "Product",
        "Pet", "Transparent Object", "Clothing", "Jewelry", "Vehicle", "Food", "Plant"
    ]
    for sc in scenarios:
        assert sc in POLICIES["scenarios"], f"Scenario '{sc}' is missing from POLICIES"
        p = POLICIES["scenarios"][sc]
        assert "model_name" in p, f"model_name missing in scenario {sc}"
        assert "processing_mode" in p, f"processing_mode missing in scenario {sc}"
        assert p["processing_mode"] in ["fast", "quality", "ultra"], f"Invalid mode in scenario {sc}"
        assert "radius_base" in p, f"radius_base missing in scenario {sc}"
        
    # 2. Materials
    materials = [
        "Skin", "Hair", "Fur", "Fabric", "Glass", "Plastic",
        "Metal", "Leather", "Feather", "Lace", "Water", "Smoke"
    ]
    for mat in materials:
        assert mat in POLICIES["materials"], f"Material '{mat}' is missing from POLICIES"
        m = POLICIES["materials"][mat]
        assert "alpha_policy" in m, f"alpha_policy missing in material {mat}"
        assert "radius" in m, f"radius missing in material {mat}"
        
    # 3. Edges
    edges = [
        "Hard", "Soft", "Hair", "Fur", "Fabric",
        "Transparent", "Reflection", "Motion Blur", "Shadow", "Whisker"
    ]
    for ed in edges:
        assert ed in POLICIES["edges"], f"Edge '{ed}' is missing from POLICIES"
        e = POLICIES["edges"][ed]
        assert "radius_mult" in e, f"radius_mult missing in edge {ed}"
        assert "sharpness_boost" in e, f"sharpness_boost missing in edge {ed}"
        
    print("[OK] Configuration validation tests passed!")

def test_pipeline_graph_validation():
    """
    Simulates a run to verify dimensions and constraints propagate correctly
    through the intelligence classes.
    """
    print("[*] Testing pipeline graph and shape propagation...")
    
    # Create dummy input data
    h, w = 128, 128
    dummy_img = np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)
    dummy_mask = np.zeros((h, w), dtype=np.uint8)
    dummy_mask[32:96, 32:96] = 255  # Square subject in center
    
    # 1. Recipe check
    recipe_engine = RecipeEngine()
    recipe = recipe_engine.generate_recipe(dummy_img)
    assert recipe.apply_matting is True, "Matting should be enabled by default"
    
    # 2. Materials map check
    mat_classifier = MaterialClassifier()
    prob_maps, confidences = mat_classifier.compute_material_maps(dummy_img, dummy_mask)
    assert prob_maps.shape == (h, w, 12), f"Expected material maps shape {(h, w, 12)}, got {prob_maps.shape}"
    for mat in mat_classifier.materials:
        assert mat in confidences, f"Confidence score missing for {mat}"
        assert 0.0 <= confidences[mat] <= 1.0, f"Confidence for {mat} out of bounds: {confidences[mat]}"
        
    # 3. Edge check
    edge_classifier = EdgeClassifier()
    edge_map = edge_classifier.classify_edges(dummy_img, dummy_mask, prob_maps)
    assert edge_map.shape == (h, w), f"Expected edge map shape {(h, w)}, got {edge_map.shape}"
    assert np.all(edge_map >= -1) and np.all(edge_map <= 9), "Edge map values out of bounds [-1, 9]"
    
    # 4. Adaptive Radius check
    radius_gen = AdaptiveRadiusFieldGenerator()
    radius_map = radius_gen.generate_radius_field(dummy_mask, edge_map, prob_maps)
    assert radius_map.shape == (h, w), f"Expected radius map shape {(h, w)}, got {radius_map.shape}"
    assert np.all(radius_map >= 1.0) and np.all(radius_map <= 25.0), "Radius map values out of bounds [1.0, 25.0]"
    
    # 5. Confidence maps check
    conf_engine = ConfidenceEngine()
    confs = conf_engine.generate_all_confidences(dummy_img, dummy_mask, prob_maps, edge_map)
    keys = [
        "segmentation_confidence", "hair_confidence", "fur_confidence", "material_confidence",
        "edge_confidence", "transparency_confidence", "alpha_confidence", "reconstruction_confidence"
    ]
    for k in keys:
        assert k in confs, f"Confidence map {k} is missing"
        assert confs[k].shape == (h, w), f"Expected {k} shape {(h, w)}, got {confs[k].shape}"
        assert np.all(confs[k] >= 0.0) and np.all(confs[k] <= 1.0), f"Values in {k} out of bounds [0.0, 1.0]"
        
    print("[OK] Pipeline graph and shape propagation tests passed!")

def test_v2_intelligence_engine():
    """
    Validates that the new v2 runtime sdk modules comply with shape and output constraints.
    """
    print("[*] Testing v2 Image Intelligence SDK components...")
    h, w = 128, 128
    dummy_img = np.random.randint(0, 255, (h, w, 3), dtype=np.uint8)
    dummy_mask = np.zeros((h, w), dtype=np.uint8)
    dummy_mask[32:96, 32:96] = 255
    
    # Scene/Subject/Background
    scene_intel = SceneIntelligence()
    scene_res = scene_intel.analyze(dummy_img)
    assert "scene" in scene_res
    assert "confidence" in scene_res
    
    subject_intel = SubjectIntelligence()
    subj_res = subject_intel.analyze(dummy_img, scene_res["metrics"])
    assert "subjects" in subj_res
    
    bg_intel = BackgroundIntelligence()
    bg_res = bg_intel.analyze(dummy_img, scene_res["metrics"])
    assert "complexity" in bg_res
    assert "dominant_colors" in bg_res
    
    # ImageProfile compile
    profile = ImageProfile(
        scene=scene_res["scene"],
        subject=subj_res["subjects"],
        background=bg_res
    )
    assert profile.scene == scene_res["scene"]
    
    recipe_engine = AdaptiveRecipeEngine()
    recipe = recipe_engine.compile_recipe(profile)
    assert recipe.model_name in ["birefnet-general", "birefnet-general-lite"]
    
    # Runtimes and Region Graph
    mat_runtime = MaterialRuntime()
    mat_res = mat_runtime.analyze(dummy_img, dummy_mask, subjects=profile.subject)
    assert mat_res["maps"].shape == (h, w, 12)
    
    hair_runtime = HairRuntime()
    hair_res = hair_runtime.analyze(dummy_img, dummy_mask)
    assert "hair_type" in hair_res
    
    fur_runtime = FurRuntime()
    fur_res = fur_runtime.analyze(dummy_img, dummy_mask)
    assert "fur_type" in fur_res
    
    edge_runtime = EdgeRuntime()
    edge_res = edge_runtime.analyze(dummy_img, dummy_mask, mat_res["maps"])
    assert edge_res["edge_map"].shape == (h, w)
    
    conf_engine = ConfidenceEngine()
    confs = conf_engine.generate_all_confidences(dummy_img, dummy_mask, mat_res["maps"], edge_res["edge_map"])

    graph_builder = SubjectRegionGraph()
    graph = graph_builder.build_graph(dummy_mask, mat_res["maps"], edge_res["edge_map"], confs)
    assert "nodes" in graph
    assert len(graph["nodes"]) > 0
    assert "labeled_regions" in graph
    
    # Assert v3 node attributes
    node = graph["nodes"][0]
    assert "semantic_class" in node
    assert "material" in node
    assert "edge_type" in node
    assert "transparency" in node
    assert "confidence" in node
    assert "refinement_profile" in node
    
    reg_recipe = RegionalRecipeEngine()
    policies = reg_recipe.compile_regional_policies(graph, recipe)
    assert len(policies) > 0
    
    # Check that region-aware setting exists
    for r_id, pol in policies.items():
        assert "decontaminate" in pol
    
    print("[OK] v3 Image Intelligence SDK components validated successfully!")


def test_v4_registry_and_scheduler():
    """
    Validates that runtimes are conformed to BaseRuntime and topologically sort correctly.
    """
    print("[*] Testing v4.0 Runtime Registry and Scheduler...")
    from src.core.runtime_registry import RuntimeRegistry
    from src.core.runtime_scheduler import RuntimeScheduler
    
    registry = RuntimeRegistry()
    scheduler = RuntimeScheduler(registry)
    
    # 1. Test registration
    runtimes = registry.list_runtimes()
    assert "scene" in runtimes
    assert "subject" in runtimes
    assert "material" in runtimes
    assert "hair" in runtimes
    assert "fur" in runtimes
    assert "confidence_fusion" in runtimes
    
    # 2. Test topological sort
    plan_ids = ["confidence_fusion", "scene", "subject", "material", "hair"]
    ordered = scheduler.resolve_dependencies(plan_ids)
    assert ordered.index("scene") < ordered.index("subject")
    assert ordered.index("subject") < ordered.index("material")
    assert ordered.index("material") < ordered.index("hair")
    assert ordered.index("hair") < ordered.index("confidence_fusion")
    
    # 3. Test dynamic execution plan selections
    # Case A: Portrait -> should execute hair, skip fur
    plan_portrait = scheduler.get_execution_plan("Studio Portrait", ["Human"])
    assert "hair" in plan_portrait["plan"]
    assert "fur" not in plan_portrait["plan"]
    assert "fur" in plan_portrait["skipped"]
    assert plan_portrait["cpu_savings_percent"] > 0.0
    
    # Case B: Product -> should skip hair and fur, resulting in high CPU savings
    plan_product = scheduler.get_execution_plan("Product", ["Product"])
    assert "hair" not in plan_product["plan"]
    assert "fur" not in plan_product["plan"]
    assert "hair" in plan_product["skipped"]
    assert "fur" in plan_product["skipped"]
    assert plan_product["cpu_savings_percent"] >= 30.0 # significant CPU savings
    
    # Case C: Pet -> should execute fur, skip hair
    plan_pet = scheduler.get_execution_plan("Pet", ["Animal"])
    assert "fur" in plan_pet["plan"]
    assert "hair" not in plan_pet["plan"]
    assert "hair" in plan_pet["skipped"]
    
    print("[OK] v4.0 Runtime Registry and Scheduler validated successfully!")


def run_all_tests():
    try:
        test_configuration_validation()
        print("")
        test_pipeline_graph_validation()
        print("")
        test_v2_intelligence_engine()
        print("")
        test_v4_registry_and_scheduler()
        print("\n======================================")
        print("Architecture Test Suite completed: ALL TESTS PASSED.")
        print("======================================")
        return True
    except AssertionError as e:
        print(f"\n[FAIL] Architecture validation failed: {e}")
        return False

if __name__ == "__main__":
    success = run_all_tests()
    sys.exit(0 if success else 1)

