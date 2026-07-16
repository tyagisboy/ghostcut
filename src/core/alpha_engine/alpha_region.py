class AlphaRegion:
    """
    Represents semantic region criteria inside the alpha composition solver.
    """
    def __init__(self, semantic_type: str, material: str, edge_type: str, transparency_class: str, confidence: float = 0.90, repair_priority: int = 3, expected_behavior: str = "default"):
        self.semantic_type = semantic_type
        self.material = material
        self.edge_type = edge_type  # Hard, Soft, Hair, Fur, Transparent
        self.transparency_class = transparency_class  # Opaque, SemiTransparent, FullTransparent
        self.confidence = float(confidence)
        self.repair_priority = int(repair_priority)
        self.expected_behavior = expected_behavior

    def to_dict(self) -> dict:
        return {
            "semantic_type": self.semantic_type,
            "material": self.material,
            "edge_type": self.edge_type,
            "transparency_class": self.transparency_class,
            "confidence": self.confidence,
            "repair_priority": self.repair_priority,
            "expected_behavior": self.expected_behavior
        }
