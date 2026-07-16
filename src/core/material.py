import cv2
import numpy as np

class MaterialClassifier:
    """
    Computes material probability maps and confidence scores for 12 materials:
    Skin, Hair, Fur, Fabric, Glass, Plastic, Metal, Leather, Feather, Lace, Water, Smoke.
    """
    def __init__(self):
        self.materials = [
            "Skin", "Hair", "Fur", "Fabric", "Glass", "Plastic",
            "Metal", "Leather", "Feather", "Lace", "Water", "Smoke"
        ]

    def compute_material_maps(self, img_bgr, mask):
        """
        Generates pixel-wise probability maps of shape (H, W, 12) for each material,
        along with a summary dictionary of average material confidence scores.
        """
        h, w = mask.shape[:2]
        num_mats = len(self.materials)
        
        # Initialize probability maps to zeros
        prob_maps = np.zeros((h, w, num_mats), dtype=np.float32)
        
        # Downscale for performance if image is very large
        scale = 1.0
        if max(h, w) > 512:
            scale = 512.0 / max(h, w)
            img_small = cv2.resize(img_bgr, (0, 0), fx=scale, fy=scale)
            mask_small = cv2.resize(mask, (0, 0), fx=scale, fy=scale)
        else:
            img_small = img_bgr.copy()
            mask_small = mask.copy()
            
        sh, sw = mask_small.shape[:2]
        
        # Compute color spaces
        ycrcb = cv2.cvtColor(img_small, cv2.COLOR_BGR2YCrCb)
        hsv = cv2.cvtColor(img_small, cv2.COLOR_BGR2HSV)
        gray = cv2.cvtColor(img_small, cv2.COLOR_BGR2GRAY)
        
        # Compute texture maps
        lap = cv2.Laplacian(gray, cv2.CV_32F)
        lap_abs = np.abs(lap)
        lap_var = cv2.boxFilter(lap_abs, -1, (9, 9))
        
        # Gradient magnitude
        sobelx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        grad_mag = np.sqrt(sobelx**2 + sobely**2)
        grad_var = cv2.boxFilter(grad_mag, -1, (9, 9))
        
        # Binary transition zone
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        dilated = cv2.dilate(mask_small, kernel)
        eroded = cv2.erode(mask_small, kernel)
        transition = ((dilated > 10) & (eroded < 245)).astype(np.float32)
        foreground = (mask_small > 150).astype(np.float32)
        active_zone = (dilated > 5).astype(np.uint8)
        
        # 1. Skin
        # YCrCb color range detector
        skin_mask = cv2.inRange(ycrcb, np.array([0, 133, 77]), np.array([255, 173, 127]))
        skin_prob = (skin_mask.astype(np.float32) / 255.0) * (foreground + 0.5 * transition)
        
        # 2. Hair
        # High texture variance + located in the upper parts of the foreground mask
        y_coords, x_coords = np.indices((sh, sw))
        vertical_weight = np.clip(1.2 - (y_coords.astype(np.float32) / sh), 0.0, 1.0)
        hair_texture = np.clip((lap_var - 5.0) / 30.0, 0.0, 1.0)
        hair_prob = hair_texture * vertical_weight * (transition + 0.3 * foreground)
        
        # 3. Fur
        # High texture variance along the transition zone of non-human subjects
        fur_texture = np.clip((lap_var - 8.0) / 40.0, 0.0, 1.0)
        # Pet transition border
        fur_prob = fur_texture * (transition + 0.1 * foreground)
        # Reduce skin overlap
        fur_prob = np.clip(fur_prob - skin_prob, 0.0, 1.0)
        
        # 4. Fabric
        # Low-to-medium texture variance, uniform color, inside foreground
        fabric_prob = np.clip(1.0 - (lap_var / 15.0), 0.0, 1.0) * foreground
        fabric_prob = np.clip(fabric_prob - skin_prob - hair_prob, 0.0, 1.0)
        
        # 5. Glass
        # Smooth interior (low lap_var), low saturation, high brightness
        sat_small = hsv[:, :, 1]
        val_small = hsv[:, :, 2]
        glass_prob = np.clip(1.0 - (sat_small / 30.0), 0.0, 1.0) * np.clip(1.0 - (lap_var / 10.0), 0.0, 1.0) * (foreground + transition)
        glass_prob = glass_prob * (val_small > 100).astype(np.float32)
        
        # 6. Plastic
        # Similar to glass but more opaque (higher dynamic range of interior)
        plastic_prob = np.clip(1.0 - (sat_small / 50.0), 0.0, 1.0) * np.clip(1.0 - (lap_var / 20.0), 0.0, 1.0) * foreground
        plastic_prob = np.clip(plastic_prob - glass_prob, 0.0, 1.0)
        
        # 7. Metal
        # High specular highlights + low saturation
        specular = (val_small > 235).astype(np.float32)
        metal_prob = specular * np.clip(1.0 - (sat_small / 40.0), 0.0, 1.0) * (foreground + transition)
        
        # 8. Leather
        # Moderate texture, low-mid saturation, brown/dark hues
        hue_small = hsv[:, :, 0]
        brown_hue = ((hue_small >= 5) & (hue_small <= 20)).astype(np.float32)
        dark_val = (val_small < 100).astype(np.float32)
        leather_prob = brown_hue * dark_val * foreground
        
        # 9. Feather
        # Highly directional fine texture patterns
        feather_prob = np.clip((lap_var - 25.0) / 50.0, 0.0, 1.0) * (transition + foreground)
        feather_prob = np.clip(feather_prob - hair_prob - skin_prob, 0.0, 1.0)
        
        # 10. Lace
        # Extremely high gradient transitions inside foreground, high binary variance
        lace_prob = np.clip((grad_var - 15.0) / 45.0, 0.0, 1.0) * (foreground + transition)
        lace_prob = np.clip(lace_prob - skin_prob - hair_prob, 0.0, 1.0)
        
        # 11. Water
        # High brightness highlights + blue/cyan colors
        blue_hue = ((hue_small >= 80) & (hue_small <= 130)).astype(np.float32)
        water_prob = blue_hue * (val_small > 150).astype(np.float32) * (foreground + transition)
        
        # 12. Smoke
        # Extremely soft transition boundary, very low gradient values
        smoke_prob = np.clip(1.0 - (grad_mag / 8.0), 0.0, 1.0) * (mask_small > 10) * (mask_small < 240)
        
        # Map values back to full scale
        prob_small = np.zeros((sh, sw, num_mats), dtype=np.float32)
        prob_small[:, :, 0] = skin_prob
        prob_small[:, :, 1] = hair_prob
        prob_small[:, :, 2] = fur_prob
        prob_small[:, :, 3] = fabric_prob
        prob_small[:, :, 4] = glass_prob
        prob_small[:, :, 5] = plastic_prob
        prob_small[:, :, 6] = metal_prob
        prob_small[:, :, 7] = leather_prob
        prob_small[:, :, 8] = feather_prob
        prob_small[:, :, 9] = lace_prob
        prob_small[:, :, 10] = water_prob
        prob_small[:, :, 11] = smoke_prob
        
        # Apply mask constraints (only keep where foreground or transition exists)
        for i in range(num_mats):
            prob_small[:, :, i] = np.clip(prob_small[:, :, i] * (active_zone > 0), 0.0, 1.0)
            
        # Resize to original resolution
        if scale != 1.0:
            prob_maps = cv2.resize(prob_small, (w, h), interpolation=cv2.INTER_LINEAR)
        else:
            prob_maps = prob_small
            
        # Ensure outputs are shape (H, W, 12) even if single-channel maps are resized
        if prob_maps.ndim == 2:
            prob_maps = np.expand_dims(prob_maps, axis=-1)
            
        # Compute average confidence values inside active zone
        confidences = {}
        active_pixels = np.count_nonzero(active_zone)
        if active_pixels > 0:
            for idx, mat in enumerate(self.materials):
                conf_val = float(np.sum(prob_small[:, :, idx])) / active_pixels
                confidences[mat] = float(np.clip(conf_val * 3.0, 0.0, 1.0)) # scale for visibility
        else:
            for mat in self.materials:
                confidences[mat] = 0.0
                
        return prob_maps, confidences
