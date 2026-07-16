import os
import json

class CalibrationDatabase:
    """
    Manages reliability statistics for runtimes across semantic categories.
    Used to dynamically adjust confidence calculations during fusion and consensus.
    """
    def __init__(self, db_path: str = None):
        if db_path is None:
            # Set default path in AppData to avoid permission locks
            app_data = os.environ.get("APPDATA", "C:\\Users\\Neha Tyagi\\AppData\\Local")
            self.db_path = os.path.join(app_data, "GhostCutOffline", "calibration_db.json")
        else:
            self.db_path = db_path
            
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.stats = {}
        self.load()

    def load(self) -> None:
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    self.stats = json.load(f)
            except Exception as e:
                print(f"[-] Error loading calibration database: {e}")
                self.stats = {}
        else:
            # Initialize defaults
            self.stats = {
                "hair": {
                    "portrait": {"success": 96, "total": 100},
                    "pet": {"success": 87, "total": 100},
                    "plant": {"success": 12, "total": 100}
                },
                "fur": {
                    "pet": {"success": 94, "total": 100},
                    "portrait": {"success": 15, "total": 100}
                },
                "face": {
                    "portrait": {"success": 99, "total": 100},
                    "product": {"success": 5, "total": 100}
                },
                "plant": {
                    "plant": {"success": 95, "total": 100},
                    "portrait": {"success": 20, "total": 100}
                }
            }
            self.save()

    def save(self) -> None:
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(self.stats, f, indent=4)
        except Exception as e:
            print(f"[-] Error saving calibration database: {e}")

    def get_reliability(self, runtime_id: str, category: str) -> float:
        """
        Returns the historical success rate [0.0, 1.0] for a runtime in a category.
        """
        r_id = runtime_id.lower()
        cat = category.lower()
        if r_id in self.stats and cat in self.stats[r_id]:
            entry = self.stats[r_id][cat]
            if entry.get("total", 0) > 0:
                return float(entry["success"] / entry["total"])
        return 0.50 # Default fallback reliability

    def record_success(self, runtime_id: str, category: str, is_success: bool) -> None:
        """
        Appends success/failure trial metrics.
        """
        r_id = runtime_id.lower()
        cat = category.lower()
        if r_id not in self.stats:
            self.stats[r_id] = {}
        if cat not in self.stats[r_id]:
            self.stats[r_id][cat] = {"success": 0, "total": 0}
            
        self.stats[r_id][cat]["total"] += 1
        if is_success:
            self.stats[r_id][cat]["success"] += 1
        self.save()

    def calibrate_confidence(self, raw_conf: float, runtime_id: str, category: str) -> float:
        """
        Calibrates raw confidence by scaling it using the runtime reliability coefficient.
        """
        rel = self.get_reliability(runtime_id, category)
        # Fuse raw confidence with historical reliability
        import numpy as np
        calibrated = float(np.clip(raw_conf * (0.3 + 0.7 * rel), 0.0, 1.0))
        return calibrated
