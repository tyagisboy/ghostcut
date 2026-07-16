import os
import onnxruntime as ort
from src.core.policies import POLICIES
from src.core.scenario import classify_scenario

class ProcessingRecipe:
    """
    Data structure representing the compiled execution plan for background removal.
    """
    def __init__(self, settings_dict, decisions=None):
        self.model_name = settings_dict.get("model_name", "birefnet-general-lite")
        self.processing_mode = settings_dict.get("processing_mode", "fast")
        self.apply_matting = settings_dict.get("apply_matting", True)
        self.erode_size = settings_dict.get("erode_size", 3)
        self.preserve_transparency = settings_dict.get("preserve_transparency", False)
        self.sharpness = settings_dict.get("sharpness", 0)
        self.focus_thresh = settings_dict.get("focus_thresh", 0.0)
        self.decontaminate = settings_dict.get("decontaminate", True)
        self.quality_loop = settings_dict.get("quality_loop", True)
        self.multi_scale = settings_dict.get("multi_scale", False)
        self.radius_base = settings_dict.get("radius_base", 4.0)
        self.use_gpu = settings_dict.get("use_gpu", False)
        self.export_profile = settings_dict.get("export_profile", "PNG-8bit")
        
        self.decisions = decisions if decisions is not None else []

    def to_dict(self):
        return {
            "model_name": self.model_name,
            "processing_mode": self.processing_mode,
            "apply_matting": self.apply_matting,
            "erode_size": self.erode_size,
            "preserve_transparency": self.preserve_transparency,
            "sharpness": self.sharpness,
            "focus_thresh": self.focus_thresh,
            "decontaminate": self.decontaminate,
            "quality_loop": self.quality_loop,
            "multi_scale": self.multi_scale,
            "radius_base": self.radius_base,
            "use_gpu": self.use_gpu,
            "export_profile": self.export_profile
        }


class RecipeEngine:
    """
    Compiles hardware capabilities, scenario classification, and image profiles
    into a custom ProcessingRecipe before full-scale AI models are executed.
    """
    def __init__(self):
        pass

    def detect_hardware_profile(self):
        """
        Queries ONNX Runtime execution providers to find available hardware acceleration.
        """
        providers = ort.get_available_providers()
        cuda = "CUDAExecutionProvider" in providers
        dml = "DirectMLExecutionProvider" in providers
        
        profile = {
            "gpu_accelerated": cuda or dml,
            "gpu_provider": "CUDA" if cuda else ("DirectML" if dml else "None"),
            "system_cpu_threads": os.cpu_count() or 4
        }
        return profile

    def generate_recipe(self, img_bgr=None, user_prefs=None, scenario_override=None, metrics_override=None):
        """
        Performs pre-inference scenario classification and hardware checks
        to compile a custom ProcessingRecipe.
        """
        decisions = []
        
        # 1. Analyze hardware
        hw = self.detect_hardware_profile()
        gpu_avail = hw["gpu_accelerated"]
        provider = hw["gpu_provider"]
        decisions.append(f"Hardware Profile: GPU acceleration available={gpu_avail} via {provider}")
        
        # 2. Get Scenario & Metrics
        if scenario_override is not None:
            scenario = scenario_override
            scenario_conf = 1.0
            metrics = metrics_override if metrics_override is not None else {
                "aspect_ratio": 1.0,
                "laplacian_var": 1000.0,
                "mean_sat": 50.0,
                "skin_ratio": 0.0,
                "specular_ratio": 0.0,
                "backlit_ratio": 1.0,
                "bg_brightness": 128.0,
                "fg_brightness": 128.0
            }
            decisions.append(f"Synthetic Mock Profile loaded: '{scenario}'")
        else:
            if img_bgr is None:
                raise ValueError("Either img_bgr or scenario_override must be provided")
            scenario, scenario_conf, metrics = classify_scenario(img_bgr)
            decisions.append(f"Pre-Inference Scenario: '{scenario}' detected (confidence={scenario_conf:.2f})")
        
        # 3. Retrieve policy settings for this scenario
        policy = POLICIES["scenarios"].get(scenario, POLICIES["scenarios"]["Product"]).copy()
        decisions.append(f"Retrieved Scenario Policy: '{scenario}' preset settings loaded")
        
        # 4. Integrate User Preferences
        if user_prefs is not None:
            # Overwrite policy with user preferences if specified
            for key, val in user_prefs.items():
                if val is not None:
                    policy[key] = val
            decisions.append("Integrated user preference overrides")
            
        # 5. Adapt recipe based on hardware constraints (CPU-first vs GPU-first)
        # If running on CPU, we prioritize fast or quality processing over ultra, and lite models over heavy models
        policy["use_gpu"] = gpu_avail
        if not gpu_avail:
            # Optimize for CPU
            if policy["model_name"] == "birefnet-general" and scenario in ["Product", "Clothing", "Food", "Vehicle"]:
                policy["model_name"] = "birefnet-general-lite"
                decisions.append("CPU Safety Override: Swapped model to 'birefnet-general-lite' to optimize CPU runtime")
            if policy["processing_mode"] == "ultra":
                policy["processing_mode"] = "quality"
                decisions.append("CPU Safety Override: Downgraded processing mode to 'quality' (avoiding dual-scale ultra mode)")
        else:
            # GPU is available - we can enable higher quality settings safely
            if policy["processing_mode"] == "fast" and scenario in ["Studio Portrait", "Backlit Portrait", "Pet"]:
                policy["processing_mode"] = "quality"
                decisions.append("GPU Boost: Upgraded processing mode to 'quality' due to GPU presence")
                
        # 6. Edge cases and specific rules
        # High background complexity (if backlit or dynamic range is high) -> ensure general model and matting is active
        if metrics["backlit_ratio"] > 1.3:
            policy["decontaminate"] = True
            policy["erode_size"] = max(policy["erode_size"], 4)
            decisions.append("Backlit Override: Activated color decontamination and expanded matting edge zone")
            
        # Glass / Transparency preservation
        if scenario == "Transparent Object":
            policy["preserve_transparency"] = True
            policy["processing_mode"] = "quality"
            decisions.append("Glass Override: Transparency preservation activated")
            
        # Compile recipe
        recipe = ProcessingRecipe(policy, decisions)
        return recipe
