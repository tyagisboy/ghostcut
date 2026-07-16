# GhostCut Vision Evaluation Framework (VEF) v1.0

## Objective

Freeze the current architecture and focus on evaluating and calibrating
GhostCut's perception quality instead of adding new runtimes.

## Phase 1 --- Architecture Freeze

-   No new AI models.
-   No new segmentation algorithms.
-   No new cognitive layers.
-   Improvements must be evidence-driven.

## Phase 2 --- Vision Evaluation Framework

Create `src/core/vision_evaluation/` with: - vision_score.py -
benchmark_dataset.py - runtime_accuracy.py - confusion_matrix.py -
calibration_metrics.py - evaluator.py - report_generator.py

## Phase 3 --- Runtime Accuracy

Each runtime returns: - prediction - confidence - ground_truth -
correct - score

Measure Scene, Subject, Background, Material, Hair, Fur, Edge,
Transparency, Strategy and Self-Critic.

## Phase 4 --- Vision Score

Generate per-image scorecards and an overall Vision Score. Save results
with the image profile JSON.

## Phase 5 --- Runtime Reliability Database

Create `vision_runtime_stats.json` storing accuracy, precision, recall,
F1, false positives and false negatives by category: Portrait, Animal,
Product, Plant, Food, Glass, Outdoor, Studio.

## Phase 6 --- Confidence Calibration

Calibrate confidence using: Model Confidence × Historical Runtime
Accuracy × Scene Reliability × Strategy Reliability.

## Phase 7 --- Confusion Matrices

Generate confusion matrices for Scene, Subject, Hair, Material and Edge
classifications.

## Phase 8 --- Explainability Dashboard

Display: - Vision Score - Runtime Accuracy - Reliability - Consensus
Confidence - Calibration Adjustments - Runtime Disagreements - Final
Decision - Self-Critic Summary

## Phase 9 --- Benchmark Dataset

Create benchmark folders: Portrait, Animal, Product, Glass, Jewelry,
Plants, Food, Transparent, CurlyHair, StraightHair, WetHair, Backlit.
Each benchmark contains the original image plus expected labels and
expected runtime outputs.

## Phase 10 --- Validation Workflow

Image → Prediction → Ground Truth Comparison → Runtime Metrics →
Calibration → Consensus → Strategy → Segmentation → Self-Critic → Final
Vision Report.

## Deliverables

-   Vision Evaluation Framework
-   Runtime Accuracy Database
-   Vision Score Engine
-   Confusion Matrix Engine
-   Confidence Calibration Engine
-   Reliability Statistics
-   Explainability Dashboard v2
-   Automated Evaluation Reports

## Success Criteria

-   Architecture unchanged.
-   Runtime accuracy measurable.
-   Confidence calibrated.
-   Reproducible benchmark reports.
-   Future development guided by benchmark evidence.
