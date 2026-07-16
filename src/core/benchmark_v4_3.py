import os
import sys
import numpy as np
from src.core.recipe_memory_runtime import RecipeMemoryRuntime
from src.core.failure_memory_runtime import FailureMemoryRuntime
from src.core.recipe_ranking_engine import RecipeRankingEngine
from src.core.confidence_calibration_runtime import ConfidenceCalibrationRuntime
from src.core.benchmark_intelligence import BenchmarkIntelligenceRuntime
from src.core.regression_intelligence import RegressionIntelligence
from src.core.learning_import_export import LearningImportExport
from src.core.recipe_engine import ProcessingRecipe

def run_v4_3_benchmarks():
    print("[*] Initializing Adaptive Learning v4.3 Benchmark Suite...")
    
    test_db = "test_learning_db.json"
    test_fail_db = "test_failure_db.json"
    test_bench_db = "test_benchmark_history.json"
    test_export = "test_scrubbed_export.json"

    # Ensure clean database files for testing
    for path in [test_db, test_fail_db, test_bench_db, test_export]:
        if os.path.exists(path):
            os.remove(path)

    try:
        # 1. Test Recipe Memory & Querying
        print("[*] Testing Recipe Memory Runtime database writes and querying...")
        mem_runtime = RecipeMemoryRuntime(test_db)
        
        # Log mock successful run
        mock_features = {
            "aspect_ratio": 1.5,
            "mean_b": 120.0,
            "mean_g": 130.0,
            "mean_r": 140.0,
            "laplacian_var": 950.0,
            "bg_var": 500.0,
            "bg_mean": 200.0
        }
        mock_params = {
            "model_name": "birefnet-general-lite",
            "erode_size": 2,
            "apply_matting": True
        }
        mem_runtime.save_record("h:/AI Tools/Background Removal/my_secret_portrait.jpg", mock_features, mock_params, rating=1)
        
        # Verify db contains 1 record
        assert len(mem_runtime.records) == 1
        
        # Query matching features
        match = mem_runtime.find_similar_recipe(mock_features)
        assert match is not None
        assert match["params"]["erode_size"] == 2
        assert "my_secret_portrait.jpg" in match["file_path"]
        print("[OK] Recipe Memory Runtime lookup successfully matching parameters.")

        # 2. Test Recipe Ranking Engine
        print("\n[*] Testing Recipe Ranking Engine candidates sorting...")
        ranker = RecipeRankingEngine()
        
        default_recipe = ProcessingRecipe(settings_dict={"model_name": "birefnet-general"})
        ranking_res = ranker.rank_recipes(default_recipe, match)
        
        # Match has rating 1 and 0 distance, score should be ~0.95 -> ranked 1st
        assert ranking_res["best_recipe"].model_name == "birefnet-general-lite"
        assert ranking_res["confidence"] > 0.85
        print("[OK] Recipe Ranking Engine successfully prioritized historical recipe.")

        # 3. Test Failure Memory Prediction
        print("\n[*] Testing Failure Memory Runtime recording and proactive prevention...")
        fail_runtime = FailureMemoryRuntime(test_fail_db)
        
        # Log a mock halo failure
        fail_runtime.log_failure(mock_features, {"halo": 0.8, "spill": 0.1}, "contract_matte")
        assert len(fail_runtime.failures) == 1
        
        # Query risk for matching features
        risk_res = fail_runtime.predict_failure_risk(mock_features)
        assert "halo" in risk_res["risk_factors"]
        assert risk_res["suggested_action"]["repair_strategy"] == "contract_matte"
        print("[OK] Failure Memory Runtime properly recorded and predicted artifact risks.")

        # 4. Test Confidence Calibration
        print("\n[*] Testing Confidence Calibration Runtime scaling...")
        calibrator = ConfidenceCalibrationRuntime()
        
        # Under normal conditions, hair calibration is high
        cal_normal = calibrator.calibrate(0.85, "hair", context={})
        # Under high background complexity, calibration decreases due to reliability penalty
        cal_complex = calibrator.calibrate(0.85, "hair", context={"background": {"complexity": "high"}})
        
        assert cal_complex < cal_normal
        print(f"[OK] Confidence calibrated: Normal={cal_normal:.2f} | Complex={cal_complex:.2f} (penalized).")

        # 5. Test Benchmark Intelligence & Regression Detection
        print("\n[*] Testing Benchmark Intelligence aggregates and Regression check...")
        bench_runtime = BenchmarkIntelligenceRuntime(test_bench_db)
        
        # Log previous version (v4.2) averages
        bench_runtime.log_run("v4.2", overall_score=0.96, cpu_time_ms=120.0, peak_memory_mb=40.0)
        bench_runtime.log_run("v4.2", overall_score=0.94, cpu_time_ms=130.0, peak_memory_mb=42.0)
        
        # Log current version (v4.3) showing regression (e.g. CPU time spikes)
        bench_runtime.log_run("v4.3", overall_score=0.95, cpu_time_ms=210.0, peak_memory_mb=41.0)
        
        averages = bench_runtime.get_version_averages()
        assert "v4.2" in averages
        assert "v4.3" in averages
        
        reg_intel = RegressionIntelligence()
        reg_res = reg_intel.check_regression("v4.3", "v4.2", averages)
        
        # CPU spike was 210 / 125 = 1.68 (> 1.25), regression should trigger
        assert reg_res["regression_detected"] is True
        assert any("CPU performance regression" in w for w in reg_res["warnings"])
        print("[OK] Regression Intelligence successfully flagged version speed regressions.")

        # 6. Test Learning Import / Export
        print("\n[*] Testing Learning Import/Export path-scrubbing...")
        io_handler = LearningImportExport(db_path=test_db, failure_path=test_fail_db)
        
        # Export database
        success_exp = io_handler.export_database(test_export)
        assert success_exp is True
        
        # Inspect export file: absolute path must be scrubbed for privacy
        with open(test_export, "r", encoding="utf-8") as f:
            exported_data = json.load(f)
            
        exp_recipe = exported_data["recipes"][0]
        # Should be base filename "my_secret_portrait.jpg", NOT full path!
        assert exp_recipe["file_path"] == "my_secret_portrait.jpg"
        print("[OK] Export verified: absolute paths scrubbed successfully.")

        # Clean databases and verify import merges correctly
        os.remove(test_db)
        os.remove(test_fail_db)
        
        io_new = LearningImportExport(db_path=test_db, failure_path=test_fail_db)
        success_imp = io_new.import_database(test_export)
        assert success_imp is True
        
        # Re-query imported db
        new_mem = RecipeMemoryRuntime(test_db)
        assert len(new_mem.records) == 1
        assert new_mem.records[0]["file_path"] == "my_secret_portrait.jpg"
        print("[OK] Import verified: databases merged and restored successfully.")

        print("\n======================================")
        print("Adaptive Learning v4.3 benchmarks completed: ALL PASSED.")
        print("======================================")
        return True

    finally:
        # Clean up test database files
        for path in [test_db, test_fail_db, test_bench_db, test_export]:
            if os.path.exists(path):
                os.remove(path)

if __name__ == "__main__":
    import json
    success = run_v4_3_benchmarks()
    sys.exit(0 if success else 1)
