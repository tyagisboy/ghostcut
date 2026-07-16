import cv2
import numpy as np

class EdgeClassifier:
    """
    Computes a pixel-wise edge classification map for 10 classes:
    0: Hard
    1: Soft
    2: Hair
    3: Fur
    4: Fabric
    5: Transparent
    6: Reflection
    7: Motion Blur
    8: Shadow
    9: Whisker
    """
    def __init__(self):
        self.edge_classes = [
            "Hard", "Soft", "Hair", "Fur", "Fabric",
            "Transparent", "Reflection", "Motion Blur", "Shadow", "Whisker"
        ]

    def classify_edges(self, img_bgr, mask, material_maps=None):
        """
        Returns a single-channel edge classification map (0 to 9) of shape (H, W).
        If pixel is not on an edge, it is assigned -1.
        """
        h, w = mask.shape[:2]
        
        # Calculate transition edge zone
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
        dilated = cv2.dilate(mask, kernel)
        eroded = cv2.erode(mask, kernel)
        edge_mask = (dilated > 5) & (eroded < 250)
        
        # Initialize default to -1 (non-edge)
        edge_map = np.full((h, w), -1, dtype=np.int8)
        
        if not np.any(edge_mask):
            return edge_map
            
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
        
        # Sobel Gradients
        sobelx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        grad_mag = np.sqrt(sobelx**2 + sobely**2)
        
        # Laplacian local variance to detect details
        lap = cv2.Laplacian(gray, cv2.CV_32F)
        lap_abs = np.abs(lap)
        local_std = cv2.boxFilter(lap_abs, -1, (7, 7))
        
        # Motion blur check: ratio of min/max gradient direction variance
        # (Uniform blurry edges have specific low gradient magnitude but wide width)
        
        # If material maps are provided, use them as priors (resized to match shape)
        if material_maps is not None:
            # Material maps is shape (H, W, 12)
            skin_prob = material_maps[:, :, 0]
            hair_prob = material_maps[:, :, 1]
            fur_prob = material_maps[:, :, 2]
            fabric_prob = material_maps[:, :, 3]
            glass_prob = material_maps[:, :, 4]
            metal_prob = material_maps[:, :, 6]
        else:
            skin_prob = np.zeros((h, w), dtype=np.float32)
            hair_prob = np.zeros((h, w), dtype=np.float32)
            fur_prob = np.zeros((h, w), dtype=np.float32)
            fabric_prob = np.zeros((h, w), dtype=np.float32)
            glass_prob = np.zeros((h, w), dtype=np.float32)
            metal_prob = np.zeros((h, w), dtype=np.float32)
            
        # Classify each pixel in the edge mask
        # 1. Hair/Fur (High texture and matching material probability)
        is_hair = edge_mask & ((hair_prob > 0.1) | ((local_std > 20.0) & (skin_prob > 0.05)))
        is_fur = edge_mask & ((fur_prob > 0.1) | ((local_std > 22.0) & (hair_prob == 0)))
        
        # 2. Whisker: very high local std in thin lines near pet fur edges
        is_whisker = edge_mask & (local_std > 35.0) & (fur_prob > 0.05)
        
        # 3. Transparent / Reflection: glass/metal boundaries
        is_transparent = edge_mask & (glass_prob > 0.1) & (grad_mag < 25.0)
        is_reflection = edge_mask & (metal_prob > 0.1) & (grad_mag > 15.0)
        
        # 4. Fabric
        is_fabric = edge_mask & (fabric_prob > 0.1) & (local_std < 15.0)
        
        # 5. Motion Blur / Shadow: very low gradient magnitude inside a wide transition zone
        # We can find wide transition zones using a larger distance transform
        dist_mask = cv2.distanceTransform(edge_mask.astype(np.uint8), cv2.DIST_L2, 3)
        is_motion_blur = edge_mask & (grad_mag < 10.0) & (dist_mask > 3.0)
        is_shadow = edge_mask & (grad_mag < 15.0) & (gray < 75.0) & (dist_mask > 2.0)
        
        # 6. Hard vs Soft
        is_hard = edge_mask & (grad_mag > 35.0) & (local_std < 10.0)
        is_soft = edge_mask & (grad_mag <= 35.0)
        
        # Assign values (ordered by priority, later writes overwrite)
        edge_map[edge_mask] = 1  # Default Soft
        edge_map[is_hard] = 0
        edge_map[is_fabric] = 4
        edge_map[is_shadow] = 8
        edge_map[is_motion_blur] = 7
        edge_map[is_transparent] = 5
        edge_map[is_reflection] = 6
        edge_map[is_hair] = 2
        edge_map[is_fur] = 3
        edge_map[is_whisker] = 9
        
        return edge_map
