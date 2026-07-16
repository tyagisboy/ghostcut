class RuntimeResult:
    """
    Standardized payload packaging execution output metrics
    for all GhostCut runtime sensors.
    """
    def __init__(self, runtime_id: str, observations: list = None, evidence: list = None, confidence: float = 1.0, duration_ms: float = 0.0, warnings: list = None):
        self.runtime_id = runtime_id
        self.observations = observations if observations is not None else []
        self.evidence = evidence if evidence is not None else []
        self.confidence = float(confidence)
        self.duration_ms = float(duration_ms)
        self.warnings = warnings if warnings is not None else []

    def to_dict(self) -> dict:
        return {
            "runtime_id": self.runtime_id,
            "observations": self.observations,
            "evidence": self.evidence,
            "confidence": self.confidence,
            "duration_ms": self.duration_ms,
            "warnings": self.warnings
        }
