import os

class ReportGenerator:
    """
    Formats multi-image evaluation scorecards into standard Markdown/Text reports.
    """
    @staticmethod
    def generate_markdown_report(results_list: list) -> str:
        """
        Compiles list of scorecard results into a clean markdown document.
        """
        lines = []
        lines.append("# GhostCut Vision Evaluation Framework (VEF) v1.0 Report")
        lines.append("")
        
        # Calculate overall statistics
        total_images = len(results_list)
        if total_images == 0:
            lines.append("No evaluation metrics recorded.")
            return "\n".join(lines)
            
        avg_vision_score = sum(r["overall_vision_score"] for r in results_list) / total_images
        
        lines.append("## Summary Metrics")
        lines.append(f"- **Total Evaluated Images:** {total_images}")
        lines.append(f"- **Average Vision Score:** {avg_vision_score*100:.2f}%")
        lines.append("")
        
        lines.append("## Individual Scorecards")
        lines.append("| Image ID | Category | Vision Score | Calibrated Scene Conf |")
        lines.append("| --- | --- | --- | --- |")
        
        for r in results_list:
            score_pct = r["overall_vision_score"] * 100.0
            cal_conf = r.get("calibrated_scene_confidence", 1.0) * 100.0
            lines.append(f"| {r['image_id']} | {r['category']} | {score_pct:.1f}% | {cal_conf:.1f}% |")
            
        lines.append("")
        lines.append("## Detailed Category Analysis")
        for r in results_list:
            lines.append(f"### Scorecard details for: `{r['image_id']}` ({r['category']})")
            for cat, details in r["category_scores"].items():
                lines.append(f"- **{cat.capitalize()} Score:** {details['score']*100:.1f}%")
                
        return "\n".join(lines)
