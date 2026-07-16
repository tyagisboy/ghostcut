import numpy as np

class SelfCriticEngine:
    """
    Cognitive Self-Critic layer verifying final outputs before export.
    Flags defects (e.g., halo, spill, discontinuities) and identifies repair priority zones.
    """
    def __init__(self):
        pass

    def criticize(self, alpha_mask: np.ndarray, quality_metrics: dict, belief_graph: dict = None) -> dict:
        """
        Inputs:
            alpha_mask: The final post-matting mask
            quality_metrics: Evaluated quality scores from Quality SDK runtimes
            belief_graph: Hierarchical beliefs dictionary
        Returns:
            quality_grade: str (A, B, C, D)
            failures: list of warning strings
            repair_regions: list of dict suggestions
        """
        failures = []
        repair_regions = []

        edge_score = quality_metrics.get("edge_score", 1.0)
        alpha_score = quality_metrics.get("alpha_score", 1.0)
        stability_score = quality_metrics.get("stability_score", 1.0)
        halo_score = quality_metrics.get("halo_spill_score", 1.0)
        trans_score = quality_metrics.get("transparency_score", 1.0)
        consistency_score = quality_metrics.get("consistency_score", 1.0)

        # 1. Criticize Edge quality
        if edge_score < 0.85:
            failures.append(f"Edge jaggedness/leakage detected (Score: {edge_score*100:.1f}%)")
            
        # 2. Criticize Alpha transitions
        if alpha_score < 0.85:
            failures.append(f"Matte clipping / blur expansion detected (Score: {alpha_score*100:.1f}%)")
            
        # 3. Criticize Stability
        if stability_score < 0.95:
            failures.append(f"Stability defects (floating pixels or micro-holes) found in solid mask (Score: {stability_score*100:.1f}%)")

            
        # 4. Criticize Halo & Spill
        if halo_score < 0.85:
            failures.append(f"Chromatic background color spill or halo rings detected (Score: {halo_score*100:.1f}%)")
            
        # 5. Criticize Transparency
        if trans_score < 0.90:
            failures.append(f"Transparency missing in Designated regions (Score: {trans_score*100:.1f}%)")

        # 6. Criticize Topology Consistency
        if consistency_score < 0.90:
            failures.append(f"Topological connectivity gaps flagged (Score: {consistency_score*100:.1f}%)")

        # Determine overall grade
        avg_score = (edge_score + alpha_score + stability_score + halo_score + trans_score + consistency_score) / 6.0
        
        if avg_score > 0.92 and not failures:
            grade = "A"
        elif avg_score > 0.82:
            grade = "B"
        elif avg_score > 0.68:
            grade = "C"
        else:
            grade = "D"

        return {
            "quality_grade": grade,
            "overall_score": avg_score,
            "failures": failures,
            "repair_needed": len(failures) > 0
        }
