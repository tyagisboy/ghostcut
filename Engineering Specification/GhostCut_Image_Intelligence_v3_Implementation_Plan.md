# GhostCut Image Intelligence Engine v3

## Next Development Cycle (Post Iteration-3 Review)

### Executive Summary

Iteration-3 shows the segmentation backbone is no longer the primary
bottleneck. The main issue is incorrect semantic decisions before
refinement. The objective of v3 is to improve decision quality, not
increase iterations or add heavier AI models.

## Phase 1 --- Semantic Validation Runtime

Create `semantic_validation_runtime.py`. - Remove impossible
predictions. - Apply semantic consistency rules. - Reject conflicting
labels. Examples: - Human -\> Fur=False - Plant -\> Skin=False - Product
-\> Hair=False - Cactus -\> Whisker=False

Output: ValidatedImageProfile.

## Phase 2 --- Hierarchical Decision Engine

Pipeline: Image -\> Scene -\> Subject -\> Material -\> Hair/Fur -\>
Semantic Validation -\> Consistency Engine -\> Recipe Generator

## Phase 3 --- Hair Intelligence v2

Estimate: - length - density - curl level - strand width - flyaway
score - transparency score - wetness - frizz - volume - backlit
probability - confidence

## Phase 4 --- Fur Intelligence v2

Estimate: - fur length - density - fluffiness - whiskers - undercoat -
transparency - confidence

## Phase 5 --- Material Runtime v2

Infer materials hierarchically: Subject -\> Region -\> Material. Only
valid materials survive.

## Phase 6 --- Region Graph v2

Each node stores: semantic class, material, edge type, transparency,
confidence, refinement profile.

## Phase 7 --- Recipe Generator v2

Recipes become region-aware. Hair, skin, glass, fabric and metal receive
independent refinement settings.

## Phase 8 --- Explainability Dashboard

Display: - Raw predictions - Rejected predictions - Final validated
profile - Rules fired - Final recipe

## Phase 9 --- Benchmark Framework

Save: - Original image - Alpha - Output - Raw profile - Validated
profile - Recipe - Metrics

## Success Criteria

-   Eliminate impossible semantic combinations.
-   Eliminate cactus/human misclassification.
-   Reduce halos.
-   Improve fine hair.
-   Maintain single-pass execution.
-   No extra segmentation iterations.

## Final Target Architecture

Image -\> Scene -\> Subject -\> Material -\> Hair/Fur -\> Semantic
Validation -\> Consistency Engine -\> Region Graph -\> Regional Recipe
Generator -\> Matting -\> Decontamination -\> Quality Verification -\>
Export
