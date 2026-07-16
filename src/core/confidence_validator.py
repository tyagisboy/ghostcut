from src.core.belief_graph import BeliefGraph

class ConfidenceValidator:
    """
    Validates logical consistency among compiled beliefs and recipe selections.
    Enforces rules rejecting logically impossible semantic configurations.
    """
    def __init__(self):
        pass

    def validate_beliefs(self, belief_graph: BeliefGraph, recipe) -> dict:
        """
        Validates confidence relationships and overrides inconsistent variables.
        """
        warnings = []
        corrections = []

        # 1. Subject category extraction
        has_human = belief_graph.get_belief("Human") and belief_graph.get_belief("Human").status == "ACCEPTED"
        has_animal = belief_graph.get_belief("Animal") and belief_graph.get_belief("Animal").status == "ACCEPTED"
        has_product = belief_graph.get_belief("Product") and belief_graph.get_belief("Product").status == "ACCEPTED"

        # Rule 1: Human with Fur=98% (without Animal) -> Impossible state
        fur_node = belief_graph.get_belief("Fur")
        if fur_node and fur_node.status == "ACCEPTED" and has_human and not has_animal:
            # Downgrade Fur belief
            fur_node.status = "REJECTED"
            fur_node.confidence = 0.05
            warnings.append("Impossible State: Accepted Fur on Human subject without Animal present")
            corrections.append("Rejected Fur belief and reset confidence to 5%")

        # Rule 2: Hair=0% with high Overall segmentation confidence on portraits
        hair_node = belief_graph.get_belief("Hair")
        if has_human and hair_node and hair_node.confidence == 0.0:
            # Force hair confidence to minimal base level if human is present
            hair_node.confidence = 0.50
            hair_node.status = "ACCEPTED"
            warnings.append("Inconsistent State: Hair is 0% on validated Human subject portrait")
            corrections.append("Calibrated Hair confidence to base 50%")

        # Rule 3: Product using Hair recipes -> Reject Hair overrides
        if has_product and recipe and hasattr(recipe, "erode_size") and hasattr(recipe, "preserve_transparency"):
            if getattr(recipe, "preserve_transparency", False) and not belief_graph.get_belief("Glasses"):
                # Products shouldn't keep hair-style transparency unless transparent glasses/mesh is active
                setattr(recipe, "preserve_transparency", False)
                warnings.append("Impossible Strategy: Product executing Hair transparency preservation rules")
                corrections.append("Disabled preserve_transparency on Product recipe")

        return {
            "valid": len(warnings) == 0,
            "warnings": warnings,
            "corrections": corrections
        }
