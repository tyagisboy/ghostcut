import sys
import os
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..")))

from src.core.runtime_registry import RuntimeRegistry
from src.core.runtime_scheduler import RuntimeScheduler
from src.core.execution_context import ExecutionContext
from src.core.confidence_validator import ConfidenceValidator
from src.core.belief_graph import BeliefGraph, BeliefNode
from src.core.recipe import ProcessingRecipe

def test_registry_validation_errors():
    print("[*] Testing registry validation for errors...")
    registry = RuntimeRegistry()
    
    # 1. Duplicate registration check
    try:
        registry.register("scene", registry.list_runtimes()["scene"])
        assert False, "Failed to raise duplicate registration error!"
    except ValueError as e:
        print(f"  [+] Correctly caught duplicate error: '{e}'")
        
    # 2. Dependency cycle check
    # Create a temporary custom registry with cycle
    cycle_reg = RuntimeRegistry()
    cycle_reg._runtimes.clear() # clear registry
    
    class RuntimeA:
        def get_metadata(self):
            return {"id": "runtime_a", "dependencies": ["runtime_b"]}
    class RuntimeB:
        def get_metadata(self):
            return {"id": "runtime_b", "dependencies": ["runtime_a"]}
            
    cycle_reg._runtimes["runtime_a"] = RuntimeA
    cycle_reg._runtimes["runtime_b"] = RuntimeB
    
    try:
        cycle_reg.validate_registry()
        assert False, "Failed to detect dependency cycle in registry!"
    except ValueError as e:
        print(f"  [+] Correctly caught dependency cycle: '{e}'")

def test_scheduler_execution_trace():
    print("[*] Testing scheduler trace logs and topological sorting...")
    registry = RuntimeRegistry()
    scheduler = RuntimeScheduler(registry)
    
    plan_out = scheduler.get_execution_plan("Studio Portrait", ["Human"])
    assert "plan" in plan_out
    assert "execution_trace" in plan_out
    assert len(plan_out["execution_trace"]) > 0
    
    print("  [+] Compiled plan:", plan_out["plan"])
    print("  [+] Generated scheduler traces:")
    for trace in plan_out["execution_trace"]:
        print(f"    - {trace}")
        
    # Check that skipped reasons is populated
    assert len(plan_out["skipped_reasons"]) > 0
    print("  [+] Skipped reasons mapped successfully:", plan_out["skipped_reasons"])

def test_confidence_consistency_assertions():
    print("[*] Testing confidence consistency assertions...")
    validator = ConfidenceValidator()
    
    # Inconsistent state: Human portrait with accepted Fur (and no Animal)
    bg = BeliefGraph()
    bg.add_belief("Human")
    bg.get_belief("Human").confidence = 0.95
    bg.get_belief("Human").status = "ACCEPTED"
    bg.add_belief("Fur")
    bg.get_belief("Fur").confidence = 0.98
    bg.get_belief("Fur").status = "ACCEPTED"
    
    # Inconsistent recipe check: Product using Hair transparency preservation
    bg_prod = BeliefGraph()
    bg_prod.add_belief("Product")
    bg_prod.get_belief("Product").confidence = 0.95
    bg_prod.get_belief("Product").status = "ACCEPTED"
    
    class DummyRecipe:
        def __init__(self):
            self.erode_size = 3
            self.preserve_transparency = True
            
    recipe = DummyRecipe()
    
    # Validate Human + Fur
    res_fur = validator.validate_beliefs(bg, recipe)
    assert bg.get_belief("Fur").status == "REJECTED"
    assert bg.get_belief("Fur").confidence == 0.05
    print("  [+] Correctly rejected Fur on Human subject:", res_fur["corrections"])
    
    # Validate Product recipe
    res_recipe = validator.validate_beliefs(bg_prod, recipe)
    assert recipe.preserve_transparency is False
    print("  [+] Correctly disabled hair transparency on Product recipe:", res_recipe["corrections"])

def main():
    print("======================================")
    print("Running GhostCut v5.0.1 Integration Tests")
    print("======================================")
    
    test_registry_validation_errors()
    test_scheduler_execution_trace()
    test_confidence_consistency_assertions()
    
    print("\n======================================")
    print("All Integration Tests Passed successfully.")
    print("======================================")

if __name__ == "__main__":
    main()
