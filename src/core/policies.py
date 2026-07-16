# Policy-based configuration settings for the Image Intelligence Engine.
# Replaces hardcoded values with editable presets for scenarios, materials, and edges.

POLICIES = {
    "scenarios": {
        "Studio Portrait": {
            "model_name": "birefnet-general",
            "processing_mode": "quality",
            "apply_matting": True,
            "erode_size": 3,
            "sharpness": 1,
            "focus_thresh": 0.0,
            "preserve_transparency": False,
            "decontaminate": True,
            "quality_loop": True,
            "radius_base": 6.0
        },
        "Outdoor Portrait": {
            "model_name": "birefnet-general",
            "processing_mode": "quality",
            "apply_matting": True,
            "erode_size": 4,
            "sharpness": 2,
            "focus_thresh": 2.0,
            "preserve_transparency": False,
            "decontaminate": True,
            "quality_loop": True,
            "radius_base": 7.0
        },
        "Backlit Portrait": {
            "model_name": "birefnet-general",
            "processing_mode": "ultra",
            "apply_matting": True,
            "erode_size": 5,
            "sharpness": 0,
            "focus_thresh": 0.0,
            "preserve_transparency": False,
            "decontaminate": True,
            "quality_loop": True,
            "radius_base": 10.0
        },
        "Product": {
            "model_name": "birefnet-general-lite",
            "processing_mode": "fast",
            "apply_matting": True,
            "erode_size": 2,
            "sharpness": 3,
            "focus_thresh": 4.0,
            "preserve_transparency": False,
            "decontaminate": False,
            "quality_loop": True,
            "radius_base": 2.0
        },
        "Pet": {
            "model_name": "birefnet-general",
            "processing_mode": "quality",
            "apply_matting": True,
            "erode_size": 6,
            "sharpness": 1,
            "focus_thresh": 1.0,
            "preserve_transparency": False,
            "decontaminate": True,
            "quality_loop": True,
            "radius_base": 12.0
        },
        "Transparent Object": {
            "model_name": "birefnet-general-lite",
            "processing_mode": "quality",
            "apply_matting": True,
            "erode_size": 4,
            "sharpness": 0,
            "focus_thresh": 0.0,
            "preserve_transparency": True,
            "decontaminate": True,
            "quality_loop": True,
            "radius_base": 8.0
        },
        "Clothing": {
            "model_name": "birefnet-general-lite",
            "processing_mode": "fast",
            "apply_matting": True,
            "erode_size": 3,
            "sharpness": 2,
            "focus_thresh": 2.0,
            "preserve_transparency": False,
            "decontaminate": False,
            "quality_loop": False,
            "radius_base": 3.0
        },
        "Jewelry": {
            "model_name": "birefnet-general-lite",
            "processing_mode": "fast",
            "apply_matting": True,
            "erode_size": 1,
            "sharpness": 4,
            "focus_thresh": 0.0,
            "preserve_transparency": False,
            "decontaminate": False,
            "quality_loop": True,
            "radius_base": 1.0
        },
        "Vehicle": {
            "model_name": "birefnet-general-lite",
            "processing_mode": "fast",
            "apply_matting": True,
            "erode_size": 2,
            "sharpness": 4,
            "focus_thresh": 3.0,
            "preserve_transparency": False,
            "decontaminate": False,
            "quality_loop": True,
            "radius_base": 2.0
        },
        "Food": {
            "model_name": "birefnet-general-lite",
            "processing_mode": "fast",
            "apply_matting": True,
            "erode_size": 2,
            "sharpness": 2,
            "focus_thresh": 2.0,
            "preserve_transparency": False,
            "decontaminate": False,
            "quality_loop": False,
            "radius_base": 2.0
        },
        "Plant": {
            "model_name": "birefnet-general-lite",
            "processing_mode": "quality",
            "apply_matting": True,
            "erode_size": 4,
            "sharpness": 2,
            "focus_thresh": 1.0,
            "preserve_transparency": False,
            "decontaminate": False,
            "quality_loop": True,
            "radius_base": 5.0
        }
    },
    "materials": {
        "Skin": {"alpha_policy": "hard", "radius": 2.0, "decontaminate": False},
        "Hair": {"alpha_policy": "soft", "radius": 12.0, "decontaminate": True},
        "Fur": {"alpha_policy": "soft", "radius": 12.0, "decontaminate": True},
        "Fabric": {"alpha_policy": "medium", "radius": 3.0, "decontaminate": False},
        "Glass": {"alpha_policy": "transparent", "radius": 8.0, "decontaminate": True},
        "Plastic": {"alpha_policy": "transparent", "radius": 6.0, "decontaminate": True},
        "Metal": {"alpha_policy": "hard", "radius": 1.5, "decontaminate": False},
        "Leather": {"alpha_policy": "hard", "radius": 2.0, "decontaminate": False},
        "Feather": {"alpha_policy": "soft", "radius": 9.0, "decontaminate": True},
        "Lace": {"alpha_policy": "semi-transparent", "radius": 7.0, "decontaminate": True},
        "Water": {"alpha_policy": "transparent", "radius": 10.0, "decontaminate": True},
        "Smoke": {"alpha_policy": "soft", "radius": 15.0, "decontaminate": True}
    },
    "edges": {
        "Hard": {"radius_mult": 0.5, "sharpness_boost": 2},
        "Soft": {"radius_mult": 1.0, "sharpness_boost": 0},
        "Hair": {"radius_mult": 2.0, "sharpness_boost": -1},
        "Fur": {"radius_mult": 2.0, "sharpness_boost": -1},
        "Fabric": {"radius_mult": 0.8, "sharpness_boost": 1},
        "Transparent": {"radius_mult": 1.5, "sharpness_boost": -2},
        "Reflection": {"radius_mult": 1.2, "sharpness_boost": -1},
        "Motion Blur": {"radius_mult": 2.5, "sharpness_boost": -3},
        "Shadow": {"radius_mult": 2.0, "sharpness_boost": -2},
        "Whisker": {"radius_mult": 2.5, "sharpness_boost": -1}
    }
}
