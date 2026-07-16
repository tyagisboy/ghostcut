import numpy as np
from src.core.base_runtime import BaseRuntime
from src.core.image_profile import ImageProfile

class ConfidenceFusionRuntime(BaseRuntime):
    """
    Confidence Fusion Engine combining confidence signals from multiple runtimes
    to resolve inconsistencies and produce a unified overall confidence.
    """
    def __init__(self):
        pass

    def get_metadata(self) -> dict:
        return {
            "id": "confidence_fusion",
            "name": "Confidence Fusion Engine",
            "dependencies": ["material", "edge", "hair", "fur"],
            "execution_cost": 0.5,
            "quality_impact": 8.0,
            "requires_mask": True
        }


    def analyze(self, img_bgr: np.ndarray, mask: np.ndarray = None, context: dict = None) -> dict:
        """
        No-op during pipeline execution, as fusion is applied directly on the profile.
        """
        return {}

    def fuse_confidences(self, profile: ImageProfile, context: dict = None) -> ImageProfile:
        """
        Applies weighted consensus algorithms across raw indicators to update profile confidence.
        """
        subjects = profile.subject
        has_human = "Human" in subjects or profile.scene in ["Studio Portrait", "Outdoor Portrait", "Backlit Portrait"]
        has_animal = "Animal" in subjects or profile.scene in ["Pet"]

        # 1. Hair Confidence Fusion
        if has_human:
            hair_mat_score = profile.materials.get("Hair", 0.0)
            hair_score = profile.hair_fur.get("hair_confidence", 0.0)
            human_conf = profile.confidence.get("Human", 0.8) if isinstance(profile.confidence, dict) else 0.8
            # Weighted average
            fused_hair_conf = 0.5 * hair_mat_score + 0.4 * hair_score + 0.1 * human_conf
            fused_hair_conf = float(np.clip(fused_hair_conf, 0.0, 1.0))
        else:
            fused_hair_conf = 0.0

        # 2. Fur Confidence Fusion
        if has_animal:
            fur_mat_score = profile.materials.get("Fur", 0.0)
            fur_score = profile.hair_fur.get("fur_confidence", 0.0)
            animal_conf = profile.confidence.get("Animal", 0.8) if isinstance(profile.confidence, dict) else 0.8
            fused_fur_conf = 0.5 * fur_mat_score + 0.4 * fur_score + 0.1 * animal_conf
            fused_fur_conf = float(np.clip(fused_fur_conf, 0.0, 1.0))
        else:
            fused_fur_conf = 0.0

        # 3. Transparency Confidence Fusion
        glass_score = profile.materials.get("Glass", 0.0)
        plastic_score = profile.materials.get("Plastic", 0.0)
        trans_score = profile.materials.get("Lace", 0.0) * 0.5 + profile.materials.get("Feather", 0.0) * 0.5
        fused_trans_conf = float(np.clip(max(glass_score, plastic_score, trans_score), 0.0, 1.0))

        # Update profile properties
        profile.hair_fur["hair_confidence"] = fused_hair_conf
        profile.hair_fur["fur_confidence"] = fused_fur_conf
        profile.hair_fur["transparency_confidence"] = fused_trans_conf

        # 4. Overall Pipeline Confidence
        base_seg_conf = profile.confidence.get("initial_segmentation", 0.8) if isinstance(profile.confidence, dict) else 0.8
        
        # Adjust overall based on background complexity & contradictions
        bg_complexity = profile.background.get("complexity", "low")
        bg_penalty = 0.0
        if bg_complexity == "high":
            bg_penalty = 0.15
        elif bg_complexity == "medium":
            bg_penalty = 0.05
            
        overall = base_seg_conf - bg_penalty
        if hasattr(profile, "rejected_predictions") and len(profile.rejected_predictions) > 0:
            # Penalty for semantic conflicts resolved
            overall -= 0.05 * len(profile.rejected_predictions)
            
        overall_conf = float(np.clip(overall, 0.3, 0.99))
        
        # Save fused metrics in profile confidence dictionary
        if not isinstance(profile.confidence, dict):
            profile.confidence = {}
        profile.confidence["fused_hair"] = fused_hair_conf
        profile.confidence["fused_fur"] = fused_fur_conf
        profile.confidence["fused_transparency"] = fused_trans_conf
        profile.confidence["overall"] = overall_conf

        return profile
