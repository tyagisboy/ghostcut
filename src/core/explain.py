import os
import json
import datetime

class DecisionLogger:
    """
    Saves explainable processing decisions made by the Image Intelligence Engine.
    Exposes these decisions in human-readable and structured formats for developers and UI dashboards.
    """
    _instance = None
    
    def __new__(cls, *args, **kwargs):
        if not cls._instance:
            cls._instance = super(DecisionLogger, cls).__new__(cls, *args, **kwargs)
            cls._instance.logs = []
        return cls._instance
        
    def clear(self):
        self.logs = []

    def log(self, category, parameter, decision_value, reason):
        """
        Records a single decision.
        """
        entry = {
            "timestamp": datetime.datetime.now().isoformat(),
            "category": category,
            "parameter": parameter,
            "value": str(decision_value),
            "reason": reason
        }
        self.logs.append(entry)
        print(f"[DECISION] {category} | {parameter} -> {decision_value} ({reason})")

    def get_logs(self):
        return self.logs

    def get_formatted_text(self):
        """
        Formats logs as a clean, human-readable markdown text.
        """
        if not self.logs:
            return "No decisions logged yet."
            
        lines = ["### Image Intelligence Decision Log\n"]
        for log in self.logs:
            lines.append(f"- **[{log['category']}]** {log['parameter']} set to `{log['value']}`  \n  *Reason:* {log['reason']}")
        return "\n".join(lines)

    def save_to_file(self, target_dir):
        """
        Saves the structured log into a file.
        """
        os.makedirs(target_dir, exist_ok=True)
        path = os.path.join(target_dir, "intelligence_decision_log.json")
        try:
            with open(path, "w", encoding="utf-8") as f:
                json.dump(self.logs, f, indent=4)
        except Exception as e:
            print(f"[-] Failed to save decision logs: {e}")
        return path
