import os
import json

class PerceptionMemory:
    """
    Saves and indexes successful perception decisions and region policy mappings
    using image signatures to allow automatic selection improvements.
    """
    def __init__(self, db_path: str = None):
        if db_path is None:
            self.db_path = os.path.join(os.path.dirname(__file__), "perception_memory.json")
        else:
            self.db_path = db_path
        self.records = self._load_records()

    def _load_records(self) -> dict:
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        return {}

    def _save_records(self) -> None:
        try:
            with open(self.db_path, "w") as f:
                json.dump(self.records, f, indent=4)
        except Exception:
            pass

    def get_fingerprint(self, img_bgr) -> str:
        # Simple color histogram descriptor as signature fingerprint
        h, w = img_bgr.shape[:2]
        mean_val = img_bgr.mean(axis=(0,1))
        std_val = img_bgr.std(axis=(0,1))
        return f"w{w}_h{h}_m{mean_val[0]:.1f}_{mean_val[1]:.1f}_{mean_val[2]:.1f}_s{std_val[0]:.1f}"

    def match_memory(self, img_fingerprint: str) -> dict:
        """
        Finds the closest policy in history.
        """
        return self.records.get(img_fingerprint)

    def save_memory(self, img_fingerprint: str, policy_name: str, region_policies: dict, score: float) -> None:
        self.records[img_fingerprint] = {
            "policy_name": policy_name,
            "region_policies": region_policies,
            "score": float(score)
        }
        self._save_records()
