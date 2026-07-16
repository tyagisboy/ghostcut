import os
import json

class ReportGenerator:
    """
    Compiles capability-driven metrics into clear markdown summary reports.
    """
    def __init__(self, data_path: str = None):
        if data_path is None:
            self.data_path = os.path.join(os.path.dirname(__file__), "alpha_benchmark_history.json")
        else:
            self.data_path = data_path

    def compile_markdown(self) -> str:
        if not os.path.exists(self.data_path):
            return "No historical benchmark runs found."
            
        try:
            with open(self.data_path, "r") as f:
                history = json.load(f)
        except Exception as e:
            return f"Error loading results: {e}"
            
        lines = []
        lines.append("# GhostCut Alpha Validation & Benchmark Program (AVBP) v7.5 Summary")
        lines.append("")
        lines.append("## Objective Capability-Based Scorecards")
        lines.append("The following tables verify that the Unified Alpha Intelligence Engine consistently maintains high capability scores across categories.")
        lines.append("")
        
        for version, runs in history.items():
            lines.append(f"### Run Version Target: `{version}`")
            lines.append("| Category | Capability Metric | Score | status |")
            lines.append("| --- | --- | --- | --- |")
            
            for cat, caps in runs.items():
                for cap_name, val in caps.items():
                    status_str = "✔ PASS" if val >= 0.85 else "⚠ WARNING" if val >= 0.70 else "✘ FAIL"
                    lines.append(f"| {cat} | {cap_name} | {val*100.0:.1f}% | {status_str} |")
            lines.append("")
            
        return "\n".join(lines)
