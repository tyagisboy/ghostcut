import sys
import os
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from src.core.perception.perception_orchestrator import PerceptionOrchestrator
from src.core.perception.perception_state import PerceptionState, PerceptionRegion
from src.core.perception.repair_planner import PerceptionRepairPlanner
from src.core.perception.adaptive_policy_library import AdaptivePolicyLibrary

def test_perception_orchestrator():
    print("[*] Testing APF perception orchestrator run...")
    dummy_img = np.zeros((256, 256, 3), dtype=np.uint8)
    orchestrator = PerceptionOrchestrator()
    
    orch_res = orchestrator.orchestrate_perception(
        img_bgr=dummy_img,
        scene_name="Studio Portrait",
        subjects=["Human"],
        initial_confidence=0.92
    )
    
    assert "fingerprint" in orch_res
    assert "state" in orch_res
    assert "region_policies" in orch_res
    
    state = orch_res["state"]
    # Should have Hair and Skin regions mapped in Portrait strategy
    assert "hair" in state.regions
    assert "skin" in state.regions
    
    print("  [+] Regions detected:", list(state.regions.keys()))
    print("  [+] Region Policies compiled:", orch_res["region_policies"])

def test_repair_planner_operations():
    print("[*] Testing Targeted Repair Planner logic...")
    planner = PerceptionRepairPlanner()
    
    # Setup state
    state = PerceptionState()
    state.add_region("Hair", confidence=0.88, repair_priority=1)
    state.add_region("Glass", confidence=0.85, repair_priority=2)
    
    critic_report = {
        "failures": [
            "Color spill bleed detected in hair",
            "Lost transparency edge detail in glass"
        ]
    }
    
    repair_plan = planner.formulate_repair_plan(state, critic_report)
    assert len(repair_plan) > 0
    print("  [+] Formulated repair plan:")
    for step in repair_plan:
        print(f"    - Region: {step['region']} | Operation: {step['operation']} | Priority: {step['priority']}")
        
    # Assert priorities order (lowest priority value first)
    assert repair_plan[0]["region"] == "Hair"
    assert repair_plan[1]["region"] == "Glass"

def main():
    print("======================================")
    print("Running GhostCut APF v6.0 Unit Tests")
    print("======================================")
    
    test_perception_orchestrator()
    test_repair_planner_operations()
    
    print("\n======================================")
    print("All APF v6.0 Unit Tests Passed.")
    print("======================================")

if __name__ == "__main__":
    main()
