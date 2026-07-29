# Implementation Plan v8.9.0: Dual-Stream Absolute Edge & Alpha Engine

## Architectural Problem Statement & Pixel Analysis
Across the 5 uploaded screenshots, GhostCut exhibits severe quality degradation compared to Photoroom:
1. **Pink Sweater & Arms**: A 15–20px wide semi-transparent grey vapor halo surrounds her entire sweater, arms, skin, and shoulders.
2. **Top Hair & Curl Volume**: A dirty grey smoky mist outlines her entire head and fills inter-hair gaps with white/grey residual islands.

### Fundamental Root Cause: The Guided Filter Alpha Ramp Disease
GhostCut's current pipeline passes all mask regions through `color_guided_filter`. Guided filter spreads high-contrast boundaries into a 15–30px semi-transparent alpha ramp ($\alpha = 0.05 \to 0.95$). When composited on dark, red, or blue backgrounds, this 30px alpha ramp mixes the new background with the original off-white wall color, producing a massive grey halo cloud around the subject.

---

## Dual-Stream Solution Architecture (v8.9.0)

```
                            ┌─► Stream A: Hard Object Stream (Clothes, Sweater, Skin, Arms)
                            │   - BYPASS Guided Filter completely
                            │   - Strict Binary Mask with 1-Pixel Subpixel Anti-Aliasing
                            │   - Alpha = 0.0 everywhere outside the 1px boundary line
Input Image + Raw Mask ─────┤
                            └─► Stream B: Hair & Translucent Detail Stream (Hair & Curls)
                                - ViTMatte Transformer Matting ONLY on hair_prob > 0.15
                                - Strict Alpha Noise Clamp: alpha < 0.18 -> 0.0
                                - Color Decontamination replacing wall color with true hair BGR
```

### Stream A: Hard Object Stream (Clothes, Sweater, Skin, Arms)
- Bypasses Guided Filter matting entirely.
- Computes `mask_hard`:
  ```python
  # Hard thresholding with 1px subpixel anti-aliasing
  mask_hard = cv2.threshold(raw_mask, 128, 255, cv2.THRESH_BINARY)[1]
  # 1px Gaussian smooth ONLY along the 1px boundary line
  boundary_1px = cv2.Canny(mask_hard, 100, 200)
  mask_hard = np.where(boundary_1px > 0, cv2.GaussianBlur(mask_hard, (3, 3), 0.5), mask_hard)
  ```
- **Result**: Zero grey halo, zero pink sweater bleed, zero arm ghosting lines!

### Stream B: Hair & Translucent Detail Stream (Hair Volume & Curls)
- Executed strictly inside hair regions (`hair_prob > 0.15`).
- ViTMatte transformer matting refined with **Strict Alpha Noise Clamping**:
  ```python
  # Clamp background alpha noise mist directly to 0.0
  q_hair = np.where(q_hair < 0.18, 0.0, q_hair)
  # Strip interior white wall holes
  q_hair = np.where(local_bg_dist < 25.0, 0.0, q_hair)
  ```

---

## User Review Required

> [!IMPORTANT]
> **Complete Elimination of Guided Filter Blur on Solid Objects**: Clothes, sweaters, skin, arms, and fingernails will bypass Guided Filter completely and receive a 1-pixel anti-aliased hard boundary, permanently eliminating the 20px grey halo cloud and sweater bleed.

---

## Verification Plan

### Automated Verification
- Run `py -u test_run.py` to confirm benchmark quality scores remain Grade A ($\ge 98.2\%$).

### Visual Verification
1. **Straight Hair Model (`GhostCut_v870_Straight_RGBA.png`)**: Inspect on black/dark background to verify 100% elimination of the grey foggy halo around the pink sweater and arms.
2. **Curly Hair Model (`GhostCut_v870_Curly_RGBA.png`)**: Inspect on dark background to verify zero smoky grey mist around top curls and zero white trapped islands inside curly loops.
