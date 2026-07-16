import cv2
import numpy as np

class AdaptiveRadiusFieldGenerator:
    """
    Generates a per-pixel adaptive radius map based on local edge classes,
    material probabilities, texture variance, and confidence maps.
    Fully dynamic and adaptive based on image size/resolution, color variance,
    and local texture complexity.
    """
    def __init__(self):
        pass

    def generate_radius_field(self, mask, edge_map, material_maps=None, texture_std=None):
        """
        Computes a float32 radius map of shape (H, W) dynamically scaled by image resolution and features.
        """
        h, w = mask.shape[:2]
        
        # 1. Compute resolution scale factor dynamically based on diagonal relative to 1200px
        diagonal = np.sqrt(h**2 + w**2)
        scale_factor = max(0.4, min(diagonal / 1200.0, 3.5))
        
        # Initialize default base radius (e.g. 4.0 scaled for generic soft boundaries)
        base_soft = 4.0 * scale_factor
        radius_map = np.full((h, w), base_soft, dtype=np.float32)
        
        # Assign radius based on Edge Classes, scaled by resolution factor:
        # 0: Hard -> 1.5
        # 1: Soft -> 4.0
        # 2: Hair -> 12.0
        # 3: Fur -> 12.0
        # 4: Fabric -> 3.5
        # 5: Transparent -> 8.0
        # 6: Reflection -> 6.0
        # 7: Motion Blur -> 10.0
        # 8: Shadow -> 8.0
        # 9: Whisker -> 15.0
        
        radius_map[edge_map == 0] = 1.5 * scale_factor
        radius_map[edge_map == 1] = 4.0 * scale_factor
        radius_map[edge_map == 4] = 3.5 * scale_factor
        radius_map[edge_map == 6] = 6.0 * scale_factor
        radius_map[edge_map == 8] = 8.0 * scale_factor
        radius_map[edge_map == 7] = 10.0 * scale_factor
        radius_map[edge_map == 5] = 8.0 * scale_factor
        radius_map[edge_map == 2] = 12.0 * scale_factor
        radius_map[edge_map == 3] = 12.0 * scale_factor
        radius_map[edge_map == 9] = 15.0 * scale_factor
        
        # 2. Refine using material probability maps if available
        if material_maps is not None:
            # Material indices: 0=Skin, 1=Hair, 2=Fur, 4=Glass
            hair_prob = material_maps[:, :, 1]
            fur_prob = material_maps[:, :, 2]
            skin_prob = material_maps[:, :, 0]
            glass_prob = material_maps[:, :, 4]
            
            # Blend radius dynamically using probabilities and scale factor
            radius_map = (
                radius_map * (1.0 - hair_prob) + (12.0 * scale_factor) * hair_prob
            )
            radius_map = (
                radius_map * (1.0 - fur_prob) + (12.0 * scale_factor) * fur_prob
            )
            radius_map = (
                radius_map * (1.0 - skin_prob) + (2.0 * scale_factor) * skin_prob
            )
            radius_map = (
                radius_map * (1.0 - glass_prob) + (8.0 * scale_factor) * glass_prob
            )
            
        # 3. Refine using local texture variance (if provided)
        if texture_std is not None:
            # If texture variance is high, slightly expand the radius to capture detail
            high_tex = np.clip((texture_std - 15.0) / 20.0, 0.0, 1.0)
            radius_map = radius_map + high_tex * (3.0 * scale_factor)
            
        # Ensure we don't drop below 0.5 or exceed 45.0
        radius_map = np.clip(radius_map, 0.5, 45.0)
        
        # Apply Gaussian Blur to smooth transitions and avoid hard boundaries/seams in matting
        # Ensure kernel size is odd and depends on image size
        k_size = int(round(15 * scale_factor))
        if k_size % 2 == 0:
            k_size += 1
        k_size = max(5, k_size)
        
        radius_map_smoothed = cv2.GaussianBlur(radius_map, (k_size, k_size), 5.0 * scale_factor)
        
        return radius_map_smoothed
