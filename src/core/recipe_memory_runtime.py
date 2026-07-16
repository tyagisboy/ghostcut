import os
import json
import numpy as np
from src.core.base_learning_runtime import BaseLearningRuntime

class RecipeMemoryRuntime(BaseLearningRuntime):
    """
    SDK compliant Recipe Memory runtime.
    Manages loading, saving, and similarity querying from the local recipe database.
    """
    def __init__(self, db_path="learning_db.json"):
        self.db_path = db_path
        self.records = self._load_db()

    def get_metadata(self) -> dict:
        return {
            "id": "recipe_memory",
            "name": "Recipe Memory Runtime",
            "version": "1.0",
            "execution_cost": 1.0
        }

    def _load_db(self) -> list:
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[-] Failed loading learning DB: {e}")
        return []

    def _save_db(self) -> None:
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(self.records, f, indent=4)
        except Exception as e:
            print(f"[-] Failed saving learning DB: {e}")

    def save_record(self, file_path: str, features: dict, params: dict, rating: int = 1) -> None:
        """
        Adds a new execution record to the local memory database.
        """
        record = {
            "file_path": file_path,
            "features": features,
            "params": params,
            "rating": rating
        }
        self.records.append(record)
        self._save_db()

    def find_similar_recipe(self, current_features: dict) -> dict:
        """
        Queries database for the closest matched past run using Euclidean distance.
        Only considers highly rated runs (rating == 1 or rating >= 3).
        """
        if not self.records or not current_features:
            return None

        keys = ["aspect_ratio", "mean_b", "mean_g", "mean_r", "laplacian_var", "bg_var", "bg_mean"]
        
        best_match = None
        min_dist = float("inf")

        for rec in self.records:
            if rec.get("rating", 0) < 1:
                continue

            rec_feat = rec.get("features", {})
            
            # Compute normalized Euclidean distance
            dist = 0.0
            valid_keys = 0
            for k in keys:
                if k in current_features and k in rec_feat:
                    val_curr = float(current_features[k])
                    val_rec = float(rec_feat[k])
                    
                    # Normalize based on typical scale of colors/aspect-ratios
                    denom = 255.0 if "mean" in k or "std" in k else 1.5 if "ratio" in k else 1000.0
                    dist += ((val_curr - val_rec) / denom) ** 2
                    valid_keys += 1
            
            if valid_keys > 0:
                dist = np.sqrt(dist)
                if dist < min_dist:
                    min_dist = dist
                    best_match = rec

        # Return recipe parameters if the match is sufficiently close (distance threshold < 1.0)
        if best_match and min_dist < 1.2:
            return {
                "params": best_match["params"],
                "distance": min_dist,
                "file_path": best_match["file_path"]
            }
        return None

    def learn(self, input_data: dict, outcome_data: dict) -> dict:
        self.save_record(
            file_path=input_data.get("file_path", "unknown"),
            features=input_data.get("features", {}),
            params=outcome_data.get("params", {}),
            rating=outcome_data.get("rating", 1)
        )
        return {"status": "SUCCESS"}
