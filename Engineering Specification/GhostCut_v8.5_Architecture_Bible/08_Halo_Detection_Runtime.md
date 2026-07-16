# 08 — Halo Detection Runtime

## Objective

Localize light, dark, and chroma halos while preserving valid rim lighting and translucency. A halo finding requires evidence beyond low alpha or a bright edge.

## Procedure

Build inside/outside contour rings from alpha; robustly sample local foreground/background colours; compute Lab discrepancy, alpha-gradient direction, and persistent width along connected contour segments. Suppress or lower confidence where transparency/rim-light beliefs and source gradients support the transition. Emit connected ROIs with width, affected contour fraction, and confidence.

## Repair recommendations

Recommend the least destructive operator: bounded alpha contraction, local foreground re-estimation, or edge color decontamination. Never request outward alpha expansion as a halo repair. Insufficient/heterogeneous samples produce `low_confidence`, not color replacement.

## Tests

Benchmark on pale/dark/chroma backgrounds, blonde/black hair, glass, intentional backlight, and strong JPEG artifacts. Accept a repair only if target halo metrics improve and protected/strand metrics do not regress.
