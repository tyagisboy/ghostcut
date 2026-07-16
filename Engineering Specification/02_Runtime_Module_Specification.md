# GhostCut Offline -- Runtime Module Specification

> Version: 1.0 (Living Specification)

## Runtime Design Rules

Every runtime module must:

-   Be independently testable.
-   Expose a stable interface.
-   Accept structured input only.
-   Return structured output only.
-   Never modify global state.
-   Emit confidence scores where applicable.
-   Be replaceable without affecting other runtimes.

------------------------------------------------------------------------

# Runtime 01 -- Image Intelligence

## Responsibility

Analyze raw image characteristics before any AI processing.

### Inputs

-   RGB image
-   EXIF metadata (optional)

### Outputs

ImageProfile: - Resolution - Aspect Ratio - Orientation - Histogram -
Exposure - Dynamic Range - White Balance - Blur Score - Noise Score -
Sharpness Score

Used By: - Scene Intelligence - Pipeline Planner

------------------------------------------------------------------------

# Runtime 02 -- Scene Intelligence

## Responsibility

Understand the overall scene complexity.

### Inputs

-   RGB image
-   ImageProfile

### Outputs

SceneProfile: - Background Complexity - Texture Entropy - Edge Density -
Saliency Map - Subject Occupancy - Lighting Type - Clutter Score

Used By: - Pipeline Planner

------------------------------------------------------------------------

# Runtime 03 -- Subject Intelligence

## Responsibility

Detect subject category.

### Inputs

-   RGB image
-   SceneProfile

### Outputs

SubjectProfile: - Subject Type - Detection Confidence - Bounding
Regions - Pose Estimate - Occlusion Score

Supported Classes: Human, Pet, Product, Vehicle, Furniture, Plant,
Transparent Object, Clothing, Food, Logo, Other.

------------------------------------------------------------------------

# Runtime 04 -- Material Intelligence

## Responsibility

Generate material probability maps.

### Inputs

-   RGB image
-   SubjectProfile

### Outputs

MaterialMap: - Skin - Hair - Fur - Fabric - Glass - Metal - Plastic -
Leather - Wood - Feather - Water - Smoke

------------------------------------------------------------------------

# Runtime 05 -- Hair Intelligence

## Responsibility

Estimate hair properties.

### Inputs

-   RGB image
-   MaterialMap
-   SubjectProfile

### Outputs

HairProfile: - Hair Type - Curl Probability - Strand Thickness -
Density - Flyaway Probability - Transparency - Hair Confidence Map

------------------------------------------------------------------------

# Runtime 06 -- Fur Intelligence

## Responsibility

Estimate fur characteristics.

### Outputs

FurProfile: - Fur Length - Density - Softness - Ear Fur - Tail Fur -
Whisker Map - Fur Confidence Map

------------------------------------------------------------------------

# Runtime 07 -- Pipeline Planner

## Responsibility

Generate a processing recipe.

### Inputs

ImageProfile SceneProfile SubjectProfile MaterialMap HairProfile
FurProfile HardwareProfile UserSettings

### Outputs

ProcessingRecipe: - Segmentation Model - Trimap Strategy - Matting
Model - Radius Field - Decontamination Strength - Alpha Parameters -
Multi-scale Flag - Export Profile

------------------------------------------------------------------------

# Runtime 08 -- Segmentation Engine

## Responsibility

Generate initial foreground mask.

Primary Model: BiRefNet

Fallback Models: - RMBG - IS-Net - U2Net

### Outputs

InitialMask SegmentationConfidence

------------------------------------------------------------------------

# Runtime 09 -- Trimap Generator

## Responsibility

Generate adaptive trimap.

### Inputs

InitialMask Hair/Fur Maps Edge Maps

### Outputs

Trimap Unknown Region Width Map

------------------------------------------------------------------------

# Runtime 10 -- Alpha Matting

Primary: ViTMatte

### Inputs

RGB Image Trimap

### Outputs

Alpha Matte Matting Confidence

------------------------------------------------------------------------

# Runtime 11 -- Foreground Reconstruction

## Responsibility

Recover true foreground colors.

### Inputs

RGB Image Alpha Matte

### Outputs

Foreground RGB Background Estimate Recovered Image

------------------------------------------------------------------------

# Runtime 12 -- Edge Intelligence

## Responsibility

Classify every edge.

Edge Types: - Hard - Soft - Hair - Fur - Fabric - Transparent - Shadow -
Reflection - Motion Blur - Whisker

Outputs: EdgeMap EdgeConfidence

------------------------------------------------------------------------

# Runtime 13 -- Refinement Engine

## Responsibility

Apply adaptive refinement.

Operations: - Guided Filtering - Radius Field - Color Decontamination -
Edge Sharpening - Halo Suppression - Alpha Smoothing

Output: Refined Matte

------------------------------------------------------------------------

# Runtime 14 -- Quality Verification

## Responsibility

Inspect output quality.

Checks: - Halo - Color Spill - Missing Hair - Jagged Edge - Alpha Hole -
Broken Whiskers - Low Confidence

Output: Quality Report Repair Requests

------------------------------------------------------------------------

# Runtime 15 -- Auto Repair Engine

## Responsibility

Reprocess only failing regions.

Strategies: - Local Matting - Local Radius Update - Halo Cleanup - Edge
Reconstruction - Hair Recovery

Output: Patched Matte

------------------------------------------------------------------------

# Runtime 16 -- Learning Engine

## Responsibility

Persist local intelligence.

Store: - Image Descriptors - Recipe - Runtime Statistics - User Feedback

Return: Parameter Suggestions

------------------------------------------------------------------------

# Runtime 17 -- Hardware Runtime

## Responsibility

Select execution backend.

Priority: 1. CUDA 2. DirectML 3. CPU

Manage: - Threads - Memory - Quantized Models - Tiled Processing

------------------------------------------------------------------------

# Runtime 18 -- Export Engine

## Responsibility

Produce final deliverables.

Formats: - PNG (8/16-bit Alpha) - TIFF - WebP

Preserve: - EXIF - ICC Profile - DPI

------------------------------------------------------------------------

# Shared Interface Contract

Every runtime exposes:

## Input

Typed Data Object

## Output

Typed Data Object

## Confidence

0.0--1.0

## Execution Time

## Diagnostics

## Errors

No runtime should directly call another runtime. Communication occurs
only through the Pipeline Planner and structured data contracts.

------------------------------------------------------------------------

# Dependency Flow

Image Intelligence → Scene Intelligence → Subject Intelligence →
Material Intelligence → Hair/Fur Intelligence → Pipeline Planner →
Segmentation → Trimap → Alpha Matting → Foreground Reconstruction → Edge
Intelligence → Refinement → Quality Verification → Auto Repair → Export

This document is a living interface specification. New runtimes may be
added without breaking existing contracts.
