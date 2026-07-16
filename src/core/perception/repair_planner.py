import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from src.core.perception.perception_state import PerceptionState

class PerceptionRepairPlanner:
    """
    Formulates a targeted local repair plan to resolve specific regional defects
    (e.g., color spill in Hair, edge noise in Glass) without full re-processing.
    """
    def __init__(self):
        pass

    def formulate_repair_plan(self, state: PerceptionState, self_critic_report: dict) -> list:
        """
        Creates repair steps based on quality critic anomalies and region priorities.
        """
        plan = []
        failures = self_critic_report.get("failures", [])
        
        # Check active regions to direct local repairs
        has_hair = "hair" in state.regions
        has_glass = "glass" in state.regions
        has_fur = "fur" in state.regions

        for failure in failures:
            fail_type = failure.lower()
            if "transparency" in fail_type or "alpha" in fail_type:
                if has_glass:
                    plan.append({
                        "region": "Glass",
                        "operation": "Restore transparency gradients on glass layout",
                        "priority": state.regions["glass"].repair_priority
                    })
            elif "color spill" in fail_type or "halo" in fail_type:
                if has_hair:
                    plan.append({
                        "region": "Hair",
                        "operation": "Erode and decontaminate hair boundary pixels",
                        "priority": state.regions["hair"].repair_priority
                    })
                elif has_fur:
                    plan.append({
                        "region": "Fur",
                        "operation": "Filter color spill from flyaway fur fibers",
                        "priority": state.regions["fur"].repair_priority
                    })
            elif "edge" in fail_type or "jagged" in fail_type:
                if has_hair:
                    plan.append({
                        "region": "Hair",
                        "operation": "Refine hair boundary with vitmatte crop repair",
                        "priority": state.regions["hair"].repair_priority
                    })
                else:
                    # Generic skin/product edge repair
                    plan.append({
                        "region": "Foreground Edge",
                        "operation": "Apply localized edge smoothing filter",
                        "priority": 3
                    })
                    
        # Sort repairs by priority (lowest integer value = highest priority)
        plan.sort(key=lambda x: x["priority"])
        return plan
