import os
import json

class BenchmarkDataset:
    """
    Manages evaluation ground-truth reference data and directories
    across categories (Portrait, Animal, Product, Glass, Jewelry, Plants, Food, etc.)
    """
    def __init__(self):
        self.categories = [
            "Portrait", "Animal", "Product", "Glass", "Jewelry",
            "Plants", "Food", "Transparent", "CurlyHair", "StraightHair",
            "WetHair", "Backlit"
        ]
        self.ground_truth = self._initialize_ground_truths()

    def _initialize_ground_truths(self) -> dict:
        # Default mock definitions of ground truth targets per category for validation
        return {
            "Portrait": {
                "expected_scene": "Studio Portrait",
                "expected_subjects": ["Human"],
                "expected_materials": ["Skin", "Hair", "Fabric"],
                "expected_edges": ["Hard", "Soft", "Hair"]
            },
            "Animal": {
                "expected_scene": "Pet",
                "expected_subjects": ["Animal"],
                "expected_materials": ["Fur", "Leather"],
                "expected_edges": ["Soft", "Fur", "Whisker"]
            },
            "Product": {
                "expected_scene": "Product",
                "expected_subjects": ["Product"],
                "expected_materials": ["Metal", "Plastic"],
                "expected_edges": ["Hard"]
            },
            "Glass": {
                "expected_scene": "Product",
                "expected_subjects": ["Product"],
                "expected_materials": ["Glass", "Water"],
                "expected_edges": ["Transparent", "Reflection"]
            },
            "Jewelry": {
                "expected_scene": "Product",
                "expected_subjects": ["Product"],
                "expected_materials": ["Metal", "Glass"],
                "expected_edges": ["Hard", "Reflection"]
            },
            "Plants": {
                "expected_scene": "Product",
                "expected_subjects": ["Plant"],
                "expected_materials": ["Feather", "Leather"],  # leaf material mappings
                "expected_edges": ["Soft"]
            },
            "Food": {
                "expected_scene": "Food",
                "expected_subjects": ["Product"],
                "expected_materials": ["Leather", "Skin"],
                "expected_edges": ["Soft"]
            },
            "Transparent": {
                "expected_scene": "Product",
                "expected_subjects": ["Product"],
                "expected_materials": ["Glass"],
                "expected_edges": ["Transparent"]
            },
            "CurlyHair": {
                "expected_scene": "Studio Portrait",
                "expected_subjects": ["Human"],
                "expected_materials": ["Hair", "Skin"],
                "expected_edges": ["Hair"]
            },
            "StraightHair": {
                "expected_scene": "Studio Portrait",
                "expected_subjects": ["Human"],
                "expected_materials": ["Hair", "Skin"],
                "expected_edges": ["Hair"]
            },
            "WetHair": {
                "expected_scene": "Outdoor Portrait",
                "expected_subjects": ["Human"],
                "expected_materials": ["Hair", "Skin"],
                "expected_edges": ["Hair", "Hard"]
            },
            "Backlit": {
                "expected_scene": "Backlit Portrait",
                "expected_subjects": ["Human"],
                "expected_materials": ["Skin", "Hair"],
                "expected_edges": ["Hair", "Soft"]
            }
        }

    def get_ground_truth(self, category: str) -> dict:
        return self.ground_truth.get(category, self.ground_truth["Product"])
