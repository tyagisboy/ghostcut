import os
import json

class CalibrationMetrics:
    """
    Calibrates confidence calculations using historical metrics:
    Calibrated Confidence = Model Confidence * Historical Runtime Accuracy * Scene Reliability * Strategy Reliability
    """
    def __init__(self, stats_path: str = None):
        if stats_path is None:
            self.stats_path = os.path.join(os.path.dirname(__file__), "vision_runtime_stats.json")
        else:
            self.stats_path = stats_path
            
        self.stats = self._load_stats()

    def _load_stats(self) -> dict:
        if os.path.exists(self.stats_path):
            try:
                with open(self.stats_path, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Default fallback historical stats structure
        defaults = {
            "runtimes": {
                "scene": {"accuracy": 0.96, "precision": 0.95, "recall": 0.97},
                "subject": {"accuracy": 0.94, "precision": 0.92, "recall": 0.95},
                "background": {"accuracy": 0.93, "precision": 0.91, "recall": 0.94},
                "material": {"accuracy": 0.91, "precision": 0.89, "recall": 0.92},
                "hair": {"accuracy": 0.92, "precision": 0.90, "recall": 0.93},
                "fur": {"accuracy": 0.93, "precision": 0.91, "recall": 0.92},
                "edge": {"accuracy": 0.90, "precision": 0.88, "recall": 0.91}
            },
            "scenes": {
                "Studio Portrait": {"reliability": 0.98},
                "Outdoor Portrait": {"reliability": 0.91},
                "Product": {"reliability": 0.95},
                "Pet": {"reliability": 0.93},
                "Food": {"reliability": 0.92},
                "Unknown": {"reliability": 0.80}
            },
            "strategies": {
                "Human": {"reliability": 0.97},
                "Animal": {"reliability": 0.94},
                "Plant": {"reliability": 0.91},
                "Product": {"reliability": 0.95}
            }
        }
        self._save_stats(defaults)
        return defaults

    def _save_stats(self, data: dict) -> None:
        try:
            with open(self.stats_path, "w") as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass

    def calibrate(self, runtime_id: str, model_confidence: float, scene_name: str, strategy_name: str) -> float:
        # Get historical accuracy
        runtime_data = self.stats["runtimes"].get(runtime_id, {"accuracy": 0.90})
        historical_accuracy = runtime_data.get("accuracy", 0.90)
        
        # Get scene reliability
        scene_data = self.stats["scenes"].get(scene_name, {"reliability": 0.85})
        scene_reliability = scene_data.get("reliability", 0.85)
        
        # Get strategy reliability
        strategy_data = self.stats["strategies"].get(strategy_name, {"reliability": 0.90})
        strategy_reliability = strategy_data.get("reliability", 0.90)
        
        # Apply formula
        calibrated = model_confidence * historical_accuracy * scene_reliability * strategy_reliability
        return min(1.0, max(0.0, float(calibrated)))
