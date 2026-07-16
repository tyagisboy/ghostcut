class PerceptionRegion:
    """
    Represents properties for a semantic foreground region.
    """
    def __init__(self, name: str, confidence: float = 0.0, edge_type: str = "Hard", transparency: bool = False, refinement_policy: str = "default", repair_priority: int = 3):
        self.name = name
        self.confidence = float(confidence)
        self.edge_type = edge_type  # Hard, Soft, Hair, Fur, Transparent
        self.transparency = bool(transparency)
        self.refinement_policy = refinement_policy
        self.repair_priority = int(repair_priority)  # 1 = highest, 5 = lowest

    def to_dict(self) -> dict:
        return {
            "name": self.name,
            "confidence": self.confidence,
            "edge_type": self.edge_type,
            "transparency": self.transparency,
            "refinement_policy": self.refinement_policy,
            "repair_priority": self.repair_priority
        }

class PerceptionState:
    """
    Maintains the aggregated semantic foreground region segment states.
    """
    def __init__(self):
        self.regions = {}

    def add_region(self, name: str, **kwargs) -> PerceptionRegion:
        region = PerceptionRegion(name, **kwargs)
        self.regions[name.lower()] = region
        return region

    def get_region(self, name: str) -> PerceptionRegion:
        return self.regions.get(name.lower())

    def to_dict(self) -> dict:
        return {name: reg.to_dict() for name, reg in self.regions.items()}
