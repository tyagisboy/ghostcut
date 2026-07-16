import os
import json
from src.core.base_learning_runtime import BaseLearningRuntime

class BenchmarkIntelligenceRuntime(BaseLearningRuntime):
    """
    SDK compliant Benchmark Intelligence runtime.
    Logs run times, scores, and versions to identify execution trends.
    """
    def __init__(self, history_path="benchmark_history.json"):
        self.history_path = history_path
        self.history = self._load_history()

    def get_metadata(self) -> dict:
        return {
            "id": "benchmark_intelligence",
            "name": "Benchmark Intelligence",
            "version": "1.0",
            "execution_cost": 1.0
        }

    def _load_history(self) -> list:
        if os.path.exists(self.history_path):
            try:
                with open(self.history_path, "r", encoding="utf-8") as f:
                    return json.load(f)
            except Exception as e:
                print(f"[-] Failed loading benchmark history: {e}")
        return []

    def _save_history(self) -> None:
        try:
            with open(self.history_path, "w", encoding="utf-8") as f:
                json.dump(self.history, f, indent=4)
        except Exception as e:
            print(f"[-] Failed saving benchmark history: {e}")

    def log_run(self, version: str, overall_score: float, cpu_time_ms: float, peak_memory_mb: float) -> None:
        """
        Records a benchmark run.
        """
        run = {
            "version": version,
            "overall_score": overall_score,
            "cpu_time_ms": cpu_time_ms,
            "peak_memory_mb": peak_memory_mb
        }
        self.history.append(run)
        self._save_history()

    def get_version_averages(self) -> dict:
        """
        Aggregates benchmark outcomes by code version.
        """
        averages = {}
        for run in self.history:
            ver = run.get("version", "unknown")
            if ver not in averages:
                averages[ver] = {
                    "runs": 0,
                    "total_score": 0.0,
                    "total_cpu": 0.0,
                    "total_mem": 0.0
                }
            averages[ver]["runs"] += 1
            averages[ver]["total_score"] += run.get("overall_score", 1.0)
            averages[ver]["total_cpu"] += run.get("cpu_time_ms", 100.0)
            averages[ver]["total_mem"] += run.get("peak_memory_mb", 50.0)

        results = {}
        for ver, metrics in averages.items():
            count = metrics["runs"]
            results[ver] = {
                "avg_score": metrics["total_score"] / count,
                "avg_cpu": metrics["total_cpu"] / count,
                "avg_mem": metrics["total_mem"] / count,
                "runs": count
            }
        return results

    def learn(self, input_data: dict, outcome_data: dict) -> dict:
        self.log_run(
            version=input_data.get("version", "v4.2"),
            overall_score=outcome_data.get("overall_score", 0.95),
            cpu_time_ms=outcome_data.get("cpu_time_ms", 150.0),
            peak_memory_mb=outcome_data.get("peak_memory_mb", 35.0)
        )
        return {"status": "SUCCESS"}
