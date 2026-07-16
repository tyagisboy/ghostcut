import os
import json
import numpy as np
from src.core.base_learning_runtime import BaseLearningRuntime

class FailureMemoryRuntime(BaseLearningRuntime):
    """
    SDK compliant Failure Memory runtime.
    Logs low-quality processing instances and identifies defect-prone signatures.
    """
    def __init__(self, db_path="failure_db.json"):
        self.db_path = db_path
        self.failures = self._load_db()

    def get_metadata(self) -> dict:
        return {
            "id": "failure_memory",
            "name": "Failure Memory Runtime",
            "version": "1.0",
            "execution_cost": 1.0
        }

    def _load_db(self) -> list:
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[-] Failed loading failure DB: {e}")
        return []

    def _save_db(self) -> None:
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(self.failures, f, indent=4)
        except Exception as e:
            print(f"[-] Failed saving failure DB: {e}")

    def log_failure(self, features: dict, defects: dict, strategy: str) -> None:
        record = {
            "features": features,
            "defects": defects,
            "strategy": strategy
        }
        self.failures.append(record)
        self._save_db()

    def predict_failure_risk(self, current_features: dict) -> dict:
        """
        Determines if similar images in the past suffered from specific defect categories.
        Returns:
            risk_factors: list of predicted failure modes (e.g. "halo", "transparency")
            suggested_action: override parameters to avoid this failure.
        """
        if not self.failures or not current_features:
            return {"risk_factors": [], "suggested_action": {}}

        keys = ["aspect_ratio", "laplacian_var", "bg_var", "bg_mean"]
        risk_factors = set()
        suggested_action = {}

        for fail in self.failures:
            fail_feat = fail.get("features", {})
            dist = 0.0
            valid = 0
            for k in keys:
                if k in current_features and k in fail_feat:
                    dist += ((float(current_features[k]) - float(fail_feat[k])) / 1000.0) ** 2
                    valid += 1
            
            if valid > 0 and np.sqrt(dist) < 0.5:
                # Add documented failures to risk factors
                for defect, score in fail.get("defects", {}).items():
                    if score > 0.15:  # significant defect presence
                        risk_factors.add(defect)
                        
                # Copy overrides
                if fail.get("strategy"):
                    suggested_action["repair_strategy"] = fail["strategy"]

        return {
            "risk_factors": list(risk_factors),
            "suggested_action": suggested_action
        }

    def learn(self, input_data: dict, outcome_data: dict) -> dict:
        self.log_failure(
            features=input_data.get("features", {}),
            defects=input_data.get("defects", {}),
            strategy=outcome_data.get("strategy", "local_refine")
        )
        return {"status": "SUCCESS"}
