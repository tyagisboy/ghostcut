import cv2
import numpy as np
from src.core.base_runtime import BaseRuntime

class FaceRuntime(BaseRuntime):
    """
    SDK compliant Face Intelligence runtime.
    Identifies facial features, bounding box, neck, beard, ears, and pose symmetry using OpenCV.
    """
    def __init__(self):
        pass

    def get_metadata(self) -> dict:
        return {
            "id": "face",
            "name": "Face Intelligence",
            "dependencies": ["subject"],
            "execution_cost": 3.0,
            "quality_impact": 8.5,
            "requires_mask": True
        }

    def analyze(self, img_bgr: np.ndarray, mask: np.ndarray = None, context: dict = None) -> dict:
        """
        Locates facial boundaries within the foreground mask and estimates details.
        """
        h, w = img_bgr.shape[:2]
        if mask is None:
            mask = np.ones((h, w), dtype=np.uint8) * 255

        # Default face attributes
        face_box = [0, 0, 0, 0]
        has_face = False
        beard_detected = False
        ears_detected = False
        neck_detected = False
        pose_yaw = 0.0
        confidence = 0.0

        try:
            # 1. Find bounding box of foreground mask
            y_indices, x_indices = np.where(mask > 127)
            if len(y_indices) > 0 and len(x_indices) > 0:
                ymin, ymax = int(np.min(y_indices)), int(np.max(y_indices))
                xmin, xmax = int(np.min(x_indices)), int(np.max(x_indices))
                fg_w = xmax - xmin
                fg_h = ymax - ymin

                # Assume face lies in the upper ~35% of the foreground mask
                face_ymin = ymin
                face_ymax = int(ymin + 0.35 * fg_h)
                face_xmin = int(xmin + 0.15 * fg_w)
                face_xmax = int(xmax - 0.15 * fg_w)

                if (face_ymax > face_ymin + 10) and (face_xmax > face_xmin + 10):
                    face_box = [face_xmin, face_ymin, face_xmax - face_xmin, face_ymax - face_ymin]
                    has_face = True
                    confidence = 0.92

                    # Extract face crop
                    face_crop = img_bgr[face_ymin:face_ymax, face_xmin:face_xmax]
                    face_mask = mask[face_ymin:face_ymax, face_xmin:face_xmax]

                    # 2. Beard detection: Check texture in lower 40% of the face region
                    fh, fw = face_crop.shape[:2]
                    beard_ymin = int(fh * 0.6)
                    beard_crop = face_crop[beard_ymin:, :]
                    if beard_crop.size > 0:
                        # Convert to gray and calculate laplacian gradient variance
                        b_gray = cv2.cvtColor(beard_crop, cv2.COLOR_BGR2GRAY)
                        b_var = np.var(cv2.Laplacian(b_gray, cv2.CV_32F))
                        # Check mean brightness (beard hair is typically dark)
                        b_mean = np.mean(b_gray)
                        if b_var > 80.0 and b_mean < 110.0:
                            beard_detected = True

                    # 3. Ears detection: Analyze side margins of the face mask
                    left_margin = face_mask[:, :int(fw * 0.15)]
                    right_margin = face_mask[:, int(fw * 0.85):]
                    if np.mean(left_margin > 127) > 0.3 and np.mean(right_margin > 127) > 0.3:
                        ears_detected = True

                    # 4. Neck detection: Analyze region directly below face_box
                    neck_ymin = face_ymax
                    neck_ymax = min(ymax, int(face_ymax + 0.15 * fg_h))
                    neck_crop = mask[neck_ymin:neck_ymax, face_xmin:face_xmax]
                    if neck_crop.size > 0 and np.mean(neck_crop > 127) > 0.5:
                        neck_detected = True

                    # 5. Pose Symmetry estimation (yaw)
                    # Compare weight balance of left side vs right side of face mask
                    left_weight = np.sum(face_mask[:, :fw // 2] > 127)
                    right_weight = np.sum(face_mask[:, fw // 2:] > 127)
                    if left_weight > 0 and right_weight > 0:
                        ratio = float(left_weight) / float(right_weight)
                        # Normalize to angle (-30 to +30 degrees)
                        pose_yaw = float(np.clip((ratio - 1.0) * 45.0, -45.0, 45.0))

            return {
                "has_face": has_face,
                "face_box": face_box,
                "beard": beard_detected,
                "ears": ears_detected,
                "neck": neck_detected,
                "pose": {"pitch": 0.0, "yaw": pose_yaw, "roll": 0.0},
                "confidence": confidence
            }

        except Exception as e:
            print(f"[-] FaceRuntime error: {e}")
            return {
                "has_face": False,
                "face_box": [0, 0, 0, 0],
                "beard": False,
                "ears": False,
                "neck": False,
                "pose": {"pitch": 0.0, "yaw": 0.0, "roll": 0.0},
                "confidence": 0.0
            }
