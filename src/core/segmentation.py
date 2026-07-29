import os
import cv2
import numpy as np
import onnxruntime as ort
from src.core.recipe import RecipeEngine
from src.core.explain import DecisionLogger
from src.core.validation import RuntimeValidator
from src.core.confidence import ConfidenceEngine
from src.core.material import MaterialClassifier
from src.core.edge import EdgeClassifier
from src.core.radius import AdaptiveRadiusFieldGenerator

class SegmentationEngine:
    """
    Handles local execution of BiRefNet models using ONNX Runtime.
    Supports on-the-fly model switching (High-res vs. Lite), Trimap-guided ViTMatte,
    and adaptiveguided refinement.
    """
    def __init__(self, models_dir):
        self.models_dir = models_dir
        self.sessions_cache = {}
        self.raw_masks_cache = {}
        self.session = None
        self.current_model_name = None
        self.input_name = None
        self.output_name = None
        self.vitmatte_session = None
        self.last_profile = None
        self.last_region_graph = None
        
        # GhostCut v4.0 Registry and Scheduler
        from src.core.runtime_registry import RuntimeRegistry
        from src.core.runtime_scheduler import RuntimeScheduler
        self.registry = RuntimeRegistry()
        self.scheduler = RuntimeScheduler(self.registry)
        self.last_pipeline_plan = None
        self.last_vision_graph = None
        
        # GhostCut v4.2 Quality layer metrics
        self.last_quality_metrics = None
        self.last_quality_heatmap = None
        self.last_repair_log = None

        # GhostCut v5.0 Cognitive Architecture metrics
        self.last_evidence_graph = None
        self.last_belief_graph = None
        self.last_strategy = None
        self.last_self_critic_report = None





    def load_model(self, model_name="birefnet-general"):
        """
        Loads the selected segmentation model into ONNX Runtime session with caching and acceleration.
        """
        if model_name in self.sessions_cache:
            self.session = self.sessions_cache[model_name]
            self.current_model_name = model_name
            self.input_name = self.session.get_inputs()[0].name
            self.output_name = self.session.get_outputs()[0].name
            return

        if model_name == "birefnet-general":
            model_file = "birefnet-general.onnx"
        elif model_name == "birefnet-general-lite":
            model_file = "birefnet-general-lite.onnx"
        elif model_name == "isnet-general-use":
            model_file = "isnet-general-use.onnx"
        elif model_name == "u2net":
            model_file = "u2net.onnx"
        elif model_name == "u2netp":
            model_file = "u2netp.onnx"
        else:
            raise ValueError(f"Unknown model name: {model_name}")

        model_path = os.path.join(self.models_dir, model_file)
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"Model weight file not found: {model_path}")

        # Manage cache size limit to prevent memory bloat (max 4 loaded sessions)
        if len(self.sessions_cache) >= 4:
            oldest_key = list(self.sessions_cache.keys())[0]
            del self.sessions_cache[oldest_key]
            import gc
            gc.collect()

        # Check and select the best available execution providers (DirectML/CUDA -> CPU fallback)
        available_providers = ort.get_available_providers()
        providers = []
        if 'DirectMLExecutionProvider' in available_providers:
            providers.append('DirectMLExecutionProvider')
        if 'CUDAExecutionProvider' in available_providers:
            providers.append('CUDAExecutionProvider')
        providers.append('CPUExecutionProvider')

        # Configure session options for maximum performance
        opts = ort.SessionOptions()
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        opts.enable_cpu_mem_arena = False

        session = ort.InferenceSession(model_path, sess_options=opts, providers=providers)
        self.sessions_cache[model_name] = session

        self.session = session
        self.input_name = self.session.get_inputs()[0].name
        self.output_name = self.session.get_outputs()[0].name
        self.current_model_name = model_name

    def load_vitmatte(self):
        """
        Loads the ViTMatte model into a dedicated ONNX Runtime session with acceleration.
        """
        if self.vitmatte_session is not None:
            return
            
        model_path = os.path.join(self.models_dir, "vitmatte-small.onnx")
        if not os.path.exists(model_path):
            raise FileNotFoundError(f"ViTMatte model weight file not found: {model_path}")
            
        available_providers = ort.get_available_providers()
        providers = []
        if 'DirectMLExecutionProvider' in available_providers:
            providers.append('DirectMLExecutionProvider')
        if 'CUDAExecutionProvider' in available_providers:
            providers.append('CUDAExecutionProvider')
        providers.append('CPUExecutionProvider')

        opts = ort.SessionOptions()
        opts.graph_optimization_level = ort.GraphOptimizationLevel.ORT_ENABLE_ALL
        opts.enable_cpu_mem_arena = False
        
        self.vitmatte_session = ort.InferenceSession(model_path, sess_options=opts, providers=providers)

    def run_vitmatte(self, img_np, mask_np, w_detail):
        """
        Runs ViTMatte inference on img_np (BGR image) and raw prediction mask_np (0-255).
        Includes resolution downscaling guard to prevent quadratic attention OOM memory blowup.
        """
        self.load_vitmatte()
        h, w = img_np.shape[:2]
        
        # Downscale to max 768 dimension to prevent ViTMatte quadratic token memory crash
        max_dim = 768
        if max(h, w) > max_dim:
            scale = max_dim / float(max(h, w))
            new_h_scale = int(round(h * scale))
            new_w_scale = int(round(w * scale))
            img_to_run = cv2.resize(img_np, (new_w_scale, new_h_scale), interpolation=cv2.INTER_LINEAR)
            mask_to_run = cv2.resize(mask_np, (new_w_scale, new_h_scale), interpolation=cv2.INTER_NEAREST)
            w_detail_to_run = cv2.resize(w_detail, (new_w_scale, new_h_scale), interpolation=cv2.INTER_LINEAR)
        else:
            scale = 1.0
            img_to_run = img_np
            mask_to_run = mask_np
            w_detail_to_run = w_detail
            
        h_run, w_run = img_to_run.shape[:2]
        
        # 1. Generate adaptive trimap
        trimap = generate_trimap(mask_to_run, w_detail_to_run, img_to_run)
        
        # 2. Pad to multiples of 32 for ViTMatte shape requirements
        new_h = int(np.ceil(h_run / 32) * 32)
        new_w = int(np.ceil(w_run / 32) * 32)
        
        img_padded = cv2.copyMakeBorder(img_to_run, 0, new_h - h_run, 0, new_w - w_run, cv2.BORDER_REPLICATE)
        trimap_padded = cv2.copyMakeBorder(trimap, 0, new_h - h_run, 0, new_w - w_run, cv2.BORDER_REPLICATE)
        
        # 3. Normalize Image and Trimap
        img_rgb = cv2.cvtColor(img_padded, cv2.COLOR_BGR2RGB).astype(np.float32) / 255.0
        mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
        std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
        img_norm = (img_rgb - mean) / std
        
        trimap_norm = trimap_padded.astype(np.float32) / 255.0
        trimap_norm = np.expand_dims(trimap_norm, axis=2)
        
        # 4. Concatenate and shape layout conversion
        input_concat = np.concatenate([img_norm, trimap_norm], axis=2)
        input_tensor = input_concat.transpose(2, 0, 1).astype(np.float32)
        input_tensor = np.expand_dims(input_tensor, axis=0)
        
        # 5. Run session
        outputs = self.vitmatte_session.run(["alphas"], {"pixel_values": input_tensor})
        pred_alpha = outputs[0][0, 0] # Shape: (new_h, new_w)
        
        # 6. Crop and return [0, 255]
        pred_alpha_cropped = pred_alpha[0:h_run, 0:w_run]
        pred_alpha_cropped = np.clip(pred_alpha_cropped, 0.0, 1.0)
        mask_out = (pred_alpha_cropped * 255.0).astype(np.uint8)
        
        # Upscale back to original size if downscaled
        if scale != 1.0:
            mask_out = cv2.resize(mask_out, (w, h), interpolation=cv2.INTER_LINEAR)
            
        return mask_out

    def process_image(self, img_np, apply_matting=True, fg_thresh=240, bg_thresh=15, erode_size=3, preserve_transparency=False, sharpness=0, focus_thresh=0.0, processing_mode="fast", disable_quality_loop=False, user_prefs=None, file_path=None):
        """
        Runs inference on img_np (BGR image) and returns single-channel mask (0-255).
        Integrates pre-inference scenario classification and adaptive processing recipes.
        Includes a max resolution guard to prevent Out Of Memory (OOM) memory errors.
        """
        orig_h, orig_w = img_np.shape[:2]
        
        # Max resolution guard: cap input resolution to a max dimension of 2048 to prevent OOM memory errors
        max_dim = 2048
        if max(orig_h, orig_w) > max_dim:
            scale_factor = max_dim / float(max(orig_h, orig_w))
            new_h = int(round(orig_h * scale_factor))
            new_w = int(round(orig_w * scale_factor))
            img_np_run = cv2.resize(img_np, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        else:
            scale_factor = 1.0
            img_np_run = img_np

        if not disable_quality_loop:
            # 1. Initialize and clear Decision Logger
            logger = DecisionLogger()
            logger.clear()
            
            # 2. Validate input environment & image
            validator = RuntimeValidator(self.models_dir)
            val_ok, val_issues = validator.validate_input(img_np_run)
            if not val_ok:
                print(f"[-] Input validation issues: {val_issues}")
                
            # Initialize PerformanceProfiler (Phase 1) and AdaptiveResourceManager (Phase 7)
            import json
            from src.core.optimization.performance_profiler import PerformanceProfiler
            from src.core.optimization.resource_manager import AdaptiveResourceManager
            
            self.profiler = PerformanceProfiler()
            self.profiler.start_timer("total")
            self.profiler.start_timer("decoding")
            
            resource_manager = AdaptiveResourceManager()
            self.last_hardware_profile = resource_manager.get_hardware_profile()
            
            self.profiler.stop_timer("decoding")

            # 3. GhostCut v5.0.1 Stable Cognitive Vision Flow
            from src.core.execution_context import ExecutionContext
            from src.core.image_profile import ImageProfile
            from src.core.consensus_engine import ConsensusEngine
            from src.core.strategy_engine import StrategyEngine
            
            # Validate registrations (Phase 3 exit check)
            self.registry.validate_registry()

            # Initialize shared ExecutionContext
            context = ExecutionContext(
                img_bgr=img_np_run,
                hardware={"providers": self.session.get_providers() if self.session else []}
            )

            # Execute scene runtime via unified execute API
            scene_runtime = self.registry.get_runtime("scene")()
            scene_result = scene_runtime.execute(context)
            
            # Extract scene details and store in context cache for compatibility
            scene_res = scene_runtime.observe(img_np_run)[0]
            scene_name = scene_res["scene"]
            metrics = scene_res["metrics"]
            context.cache["scene_metrics"] = metrics

            # Execute subject & background runtimes via unified execute API
            subject_runtime = self.registry.get_runtime("subject")()
            subject_result = subject_runtime.execute(context)
            subj_res = subject_runtime.observe(img_np_run, context=context)[0]

            bg_runtime = self.registry.get_runtime("background")()
            bg_result = bg_runtime.execute(context)
            bg_res = bg_runtime.observe(img_np_run, context=context)[0]

            # Resolve contradictions and compile beliefs
            consensus_engine = ConsensusEngine()
            consensus_res = consensus_engine.resolve_conflicts(context.evidence_graph, context.belief_graph)
            
            # Compile Strategy
            strategy_engine = StrategyEngine()
            strategy = strategy_engine.compile_strategy(context.belief_graph)
            
            # Compute topological plan & execution trace
            active_regions = None
            try:
                from src.core.perception.adaptive_policy_library import AdaptivePolicyLibrary
                pol_lib = AdaptivePolicyLibrary()
                policy_data = pol_lib.get_policy(scene_name)
                active_regions = policy_data.get("active_regions", ["skin", "hair"])
                # lowercase all region names
                active_regions = [r.lower() for r in active_regions]
            except Exception:
                pass

            plan_res = self.scheduler.get_execution_plan(scene_name, subj_res["subjects"], detected_regions=active_regions)
            self.last_pipeline_plan = plan_res
            
            # Store cognitive graph instances in SegmentationEngine
            self.last_evidence_graph = context.evidence_graph
            self.last_belief_graph = context.belief_graph
            self.last_strategy = strategy

            # Build ImageProfile
            profile = ImageProfile(
                scene=scene_name,
                subject=subj_res["subjects"],
                background=bg_res,
                confidence={"initial_segmentation": float(scene_res["confidence"]), "overall": 1.0}
            )
            context.profile = profile

            # Log consensus decisions
            for dec in consensus_res["decisions"]:
                logger.log("Consensus Engine", "Conflict Resolved", dec, f"Consensus: {consensus_res['consensus_score']*100:.1f}%")

            # Compile recipe via AdaptiveRecipeEngine or Strategy default
            from src.core.recipe_engine import AdaptiveRecipeEngine
            recipe_engine = AdaptiveRecipeEngine()
            
            # Seed AdaptiveRecipeEngine with user preferences, then override with Strategy values
            recipe = recipe_engine.compile_recipe(profile, user_prefs)
            
            # Override with Strategy Engine recommendations
            for k, v in strategy.params.items():
                setattr(recipe, k, v)
                logger.log("Strategy Engine", "Parameter Selection", f"{k} = {v}", "Strategy compiled recommendation")

            # Run Confidence Consistency Validator (Phase 6)
            from src.core.confidence_validator import ConfidenceValidator
            conf_validator = ConfidenceValidator()
            val_res = conf_validator.validate_beliefs(context.belief_graph, recipe)
            for warn in val_res["warnings"]:
                logger.log("Confidence Validator", "Assertion Warning", warn, "Consistency check failed")
            for corr in val_res["corrections"]:
                logger.log("Confidence Validator", "Correction Applied", corr, "Automatic resolution applied")

            # Run VEF v1.0 Evaluation (Phase 10 workflow)
            try:
                from src.core.vision_evaluation.evaluator import VisionEvaluator
                evaluator = VisionEvaluator()
                category_map = {
                    "Studio Portrait": "Portrait",
                    "Outdoor Portrait": "WetHair",
                    "Backlit Portrait": "Backlit",
                    "Pet": "Animal",
                    "Plant": "Plants",
                    "Food": "Food",
                    "Product": "Product"
                }
                vef_category = category_map.get(scene_name, "Product")
                self.last_vef_result = evaluator.evaluate_image("session_current", img_np_run, vef_category)
            except Exception as vef_err:
                print(f"[-] VEF evaluation failed: {vef_err}")
            # Run Autonomous Perception Orchestrator (APF v6.0 Phase 1)
            try:
                from src.core.perception.perception_orchestrator import PerceptionOrchestrator
                self.perception_orchestrator = PerceptionOrchestrator()
                orch_res = self.perception_orchestrator.orchestrate_perception(
                    img_np_run, scene_name, subj_res["subjects"], float(scene_res["confidence"])
                )
                self.last_perception_state = orch_res["state"]
                self.last_region_policies = orch_res["region_policies"]
                
                # Apply rules overrides
                if "Hair" in orch_res["region_policies"]:
                    recipe.preserve_transparency = True
                    recipe.erode_size = 1
            except Exception as apf_err:
                print(f"[-] APF Orchestration failed: {apf_err}")
                self.last_perception_state = None
                self.last_region_policies = None




            # Compute current image features
            current_features = extract_image_features(img_np_run)


            # Adaptive Learning: Recipe database matching & Ranking Engine
            try:
                from src.core.recipe_memory_runtime import RecipeMemoryRuntime
                from src.core.recipe_ranking_engine import RecipeRankingEngine
                from src.core.failure_memory_runtime import FailureMemoryRuntime
                from src.core.adaptive_policy_engine import AdaptivePolicyEngine

                db_path = get_db_path()
                memory_runtime = RecipeMemoryRuntime(db_path)
                similar_recipe_data = memory_runtime.find_similar_recipe(current_features)

                ranking_engine = RecipeRankingEngine()
                ranking_res = ranking_engine.rank_recipes(recipe, similar_recipe_data)
                recipe = ranking_res["best_recipe"]
                logger.log("Adaptive Learning", "Recipe Ranking Engine", ranking_res["best_recipe"].model_name, f"Confidence: {ranking_res['confidence']*100:.1f}%")

                # Proactive failure memory prevention
                failure_mem = FailureMemoryRuntime()
                fail_risk = failure_mem.predict_failure_risk(current_features)
                if fail_risk.get("risk_factors"):
                    logger.log("Adaptive Learning", "Failure Memory Prediction", f"Risks: {', '.join(fail_risk['risk_factors'])}", "Adjusting parameters based on failure memory")
                    for risk in fail_risk["risk_factors"]:
                        if risk == "halo":
                            recipe.erode_size = min(recipe.erode_size, 4)
                            recipe.sharpness = max(recipe.sharpness, 1)
                        elif risk == "color_spill":
                            recipe.decontaminate = True

                # Adaptive Policy overrides
                policy_engine = AdaptivePolicyEngine()
                policy_overrides = policy_engine.recommend_policy_overrides(profile)
                for k, v in policy_overrides.items():
                    setattr(recipe, k, v)
                    logger.log("Adaptive Learning", "Policy Engine Override", f"{k} = {v}", "Applying benchmark-derived rule overrides")
            except Exception as e:
                print(f"[-] Pre-inference adaptive learning fail: {e}")

            
            # Apply recipe attributes
            model_name = recipe.model_name
            processing_mode = recipe.processing_mode
            apply_matting = recipe.apply_matting
            erode_size = recipe.erode_size
            preserve_transparency = recipe.preserve_transparency
            sharpness = recipe.sharpness
            focus_thresh = recipe.focus_thresh
            decontaminate = recipe.decontaminate
            quality_loop = recipe.quality_loop
            radius_base = recipe.radius_base
            
            # Log recipe decisions
            for dec in recipe.decisions:
                logger.log("Recipe Compilation", "Decision", "Info", dec)
            logger.log("Engine Config", "model_name", model_name, "Selected segmentation model weights")
            logger.log("Engine Config", "processing_mode", processing_mode, "Execution scale setting")
            logger.log("Engine Config", "apply_matting", apply_matting, "Matting toggle status")
            logger.log("Engine Config", "erode_size", erode_size, "Base boundary zone radius")
            logger.log("Engine Config", "preserve_transparency", preserve_transparency, "Transparency preservation status")
            logger.log("Engine Config", "sharpness", sharpness, "Sigmoidal boost value")
            logger.log("Engine Config", "decontaminate", decontaminate, "Color spill decontamination status")
            logger.log("Engine Config", "quality_loop", quality_loop, "Confidence quality check status")
        else:
            model_name = self.current_model_name if self.current_model_name else "birefnet-general-lite"
            decontaminate = False
            quality_loop = False

        h, w, c = img_np_run.shape

        # Check cache for raw model mask to bypass heavy ONNX inference on parameter updates
        skip_onnx = False
        if file_path and hasattr(self, 'raw_masks_cache') and file_path in self.raw_masks_cache:
            cached_mask, cached_model = self.raw_masks_cache[file_path]
            if cached_model == model_name:
                mask = cached_mask.copy()
                skip_onnx = True
                logger.log("Engine Config", "BirefNet Cache Hit", "Loaded cached raw mask", f"File: {os.path.basename(file_path)}")

        if not skip_onnx:
            # Load selected model
            self.load_model(model_name)

            # Preprocessing: resize to model's expected size
            input_shape = self.session.get_inputs()[0].shape
            input_h = input_shape[2] if (len(input_shape) > 2 and isinstance(input_shape[2], int)) else 1024
            input_w = input_shape[3] if (len(input_shape) > 3 and isinstance(input_shape[3], int)) else 1024

            img_resized = cv2.resize(img_np_run, (input_w, input_h))
            img_rgb = cv2.cvtColor(img_resized, cv2.COLOR_BGR2RGB)

            # Normalization (ImageNet stats)
            mean = np.array([0.485, 0.456, 0.406], dtype=np.float32)
            std = np.array([0.229, 0.224, 0.225], dtype=np.float32)
            img_normalized = (img_rgb / 255.0 - mean) / std

            # BCHW format conversion
            img_input = img_normalized.transpose(2, 0, 1).astype(np.float32)
            img_input = np.expand_dims(img_input, axis=0)

            # Inference
            outputs = self.session.run([self.output_name], {self.input_name: img_input})
            pred = outputs[0]

            if pred.ndim == 4:
                pred_2d = pred[0, 0]
            elif pred.ndim == 3:
                pred_2d = pred[0]
            else:
                pred_2d = np.squeeze(pred)

            if pred_2d.min() < 0.0 or pred_2d.max() > 1.0:
                pred_sigmoid = 1.0 / (1.0 + np.exp(-np.clip(pred_2d, -12.0, 12.0)))
            else:
                pred_sigmoid = np.clip(pred_2d, 0.0, 1.0)

            mask_model = (pred_sigmoid * 255.0).astype(np.uint8)
            mask = cv2.resize(mask_model, (w, h), interpolation=cv2.INTER_LINEAR)

            # Cache the raw mask
            if file_path:
                if not hasattr(self, 'raw_masks_cache'):
                    self.raw_masks_cache = {}
                self.raw_masks_cache[file_path] = (mask.copy(), model_name)

        # Compute w_detail (detail density map)
        gray_guide = cv2.cvtColor(img_np_run, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        mean_I = cv2.boxFilter(gray_guide, -1, (7, 7))
        mean_I2 = cv2.boxFilter(gray_guide * gray_guide, -1, (7, 7))
        var_I = mean_I2 - mean_I * mean_I
        std_I = np.sqrt(np.maximum(var_I, 0.0))
        w_detail = np.clip((std_I - 0.02) / 0.06, 0.0, 1.0)

        # 4. Generate Material, Edge, and Confidence maps + Region Graph if running in adaptive mode
        if apply_matting and not disable_quality_loop:
            from src.core.region_graph import SubjectRegionGraph
            from src.core.regional_recipe import RegionalRecipeEngine
            
            # Fetch execution plan
            plan = self.last_pipeline_plan.get("plan", []) if self.last_pipeline_plan else []
            context = {}
            
            # Execute post-inference runtimes dynamically
            if "material" in plan:
                mat_runtime = self.registry.get_runtime("material")()
                mat_res = mat_runtime.analyze(img_np_run, mask, subjects=profile.subject)
                material_maps = mat_res["maps"]
                material_scores = mat_res["scores"]
                context["material"] = mat_res
            else:
                h_m, w_m = mask.shape[:2]
                material_maps = np.zeros((h_m, w_m, 12), dtype=np.float32)
                material_scores = {m: 0.0 for m in ["Skin", "Hair", "Fur", "Fabric", "Glass", "Plastic", "Metal", "Leather", "Lace", "Feather", "Water", "Smoke"]}
                
            dom_mat = max(material_scores, key=material_scores.get) if material_scores else "general"
            logger.log("Material Analysis", "Dominant Material", dom_mat, f"Confidence {material_scores.get(dom_mat, 0.0):.2f}")
            
            # Run v4.1 anatomical and geometric runtimes if scheduled
            if "face" in plan:
                face_runtime = self.registry.get_runtime("face")()
                face_res = face_runtime.analyze(img_np_run, mask)
                context["face"] = face_res
                logger.log("Vision Intelligence", "Face Detector", "Run", f"Detected Face: {face_res['has_face']} (Confidence {face_res['confidence']:.2f})")
                
            if "eye" in plan:
                eye_runtime = self.registry.get_runtime("eye")()
                eye_res = eye_runtime.analyze(img_np_run, mask, context=context)
                context["eye"] = eye_res
                logger.log("Vision Intelligence", "Eye Detector", "Run", f"Reflections: {eye_res['reflections']} | Glasses: {eye_res['glasses']}")
                
            if "clothing" in plan:
                clothing_runtime = self.registry.get_runtime("clothing")()
                clothing_res = clothing_runtime.analyze(img_np_run, mask)
                context["clothing"] = clothing_res
                logger.log("Vision Intelligence", "Clothing Analyzer", "Run", f"Fabric: {clothing_res['fabric_type']} | Mesh: {clothing_res['mesh']}")
                
            if "animal_anatomy" in plan:
                animal_anatomy_runtime = self.registry.get_runtime("animal_anatomy")()
                animal_anatomy_res = animal_anatomy_runtime.analyze(img_np_run, mask)
                context["animal_anatomy"] = animal_anatomy_res
                logger.log("Vision Intelligence", "Animal Anatomy Analyzer", "Run", f"Ears: {animal_anatomy_res['ears']} | Whiskers: {animal_anatomy_res['whiskers']}")
                
            if "plant" in plan:
                plant_runtime = self.registry.get_runtime("plant")()
                plant_res = plant_runtime.analyze(img_np_run, mask)
                context["plant"] = plant_res
                logger.log("Vision Intelligence", "Plant Structure Analyzer", "Run", f"Leaves: {plant_res['leaves']} | Stems: {plant_res['stems']}")
                
            if "product_geometry" in plan:
                product_geometry_runtime = self.registry.get_runtime("product_geometry")()
                product_geometry_res = product_geometry_runtime.analyze(img_np_run, mask)
                context["product_geometry"] = product_geometry_res
                logger.log("Vision Intelligence", "Product Geometry Analyzer", "Run", f"Straight Edges: {product_geometry_res['straight_edges']} | Reflective: {product_geometry_res['reflective_surfaces']}")

            hair_res = None
            if "hair" in plan:
                hair_runtime = self.registry.get_runtime("hair")()
                hair_res = hair_runtime.analyze(img_np_run, mask, metrics)
                context["hair"] = hair_res
                
            fur_res = None
            if "fur" in plan:
                fur_runtime = self.registry.get_runtime("fur")()
                fur_res = fur_runtime.analyze(img_np_run, mask, metrics)
                context["fur"] = fur_res
                
            if "edge" in plan:
                edge_runtime = self.registry.get_runtime("edge")()
                edge_res = edge_runtime.analyze(img_np_run, mask, material_maps)
                edge_map = edge_res["edge_map"]
                edge_classes = edge_res["classes"]
                context["edge"] = edge_res
            else:
                h_m, w_m = mask.shape[:2]
                edge_map = np.full((h_m, w_m), 1, dtype=np.int8)
                edge_classes = ["Soft"]
            
            # Construct raw ImageProfile with post-inference attributes
            profile.materials = material_scores
            
            # Update Hair/Fur details if they were computed
            if hair_res is not None:
                profile.hair_fur["has_hair"] = (material_scores.get("Hair", 0.0) > 0.1)
                profile.hair_fur["hair_type"] = hair_res["hair_type"]
                for k in ["length", "density", "curl_level_score", "strand_width", "flyaway_score", 
                          "transparency_score", "wetness", "frizz", "volume", "backlit_probability", "confidence"]:
                    profile.hair_fur[f"hair_{k}"] = hair_res[k]
                profile.lighting["backlit"] = hair_res["backlit"]
                
            if fur_res is not None:
                profile.hair_fur["has_fur"] = (material_scores.get("Fur", 0.0) > 0.1)
                profile.hair_fur["fur_type"] = fur_res["fur_type"]
                profile.hair_fur["whiskers"] = fur_res["whiskers"]
                for k in ["fur_length", "density", "fluffiness", "fur_whiskers", "undercoat", "transparency", "confidence"]:
                    profile.hair_fur[k if k.startswith("fur_") else f"fur_{k}"] = fur_res[k]
                
            profile.edge_types = edge_classes
            
            # Run Semantic Validation & Consistency checks (Phase 1 & 2)
            from src.core.semantic_validation_runtime import SemanticValidationRuntime
            semantic_val = SemanticValidationRuntime()
            profile = semantic_val.validate_profile(profile)
            
            # Sync material maps with validated scores
            for idx, mat in enumerate(["Skin", "Hair", "Fur", "Fabric", "Glass", "Plastic", "Metal", "Leather", "Lace", "Feather", "Water", "Smoke"]):
                if profile.materials.get(mat, 0.0) == 0.0:
                    material_maps[:, :, idx] = 0.0
            
            # Log rules fired
            for rule in profile.rules_fired:
                logger.log("Semantic Validation", "Rule Fired", rule, "Consistency engine validation enforced")
            for rej in profile.rejected_predictions:
                logger.log("Semantic Validation", "Rejected prediction", f"{rej['field']} = {rej['value']}", f"Reason: {rej['reason']}")
            
            # Run Confidence Fusion consensus engine (Phase 2 & 5)
            if "confidence_fusion" in plan:
                fusion_runtime = self.registry.get_runtime("confidence_fusion")()
                profile = fusion_runtime.fuse_confidences(profile, context)
                logger.log("Confidence Fusion", "Fused Hair Confidence", f"{profile.confidence.get('fused_hair', 0.0):.2f}", "Consensus calculated")
                logger.log("Confidence Fusion", "Fused Fur Confidence", f"{profile.confidence.get('fused_fur', 0.0):.2f}", "Consensus calculated")
                logger.log("Confidence Fusion", "Overall Pipeline Confidence", f"{profile.confidence.get('overall', 0.8):.2f}", "Consolidated consensus score")

            # Always calculate standard confidence maps first
            conf_engine = ConfidenceEngine()
            confidence_maps = conf_engine.generate_all_confidences(img_np_run, mask, material_maps, edge_map)

            # Construct VisionGraph hierarchy (v4.1 Phase 8)
            from src.core.vision_graph import VisionGraph
            v_graph_builder = VisionGraph()
            vision_graph_dict = v_graph_builder.build_graph(profile, context)
            self.last_vision_graph = vision_graph_dict

            # Construct Subject Region Graph v2
            region_graph_builder = SubjectRegionGraph()
            region_graph = region_graph_builder.build_graph(mask, material_maps, edge_map, confidence_maps)
            
            # Compile regional policies (with Recipe Engine v3 hierarchical inheritance overrides)
            reg_recipe_engine = RegionalRecipeEngine()
            regional_policies = reg_recipe_engine.compile_regional_policies(region_graph, recipe, vision_graph=self.last_vision_graph)
            
            # Expose to instance context
            self.last_profile = profile
            self.last_region_graph = region_graph

            
            # Construct regional parameter maps (Phase 7)
            h_m, w_m = img_np_run.shape[:2]
            bg_thresh_map = np.full((h_m, w_m), bg_thresh, dtype=np.float32)
            fg_thresh_map = np.full((h_m, w_m), fg_thresh, dtype=np.float32)
            erode_size_map = np.full((h_m, w_m), erode_size, dtype=np.float32)
            sharpness_map = np.full((h_m, w_m), sharpness, dtype=np.float32)
            preserve_transparency_map = np.full((h_m, w_m), float(preserve_transparency), dtype=np.float32)
            focus_thresh_map = np.full((h_m, w_m), focus_thresh, dtype=np.float32)
            
            labeled_regions = region_graph.get("labeled_regions")
            if labeled_regions is not None:
                labeled_regions_full = cv2.resize(labeled_regions, (w_m, h_m), interpolation=cv2.INTER_NEAREST)
                for r_id, pol in regional_policies.items():
                    mask_r = (labeled_regions_full == r_id)
                    if np.any(mask_r):
                        bg_thresh_map[mask_r] = pol.get("bg_thresh", bg_thresh)
                        fg_thresh_map[mask_r] = pol.get("fg_thresh", fg_thresh)
                        erode_size_map[mask_r] = pol.get("erode_size", erode_size)
                        sharpness_map[mask_r] = pol.get("sharpness", sharpness)
                        preserve_transparency_map[mask_r] = float(pol.get("preserve_transparency", preserve_transparency))
                        focus_thresh_map[mask_r] = pol.get("focus_thresh", focus_thresh)
            
            # Legacy fields for compatibility
            radius_gen = AdaptiveRadiusFieldGenerator()
            radius_field = radius_gen.generate_radius_field(mask, edge_map, material_maps, std_I)
        else:
            radius_field = None
            material_maps = None
            confidence_maps = None
            dom_mat = "general"
            self.last_profile = None
            self.last_region_graph = None


        if apply_matting:
            if hasattr(self, "profiler") and self.profiler is not None:
                self.profiler.start_timer("inference")
                self.profiler.start_timer("refinement")
            try:
                from src.core.alpha_engine.alpha_context import AlphaContext
                from src.core.alpha_engine.alpha_engine import AlphaEngine
                
                p_regions = self.last_perception_state.regions.keys() if (hasattr(self, "last_perception_state") and self.last_perception_state is not None) else ["skin", "hair"]
                
                a_context = AlphaContext(
                    img_bgr=img_np_run,
                    mask=mask,
                    perception_graph={"regions": list(p_regions)},
                    confidence_maps=confidence_maps if 'confidence_maps' in locals() else {},
                    quality_maps=self.last_quality_metrics if hasattr(self, "last_quality_metrics") else {}
                )
                
                # Attach session parameters to context for AIE execution
                a_context.fg_thresh = fg_thresh_map if not disable_quality_loop else fg_thresh
                a_context.bg_thresh = bg_thresh_map if not disable_quality_loop else bg_thresh
                a_context.erode_size = erode_size_map if not disable_quality_loop else erode_size
                a_context.preserve_transparency = preserve_transparency_map if not disable_quality_loop else preserve_transparency
                a_context.sharpness = sharpness_map if not disable_quality_loop else sharpness
                a_context.focus_thresh = focus_thresh_map if not disable_quality_loop else focus_thresh
                a_context.w_detail = w_detail
                a_context.disable_quality_loop = disable_quality_loop
                a_context.radius_field = radius_field
                a_context.material_maps = material_maps
                a_context.processing_mode = processing_mode
                
                self.alpha_engine = AlphaEngine()
                self.alpha_engine.matting_func = self.guided_filter_matting
                self.alpha_engine.vitmatte_func = self.run_vitmatte
                a_result = self.alpha_engine.execute(a_context)
                
                # Retrieve final unified alpha
                mask = a_result.alpha
                self.last_aie_result = a_result
                
            except Exception as aie_err:
                print(f"[-] AIE execute failed: {aie_err}. Falling back to legacy Guided Filter matting.")
                if processing_mode == "fast":
                    if not disable_quality_loop:
                        mask = self.guided_filter_matting(img_np_run, mask, fg_thresh_map, bg_thresh_map, erode_size_map, preserve_transparency_map, sharpness_map, focus_thresh_map, w_detail, disable_quality_loop, radius_field=radius_field, material_maps=material_maps)
                    else:
                        mask = self.guided_filter_matting(img_np_run, mask, fg_thresh, bg_thresh, erode_size, preserve_transparency, sharpness, focus_thresh, w_detail, disable_quality_loop, radius_field=radius_field, material_maps=material_maps)
                elif processing_mode in ["quality", "ultra"]:
                    try:
                        if processing_mode == "quality":
                            mask = self.run_vitmatte(img_np_run, mask, w_detail)
                        else:
                            mask_half = cv2.resize(mask, (w // 2, h // 2), interpolation=cv2.INTER_LINEAR)
                            img_half = cv2.resize(img_np_run, (w // 2, h // 2), interpolation=cv2.INTER_LINEAR)
                            w_detail_half = cv2.resize(w_detail, (w // 2, h // 2), interpolation=cv2.INTER_LINEAR)
                            
                            mask_1_0x = self.run_vitmatte(img_np_run, mask, w_detail).astype(np.float32) / 255.0
                            mask_0_5x = self.run_vitmatte(img_half, mask_half, w_detail_half)
                            mask_0_5x_upscaled = cv2.resize(mask_0_5x, (w, h), interpolation=cv2.INTER_LINEAR).astype(np.float32) / 255.0
                            
                            q_blend = 0.7 * mask_1_0x + 0.3 * mask_0_5x_upscaled
                            mask = (np.clip(q_blend, 0.0, 1.0) * 255.0).astype(np.uint8)
                        
                        if not disable_quality_loop:
                            mask = self.guided_filter_matting(img_np_run, mask, fg_thresh_map, bg_thresh_map, erode_size_map, preserve_transparency_map, sharpness_map, focus_thresh_map, w_detail, disable_quality_loop, radius_field=radius_field, material_maps=material_maps)
                        else:
                            mask = self.guided_filter_matting(img_np_run, mask, fg_thresh, bg_thresh, erode_size, preserve_transparency, sharpness, focus_thresh, w_detail, disable_quality_loop, radius_field=radius_field, material_maps=material_maps)
                    except Exception as e:
                        print(f"[-] ViTMatte error fallback: {e}.")
                        if not disable_quality_loop:
                            mask = self.guided_filter_matting(img_np_run, mask, fg_thresh_map, bg_thresh_map, erode_size_map, preserve_transparency_map, sharpness_map, focus_thresh_map, w_detail, disable_quality_loop, radius_field=radius_field, material_maps=material_maps)
                        else:
                            mask = self.guided_filter_matting(img_np_run, mask, fg_thresh, bg_thresh, erode_size, preserve_transparency, sharpness, focus_thresh, w_detail, disable_quality_loop, radius_field=radius_field, material_maps=material_maps)
            finally:
                if hasattr(self, "profiler") and self.profiler is not None:
                    self.profiler.stop_timer("inference")
                    self.profiler.stop_timer("refinement")



        # 5. GhostCut v4.2 Quality Intelligence Evaluation & Repair Layer
        if apply_matting and not disable_quality_loop:
            try:
                # Lazy load quality runtimes
                from src.core.edge_quality_runtime import EdgeQualityRuntime
                from src.core.alpha_quality_runtime import AlphaQualityRuntime
                from src.core.mask_stability_runtime import MaskStabilityRuntime
                from src.core.halo_spill_runtime import HaloSpillRuntime
                from src.core.transparency_quality_runtime import TransparencyQualityRuntime
                from src.core.region_consistency_runtime import RegionConsistencyRuntime
                from src.core.failure_prediction_runtime import FailurePredictionRuntime
                from src.core.confidence_heatmap_runtime import ConfidenceHeatmapRuntime
                                # 1. Setup ExecutionContext for v8.5 Quality pipeline
                from src.core.execution_context import ExecutionContext
                q_context = ExecutionContext(img_bgr=img_np_run)
                q_context.belief_graph = self.last_belief_graph
                q_context.cache["alpha"] = mask.copy()
                q_context.cache["material_maps"] = material_maps

                # 2. Execute v8.5 Analyzers in sequence
                hair_morph_runtime = self.registry.get_runtime("hair_morphology")()
                hair_morph_runtime.execute(q_context)

                edge_intel_runtime = self.registry.get_runtime("edge_intelligence")()
                edge_intel_runtime.execute(q_context)

                mat_boundary_runtime = self.registry.get_runtime("material_boundary")()
                mat_boundary_runtime.execute(q_context)

                halo_detect_runtime = self.registry.get_runtime("halo_detection")()
                halo_detect_runtime.execute(q_context)

                # 3. Quality Intelligence fusion
                quality_intel_runtime = self.registry.get_runtime("quality_intelligence")()
                quality_intel_runtime.execute(q_context)

                # 4. Local Repair scheduler execution (if quality loop enabled)
                if quality_loop:
                    local_repair_runtime = self.registry.get_runtime("local_repair")()
                    local_repair_runtime.execute(q_context)

                # 5. Extract output and log details
                mask = q_context.cache.get("alpha", mask)
                repair_log = q_context.cache.get("repair_records", [])
                self.last_repair_log = repair_log

                q_report = q_context.cache.get("quality_report", {})
                overall_score = q_report.get("overall_score", 0.95)
                halo_score = q_report.get("halo_score", 0.95)
                edge_score = q_report.get("edge_score", 0.95)
                hair_score = q_report.get("hair_score", 0.95)

                self.last_quality_metrics = {
                    "edge_score": edge_score,
                    "alpha_score": overall_score,
                    "stability_score": 0.95,
                    "halo_spill_score": halo_score,
                    "transparency_score": hair_score,
                    "consistency_score": 0.95,
                    "failure_score": 0.95,
                    "failure_grade": "A" if overall_score > 0.85 else "B" if overall_score > 0.70 else "C",
                    "overall_score": overall_score
                }
                self.last_quality_heatmap = np.zeros_like(mask)

                # Log quality metrics
                logger.log("Quality Intelligence", "Estimated Quality Grade", self.last_quality_metrics["failure_grade"], f"Score: {overall_score*100:.1f}%")
                logger.log("Quality Intelligence", "Edge Quality Score", f"{edge_score*100:.1f}%", "Jaggedness and leakage check")
                logger.log("Quality Intelligence", "Alpha Quality Score", f"{overall_score*100:.1f}%", "Matte transitions check")
                logger.log("Quality Intelligence", "Halo & Spill Severity Score", f"{halo_score*100:.1f}%", "Chromatic background bleed check")

                # Log local repairs
                if repair_log and quality_loop:
                    logger.log("Local Repair Scheduler", "Defects Found", len(repair_log), "Scheduling localized crops for targeted repair")
                    for r_log in repair_log:
                        logger.log("Local Repair Scheduler", f"Crop {r_log['index']} ({r_log['strategy']})", r_log['outcome'], f"Bounds: {r_log['bbox']}")

                # 4. GhostCut v5.0 Self-Critic Engine
                from src.core.self_critic_engine import SelfCriticEngine
                self_critic = SelfCriticEngine()
                critic_res = self_critic.criticize(mask, self.last_quality_metrics, belief_graph=self.last_belief_graph.get_root_belief())
                self.last_self_critic_report = critic_res
                
                # Log Self-Critic decisions
                logger.log("Self-Critic Engine", "Final Quality Grade", critic_res["quality_grade"], f"Critic Score: {critic_res['overall_score']*100:.1f}%")
                for fail in critic_res["failures"]:
                    logger.log("Self-Critic Engine", "Defect Warning", fail, "Targeted repair prioritizations applied")

                # Compile APF v6.0 Local Repair Plan (Phase 4)
                try:
                    if hasattr(self, "last_perception_state") and self.last_perception_state is not None:
                        repair_plan = self.perception_orchestrator.repair_planner.formulate_repair_plan(
                            self.last_perception_state, critic_res
                        )
                        self.last_repair_plan = repair_plan
                        for step in repair_plan:
                            logger.log("APF Repair Planner", f"Targeted Repair [{step['region']}]", step['operation'], f"Priority: {step['priority']}")
                    else:
                        self.last_repair_plan = []
                except Exception as repair_err:
                    print(f"[-] APF Repair planning failed: {repair_err}")
                    self.last_repair_plan = []



                # 4. Confidence Calibration (v4.3 Phase 5)
                from src.core.confidence_calibration_runtime import ConfidenceCalibrationRuntime
                calibrator = ConfidenceCalibrationRuntime()
                profile.confidence["fused_hair"] = calibrator.calibrate(profile.confidence.get("fused_hair", 0.8), "hair", context)
                profile.confidence["fused_fur"] = calibrator.calibrate(profile.confidence.get("fused_fur", 0.8), "fur", context)
                profile.confidence["overall"] = calibrator.calibrate(profile.confidence.get("overall", 0.8), "initial_segmentation", context)

                # 5. Adaptive Learning Update (v4.3 post-inference log)
                try:
                    from src.core.recipe_memory_runtime import RecipeMemoryRuntime
                    from src.core.failure_memory_runtime import FailureMemoryRuntime
                    from src.core.benchmark_intelligence import BenchmarkIntelligenceRuntime
                    
                    outcome_data = {
                        "params": {
                            "model_name": model_name,
                            "processing_mode": processing_mode,
                            "erode_size": erode_size,
                            "bg_thresh": bg_thresh,
                            "fg_thresh": fg_thresh,
                            "focus_thresh": focus_thresh,
                            "sharpness": sharpness,
                            "apply_matting": apply_matting,
                            "preserve_transparency": preserve_transparency,
                            "decontaminate": decontaminate,
                            "quality_loop": quality_loop
                        },
                        "rating": 1,
                        "overall_score": self.last_quality_metrics.get("overall_score", 0.95),
                        "cpu_time_ms": 150.0,
                        "peak_memory_mb": 35.0
                    }
                    
                    input_data = {
                        "file_path": file_path if file_path else "unknown_image.jpg",
                        "features": current_features
                    }
                    db_path = get_db_path()
                    RecipeMemoryRuntime(db_path).learn(input_data, outcome_data)
                    
                    if self.last_quality_metrics.get("overall_score", 1.0) < 0.85:
                        input_fail = {
                            "features": current_features,
                            "defects": {
                                "edge_defect": 1.0 - self.last_quality_metrics.get("edge_score", 1.0),
                                "alpha_defect": 1.0 - self.last_quality_metrics.get("alpha_score", 1.0),
                                "stability_defect": 1.0 - self.last_quality_metrics.get("stability_score", 1.0),
                                "halo_defect": 1.0 - self.last_quality_metrics.get("halo_spill_score", 1.0),
                            }
                        }
                        outcome_fail = {
                            "strategy": "local_refine"
                        }
                        FailureMemoryRuntime().learn(input_fail, outcome_fail)
                    
                    BenchmarkIntelligenceRuntime().learn({"version": "v4.3"}, outcome_data)
                    logger.log("Adaptive Learning", "Memory Logged", "SUCCESS", f"Execution parameters and score {outcome_data['overall_score']*100:.1f}% archived offline")
                except Exception as e:
                    print(f"[-] Adaptive Learning post-inference update fail: {e}")

            except Exception as e:
                print(f"[-] Quality Intelligence evaluation/repair error: {e}")



        # Upscale mask back to original resolution if it was downscaled
        if scale_factor != 1.0:
            mask = cv2.resize(mask, (orig_w, orig_h), interpolation=cv2.INTER_LINEAR)

        # Morphological Connected Components speckles cleanup (removes floating mask dust)
        try:
            num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats((mask > 15).astype(np.uint8))
            min_size = max(50, int(orig_h * orig_w * 0.00002))
            for i in range(1, num_labels):
                if stats[i, cv2.CC_STAT_AREA] < min_size:
                    mask[labels == i] = 0
        except Exception as speckle_err:
            print(f"[-] Speckle cleanup failed: {speckle_err}")

        # Stop total timer and save production telemetry (Phase 11)
        if hasattr(self, "profiler") and self.profiler is not None:
            self.profiler.stop_timer("total")
            self.last_performance_metrics = self.profiler.export_metrics()
            
            try:
                telemetry_path = os.path.join(os.path.dirname(__file__), "optimization", "production_telemetry.json")
                os.makedirs(os.path.dirname(telemetry_path), exist_ok=True)
                history_data = []
                if os.path.exists(telemetry_path):
                    with open(telemetry_path, "r") as f:
                        history_data = json.load(f)
                history_data.append(self.last_performance_metrics)
                with open(telemetry_path, "w") as f:
                    json.dump(history_data, f, indent=4)
            except Exception as tel_err:
                print(f"[-] Telemetry saving failed: {tel_err}")

        return mask

    def guided_filter_matting(self, img, mask, fg_thresh, bg_thresh, erode_size, preserve_transparency=False, sharpness=0, focus_thresh=0.0, w_detail=None, disable_quality_loop=False, radius_field=None, material_maps=None):
        """
        Applies a 3-channel color guided filter on the mask using the original image in LAB color space as guide.
        Supports variable/adaptive radius fields and material-based alpha policies, and regional parameter maps.
        """
        from src.core.manual_refine import color_guided_filter
        
        # Compute resolution scale factor based on diagonal relative to 1200px
        h, w = img.shape[:2]
        diagonal = np.sqrt(h**2 + w**2)
        scale_factor = max(1.0, diagonal / 1200.0)
        
        # Apply pre-matting focus guided suppression
        mask_suppressed = apply_conditional_distance_focus_suppression(img, mask, mask, focus_thresh=focus_thresh)
        
        # Pre-process mask with a fast bilateral filter to remove interpolation/resize noise while keeping edges sharp
        mask_clean = cv2.bilateralFilter(mask_suppressed, 5, 50, 50)
        
        # Convert BGR to LAB to separate structure (luminance) from color (chrominance)
        img_lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
        
        # Apply unsharp masking to luminance (L) channel to enhance guide gradients for fine matting
        L = img_lab[:, :, 0].astype(np.float32)
        L_blur = cv2.GaussianBlur(L, (3, 3), 0.5)
        L_sharp = cv2.addWeighted(L, 1.5, L_blur, -0.5, 0)
        img_lab[:, :, 0] = np.clip(L_sharp, 0, 255).astype(np.uint8)
        
        I = img_lab.astype(np.float32) / 255.0
        
        # Always calculate std_I for pixel-level edge complexity classification
        gray_guide = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        mean_I = cv2.boxFilter(gray_guide, -1, (7, 7))
        mean_I2 = cv2.boxFilter(gray_guide * gray_guide, -1, (7, 7))
        var_I = mean_I2 - mean_I * mean_I
        std_I = np.sqrt(np.maximum(var_I, 0.0))
        
        if w_detail is None:
            w_detail = np.clip((std_I - 0.02) / 0.06, 0.0, 1.0)

        # --- Automatic Interior Hole Matting Detection ---
        if not disable_quality_loop:
            bg_pixels = img[mask_clean < 5]
            if len(bg_pixels) > 100:
                bg_mean = np.mean(bg_pixels, axis=0)
                bg_std = np.std(bg_pixels, axis=0)
                bg_std = np.maximum(bg_std, 3.0)
                dist_bg = np.sqrt(np.sum(((img - bg_mean) / bg_std) ** 2, axis=2))
                interior_gaps = (dist_bg < 3.5) & (mask_clean > 50) & (w_detail > 0.15)
                mask_clean = mask_clean.copy()
                mask_clean[interior_gaps] = 128
        
        # Modulate detail weight using transition density in raw mask
        is_pres_trans = False
        if isinstance(preserve_transparency, np.ndarray):
            w_density = 1.0 - preserve_transparency
            is_pres_trans = np.any(preserve_transparency > 0.5)
        else:
            is_pres_trans = preserve_transparency
            if preserve_transparency:
                w_density = np.ones_like(mask_clean, dtype=np.float32)
            else:
                max_erode = float(np.max(erode_size)) if isinstance(erode_size, np.ndarray) else float(erode_size)
                k_size = max(21, int(max_erode * 3 * scale_factor + 1))
                kernel_edge = cv2.getStructuringElement(cv2.MORPH_RECT, (k_size, k_size))
                dilated_mask = cv2.dilate(mask_clean, kernel_edge)
                eroded_mask = cv2.erode(mask_clean, kernel_edge)
                transition_zone = ((dilated_mask > 0) & (eroded_mask < 255)).astype(np.float32)
                density_transition = cv2.boxFilter(transition_zone, -1, (25, 25))
                w_density = np.clip(density_transition * 2.0, 0.0, 1.0)
            
        w_detail_modulated = w_detail * w_density
        
        # Dynamic propagation parameters scaling based on image size/resolution
        max_erode = float(np.max(erode_size)) if isinstance(erode_size, np.ndarray) else float(erode_size)
        max_dist = max(3, int(max_erode * 2 * scale_factor))
        max_iter = max(2, int(round(max_dist / 2.0)))
        
        # Geodesic detail-guided propagation to recover thin flyaways
        details_mask = (w_detail_modulated > 0.15).astype(np.uint8)
        binary_mask = (mask_clean > 80).astype(np.uint8)
        dist_outside = cv2.distanceTransform(1 - binary_mask, cv2.DIST_L2, 3)
        
        # Dynamically scale max_dist based on hair probability to allow long stray hairs to propagate
        base_dist = float(max_dist)
        if material_maps is not None:
            hair_prob = material_maps[:, :, 1]
            max_dist_map = base_dist * (1.0 - hair_prob) + np.maximum(20.0, base_dist * 4.0) * hair_prob
        else:
            max_dist_map = np.full_like(mask_clean, base_dist, dtype=np.float32)
        
        mask_propagated = mask_clean.copy()
        kernel = np.ones((3, 3), np.uint8)
        for _ in range(max_iter * 2):  # Allow more propagation iterations to capture long stray hairs
            dilated = cv2.dilate(mask_propagated, kernel)
            mask_propagated = np.where((details_mask > 0) & (dist_outside < max_dist_map), dilated, mask_propagated)
        mask_propagated = cv2.GaussianBlur(mask_propagated, (3, 3), 0.5)
        
        # Construct mask_input using 128 (0.5) neutral prior in the propagated zone
        mask_input = mask_clean.copy()
        propagated_zone = (mask_propagated > 5) & (mask_clean < 50)
        mask_input[propagated_zone] = 128
        
        mask_clean_modulated = (w_detail_modulated * mask_input + (1.0 - w_detail_modulated) * mask_clean).astype(np.uint8)
        
        # Update w_detail_new to flag propagated regions as details
        has_propagated = ((mask_propagated > 5) & (mask_clean < 5)).astype(np.float32)
        w_detail_new = np.maximum(w_detail_modulated, has_propagated * w_detail)
        
        if not is_pres_trans:
            max_erode = float(np.max(erode_size)) if isinstance(erode_size, np.ndarray) else float(erode_size)
            if max_erode >= 3:
                w_detail_new = np.maximum(w_detail_new, 0.30 * w_density)
        
        # Apply distance-based decay to detail weights in outer background region to prevent ghost halos
        decay_factor = np.clip((max_dist_map * 1.5 - dist_outside) / np.maximum(5.0, max_dist_map * 0.8), 0.0, 1.0)
        w_detail_new = w_detail_new * decay_factor
        
        p = mask_clean_modulated.astype(np.float32) / 255.0
        
        # Detail-adaptive guided filter radius blending
        if is_pres_trans or disable_quality_loop or radius_field is None:
            base_erode = float(np.mean(erode_size)) if isinstance(erode_size, np.ndarray) else float(erode_size)
            r_small = max(5, int((base_erode + 2) * scale_factor))
            r_large = max(17, int((base_erode * 3 + 5) * scale_factor))
            q_small = color_guided_filter(I, p, r_small, eps=1e-5)
            q_large = color_guided_filter(I, p, r_large, eps=1e-5)
            q = w_detail_new * q_large + (1.0 - w_detail_new) * q_small
        else:
            # Multi-type pixel-level edge blending driven by ADAPTIVE RADIUS FIELD
            r_hard = max(2, int(2 * scale_factor))
            r_soft = max(6, int(6 * scale_factor))
            r_detail = max(15, int(15 * scale_factor))
            
            q_hard = color_guided_filter(I, p, r_hard, eps=1e-6)
            q_soft = color_guided_filter(I, p, r_soft, eps=1e-5)
            q_detail = color_guided_filter(I, p, r_detail, eps=1e-5)
            
            # Map local radius field values to weights
            w_hard = np.clip((6.0 - radius_field) / 4.0, 0.0, 1.0)
            w_detail_field = np.clip((radius_field - 6.0) / 6.0, 0.0, 1.0)
            w_soft = np.clip(1.0 - w_hard - w_detail_field, 0.0, 1.0)
            
            q = w_hard * q_hard + w_soft * q_soft + w_detail_field * q_detail
            
            # Apply material-based alpha policies
            if material_maps is not None:
                skin_prob = material_maps[:, :, 0]
                
                # Skin: contrast boost
                if np.any(skin_prob > 0.05):
                    q_skin = 1.0 / (1.0 + np.exp(-12.0 * (q - 0.5)))
                    q = skin_prob * q_skin + (1.0 - skin_prob) * q
        
        # Clamp background alpha noise in outer background regions unless active hair strand is present
        hair_prob = material_maps[:, :, 1] if material_maps is not None else None
        is_hair_strand = (hair_prob > 0.25) if hair_prob is not None else (w_detail_new > 0.30)
        
        # Suppress alpha noise in background areas without active hair texture
        no_hair_bg = (mask_clean < 20) & (~is_hair_strand)
        q = np.where(no_hair_bg & (q < 0.20), 0.0, q)
        
        # Apply sharpness control (sigmoidal/contrast enhancement)
        k = 1.0 + sharpness * 0.9
        v_min = 1.0 / (1.0 + np.exp(0.5 * k))
        v_max = 1.0 / (1.0 + np.exp(-0.5 * k))
        q_sig = 1.0 / (1.0 + np.exp(-k * (q - 0.5)))
        q = (q_sig - v_min) / (v_max - v_min)
            
        q = np.clip(q, 0.0, 1.0)
        
        # Apply definite boundaries
        bg_val_local = bg_thresh / 255.0
        fg_val_local = fg_thresh / 255.0
        
        # In solid/non-detail regions (low w_detail_new), contract thresholds to sharpen the boundaries and prevent blurry halos
        bg_val_local = bg_val_local * w_detail_new + 0.45 * (1.0 - w_detail_new)
        fg_val_local = fg_val_local * w_detail_new + 0.55 * (1.0 - w_detail_new)
        
        denom = fg_val_local - bg_val_local
        denom = np.where(np.abs(denom) < 1e-5, 1e-5, denom)
        
        u = (q - bg_val_local) / denom
        u = np.clip(u, 0.0, 1.0)
        q_smooth = 3.0 * (u ** 2) - 2.0 * (u ** 3)
        
        if isinstance(preserve_transparency, np.ndarray):
            opacity_weight = 1.0 - preserve_transparency
            q = opacity_weight * q_smooth + (1.0 - opacity_weight) * q
            q_final = q
        elif not preserve_transparency:
            # Blend based on detail probability
            q_final = w_detail_new * q + (1.0 - w_detail_new) * q_smooth
        else:
            q_final = q
            
        # --- SUBPIXEL FLYAWAY & MULTI-MATERIAL ENGINE (v9.1.0) ---
        skin_prob = material_maps[:, :, 0] if (material_maps is not None and material_maps.shape[2] >= 1) else np.zeros_like(q)
        hair_prob = material_maps[:, :, 1] if (material_maps is not None and material_maps.shape[2] >= 2) else np.zeros_like(q)
        fabric_prob = material_maps[:, :, 2] if (material_maps is not None and material_maps.shape[2] >= 3) else np.zeros_like(q)
        
        # 1. Structure Tensor Directional Coherence for Subpixel 1-Pixel Flyaway Protection
        gray_img = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        gx = cv2.Sobel(gray_img, cv2.CV_32F, 1, 0, ksize=3)
        gy = cv2.Sobel(gray_img, cv2.CV_32F, 0, 1, ksize=3)
        
        Jxx = cv2.boxFilter(gx * gx, -1, (5, 5))
        Jyy = cv2.boxFilter(gy * gy, -1, (5, 5))
        Jxy = cv2.boxFilter(gx * gy, -1, (5, 5))
        
        denom_tensor = Jxx + Jyy + 1e-6
        C_dir = np.sqrt(np.maximum(0.0, (Jxx - Jyy) ** 2 + 4.0 * (Jxy ** 2))) / denom_tensor
        
        # Protect fine 1-pixel flyaway strands (alpha in [0.04, 0.15] with strong directional coherence C_dir > 0.40)
        is_flyaway_strand = (q >= 0.04) & (q < 0.15) & (C_dir > 0.40) & (hair_prob > 0.03)
        
        # STREAM A: DEEP-SEMANTIC SOLID ENGINE (Clothes, Sweater, Skin, Arms, Accessories)
        p_raw = mask.astype(np.float32) / 255.0
        mask_hard_binary = (p_raw >= 0.48).astype(np.float32)
        edge_1px = cv2.Canny((mask_hard_binary * 255).astype(np.uint8), 100, 200) > 0
        mask_hard_aa = cv2.GaussianBlur(mask_hard_binary, (3, 3), 0.5)
        stream_a_hard = np.where(edge_1px, mask_hard_aa, mask_hard_binary)
        
        # STREAM B: DYNAMIC HAIR & TRANSLUCENT DETAIL STREAM (Hair Volume & Curls)
        img_float = img.astype(np.float32)
        bg_mask_ref = (mask_clean < 10).astype(np.float32)
        
        if np.sum(bg_mask_ref) > 100:
            bg_pixels = img_float[mask_clean < 10]
            sigma_bg = float(np.mean(np.std(bg_pixels, axis=0)))
            thresh_hole = max(18.0, min(35.0, 2.5 * sigma_bg))
            
            bg_weight = cv2.boxFilter(bg_mask_ref[:, :, np.newaxis], -1, (65, 65)) + 1e-5
            B_field = cv2.boxFilter(img_float * bg_mask_ref[:, :, np.newaxis], -1, (65, 65)) / bg_weight
            local_bg_dist = np.sqrt(np.sum((img_float - B_field) ** 2, axis=2))
            
            interior_bg_hole = (local_bg_dist < thresh_hole) & (mask_clean < 220)
            
            # Dynamic alpha unmixing
            alpha_unmix = np.clip((local_bg_dist - (thresh_hole * 0.6)) / (thresh_hole * 1.5), 0.0, 1.0)
            q_hair_clamped = np.where(~interior_bg_hole, q * alpha_unmix, 0.0)
            q_hair_clamped = np.where((~is_flyaway_strand) & (q_hair_clamped < 0.12), 0.0, q_hair_clamped)
        else:
            q_hair_clamped = np.where((~is_flyaway_strand) & (q < 0.12), 0.0, q)
            
        # 2. Continuous Multi-Material Junction Softening
        w_hair_blend = np.clip((hair_prob - 0.05) / 0.20, 0.0, 1.0)
        q_final = (1.0 - w_hair_blend) * stream_a_hard + w_hair_blend * q_hair_clamped
        
        # Re-inject protected subpixel flyaways
        q_final = np.where(is_flyaway_strand, np.maximum(q_final, q), q_final)
        q_final = np.clip(q_final, 0.0, 1.0)
            
        final_mask = (q_final * 255.0).astype(np.uint8)
            
        # Apply post-matting focus suppression to clean up propagation bleed
        final_mask = apply_conditional_distance_focus_suppression(img, final_mask, mask, focus_thresh=focus_thresh)
        return final_mask


def generate_trimap(mask, w_detail, img=None):
    """
    Generates an adaptive trimap where high-detail hair/fur regions have a wider
    unknown zone, and solid boundaries have a narrower unknown zone.
    Detects interior background-like color patches and marks them as unknown transition zone.
    """
    h, w = mask.shape
    if w_detail.shape != (h, w):
        w_detail = cv2.resize(w_detail, (w, h), interpolation=cv2.INTER_LINEAR)
        
    binary_fg = (mask > 150).astype(np.uint8)
    binary_bg = (mask <= 30).astype(np.uint8)
    
    dist_fg = cv2.distanceTransform(binary_fg, cv2.DIST_L2, 5)
    dist_bg = cv2.distanceTransform(binary_bg, cv2.DIST_L2, 5)
    
    # Adaptive threshold boundary sizes: solid = 3px, high detail = 25px
    thresh_fg = 3.0 + 22.0 * w_detail
    thresh_bg = 3.0 + 22.0 * w_detail
    
    trimap = np.full((h, w), 128, dtype=np.uint8)
    trimap[(mask > 150) & (dist_fg >= thresh_fg)] = 255
    trimap[(mask <= 30) & (dist_bg >= thresh_bg)] = 0
    
    # Automate interior background holes detection in hair/detail regions
    if img is not None:
        bg_pixels = img[mask < 5]
        if len(bg_pixels) > 100:
            bg_mean = np.mean(bg_pixels, axis=0)
            bg_std = np.std(bg_pixels, axis=0)
            bg_std = np.maximum(bg_std, 3.0)
            
            # Compute distance to background color
            dist_bg = np.sqrt(np.sum(((img - bg_mean) / bg_std) ** 2, axis=2))
            
            # Identify background-like pixels inside the foreground mask in high-detail hair areas
            bg_like_mask = (dist_bg < 3.5) & (mask > 50) & (w_detail > 0.15)
            
            # Mark them as unknown (128) in the trimap so the matting model will refine them
            trimap[bg_like_mask] = 128
            
    return trimap


def compute_hair_confidence(img, mask, w_detail):
    """
    Computes a map indicating confidence of hair/fur presence based on high-frequency
    textures and proximity to the segmentation boundary.
    """
    h, w = mask.shape
    if w_detail.shape != (h, w):
        w_detail = cv2.resize(w_detail, (w, h), interpolation=cv2.INTER_LINEAR)
        
    is_transition = ((mask > 10) & (mask < 245)).astype(np.float32)
    dist_transition = cv2.distanceTransform((1.0 - is_transition).astype(np.uint8), cv2.DIST_L2, 3)
    
    # Proximity weight: high within 30 pixels of the segmentation transition border
    weight_proximity = np.clip((30.0 - dist_transition) / 30.0, 0.0, 1.0)
    
    # Hair confidence blends texture detail and proximity
    hair_conf = np.clip(w_detail * weight_proximity * 1.5, 0.0, 1.0)
    return hair_conf


def apply_conditional_distance_focus_suppression(img, mask, raw_mask, focus_thresh=6.0, dist_max=40.0, dist_min=10.0):
    if isinstance(focus_thresh, np.ndarray):
        if np.max(focus_thresh) <= 0:
            return mask
    else:
        if focus_thresh <= 0:
            return mask
            
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)
    laplacian = np.abs(cv2.Laplacian(gray, cv2.CV_32F))
    focus_energy = cv2.boxFilter(laplacian, -1, (15, 15))
    
    binary_mask = (raw_mask > 80).astype(np.uint8)
    dist = cv2.distanceTransform(binary_mask, cv2.DIST_L2, 3)
    
    denom = np.maximum(focus_thresh, 1e-5)
    suppression = np.clip(focus_energy / denom, 0.0, 1.0)
    weight_dist = np.clip((dist_max - dist) / (dist_max - dist_min), 0.0, 1.0)
    weight_conf = np.clip((252.0 - raw_mask.astype(np.float32)) / 7.0, 0.0, 1.0)
    weight = weight_dist * weight_conf
    
    mask_float = mask.astype(np.float32)
    suppressed_vals = mask_float * suppression
    output_mask = (1.0 - weight) * mask_float + weight * suppressed_vals
    return np.clip(output_mask, 0, 255).astype(np.uint8)



def decontaminate_colors(img, mask, fg_thresh=None, hair_conf=None):
    """
    Removes background color bleed from transition boundaries using true
    foreground color estimation and detail-modulated blending.
    """
    if img is None or mask is None:
        return img
        
    h, w = img.shape[:2]
    
    # 1. Locate the active transition zone spatially (within 20px inside or 12px outside the mask edge)
    binary_fg = (mask > 10).astype(np.uint8)
    dist_inside = cv2.distanceTransform(binary_fg, cv2.DIST_L2, 3)
    dist_outside = cv2.distanceTransform(1 - binary_fg, cv2.DIST_L2, 3)
    
    # Boundary zone is within 20px inside or 12px outside the mask edge
    transition_mask = (((dist_inside > 0) & (dist_inside <= 20)) | 
                       ((dist_outside > 0) & (dist_outside <= 12))).astype(np.uint8)
    
    coords = np.argwhere(transition_mask > 0)
    if coords.size == 0:
        return img.copy() # No decontamination needed if no transition pixels exist
        
    # Crop bounding box with propagation padding
    y1, x1 = coords.min(axis=0)
    y2, x2 = coords.max(axis=0)
    
    pad = 40
    y1 = max(0, y1 - pad)
    x1 = max(0, x1 - pad)
    y2 = min(h, y2 + pad)
    x2 = min(w, x2 + pad)
    
    img_crop = img[y1:y2, x1:x2]
    mask_crop = mask[y1:y2, x1:x2]
    h_c, w_c = img_crop.shape[:2]
    
    max_decon_dim = 2048
    should_scale = max(h_c, w_c) > max_decon_dim
    if should_scale:
        scale = max_decon_dim / float(max(h_c, w_c))
        new_h = int(round(h_c * scale))
        new_w = int(round(w_c * scale))
        img_crop_orig = img_crop
        img_crop = cv2.resize(img_crop, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        mask_crop_orig = mask_crop
        mask_crop = cv2.resize(mask_crop, (new_w, new_h), interpolation=cv2.INTER_LINEAR)
        
    alpha = mask_crop.astype(np.float32) / 255.0
    alpha_3d = np.expand_dims(alpha, axis=2)
    
    # 2. Compute hair confidence on the cropped region
    if hair_conf is None:
        gray = cv2.cvtColor(img_crop, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        mean_I = cv2.boxFilter(gray, -1, (7, 7))
        mean_I2 = cv2.boxFilter(gray * gray, -1, (7, 7))
        var_I = mean_I2 - mean_I * mean_I
        std_I = np.sqrt(np.maximum(var_I, 0.0))
        w_detail = np.clip((std_I - 0.02) / 0.06, 0.0, 1.0)
        hair_conf_crop = compute_hair_confidence(img_crop, mask_crop, w_detail)
    else:
        hair_conf_crop = hair_conf[y1:y2, x1:x2]
        
    hair_conf_3d = np.expand_dims(hair_conf_crop, axis=2)
    
    # 3. Propagate background color to estimate local Background B
    bg_weights = (mask_crop <= 15).astype(np.float32)
    bg_weights_3d = np.expand_dims(bg_weights, axis=2)
    bg_color = img_crop.astype(np.float32) * bg_weights_3d
    
    accum_bg = bg_color.copy()
    accum_bg_weight = bg_weights_3d.copy()
    
    # Multi-scale propagation kernels up to 63 for high-resolution studio lighting bleed removal
    kernels = [3, 7, 15, 31, 63]
    
    for ksize in kernels:
        if ksize >= min(h_c, w_c):
            break
        blurred_color = cv2.boxFilter(accum_bg, -1, (ksize, ksize), borderType=cv2.BORDER_REPLICATE)
        blurred_weight = cv2.boxFilter(accum_bg_weight, -1, (ksize, ksize), borderType=cv2.BORDER_REPLICATE)
        
        if len(blurred_weight.shape) == 2:
            blurred_weight = np.expand_dims(blurred_weight, axis=2)
            
        blurred_weight_safe = np.where(blurred_weight < 1e-5, 1.0, blurred_weight)
        normalized_bg = blurred_color / blurred_weight_safe
        normalized_bg[blurred_weight[:, :, 0] < 1e-5] = 0
        
        blend_factor = 1.0 - accum_bg_weight
        accum_bg = accum_bg + blend_factor * normalized_bg
        accum_bg_weight = accum_bg_weight + blend_factor * (blurred_weight > 1e-5).astype(np.float32)
        
    B = np.clip(accum_bg, 0.0, 255.0)
    
    # 4. Propagate foreground colors as F_prior
    if fg_thresh is None:
        max_val = np.max(mask_crop)
        fg_thresh = max(200, int(max_val - 5)) if max_val > 200 else 200
        
    fg_weights = (mask_crop >= fg_thresh).astype(np.float32)
    fg_weights = cv2.erode(fg_weights, np.ones((3, 3), np.uint8))
    fg_weights_3d = np.expand_dims(fg_weights, axis=2)
    fg_color = img_crop.astype(np.float32) * fg_weights_3d
    
    accum_fg = fg_color.copy()
    accum_fg_weight = fg_weights_3d.copy()
    
    for ksize in kernels:
        if ksize >= min(h_c, w_c):
            break
        blurred_color = cv2.boxFilter(accum_fg, -1, (ksize, ksize), borderType=cv2.BORDER_REPLICATE)
        blurred_weight = cv2.boxFilter(accum_fg_weight, -1, (ksize, ksize), borderType=cv2.BORDER_REPLICATE)
        
        if len(blurred_weight.shape) == 2:
            blurred_weight = np.expand_dims(blurred_weight, axis=2)
            
        blurred_weight_safe = np.where(blurred_weight < 1e-5, 1.0, blurred_weight)
        normalized_fg = blurred_color / blurred_weight_safe
        normalized_fg[blurred_weight[:, :, 0] < 1e-5] = 0
        
        blend_factor = 1.0 - accum_fg_weight
        accum_fg = accum_fg + blend_factor * normalized_fg
        accum_fg_weight = accum_fg_weight + blend_factor * (blurred_weight > 1e-5).astype(np.float32)
        
    F_prior = np.clip(accum_fg, 0.0, 255.0)
    
    # 5. Mathematically recover Foreground (F = (Observed - B*(1-alpha)) / alpha)
    alpha_safe = np.maximum(alpha_3d, 0.05)
    F_recovered = (img_crop.astype(np.float32) - B * (1.0 - alpha_3d)) / alpha_safe
    F_recovered = np.clip(F_recovered, 0.0, 255.0)
    
    # 6. Blend recovered and prior foreground: favor prior at low alpha or if recovered is too close to background
    d = np.linalg.norm(F_recovered - B, axis=2)
    d_3d = np.expand_dims(d, axis=2)
    
    # Trust recovered color only if it differs significantly from local background color
    w_trust_recovered = np.clip((d_3d - 30.0) / 40.0, 0.0, 1.0)
    
    blend_alpha = np.clip((alpha_3d - 0.05) / 0.20, 0.0, 1.0)
    final_blend_alpha = blend_alpha * w_trust_recovered
    
    F_estimate = final_blend_alpha * F_recovered + (1.0 - final_blend_alpha) * F_prior
    
    # 7. Apply decontamination: modulate strength by hair confidence map or background brightness status
    bg_brightness = np.mean(B, axis=2)
    is_bright_bg = (bg_brightness > 200.0).astype(np.float32)
    is_bright_bg_3d = np.expand_dims(is_bright_bg, axis=2)
    
    # Scale baseline decontamination based on background brightness (higher brightness = stronger decontamination)
    baseline_decon = np.clip((bg_brightness - 80.0) / 120.0, 0.10, 0.90)
    baseline_decon_3d = np.expand_dims(baseline_decon, axis=2)
    
    w_decon = np.maximum(hair_conf_3d * 0.95 + (1.0 - hair_conf_3d) * baseline_decon_3d, is_bright_bg_3d * 0.95)
    decon_crop = (w_decon * F_estimate + (1.0 - w_decon) * img_crop.astype(np.float32)).astype(np.uint8)

    
    if should_scale:
        diff_small = decon_crop.astype(np.float32) - img_crop.astype(np.float32)
        diff_upscaled = cv2.resize(diff_small, (w_c, h_c), interpolation=cv2.INTER_LINEAR)
        decon_crop = np.clip(img_crop_orig.astype(np.float32) + diff_upscaled, 0.0, 255.0).astype(np.uint8)
        
    # 8. Re-paste the decontaminated patch into the full-size image
    decontaminated = img.copy()
    decontaminated[y1:y2, x1:x2] = decon_crop
    return decontaminated


def extract_image_features(img_bgr, mask=None):
    """
    Extracts key image features for parameters recommendation.
    If mask is not provided, uses a default center mask.
    """
    h, w = img_bgr.shape[:2]
    small = cv2.resize(img_bgr, (256, 256))
    
    mean_color = cv2.mean(small)[:3]
    std_color = np.std(small, axis=(0, 1))
    
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    laplacian_var = cv2.Laplacian(gray, cv2.CV_64F).var()
    
    # 1. Edge density (Canny edge pixels ratio)
    edges = cv2.Canny(gray, 50, 150)
    edge_density = float(cv2.countNonZero(edges)) / edges.size
    
    # 2. Texture entropy
    hist = cv2.calcHist([gray], [0], None, [256], [0, 256])
    hist = hist / hist.sum()
    entropy = -float(np.sum(hist * np.log2(hist + 1e-7)))
    
    # 3. Dynamic range (95th - 5th percentile)
    gray_flat = gray.flatten()
    p95, p5 = np.percentile(gray_flat, [95, 5])
    dynamic_range = float(p95 - p5)
    
    # 4. Noise estimation (residual after small Gaussian blur)
    blur_small = cv2.GaussianBlur(gray, (3, 3), 0.5)
    noise_est = float(np.std(gray.astype(np.float32) - blur_small.astype(np.float32)))
    
    # 5. Motion blur (gradient ratio stability)
    sobelx = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
    var_x = np.var(sobelx)
    var_y = np.var(sobely)
    grad_ratio = float(min(var_x, var_y) / (max(var_x, var_y) + 1e-5))
    
    # 6. Color temperature (simplified R-B balance estimate)
    color_temp = float(mean_color[2] - mean_color[0])
    
    # 7. Lighting direction & Shadow estimation (percentage of dark pixels)
    gray_norm = gray.astype(np.float32) / 255.0
    shadow_est = float(np.mean(gray_norm < 0.15))
    
    light_dx = float(np.mean(sobelx))
    light_dy = float(np.mean(sobely))
    
    # 8. Background and subject checks
    if mask is None:
        border_mask = np.ones((256, 256), dtype=np.uint8)
        border_mask[25:231, 25:231] = 0
        subject_occupancy = 0.5
        subject_scale = 1.0
    else:
        mask_small = cv2.resize(mask, (256, 256))
        border_mask = (mask_small < 50).astype(np.uint8)
        if cv2.countNonZero(border_mask) == 0:
            border_mask = np.ones((256, 256), dtype=np.uint8)
            border_mask[25:231, 25:231] = 0
            
        fg_pixels = np.count_nonzero(mask_small > 100)
        subject_occupancy = float(fg_pixels) / mask_small.size
        
        # Calculate subject scale based on bounding box
        ys, xs = np.where(mask_small > 100)
        if len(ys) > 0 and len(xs) > 0:
            bbox_h = float(ys.max() - ys.min()) / 256.0
            bbox_w = float(xs.max() - xs.min()) / 256.0
            subject_scale = float(bbox_h * bbox_w)
        else:
            subject_scale = 0.0
            
    bg_pixels = small[border_mask > 0]
    bg_var = np.var(bg_pixels) if len(bg_pixels) > 0 else 0.0
    bg_mean = np.mean(bg_pixels) if len(bg_pixels) > 0 else 128.0
    
    # Dominant background color (mean BGR of background pixels)
    if len(bg_pixels) > 0:
        bg_dom_color = [float(c) for c in np.mean(bg_pixels, axis=0)]
    else:
        bg_dom_color = [128.0, 128.0, 128.0]
        
    features = {
        "aspect_ratio": float(w) / h,
        "mean_b": float(mean_color[0]),
        "mean_g": float(mean_color[1]),
        "mean_r": float(mean_color[2]),
        "std_b": float(std_color[0]),
        "std_g": float(std_color[1]),
        "std_r": float(std_color[2]),
        "laplacian_var": float(laplacian_var),
        "bg_var": float(bg_var),
        "bg_mean": float(bg_mean),
        # New Expanded Features
        "edge_density": edge_density,
        "texture_entropy": entropy,
        "dynamic_range": dynamic_range,
        "noise_est": noise_est,
        "grad_ratio": grad_ratio,
        "color_temp": color_temp,
        "shadow_est": shadow_est,
        "light_dx": light_dx,
        "light_dy": light_dy,
        "subject_occupancy": subject_occupancy,
        "subject_scale": subject_scale,
        "bg_dom_b": bg_dom_color[0],
        "bg_dom_g": bg_dom_color[1],
        "bg_dom_r": bg_dom_color[2]
    }
    return features


def recommend_parameters(new_features, db_path):
    """
    Queries learning_db.json using a hybrid RAG + OKF (Retrieval-Augmented Parameter Selection
    with Agentic Knowledge Format overrides) engine. Retrieves the top-k similar templates,
    performs similarity-weighted parameter fusion, and applies heuristic safety rules.
    """
    if not db_path or not os.path.exists(db_path):
        return None
        
    import json
    try:
        with open(db_path, 'r') as f:
            records = json.load(f)
    except Exception as e:
        print(f"Error loading recommendation DB: {e}")
        return None
        
    good_records = [r for r in records if r.get("rating") == 1]
    if not good_records:
        return None
        
    scalers = {
        "aspect_ratio": 1.0,
        "mean_b": 255.0,
        "mean_g": 255.0,
        "mean_r": 255.0,
        "std_b": 100.0,
        "std_g": 100.0,
        "std_r": 100.0,
        "laplacian_var": 5000.0,
        "bg_var": 5000.0,
        "bg_mean": 255.0
    }
    
    # 1. RAG Retrieval: Retrieve top-k nearest neighbor templates
    scored_records = []
    for rec in good_records:
        rec_feat = rec.get("features", {})
        dist = 0.0
        for k, scale in scalers.items():
            v1 = new_features.get(k, 0.0)
            v2 = rec_feat.get(k, 0.0)
            dist += ((v1 - v2) / scale) ** 2
        scored_records.append((dist, rec))
        
    scored_records.sort(key=lambda x: x[0])
    
    # Select top k=3 templates
    k = min(3, len(scored_records))
    top_k = scored_records[:k]
    
    # Calculate similarity weights (inverse distance with small epsilon)
    weights = []
    for dist, rec in top_k:
        weight = 1.0 / (dist + 1e-5)
        weights.append(weight)
        
    sum_weights = sum(weights)
    if sum_weights < 1e-8:
        weights = [1.0] * k
        sum_weights = float(k)
        
    # 2. Parameter Fusion (Interpolation & weighted voting)
    fused_params = {}
    model_votes = {}
    mode_votes = {}
    
    num_fields = ["erode_size", "bg_thresh", "fg_thresh", "focus_thresh", "sharpness"]
    num_accum = {f: 0.0 for f in num_fields}
    
    bool_fields = ["apply_matting", "preserve_transparency", "decontaminate"]
    bool_accum = {f: 0.0 for f in bool_fields}
    
    for i, (dist, rec) in enumerate(top_k):
        params = rec.get("params", {})
        w = weights[i] / sum_weights
        
        # Categorical majority voting
        m_name = params.get("model_name", "birefnet-general")
        model_votes[m_name] = model_votes.get(m_name, 0.0) + w
        
        p_mode = params.get("processing_mode", "fast")
        mode_votes[p_mode] = mode_votes.get(p_mode, 0.0) + w
        
        # Numeric weighted interpolation
        for f in num_fields:
            num_accum[f] += float(params.get(f, 0.0)) * w
            
        # Boolean weighted vote accumulation
        for f in bool_fields:
            if params.get(f, False):
                bool_accum[f] += w
                
    fused_params["model_name"] = max(model_votes, key=model_votes.get)
    fused_params["processing_mode"] = max(mode_votes, key=mode_votes.get)
    
    for f in num_fields:
        val = num_accum[f]
        if f in ["erode_size", "bg_thresh", "fg_thresh", "sharpness"]:
            fused_params[f] = int(round(val))
        else:
            fused_params[f] = float(val)
            
    for f in bool_fields:
        fused_params[f] = (bool_accum[f] >= 0.5)
        
    # 3. Agentic Knowledge Formats (OKF) Safety Guards & Rules Overrides
    new_lap_var = new_features.get("laplacian_var", 0.0)
    new_bg_var = new_features.get("bg_var", 0.0)
    
    # Rule 1: High texture details (curly hair, lace detail)
    if new_lap_var > 900.0:
        fused_params["apply_matting"] = True
        fused_params["erode_size"] = min(fused_params["erode_size"], 5)
        fused_params["decontaminate"] = True
        
    # Rule 2: Cluttered background details
    if new_bg_var > 450.0:
        fused_params["bg_thresh"] = max(fused_params["bg_thresh"], 40)
        fused_params["focus_thresh"] = max(fused_params["focus_thresh"], 3.0)
        
    # Rule 3: Semi-transparent glass objects
    if bool_accum["preserve_transparency"] > 0.3:
        fused_params["preserve_transparency"] = True
        
    return fused_params


def get_db_path():
    """
    Returns the persistent database path in Local AppData to avoid permission errors.
    """
    appdata = os.environ.get("LOCALAPPDATA", os.path.expanduser("~"))
    db_dir = os.path.join(appdata, "GhostCutOffline")
    os.makedirs(db_dir, exist_ok=True)
    return os.path.join(db_dir, "learning_db.json")
