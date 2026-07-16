import cv2
import numpy as np
from src.core.base_runtime import BaseRuntime

class AnimalAnatomyRuntime(BaseRuntime):
    """
    SDK compliant Animal Anatomy intelligence runtime.
    Analyzes animal morphology to locate ears, tail, paws, whiskers, and feathers using contour geometry.
    """
    def __init__(self):
        pass

    def get_metadata(self) -> dict:
        return {
            "id": "animal_anatomy",
            "name": "Animal Anatomy Intelligence",
            "dependencies": ["material"],
            "execution_cost": 3.0,
            "quality_impact": 8.5,
            "requires_mask": True
        }

    def analyze(self, img_bgr: np.ndarray, mask: np.ndarray = None, context: dict = None) -> dict:
        """
        Locates anatomical extremities using contour analysis.
        """
        h, w = img_bgr.shape[:2]
        if mask is None:
            mask = np.ones((h, w), dtype=np.uint8) * 255

        has_anatomy = False
        ears_detected = False
        whiskers_detected = False
        tail_detected = False
        paws_detected = False
        feathers_detected = False
        confidence = 0.0

        try:
            # 1. Extract contours of foreground mask
            contours, _ = cv2.findContours(mask, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
            if contours:
                c = max(contours, key=cv2.contourArea)
                if cv2.contourArea(c) > 500:
                    has_anatomy = True
                    confidence = 0.91

                    # Get bounding box
                    x, y, cw, ch = cv2.boundingRect(c)

                    # 2. Check for ears: Search for peak points in upper 30% of bounding box
                    # We look at convexity defects of the hull
                    hull = cv2.convexHull(c, returnPoints=False)
                    if len(hull) > 3:
                        defects = cv2.convexityDefects(c, hull)
                        if defects is not None:
                            for i in range(defects.shape[0]):
                                s, e, f, d = defects[i, 0]
                                start = tuple(c[s][0])
                                end = tuple(c[e][0])
                                far = tuple(c[f][0])
                                
                                # If defect is in the upper part and is relatively deep
                                if start[1] < y + 0.3 * ch and end[1] < y + 0.3 * ch and d > 1500:
                                    ears_detected = True

                    # 3. Check for tail: Look for protrusions in left/right/bottom extremities
                    # Find points far away from the centroid
                    M = cv2.moments(c)
                    if M["m00"] > 0:
                        cx = int(M["m10"] / M["m00"])
                        cy = int(M["m01"] / M["m00"])
                        
                        # Check eccentricity
                        max_dist = 0
                        for pt in c:
                            px, py = pt[0]
                            dist = (px - cx) ** 2 + (py - cy) ** 2
                            if dist > max_dist:
                                max_dist = dist
                        
                        # High distance-to-area ratio suggests long extremities (like tails)
                        eccentricity = max_dist / cv2.contourArea(c)
                        if eccentricity > 1.2:
                            tail_detected = True

                    # 4. Check for paws: Search for local circular shapes in the bottom 25% region
                    bottom_ymin = y + int(ch * 0.75)
                    bottom_crop = mask[bottom_ymin:y+ch, x:x+cw]
                    if bottom_crop.size > 0:
                        # Paws manifest as multiple distinct touchpoints/components at the base
                        paw_contours, _ = cv2.findContours(bottom_crop, cv2.RETR_EXTERNAL, cv2.CHAIN_APPROX_SIMPLE)
                        if len(paw_contours) >= 2:
                            paws_detected = True

                    # 5. Whiskers detection: Look for thin high-gradient lines around centroid height
                    snout_ymin = y + int(ch * 0.2)
                    snout_ymax = y + int(ch * 0.5)
                    snout_xmin = x + int(cw * 0.25)
                    snout_xmax = x + int(cw * 0.75)
                    snout_crop = img_bgr[snout_ymin:snout_ymax, snout_xmin:snout_xmax]
                    if snout_crop.size > 0:
                        gray_snout = cv2.cvtColor(snout_crop, cv2.COLOR_BGR2GRAY)
                        # Look for thin whiskers via line detection
                        edges = cv2.Canny(gray_snout, 50, 150)
                        lines = cv2.HoughLinesP(edges, 1, np.pi/180, threshold=15, minLineLength=10, maxLineGap=4)
                        if lines is not None and len(lines) > 2:
                            whiskers_detected = True

                    # 6. Feathers detection: High frequency boundary variation
                    # Calculate arc length vs. simplified polygon perimeter
                    perimeter = cv2.arcLength(c, True)
                    approx = cv2.approxPolyDP(c, 0.002 * perimeter, True)
                    approx_perimeter = cv2.arcLength(approx, True)
                    # If high frequency serration exists, ratio of detailed perimeter to simplified is high
                    if perimeter / approx_perimeter > 1.05:
                        feathers_detected = True

            return {
                "has_anatomy": has_anatomy,
                "ears": ears_detected,
                "whiskers": whiskers_detected,
                "tail": tail_detected,
                "paws": paws_detected,
                "feathers": feathers_detected,
                "confidence": confidence
            }

        except Exception as e:
            print(f"[-] AnimalAnatomyRuntime error: {e}")
            return {
                "has_anatomy": False,
                "ears": False,
                "whiskers": False,
                "tail": False,
                "paws": False,
                "feathers": False,
                "confidence": 0.0
            }
