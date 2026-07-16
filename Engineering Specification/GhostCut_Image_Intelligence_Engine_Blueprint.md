# GhostCut Offline v2.x -- Image Intelligence Engine Blueprint

## Vision

Transform GhostCut Offline from a segmentation-first application into an
**Image Intelligence Engine** that analyzes every image before deciding
how to process it.

------------------------------------------------------------------------

# Stage 1 -- Image Intelligence

Analyze before segmentation.

## Compute

-   Resolution
-   Width / Height
-   Aspect Ratio
-   Megapixels
-   Orientation
-   EXIF Orientation
-   DPI

## Exposure Analysis

-   Histogram
-   Dynamic Range
-   White Balance
-   Brightness
-   Contrast
-   Shadows
-   Highlights
-   HDR Probability

## Questions

-   Underexposed?
-   Overexposed?
-   Flat Lighting?
-   HDR Scene?

------------------------------------------------------------------------

# Stage 2 -- Scene Understanding

Estimate global scene complexity.

## Compute

-   Background Entropy
-   Background Texture
-   Edge Density
-   Frequency Spectrum
-   Background Saliency
-   Background Confidence
-   Blur Score
-   Noise Level

Decision:

-   Simple Background
-   Moderate Background
-   Highly Cluttered Background

------------------------------------------------------------------------

# Stage 3 -- Subject Detection

Classify subject before refinement.

Possible classes:

-   Human Adult
-   Human Child
-   Pet Dog
-   Pet Cat
-   Bird
-   Wildlife
-   Product
-   Vehicle
-   Furniture
-   Clothing
-   Shoes
-   Jewelry
-   Food
-   Plant
-   Transparent Object
-   Logo

Each subject routes to a dedicated processing pipeline.

------------------------------------------------------------------------

# Stage 4 -- Hair Intelligence

Classify hair.

Possible classes:

-   Straight
-   Wavy
-   Curly
-   Afro
-   Braided
-   Wet Hair
-   Flyaway Hair
-   Messy Hair
-   Thin Hair
-   Thick Hair
-   Dense Hair
-   Blonde
-   White
-   Grey
-   Black

Decisions:

-   Trimap Width
-   Guided Radius
-   Alpha Refinement
-   Sharpening
-   Halo Suppression

------------------------------------------------------------------------

# Stage 5 -- Fur Intelligence

Detect fur characteristics.

Classes:

-   Short Fur
-   Long Fur
-   Dense Fur
-   Fluffy Fur
-   Wire Fur
-   Ear Fur
-   Tail Fur
-   Whiskers

Processing:

-   Fur Expansion
-   Whisker Recovery
-   Adaptive Alpha
-   Detail Reconstruction

------------------------------------------------------------------------

# Stage 6 -- Edge Intelligence

Every edge receives a label.

Edge Types

-   Hard Edge
-   Soft Edge
-   Hair Edge
-   Fur Edge
-   Fabric Edge
-   Transparent Edge
-   Shadow Edge
-   Reflection Edge
-   Motion Blur Edge
-   Whisker Edge

Each edge receives different refinement.

------------------------------------------------------------------------

# Stage 7 -- Material Intelligence

Recognize surface material.

Materials

-   Skin
-   Hair
-   Fur
-   Fabric
-   Leather
-   Plastic
-   Glass
-   Metal
-   Wood
-   Stone
-   Feather
-   Water
-   Smoke

Material influences:

-   Decontamination
-   Sharpening
-   Alpha Smoothing
-   Color Recovery

------------------------------------------------------------------------

# Stage 8 -- Multi-Confidence Maps

Generate multiple confidence maps.

## Hair Density

-   Sparse
-   Medium
-   Dense

## Strand Thickness

-   Fine
-   Medium
-   Thick

## Curl Probability

-   Straight
-   Wavy
-   Curly
-   Coiled

## Transparency Probability

-   Opaque
-   Semi Transparent
-   Transparent

Use all maps together during refinement.

------------------------------------------------------------------------

# Stage 9 -- Adaptive Radius Field

Replace fixed radius with a continuous per-pixel radius.

Radius Range

1 px → 16 px

Each pixel receives its own radius based on:

-   Hair Confidence
-   Texture
-   Edge Type
-   Subject Type

------------------------------------------------------------------------

# Stage 10 -- Multi-Model Routing

Instead of a fixed pipeline:

Human

BiRefNet → ViTMatte → Hair Refinement

Pet

BiRefNet → Fur Refinement → Whisker Recovery

Product

BiRefNet → Edge Optimization

Transparent Object

BiRefNet → Transparency Recovery

------------------------------------------------------------------------

# Stage 11 -- Quality Verification

After alpha generation, inspect the output.

Automatically detect:

-   Halo
-   Color Spill
-   Jagged Edges
-   Missing Hair
-   Broken Whiskers
-   Alpha Holes
-   Edge Noise
-   Low Confidence Regions

If defects are detected:

Reprocess only the affected region.

------------------------------------------------------------------------

# Stage 12 -- AI Decision Engine

Instead of fixed parameters, generate an image-specific recipe.

Example

``` json
{
  "model":"BiRefNet-General",
  "trimapExpansion":18,
  "hairRadius":11,
  "furRadius":14,
  "sharpen":0.25,
  "decontaminate":0.92,
  "alphaGamma":1.08,
  "whiskerRecovery":true,
  "haloRemoval":"adaptive",
  "edgeMode":"curly"
}
```

Decision inputs may include:

-   Subject Type
-   Hair Type
-   Fur Type
-   Background Complexity
-   Image Resolution
-   Contrast
-   Blur
-   Lighting
-   Material Type
-   Transparency Probability
-   Hair Density
-   Edge Confidence
-   User Preferences
-   Hardware Capability (CPU/GPU)
-   Previous Learning Database Results

------------------------------------------------------------------------

# Master Decision Pointer Matrix

For every imported image, build an Image Intelligence Report.

## Image Metrics

-   Resolution
-   Aspect Ratio
-   Orientation
-   Histogram
-   Dynamic Range
-   White Balance
-   Exposure
-   Noise
-   Sharpness

## Scene Metrics

-   Background Complexity
-   Texture Density
-   Saliency
-   Edge Density
-   Blur
-   Subject Occupancy

## Subject Metrics

-   Subject Category
-   Pose
-   Face Visibility
-   Occlusion
-   Confidence Score

## Hair/Fur Metrics

-   Hair Type
-   Curl Level
-   Strand Thickness
-   Hair Density
-   Flyaway Probability
-   Fur Density
-   Whisker Presence

## Edge Metrics

-   Edge Type
-   Alpha Confidence
-   Transition Width
-   Halo Probability
-   Color Spill Probability

## Material Metrics

-   Skin
-   Hair
-   Fabric
-   Glass
-   Metal
-   Plastic
-   Leather
-   Fur
-   Feather

## Pipeline Decisions

-   Segmentation Model
-   Trimap Strategy
-   Guided Filter Radius
-   Matting Model
-   Decontamination Strength
-   Alpha Gamma
-   Multi-scale Enabled
-   Foreground Reconstruction
-   Edge Repair
-   Export Quality

------------------------------------------------------------------------

# Final Vision

GhostCut should no longer think:

"How do I remove the background?"

Instead it should think:

"What am I looking at, what materials and edge types are present, and
what is the best possible processing pipeline for this specific image?"
