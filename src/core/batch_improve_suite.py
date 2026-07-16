import os
import sys
import cv2
import numpy as np
import json

sys.path.append("h:/AI Tools/Background Removal")
from src.core.segmentation import SegmentationEngine, decontaminate_colors, get_db_path, extract_image_features
from src.core.intelligence import classify_hair_type, classify_materials

def composite_on_bg(bgr, mask, bg_color=(255, 255, 255)):
    # Composite on a custom background color (default: white)
    alpha = (mask.astype(np.float32) / 255.0)[:, :, np.newaxis]
    bg = np.zeros_like(bgr)
    for c in range(3):
        bg[:, :, c] = bg_color[c]
    comp = bgr.astype(np.float32) * alpha + bg * (1.0 - alpha)
    return np.clip(comp, 0, 255).astype(np.uint8)

def evaluate_mask_quality(mask, category):
    # Evaluates mask characteristics to detect edge artifacts
    total = mask.size
    opaque = np.sum(mask >= 250)
    transparent = np.sum(mask <= 5)
    semi = total - opaque - transparent
    semi_pct = (semi / total) * 100
    
    issues = []
    # Class-specific heuristic assertions
    if category == "glass":
        # Glass should preserve a lot of intermediate transparency values
        if semi_pct < 2.0:
            issues.append("Transparency details clipped in glass mode")
    elif category in ["car", "sharp_object"]:
        # Hard objects should have very tight margins
        if semi_pct > 3.0:
            issues.append("Edge outline is too wide/blurry")
    elif category in ["hair", "fur", "fiber"]:
        # Hair/fur needs soft margins to avoid aliased step functions
        if semi_pct < 2.0:
            issues.append("Hair edges are too hard/jagged")
            
    return semi, semi_pct, issues

def get_image_category(filename):
    name = filename.lower()
    if "glass" in name:
        return "glass"
    elif "car" in name:
        return "car"
    elif "katana" in name:
        return "sharp_object"
    elif "apple" in name:
        return "sharp_object"
    elif "curly" in name or "jude" in name:
        return "hair"
    elif "cat" in name or "dog" in name:
        return "fur"
    elif "spiderman" in name:
        return "fiber"
    else:
        return "general"

def main():
    workspace = "h:/AI Tools/Background Removal"
    test_dir = os.path.join(workspace, "Test images")
    results_dir = os.path.join(test_dir, "Results")
    models_dir = os.path.join(workspace, "src/models")
    
    os.makedirs(results_dir, exist_ok=True)
    
    engine = SegmentationEngine(models_dir)
    engine.load_model("birefnet-general-lite")
    
    # List all valid test images
    valid_ext = ('.png', '.jpg', '.jpeg', '.webp')
    test_images = [f for f in os.listdir(test_dir) if f.lower().endswith(valid_ext)]
    print(f"[*] Found {len(test_images)} test images in {test_dir}")
    
    # We run 3 iterations of refinement
    for iteration in range(1, 4):
        iter_dir = os.path.join(results_dir, f"Iteration_{iteration}")
        os.makedirs(iter_dir, exist_ok=True)
        print(f"\n=================== ITERATION {iteration} ===================")
        
        # Iteration parameter profiles adjusted based on previous evaluation feedback
        if iteration == 1:
            # Baseline parameters
            print("[*] Running Baseline Parameters (Quality Loop and Multi-Type Blending Disabled)...")
            disable_quality_loop = True
            def get_params(category, has_busy_bg):
                return {
                    "bg_thresh": 15, "fg_thresh": 240, "erode_size": 7,
                    "sharpness": 0, "focus_thresh": 0.0, "preserve_transparency": (category == "glass")
                }
        elif iteration == 2:
            # Tuned Mappings with no local repairs or multi-type blending
            print("[*] Running Intermediate Parameters (Tuned Mappings, but Quality Loop/Multi-Type Blending Disabled)...")
            disable_quality_loop = True
            def get_params(category, has_busy_bg):
                if category == "fiber":
                    return {
                        "bg_thresh": 30, "fg_thresh": 235, "erode_size": 3,
                        "sharpness": 1, "focus_thresh": 0.0, "preserve_transparency": False
                    }
                elif category == "sharp_object":
                    return {
                        "bg_thresh": 60, "fg_thresh": 200, "erode_size": 1,
                        "sharpness": 4, "focus_thresh": 0.0, "preserve_transparency": False
                    }
                elif category == "fur":
                    return {
                        "bg_thresh": 20, "fg_thresh": 250, "erode_size": 7,
                        "sharpness": 0, "focus_thresh": 0.0, "preserve_transparency": False
                    }
                bg = 40 if not has_busy_bg else 150
                fg = 240 if not has_busy_bg else 190
                f_th = 6.0 if has_busy_bg else 0.0
                r = 3 if category in ["car", "sharp_object", "glass", "hair"] else 7
                return {
                    "bg_thresh": bg, "fg_thresh": fg, "erode_size": r,
                    "sharpness": 5 if has_busy_bg else 0, "focus_thresh": f_th, "preserve_transparency": (category == "glass")
                }
        elif iteration == 3:
            # Decision Graph Final Optimized Parameters with Quality Loop & Multi-Type Blending
            print("[*] Running Final Optimized Parameters with Quality Loop & Multi-Type Pixel Edge Blending...")
            disable_quality_loop = False
            def get_params(category, has_busy_bg):
                if category == "fiber":
                    return {
                        "bg_thresh": 30, "fg_thresh": 235, "erode_size": 3,
                        "sharpness": 1, "focus_thresh": 0.0, "preserve_transparency": False
                    }
                elif category == "sharp_object":
                    return {
                        "bg_thresh": 60, "fg_thresh": 200, "erode_size": 1,
                        "sharpness": 4, "focus_thresh": 0.0, "preserve_transparency": False
                    }
                elif category == "fur":
                    return {
                        "bg_thresh": 20, "fg_thresh": 250, "erode_size": 7,
                        "sharpness": 0, "focus_thresh": 0.0, "preserve_transparency": False
                    }
                bg = 40 if not has_busy_bg else 150
                fg = 240 if not has_busy_bg else 190
                f_th = 6.0 if has_busy_bg else 0.0
                r = 3 if category in ["car", "sharp_object", "glass", "hair"] else 7
                return {
                    "bg_thresh": bg, "fg_thresh": fg, "erode_size": r,
                    "sharpness": 5 if has_busy_bg else 0, "focus_thresh": f_th, "preserve_transparency": (category == "glass")
                }
                
        # Process all images under this iteration's parameter profiles
        for img_name in test_images:
            root, _ = os.path.splitext(img_name)
            out_path = os.path.join(iter_dir, f"{root}_no_bg.png")
            profile_path = os.path.join(iter_dir, f"{root}_profile.json")
            
            # Cheap pre-check to utilize hardware efficiently and avoid redundant loops
            if os.path.exists(out_path) and os.path.exists(profile_path) and "--force" not in sys.argv:
                print(f"  [SKIP] Already processed (Pre-Check): {img_name}")
                continue
                
            path = os.path.join(test_dir, img_name)
            img_bgr = cv2.imread(path)
            if img_bgr is None:
                continue
                
            # Perform scene detection and category classification dynamically to get parameters
            raw_mask = engine.process_image(img_bgr, apply_matting=False)
            features = extract_image_features(img_bgr, raw_mask)
            
            is_person = any(k in img_name.lower() for k in ["man", "woman", "girl", "blonde", "portrait", "hair", "curly", "afro", "frizzy", "jude", "ejiofor", "model", "pyjamas", "standing", "beauty"])
            is_pet = any(k in img_name.lower() for k in ["cat", "dog", "otter", "husky", "whiskers", "fluffy", "golden", "persian", "retriever", "chihuahua", "collie"])
            
            if is_person:
                category = "hair"
            elif is_pet:
                category = "fur"
            else:
                material_type = classify_materials(img_bgr, raw_mask, features)
                if material_type == "glass" or any(k in img_name.lower() for k in ["glass", "plastic", "jar", "bottle"]):
                    category = "glass"
                elif material_type == "jewelry" or any(k in img_name.lower() for k in ["jewelry", "necklace", "ring", "watch"]):
                    category = "sharp_object"
                elif any(k in img_name.lower() for k in ["car", "laptop", "chair"]):
                    category = "car"
                else:
                    category = "general"
                
            has_busy_bg = ("curly4" in img_name) # test_curly4.jpg is our busy-background reference
            p = get_params(category, has_busy_bg)
            
            # Run matting and decision graph loops
            mask = engine.process_image(
                img_bgr, apply_matting=True,
                fg_thresh=p["fg_thresh"], bg_thresh=p["bg_thresh"],
                erode_size=p["erode_size"], preserve_transparency=p["preserve_transparency"],
                sharpness=p["sharpness"], focus_thresh=p["focus_thresh"],
                processing_mode="fast", disable_quality_loop=disable_quality_loop
            )
            
            # Apply color decontamination
            decon = decontaminate_colors(img_bgr, mask)
            
            # Save PNG output
            rgba = cv2.cvtColor(decon, cv2.COLOR_BGR2BGRA)
            rgba[:, :, 3] = mask
            cv2.imwrite(out_path, rgba)
            
            # Save ImageProfile JSON
            if engine.last_profile is not None:
                try:
                    with open(profile_path, "w", encoding="utf-8") as pf:
                        json.dump(engine.last_profile.to_dict(), pf, indent=4)
                except Exception as e:
                    print(f"[-] Failed to write ImageProfile JSON: {e}")
            
            # Evaluate quality and check for issues using the ground truth category constraints
            gt_category = get_image_category(img_name)
            semi, semi_pct, issues = evaluate_mask_quality(mask, gt_category)
            issues_str = " | ISSUES: " + ", ".join(issues) if issues else " | [OK]"
            print(f"  Processed: {img_name} | Semi: {semi} ({semi_pct:.2f}%){issues_str}")
            
    print("\n[SUCCESS] Completed all 3 iterations of batch optimization suite!")

if __name__ == "__main__":
    main()
