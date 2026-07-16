class RuntimeRegistry:
    """
    Centralized Runtime Registry managing all pluggable GhostCut intelligence modules.
    Registers IDs to their respective runtime classes to support modular loading.
    """
    def __init__(self):
        self._runtimes = {}
        self._initialize_registry()

    def register(self, runtime_id: str, runtime_class) -> None:
        if runtime_id in self._runtimes:
            raise ValueError(f"Duplicate registration ID: '{runtime_id}'")
        self._runtimes[runtime_id] = runtime_class

    def validate_registry(self) -> None:
        """
        Validates registrations: duplicate IDs, missing dependencies, cycles.
        """
        visited = {}
        
        def dfs(rid):
            if rid in visited:
                if visited[rid] == 0:
                    raise ValueError(f"Dependency cycle detected at runtime ID: '{rid}'")
                return
            
            visited[rid] = 0
            
            r_inst = self.get_runtime(rid)()
            meta = r_inst.get_metadata()
            deps = meta.get("dependencies", [])
            
            for dep in deps:
                if dep not in self._runtimes:
                    raise ValueError(f"Runtime ID '{rid}' relies on missing registration: '{dep}'")
                dfs(dep)
                
            visited[rid] = 1
            
        for rid in self._runtimes:
            dfs(rid)

    def get_runtime(self, runtime_id: str):
        runtime_class = self._runtimes.get(runtime_id)
        if runtime_class is None:
            return None
            
        def instantiator(*args, **kwargs):
            instance = runtime_class(*args, **kwargs)
            return CognitiveRuntimeWrapper(instance, runtime_id)
        return instantiator

    def list_runtimes(self) -> dict:
        return self._runtimes


    def _initialize_registry(self) -> None:
        # Lazy imports to avoid cyclic dependencies
        from src.core.scene import SceneIntelligence
        from src.core.subject import SubjectIntelligence
        from src.core.background import BackgroundIntelligence
        from src.core.material_runtime import MaterialRuntime
        from src.core.hair_runtime import HairRuntime
        from src.core.fur_runtime import FurRuntime
        from src.core.edge_runtime import EdgeRuntime
        from src.core.confidence_fusion import ConfidenceFusionRuntime
        from src.core.face_runtime import FaceRuntime
        from src.core.eye_runtime import EyeRuntime
        from src.core.clothing_runtime import ClothingRuntime
        from src.core.animal_anatomy import AnimalAnatomyRuntime
        from src.core.plant_intelligence import PlantIntelligenceRuntime
        from src.core.product_geometry import ProductGeometryRuntime

        self.register("scene", SceneIntelligence)
        self.register("subject", SubjectIntelligence)
        self.register("background", BackgroundIntelligence)
        self.register("material", MaterialRuntime)
        self.register("hair", HairRuntime)
        self.register("fur", FurRuntime)
        self.register("edge", EdgeRuntime)
        self.register("confidence_fusion", ConfidenceFusionRuntime)
        self.register("face", FaceRuntime)
        self.register("eye", EyeRuntime)
        self.register("clothing", ClothingRuntime)
        self.register("animal_anatomy", AnimalAnatomyRuntime)
        self.register("plant", PlantIntelligenceRuntime)
        self.register("product_geometry", ProductGeometryRuntime)

        # v8.5 Quality Intelligence runtimes
        from src.core.hair_morphology_runtime import HairMorphologyRuntime
        from src.core.edge_intelligence_runtime import EdgeIntelligenceRuntime
        from src.core.material_boundary_runtime import MaterialBoundaryRuntime
        from src.core.halo_detection_runtime import HaloDetectionRuntime
        from src.core.quality_intelligence_runtime import QualityIntelligenceRuntime
        from src.core.local_repair_runtime import LocalRepairRuntime

        self.register("hair_morphology", HairMorphologyRuntime)
        self.register("edge_intelligence", EdgeIntelligenceRuntime)
        self.register("material_boundary", MaterialBoundaryRuntime)
        self.register("halo_detection", HaloDetectionRuntime)
        self.register("quality_intelligence", QualityIntelligenceRuntime)
        self.register("local_repair", LocalRepairRuntime)


from src.core.base_cognitive_runtime import BaseCognitiveRuntime

class CognitiveRuntimeWrapper(BaseCognitiveRuntime):
    def __init__(self, raw_instance, runtime_id):
        self.instance = raw_instance
        self.runtime_id = runtime_id

    def get_metadata(self) -> dict:
        if hasattr(self.instance, "get_metadata"):
            return self.instance.get_metadata()
        return {
            "id": self.runtime_id,
            "version": "1.0",
            "dependencies": self.validateDependencies(),
            "execution_cost": self.estimateCost()
        }
    def __getattr__(self, name):
        if hasattr(self.instance, name):
            return getattr(self.instance, name)
        raise AttributeError(f"Wrapped runtime '{self.runtime_id}' has no attribute '{name}'")



    def execute(self, context) -> "RuntimeResult":
        if hasattr(self.instance, "execute"):
            return self.instance.execute(context)
            
        import time
        from src.core.runtime_result import RuntimeResult
        
        start = time.time()
        warnings = []
        try:
            ev_nodes = self.produceEvidence(context.img_bgr, context=context)
            obs = [ev["observation"] for ev in ev_nodes]
            conf = self.estimateConfidence()
            
            for ev in ev_nodes:
                context.evidence_graph.add_node(
                    runtime_id=ev.get("runtime", self.runtime_id),
                    observation=ev["observation"],
                    confidence=ev["confidence"],
                    evidence_details=ev["evidence"]
                )
        except Exception as e:
            warnings.append(f"Execution failed on wrapper: {e}")
            obs = []
            ev_nodes = []
            conf = 0.0
            
        dur = (time.time() - start) * 1000.0
        return RuntimeResult(
            runtime_id=self.runtime_id,
            observations=obs,
            evidence=[ev["evidence"] for ev in ev_nodes],
            confidence=conf,
            duration_ms=dur,
            warnings=warnings
        )

    def observe(self, img_bgr, mask=None, context=None) -> list:
        if hasattr(self.instance, "analyze"):
            try:
                # Resolve context format (ExecutionContext vs. dict)
                if hasattr(context, "cache"):
                    scene_metrics = context.cache.get("scene_metrics", {})
                else:
                    scene_metrics = context.get("scene_metrics", {}) if context else {}

                if self.runtime_id == "subject":
                    res = self.instance.analyze(img_bgr, scene_metrics)
                elif self.runtime_id == "background":
                    res = self.instance.analyze(img_bgr, scene_metrics)
                else:
                    res = self.instance.analyze(img_bgr, mask)
                return [res] if isinstance(res, dict) else []
            except Exception as e:
                print(f"Wrapper observe error on '{self.runtime_id}': {e}")
        return []


    def produceEvidence(self, img_bgr, mask=None, context=None) -> list:
        observations = self.observe(img_bgr, mask, context)
        ev_nodes = []
        for obs in observations:
            if isinstance(obs, dict):
                # Standardize evidence mapping based on runtime type
                if self.runtime_id == "scene":
                    ev_nodes.append({
                        "runtime": self.runtime_id,
                        "observation": obs.get("scene", "General"),
                        "confidence": float(obs.get("confidence", 0.9)),
                        "evidence": list(obs.get("metrics", {}).keys())
                    })
                elif self.runtime_id == "subject":
                    for subj in obs.get("subjects", []):
                        ev_nodes.append({
                            "runtime": self.runtime_id,
                            "observation": subj,
                            "confidence": 0.95,
                            "evidence": ["subject_segmentation"]
                        })
                elif self.runtime_id == "face":
                    if obs.get("has_face"):
                        ev_nodes.append({
                            "runtime": self.runtime_id,
                            "observation": "Human",
                            "confidence": float(obs.get("confidence", 0.95)),
                            "evidence": ["facial_landmarks", "ears", "neck"]
                        })
                elif self.runtime_id == "eye":
                    if obs.get("has_eyes"):
                        ev_nodes.append({
                            "runtime": self.runtime_id,
                            "observation": "Human",
                            "confidence": float(obs.get("confidence", 0.92)),
                            "evidence": ["glasses_detection" if obs.get("glasses") else "pupils"]
                        })
                elif self.runtime_id == "hair":
                    ev_nodes.append({
                        "runtime": self.runtime_id,
                        "observation": "Hair",
                        "confidence": 0.90,
                        "evidence": [obs.get("hair_type", "general")]
                    })
                elif self.runtime_id == "fur":
                    ev_nodes.append({
                        "runtime": self.runtime_id,
                        "observation": "Fur",
                        "confidence": 0.88,
                        "evidence": [obs.get("fur_type", "general")]
                    })

        # Default fallback evidence node
        if not ev_nodes:
            ev_nodes.append({
                "runtime": self.runtime_id,
                "observation": self.runtime_id.capitalize(),
                "confidence": 0.90,
                "evidence": ["sensory_detection"]
            })
        return ev_nodes

    def estimateConfidence(self) -> float:
        if hasattr(self.instance, "estimateConfidence"):
            return self.instance.estimateConfidence()
        return 0.90

    def estimateCost(self) -> float:
        if hasattr(self.instance, "estimateCost"):
            return self.instance.estimateCost()
        costs = {"scene": 1.0, "subject": 1.0, "face": 3.0, "eye": 2.0, "clothing": 2.5}
        return costs.get(self.runtime_id, 1.0)

    def explain(self) -> str:
        if hasattr(self.instance, "explain"):
            return self.instance.explain()
        return f"Standard cognitive sensory processing for {self.runtime_id}"

    def validateDependencies(self) -> list:
        if hasattr(self.instance, "validateDependencies"):
            return self.instance.validateDependencies()
        return []


