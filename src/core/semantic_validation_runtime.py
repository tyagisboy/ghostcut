import copy
from src.core.image_profile import ImageProfile, ValidatedImageProfile

class SemanticValidationRuntime:
    """
    Validates ImageProfile predictions post-inference to enforce semantic consistency.
    Removes impossible prediction combinations and resolves conflicts before matting.
    """
    def __init__(self):
        pass

    def validate_profile(self, profile: ImageProfile) -> ValidatedImageProfile:
        """
        Applies consistency rules on ImageProfile, returning a ValidatedImageProfile.
        """
        raw_dict = copy.deepcopy(profile.to_dict())
        rules_fired = []
        rejected_predictions = []

        subjects = profile.subject
        scene = profile.scene

        # Help with list containment
        has_human = "Human" in subjects or "Studio Portrait" in scene or "Outdoor Portrait" in scene
        has_animal = "Animal" in subjects or "Pet" in scene
        has_plant = "Plant" in subjects or "Plant" in scene
        has_product = "Product" in subjects or "Product" in scene or "Vehicle" in scene or "Food" in scene or "Jewelry" in scene or "Clothing" in scene

        # Rule 1: Human -> Fur = False (unless Animal is also present in mixed context)
        if has_human and not has_animal:
            # Check for fur properties
            has_fur = profile.hair_fur.get("has_fur", False)
            fur_type = profile.hair_fur.get("fur_type", "none")
            fur_prob = profile.materials.get("Fur", 0.0)
            whiskers = profile.hair_fur.get("whiskers", False) or profile.hair_fur.get("fur_whiskers", False)

            if has_fur or fur_type != "none" or fur_prob > 0.0 or whiskers:
                rules_fired.append("Human -> Fur=False")
                
                if has_fur:
                    rejected_predictions.append({"field": "hair_fur.has_fur", "value": has_fur, "reason": "Subject is Human (no Animal)"})
                    profile.hair_fur["has_fur"] = False
                    
                if fur_type != "none":
                    rejected_predictions.append({"field": "hair_fur.fur_type", "value": fur_type, "reason": "Subject is Human (no Animal)"})
                    profile.hair_fur["fur_type"] = "none"
                    
                if fur_prob > 0.0:
                    rejected_predictions.append({"field": "materials.Fur", "value": fur_prob, "reason": "Subject is Human (no Animal)"})
                    profile.materials["Fur"] = 0.0
                    
                if profile.hair_fur.get("whiskers", False):
                    rejected_predictions.append({"field": "hair_fur.whiskers", "value": True, "reason": "Subject is Human (no Animal)"})
                    profile.hair_fur["whiskers"] = False
                    
                if profile.hair_fur.get("fur_whiskers", False):
                    rejected_predictions.append({"field": "hair_fur.fur_whiskers", "value": True, "reason": "Subject is Human (no Animal)"})
                    profile.hair_fur["fur_whiskers"] = False

                # Zero out fur estimators
                profile.hair_fur["fur_density"] = 0.0
                profile.hair_fur["fur_fluffiness"] = 0.0
                profile.hair_fur["fur_undercoat"] = 0.0
                profile.hair_fur["fur_transparency"] = 0.0
                profile.hair_fur["fur_confidence"] = 0.0

        # Rule 2: Plant -> Skin = False (unless Human is also present in mixed context)
        if has_plant and not has_human:
            skin_prob = profile.materials.get("Skin", 0.0)
            if skin_prob > 0.0:
                rules_fired.append("Plant -> Skin=False")
                rejected_predictions.append({"field": "materials.Skin", "value": skin_prob, "reason": "Subject is Plant (no Human)"})
                profile.materials["Skin"] = 0.0

        # Rule 3: Product -> Hair = False (unless Human or Animal is also present)
        if has_product and not (has_human or has_animal):
            has_hair = profile.hair_fur.get("has_hair", False)
            hair_type = profile.hair_fur.get("hair_type", "general")
            hair_prob = profile.materials.get("Hair", 0.0)

            if has_hair or hair_type != "general" or hair_prob > 0.0:
                rules_fired.append("Product -> Hair=False")
                
                if has_hair:
                    rejected_predictions.append({"field": "hair_fur.has_hair", "value": has_hair, "reason": "Subject is Product (no Human/Animal)"})
                    profile.hair_fur["has_hair"] = False
                    
                if hair_type != "general":
                    rejected_predictions.append({"field": "hair_fur.hair_type", "value": hair_type, "reason": "Subject is Product (no Human/Animal)"})
                    profile.hair_fur["hair_type"] = "general"
                    
                if hair_prob > 0.0:
                    rejected_predictions.append({"field": "materials.Hair", "value": hair_prob, "reason": "Subject is Product (no Human/Animal)"})
                    profile.materials["Hair"] = 0.0

                # Zero out hair estimators
                profile.hair_fur["hair_density"] = 0.0
                profile.hair_fur["hair_curl_level"] = 0.0
                profile.hair_fur["hair_flyaway_score"] = 0.0
                profile.hair_fur["hair_transparency_score"] = 0.0
                profile.hair_fur["hair_wetness"] = 0.0
                profile.hair_fur["hair_frizz"] = 0.0
                profile.hair_fur["hair_volume"] = 0.0
                profile.hair_fur["hair_backlit_probability"] = 0.0
                profile.hair_fur["hair_confidence"] = 0.0

        # Rule 4: Cactus/Plant -> Whisker = False (unless Animal is also present)
        if has_plant and not has_animal:
            whiskers = profile.hair_fur.get("whiskers", False) or profile.hair_fur.get("fur_whiskers", False)
            if whiskers:
                rules_fired.append("Cactus/Plant -> Whisker=False")
                
                if profile.hair_fur.get("whiskers", False):
                    rejected_predictions.append({"field": "hair_fur.whiskers", "value": True, "reason": "Subject is Plant/Cactus (no Animal)"})
                    profile.hair_fur["whiskers"] = False
                    
                if profile.hair_fur.get("fur_whiskers", False):
                    rejected_predictions.append({"field": "hair_fur.fur_whiskers", "value": True, "reason": "Subject is Plant/Cactus (no Animal)"})
                    profile.hair_fur["fur_whiskers"] = False

        # Consistency Engine validation checks
        if profile.hair_fur.get("has_hair", False) and profile.materials.get("Hair", 0.0) < 0.05:
            profile.materials["Hair"] = 0.15
            rules_fired.append("Consistency -> Sync Hair Material")
            
        if profile.hair_fur.get("has_fur", False) and profile.materials.get("Fur", 0.0) < 0.05:
            profile.materials["Fur"] = 0.15
            rules_fired.append("Consistency -> Sync Fur Material")

        if profile.hair_fur.get("fur_whiskers", False) and not profile.hair_fur.get("whiskers", False):
            profile.hair_fur["whiskers"] = True
            
        return ValidatedImageProfile(
            raw_profile_dict=raw_dict,
            scene=profile.scene,
            subject=profile.subject,
            background=profile.background,
            materials=profile.materials,
            hair_fur=profile.hair_fur,
            edge_types=profile.edge_types,
            lighting=profile.lighting,
            confidence=profile.confidence,
            rejected_predictions=rejected_predictions,
            rules_fired=rules_fired
        )
