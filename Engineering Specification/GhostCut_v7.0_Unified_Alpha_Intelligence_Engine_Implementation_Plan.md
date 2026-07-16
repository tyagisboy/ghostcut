# GhostCut v7.0 --- Unified Alpha Intelligence Engine

## Engineering Implementation Plan

### Objective

Replace multiple heuristic alpha refinement stages with a single
**Unified Alpha Intelligence Engine (AIE)** that generates, validates,
repairs, and explains region-aware alpha mattes.

## Phase 1 --- Alpha SDK

Create `src/core/alpha_engine/` - alpha_engine.py - alpha_context.py -
alpha_policy.py - alpha_region.py - alpha_result.py - alpha_cache.py

All modules communicate through immutable `AlphaContext` and
`AlphaResult`.

## Phase 2 --- Region Alpha Model

Define AlphaRegion: - semantic type - material - edge type -
transparency class - confidence - repair priority - expected alpha
behaviour

Support Hair, Fur, Skin, Beard, Fabric, Glass, Metal, Plastic, Leaves,
Feathers, Jewelry and Accessories.

## Phase 3 --- Alpha Policy Library

Implement reusable policies: - Hair (flyaway preservation) - Skin (hard
edge) - Fur (fiber preservation) - Glass (opacity gradients) - Fabric
(mesh) Store in `alpha_policy_library.json`.

## Phase 4 --- Unified Alpha Composer

Inputs: - segmentation mask - perception graph - region policies -
confidence maps - quality maps

Outputs: - unified alpha - region alpha maps - alpha confidence map

## Phase 5 --- Adaptive Boundary Solver

Handle: - Hair↔Skin - Fur↔Background - Glass↔Background - Fabric↔Air -
Leaf↔Sky

Use gradients, edge orientation and confidence instead of fixed radii.

## Phase 6 --- Alpha Quality Analyzer

Measure: - boundary continuity - clipping - halo width - transparency -
strand preservation - whisker preservation - matte smoothness

## Phase 7 --- Local Alpha Repair

Repair only defective regions: - halo suppression - transparency
recovery - edge smoothing - boundary sharpening - hair completion

## Phase 8 --- Alpha Memory

Persist: - image fingerprint - alpha policies - repair history - quality
score Reuse successful policies.

## Phase 9 --- Explainability Dashboard

Display: - alpha strategy - region policies - confidence - repair
timeline - alpha quality grade

## Phase 10 --- Benchmark Framework

Categories: Curly Hair, Straight Hair, Afro Hair, Wet Hair, Long Fur,
Glass, Mesh, Lace, Jewelry, Plants, Feathers.

Metrics: Boundary IoU, SAD, Connectivity Error, Boundary F-score, Halo
Width, Transparency Accuracy, Processing Time.

## Phase 11 --- Runtime Optimization

-   Tile-based processing
-   Cache intermediate maps
-   CPU-first
-   DirectML/CUDA acceleration
-   Maintain identical output across providers

## Phase 12 --- Production Integration

Integrate AIE into the main pipeline. Legacy refinement becomes internal
services. Maintain backward compatibility until migration completes.

## Deliverables

-   Alpha SDK
-   Unified Alpha Composer
-   Region Alpha Model
-   Alpha Policy Library
-   Adaptive Boundary Solver
-   Alpha Quality Analyzer
-   Local Alpha Repair
-   Alpha Memory
-   Explainability Dashboard v4
-   Alpha Benchmark Suite

## Acceptance Criteria

-   Single alpha generation path.
-   Region-aware alpha policies.
-   Explainable decisions.
-   Local repair only.
-   Improved edge consistency.
-   Equal or lower CPU cost.
-   Backward compatible migration.
