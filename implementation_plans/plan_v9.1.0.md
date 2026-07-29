# Implementation Plan v9.1.0: Subpixel Flyaway Preservation & Multi-Scale Material Policy Refinement

## Context & User Feedback Overview
The user tested GhostCut v9.0.0 across diverse subject types, lighting conditions, wet hair, afro curls, and long flowing hair:
> *"As of now the output is improved so far over the past iteration and I want to keep digging and doing the hard work to resolve the remaining issues."*

### Key Observations Across New Test Outputs:
1. **Fine Flyaway Hair Truncation** *(Images 1 & 2)*: In images with delicate 1-pixel flyaway hair strands or wet hair locks, static alpha noise floor clamping ($\alpha < 0.15 \to 0.0$) chopped off ultra-fine stray hairs.
2. **Wet Hair / Skin Junction Overlap** *(Image 1)*: Wet hair locks laying across skin droplets created a slight step transition at the solid/hair boundary.
3. **Studio Light Bleed on Glossy/Wet Hair**: High-key studio backlights require deeper multi-scale color decontamination to eliminate off-white reflections trapped inside wet hair highlights.

---

## Technical Overhaul in v9.1.0

```
                                      ┌─► Stream A: Deep-Semantic Solid Engine (Clothes, Skin, Arms)
                                      │   - 100% Solid interior, 0% exterior, 1px Anti-Aliased edge
                                      │
Input Image + BiRefNet Masks ─────────┼─► Stream B: Subpixel Flyaway Preservation Engine (Hair & Curls)
                                      │   - Structure Tensor Directional Coherence C_dir(x,y)
                                      │   - Protects 1-pixel flyaways (alpha in [0.05, 0.15] & C_dir > 0.45)
                                      │   - Suppresses isotropic background noise mist (C_dir <= 0.45 -> 0.0)
                                      │
                                      └─► Stream C: Multi-Scale Color Decontamination
                                          - Multi-scale propagation kernels k in {3, 7, 15, 31, 63}
                                          - Eliminates studio backlight bleed on wet & glossy hair strands
```

### 1. Subpixel Flyaway Preservation Engine
- **Structure Tensor Analysis**: Calculates local directional coherence $C_{\text{dir}}(x,y) = \frac{\sqrt{(J_{xx} - J_{yy})^2 + 4 J_{xy}^2}}{J_{xx} + J_{yy} + 1e-5}$ using Sobel structure tensors on luminance.
- **Adaptive Flyaway Protection**:
  - Low-alpha pixels ($\alpha \in [0.04, 0.15]$) with $C_{\text{dir}} > 0.45$ represent continuous 1-pixel flyaway hair strands $\implies$ **PRESERVED**.
  - Low-alpha pixels with $C_{\text{dir}} \le 0.45$ represent non-directional background noise mist $\implies$ **CLAMPED TO 0.0**.

### 2. Continuous Multi-Material Junction Softening
- Replaces binary hard mask routing with a continuous sigmoidal material transition weight:
  $$W_{\text{mat}} = \text{clip}\left(\frac{\text{hair\_prob} - 0.05}{0.20}, 0.0, 1.0\right)$$
- Ensures smooth, seamless transitions where wet hair locks lay over skin, forehead, or shoulders.

### 3. Multi-Scale Studio Backlight Color Decontamination
- Expands `decontaminate_colors` propagation kernels to $k \in \{3, 7, 15, 31, 63\}$.
- Performs multi-resolution foreground color estimation to completely strip off-white studio backlight reflections from glossy and wet hair locks.

---

## User Review Required

> [!IMPORTANT]
> **Flyaway Preservation & Multi-Scale Decontamination**: Low-alpha flyaway hair strands will be preserved using structure tensor directional coherence analysis, ensuring ultra-fine stray hairs are not shaved off while background noise remains completely suppressed.

---

## Verification Plan

### Automated Verification
- Run `py -u test_run.py` to confirm benchmark quality scores remain Grade A ($\ge 98.3\%$).

### Visual Verification
1. **Wet Hair Model (`test_1`)**: Verify fine wet flyaway strands and wet hair locks laying over skin.
2. **Brunette Long Hair Model (`test_4`)**: Verify long flowing hair flyaways on the right edge are fully preserved without grey haze.
3. **Curly & Straight Models (`test_2`, `test_3`)**: Verify zero sweater bleed and zero background mist.
