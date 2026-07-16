# 15 — Testing and Benchmark Framework

## Benchmark design

Maintain a versioned, consented suite split by scenario: hard products, skin edges, straight/wavy/curly/coily hair geometry, fur, translucent objects, backlight, clutter, and counterexamples. Use development/held-out splits; never tune thresholds on held-out data.

## Required measurements

SAD, MSE, gradient/connectivity error, boundary F-score, per-band alpha error, halo width/chroma, strand precision/recall where annotated, wall time, peak memory, repair accept/rollback rate, and deferred ROI count. Report paired per-image deltas, category medians, and tail (p95), not only one average.

## Gates

A change passes only when critical categories remain within tolerance, aggregate quality improves or stays neutral, low-resource budgets are met, and results reproduce with policy/model versions recorded. Include unit, property, integration, regression, and blinded manual review layers.
