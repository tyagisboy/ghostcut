import cv2
import numpy as np
from src.core.base_runtime import BaseRuntime

class PlantIntelligenceRuntime(BaseRuntime):
    """
    SDK compliant Plant Intelligence runtime.
    Analyzes botanical boundaries, leaf regions, stems, flowers, and needles using HSV color and line transforms.
    """
    def __init__(self):
        pass

    def get_metadata(self) -> dict:
        return {
            "id": "plant",
            "name": "Plant Intelligence",
            "dependencies": ["material"],
            "execution_cost": 2.5,
            "quality_impact": 8.0,
            "requires_mask": True
        }

    def analyze(self, img_bgr: np.ndarray, mask: np.ndarray = None, context: dict = None) -> dict:
        """
        Extracts leaf contours, stem lines, and floral colored regions.
        """
        h, w = img_bgr.shape[:2]
        if mask is None:
            mask = np.ones((h, w), dtype=np.uint8) * 255

        has_botanical = False
        leaves_detected = False
        stems_detected = False
        flowers_detected = False
        thorns_detected = False
        needles_detected = False
        confidence = 0.0

        try:
            # Mask applied to BGR image
            masked_img = cv2.bitwise_and(img_bgr, img_bgr, mask=mask)
            
            # Check if mask has enough pixels
            if np.sum(mask > 127) > 500:
                has_botanical = True
                confidence = 0.90

                # 1. Color Segmentation for Leaves and Stems (Green mask)
                hsv = cv2.cvtColor(masked_img, cv2.COLOR_BGR2HSV)
                lower_green = np.array([35, 30, 30])
                upper_green = np.array([90, 255, 255])
                green_mask = cv2.inRange(hsv, lower_green, upper_green)
                green_ratio = np.mean(green_mask > 0)
                
                if green_ratio > 0.05:  # Over 5% of mask is green
                    leaves_detected = True

                # 2. Color Segmentation for Flowers (Non-green, non-brown colors: e.g. red, yellow, pink)
                # Red color ranges
                lower_red1 = np.array([0, 50, 50])
                upper_red1 = np.array([10, 255, 255])
                lower_red2 = np.array([170, 50, 50])
                upper_red2 = np.array([180, 255, 255])
                red_mask1 = cv2.inRange(hsv, lower_red1, upper_red1)
                red_mask2 = cv2.inRange(hsv, lower_red2, upper_red2)
                
                # Yellow/Pink range
                lower_pink = np.array([140, 50, 50])
                upper_pink = np.array([170, 255, 255])
                pink_mask = cv2.inRange(hsv, lower_pink, upper_pink)

                floral_pixels = np.sum(red_mask1) + np.sum(red_mask2) + np.sum(pink_mask)
                if floral_pixels > 1000:
                    flowers_detected = True

                # 3. Stem and branch detection (Hough line transform on wood/brown or green skeleton)
                gray = cv2.cvtColor(masked_img, cv2.COLOR_BGR2GRAY)
                edges = cv2.Canny(gray, 40, 120)
                lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=20, minLineLength=15, maxLineGap=5)
                if lines is not None and len(lines) > 3:
                    stems_detected = True

                # 4. Thorns and Needles detection (sharp high-frequency contour projections)
                contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                if contours:
                    c = max(contours, key=cv2.contourArea)
                    perimeter = cv2.arcLength(c, True)
                    approx = cv2.approxPolyDP(c, 0.005 * perimeter, True)
                    
                    # Sharp angle peaks indicate thorns/needles
                    sharp_peaks = 0
                    pts = approx.reshape(-1, 2)
                    n_pts = len(pts)
                    for i in range(n_pts):
                        p1 = pts[i - 1]
                        p2 = pts[i]
                        p3 = pts[(i + 1) % n_pts]
                        
                        v1 = p1 - p2
                        v2 = p3 - p2
                        cosine_angle = np.dot(v1, v2) / (np.linalg.norm(v1) * np.linalg.norm(v2) + 1e-6)
                        angle = np.degrees(np.arccos(np.clip(cosine_angle, -1.0, 1.0)))
                        
                        # Very sharp angle (< 45 degrees)
                        if angle < 45.0:
                            sharp_peaks += 1
                    
                    if sharp_peaks > 2:
                        thorns_detected = True
                        if green_ratio > 0.4:
                            needles_detected = True

            return {
                "has_botanical": has_botanical,
                "leaves": leaves_detected,
                "stems": stems_detected,
                "flowers": flowers_detected,
                "thorns": thorns_detected,
                "needles": needles_detected,
                "confidence": confidence
            }

        except Exception as e:
            print(f"[-] PlantIntelligenceRuntime error: {e}")
            return {
                "has_botanical": False,
                "leaves": False,
                "stems": False,
                "flowers": False,
                "thorns": False,
                "needles": False,
                "confidence": 0.0
            }
