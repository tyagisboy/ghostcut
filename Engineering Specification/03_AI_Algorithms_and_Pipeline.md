# 03_AI_Algorithms_and_Pipeline

> GhostCut Offline -- AI Algorithms & Processing Pipeline (Living
> Specification)

## Objective

Define the complete AI processing pipeline, algorithm responsibilities,
decision logic, data flow, and quality strategy independent of any
single model implementation.

------------------------------------------------------------------------

# Pipeline Overview

Image Input → Image Analysis → Scene Analysis → Subject Classification →
Material Recognition → Hair/Fur Analysis → Pipeline Planning →
Segmentation → Confidence Estimation → Trimap Generation → Alpha Matting
→ Foreground Reconstruction → Edge Refinement → Color Decontamination →
Quality Verification → Local Repair → Export

------------------------------------------------------------------------

# 1. Image Analysis

## Purpose

Extract global descriptors before AI inference.

Algorithms - Histogram analysis - Exposure estimation - Blur detection -
Noise estimation - Dynamic range - White balance - Resolution analysis -
Sharpness estimation

Outputs - ImageProfile - ImageQualityScore

------------------------------------------------------------------------

# 2. Scene Analysis

Algorithms - Saliency estimation - Texture entropy - Edge density -
Background complexity - Subject occupancy - Lighting estimation

Outputs - SceneProfile - ComplexityScore

------------------------------------------------------------------------

# 3. Subject Classification

Primary Goal

Determine processing strategy.

Supported Classes

-   Human
-   Pet
-   Product
-   Clothing
-   Vehicle
-   Furniture
-   Plant
-   Food
-   Transparent Object
-   Logo
-   Other

Outputs

SubjectProfile

------------------------------------------------------------------------

# 4. Material Recognition

Generate probability maps for

-   Skin
-   Hair
-   Fur
-   Fabric
-   Glass
-   Metal
-   Plastic
-   Leather
-   Wood
-   Feather
-   Water
-   Smoke

Output

MaterialMap

------------------------------------------------------------------------

# 5. Hair & Fur Analysis

Estimate

Hair - Type - Curl - Density - Thickness - Flyaway probability -
Transparency

Fur - Length - Density - Softness - Whiskers

Outputs

HairConfidenceMap

FurConfidenceMap

------------------------------------------------------------------------

# 6. Pipeline Planner

Generate an adaptive ProcessingRecipe.

Decision Inputs

-   Image Profile
-   Scene Profile
-   Subject
-   Materials
-   Hair/Fur
-   Hardware
-   User Preferences
-   Local Learning Database

Decision Outputs

-   Segmentation model
-   Matting model
-   Trimap width
-   Radius field
-   Decontamination strength
-   Multi-scale mode
-   Export profile

------------------------------------------------------------------------

# 7. Segmentation

Primary Model

BiRefNet

Fallback

-   RMBG
-   IS-Net
-   U²-Net

Responsibilities

-   Initial foreground extraction
-   Probability map generation
-   Segmentation confidence

Output

InitialMask

------------------------------------------------------------------------

# 8. Confidence Estimation

Generate confidence maps for

-   Segmentation
-   Hair
-   Fur
-   Materials
-   Edge quality
-   Transparency

Purpose

Guide every downstream algorithm.

------------------------------------------------------------------------

# 9. Trimap Generation

Inputs

-   Initial mask
-   Hair map
-   Fur map
-   Edge map

Algorithm

Adaptive unknown region expansion.

Unknown width depends on

-   Hair density
-   Fur density
-   Edge confidence
-   Texture

Output

Adaptive Trimap

------------------------------------------------------------------------

# 10. Alpha Matting

Primary

ViTMatte

Responsibilities

-   Recover fine alpha
-   Preserve transparency
-   Recover strands
-   Improve semi-transparent edges

Outputs

-   Alpha Matte
-   Matting Confidence

------------------------------------------------------------------------

# 11. Foreground Reconstruction

Purpose

Recover true foreground colours.

Algorithms

-   Background estimation
-   Foreground estimation
-   Alpha equation solving
-   Local propagation

Outputs

RecoveredForeground

------------------------------------------------------------------------

# 12. Edge Intelligence

Classify

-   Hard
-   Soft
-   Hair
-   Fur
-   Fabric
-   Transparent
-   Motion blur
-   Reflection
-   Shadow
-   Whisker

Output

EdgeMap

EdgeConfidence

------------------------------------------------------------------------

# 13. Adaptive Radius Field

Instead of fixed radius.

Generate per-pixel radius.

Range

1--16 pixels

Factors

-   Hair confidence
-   Fur confidence
-   Texture
-   Subject type
-   Edge confidence

Output

RadiusField

------------------------------------------------------------------------

# 14. Guided Refinement

Operations

-   Edge-aware guided filter
-   Radius field blending
-   Alpha smoothing
-   Detail preservation

Output

RefinedAlpha

------------------------------------------------------------------------

# 15. Color Decontamination

Purpose

Remove background spill.

Algorithm

Estimate

Foreground

Background

Recover

True foreground colours.

Adaptive strength

Depends on

-   Hair confidence
-   Material
-   Transparency

Output

DecontaminatedForeground

------------------------------------------------------------------------

# 16. Multi-Scale Refinement

Process

1.0×

0.5×

0.25×

Merge confidence maps.

Purpose

Recover both coarse structures and micro-details.

------------------------------------------------------------------------

# 17. Quality Verification

Detect

-   Halo
-   Jagged edges
-   Color spill
-   Missing strands
-   Alpha holes
-   Broken whiskers
-   Low-confidence regions

Generate

QualityReport

------------------------------------------------------------------------

# 18. Local Repair

Only repair failed regions.

Possible actions

-   Local rematting
-   Radius update
-   Halo cleanup
-   Hair recovery
-   Edge reconstruction

Output

PatchedResult

------------------------------------------------------------------------

# 19. Learning Engine

Store

-   Image descriptors
-   Processing recipe
-   Runtime metrics
-   User feedback

Generate

Recommended parameters.

------------------------------------------------------------------------

# 20. Export Pipeline

Support

-   PNG 8-bit alpha
-   PNG 16-bit alpha
-   TIFF
-   WebP

Preserve

-   EXIF
-   ICC profile
-   DPI
-   Metadata

------------------------------------------------------------------------

# Data Contracts

Every algorithm must expose

Inputs

Outputs

Confidence

Execution time

Diagnostics

Version

------------------------------------------------------------------------

# Performance Goals

Fast Mode

Segmentation → Guided Refinement → Export

Quality Mode

Segmentation → Trimap → ViTMatte → Reconstruction → Export

Ultra Mode

Quality Mode + Multi-scale + Verification + Local Repair

------------------------------------------------------------------------

# Long-Term Objective

Every image should receive an automatically generated processing recipe
based on measurable image characteristics rather than fixed parameters.
Algorithms should remain modular, independently benchmarkable, and
replaceable without changing the surrounding pipeline.
