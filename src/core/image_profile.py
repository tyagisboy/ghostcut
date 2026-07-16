class ImageProfile:
    """
    Represents the complete multi-attribute Image Intelligence Profile of an image.
    """
    def __init__(self, scene="Unknown", subject=None, background=None, materials=None, hair_fur=None, edge_types=None, lighting=None, confidence=None):
        self.scene = scene
        self.subject = subject if subject is not None else []
        
        # Background properties
        self.background = background if background is not None else {
            "complexity": "low",
            "dominant_colors": [],
            "blur": 0.0,
            "contrast": 0.0
        }
        
        # Materials mapping (prob/ratio)
        self.materials = materials if materials is not None else {
            "Skin": 0.0, "Hair": 0.0, "Fur": 0.0, "Fabric": 0.0, "Glass": 0.0,
            "Plastic": 0.0, "Metal": 0.0, "Leather": 0.0, "Lace": 0.0, "Feather": 0.0
        }
        
        # Hair/Fur specifications with v3 defaults
        defaults = {
            "has_hair": False,
            "has_fur": False,
            "hair_type": "general",
            "fur_type": "none",
            "whiskers": False,
            
            # Hair Intelligence v2
            "hair_length": "medium",
            "hair_density": 0.0,
            "hair_curl_level": 0.0,
            "hair_strand_width": "medium",
            "hair_flyaway_score": 0.0,
            "hair_transparency_score": 0.0,
            "hair_wetness": 0.0,
            "hair_frizz": 0.0,
            "hair_volume": 0.0,
            "hair_backlit_probability": 0.0,
            "hair_confidence": 0.0,

            # Fur Intelligence v2
            "fur_length": "none",
            "fur_density": 0.0,
            "fur_fluffiness": 0.0,
            "fur_whiskers": False,
            "fur_undercoat": 0.0,
            "fur_transparency": 0.0,
            "fur_confidence": 0.0
        }
        self.hair_fur = defaults
        if hair_fur is not None:
            self.hair_fur.update(hair_fur)
            
        # Edge types present in transition zone
        self.edge_types = edge_types if edge_types is not None else []
        
        # Lighting environment
        self.lighting = lighting if lighting is not None else {
            "backlit": False,
            "ambient_brightness": 128.0,
            "specular_highlights": False
        }
        
        # Pipeline confidence tracking
        self.confidence = confidence if confidence is not None else {
            "initial_segmentation": 1.0,
            "overall": 1.0
        }

    def to_dict(self):
        return {
            "scene": self.scene,
            "subject": self.subject,
            "background": self.background,
            "materials": self.materials,
            "hair_fur": self.hair_fur,
            "edge_types": self.edge_types,
            "lighting": self.lighting,
            "confidence": self.confidence
        }


class ValidatedImageProfile(ImageProfile):
    """
    Subclass representing a semantically validated and consistent ImageProfile,
    maintaining the original raw predictions and validation metadata.
    """
    def __init__(self, raw_profile_dict, scene="Unknown", subject=None, background=None, materials=None, hair_fur=None, edge_types=None, lighting=None, confidence=None, rejected_predictions=None, rules_fired=None):
        super().__init__(scene, subject, background, materials, hair_fur, edge_types, lighting, confidence)
        self.raw_profile = raw_profile_dict
        self.rejected_predictions = rejected_predictions if rejected_predictions is not None else []
        self.rules_fired = rules_fired if rules_fired is not None else []

    def to_dict(self):
        d = super().to_dict()
        d["raw_profile"] = self.raw_profile
        d["rejected_predictions"] = self.rejected_predictions
        d["rules_fired"] = self.rules_fired
        return d

