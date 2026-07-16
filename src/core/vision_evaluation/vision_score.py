class VisionScorecard:
    """
    Scorecard tracking validation correctness indices and calculating a composite
    overall Vision Score for evaluation runs.
    """
    def __init__(self, image_id: str):
        self.image_id = image_id
        self.scores = {}
        self.warnings = []

    def add_score(self, category: str, score: float, details: dict = None) -> None:
        self.scores[category] = {
            "score": float(score),
            "details": details if details is not None else {}
        }

    def add_warning(self, warn_str: str) -> None:
        self.warnings.append(warn_str)

    def calculate_vision_score(self) -> float:
        if not self.scores:
            return 1.0
        # Compute simple average of category scores
        total = sum(item["score"] for item in self.scores.values())
        return float(total / len(self.scores))

    def to_dict(self) -> dict:
        v_score = self.calculate_vision_score()
        return {
            "image_id": self.image_id,
            "overall_vision_score": v_score,
            "category_scores": self.scores,
            "warnings": self.warnings
        }
