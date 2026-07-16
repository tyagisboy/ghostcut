# 13 — Explainability Framework

## Layered audiences

Default UI states outcomes: “Fine edge detail preserved” or “Kept original edge for safety.” Professional mode adds affected ROI, policy, quality score, and repairs. Developer mode exposes evidence IDs, confidence calibration, scheduler trace, telemetry, map overlays, and before/after metrics. Raw developer logs are never the default user experience.

## Record schema

Each decision stores stage, action, reason, evidence IDs, ROI, policy/calibration versions, elapsed time, and accepted/rejected state. Every displayed claim must map to a measurement or validated strategy—not a generic assertion.

## Privacy and tests

No absolute paths/raw pixels are exported by default. Diagnostic packages are opt-in and redact metadata. Test that accepted, skipped, deferred, and rolled-back repairs each generate clear explanations; test that uncertainty is shown rather than rounded to 100%.
