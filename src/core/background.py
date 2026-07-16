import cv2
import numpy as np

from src.core.base_runtime import BaseRuntime

class BackgroundIntelligence(BaseRuntime):
    """
    Analyzes background characteristics: complexity, blur, separation difficulty, and dominant colors.
    """
    def __init__(self):
        pass

    def get_metadata(self) -> dict:
        return {
            "id": "background",
            "name": "Background Intelligence",
            "dependencies": ["scene"],
            "execution_cost": 1.5,
            "quality_impact": 6.0,
            "requires_mask": False
        }

    def analyze(self, img_bgr, metrics=None, context=None):

        h, w = img_bgr.shape[:2]
        small = cv2.resize(img_bgr, (128, 128))
        gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
        
        # Define background border mask
        border = np.ones((128, 128), dtype=np.uint8)
        border[16:112, 16:112] = 0
        
        # Calculate background laplacian variance (blur estimation)
        bg_gray = gray[border > 0]
        lap_bg = cv2.Laplacian(gray, cv2.CV_32F)
        bg_var = float(np.var(lap_bg[border > 0]))
        
        # Complexity classification
        if bg_var < 50.0:
            complexity = "low"
        elif bg_var < 300.0:
            complexity = "medium"
        else:
            complexity = "high"
            
        # Separation difficulty based on fg-bg contrast
        if metrics is not None:
            bg_b = metrics.get("bg_brightness", 128.0)
            fg_b = metrics.get("fg_brightness", 128.0)
        else:
            bg_b = float(np.mean(gray[border > 0]))
            fg_b = float(np.mean(gray[border == 0]))
            
        brightness_diff = abs(fg_b - bg_b)
        sep_difficulty = float(np.clip(1.0 - (brightness_diff / 150.0), 0.0, 1.0))
        
        # Dynamic Range
        p95, p5 = np.percentile(bg_gray, [95, 5])
        contrast = float(p95 - p5) / 255.0
        
        # Dominant Colors (k-means on background border pixels)
        bg_pixels = small[border > 0].reshape(-1, 3).astype(np.float32)
        criteria = (cv2.TERM_CRITERIA_EPS + cv2.TERM_CRITERIA_MAX_ITER, 10, 1.0)
        flags = cv2.KMEANS_RANDOM_CENTERS
        compactness, labels, centers = cv2.kmeans(bg_pixels, 3, None, criteria, 10, flags)
        
        dominant_colors = []
        for center in centers:
            # Convert BGR to hex string
            b, g, r = map(int, center)
            dominant_colors.append(f"#{r:02x}{g:02x}{b:02x}")
            
        return {
            "complexity": complexity,
            "dominant_colors": dominant_colors,
            "blur": float(bg_var),
            "contrast": contrast,
            "separation_difficulty": sep_difficulty
        }
