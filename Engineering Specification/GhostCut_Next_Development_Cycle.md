# GhostCut Next Development Cycle

## Primary Objective

Transform GhostCut from a linear background removal pipeline into an
adaptive **Image Intelligence Engine** where every image is analyzed
first, a processing recipe is generated, and only the required AI
modules are executed.

Goals:

-   Adobe-class quality
-   CPU-first with optional GPU acceleration
-   Minimal unnecessary inference
-   Region-aware alpha
-   Material-aware refinement
-   Confidence-driven processing
-   Explainable decision making

------------------------------------------------------------------------

# Priority 1 --- Adaptive Processing Recipe Engine

Generate a processing recipe before AI inference.

Responsibilities:

-   Select segmentation model
-   Select matting model
-   Configure trimap
-   Configure radius field
-   Configure decontamination
-   Configure multi-scale refinement
-   Configure quality verification
-   Configure export profile

Inputs:

-   Image Profile
-   Scene Profile
-   Subject Profile
-   Material Profile
-   Hair/Fur Profile
-   Hardware Profile
-   User Preferences

Outputs:

-   ProcessingRecipe

------------------------------------------------------------------------

# Priority 2 --- Image Scenario Classifier

Detect image scenario before segmentation.

Supported scenarios:

-   Studio Portrait
-   Outdoor Portrait
-   Backlit Portrait
-   Product
-   Pet
-   Transparent Object
-   Clothing
-   Jewelry
-   Vehicle
-   Food
-   Plant

Each scenario activates a dedicated processing policy.

------------------------------------------------------------------------

# Priority 3 --- Material Intelligence

Recognize:

-   Skin
-   Hair
-   Fur
-   Fabric
-   Glass
-   Plastic
-   Metal
-   Leather
-   Feather
-   Lace
-   Water
-   Smoke

Outputs:

-   Material Probability Map
-   Material Confidence

------------------------------------------------------------------------

# Priority 4 --- Edge Intelligence

Edge classes:

-   Hard
-   Soft
-   Hair
-   Fur
-   Fabric
-   Transparent
-   Reflection
-   Motion Blur
-   Shadow
-   Whisker

Each edge class uses different refinement rules.

------------------------------------------------------------------------

# Priority 5 --- Region-Based Alpha Policies

Apply different alpha behaviour by material.

Examples:

Hair: - Soft continuous alpha - Strand preservation

Skin: - Crisp hard alpha

Glass: - Transparency-aware alpha

Fur: - Fibre preservation

Lace: - Semi-transparent alpha

------------------------------------------------------------------------

# Priority 6 --- Adaptive Radius Field

Generate per-pixel radius but should be adaptive and dynamic based on hair thiokness, type, flow and direction. 

Examples:

-   Hair → 12 px
-   Skin → 2 px
-   Glass → 8 px
-   Whiskers → 15 px

Based on:

-   Hair confidence
-   Edge confidence
-   Material
-   Transparency
-   Texture

------------------------------------------------------------------------

# Priority 7 --- Confidence Engine

Generate confidence maps:

-   Segmentation
-   Hair
-   Fur
-   Material
-   Edge
-   Transparency
-   Alpha
-   Reconstruction

Confidence maps guide downstream processing.

------------------------------------------------------------------------

# Priority 8 --- Confidence-Driven Local Repair

Workflow:

Segmentation → Confidence Analysis → Low Confidence Region → Crop Region
→ High Quality Processing → Merge → Continue

Benefits:

-   Less CPU work
-   Lower memory
-   Better hair recovery
-   Better edge quality

------------------------------------------------------------------------

# Priority 9 --- Policy-Based Configuration

Replace hard-coded values with editable policies.

Example:

Curly Hair: - Adaptive trimap - Dynamic radius - Soft alpha

Straight Hair: - Narrow trimap - Hard alpha

Glass: - Transparency-aware processing

------------------------------------------------------------------------

# Priority 10 --- Explainable Decision Logging

Record every important decision.

Example:

Background Complexity = High → BiRefNet-General selected

Hair Density = 0.91 → Hair Recovery enabled

Glass Confidence = 0.84 → Transparency processing enabled

------------------------------------------------------------------------

# Priority 11 --- Runtime Validation

Validate:

-   Inputs
-   Outputs
-   Dependencies
-   Configuration
-   Confidence
-   Performance

No image inference required.

------------------------------------------------------------------------

# Priority 12 --- Synthetic Benchmark Profiles

Generate virtual image profiles instead of repeatedly processing real
images.

Example:

Subject: Human

Hair: Tight Curly

Background: Complex

Lighting: Backlit

Expected Recipe:

-   BiRefNet-General
-   ViTMatte
-   Hair Recovery
-   Multi-scale
-   Local Repair

Compare expected and generated recipes automatically.

------------------------------------------------------------------------

# Priority 13 --- Architecture Test Framework

Automate:

-   Rule-based tests
-   Property-based tests
-   Pipeline validation
-   Runtime graph validation
-   Configuration validation
-   Regression tests

Run before real-image testing.

------------------------------------------------------------------------

# Recommended Workflow

Architecture → Runtime Validation → Decision Simulation → Synthetic
Benchmark Profiles → Property Tests → Real Benchmark Suite (50--100
images) → Release Candidate

------------------------------------------------------------------------

# Expected Benefits

Quality

-   Better hair extraction
-   Better transparency
-   Better material-aware alpha
-   Fewer halos

Performance

-   Lower CPU usage
-   Reduced memory
-   Less unnecessary inference

Engineering

-   Easier debugging
-   Faster development
-   Fewer regression bugs
-   Explainable AI decisions

------------------------------------------------------------------------

# Long-Term Vision

GhostCut becomes an adaptive Image Intelligence Platform where every
image receives a custom processing recipe before execution, enabling
higher quality, lower resource usage, and significantly fewer
development iterations.
