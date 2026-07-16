import os
import json

class TelemetrySystem:
    """
    Collects performance, memory usage, and runtime execution metrics automatically.
    """
    def __init__(self, db_path: str = None):
        if db_path is None:
            app_data = os.environ.get("APPDATA", "C:\\Users\\Neha Tyagi\\AppData\\Local")
            self.db_path = os.path.join(app_data, "GhostCutOffline", "telemetry_db.json")
        else:
            self.db_path = db_path
            
        os.makedirs(os.path.dirname(self.db_path), exist_ok=True)
        self.records = {}
        self.load()

    def load(self) -> None:
        if os.path.exists(self.db_path):
            try:
                with open(self.db_path, "r", encoding="utf-8") as f:
                    self.records = json.load(f)
            except Exception as e:
                print(f"[-] Error loading telemetry database: {e}")
                self.records = {}
        else:
            self.records = {}
            self.save()

    def save(self) -> None:
        try:
            with open(self.db_path, "w", encoding="utf-8") as f:
                json.dump(self.records, f, indent=4)
        except Exception as e:
            print(f"[-] Error saving telemetry database: {e}")

    def record_run(self, runtime_id: str, duration_ms: float, peak_ram_mb: float, confidence: float, accepted: bool) -> None:
        r_id = runtime_id.lower()
        if r_id not in self.records:
            self.records[r_id] = []
            
        self.records[r_id].append({
            "duration_ms": float(duration_ms),
            "peak_ram_mb": float(peak_ram_mb),
            "confidence": float(confidence),
            "accepted": bool(accepted)
        })
        # Keep list size bounded for efficiency
        if len(self.records[r_id]) > 500:
            self.records[r_id].pop(0)
        self.save()

    def get_runtime_averages(self) -> dict:
        averages = {}
        for r_id, runs in self.records.items():
            if not runs:
                continue
            durations = [r["duration_ms"] for r in runs]
            rams = [r["peak_ram_mb"] for r in runs]
            confs = [r["confidence"] for r in runs]
            accepts = [1 if r["accepted"] else 0 for r in runs]
            
            averages[r_id] = {
                "avg_duration_ms": sum(durations) / len(runs),
                "avg_peak_ram_mb": sum(rams) / len(runs),
                "avg_confidence": sum(confs) / len(runs),
                "acceptance_rate": sum(accepts) / len(runs),
                "total_runs": len(runs)
            }
        return averages
