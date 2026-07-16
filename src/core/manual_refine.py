import cv2
import numpy as np

def apply_lasso_mask(current_mask, points, action="ADD"):
    """
    Modifies the active extraction alpha channel using a drawn polygon matrix.
    action: "ADD" to restore background (make mask 255), "SUB" to erase foreground (make mask 0).
    Robust coordinate clipping is implemented to prevent array overflows.
    """
    if len(points) < 3:
        return current_mask.copy()
        
    h, w = current_mask.shape[:2]
    
    # Clip points to ensure they lie within the mask dimensions
    clipped_points = []
    for pt in points:
        cx = max(0, min(int(pt[0]), w - 1))
        cy = max(0, min(int(pt[1]), h - 1))
        clipped_points.append((cx, cy))
        
    poly_mask = np.zeros(current_mask.shape, dtype=np.uint8)
    cv2.fillPoly(poly_mask, [np.array(clipped_points, dtype=np.int32)], 255)
    
    if action == "ADD":
        return cv2.bitwise_or(current_mask, poly_mask)
    elif action == "SUB":
        return cv2.bitwise_and(current_mask, cv2.bitwise_not(poly_mask))
    return current_mask.copy()

def apply_magic_wand(img, current_mask, seed_point, tolerance, action="ADD"):
    """
    Measures color distance from seed point in Uniform CIELAB color-space.
    Selects adjacent pixels where Delta E <= tolerance.
    action: "ADD" to make mask 255 (restore), "SUB" to make mask 0 (erase).
    Includes boundary validation for the seed coordinates.
    """
    h, w = current_mask.shape[:2]
    sx, sy = int(seed_point[0]), int(seed_point[1])
    
    # Validate seed point boundaries
    if not (0 <= sx < w and 0 <= sy < h):
        return current_mask.copy()
        
    # Convert BGR to Lab color space
    lab = cv2.cvtColor(img, cv2.COLOR_BGR2LAB)
    
    # Mask size must be (h+2) x (w+2) for cv2.floodFill
    ff_mask = np.zeros((h + 2, w + 2), dtype=np.uint8)
    
    # Tolerance for L, A, B channels
    diff = (int(tolerance), int(tolerance), int(tolerance))
    
    # Perform floodFill on the Lab image
    flags = 4 | cv2.FLOODFILL_MASK_ONLY | (255 << 8)
    
    try:
        cv2.floodFill(
            lab, ff_mask, (sx, sy), 255, 
            loDiff=diff, upDiff=diff, flags=flags
        )
    except Exception as e:
        print(f"[-] OpenCV floodFill failed: {e}")
        return current_mask.copy()
    
    # Extract the filled region from the floodFill mask
    region = ff_mask[1:-1, 1:-1]
    
    if action == "ADD":
        return cv2.bitwise_or(current_mask, region)
    elif action == "SUB":
        return cv2.bitwise_and(current_mask, cv2.bitwise_not(region))
    return current_mask.copy()

def apply_grabcut(img, current_mask, rect):
    """
    Performs GrabCut segmentation on a bounding box.
    Returns the updated mask.
    Robustly clips coordinates to image dimensions to prevent OpenCV GrabCut crashes.
    """
    h, w = img.shape[:2]
    x, y, rw, rh = rect
    
    # Clip bounding box coordinates to image dimensions
    x1 = max(0, min(int(x), w - 1))
    y1 = max(0, min(int(y), h - 1))
    x2 = max(0, min(int(x + rw), w))
    y2 = max(0, min(int(y + rh), h))
    
    cx = x1
    cy = y1
    cw = x2 - x1
    ch = y2 - y1
    
    if cw <= 5 or ch <= 5:
        return current_mask.copy()
        
    mask = np.zeros(img.shape[:2], np.uint8)
    bgdModel = np.zeros((1, 65), np.float64)
    fgdModel = np.zeros((1, 65), np.float64)
    
    try:
        # Run GrabCut initialization with rect
        cv2.grabCut(img, mask, (cx, cy, cw, ch), bgdModel, fgdModel, 5, cv2.GC_INIT_WITH_RECT)
    except Exception as e:
        print(f"[-] OpenCV GrabCut failed: {e}")
        return current_mask.copy()
    
    # GC_PR_FGD (probable foreground) & GC_FGD (foreground) set to 255
    grabcut_mask = np.where((mask == cv2.GC_BGD) | (mask == cv2.GC_PR_BGD), 0, 255).astype(np.uint8)
    
    # Combine it with the current mask by replacing the rect area
    new_mask = current_mask.copy()
    roi_mask = np.zeros_like(current_mask)
    roi_mask[cy:cy+ch, cx:cx+cw] = 255
    
    # Clear the old mask inside rect, and bitwise OR with grabcut mask
    new_mask = cv2.bitwise_and(new_mask, cv2.bitwise_not(roi_mask))
    grabcut_roi = cv2.bitwise_and(grabcut_mask, roi_mask)
    new_mask = cv2.bitwise_or(new_mask, grabcut_roi)
    
    return new_mask

def apply_brush_draw(current_mask, center, radius, action="ADD"):
    """
    Draws a standard circular brush stroke to modify the mask.
    action: "ADD" (restore to 255), "SUB" (erase to 0)
    """
    new_mask = current_mask.copy()
    val = 255 if action == "ADD" else 0
    cx = int(center[0])
    cy = int(center[1])
    cv2.circle(new_mask, (cx, cy), int(radius), val, -1)
    return new_mask

def color_guided_filter(img, p, radius, eps=1e-3):
    """
    Fast O(1) 3-channel Color Guided Filter using OpenCV boxFilter.
    img: BGR guide image (normalized to float32 [0, 1])
    p: input channel to be guided (normalized to float32 [0, 1])
    radius: filter radius
    eps: regularization parameter
    """
    # Split guide channels and normalize
    I_b = img[:, :, 0]
    I_g = img[:, :, 1]
    I_r = img[:, :, 2]
    
    r = radius
    
    # Means
    mean_I_r = cv2.boxFilter(I_r, -1, (r, r))
    mean_I_g = cv2.boxFilter(I_g, -1, (r, r))
    mean_I_b = cv2.boxFilter(I_b, -1, (r, r))
    mean_p   = cv2.boxFilter(p,   -1, (r, r))
    
    # Covariances of Ip
    mean_Ip_r = cv2.boxFilter(I_r * p, -1, (r, r))
    mean_Ip_g = cv2.boxFilter(I_g * p, -1, (r, r))
    mean_Ip_b = cv2.boxFilter(I_b * p, -1, (r, r))
    
    cov_Ip_r = mean_Ip_r - mean_I_r * mean_p
    cov_Ip_g = mean_Ip_g - mean_I_g * mean_p
    cov_Ip_b = mean_Ip_b - mean_I_b * mean_p
    
    # Variance/Covariance of I
    var_I_rr = cv2.boxFilter(I_r * I_r, -1, (r, r)) - mean_I_r * mean_I_r + eps
    var_I_rg = cv2.boxFilter(I_r * I_g, -1, (r, r)) - mean_I_r * mean_I_g
    var_I_rb = cv2.boxFilter(I_r * I_b, -1, (r, r)) - mean_I_r * mean_I_b
    var_I_gg = cv2.boxFilter(I_g * I_g, -1, (r, r)) - mean_I_g * mean_I_g + eps
    var_I_gb = cv2.boxFilter(I_g * I_b, -1, (r, r)) - mean_I_g * mean_I_b
    var_I_bb = cv2.boxFilter(I_b * I_b, -1, (r, r)) - mean_I_b * mean_I_b + eps
    
    # Determinant of the covariance matrix
    det = (var_I_rr * (var_I_gg * var_I_bb - var_I_gb * var_I_gb) -
           var_I_rg * (var_I_rg * var_I_bb - var_I_gb * var_I_rb) +
           var_I_rb * (var_I_rg * var_I_gb - var_I_gg * var_I_rb))
    
    # Compute inverse elements (avoid dividing by zero)
    det = np.maximum(det, 1e-6)
    
    inv_rr = var_I_gg * var_I_bb - var_I_gb * var_I_gb
    inv_rg = var_I_gb * var_I_rb - var_I_rg * var_I_bb
    inv_rb = var_I_rg * var_I_gb - var_I_gg * var_I_rb
    inv_gg = var_I_rr * var_I_bb - var_I_rb * var_I_rb
    inv_gb = var_I_rg * var_I_rb - var_I_rr * var_I_gb
    inv_bb = var_I_rr * var_I_gg - var_I_rg * var_I_rg
    
    a_r = (inv_rr * cov_Ip_r + inv_rg * cov_Ip_g + inv_rb * cov_Ip_b) / det
    a_g = (inv_rg * cov_Ip_r + inv_gg * cov_Ip_g + inv_gb * cov_Ip_b) / det
    a_b = (inv_rb * cov_Ip_r + inv_gb * cov_Ip_g + inv_bb * cov_Ip_b) / det
    
    b = mean_p - (a_r * mean_I_r + a_g * mean_I_g + a_b * mean_I_b)
    
    # Filter coefficients
    mean_a_r = cv2.boxFilter(a_r, -1, (r, r))
    mean_a_g = cv2.boxFilter(a_g, -1, (r, r))
    mean_a_b = cv2.boxFilter(a_b, -1, (r, r))
    mean_b   = cv2.boxFilter(b,   -1, (r, r))
    
    # Output
    q = mean_a_r * I_r + mean_a_g * I_g + mean_a_b * I_b + mean_b
    return q

def apply_refine_edge_brush(img, current_mask, stroke_mask, brush_size):
    """
    Applies a local 3-channel color guided filter to refine the transition edges of the mask
    within the region painted by the user (stroke_mask).
    """
    h, w = current_mask.shape[:2]
    
    # Find bounding box of the stroke for performance
    coords = np.argwhere(stroke_mask > 0)
    if coords.size == 0:
        return current_mask.copy()
        
    y1, x1 = coords.min(axis=0)
    y2, x2 = coords.max(axis=0)
    
    # Add padding to bounding box
    radius = max(3, int(brush_size))
    pad = radius * 2
    y1 = max(0, y1 - pad)
    x1 = max(0, x1 - pad)
    y2 = min(h, y2 + pad)
    x2 = min(w, x2 + pad)
    
    # Crop the image, mask, and stroke mask
    img_crop_bgr = img[y1:y2, x1:x2]
    img_crop_lab = cv2.cvtColor(img_crop_bgr, cv2.COLOR_BGR2LAB)
    
    # Apply unsharp masking to the local luminance channel for fine edge detailing
    L = img_crop_lab[:, :, 0].astype(np.float32)
    L_blur = cv2.GaussianBlur(L, (3, 3), 0.5)
    L_sharp = cv2.addWeighted(L, 1.5, L_blur, -0.5, 0)
    img_crop_lab[:, :, 0] = np.clip(L_sharp, 0, 255).astype(np.uint8)
    
    img_crop = img_crop_lab.astype(np.float32) / 255.0
    mask_crop = current_mask[y1:y2, x1:x2].astype(np.float32) / 255.0
    stroke_crop = stroke_mask[y1:y2, x1:x2]
    
    # Perform 3-channel Color Guided Filter locally in LAB space
    q = color_guided_filter(img_crop, mask_crop, radius, eps=1e-3)
    q = np.clip(q * 255.0, 0, 255).astype(np.uint8)
    
    # Update mask crop only inside the brushed region
    new_mask = current_mask.copy()
    new_mask_crop = new_mask[y1:y2, x1:x2]
    idx = (stroke_crop > 0)
    new_mask_crop[idx] = q[idx]
    
    return new_mask

def compress_rle(mask):
    """
    Run-Length Encoding (RLE) compression of single-channel mask.
    Returns (lengths, values, shape).
    """
    flat = mask.flatten()
    n = len(flat)
    if n == 0:
        return np.array([], dtype=np.int32), np.array([], dtype=np.uint8), mask.shape
        
    changes = np.where(flat[:-1] != flat[1:])[0] + 1
    indices = np.concatenate(([0], changes, [n]))
    
    lengths = indices[1:] - indices[:-1]
    values = flat[indices[:-1]]
    
    return lengths.astype(np.int32), values.astype(np.uint8), mask.shape

def decompress_rle(lengths, values, shape):
    """
    Decompresses RLE arrays back to original mask.
    """
    if len(lengths) == 0:
        return np.zeros(shape, dtype=np.uint8)
    flat = np.repeat(values, lengths)
    return flat.reshape(shape)

class HistoryManager:
    """
    LIFO Stack supporting Undo/Redo cycles using compressed RLE bitmasks to save RAM.
    """
    def __init__(self, max_depth=30):
        self.max_depth = max_depth
        self.undo_stack = []
        self.redo_stack = []

    def push_state(self, mask):
        rle_state = compress_rle(mask)
        self.undo_stack.append(rle_state)
        if len(self.undo_stack) > self.max_depth:
            self.undo_stack.pop(0)
        self.redo_stack.clear()

    def undo(self, current_mask):
        if not self.undo_stack:
            return current_mask.copy()
        
        self.redo_stack.append(compress_rle(current_mask))
        rle_prev = self.undo_stack.pop()
        return decompress_rle(*rle_prev)

    def redo(self, current_mask):
        if not self.redo_stack:
            return current_mask.copy()
            
        self.undo_stack.append(compress_rle(current_mask))
        rle_next = self.redo_stack.pop()
        return decompress_rle(*rle_next)
        
    def clear(self):
        self.undo_stack.clear()
        self.redo_stack.clear()
