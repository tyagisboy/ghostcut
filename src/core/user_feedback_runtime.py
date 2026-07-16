import os
import json
from src.core.base_learning_runtime import BaseLearningRuntime

class UserFeedbackRuntime(BaseLearningRuntime):
    """
    SDK compliant User Feedback runtime.
    Processes user feedback (Excellent, Good, Acceptable, Poor) to adjust database ranking scores.
    """
    def __init__(self, db_path="learning_db.json"):
        self.db_path = db_path

    def get_metadata(self) -> dict:
        return {
            "id": "user_feedback",
            "name": "User Feedback Runtime",
            "version": "1.0",
            "execution_cost": 0.5
        }

    def submit_rating(self, file_path: str, rating_str: str) -> bool:
        """
        Maps feedback strings and writes back to learning_db.json records.
        """
        rating_map = {
            "Excellent": 1,
            "Good": 2,
            "Acceptable": 3,
            "Poor": 0
        }
        num_rating = rating_map.get(rating_str, 1)

        if not os.path.exists(self.db_path):
            return False

        try:
            with open(self.db_path, "r", encoding="utf-8") as f:
                data = json.load(f)

            # Find matching file path and update rating
            updated = False
            for record in data:
                # Normalizing paths for comparison
                p1 = os.path.abspath(record.get("file_path", ""))
                p2 = os.path.abspath(file_path)
                if p1 == p2:
                    record["rating"] = num_rating
                    updated = True
                    break

            if updated:
                with open(self.db_path, "w", encoding="utf-8") as f:
                    json.dump(data, f, indent=4)
                return True
        except Exception as e:
            print(f"[-] Failed to submit feedback: {e}")
        return False

    def learn(self, input_data: dict, outcome_data: dict) -> dict:
        success = self.submit_rating(
            file_path=input_data.get("file_path", ""),
            rating_str=outcome_data.get("rating_str", "Excellent")
        )
        return {"status": "SUCCESS" if success else "FAILED"}
