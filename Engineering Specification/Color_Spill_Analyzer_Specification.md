# Color_Spill_Analyzer_Specification.md

# Color Spill Analyzer (CSA)

**Module ID:** CSA-001\
**Runtime Category:** Image Intelligence Engine\
**Status:** Engineering Specification v1.0 (Living Document)

------------------------------------------------------------------------

# Purpose

The Color Spill Analyzer (CSA) detects, quantifies, classifies, and
localizes unwanted background color contamination on foreground pixels,
particularly along semi-transparent boundaries. It produces diagnostic
maps and recovery guidance for the Foreground Reconstruction,
Decontamination, and Auto Repair runtimes without directly modifying
image pixels.

Typical spill sources include:

-   Green screen spill
-   Blue sky spill
-   Studio backdrop spill
-   Colored walls
-   Grass reflections
-   Water reflections
-   Clothing reflections
-   Environmental color bleed
-   Lens bloom around edges

------------------------------------------------------------------------

# Design Goals

-   Detect true color contamination without harming natural edge colors.
-   Distinguish color spill from natural lighting.
-   Preserve original foreground appearance.
-   Produce continuous confidence maps.
-   Remain independent from segmentation implementation.
-   Operate efficiently on CPU with optional GPU acceleration.

------------------------------------------------------------------------

# Responsibilities

1.  Detect foreground color contamination.
2.  Estimate local background color.
3.  Estimate spill strength.
4.  Classify spill type.
5.  Produce spill confidence maps.
6.  Generate recovery recommendations.
7.  Supply diagnostics to downstream runtimes.
8.  Support localized repair only.

------------------------------------------------------------------------

# Inputs

Required

-   RGB Image
-   Alpha Matte
-   Foreground Estimate
-   Background Estimate
-   Edge Map
-   Material Map

Optional

-   Hair Confidence Map
-   Fur Confidence Map
-   Transparency Map
-   Halo Map
-   Previous Repair Mask
-   Learning Engine Suggestions

------------------------------------------------------------------------

# Outputs

ColorSpillProfile

ColorSpillMask

ColorSpillConfidenceMap

BackgroundColorEstimate

ForegroundColorEstimate

RecoveryMask

RecoveryRecommendations

ColorSpillDiagnostics

------------------------------------------------------------------------

# Spill Categories

-   Green Spill
-   Blue Spill
-   Red Spill
-   Cyan Spill
-   Yellow Spill
-   Magenta Spill
-   Neutral Grey Spill
-   Mixed Environmental Spill
-   Reflection Spill
-   Unknown Spill

------------------------------------------------------------------------

# Processing Pipeline

Image

↓

Boundary Extraction

↓

Foreground / Background Sampling

↓

Color Space Conversion

↓

Local Background Estimation

↓

Foreground Color Estimation

↓

Spill Probability

↓

Confidence Fusion

↓

Color Spill Maps

------------------------------------------------------------------------

# Feature Extraction

Compute

-   RGB statistics
-   LAB statistics
-   HSV statistics
-   Chroma difference
-   Hue deviation
-   Saturation shift
-   Luminance consistency
-   Edge proximity
-   Alpha transition width
-   Local variance
-   Texture continuity
-   Reflection probability

------------------------------------------------------------------------

# Supported Color Spaces

-   RGB
-   Linear RGB
-   CIELAB
-   HSV
-   YCbCr

Color space selection is implementation configurable.

------------------------------------------------------------------------

# Detection Algorithms

Apply

-   Foreground/background color comparison
-   Chroma deviation analysis
-   Hue continuity analysis
-   Boundary sampling
-   Confidence-weighted neighborhood estimation
-   Adaptive local statistics
-   Multi-space voting

------------------------------------------------------------------------

# Spill Confidence Maps

Generate

-   Green Spill Confidence
-   Blue Spill Confidence
-   Reflection Confidence
-   Boundary Spill Confidence
-   Material Spill Confidence
-   Overall Spill Confidence

Range

0.0 → 1.0

------------------------------------------------------------------------

# Severity Levels

-   None
-   Very Low
-   Low
-   Moderate
-   High
-   Critical

------------------------------------------------------------------------

# Recovery Recommendations

Possible actions

-   Adaptive color decontamination
-   Foreground reconstruction
-   Local alpha refinement
-   Boundary recoloring
-   Halo inspection
-   Edge reconstruction
-   No correction required

------------------------------------------------------------------------

# Integration

Consumes

-   Material Intelligence Runtime
-   Alpha Reconstruction Runtime
-   Foreground Reconstruction Runtime
-   Transparency Intelligence Runtime
-   Edge Intelligence Runtime

Produces

-   ColorSpillProfile
-   SpillMask
-   RecoveryMask
-   RecoveryRecommendations

Used By

-   Foreground Reconstruction Runtime
-   Decontamination Runtime
-   Halo Detection Engine
-   Auto Repair Engine
-   Quality Verification Runtime

------------------------------------------------------------------------

# Configuration

-   enable_runtime
-   confidence_threshold
-   spill_threshold
-   color_space
-   chroma_weight
-   luminance_weight
-   alpha_weight
-   sampling_radius
-   cpu_tile_size
-   gpu_tile_size

------------------------------------------------------------------------

# Diagnostics

Report

-   Spill type
-   Spill area
-   Mean spill confidence
-   Dominant contamination color
-   Average severity
-   Runtime duration
-   Memory usage
-   Suggested corrective action

------------------------------------------------------------------------

# Failure Handling

If spill confidence is insufficient

-   Preserve original foreground colors
-   Flag uncertain regions
-   Avoid destructive correction
-   Pass diagnostics downstream

------------------------------------------------------------------------

# Performance Targets

CPU

-   \<300 ms (2 MP image)

Memory

-   \<150 MB additional RAM

Thread-safe

-   Yes

Deterministic

-   Yes

------------------------------------------------------------------------

# Interface Contract

Inputs

Structured runtime objects only.

Outputs

Structured runtime objects with:

-   Confidence
-   Diagnostics
-   Version
-   Execution metadata

No direct pixel modification is performed by this runtime.

------------------------------------------------------------------------

# Acceptance Criteria

The runtime is complete when it:

-   Detects background color contamination with high precision.
-   Correctly classifies spill type.
-   Produces reliable recovery masks.
-   Integrates with Foreground Reconstruction, Halo Detection, and Auto
    Repair.
-   Preserves natural foreground colors while minimizing false
    positives.
