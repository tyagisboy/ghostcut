import os
import sys
import cv2
import numpy as np

sys.path.append(os.path.abspath(os.path.dirname(__file__)))
from src.core.segmentation import SegmentationEngine

def test_image(img_name):
    workspace = "H:/AI Tools/Background Removal"
    img_path = os.path.join(workspace, "Test images", img_name)
    if not os.path.exists(img_path):
        print(f"[-] Image not found: {img_path}")
        return
        
    print(f"\n[*] Processing image: {img_name}")
    img_bgr = cv2.imread(img_path)
    # Downscale to speed up local execution
    img_bgr = cv2.resize(img_bgr, (512, 512))
    
    engine = SegmentationEngine(os.path.join(workspace, "src/models"))
    engine.load_model("birefnet-general-lite")
    
    # Process
    mask = engine.process_image(
        img_bgr, apply_matting=True,
        bg_thresh=40, fg_thresh=240, erode_size=3,
        preserve_transparency=False, sharpness=0,
        focus_thresh=0.0, processing_mode="fast",
        disable_quality_loop=False
    )
    
    # Print metrics
    print(f"[+] Processed. Quality metrics: {engine.last_quality_metrics}")
    print(f"[+] Repair Log:")
    for log in engine.last_repair_log:
        print(f"  - Crop {log['index']} ({log['strategy']}): {log['outcome']} at {log['bbox']}")

if __name__ == "__main__":
    test_image("1_woman_straight.jpg")
    test_image("beauty-portrait-young-curly-model.jpg")
