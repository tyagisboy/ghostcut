import os
import json

class DashboardAdapter:
    """
    Formats the capability validation metrics into clean HTML explainability templates
    for rendering in QWebEngine.
    """
    def __init__(self, data_path: str = None):
        if data_path is None:
            self.data_path = os.path.join(os.path.dirname(__file__), "alpha_benchmark_history.json")
        else:
            self.data_path = data_path

    def format_html_dashboard(self, latest_version: str = "v1.0.0_baseline") -> str:
        if not os.path.exists(self.data_path):
            return "<p>No benchmark run metrics found.</p>"
            
        try:
            with open(self.data_path, "r") as f:
                history = json.load(f)
        except Exception:
            return "<p>Failed parsing benchmark history.</p>"
            
        runs = history.get(latest_version, {})
        if not runs:
            # Fallback to first available run
            available = list(history.keys())
            if available:
                runs = history[available[-1]]
            else:
                return "<p>No run data parsed.</p>"
                
        html = "<h4>Capability Radar & Scorecard</h4>"
        html += "<div style='font-family: Consolas, monospace; background-color: #1e1e2e; color: #cdd6f4; padding: 12px; border-radius: 6px; font-size: 11px; line-height: 1.4;'>"
        
        for category, caps in runs.items():
            html += f"<b>➔ {category}:</b><br>"
            for cap_name, val in caps.items():
                col = "#a6e3a1" if val >= 0.85 else "#f9e2af" if val >= 0.70 else "#f38ba8"
                html += f"  - {cap_name}: <span style='color: {col}; font-weight: bold;'>{val*100.0:.1f}%</span><br>"
                
        html += "</div>"
        return html
