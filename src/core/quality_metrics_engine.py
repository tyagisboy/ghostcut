import cv2
import numpy as np

class QualityMetricsEngine:
    """
    Computes mathematical quality metrics comparing a segmented alpha matte with ground-truth.
    """
    def __init__(self):
        pass

    def evaluate(self, pred: np.ndarray, gt: np.ndarray) -> dict:
        """
        Calculates quality deltas. pred and gt should be 2D arrays in range [0, 255] or [0, 1].
        """
        # Ensure correct formats and scales
        if pred.max() > 1.0:
            pred = (pred / 255.0).astype(np.float32)
        if gt.max() > 1.0:
            gt = (gt / 255.0).astype(np.float32)

        pred = np.clip(pred, 0.0, 1.0)
        gt = np.clip(gt, 0.0, 1.0)

        # 1. IoU (Intersection over Union)
        intersection = np.sum(pred * gt)
        union = np.sum(pred) + np.sum(gt) - intersection
        iou = float(intersection / (union + 1e-6))

        # 2. SAD (Sum of Absolute Differences)
        sad = float(np.sum(np.abs(pred - gt))) / 1000.0 # scale parameter

        # 3. MSE (Mean Squared Error)
        mse = float(np.mean((pred - gt) ** 2))

        # 4. Boundary IoU (focusing on a 5px band around contours)
        # Create contour dilation
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        gt_boundary = cv2.dilate(gt, kernel) - cv2.erode(gt, kernel)
        pred_boundary = cv2.dilate(pred, kernel) - cv2.erode(pred, kernel)
        
        b_intersect = np.sum(gt_boundary * pred_boundary)
        b_union = np.sum(gt_boundary) + np.sum(pred_boundary) - b_intersect
        boundary_iou = float(b_intersect / (b_union + 1e-6))

        # 5. Gradient Error
        # Calculate Sobel derivatives
        gt_dx = cv2.Sobel(gt, cv2.CV_32F, 1, 0, ksize=3)
        gt_dy = cv2.Sobel(gt, cv2.CV_32F, 0, 1, ksize=3)
        pred_dx = cv2.Sobel(pred, cv2.CV_32F, 1, 0, ksize=3)
        pred_dy = cv2.Sobel(pred, cv2.CV_32F, 0, 1, ksize=3)
        
        gt_grad = np.sqrt(gt_dx**2 + gt_dy**2)
        pred_grad = np.sqrt(pred_dx**2 + pred_dy**2)
        grad_error = float(np.mean((gt_grad - pred_grad) ** 2))

        # 6. Connectivity Error (connected components divergence)
        # Binary thresholding
        gt_bin = (gt > 0.5).astype(np.uint8)
        pred_bin = (pred > 0.5).astype(np.uint8)
        
        _, gt_labels = cv2.connectedComponents(gt_bin)
        _, pred_labels = cv2.connectedComponents(pred_bin)
        
        conn_error = float(np.mean(np.abs(gt_labels - pred_labels))) / 10.0

        # 7. Specialist Preservations (simulated derived scores for detailed textures)
        hair_preservation = float(np.clip(1.0 - (grad_error * 2.0), 0.5, 1.0))
        fur_preservation = float(np.clip(1.0 - (sad / 50.0), 0.5, 1.0))
        transparency_preservation = float(np.clip(1.0 - (mse * 5.0), 0.5, 1.0))
        
        # Halo Width Estimate: distance between boundary contours
        halo_width = float(np.sum(np.abs(gt_boundary - pred_boundary)) / (np.sum(gt_boundary) + 1e-6))

        # F-score on boundary
        f_score = float(2 * boundary_iou / (boundary_iou + 1.0 + 1e-6))

        # Fused overall quality score
        overall_score = float(np.clip((iou * 0.4 + boundary_iou * 0.3 + (1.0 - np.clip(sad/10.0, 0.0, 1.0)) * 0.15 + (1.0 - np.clip(grad_error*10.0, 0.0, 1.0)) * 0.15), 0.0, 1.0))

        return {
            "iou": iou,
            "boundary_iou": boundary_iou,
            "sad": sad,
            "mse": mse,
            "gradient_error": grad_error,
            "connectivity_error": conn_error,
            "boundary_f_score": f_score,
            "halo_width": halo_width,
            "hair_preservation": hair_preservation,
            "fur_preservation": fur_preservation,
            "transparency_preservation": transparency_preservation,
            "overall_score": overall_score
        }
