import os
import sys
import numpy as np

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from src.core.perception.perception_state import PerceptionState
from src.core.perception.perception_rules import RegionPolicyEngine
from src.core.perception.perception_memory import PerceptionMemory
from src.core.perception.adaptive_policy_library import AdaptivePolicyLibrary
from src.core.perception.repair_planner import PerceptionRepairPlanner

class PerceptionOrchestrator:
    """
    APF v6.0 core perception orchestrator.
    Maintains semantic state coordinates, compiles policies, and plans repairs.
    """
    def __init__(self, stats_path: str = None):
        self.state = PerceptionState()
        self.rules_engine = RegionPolicyEngine()
        self.memory = PerceptionMemory(stats_path)
        self.policy_library = AdaptivePolicyLibrary()
        self.repair_planner = PerceptionRepairPlanner()

    def orchestrate_perception(self, img_bgr, scene_name: str, subjects: list, initial_confidence: float) -> dict:
        """
        Coordinates the overall perception loop.
        """
        # 1. Image Fingerprint lookup
        fingerprint = self.memory.get_fingerprint(img_bgr)
        matched = self.memory.match_memory(fingerprint)
        
        # 2. Add detected regions based on subjects
        self.state.regions.clear()
        
        # Set up active regions according to adaptive templates or history
        active_policy_name = scene_name
        if matched:
            active_policy_name = matched["policy_name"]
            
        policy_data = self.policy_library.get_policy(active_policy_name)
        active_regions = policy_data.get("active_regions", ["skin", "hair"])
        
        # Create regions inside state
        for r_name in active_regions:
            # Map edge types
            edge_type = "Hair" if r_name == "hair" else "Fur" if r_name == "fur" else "Transparent" if r_name in ["glass", "transparent"] else "Hard"
            trans = (r_name in ["hair", "fur", "glass", "transparent"])
            
            self.state.add_region(
                name=r_name.capitalize(),
                confidence=initial_confidence,
                edge_type=edge_type,
                transparency=trans,
                refinement_policy="soft_matting" if trans else "crisp_threshold",
                repair_priority=1 if r_name == "hair" else 2 if r_name == "glass" else 3
            )
            
        # 3. Compile regional policies
        region_policies = self.rules_engine.compile_region_policies(self.state)
        
        return {
            "fingerprint": fingerprint,
            "policy_name": active_policy_name,
            "region_policies": region_policies,
            "state": self.state
        }
