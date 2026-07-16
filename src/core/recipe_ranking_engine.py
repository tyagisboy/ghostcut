import numpy as np
from src.core.base_learning_runtime import BaseLearningRuntime


class RecipeRankingEngine(BaseLearningRuntime):
    """
    Ranks multiple alternative recipe configurations using historical success,
    quality metrics, and execution costs to select the optimal runtime recipe.
    """
    def __init__(self):
        pass

    def get_metadata(self) -> dict:
        return {
            "id": "recipe_ranking",
            "name": "Recipe Ranking Engine",
            "version": "1.0",
            "execution_cost": 1.0
        }

    def rank_recipes(self, base_recipe, similar_rec: dict = None) -> dict:
        """
        Inputs:
            base_recipe: The dynamically compiled recipe from AdaptiveRecipeEngine
            similar_rec: Similar historical recipe parameters retrieved from DB (if any)
        Returns:
            best_recipe: Selected optimal recipe
            alternatives: List of ranked recipes
            confidence: Confidence score of ranking decision
        """
        candidates = []
        
        # 1. Base default recipe compiled dynamically
        candidates.append({
            "name": "Dynamic Default",
            "recipe": base_recipe,
            "score": 0.82,  # default baseline
            "cost": 3.0
        })

        # 2. Historical candidate from Database
        if similar_rec and "params" in similar_rec:
            # Reconstruct recipe from parameter values
            from src.core.recipe import ProcessingRecipe
            hist_params = similar_rec["params"]
            hist_recipe = ProcessingRecipe(settings_dict=hist_params)

            
            # Distance penalty: closer match gets higher score boost
            dist = similar_rec.get("distance", 1.0)
            hist_score = 0.95 - (dist * 0.15)
            
            candidates.append({
                "name": f"Historical Match ({similar_rec.get('file_path', 'db')})",
                "recipe": hist_recipe,
                "score": float(np.clip(hist_score, 0.4, 0.99)),
                "cost": 3.0
            })

        # Sort candidates by score descending
        ranked = sorted(candidates, key=lambda x: x["score"], reverse=True)
        
        best = ranked[0]["recipe"]
        alternatives = [{"name": c["name"], "score": c["score"]} for c in ranked]
        ranking_conf = float(ranked[0]["score"])

        return {
            "best_recipe": best,
            "alternatives": alternatives,
            "confidence": ranking_conf
        }

    def learn(self, input_data: dict, outcome_data: dict) -> dict:
        return {"status": "SUCCESS"}
