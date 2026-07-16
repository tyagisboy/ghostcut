class BenchmarkManifest:
    """
    Defines capabilities-driven configuration metadata schemas
    across categories (curly hair, transparency, backlit, backlit portraits, etc.)
    """
    def __init__(self):
        self.manifest = self._initialize_manifest()

    def _initialize_manifest(self) -> dict:
        return {
            "Straight Hair": {
                "image_id": "straight_hair_001",
                "difficulty": "Easy",
                "scene": "Studio Portrait",
                "subject": "Human",
                "materials": ["Skin", "Hair"],
                "expected_capabilities": ["Boundary Accuracy", "Hair Preservation", "Edge Smoothness"]
            },
            "Curly Hair": {
                "image_id": "curly_hair_002",
                "difficulty": "Medium",
                "scene": "Outdoor Portrait",
                "subject": "Human",
                "materials": ["Skin", "Hair"],
                "expected_capabilities": ["Boundary Accuracy", "Hair Preservation", "Halo Suppression"]
            },
            "Afro Hair": {
                "image_id": "afro_hair_003",
                "difficulty": "Hard",
                "scene": "Studio Portrait",
                "subject": "Human",
                "materials": ["Skin", "Hair"],
                "expected_capabilities": ["Boundary Accuracy", "Hair Preservation", "Thin Structure Preservation"]
            },
            "Wet Hair": {
                "image_id": "wet_hair_004",
                "difficulty": "Medium",
                "scene": "Backlit Portrait",
                "subject": "Human",
                "materials": ["Skin", "Hair"],
                "expected_capabilities": ["Boundary Accuracy", "Hair Preservation", "Edge Smoothness"]
            },
            "Long Fur": {
                "image_id": "long_fur_005",
                "difficulty": "Medium",
                "scene": "Pet",
                "subject": "Animal",
                "materials": ["Fur"],
                "expected_capabilities": ["Boundary Accuracy", "Fur Preservation", "Color Spill Suppression"]
            },
            "Short Fur": {
                "image_id": "short_fur_006",
                "difficulty": "Easy",
                "scene": "Pet",
                "subject": "Animal",
                "materials": ["Fur"],
                "expected_capabilities": ["Boundary Accuracy", "Fur Preservation", "Edge Smoothness"]
            },
            "Glass": {
                "image_id": "glass_007",
                "difficulty": "Hard",
                "scene": "Product",
                "subject": "Product",
                "materials": ["Glass"],
                "expected_capabilities": ["Boundary Accuracy", "Transparency Preservation", "Halo Suppression"]
            },
            "Plastic": {
                "image_id": "plastic_008",
                "difficulty": "Easy",
                "scene": "Product",
                "subject": "Product",
                "materials": ["Plastic"],
                "expected_capabilities": ["Boundary Accuracy", "Edge Smoothness"]
            },
            "Mesh": {
                "image_id": "mesh_009",
                "difficulty": "Hard",
                "scene": "Studio Portrait",
                "subject": "Human",
                "materials": ["Fabric"],
                "expected_capabilities": ["Boundary Accuracy", "Thin Structure Preservation"]
            },
            "Lace": {
                "image_id": "lace_010",
                "difficulty": "Hard",
                "scene": "Studio Portrait",
                "subject": "Human",
                "materials": ["Fabric"],
                "expected_capabilities": ["Boundary Accuracy", "Thin Structure Preservation", "Halo Suppression"]
            },
            "Jewelry": {
                "image_id": "jewelry_011",
                "difficulty": "Medium",
                "scene": "Product",
                "subject": "Product",
                "materials": ["Metal", "Glass"],
                "expected_capabilities": ["Boundary Accuracy", "Edge Smoothness"]
            },
            "Leaves": {
                "image_id": "leaves_012",
                "difficulty": "Medium",
                "scene": "Product",
                "subject": "Plant",
                "materials": ["Leather"],
                "expected_capabilities": ["Boundary Accuracy", "Thin Structure Preservation"]
            },
            "Feathers": {
                "image_id": "feathers_013",
                "difficulty": "Hard",
                "scene": "Product",
                "subject": "Animal",
                "materials": ["Feather"],
                "expected_capabilities": ["Boundary Accuracy", "Thin Structure Preservation", "Fur Preservation"]
            },
            "Motion Blur": {
                "image_id": "motion_blur_014",
                "difficulty": "Hard",
                "scene": "Outdoor Portrait",
                "subject": "Human",
                "materials": ["Skin"],
                "expected_capabilities": ["Boundary Accuracy", "Edge Smoothness", "Halo Suppression"]
            },
            "Backlit": {
                "image_id": "backlit_015",
                "difficulty": "Medium",
                "scene": "Backlit Portrait",
                "subject": "Human",
                "materials": ["Skin", "Hair"],
                "expected_capabilities": ["Boundary Accuracy", "Hair Preservation", "Color Spill Suppression"]
            }
        }

    def get_entry(self, category: str) -> dict:
        return self.manifest.get(category, self.manifest["Plastic"])
