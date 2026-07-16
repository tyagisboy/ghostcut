# 04 — Algorithms and Mathematics

## Numerical conventions

Alpha `α` is float32 in `[0,1]`. RGB is declared as sRGB or linear; compositing/decontamination equations require linear RGB. Lab-derived distances are used only as perceptual evidence. Clamp only at artifact boundaries, not repeatedly within intermediate calculations.

## Matte model

For observed image `I`, foreground `F`, background `B`, and alpha `α`:

`I = αF + (1 − α)B`.

For a candidate boundary pixel, reconstructed foreground is `F̂ = (I − (1−α)B̂) / max(α, ε)`, where `ε` is policy bounded. Use this only in an uncertain transition band and blend with a locally sampled foreground prior; do not reconstruct near zero-alpha pixels or assume `B̂` is reliable in complex backgrounds.

## Boundary geometry

Create signed distance `D` from the 0.5 alpha contour. A local active band is `|D(x)| ≤ r(x)`, where `r(x)` comes from the fused regional policy. `r` is a search and repair bound, never a blanket dilation. Edge normal is `n = ∇α / (||∇α|| + ε)`; alpha movement is constrained along `n` to reduce tangential bleeding.

## Halo evidence

For a boundary point `x`, sample robust inside/outside rings and estimate local colors `Fprior`, `Bprior`. Compute:

`H(x) = w_c ΔE00(I(x), Fprior) + w_b ΔE00(I(x), Bprior) + w_a |∇α(x)| + w_w width(x)`.

Weights are calibrated by scenario and never treated as universal. Aggregate connected components using median/95th percentile to avoid one noisy pixel dictating a repair. Halo classification additionally considers sign/direction: light, dark, or chroma spill.

## Alpha transition quality

Measure transition width as signed-distance separation between `α=0.1` and `α=0.9` contours. For hard edges, penalize unjustified width; for strand/transparency policies, penalize sudden clamping and topology breaks instead. A generic smoothness loss is unsafe because it removes valid hair detail.

## Edge alignment

Let `gI` be luminance gradient and `gα` alpha gradient. Alignment `A=(gI·gα)/(||gI|| ||gα||+ε)` supports an observed boundary when positive and spatially persistent. It is evidence, not a proof: low-contrast hair may have weak alignment and must remain eligible when other evidence supports it.

## Repair choice

For proposal `o`, minimize:

`J(o)=λd·DefectAfter(o)+λp·ProtectedRegression(o)+λΔ·PixelDelta(o)+λt·Cost(o)+λu·Uncertainty(o)`.

Reject if expected improvement is below policy threshold or if protected-region regression is nonzero above tolerance. Candidate repair is compared against the original ROI metrics, then rolled back unless verified.

## Calibration discipline

All weights, thresholds, and score-to-confidence mappings are versioned policies fitted on a development set. Evaluate on a held-out set with SAD, gradient error, connectivity, boundary F-score, halo width/chroma, runtime, and peak memory. Never tune a policy based on a single illustrative image.
