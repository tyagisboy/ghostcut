import os
import json

class FailureLibrary:
    """
    Persistent repository tracking output failures and structural defects.
    Provides diagnostic taxonomy categorization.
    """
    def __init__(self, db_path: str = None):
        if db_path is None:
            app_data = os.environ.get("APPDATA", "C:\\Users\\Neha Tyagi\\AppData\\Local")
            self.db_path = os.path.join(app_data, "GhostCutOffline", "failures_db.json")
        else:
            self.db_path = db_path
            
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.failures = []
        self.load()

    def load(self) -> None:
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    self.failures = json.load(f)
            except Exception as e:
                print(f"[-] Error loading failure library: {e}")
                self.failures = []
        else:
            self.failures = []
            self.save()

    def save(self) -> None:
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(self.failures, f, indent=4)
        except Exception as e:
            print(f"[-] Error saving failure library: {e}")

    def log_failure(self, failure_type: str, category: str, recipe: dict, strategy: str, repair_outcome: str) -> None:
        """
        Taxonomy options: HAIR_HALO, EDGE_LEAKAGE, MISSING_STRANDS, TRANSPARENCY_LOSS, COLOR_SPILL, BROKEN_MASKS, SEMANTIC_ERROR
        """
        entry = {
            "failure_type": failure_type.upper(),
            "category": category.lower(),
            "recipe": recipe,
            "strategy": strategy,
            "repair_outcome": repair_outcome,
            "timestamp": int(np_timestamp())
        }
        self.failures.append(entry)
        self.save()

    def get_failures_by_type(self, failure_type: str) -> list:
        return [f for f in self.failures if f["failure_type"] == failure_type.upper()]

    def get_failures_by_category(self, category: str) -> list:
        return [f for f in self.failures if f["category"] == category.lower()]


def np_timestamp():
    import time
    return time.time()
