class BaseCognitiveRuntime:
    """
    Abstract Base Class for GhostCut v5 Runtimes (sensors).
    Conforms to the Cognitive Vision Sensor contract.
    """
    def initialize(self, config: dict) -> None:
        pass

    def execute(self, context) -> "RuntimeResult":
        """
        Standardized execution wrapper compiling sensory details.
        """
        import time
        from src.core.runtime_result import RuntimeResult
        
        start = time.time()
        warnings = []
        try:
            evidences = self.produceEvidence(context.img_bgr, context=context)
            obs = [ev["observation"] for ev in evidences]
            conf = self.estimateConfidence()
            
            for ev in evidences:
                context.evidence_graph.add_node(
                    runtime_id=ev.get("runtime", "unknown"),
                    observation=ev["observation"],
                    confidence=ev["confidence"],
                    evidence_details=ev["evidence"]
                )
        except Exception as e:
            warnings.append(f"Execution failed: {e}")
            obs = []
            evidences = []
            conf = 0.0
            
        dur = (time.time() - start) * 1000.0
        return RuntimeResult(
            runtime_id=getattr(self, "runtime_id", "unknown"),
            observations=obs,
            evidence=[ev["evidence"] for ev in evidences],
            confidence=conf,
            duration_ms=dur,
            warnings=warnings
        )

    def observe(self, img_bgr, mask=None, context=None) -> list:
        """
        Extracts observations from inputs.
        """
        raise NotImplementedError

    def produceEvidence(self, img_bgr, mask=None, context=None) -> list:
        """
        Compiles observations into a list of structured EvidenceNode dicts:
        {
            "id": str,
            "runtime": str,
            "observation": str,
            "confidence": float,
            "evidence": list,
            "cost": float,
            "dependencies": list
        }
        """
        raise NotImplementedError

    def estimateConfidence(self) -> float:
        """
        Calculates raw self-estimation confidence.
        """
        return 0.90

    def estimateCost(self) -> float:
        """
        Returns runtime CPU execution cost.
        """
        return 1.0

    def explain(self) -> str:
        """
        Returns natural language description of evidence detection rules.
        """
        return ""

    def validateDependencies(self) -> list:
        """
        Returns list of required runtimes.
        """
        return []
