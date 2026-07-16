from src.core.base_runtime import BaseRuntime
from src.core.scenario import classify_scenario

class SceneIntelligence(BaseRuntime):
    """
    Analyzes pre-inference image characteristics to detect the overall scene category.
    """
    def __init__(self):
        self.supported_scenes = [
            "Studio Portrait", "Outdoor Portrait", "Product", "Pet",
            "Vehicle", "Food", "Document", "Unknown"
        ]

    def get_metadata(self) -> dict:
        return {
            "id": "scene",
            "name": "Scene Intelligence",
            "dependencies": [],
            "execution_cost": 1.0,
            "quality_impact": 7.0,
            "requires_mask": False
        }

    def analyze(self, img_bgr, mask=None, context=None):

        """
        Executes scene analysis on the BGR image.
        """
        try:
            scenario, conf, metrics = classify_scenario(img_bgr)
            # Map scenarios to supported scene types
            if scenario in ["Studio Portrait", "Backlit Portrait"]:
                scene = "Studio Portrait"
            elif scenario == "Outdoor Portrait":
                scene = "Outdoor Portrait"
            elif scenario == "Pet":
                scene = "Pet"
            elif scenario == "Vehicle":
                scene = "Vehicle"
            elif scenario == "Food":
                scene = "Food"
            elif scenario == "Transparent Object":
                scene = "Product"  # product subcategory
            elif scenario in ["Product", "Clothing", "Jewelry", "Plant"]:
                scene = "Product"
            else:
                scene = "Unknown"
            return {
                "scene": scene,
                "confidence": float(conf),
                "metrics": metrics
            }
        except Exception as e:
            return {
                "scene": "Unknown",
                "confidence": 0.0,
                "metrics": {}
            }
