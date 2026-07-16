from src.core.perception.perception_state import PerceptionState

class RegionPolicyEngine:
    """
    Compiles detailed regional processing policies and parameters
    based on semantic states and beliefs.
    """
    def __init__(self):
        pass

    def compile_region_policies(self, state: PerceptionState) -> dict:
        """
        Compiles overrides for each active semantic region.
        """
        policies = {}
        for r_name, region in state.regions.items():
            r_type = region.name.lower()
            if r_type == "hair":
                policies[region.name] = {
                    "preserve_strands": True,
                    "alpha_type": "soft",
                    "decontamination": True
                }
            elif r_type == "skin":
                policies[region.name] = {
                    "crisp_edge": True,
                    "transparency": False,
                    "erode_size": 2
                }
            elif r_type == "glass":
                policies[region.name] = {
                    "preserve_gradients": True,
                    "alpha_type": "gradient",
                    "transparency": True
                }
            elif r_type == "fur":
                policies[region.name] = {
                    "preserve_fibers": True,
                    "alpha_type": "soft"
                }
            else:
                policies[region.name] = {
                    "crisp_edge": True,
                    "transparency": False
                }
        return policies
