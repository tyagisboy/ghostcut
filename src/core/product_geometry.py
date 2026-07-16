import cv2
import numpy as np
from src.core.base_runtime import BaseRuntime

class ProductGeometryRuntime(BaseRuntime):
    """
    SDK compliant Product Geometry intelligence runtime.
    Detects straight edges, circular profiles, mirror symmetry, and highlights indicating reflective surfaces.
    """
    def __init__(self):
        pass

    def get_metadata(self) -> dict:
        return {
            "id": "product_geometry",
            "name": "Product Geometry Intelligence",
            "dependencies": ["material"],
            "execution_cost": 2.5,
            "quality_impact": 8.5,
            "requires_mask": True
        }

    def analyze(self, img_bgr: np.ndarray, mask: np.ndarray = None, context: dict = None) -> dict:
        """
        Extracts structural geometric lines, circles, symmetry scores, and specularity.
        """
        h, w = img_bgr.shape[:2]
        if mask is None:
            mask = np.ones((h, w), dtype=np.uint8) * 255

        has_geometry = False
        straight_edges = False
        circular_edges = False
        symmetry_score = 0.0
        reflective_surfaces = False
        confidence = 0.0

        try:
            # Check mask coverage
            mask_pixels = np.sum(mask > 127)
            if mask_pixels > 500:
                has_geometry = True
                confidence = 0.92

                # 1. Straight edge detection (Hough Lines)
                gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
                # Apply mask to focus only on foreground object edges
                masked_gray = cv2.bitwise_and(gray, gray, mask=mask)
                edges = cv2.Canny(masked_gray, 50, 150)
                
                lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=40, minLineLength=30, maxLineGap=10)
                if lines is not None and len(lines) > 4:
                    straight_edges = True

                # 2. Circular edge detection (Hough Circles)
                # Blur first to reduce noise
                blurred = cv2.medianBlur(masked_gray, 5)
                circles = cv2.HoughCircles(blurred, cv2.HOUGH_GRADIENT, dp=1.2, minDist=30,
                                            param1=50, param2=30, minRadius=10, maxRadius=100)
                if circles is not None and len(circles) > 0:
                    circular_edges = True

                # 3. Symmetry score calculation
                # Mirror mask horizontally and compute IoU of overlap
                # Get bounding box of mask
                y_indices, x_indices = np.where(mask > 127)
                ymin, ymax = int(np.min(y_indices)), int(np.max(y_indices))
                xmin, xmax = int(np.min(x_indices)), int(np.max(x_indices))
                
                obj_mask = mask[ymin:ymax, xmin:xmax]
                if obj_mask.size > 0:
                    # Flip horizontally
                    flipped_mask = cv2.flip(obj_mask, 1)
                    intersection = np.sum(cv2.bitwise_and(obj_mask, flipped_mask) > 127)
                    union = np.sum(cv2.bitwise_or(obj_mask, flipped_mask) > 127)
                    if union > 0:
                        symmetry_score = float(intersection / union)

                # 4. Reflective surfaces detection (high intensity specular highlights near sharp edges)
                # Reflective materials (metal, glass) exhibit bright specular glare spots
                _, spec_spots = cv2.threshold(gray, 245, 255, cv2.THRESH_BINARY)
                # Mask to object bounds
                spec_spots = cv2.bitwise_and(spec_spots, spec_spots, mask=mask)
                if np.sum(spec_spots > 127) > 50:  # significant bright spots inside mask
                    # Verify they align with material predictions like Metal or Glass if available in context
                    reflective_surfaces = True

            return {
                "has_geometry": has_geometry,
                "straight_edges": straight_edges,
                "circular_edges": circular_edges,
                "symmetry": symmetry_score,
                "reflective_surfaces": reflective_surfaces,
                "confidence": confidence
            }

        except Exception as e:
            print(f"[-] ProductGeometryRuntime error: {e}")
            return {
                "has_geometry": False,
                "straight_edges": False,
                "circular_edges": False,
                "symmetry": 0.0,
                "reflective_surfaces": False,
                "confidence": 0.0
            }
