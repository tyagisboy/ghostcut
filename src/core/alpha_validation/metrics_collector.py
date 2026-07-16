import numpy as np
import cv2

class AlphaMetricsCollector:
    """
    Computes comparative metrics: Boundary IoU, SAD, MSE, Connectivity error,
    Gradient error, Halo Width, Smoothness, and Detail Preservation.
    """
    def __init__(self):
        pass

    @staticmethod
    def calculate_sad(alpha: np.ndarray, gt: np.ndarray) -> float:
        a_f = alpha.astype(np.float32) / 255.0
        gt_f = gt.astype(np.float32) / 255.0
        return float(np.sum(np.abs(a_f - gt_f)))

    @staticmethod
    def calculate_mse(alpha: np.ndarray, gt: np.ndarray) -> float:
        a_f = alpha.astype(np.float32) / 255.0
        gt_f = gt.astype(np.float32) / 255.0
        return float(np.mean((a_f - gt_f) ** 2))

    @staticmethod
    def calculate_boundary_iou(alpha: np.ndarray, gt: np.ndarray) -> float:
        kernel = cv2.getStructuringElement(cv2.MORPH_RECT, (5, 5))
        gt_dilate = cv2.dilate(gt, kernel)
        gt_erode = cv2.erode(gt, kernel)
        boundary_zone = (gt_dilate > 0) & (gt_erode == 0)
        
        if np.sum(boundary_zone) > 0:
            pred_bin = (alpha > 127) & boundary_zone
            gt_bin = (gt > 127) & boundary_zone
            intersection = np.sum(pred_bin & gt_bin)
            union = np.sum(pred_bin | gt_bin)
            return float(intersection / union) if union > 0 else 1.0
        return 1.0

    @staticmethod
    def calculate_connectivity(alpha: np.ndarray, gt: np.ndarray) -> float:
        _, pred_labels = cv2.connectedComponents((alpha > 127).astype(np.uint8))
        _, gt_labels = cv2.connectedComponents((gt > 127).astype(np.uint8))
        return float(abs(np.max(pred_labels) - np.max(gt_labels)))

    @staticmethod
    def calculate_gradient_error(alpha: np.ndarray, gt: np.ndarray) -> float:
        pred_grad = cv2.Sobel(alpha.astype(np.float32)/255.0, cv2.CV_32F, 1, 1, ksize=3)
        gt_grad = cv2.Sobel(gt.astype(np.float32)/255.0, cv2.CV_32F, 1, 1, ksize=3)
        return float(np.sum((pred_grad - gt_grad) ** 2))

    @staticmethod
    def calculate_halo_width(alpha: np.ndarray, gt: np.ndarray) -> float:
        halo_mask = (alpha > 5) & (alpha < 250)
        return float(np.sum(halo_mask) / float(alpha.shape[0]))

    @staticmethod
    def calculate_smoothness(alpha: np.ndarray) -> float:
        grad_x = cv2.Sobel(alpha, cv2.CV_32F, 1, 0, ksize=3)
        grad_y = cv2.Sobel(alpha, cv2.CV_32F, 0, 1, ksize=3)
        grad_mag = np.sqrt(grad_x**2 + grad_y**2)
        return float(1.0 - (np.mean(grad_mag) / 255.0))

    @staticmethod
    def calculate_detail_preservation(alpha: np.ndarray, gt: np.ndarray) -> float:
        # Measures correlation of high frequency edges between alpha and ground truth
        lap_alpha = cv2.Laplacian(alpha, cv2.CV_32F)
        lap_gt = cv2.Laplacian(gt, cv2.CV_32F)
        correlation = np.corrcoef(lap_alpha.flatten(), lap_gt.flatten())[0, 1]
        return float(correlation) if not np.isnan(correlation) else 1.0
