from src.core.belief_graph import BeliefGraph

class ExecutionStrategy:
    """
    Detailed strategy detailing active runtimes, order,
    refinement policies, and localized repair parameters.
    """
    def __init__(self, active_runtimes: list, params: dict, budget: int = 5, rationale: str = ""):
        self.active_runtimes = active_runtimes
        self.params = params
        self.repair_budget = budget
        self.rationale = rationale

class StrategyEngine:
    """
    Compiles validated system beliefs into concrete pipeline ExecutionStrategies.
    """
    def __init__(self):
        pass

    def compile_strategy(self, belief_graph: BeliefGraph) -> ExecutionStrategy:
        """
        Translates belief hierarchies into concrete processing pipelines.
        """
        active = ["scene", "subject", "background", "confidence_fusion"]
        params = {
            "model_name": "birefnet-general-lite",
            "processing_mode": "fast",
            "erode_size": 3,
            "sharpness": 0,
            "preserve_transparency": False,
            "decontaminate": True
        }
        
        reasons = []

        # Check beliefs status
        has_human = False
        has_product = False
        has_plant = False
        
        for b_id, node in belief_graph.nodes.items():
            if node.status != "ACCEPTED":
                continue
                
            if node.entity == "Human":
                has_human = True
                active.extend(["face", "eye", "clothing", "hair"])
                reasons.append("Human subject detected -> Enable human sensory runtimes")
            elif node.entity == "Animal":
                active.extend(["animal_anatomy", "fur"])
                params["model_name"] = "birefnet-general"
                reasons.append("Animal subject detected -> Enable animal/fur runtimes")
            elif node.entity == "Plant":
                has_plant = True
                active.append("plant")
                params["erode_size"] = 2
                reasons.append("Plant subject detected -> Enable thin structure refinement")
            elif node.entity == "Product":
                has_product = True
                active.append("product_geometry")
                reasons.append("Product subject detected -> Enable straight edge tracking")

        # Set specific parameters based on fused beliefs
        if has_product:
            params["model_name"] = "birefnet-general"
            params["erode_size"] = 1 # preserve geometric borders
            params["decontaminate"] = False
            
        if belief_graph.get_belief("Glasses") and belief_graph.get_belief("Glasses").status == "ACCEPTED":
            params["preserve_transparency"] = True
            reasons.append("Glasses detected -> Enable transparency preservation")

        strategy = ExecutionStrategy(
            active_runtimes=active,
            params=params,
            budget=8 if has_human else 5,
            rationale="; ".join(reasons) if reasons else "Default general execution plan"
        )
        return strategy
