# Implementation Plan v9.0.0: Dynamic Deep-Semantic Material & Decontaminated Alpha Engine

## User Complaint & Brutal Truth Analysis
The user correctly pointed out:
> *"I suspect that you are setting policy parameters according to the images i gave you, you do not create the capability to keep the policy parameters dynamic according to the image. Am I correct ?"*

**Yes. The diagnosis is 100% accurate.** Previous iterations used static heuristic thresholds (e.g. `w_detail_new > 0.30`), which misclassified textured sweater knit fabric as "hair detail", causing clothing edges to be routed to soft Guided Filter matting and producing a 20px grey foggy halo. Furthermore, static thresholds failed to dynamically adapt to local image statistics, and lack of foreground color decontamination left original studio wall RGB trapped inside translucent hair strands.

---

## Architectural Breakthrough in v9.0.0

```
                                  ┌─► Stream A: Deep-Semantic Solid Engine (Clothes, Sweater, Skin, Arms)
                                  │   - Condition: IS_FABRIC + IS_SKIN > IS_HAIR
                                  │   - BYPASS Guided Filter completely
                                  │   - Adaptive Color Gradient (|∇I| max) Subpixel Edge Snapping
                                  │   - 100% Solid Alpha inside, 0% Alpha outside, 1px Anti-Aliased Edge
Input Image + BiRefNet Masks ─────┤
                                  └─► Stream B: Dynamic Hair & Foreground Decontamination Engine (Hair & Curls)
                                      - Condition: IS_HAIR > IS_FABRIC + IS_SKIN
                                      - Dynamic Image-Adaptive Noise Floor: τ_noise = μ_bg + 2.0 * σ_bg
                                      - Dynamic Spatially-Varying Background Field B_adaptive(x,y)
                                      - Foreground Color Decontamination: F = (I - (1-α)B_orig) / α
```

### 1. Deep-Semantic Solid Engine (Clothes, Sweater, Skin, Arms)
- **Eliminates `w_detail_new` Heuristic**: Routes pixels based strictly on BiRefNet semantic material probabilities: `IS_FABRIC + IS_SKIN > IS_HAIR`.
- **Zero Halo / Zero Bleed**: Sweaters, cotton t-shirts, skin, arms, and fingernails bypass Guided Filter matting entirely.
- **Subpixel Gradient Snapping**: Snaps boundary to $|\nabla I|_{\max}$, generating a $100\%$ solid alpha interior ($\alpha = 1.0$), $0\%$ alpha exterior ($\alpha = 0.0$), with 1-pixel subpixel anti-aliasing ONLY on the edge contour.

### 2. Dynamic Image-Adaptive Local Statistics Engine
- **No Hardcoded Constants**: Calculates local mean $\mu_{\text{bg}}$ and standard deviation $\sigma_{\text{bg}}$ of background pixels.
- Dynamic noise floor: $\tau_{\text{noise}} = \mu_{\text{bg\_alpha}} + 2.0 \times \sigma_{\text{bg\_alpha}}$. Any alpha below $\tau_{\text{noise}}$ is clamped to $0.0$.
- Dynamic background color distance threshold: $D_{\text{bg\_local}}(x,y) < 2.5 \times \sigma_{\text{bg\_color}} \to \alpha = 0.0$.

### 3. Foreground Color Decontamination (Unmixing Studio Wall Color)
- Translucent hair pixels ($\alpha \in [0.15, 0.85]$) currently retain the original white studio wall color $B_{\text{orig}}$ inside their RGB channels, causing a grey haze on dark backgrounds.
- v9.0.0 unmixes true hair color $F_{\text{hair}}$:
  $$F = \text{clip}\left(\frac{I - (1 - \alpha) B_{\text{orig}}}{\alpha}, 0, 255\right)$$
- Replaces original image RGB with $F$ in translucent hair pixels, eliminating all grey haze on dark/black/colored backgrounds!

---

## User Review Required

> [!IMPORTANT]
> **Dynamic Image-Adaptive Engine & Foreground Decontamination**: Parameters will no longer use static thresholds. Solid clothing and skin will be dynamically separated from hair using deep semantic material probabilities, and hair pixels will undergo true foreground color decontamination to eliminate off-white wall color trapped inside hair strands.

---

## Verification Plan

### Automated Verification
- Run `py -u test_run.py` to confirm benchmark quality scores remain Grade A ($\ge 98.3\%$).

### Visual Verification
1. **Straight Hair Model (`GhostCut_v870_Straight_RGBA.png`)**: Verify on dark background that pink sweater sleeve has $0.0$ outer alpha and zero grey foggy halo.
2. **Curly Hair Model (`GhostCut_v870_Curly_RGBA.png`)**: Compare side-by-side with Photoroom to verify hair strands are deep chestnut brown with zero background mist and $100\%$ transparent inter-hair gaps.
