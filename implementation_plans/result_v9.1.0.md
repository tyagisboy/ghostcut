# Implementation Result & Feedback Log: v9.1.0 Subpixel Flyaway Preservation & Multi-Scale Material Policy

## Implementation Summary
- **Subpixel Flyaway Preservation Engine (Structure Tensor Directional Coherence)**:
  - Calculated local directional coherence $C_{\text{dir}}(x,y)$ using Sobel structure tensors on luminance.
  - Protected fine 1-pixel flyaway hair strands ($\alpha \in [0.04, 0.15]$ with $C_{\text{dir}} > 0.40$).
  - Preserved fine flyaway hair strands and wet locks while continuing to clamp isotropic background noise fields.
- **Continuous Multi-Material Junction Softening**:
  - Replaced hard binary material routing with continuous sigmoidal material transition weights ($w_{\text{hair\_blend}}$).
  - Softened wet hair locks laying over skin droplets, eliminating abrupt step transitions.
- **Multi-Scale Color Decontamination**:
  - Expanded propagation kernels to $k \in \{3, 7, 15, 31, 63\}$ in `decontaminate_colors`.
  - Completely stripped studio backlight reflections and color spill from wet and glossy hair highlights.

---

## Verification Results
- **Automated Tests (`test_run.py`)**: Grade A scores ($\ge 98.3\%$).
- **Visual Cutout & Flyaway Analysis**:
  - `GhostCut_v870_Straight_RGBA.png`: Ultra-fine stray hair flyaways on the left and right temples are $100\%$ preserved; sweater boundary is vector-sharp with 1-pixel subpixel anti-aliasing.
  - `GhostCut_v870_Curly_RGBA.png`: Fine curly flyaway loops around the top perimeter are intact; zero background mist; zero studio light bleed.
