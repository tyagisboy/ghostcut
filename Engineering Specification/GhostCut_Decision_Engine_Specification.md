# GhostCut Decision Engine Specification (v2)

This specification details the policy rules, decision logic, and adaptive heuristics of the GhostCut Decision Engine.

---

## 1. Policy Inheritance Hierarchy

Decision engine rules resolve parameter conflicts using a strict cascading inheritance hierarchy:

```
Global Policy Defaults
   └── Hardware Profile Constraints
         └── Scenario Default Rules
               └── Material/Edge Adaptive Rules
                     └── User Preferences (Highest Priority Override)
```

---

## 2. Adaptive Recipe Generation Rules

### A. Model Selection Matrix
- **CPU Constraints**: If `gpu_accelerated = False`, default to `birefnet-general-lite.onnx`.
- **GPU Present**: If `gpu_accelerated = True`, default to `birefnet-general.onnx` for maximum quality.
- **Portraits/Pets on CPU**: If scene is `Studio Portrait` or `Pet`, and only CPU is available, use `birefnet-general.onnx` but fallback matting processing mode to `quality` (capping dimensions to 768px).

### B. Matting Mode Compilation
- **Hard Edges Only**: If edge classes contain `Hard` (> 80%), set `apply_matting = False` or run Guided Filter with a tiny radius `erode_size = 1`.
- **Fine Details Present**: If edge classes contain `Hair`, `Fur`, or `Whisker`, use `processing_mode = quality` or `ultra` (ViTMatte enabled).

---

## 3. Scenario & Material Decision Rules

### A. Portraits (Studio / Outdoor)
- Set `decontaminate = True` (activates color spill decontamination).
- If backlit ratio > 1.3, increase `erode_size` to 4 and enable unsharp masking on the guide image.

### B. Transparent Objects (Glass / Plastic)
- Set `preserve_transparency = True`.
- Set Guided Filter parameter `w_density = 1.0` (preserves linear grey zones around boundary).
- Set `processing_mode = quality`.

### C. Sharp Objects (Jewelry / Metal)
- Set `erode_size = 1`.
- Set `sharpness = 4` (applies sigmoidal sharpening to mask edges).
- Set `focus_thresh = 0.0` (disables focus suppression).

---

## 4. Regional Alpha Policies

When processing a `SubjectRegionGraph`, the alpha matting parameters are customized per region node:
- **`hair` Node**: Guided filter radius modulated by local `w_detail` map. Max radius = 12px.
- **`skin` Node**: Tiny guided filter radius (2px) to prevent soft halo outlines.
- **`glass` Node**: High transparency preservation.
- **`fabric` Node**: Moderate radius (5px) with low sharpness to maintain smooth texture blends.

---

## 5. Confidence-Driven Local Repair Logic

Local repairs are executed only when the `ConfidenceEngine` reports low confidence values:
1. **Check Block Confidence**: Divide boundary zones into 16x16 pixel blocks.
2. **Flag Low Confidence**: If segmentation, edge, or alpha confidence falls below `0.3`, label block as failing.
3. **Cluster & Cap**: Cluster contiguous failing blocks into bounding boxes. Cap repair crops to the top 5 largest boxes to bound CPU runtime.
4. **Local Matting**: Run crop-specific ViTMatte detail extraction and blend using distance-feathered alphas.
