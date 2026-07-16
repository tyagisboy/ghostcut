import cv2
import numpy as np
from src.core.base_runtime import BaseRuntime

class EyeRuntime(BaseRuntime):
    """
    SDK compliant Eye Intelligence runtime.
    Detects eyes, reflections, glasses frame edges, and blink state using face bounding box context.
    """
    def __init__(self):
        pass

    def get_metadata(self) -> dict:
        return {
            "id": "eye",
            "name": "Eye Intelligence",
            "dependencies": ["face"],
            "execution_cost": 2.0,
            "quality_impact": 9.0,
            "requires_mask": True
        }

    def analyze(self, img_bgr: np.ndarray, mask: np.ndarray = None, context: dict = None) -> dict:
        """
        Extracts eye coordinates based on Face context and performs feature extraction.
        """
        h, w = img_bgr.shape[:2]
        
        # Defaults
        has_eyes = False
        reflections_detected = False
        glasses_detected = False
        blink_state = "open"
        confidence = 0.0

        try:
            # Resolve face box from preceding runtime context
            face_box = [0, 0, w, int(h * 0.4)]
            if context and "face" in context and context["face"].get("has_face"):
                face_box = context["face"]["face_box"]
                has_eyes = True
                confidence = 0.88

            fx, fy, fw, fh = face_box
            if fw > 20 and fh > 20:
                # Approximate eye line (y-range: 25% to 50% of face height)
                eye_ymin = fy + int(fh * 0.25)
                eye_ymax = fy + int(fh * 0.50)
                
                # Left eye (x-range: 15% to 45% of face width)
                le_xmin = fx + int(fw * 0.15)
                le_xmax = fx + int(fw * 0.45)
                
                # Right eye (x-range: 55% to 85% of face width)
                re_xmin = fx + int(fw * 0.55)
                re_xmax = fx + int(fw * 0.85)

                # Validate ranges
                if (eye_ymax > eye_ymin) and (le_xmax > le_xmin) and (re_xmax > re_xmin):
                    left_crop = img_bgr[eye_ymin:eye_ymax, le_xmin:le_xmax]
                    right_crop = img_bgr[eye_ymin:eye_ymax, re_xmin:re_xmax]

                    # 1. Reflection detection (check for specular high-intensity spots)
                    for crop in [left_crop, right_crop]:
                        if crop.size > 0:
                            gray = cv2.cvtColor(crop, cv2.COLOR_BGR2GRAY)
                            _, thresh = cv2.threshold(gray, 240, 255, cv2.THRESH_BINARY)
                            if np.sum(thresh) > 0:
                                reflections_detected = True

                    # 2. Eyeglasses detection (check for high gradient edges around eyes/bridge)
                    # Merge left & right eye regions including the nose bridge
                    bridge_crop = img_bgr[eye_ymin:eye_ymax, le_xmin:re_xmax]
                    if bridge_crop.size > 0:
                        gray_bridge = cv2.cvtColor(bridge_crop, cv2.COLOR_BGR2GRAY)
                        edges = cv2.Canny(gray_bridge, 50, 150)
                        # Check edge density. Glasses frames produce distinct contour lines
                        edge_density = np.mean(edges > 0)
                        if edge_density > 0.05:  # more than 5% edge pixels
                            glasses_detected = True

                    # 3. Blink State (check vertical profile of iris/pupil)
                    # Open eyes have high contrast dark circles in the center
                    if left_crop.size > 0:
                        gray_left = cv2.cvtColor(left_crop, cv2.COLOR_BGR2GRAY)
                        # Dark pixels ratio
                        dark_pixels = np.mean(gray_left < 80)
                        if dark_pixels < 0.05:  # very few dark pixels indicating closed eyelids
                            blink_state = "closed"

            return {
                "has_eyes": has_eyes,
                "reflections": reflections_detected,
                "glasses": glasses_detected,
                "blink_state": blink_state,
                "confidence": confidence
            }

        except Exception as e:
            print(f"[-] EyeRuntime error: {e}")
            return {
                "has_eyes": False,
                "reflections": False,
                "glasses": False,
                "blink_state": "open",
                "confidence": 0.0
            }
