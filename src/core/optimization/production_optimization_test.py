import os
import sys

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "..", "..", "..")))

from src.core.optimization.performance_profiler import PerformanceProfiler
from src.core.optimization.resource_manager import AdaptiveResourceManager
from src.core.optimization.bottleneck_detector import BottleneckDetector

def test_performance_profiler():
    print("[*] Testing PerformanceProfiler timers and psutil RSS metrics...")
    profiler = PerformanceProfiler()
    profiler.start_timer("total")
    profiler.start_timer("decoding")
    profiler.stop_timer("decoding")
    profiler.stop_timer("total")
    
    metrics = profiler.export_metrics()
    assert "peak_memory_mb" in metrics
    assert "cpu_utilization_pct" in metrics
    assert metrics["decoding_time_ms"] >= 0.0
    print("  [+] Profiler metrics generated successfully:", metrics)

def test_resource_manager():
    print("[*] Testing AdaptiveResourceManager profiling parameters...")
    manager = AdaptiveResourceManager()
    hw = manager.get_hardware_profile()
    assert "cpu_cores" in hw
    assert "total_ram_gb" in hw
    assert hw["selected_profile"] in ["Eco", "Balanced", "Quality", "Ultra"]
    print("  [+] Resource manager loaded successfully. Hardware Profile:", hw)

def test_bottleneck_detector():
    print("[*] Testing BottleneckDetector budget checks...")
    detector = BottleneckDetector()
    metrics = {
        "decoding_time_ms": 10.0,
        "inference_time_ms": 850.0,  # Exceeds threshold of 500ms
        "refinement_time_ms": 150.0
    }
    bottlenecks = detector.detect_bottlenecks(metrics)
    assert len(bottlenecks) > 0
    assert bottlenecks[0]["component"] == "inference"
    assert bottlenecks[0]["severity"] == "High"
    print("  [+] Detected bottleneck alerts:", bottlenecks)

def main():
    print("======================================")
    print("Running GhostCut v8.0 Optimization Tests")
    print("======================================")
    
    test_performance_profiler()
    test_resource_manager()
    test_bottleneck_detector()
    
    print("\n======================================")
    print("All GhostCut v8.0 Optimization Tests Passed.")
    print("======================================")

if __name__ == "__main__":
    main()
