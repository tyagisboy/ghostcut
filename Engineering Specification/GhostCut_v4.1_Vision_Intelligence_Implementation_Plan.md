# GhostCut v4.1 --- Vision Intelligence Implementation Plan

## Objective

Transform GhostCut into a semantic vision system that understands
subjects, anatomy, materials and geometry before recipe generation.

## Phase 1 -- Vision Intelligence SDK

Define a common runtime contract: - Runtime ID, version, dependencies -
Execution cost - Inputs/outputs - Confidence - Explainability evidence -
Region contributions

## Phase 2 -- Face Intelligence Runtime

Detect face, landmarks, beard, moustache, eyebrows, ears, neck, pose and
confidence. Recipe: preserve facial contours and beard edges.

## Phase 3 -- Eye Intelligence Runtime

Detect eyes, eyelashes, iris, glasses, reflections, blink state. Recipe:
preserve eyelashes and transparent glasses.

## Phase 4 -- Clothing Intelligence Runtime

Detect clothing type, fabric type, folds, mesh, transparency. Recipe:
fabric-aware refinement and mesh preservation.

## Phase 5 -- Animal Anatomy Runtime

Detect ears, whiskers, tail, paws, feathers, mane, horns. Recipe:
anatomy-aware fur and feather refinement.

## Phase 6 -- Plant Intelligence Runtime

Detect leaves, stems, flowers, thorns, branches, needles. Recipe:
preserve thin botanical structures.

## Phase 7 -- Product Geometry Runtime

Recognize products and geometry: - Straight edges - Circular edges -
Symmetry - Reflective surfaces Recipe: industrial edge preservation.

## Phase 8 -- VisionGraph

Create hierarchical graph: Face→Hair→Flyaways Human→Clothing Animal→Tail
Plant→Leaves

Each node stores semantic type, material, edge type, transparency and
confidence.

## Phase 9 -- Recipe Engine v3

Generate recipes per semantic node instead of globally.

## Phase 10 -- Explainability

Visualize: - Runtime execution - VisionGraph - Semantic evidence -
Regional recipes - Confidence timeline

## Phase 11 -- Benchmarks

Benchmark portraits, pets, plants, transparent objects, vehicles,
jewelry and products. Store ImageProfile, VisionGraph, recipes and
quality metrics.

## Acceptance Criteria

-   Scheduler executes only required vision runtimes.
-   VisionGraph generated for every image.
-   Semantic recipes replace global recipes.
-   CPU overhead remains below 15% on portraits.
-   Architecture ready for v4.2 Quality Intelligence.

## Deliverables

-   Face Intelligence Runtime
-   Eye Intelligence Runtime
-   Clothing Intelligence Runtime
-   Animal Anatomy Runtime
-   Plant Intelligence Runtime
-   Product Geometry Runtime
-   VisionGraph
-   Recipe Engine v3
-   Dashboard v4.1
-   Benchmark Suite
