import cv2
import numpy as np

class ConfidenceEngine:
    """
    Generates confidence maps for various stages of the background removal pipeline:
    - Segmentation Confidence
    - Hair Confidence
    - Fur Confidence
    - Material Confidence
    - Edge Confidence
    - Transparency Confidence
    - Alpha Confidence
    - Reconstruction Confidence
    """
    def __init__(self):
        pass

    def generate_all_confidences(self, img_bgr, mask, material_maps=None, edge_map=None):
        """
        Computes all confidence maps (0.0 to 1.0) and returns a dictionary.
        """
        h, w = mask.shape[:2]
        gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
        
        # 1. Segmentation Confidence (distance from mask boundary)
        dist_fg = cv2.distanceTransform((mask > 200).astype(np.uint8), cv2.DIST_L2, 3)
        dist_bg = cv2.distanceTransform((mask < 50).astype(np.uint8), cv2.DIST_L2, 3)
        max_d = max(1.0, np.max(dist_fg) + np.max(dist_bg))
        seg_conf = np.clip((dist_fg + dist_bg) / (max_d * 0.12), 0.0, 1.0)
        
        # 2. Hair Confidence
        from src.core.segmentation import compute_hair_confidence
        # Texture detail guide
        mean_I = cv2.boxFilter(gray, -1, (7, 7))
        mean_I2 = cv2.boxFilter(gray * gray, -1, (7, 7))
        var_I = mean_I2 - mean_I * mean_I
        std_I = np.sqrt(np.maximum(var_I, 0.0))
        w_detail = np.clip((std_I - 0.02) / 0.06, 0.0, 1.0)
        hair_conf = compute_hair_confidence(img_bgr, mask, w_detail)
        
        # 3. Fur Confidence
        # Similar to hair but check fur probability maps if available
        if material_maps is not None:
            fur_conf = material_maps[:, :, 2]
        else:
            # Fallback
            fur_conf = hair_conf * 0.5  # approximation if fur classifier not run
            
        # 4. Material Confidence
        if material_maps is not None:
            # Sum of max material probabilities inside active zone
            mat_conf = np.max(material_maps, axis=2)
        else:
            mat_conf = np.ones((h, w), dtype=np.float32)
            
        # 5. Edge Confidence
        # Sharp solid edges have high confidence, blurry/halo edges have lower confidence
        sobelx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
        sobely = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
        grad_mag = np.sqrt(sobelx**2 + sobely**2)
        
        # Blurry edge zone check
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
        dilated = cv2.dilate(mask, kernel)
        eroded = cv2.erode(mask, kernel)
        edge_zone = (dilated > 10) & (eroded < 245)
        
        edge_conf = np.ones((h, w), dtype=np.float32)
        if np.any(edge_zone):
            # Low gradient magnitude along mask edge = low confidence edge
            edge_conf[edge_zone] = np.clip(grad_mag[edge_zone] / 15.0, 0.1, 1.0)
            
        # 6. Transparency Confidence
        # High confidence transparent regions (where gradient magnitude is low and std_I is low along the transition boundary)
        trans_conf = np.zeros((h, w), dtype=np.float32)
        if np.any(edge_zone):
            local_grad_std = cv2.boxFilter(grad_mag, -1, (7, 7))
            trans_conf[edge_zone] = np.clip(1.0 - (local_grad_std[edge_zone] * 4.0), 0.0, 1.0)
            
        # 7. Alpha Confidence
        # Binary pixels have 1.0 confidence, intermediate grey pixels have lower confidence
        alpha_norm = mask.astype(np.float32) / 255.0
        alpha_conf = 1.0 - 4.0 * (alpha_norm - 0.5)**2
        alpha_conf = np.clip(1.0 - alpha_conf, 0.0, 1.0)
        
        # 8. Reconstruction Confidence
        # How confident we are in the color decontamination (high where mask is fully solid/bg, lower in transition)
        recon_conf = 1.0 - (edge_zone.astype(np.float32) * 0.5)
        
        return {
            "segmentation_confidence": seg_conf,
            "hair_confidence": hair_conf,
            "fur_confidence": fur_conf,
            "material_confidence": mat_conf,
            "edge_confidence": edge_conf,
            "transparency_confidence": trans_conf,
            "alpha_confidence": alpha_conf,
            "reconstruction_confidence": recon_conf
        }
