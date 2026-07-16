# 07 — Quality Intelligence Runtime

## Role

Quality Intelligence is a read-only assessor. It fuses halo, edge, morphology, material, and alpha findings into a calibrated report; it never changes pixels or chooses a semantic label.

## Scoring and decisions

Compute separate hard-edge, soft-edge, halo, color-integrity, strand-retention, and confidence/deferred-work components. `overall_score` is a versioned weighted summary, not a substitute for the components. High severity plus low confidence becomes inspection/defer, not automatic repair. Protected regions cap allowed pixel deltas.

## API output

Return `QualityReport` with finding IDs, ROI, severity, confidence, supporting evidence, proposed operators, protected-map summary, and export recommendation. Conflicting evidence remains visible to the planner.

## Verification

Unit-test fusion monotonicity, missing analyzers, contradictions, and protection caps. Integration-test that a quality report alone cannot mutate any artifact. Benchmark reports must include per-category metrics, not only an aggregate score.
