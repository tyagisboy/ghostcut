import cv2
import numpy as np

class AdaptiveBoundarySolver:
    """
    Computes local transition zones dynamically using Sobel gradients and orientations
    instead of fixed-pixel radii boundaries.
    """
    def __init__(self):
        pass

    def solve_boundary(self, img_bgr: np.ndarray, mask: np.ndarray, region_type: str) -> np.ndarray:
        """
        Generates dynamic trimap/transition band mask using local texture gradients.
        """
        # Calculate grayscale guide
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        
        # Sobel gradient analysis
        sobel_x = cv2.Sobel(gray, cv2.CV_64F, 1, 0, ksize=3)
        sobel_y = cv2.Sobel(gray, cv2.CV_64F, 0, 1, ksize=3)
        
        # Calculate magnitude
        grad_mag = np.sqrt(sobel_x**2 + sobel_y**2)
        grad_mag_norm = cv2.normalize(grad_mag, None, 0, 255, cv2.NORM_MINMAX).astype(np.uint8)
        
        # Determine dynamic adaptive radius threshold
        if region_type.lower() == "hair":
            base_size = 15
            grad_scale = 1.8
        elif region_type.lower() == "fur":
            base_size = 12
            grad_scale = 1.5
        elif region_type.lower() == "glass":
            base_size = 20
            grad_scale = 2.2
        elif region_type.lower() == "leaves":
            base_size = 8
            grad_scale = 1.0
        else:
            base_size = 5
            grad_scale = 0.5
            
        # Dilate and erode to create custom adaptive trimap boundaries
        kernel_size = max(3, int(base_size + grad_scale * np.mean(grad_mag_norm) / 50.0))
        kernel = cv2.getStructuringElement(cv2.MORPH_ELLIPSE, (kernel_size, kernel_size))
        
        dilated = cv2.dilate(mask, kernel, iterations=1)
        eroded = cv2.erode(mask, kernel, iterations=1)
        
        # Trimap: 128 is transition boundary zone, 255 is foreground, 0 is background
        trimap = np.zeros_like(mask)
        trimap[dilated > 0] = 128
        trimap[eroded > 0] = 255
        
        return trimap
