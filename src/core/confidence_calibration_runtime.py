from src.core.base_learning_runtime import BaseLearningRuntime

class ConfidenceCalibrationRuntime(BaseLearningRuntime):
    """
    SDK compliant Confidence Calibration runtime.
    Calibrates prediction scores using historical reliability metrics to prevent systematic overconfidence.
    """
    def __init__(self):
        # Local historical reliability dictionary
        # Defines average precision of each runtime under standard conditions
        self.reliability_table = {
            "hair": 0.91,
            "fur": 0.88,
            "transparency": 0.85,
            "face": 0.94,
            "clothing": 0.92,
            "edge": 0.89,
            "initial_segmentation": 0.90
        }

    def get_metadata(self) -> dict:
        return {
            "id": "confidence_calibration",
            "name": "Confidence Calibration",
            "version": "1.0",
            "execution_cost": 0.5
        }

    def calibrate(self, raw_confidence: float, runtime_id: str, context: dict = None) -> float:
        """
        Calibrates the raw score using history reliability and background complexity penalties.
        """
        base_rel = self.reliability_table.get(runtime_id, 0.90)
        
        # Penalize reliability if background is highly complex
        penalty = 0.0
        if context and "background" in context:
            complexity = context["background"].get("complexity", "low")
            if complexity == "high":
                penalty = 0.12
            elif complexity == "medium":
                penalty = 0.04
                
        calibrated = raw_confidence * (base_rel - penalty)
        import numpy as np
        return float(np.clip(calibrated, 0.1, 1.0))

    def learn(self, input_data: dict, outcome_data: dict) -> dict:
        # Dynamically update reliability table based on user rating changes
        # (simulated offline calibration loop)
        runtime_id = input_data.get("runtime_id")
        success = outcome_data.get("rating", 1) == 1
        if runtime_id in self.reliability_table:
            # Shift table slightly based on reinforcement learning feedback
            shift = 0.01 if success else -0.02
            import numpy as np
            self.reliability_table[runtime_id] = float(np.clip(self.reliability_table[runtime_id] + shift, 0.5, 0.99))
        return {"status": "SUCCESS", "reliability_table": self.reliability_table}
