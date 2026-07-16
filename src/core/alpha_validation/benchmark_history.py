import os
import json

class BenchmarkHistory:
    """
    Manages persistent JSON history tracking version run records.
    """
    def __init__(self, history_path: str = None):
        if history_path is None:
            self.history_path = os.path.join(os.path.dirname(__file__), "alpha_benchmark_history.json")
        else:
            self.history_path = history_path
        self.history = self._load_history()

    def _load_history(self) -> dict:
        if os.path.exists(self.history_path):
            try:
                with open(self.history_path, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Seed default initial baseline metrics structure
        defaults = {
            "v1.0.0_baseline": {
                "Straight hair": {"Boundary Accuracy": 0.88, "Hair Preservation": 0.85},
                "Curly hair": {"Boundary Accuracy": 0.82, "Hair Preservation": 0.80},
                "Transparent glass": {"Boundary Accuracy": 0.84, "Transparency Preservation": 0.81}
            }
        }
        self.save_history(defaults)
        return defaults

    def save_history(self, data: dict) -> None:
        try:
            with open(self.history_path, "w") as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass

    def add_run(self, version: str, results: dict) -> None:
        self.history[version] = results
        self.save_history(self.history)
