import os
import json
from src.core.base_learning_runtime import BaseLearningRuntime

class UserFeedbackRuntime(BaseLearningRuntime):
    """
    SDK compliant User Feedback runtime.
    Processes user feedback (star rating, specific defect flags, notes) to adjust
    adaptive policy rules and database ranking scores.
    """
    def __init__(self, db_path="user_feedback_history.json"):
        self.db_path = db_path

    def get_metadata(self) -> dict:
        return {
            "id": "user_feedback",
            "name": "User Feedback & Policy Self-Tuning Runtime",
            "version": "9.2.0",
            "execution_cost": 0.5
        }

    def submit_detailed_feedback(self, feedback_data: dict) -> bool:
        """
        Processes rich feedback from FeedbackDialog and updates user_feedback_history.json.
        """
        history = []
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    history = json.load(f)
            except Exception:
                history = []

        history.append(feedback_data)

        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(history, f, indent=4)
            print(f"[+] User feedback logged successfully ({len(history)} total records).")
            return True
        except Exception as e:
            print(f"[-] Failed to write user feedback log: {e}")
            return False

    def get_learned_overrides(self, dominant_material: str) -> dict:
        """
        Analyzes historical feedback records for a given material and returns policy overrides.
        """
        if not os.path.exists(self.db_path):
            return {}

        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                history = json.load(f)

            overrides = {}
            relevant_defects = []

            for entry in history:
                meta = entry.get("scene_metadata", {})
                mat = meta.get("dominant_material", "")
                if dominant_material.lower() in mat.lower() or mat.lower() in dominant_material.lower():
                    defects = entry.get("defects", [])
                    relevant_defects.extend(defects)

            if "hair_flyaways_missing" in relevant_defects:
                overrides["preserve_flyaways"] = True
                overrides["alpha_clamp_floor"] = 0.04
            if "clothing_edge_halo" in relevant_defects:
                overrides["force_solid_snapping"] = True
                overrides["erode_size"] = 3
            if "studio_light_bleed" in relevant_defects:
                overrides["decontaminate_scale"] = 63

            return overrides
        except Exception as e:
            print(f"[-] Error reading feedback overrides: {e}")
            return {}

    def submit_rating(self, file_path: str, rating_str: str) -> bool:
        return self.submit_detailed_feedback({
            "file_path": file_path,
            "rating": rating_str
        })

    def learn(self, input_data: dict, outcome_data: dict) -> dict:
        success = self.submit_detailed_feedback(outcome_data)
        return {"status": "SUCCESS" if success else "FAILED"}
