# GhostCut Offline -- Compact Engineering Specification (Living Blueprint)

## Purpose

Build a modular, offline AI background remover that automatically
analyzes every image, selects the optimal processing pipeline, produces
Adobe-class alpha mattes, and runs on low-end CPUs with optional GPU
acceleration.

## Core Principles

-   Offline first
-   Modular runtime architecture
-   Adaptive per-image decisions
-   Non-destructive processing
-   CPU compatible, GPU accelerated when available
-   Learning without cloud dependency

## Runtime Pipeline

Image Input → Image Intelligence → Scene Intelligence → Subject
Intelligence → Material Intelligence → Hair/Fur Intelligence → Pipeline
Planner → Segmentation → Trimap → Alpha Matting → Foreground
Reconstruction → Edge Refinement → Quality Verification → Auto Repair
(if needed) → Export

## Runtime Modules

### 1. Image Intelligence

Collect image descriptors: - Resolution, aspect ratio, orientation -
Histogram, exposure, dynamic range - Noise, sharpness, blur - White
balance, color statistics Output: Image Profile

### 2. Scene Intelligence

Measure: - Background complexity - Texture entropy - Edge density -
Saliency - Subject occupancy Output: Scene Profile

### 3. Subject Intelligence

Classify: Human, Pet, Product, Vehicle, Furniture, Plant, Clothing,
Jewelry, Transparent Object, Food, Logo. Output: Subject Profile

### 4. Material Intelligence

Recognize: Skin, Hair, Fur, Fabric, Glass, Metal, Plastic, Leather,
Wood, Stone, Feather, Water, Smoke. Output: Material Map

### 5. Hair & Fur Intelligence

Predict: - Hair type - Curl level - Strand thickness - Density - Flyaway
probability - Fur density - Whiskers Output: Hair/Fur Confidence Maps

### 6. Pipeline Planner

Select: - Segmentation model - Trimap strategy - Matting model - Guided
filter radius - Decontamination strength - Multi-scale mode - Export
profile Output: Processing Recipe

### 7. Segmentation

Primary: BiRefNet. Fallback models supported. Output: Initial Mask.

### 8. Trimap

Adaptive unknown region using edge, hair and confidence maps. Output:
Intelligent Trimap.

### 9. Alpha Matting

Primary: ViTMatte. Generate continuous alpha matte.

### 10. Foreground Reconstruction

Estimate foreground/background colors. Recover contaminated boundary
pixels. Suppress halos.

### 11. Edge Intelligence

Classify: Hard, Soft, Hair, Fur, Fabric, Transparent, Shadow,
Reflection, Motion Blur, Whisker. Apply edge-specific refinement.

### 12. Quality Verification

Detect: Halos, color spill, jagged edges, holes, broken strands, missing
whiskers, low-confidence regions. Reprocess only failing regions.

### 13. Learning Engine

Store: Image descriptors, parameters, user feedback. Recommend settings
for similar images. Never retrain automatically.

### 14. Hardware Runtime

Priority: CUDA → DirectML → CPU. Support quantized models.

### 15. Export Engine

Preserve: EXIF, ICC, DPI. Support PNG (8/16-bit alpha), TIFF, WebP.

## Master Decision Inputs

-   Image metrics
-   Scene metrics
-   Subject class
-   Material map
-   Hair/Fur maps
-   Edge maps
-   Lighting
-   Transparency
-   Blur
-   Hardware capability
-   User preferences
-   Historical learning

## Master Decision Outputs

-   Model selection
-   Trimap width
-   Radius field
-   Alpha refinement
-   Foreground reconstruction
-   Decontamination
-   Multi-scale enablement
-   Edge repair
-   Export quality

## Repository Structure

core/ intelligence/ planner/ segmentation/ matting/ reconstruction/
refinement/ verification/ learning/ export/ gui/ models/ tests/

Each runtime must: - expose a clean interface - accept typed inputs -
return structured outputs - be independently replaceable - support
benchmarking

## Engineering Rules

-   Never hard-code parameters when adaptive estimation is possible.
-   Separate analysis from execution.
-   Prefer confidence maps over binary decisions.
-   Reprocess locally instead of rerunning the full pipeline.
-   Keep every runtime independently testable.

## Long-Term Goal

GhostCut is an Image Intelligence Engine---not merely a background
remover. Every image receives a unique processing recipe generated from
measurable characteristics, enabling professional-quality offline
cutouts across portraits, pets, products, transparent objects, and
complex scenes.
