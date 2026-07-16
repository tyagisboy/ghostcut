import cv2
import numpy as np

def classify_hair_type(img_bgr, mask, features):
    """
    Classifies hair edge patterns to dynamically adjust matting strategies.
    Returns: 'straight', 'wavy', 'loose_curl', 'tight_curl', 'afro', 'frizzy', 'wet', 'flyaway', 'backlit', or 'general'
    """
    if mask is None:
        return 'general'
        
    h, w = img_bgr.shape[:2]
    small_mask = cv2.resize(mask, (256, 256))
    small_img = cv2.resize(img_bgr, (256, 256))
    
    # Locate transition region around hair/fur
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (15, 15))
    dilated = cv2.dilate(small_mask, kernel)
    eroded = cv2.erode(small_mask, kernel)
    transition = ((dilated > 50) & (eroded < 200)).astype(np.uint8)
    
    if cv2.countNonZero(transition) == 0:
        return 'general'
        
    gray = cv2.cvtColor(small_img, cv2.COLOR_BGR2GRAY)
    
    # Calculate descriptors inside transition zone
    trans_gray = gray[transition > 0]
    if len(trans_gray) == 0:
        return 'general'
        
    # 1. Backlit: check for bright highlights on edge (luminance near 255)
    mean_val = np.mean(trans_gray)
    std_val = np.std(trans_gray)
    p90 = np.percentile(trans_gray, 90)
    if p90 > 230 and mean_val > 150:
        return 'backlit'
        
    # 2. Wet hair: generally low mean luminance and low standard deviation in edge zone
    if mean_val < 70 and std_val < 30:
        return 'wet'
        
    # Compute Sobel gradients in transition region
    sobelx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    
    # Crop to transition zone
    gx = sobelx[transition > 0]
    gy = sobely[transition > 0]
    
    angles = np.arctan2(gy, gx) * 180 / np.pi
    angles[angles < 0] += 180
    
    # Gradient direction histogram entropy
    hist_angles, _ = np.histogram(angles, bins=18, range=(0, 180))
    hist_angles = hist_angles.astype(np.float32) / (hist_angles.sum() + 1e-7)
    angle_entropy = -np.sum(hist_angles * np.log2(hist_angles + 1e-7))
    
    # Laplacian variance inside transition zone (high texture complexity)
    lap = cv2.Laplacian(gray, cv2.CV_32F)
    lap_trans = np.var(lap[transition > 0])
    
    # 3. Flyaway hair check: look for Canny edges in the outer dilated zone
    canny = cv2.Canny(gray, 30, 100)
    outer_zone = ((dilated > 50) & (small_mask < 20)).astype(np.uint8)
    outer_edges = np.count_nonzero(canny[outer_zone > 0]) if np.count_nonzero(outer_zone) > 0 else 0
    if outer_edges > 150:
        return 'flyaway'
        
    # Classify by entropy and lap_trans variance
    if angle_entropy < 2.5:
        # Heavily aligned gradients = Straight hair
        return 'straight'
    elif lap_trans > 2500:
        if angle_entropy > 3.6:
            # Extreme multi-directional texture = Afro
            return 'afro'
        else:
            # Very curly high-frequency = Tight Curl or Frizzy
            return 'tight_curl'
    elif lap_trans > 1200:
        return 'loose_curl'
    elif lap_trans > 600:
        return 'wavy'
        
    return 'general'


def classify_materials(img_bgr, mask, features):
    """
    Classifies the dominant material category of the subject to guide spatial repair.
    Returns: 'hair', 'fur', 'fabric', 'lace', 'feather', 'glass', 'plastic', 'jewelry', 'metal', or 'general'
    """
    if mask is None:
        return 'general'
        
    # Quick checks based on image features
    lap_var = features.get("laplacian_var", 0.0)
    bg_var = features.get("bg_var", 0.0)
    std_color = (features.get("std_b", 0.0) + features.get("std_g", 0.0) + features.get("std_r", 0.0)) / 3.0
    
    h, w = img_bgr.shape[:2]
    small_mask = cv2.resize(mask, (128, 128))
    small_img = cv2.resize(img_bgr, (128, 128))
    
    gray = cv2.cvtColor(small_img, cv2.COLOR_BGR2GRAY)
    
    # 1. Glass/Plastic check: Check for transparency features in transition region
    # Low dynamic range edges but gradient highlights present
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (9, 9))
    dilated = cv2.dilate(small_mask, kernel)
    eroded = cv2.erode(small_mask, kernel)
    transition = ((dilated > 50) & (eroded < 200)).astype(np.uint8)
    
    if cv2.countNonZero(transition) > 0:
        trans_gray = gray[transition > 0]
        # Check standard deviation inside transition: glass/plastic tends to have very smooth regions
        trans_std = np.std(trans_gray)
        if trans_std < 18.0 and features.get("aspect_ratio", 1.0) < 1.3:
            return 'glass'
            
    # 2. Jewelry/Metal check: look for high specular highlights
    high_highlights = np.count_nonzero(gray > 248)
    if high_highlights > 50 and lap_var > 1500.0:
        return 'jewelry'
        
    # 3. Feather/Lace check: high-frequency interior details
    interior = (small_mask > 200).astype(np.uint8)
    if cv2.countNonZero(interior) > 0:
        lap = cv2.Laplacian(gray, cv2.CV_32F)
        int_lap_var = np.var(lap[interior > 0])
        if int_lap_var > 3500:
            return 'lace'
        elif int_lap_var > 2000:
            return 'feather'
            
    return 'general'


def classify_edge_pixels(img_bgr, mask, scale_factor=1.0):
    """
    Computes a pixel-wise edge classification map:
    0: Hard Edge (solid, sharp boundary)
    1: Soft Edge (transparency, slow gradients)
    2: Hair/Fur Details (high frequency flyaways)
    3: Background/Foreground (non-edge pixels)
    """
    h, w = mask.shape[:2]
    
    # Morphological boundary detection
    k_size = max(5, int(5 * scale_factor))
    if k_size % 2 == 0:
        k_size += 1
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k_size, k_size))
    
    dilated = cv2.dilate(mask, kernel)
    eroded = cv2.erode(mask, kernel)
    edge_zone = (dilated > 0) & (eroded < 255)
    
    # Initialize all as background/foreground (3)
    edge_map = np.full((h, w), 3, dtype=np.uint8)
    
    if not np.any(edge_zone):
        return edge_map
        
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    
    # Compute high frequency information (Laplacian local variance)
    lap = cv2.Laplacian(gray, cv2.CV_32F)
    lap_abs = np.abs(lap)
    
    # Local texture variance filter
    local_std = cv2.boxFilter(lap_abs, -1, (7, 7))
    
    # Segment boundaries
    edge_map[edge_zone & (local_std > 20.0)] = 2  # Hair/Fur detail
    edge_map[edge_zone & (local_std <= 20.0) & (local_std > 5.0)] = 1  # Soft Edge
    edge_map[edge_zone & (local_std <= 5.0)] = 0  # Hard Edge
    
    return edge_map
