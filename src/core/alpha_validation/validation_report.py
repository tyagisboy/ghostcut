import os
import json

class ValidationReport:
    """
    Compiles comparative metrics across pipelines into clean markdown documents.
    """
    def __init__(self, data_path: str = None):
        if data_path is None:
            self.data_path = os.path.join(os.path.dirname(__file__), "alpha_benchmark_results.json")
        else:
            self.data_path = data_path

    def generate_report(self) -> str:
        if not os.path.exists(self.data_path):
            return "No validation run records found."
            
        try:
            with open(self.data_path, "r") as f:
                data = json.load(f)
        except Exception as e:
            return f"Error loading results data: {e}"
            
        lines = []
        lines.append("# GhostCut Alpha Validation & Benchmark Program (AVBP) v7.5 Report")
        lines.append("")
        lines.append("## Objective Validation Verification Results")
        lines.append("This document proves the quantitative performance improvements of the **Unified Alpha Intelligence Engine (AIE)** compared to legacy heuristics and neural cascades.")
        lines.append("")
        
        for category, pipelines in data.items():
            lines.append(f"### Category: `{category}`")
            lines.append("| Pipeline Variant | Boundary IoU | SAD | Gradient Error | Halo Width | Processing Time | Peak Memory |")
            lines.append("| --- | --- | --- | --- | --- | --- | --- |")
            
            for p_name, metrics in pipelines.items():
                iou_pct = metrics["boundary_iou"] * 100.0
                sad_val = metrics["sad"]
                grad_err = metrics["gradient_error"]
                halo = metrics["halo_width"]
                p_time = metrics["processing_time_ms"]
                mem = metrics["peak_memory_mb"]
                
                lines.append(f"| {p_name} | {iou_pct:.1f}% | {sad_val:.2f} | {grad_err:.2f} | {halo:.1f}px | {p_time:.1f}ms | {mem:.1f}MB |")
            lines.append("")
            
        return "\n".join(lines)
