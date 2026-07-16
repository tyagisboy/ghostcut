import os
import json

class AlphaPolicy:
    """
    Manages loading and matching of regional alpha policies.
    """
    def __init__(self, library_path: str = None):
        if library_path is None:
            self.library_path = os.path.join(os.path.dirname(__file__), "alpha_policy_library.json")
        else:
            self.library_path = library_path
            
        self.policies = self._load_policies()

    def _load_policies(self) -> dict:
        if os.path.exists(self.library_path):
            try:
                with open(self.library_path, "r") as f:
                    return json.load(f)
            except Exception:
                pass
        
        # Default policies if not found
        defaults = {
            "Hair": {
                "preserve_strands": True,
                "decontaminate": True,
                "smoothness": 0.4,
                "edge_gradient_scale": 1.5
            },
            "Fur": {
                "preserve_fibers": True,
                "decontaminate": True,
                "smoothness": 0.3,
                "edge_gradient_scale": 1.2
            },
            "Skin": {
                "preserve_strands": False,
                "decontaminate": False,
                "smoothness": 0.8,
                "edge_gradient_scale": 0.5
            },
            "Glass": {
                "preserve_strands": False,
                "decontaminate": False,
                "smoothness": 0.9,
                "edge_gradient_scale": 2.0,
                "transparency_boost": True
            },
            "Fabric": {
                "preserve_strands": False,
                "decontaminate": True,
                "smoothness": 0.5,
                "edge_gradient_scale": 1.0
            }
        }
        self._save_policies(defaults)
        return defaults

    def _save_policies(self, data: dict) -> None:
        try:
            with open(self.library_path, "w") as f:
                json.dump(data, f, indent=4)
        except Exception:
            pass

    def get_policy(self, name: str) -> dict:
        return self.policies.get(name, self.policies.get("Skin"))
