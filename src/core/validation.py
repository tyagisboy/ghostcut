import os
import time
import numpy as np

class RuntimeValidator:
    """
    Validates input details, generated recipes, system environments, and output quality characteristics
    to catch system anomalies before and after processing.
    """
    def __init__(self, models_dir):
        self.models_dir = models_dir

    def validate_environment(self):
        """
        Validates presence of essential model weights and software libraries.
        Returns: success (bool), issues (list)
        """
        issues = []
        
        # Check ONNX files
        required_models = [
            "birefnet-general-lite.onnx",
            "birefnet-general.onnx",
            "vitmatte-small.onnx"
        ]
        
        for model in required_models:
            path = os.path.join(self.models_dir, model)
            if not os.path.exists(path):
                issues.append(f"Missing model weight file: {model} at {path}")
                
        # Check system libraries by attempting imports
        try:
            import cv2
        except ImportError:
            issues.append("OpenCV library ('cv2') is not installed")
            
        try:
            import onnxruntime as ort
        except ImportError:
            issues.append("ONNX Runtime library ('onnxruntime') is not installed")
            
        success = len(issues) == 0
        return success, issues

    def validate_input(self, img_bgr):
        """
        Validates characteristics of the input BGR image matrix.
        """
        issues = []
        if img_bgr is None:
            return False, ["Input image matrix is None"]
            
        if not isinstance(img_bgr, np.ndarray):
            return False, [f"Invalid input type: expected np.ndarray, got {type(img_bgr)}"]
            
        if img_bgr.ndim != 3 or img_bgr.shape[2] != 3:
            issues.append(f"Invalid channel count: expected 3 (BGR), got shape {img_bgr.shape}")
            
        h, w = img_bgr.shape[:2]
        if h < 64 or w < 64:
            issues.append(f"Image resolution too small: {w}x{h} (minimum 64x64)")
            
        if h > 8000 or w > 8000:
            issues.append(f"Image resolution extremely large: {w}x{h} (maximum supported 8000x8000)")
            
        success = len(issues) == 0
        return success, issues

    def validate_recipe(self, recipe):
        """
        Validates generated parameters in the ProcessingRecipe.
        """
        issues = []
        if recipe is None:
            return False, ["Recipe is None"]
            
        # Validate bounds
        if recipe.erode_size < 1 or recipe.erode_size > 15:
            issues.append(f"erode_size {recipe.erode_size} is out of bounds [1, 15]")
            
        if recipe.sharpness < 0 or recipe.sharpness > 10:
            issues.append(f"sharpness {recipe.sharpness} is out of bounds [0, 10]")
            
        if recipe.focus_thresh < 0.0 or recipe.focus_thresh > 15.0:
            issues.append(f"focus_thresh {recipe.focus_thresh} is out of bounds [0.0, 15.0]")
            
        if recipe.radius_base < 0.5 or recipe.radius_base > 30.0:
            issues.append(f"radius_base {recipe.radius_base} is out of bounds [0.5, 30.0]")
            
        valid_modes = ["fast", "quality", "ultra"]
        if recipe.processing_mode not in valid_modes:
            issues.append(f"Invalid processing_mode: {recipe.processing_mode}. Supported: {valid_modes}")
            
        success = len(issues) == 0
        return success, issues

    def validate_output(self, mask, original_shape):
        """
        Validates characteristics of the generated output mask.
        """
        issues = []
        if mask is None:
            return False, ["Output mask matrix is None"]
            
        if mask.shape[:2] != original_shape[:2]:
            issues.append(f"Mask dimensions mismatch: expected {original_shape[:2]}, got {mask.shape[:2]}")
            
        # Check range
        min_val, max_val = np.min(mask), np.max(mask)
        if min_val < 0 or max_val > 255:
            issues.append(f"Mask pixel values out of bounds [0, 255]: min={min_val}, max={max_val}")
            
        success = len(issues) == 0
        return success, issues
