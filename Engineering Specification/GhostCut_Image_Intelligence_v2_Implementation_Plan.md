# GhostCut Image Intelligence Engine v2 - Corrected Implementation Plan

This implementation plan supersedes the previous architecture by
replacing single-label image classification with a multi-attribute Image
Intelligence Profile.

## User Review Required

> Architecture Change: Images must not be classified into folders such
> as general, fur, glass or sharp_object. Every image generates an
> ImageProfile containing: - Scene - Subject - Background - Materials -
> Hair/Fur - Edge Types - Lighting - Confidence

> CPU First: Only lightweight analysis runs before AI inference.

> Regional Processing: Different alpha policies are applied to Hair,
> Skin, Fur, Glass, Fabric and other detected regions.

------------------------------------------------------------------------

# Proposed Architecture

Image → Fast Image Analysis → Initial Image Profile → Segmentation →
Subject Region Graph → Material + Edge Analysis → Adaptive Recipe Engine
→ Regional Processing → Confidence Verification → Local Repair → Export

------------------------------------------------------------------------

# Component 1 --- Image Intelligence

## NEW image_profile.py

Defines ImageProfile schema.

Stores: - Scene - Subject - Background - Lighting - Resolution - Noise -
Dynamic Range - Texture - Initial Confidence

------------------------------------------------------------------------

# Component 2 --- Scene Intelligence

## NEW scene.py

Detect: - Studio Portrait - Outdoor Portrait - Product - Pet - Vehicle -
Food - Document - Unknown

------------------------------------------------------------------------

# Component 3 --- Subject Intelligence

## NEW subject.py

Supports multiple simultaneous subjects: - Human - Animal - Product -
Plant - Mixed

------------------------------------------------------------------------

# Component 4 --- Background Intelligence

## NEW background.py

Measures: - Complexity - Dominant Colors - Gradient - Blur - Contrast -
Separation Difficulty

------------------------------------------------------------------------

# Component 5 --- Recipe Engine

## NEW recipe_engine.py

Consumes: - ImageProfile - HardwareProfile - UserPreferences

Produces InitialRecipe.

Selects: - Segmentation model - Execution provider - Precision - Tiling

------------------------------------------------------------------------

# Component 6 --- Segmentation

## MODIFY segmentation.py

Outputs: - Subject Mask - Segmentation Confidence - Region Masks

------------------------------------------------------------------------

# Component 7 --- Region Graph

## NEW region_graph.py

Create semantic regions: - Hair - Skin - Face - Beard - Eyes -
Clothing - Glass - Jewelry - Background

------------------------------------------------------------------------

# Component 8 --- Material Runtime

## NEW material_runtime.py

Outputs probability maps for: - Skin - Hair - Fur - Fabric - Glass -
Plastic - Metal - Leather - Lace - Feather

------------------------------------------------------------------------

# Component 9 --- Hair Runtime

## NEW hair_runtime.py

Detect: - Hair Type - Curl Level - Strand Density - Strand Thickness -
Flyaway Probability - Transparency - Direction

------------------------------------------------------------------------

# Component 10 --- Fur Runtime

## NEW fur_runtime.py

Detect: - Long Fur - Short Fur - Fine Fur - Dense Fur - Whiskers

------------------------------------------------------------------------

# Component 11 --- Edge Runtime

## NEW edge_runtime.py

Classify: - Hard - Soft - Hair - Fur - Fabric - Transparent -
Reflection - Motion Blur - Shadow

------------------------------------------------------------------------

# Component 12 --- Regional Recipe Engine

## NEW regional_recipe.py

Generate per-region policies.

Hair: - Radius 12 - Soft Alpha

Skin: - Radius 2 - Hard Alpha

Glass: - Transparency Mode

Fabric: - Medium Refinement

------------------------------------------------------------------------

# Component 13 --- Confidence Runtime

Generate: - Segmentation Confidence - Material Confidence - Hair
Confidence - Edge Confidence - Alpha Confidence

------------------------------------------------------------------------

# Component 14 --- Local Repair

## MODIFY quality.py

Repair only low-confidence regions.

------------------------------------------------------------------------

# Component 15 --- Explain Runtime

Log: - Decisions - Parameters - Confidence - Runtime - Region Policies

------------------------------------------------------------------------

# Component 16 --- Validation

Validate: - Runtime Graph - Dependencies - Policies - Memory

------------------------------------------------------------------------

# Component 17 --- Synthetic Testing

Generate ImageProfiles and validate recipes without AI inference.

------------------------------------------------------------------------

# Component 18 --- GUI

Display: - Image Profile - Region Graph - Materials - Hair Type -
Confidence - Recipe - Decision Log

------------------------------------------------------------------------

# Verification Plan

Automated: 1. Runtime Graph Validation 2. Recipe Validation 3. Synthetic
Profiles 4. Policy Validation 5. Memory Validation

Real Benchmark: Run only 50--100 benchmark images after all automated
validation passes.

------------------------------------------------------------------------

# Success Criteria

-   Every image produces an ImageProfile.
-   No single-label categories.
-   Recipes generated per region.
-   Heavy AI only for low-confidence areas.
-   Automated validation before inference.
-   Better quality with fewer iterations.
