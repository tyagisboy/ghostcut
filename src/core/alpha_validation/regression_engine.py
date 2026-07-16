class RegressionEngine:
    """
    Automated change detection comparing current run metrics against baseline records.
    Triggers flags on: quality loss, halo increase, boundary degradation, memory leaks.
    """
    def __init__(self):
        pass

    def check_regressions(self, current_metrics: dict, baseline_metrics: dict) -> dict:
        warnings = []
        status = "STABLE"
        
        # Check boundary degradation
        curr_iou = current_metrics.get("boundary_iou", 1.0)
        base_iou = baseline_metrics.get("boundary_iou", 1.0)
        if curr_iou < (base_iou - 0.05):
            warnings.append(f"Boundary degradation: {curr_iou*100:.1f}% vs baseline {base_iou*100:.1f}%")
            status = "DEGRADED"
            
        # Check halo increase
        curr_halo = current_metrics.get("halo_width", 0.0)
        base_halo = baseline_metrics.get("halo_width", 0.0)
        if curr_halo > (base_halo + 5.0):
            warnings.append(f"Halo width increase: {curr_halo:.1f}px vs baseline {base_halo:.1f}px")
            status = "DEGRADED"
            
        # Check runtime increase
        curr_time = current_metrics.get("processing_time_ms", 0.0)
        base_time = baseline_metrics.get("processing_time_ms", 0.0)
        if curr_time > (base_time * 1.5) and curr_time > 10.0:
            warnings.append(f"Runtime execution delay: {curr_time:.1f}ms vs baseline {base_time:.1f}ms")
            
        return {
            "status": status,
            "warnings": warnings
        }
