import os
import onnxruntime as ort
from src.core.recipe import ProcessingRecipe
from src.core.policies import POLICIES

class AdaptiveRecipeEngine:
    """
    Adaptive Recipe Engine (v2) compiling ImageProfiles and HardwareProfiles
    into execution ProcessingRecipe settings.
    """
    def __init__(self):
        pass

    def detect_hardware_profile(self):
        providers = ort.get_available_providers()
        cuda = "CUDAExecutionProvider" in providers
        dml = "DirectMLExecutionProvider" in providers
        return {
            "gpu_accelerated": cuda or dml,
            "gpu_provider": "CUDA" if cuda else ("DirectML" if dml else "None"),
            "system_cpu_threads": os.cpu_count() or 4
        }

    def compile_recipe(self, profile, user_prefs=None):
        """
        Compiles an initial recipe using ImageProfile attributes and hardware flags.
        """
        decisions = []
        hw = self.detect_hardware_profile()
        gpu_avail = hw["gpu_accelerated"]
        
        decisions.append(f"Hardware Profile: GPU acceleration available={gpu_avail} via {hw['gpu_provider']}")
        
        # 1. Base recipe policies from scene
        scene = profile.scene
        # Map scene categories to presets
        policy_key = "Product"
        if scene == "Studio Portrait":
            policy_key = "Studio Portrait"
        elif scene == "Outdoor Portrait":
            policy_key = "Outdoor Portrait"
        elif scene == "Pet":
            policy_key = "Pet"
        elif "Vehicle" in scene:
            policy_key = "Vehicle"
        
        policy = POLICIES["scenarios"].get(policy_key, POLICIES["scenarios"]["Product"]).copy()
        decisions.append(f"Pre-Inference Scenario: '{scene}' detected")
        decisions.append(f"Retrieved Scenario Policy: '{policy_key}' preset loaded")
        
        # Apply hardware optimization
        policy["use_gpu"] = gpu_avail
        if not gpu_avail:
            # CPU limits
            if policy["model_name"] == "birefnet-general":
                policy["model_name"] = "birefnet-general-lite"
                decisions.append("CPU Safety Override: Swapped model to 'birefnet-general-lite' to optimize runtime")
            if policy["processing_mode"] == "ultra":
                policy["processing_mode"] = "quality"
                decisions.append("CPU Safety Override: Downgraded processing mode to 'quality'")
                
        # 2. Refine recipe using material attributes
        mats = profile.materials
        if mats.get("Glass", 0.0) > 0.15:
            policy["preserve_transparency"] = True
            policy["processing_mode"] = "quality"
            decisions.append("Glass Override: Transparency preservation activated")
            
        if profile.lighting.get("backlit", False):
            policy["decontaminate"] = True
            policy["erode_size"] = max(policy["erode_size"], 4)
            decisions.append("Backlit Override: Activated color decontamination")
            
        # Incorporate user preference overrides
        if user_prefs is not None:
            for key, val in user_prefs.items():
                if val is not None:
                    policy[key] = val
            decisions.append("User preference overrides applied")
            
        return ProcessingRecipe(policy, decisions)
