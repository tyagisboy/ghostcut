import os
import sys
import numpy as np
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from src.core.vision_evaluation.benchmark_dataset import BenchmarkDataset
from src.core.vision_evaluation.runtime_accuracy import RuntimeAccuracy
from src.core.vision_evaluation.calibration_metrics import CalibrationMetrics
from src.core.vision_evaluation.vision_score import VisionScorecard

from src.core.runtime_registry import RuntimeRegistry
from src.core.runtime_scheduler import RuntimeScheduler
from src.core.execution_context import ExecutionContext

class VisionEvaluator:
    """
    Coordinates end-to-end evaluation runs matching current runtime outputs
    against benchmark ground truths.
    """
    def __init__(self, stats_path: str = None):
        self.dataset = BenchmarkDataset()
        self.calibrator = CalibrationMetrics(stats_path)
        self.registry = RuntimeRegistry()
        self.scheduler = RuntimeScheduler(self.registry)

    def evaluate_image(self, img_id: str, img_bgr: np.ndarray, category: str) -> dict:
        """
        Executes workflow: prediction -> ground truth comparison -> score compilation -> calibration
        """
        gt = self.dataset.get_ground_truth(category)
        scorecard = VisionScorecard(img_id)
        
        # 1. Setup execution context
        context = ExecutionContext(img_bgr=img_bgr)
        
        # 2. Run prediction runtimes
        # Scene Runtime
        scene_rt = self.registry.get_runtime("scene")()
        scene_res = scene_rt.execute(context)
        actual_scene = scene_res.observations[0] if scene_res.observations else "Unknown"
        
        scene_eval = RuntimeAccuracy.evaluate_classification(
            prediction=actual_scene,
            ground_truth=gt["expected_scene"],
            confidence=scene_res.confidence
        )
        scorecard.add_score("scene", scene_eval["score"], scene_eval)
        
        # Subject Runtime
        subj_rt = self.registry.get_runtime("subject")()
        context.cache["scene_metrics"] = {}
        subj_res = subj_rt.execute(context)
        actual_subjects = subj_res.observations
        
        subj_eval = RuntimeAccuracy.evaluate_set(
            predictions=actual_subjects,
            ground_truth=gt["expected_subjects"]
        )
        scorecard.add_score("subject", subj_eval["score"], subj_eval)
        
        # Material mapping & classification (using mock checks)
        expected_materials = gt["expected_materials"]
        # Run Material runtime if mapped
        mat_rt = self.registry.get_runtime("material")()
        mat_res = mat_rt.execute(context)
        mat_eval = RuntimeAccuracy.evaluate_set(
            predictions=mat_res.observations,
            ground_truth=expected_materials
        )
        scorecard.add_score("material", mat_eval["score"], mat_eval)

        # Edge classification
        expected_edges = gt["expected_edges"]
        edge_rt = self.registry.get_runtime("edge")()
        edge_res = edge_rt.execute(context)
        edge_eval = RuntimeAccuracy.evaluate_set(
            predictions=edge_res.observations,
            ground_truth=expected_edges
        )
        scorecard.add_score("edge", edge_eval["score"], edge_eval)

        # 3. Apply confidence calibration metrics
        # Calibrated Confidence = Model Confidence * Accuracy * Scene Reliability * Strategy Reliability
        strategy_name = "Human" if "Human" in actual_subjects else "Product"
        calibrated_scene_conf = self.calibrator.calibrate(
            runtime_id="scene",
            model_confidence=scene_res.confidence,
            scene_name=actual_scene,
            strategy_name=strategy_name
        )
        
        # Compile final results package
        results = scorecard.to_dict()
        results["category"] = category
        results["calibrated_scene_confidence"] = calibrated_scene_conf
        
        return results

if __name__ == "__main__":
    # Test script run
    evaluator = VisionEvaluator()
    dummy_img = np.zeros((256, 256, 3), dtype=np.uint8)
    dummy_img[64:192, 64:192] = [120, 150, 200]  # Skin colors
    
    out = evaluator.evaluate_image("test_run_1", dummy_img, "Portrait")
    print("Evaluator Test Result:")
    print(out)
