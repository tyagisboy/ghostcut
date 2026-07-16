from src.core.base_learning_runtime import BaseLearningRuntime

class RegressionIntelligence(BaseLearningRuntime):
    """
    Checks for performance or quality regressions by comparing metrics
    from the current code version against the previous baseline version.
    """
    def __init__(self):
        pass

    def get_metadata(self) -> dict:
        return {
            "id": "regression_intelligence",
            "name": "Regression Intelligence",
            "version": "1.0",
            "execution_cost": 0.5
        }

    def check_regression(self, current_version: str, prev_version: str, version_averages: dict) -> dict:
        """
        Inputs:
            current_version: e.g. "v4.3"
            prev_version: e.g. "v4.2"
            version_averages: Aggregated version metrics from BenchmarkIntelligence
        Returns:
            regression_detected: bool
            report: dict with details on CPU changes, quality changes, and warnings.
        """
        if current_version not in version_averages or prev_version not in version_averages:
            return {
                "regression_detected": False,
                "reason": "Insufficient comparative version history",
                "details": {}
            }

        curr = version_averages[current_version]
        prev = version_averages[prev_version]

        score_diff = curr["avg_score"] - prev["avg_score"]
        cpu_ratio = curr["avg_cpu"] / (prev["avg_cpu"] + 1e-5)
        mem_ratio = curr["avg_mem"] / (prev["avg_mem"] + 1e-5)

        warnings = []
        regression = False

        # Flag quality regression: drop > 2%
        if score_diff < -0.02:
            regression = True
            warnings.append(f"Quality regression detected: average score dropped by {abs(score_diff)*100:.1f}%")

        # Flag performance regression: CPU time increase > 25%
        if cpu_ratio > 1.25:
            regression = True
            warnings.append(f"CPU performance regression detected: execution time increased by {(cpu_ratio - 1.0)*100:.1f}%")

        # Flag memory regression: memory usage increase > 35%
        if mem_ratio > 1.35:
            regression = True
            warnings.append(f"Memory overhead regression detected: peak memory increased by {(mem_ratio - 1.0)*100:.1f}%")

        return {
            "regression_detected": regression,
            "warnings": warnings,
            "details": {
                "quality_diff_percent": float(score_diff * 100.0),
                "cpu_change_percent": float((cpu_ratio - 1.0) * 100.0),
                "mem_change_percent": float((mem_ratio - 1.0) * 100.0)
            }
        }

    def learn(self, input_data: dict, outcome_data: dict) -> dict:
        return {"status": "SUCCESS"}
