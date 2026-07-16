# 12 — Local Repair Runtime

## Transactional repair

The runtime receives approved proposals only. Each names a padded ROI, defect IDs, operator, bounded parameters, protected mask, expected gain, and rollback artifact. Flow: snapshot → candidate in ROI → affected-metric verification → commit or rollback.

## Baseline operators

Bounded normal-direction alpha contraction/relaxation, confidence-weighted guided refinement, transition regularization, local foreground-color decontamination, and policy-map seam blending. v8.5 excludes generative strand synthesis and unconstrained global morphology.

## Acceptance rules

One repair chain/ROI and one retry maximum. Accept only if target defect decreases by threshold and protected metrics, leakage, and alpha bounds remain safe. Record exact parameters/before-after metrics; rejected candidates remain visible in diagnostics but not in export.

## Tests

Test rollback, ROI isolation, cancellation before commit, seam behavior, no source RGB mutation, and benchmark gates that reject a hair gain accompanied by background leakage.
