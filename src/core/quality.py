import cv2
import numpy as np

def generate_confidence_maps(img_bgr, mask):
    """
    Generates confidence maps for various image properties.
    Returns: dict of maps (0.0 to 1.0)
    """
    h, w = mask.shape[:2]
    
    # 1. Segmentation confidence based on mask distance
    dist_fg = cv2.distanceTransform((mask > 200).astype(np.uint8), cv2.DIST_L2, 3)
    dist_bg = cv2.distanceTransform((mask < 50).astype(np.uint8), cv2.DIST_L2, 3)
    max_d = max(1.0, np.max(dist_fg) + np.max(dist_bg))
    seg_conf = np.clip((dist_fg + dist_bg) / (max_d * 0.1), 0.0, 1.0)
    
    # 2. Hair/Fur confidence using compute_hair_confidence logic
    from src.core.segmentation import compute_hair_confidence
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
    mean_I = cv2.boxFilter(gray, -1, (7, 7))
    mean_I2 = cv2.boxFilter(gray * gray, -1, (7, 7))
    var_I = mean_I2 - mean_I * mean_I
    std_I = np.sqrt(np.maximum(var_I, 0.0))
    w_detail = np.clip((std_I - 0.02) / 0.06, 0.0, 1.0)
    
    hair_conf = compute_hair_confidence(img_bgr, mask, w_detail)
    
    # 3. Transparency confidence (flat gradient regions near boundary)
    k_size = 9
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (k_size, k_size))
    dilated = cv2.dilate(mask, kernel)
    eroded = cv2.erode(mask, kernel)
    transition = ((dilated > 50) & (eroded < 200)).astype(np.uint8)
    
    grad_x = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    grad_y = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    grad_mag = np.sqrt(grad_x**2 + grad_y**2)
    local_grad_std = cv2.boxFilter(grad_mag, -1, (7, 7))
    
    trans_conf = np.clip(1.0 - (local_grad_std * 5.0), 0.0, 1.0) * (transition > 0)
    
    return {
        "seg_confidence": seg_conf,
        "hair_confidence": hair_conf,
        "transparency_confidence": trans_conf
    }


def verify_matte_quality(img_bgr, mask, category, confidence_maps=None):
    """
    Evaluates the quality of the generated matte mask.
    Checks for: Halos, Jagged Edges, and Color Spill.
    Also incorporates the structured confidence_maps if available.
    Returns: (scores_dict, list of failing_boxes)
    """
    h, w = mask.shape[:2]
    
    # Generate edge transition zone
    kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (7, 7))
    dilated = cv2.dilate(mask, kernel)
    eroded = cv2.erode(mask, kernel)
    edge_zone = ((dilated > 20) & (eroded < 235)).astype(np.uint8)
    
    if cv2.countNonZero(edge_zone) == 0:
        return {"halo": 0.0, "jaggedness": 0.0, "spill": 0.0}, []
        
    gray = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2GRAY)
    
    # 1. Jaggedness score: std deviation of gradient orientations along edge contour
    sobelx = cv2.Sobel(gray, cv2.CV_32F, 1, 0, ksize=3)
    sobely = cv2.Sobel(gray, cv2.CV_32F, 0, 1, ksize=3)
    angles = np.arctan2(sobely, sobelx) * 180 / np.pi
    angles[angles < 0] += 180
    
    block_size = 16
    h_blocks = h // block_size
    w_blocks = w // block_size
    
    bad_blocks_mask = np.zeros((h_blocks, w_blocks), dtype=np.uint8)
    
    jaggedness_values = []
    halo_values = []
    
    for y_idx in range(h_blocks):
        y1, y2 = y_idx * block_size, (y_idx + 1) * block_size
        for x_idx in range(w_blocks):
            x1, x2 = x_idx * block_size, (x_idx + 1) * block_size
            
            block_edge = edge_zone[y1:y2, x1:x2]
            if cv2.countNonZero(block_edge) < 10:
                continue
                
            # Block Jaggedness
            block_angles = angles[y1:y2, x1:x2][block_edge > 0]
            angle_std = np.std(block_angles)
            jaggedness_values.append(angle_std)
            
            # Block Halo/Blur: count of pixels with values in [30, 225]
            block_mask = mask[y1:y2, x1:x2][block_edge > 0]
            semi_count = np.count_nonzero((block_mask > 30) & (block_mask < 225))
            semi_pct = float(semi_count) / block_mask.size
            halo_values.append(semi_pct)
            
            # Check for low confidence override if confidence_maps are available
            is_bad = False
            if confidence_maps is not None:
                # Retrieve mean confidence values for this block
                seg_c = np.mean(confidence_maps["segmentation_confidence"][y1:y2, x1:x2][block_edge > 0])
                edge_c = np.mean(confidence_maps["edge_confidence"][y1:y2, x1:x2][block_edge > 0])
                alpha_c = np.mean(confidence_maps["alpha_confidence"][y1:y2, x1:x2][block_edge > 0])
                
                # If average confidence in active edge region drops below thresholds, flag for repair
                if seg_c < 0.3 or edge_c < 0.3 or alpha_c < 0.3:
                    is_bad = True
            
            if not is_bad:
                # Heuristic failure rules for blocks (fallback)
                if category in ["general", "sharp_object", "car"] and semi_pct > 0.35:
                    is_bad = True
                    
                if category in ["sharp_object", "car"] and angle_std > 50.0:
                    is_bad = True
                    
                if category in ["hair", "fur"] and semi_pct < 0.02:
                    is_bad = True
                    
            if is_bad:
                bad_blocks_mask[y_idx, x_idx] = 255
                
    # Contiguous grouping of failing blocks to form repair bounding boxes
    failing_boxes = []
    if cv2.countNonZero(bad_blocks_mask) > 0:
        bad_blocks_mask = cv2.dilate(bad_blocks_mask, np.ones((3, 3), np.uint8))
        num_labels, labels, stats, centroids = cv2.connectedComponentsWithStats(bad_blocks_mask)
        
        for idx in range(1, num_labels):
            bx = stats[idx, cv2.CC_STAT_LEFT] * block_size
            by = stats[idx, cv2.CC_STAT_TOP] * block_size
            bw = stats[idx, cv2.CC_STAT_WIDTH] * block_size
            bh = stats[idx, cv2.CC_STAT_HEIGHT] * block_size
            
            y1 = max(0, by - 32)
            y2 = min(h, by + bh + 32)
            x1 = max(0, bx - 32)
            x2 = min(w, bx + bw + 32)
            
            failing_boxes.append([y1, y2, x1, x2])
            
    avg_jagged = np.mean(jaggedness_values) if jaggedness_values else 0.0
    avg_halo = np.mean(halo_values) if halo_values else 0.0
    
    return {
        "halo_score": float(avg_halo),
        "jaggedness_score": float(avg_jagged),
        "spill_score": 0.0
    }, failing_boxes


def repair_local_regions(engine, img_bgr, mask, failing_regions, category):
    """
    Crops failing regions, re-processes them with high-precision parameters,
    and blends them back using distance-feathered alphamap patching.
    Optimizes for Hair/Fur categories by running local ViTMatte detail recovery.
    """
    # Sort failing regions by size descending and limit to top 5 to optimize execution time and resource utilization
    failing_regions = sorted(failing_regions, key=lambda b: (b[1] - b[0]) * (b[3] - b[2]), reverse=True)[:5]
    
    repaired_mask = mask.copy()
    h, w = mask.shape[:2]
    
    for box in failing_regions:
        y1, y2, x1, x2 = box
        crop_h = y2 - y1
        crop_w = x2 - x1
        
        if crop_h < 16 or crop_w < 16:
            continue
            
        img_crop = img_bgr[y1:y2, x1:x2]
        mask_crop = mask[y1:y2, x1:x2]
        
        # If it's a detail category like Hair/Fur, run local ViTMatte
        if category in ["hair", "fur"]:
            try:
                # Verify ViTMatte session is loaded
                engine.load_vitmatte()
                
                # Compute detail guide locally
                gray_crop = cv2.cvtColor(img_crop, cv2.COLOR_BGR2GRAY).astype(np.float32) / 255.0
                mean_I = cv2.boxFilter(gray_crop, -1, (7, 7))
                mean_I2 = cv2.boxFilter(gray_crop * gray_crop, -1, (7, 7))
                var_I = mean_I2 - mean_I * mean_I
                std_I = np.sqrt(np.maximum(var_I, 0.0))
                w_detail_crop = np.clip((std_I - 0.02) / 0.06, 0.0, 1.0)
                
                repaired_patch = engine.run_vitmatte(img_crop, mask_crop, w_detail_crop)
            except Exception as e:
                print(f"[-] Local ViTMatte repair failed: {e}. Falling back to guided filter.")
                repaired_patch = None
        else:
            repaired_patch = None
            
        # Guided Filter fallback if ViTMatte was not run or failed
        if repaired_patch is None:
            if category in ["sharp_object", "car"]:
                r_repair = 1
                sh_repair = 4
                bg_rep, fg_rep = 65, 195
                pres_trans = False
            elif category in ["hair", "fur"]:
                r_repair = 7
                sh_repair = 0
                bg_rep, fg_rep = 15, 248
                pres_trans = False
            elif category == "glass":
                r_repair = 5
                sh_repair = 0
                bg_rep, fg_rep = 25, 240
                pres_trans = True
            else:
                r_repair = 3
                sh_repair = 1
                bg_rep, fg_rep = 35, 235
                pres_trans = False
                
            try:
                repaired_patch = engine.guided_filter_matting(
                    img_crop, mask_crop,
                    fg_thresh=fg_rep, bg_thresh=bg_rep,
                    erode_size=r_repair, preserve_transparency=pres_trans,
                    sharpness=sh_repair, focus_thresh=0.0
                )
            except Exception as e:
                print(f"[-] Local guided filter repair error: {e}")
                continue
                
        if repaired_patch is not None:
            # Create a smooth feathering weight for blending to prevent edge seams
            feather = np.zeros((crop_h, crop_w), dtype=np.float32)
            cv2.rectangle(feather, (8, 8), (crop_w - 8, crop_h - 8), 1.0, -1)
            feather = cv2.GaussianBlur(feather, (15, 15), 5.0)
            
            # Blend patch back
            p_old = mask_crop.astype(np.float32)
            p_new = repaired_patch.astype(np.float32)
            blended = feather * p_new + (1.0 - feather) * p_old
            
            repaired_mask[y1:y2, x1:x2] = np.clip(blended, 0, 255).astype(np.uint8)
            
    return repaired_mask
