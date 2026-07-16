import os
import json

class RegressionDashboard:
    """
    Compares current version performance telemetry against baseline builds.
    Flags performance, memory, and quality regressions automatically.
    """
    def __init__(self, baseline_path: str = None):
        if baseline_path is None:
            app_data = os.environ.get("APPDATA", "C:\\Users\\Neha Tyagi\\AppData\\Local")
            self.baseline_path = os.path.join(app_data, "GhostCutOffline", "regression_baseline.json")
        else:
            self.baseline_path = baseline_path
            
        os.makedirs(os.path.dirname(self.baseline_path), exist_ok=True)
        self.baseline = {}
        self.load_baseline()

    def load_baseline(self) -> None:
        if os.path.exists(self.baseline_path):
            try:
                with open(self.baseline_path, "r", encoding="utf-8") as f:
                    self.baseline = json.load(f)
            except Exception as e:
                print(f"[-] Error loading regression baseline: {e}")
                self.baseline = self.get_default_baseline()
        else:
            self.baseline = self.get_default_baseline()
            self.save_baseline()

    def save_baseline(self) -> None:
        try:
            with open(self.baseline_path, "w", encoding="utf-8") as f:
                json.dump(self.baseline, f, indent=4)
        except Exception as e:
            print(f"[-] Error saving regression baseline: {e}")

    def get_default_baseline(self) -> dict:
        return {
            "avg_quality_score": 0.90,
            "avg_iou": 0.88,
            "avg_duration_ms": 145.0,
            "avg_peak_ram_mb": 34.0
        }

    def compare_build(self, current_stats: dict) -> dict:
        """
        current_stats: {
            "avg_quality_score": float,
            "avg_iou": float,
            "avg_duration_ms": float,
            "avg_peak_ram_mb": float
        }
        """
        warnings = []
        regression_detected = False

        # Quality Delta check (threshold: > 2.0% quality drop)
        quality_drop = self.baseline["avg_quality_score"] - current_stats["avg_quality_score"]
        if quality_drop > 0.02:
            regression_detected = True
            warnings.append(f"Quality Regression: Overall quality dropped by {quality_drop*100:.2f}% (Baseline: {self.baseline['avg_quality_score']*100:.1f}%)")

        # CPU latency delta check (threshold: > 15.0% slower)
        speed_ratio = current_stats["avg_duration_ms"] / (self.baseline["avg_duration_ms"] + 1e-6)
        if speed_ratio > 1.15:
            regression_detected = True
            warnings.append(f"CPU speed Regression: latency increased by {(speed_ratio - 1.0)*100:.1f}% ({current_stats['avg_duration_ms']:.1f}ms vs. baseline {self.baseline['avg_duration_ms']:.1f}ms)")

        # RAM growth delta check (threshold: > 10.0% growth)
        ram_ratio = current_stats["avg_peak_ram_mb"] / (self.baseline["avg_peak_ram_mb"] + 1e-6)
        if ram_ratio > 1.10:
            regression_detected = True
            warnings.append(f"RAM usage Regression: memory footprint grew by {(ram_ratio - 1.0)*100:.1f}% ({current_stats['avg_peak_ram_mb']:.1f}MB vs. baseline {self.baseline['avg_peak_ram_mb']:.1f}MB)")

        return {
            "regression_detected": regression_detected,
            "warnings": warnings,
            "quality_delta": -quality_drop,
            "latency_delta_percent": (speed_ratio - 1.0) * 100.0,
            "memory_delta_percent": (ram_ratio - 1.0) * 100.0
        }
