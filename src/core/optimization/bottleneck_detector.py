class BottleneckDetector:
    """
    Detects subsystems that exceed target latency budgets (in ms).
    """
    def __init__(self):
        # Latency thresholds (ms)
        self.thresholds = {
            "decoding": 150.0,
            "inference": 500.0,
            "refinement": 300.0,
            "export": 200.0
        }

    def detect_bottlenecks(self, metrics: dict) -> list:
        bottlenecks = []
        for key, val in metrics.items():
            clean_key = key.replace("_time_ms", "")
            thresh = self.thresholds.get(clean_key)
            if thresh is not None and val > thresh:
                bottlenecks.append({
                    "component": clean_key,
                    "measured_ms": val,
                    "threshold_ms": thresh,
                    "severity": "High" if val > (thresh * 1.5) else "Medium"
                })
        return bottlenecks
