import sys
import subprocess
from src.core.segmentation import SegmentationEngine
from src.core.benchmark_runner import BenchmarkRunner
from src.core.regression_dashboard import RegressionDashboard

def execute_release_validation():
    print("======================================================================")
    print("      GHOSTCUT v1.0 VALIDATION & CALIBRATION PROGRAM (VCP) RUNNER")
    print("======================================================================\n")

    # 1. Run unit/architecture verification tests
    print("[*] Verifying Architecture Integration Suite...")
    arch_res = subprocess.run([sys.executable, "src/core/arch_test.py"], capture_output=True, text=True)
    if arch_res.returncode != 0:
        print("[-] RELEASE BLOCKED: Architecture unit verification failed!")
        print(arch_res.stdout)
        print(arch_res.stderr)
        return False
    print("[OK] Architecture integration verification passed.")

    # 2. Run cognitive system tests
    print("\n[*] Verifying Cognitive Reasoning Suite...")
    cog_res = subprocess.run([sys.executable, "-m", "src.core.benchmark_v5_0"], capture_output=True, text=True)
    if cog_res.returncode != 0:
        print("[-] RELEASE BLOCKED: Cognitive reasoning tests failed!")
        print(cog_res.stdout)
        print(cog_res.stderr)
        return False
    print("[OK] Cognitive reasoning verification passed.")

    # 3. Initialize engine and run benchmark tests
    print("\n[*] Running Gold-Standard Benchmark Runner on categories...")
    engine = SegmentationEngine("models")
    runner = BenchmarkRunner()
    report = runner.run_suite(engine)

    # 4. Perform Regression Delta Checks
    print("\n[*] Auditing Performance & Quality Regression Deltas...")
    avg_quality = sum(r["quality"]["overall_score"] for r in report["results"]) / len(report["results"])
    avg_iou = sum(r["quality"]["iou"] for r in report["results"]) / len(report["results"])
    avg_duration = sum(r["performance"]["duration_ms"] for r in report["results"]) / len(report["results"])
    avg_ram = sum(r["performance"]["peak_ram_mb"] for r in report["results"]) / len(report["results"])

    current_stats = {
        "avg_quality_score": avg_quality,
        "avg_iou": avg_iou,
        "avg_duration_ms": avg_duration,
        "avg_peak_ram_mb": avg_ram
    }

    reg_dashboard = RegressionDashboard()
    comparison = reg_dashboard.compare_build(current_stats)

    # 5. Evaluate Release Certification Checklist
    print("\n======================================================================")
    print("                RELEASE CERTIFICATION CHECKLIST")
    print("======================================================================")
    
    check_arch = "PASS"
    check_cognitive = "PASS"
    check_quality = "PASS" if avg_quality >= 0.88 else "FAIL"
    check_regression = "PASS" if not comparison["regression_detected"] else "FAIL"
    check_telemetry = "PASS" if avg_ram <= 64.0 else "FAIL"

    print(f"- Architecture Tests Status  : {check_arch}")
    print(f"- Cognitive Systems Status   : {check_cognitive}")
    print(f"- Quality Score Threshold    : {check_quality} (Observed: {avg_quality*100:.1f}%)")
    print(f"- Regression Safeguard Status : {check_regression}")
    print(f"- Telemetry RAM Threshold    : {check_telemetry} (Observed: {avg_ram:.1f}MB)")
    print("----------------------------------------------------------------------")

    if "FAIL" in [check_arch, check_cognitive, check_quality, check_regression, check_telemetry]:
        print("\n[-] STATUS: RELEASE BLOCKED")
        print("Warnings/Reasons:")
        for warn in comparison["warnings"]:
            print(f"  [WARNING] {warn}")
        if avg_quality < 0.88:
            print(f"  [WARNING] Quality threshold not met ({avg_quality*100:.1f}% observed vs. 88.0% required)")
        print("======================================================================\n")
        return False
    else:
        print("\n[+] STATUS: RELEASE APPROVED (GhostCut v1.0 Core Frozen)")
        print("======================================================================\n")
        return True

if __name__ == "__main__":
    success = execute_release_validation()
    sys.exit(0 if success else 1)
