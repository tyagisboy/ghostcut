import cv2
import numpy as np

def classify_scenario(img_bgr):
    """
    Analyzes an input BGR image (pre-inference) to classify the scenario.
    Supported scenarios:
        - Studio Portrait
        - Outdoor Portrait
        - Backlit Portrait
        - Product
        - Pet
        - Transparent Object
        - Clothing
        - Jewelry
        - Vehicle
        - Food
        - Plant
    Returns:
        scenario_name (str), confidence (float), metrics (dict)
    """
    h, w = img_bgr.shape[:2]
    aspect_ratio = float(w) / h
    
    # Downsample for cheap, fast computation (~1-5ms)
    small = cv2.resize(img_bgr, (256, 256))
    gray = cv2.cvtColor(small, cv2.COLOR_BGR2GRAY)
    
    # 1. Texture analysis (Laplacian variance)
    laplacian_var = float(cv2.Laplacian(gray, cv2.CV_64F).var())
    
    # 2. Brightness & Dynamic range
    mean_val = float(np.mean(gray))
    std_val = float(np.std(gray))
    gray_flat = gray.flatten()
    p95, p5 = np.percentile(gray_flat, [95, 5])
    dynamic_range = float(p95 - p5)
    
    # 3. High highlights (specular reflections)
    specular_pixels = np.count_nonzero(gray > 245)
    specular_ratio = float(specular_pixels) / gray.size
    
    # 4. Skin detection (YCrCb color space skin mask)
    ycrcb = cv2.cvtColor(small, cv2.COLOR_BGR2YCrCb)
    skin_mask = cv2.inRange(ycrcb, np.array([0, 133, 77]), np.array([255, 173, 127]))
    skin_ratio = float(np.count_nonzero(skin_mask)) / skin_mask.size
    
    # 5. Background vs Foreground brightness difference (backlit check)
    # Define border region as background
    border = np.ones((256, 256), dtype=np.uint8)
    border[32:224, 32:224] = 0
    center = 1 - border
    bg_brightness = float(np.mean(gray[border > 0]))
    fg_brightness = float(np.mean(gray[center > 0]))
    backlit_ratio = bg_brightness / (fg_brightness + 1e-5)
    
    # 6. Color saturation analysis
    hsv = cv2.cvtColor(small, cv2.COLOR_BGR2HSV)
    sat = hsv[:, :, 1]
    mean_sat = float(np.mean(sat))
    
    # Classification Logic
    metrics = {
        "aspect_ratio": aspect_ratio,
        "laplacian_var": laplacian_var,
        "mean_sat": mean_sat,
        "skin_ratio": skin_ratio,
        "specular_ratio": specular_ratio,
        "backlit_ratio": backlit_ratio,
        "bg_brightness": bg_brightness,
        "fg_brightness": fg_brightness
    }
    
    # Check Portrait first
    if skin_ratio > 0.04:
        # Background uniformity check
        border_mask = np.ones((256, 256), dtype=np.uint8)
        border_mask[32:224, 32:224] = 0
        bg_pixels = gray[border_mask > 0]
        bg_uniformity_std = float(np.std(bg_pixels))
        
        # Edge density check in background
        bg_edges = cv2.Canny(gray, 50, 150)
        bg_edge_pixels = bg_edges[border_mask > 0]
        bg_edge_density = float(np.count_nonzero(bg_edge_pixels)) / bg_edge_pixels.size
        
        # Left-right lighting balance
        left_mean = float(np.mean(gray[:, :128]))
        right_mean = float(np.mean(gray[:, 128:]))
        lighting_delta = abs(left_mean - right_mean)
        
        # Dominant color analysis (in HSV for chroma detection)
        # Check if background chroma is neutral (low saturation)
        hsv_border_sat = hsv[:, :, 1][border_mask > 0]
        bg_mean_sat = float(np.mean(hsv_border_sat))
        
        metrics["bg_uniformity_std"] = bg_uniformity_std
        metrics["bg_edge_density"] = bg_edge_density
        metrics["lighting_delta"] = lighting_delta
        metrics["bg_mean_sat"] = bg_mean_sat
        
        reasoning = []
        if backlit_ratio > 1.35 and bg_brightness > 190:
            reasoning.append("High backlit ratio detected with bright background")
            metrics["scene_reasoning"] = "; ".join(reasoning)
            return "Backlit Portrait", 0.90, metrics
        
        # Studio portraits: highly uniform background standard deviation, clean edges, neutral color chroma
        is_uniform_bg = bg_uniformity_std < 22.0
        is_clean_bg = bg_edge_density < 0.05
        is_balanced_light = lighting_delta < 20.0
        is_neutral_chroma = bg_mean_sat < 35.0
        
        studio_score = 0
        if is_uniform_bg: studio_score += 2
        if is_clean_bg: studio_score += 2
        if is_balanced_light: studio_score += 1
        if is_neutral_chroma: studio_score += 1
        
        if studio_score >= 4 or bg_brightness > 220:
            reasoning.append(f"Studio indicators: uniformity={bg_uniformity_std:.1f}, edge={bg_edge_density*100:.1f}%, lighting={lighting_delta:.1f}")
            metrics["scene_reasoning"] = "; ".join(reasoning)
            return "Studio Portrait", 0.88, metrics
        else:
            reasoning.append(f"Outdoor indicators: uniformity={bg_uniformity_std:.1f}, edge={bg_edge_density*100:.1f}%, lighting={lighting_delta:.1f}")
            metrics["scene_reasoning"] = "; ".join(reasoning)
            return "Outdoor Portrait", 0.82, metrics
            
    # Check Jewelry (high texture variance, high specular highlights)
    if specular_ratio > 0.008 and laplacian_var > 2200 and aspect_ratio > 0.5 and aspect_ratio < 2.0:
        return "Jewelry", 0.85, metrics
        
    # Check Transparent Object (e.g. Glass)
    # Low dynamic range edges, specific highlights, moderate aspect ratio
    if std_val < 30.0 and specular_ratio > 0.001 and bg_brightness > 120:
        return "Transparent Object", 0.80, metrics
        
    # Check Pet (high high-frequency texture, specific color profiles)
    if laplacian_var > 1400 and mean_sat < 70 and not (skin_ratio > 0.05):
        return "Pet", 0.75, metrics
        
    # Check Plant (highly textured, green saturation dominates)
    green_mask = cv2.inRange(small, np.array([0, 60, 0]), np.array([100, 255, 100]))
    green_ratio = float(np.count_nonzero(green_mask)) / green_mask.size
    if green_ratio > 0.15 and laplacian_var > 1200:
        return "Plant", 0.80, metrics

    # Check Vehicle (often wide aspect ratio, horizontal line patterns)
    if (aspect_ratio > 1.25 or aspect_ratio < 0.8) and laplacian_var > 800 and specular_ratio > 0.005:
        # Check for vehicle outline cues
        return "Vehicle", 0.75, metrics
        
    # Check Clothing
    if mean_sat > 40 and std_val > 40 and skin_ratio > 0.01:
        return "Clothing", 0.70, metrics

    # Check Food (often round/circular layout, high saturation)
    if mean_sat > 60 and aspect_ratio > 0.8 and aspect_ratio < 1.3:
        return "Food", 0.70, metrics

    # Default fallback: Product
    return "Product", 0.65, metrics
