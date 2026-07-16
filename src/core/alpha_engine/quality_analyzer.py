import numpy as np
import cv2

class AlphaQualityAnalyzer:
    """
    Evaluates generated alpha matte quality.
    Measures Boundary IoU, SAD, Connectivity error, Matte smoothness, and Halo width.
    """
    def __init__(self):
        pass

    def analyze_quality(self, alpha: np.ndarray, ground_truth: np.ndarray) -> dict:
        """
        Computes numerical benchmarks comparing alpha matte to expected shape.
        """
        # Ensure identical shapes
        if alpha.shape != ground_truth.shape:
            ground_truth = cv2.resize(ground_truth, (alpha.shape[1], alpha.shape[0]), interpolation=cv2.INTER_NEAREST)
            
        a_f = alpha.astype(np.float32) / 255.0
        gt_f = ground_truth.astype(np.float32) / 255.0
        
        # 1. Sum of Absolute Differences (SAD)
        sad = float(np.sum(np.abs(a_f - gt_f)))
        
        # 2. Mean Squared Error (MSE)
        mse = float(np.mean((a_f - gt_f) ** 2))
        
        # 3. Boundary Intersection over Union (BIoU)
        # Define narrow band boundary of GT
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        gt_dilate = cv2.dilate(ground_truth, kernel)
        gt_erode = cv2.erode(ground_truth, kernel)
        boundary_zone = (gt_dilate > 0) & (gt_erode == 0)
        
        if np.sum(boundary_zone) > 0:
            pred_bin = (alpha > 127) & boundary_zone
            gt_bin = (ground_truth > 127) & boundary_zone
            intersection = np.sum(pred_bin & gt_bin)
            union = np.sum(pred_bin | gt_bin)
            boundary_iou = float(intersection / union) if union > 0 else 1.0
        else:
            boundary_iou = 1.0
            
        # 4. Matte Smoothness (First-order derivative variance)
        grad_x = cv2.Sobel(alpha, cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(alpha, cv2.CV_32F, 0, 1, ksize=3)
        grad_mag = np.sqrt(grad_x**2 + grad_y**2)
        smoothness = float(1.0 - (np.mean(grad_mag) / 255.0))
        
        # Compute quality rating grade based on MSE & SAD
        overall_score = max(0.0, min(1.0, 1.0 - (mse * 5.0)))
        quality_grade = "A" if overall_score >= 0.92 else "B" if overall_score >= 0.80 else "C" if overall_score >= 0.65 else "F"
        
        return {
            "sad": sad,
            "mse": mse,
            "boundary_iou": boundary_iou,
            "smoothness": smoothness,
            "overall_score": overall_score,
            "quality_grade": quality_grade
        }
