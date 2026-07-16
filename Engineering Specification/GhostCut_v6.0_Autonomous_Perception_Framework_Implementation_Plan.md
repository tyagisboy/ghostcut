# GhostCut Autonomous Perception Framework (APF) v6.0

## Implementation Plan (Post Vision Evaluation Framework)

## Purpose

After Vision Evaluation Framework measures performance, GhostCut should
become capable of **improving its decisions automatically**. The focus
shifts from evaluation to autonomous perception refinement while keeping
the same segmentation models.

------------------------------------------------------------------------

# Phase 1 --- Perception Orchestrator

Create `src/core/perception/`

Modules:

-   perception_orchestrator.py
-   perception_state.py
-   perception_memory.py
-   perception_rules.py

Responsibilities:

-   Coordinate every runtime
-   Maintain image understanding state
-   Prevent contradictory decisions
-   Expose one unified perception object

------------------------------------------------------------------------

# Phase 2 --- Region Intelligence

Instead of treating the foreground as one object, divide it into
semantic regions.

Regions:

-   Face
-   Hair
-   Beard
-   Eyebrows
-   Skin
-   Fabric
-   Fur
-   Glass
-   Metal
-   Transparent
-   Shadow
-   Accessories

Each region stores:

-   confidence
-   edge type
-   transparency
-   refinement policy
-   repair priority

------------------------------------------------------------------------

# Phase 3 --- Region Policy Engine

Replace global parameters with region policies.

Examples:

Hair: - preserve strands - soft alpha - decontamination enabled

Skin: - crisp edge - no transparency

Glass: - preserve opacity gradients

Fur: - preserve flyaway fibers

------------------------------------------------------------------------

# Phase 4 --- Repair Planner

Create a planner that repairs only problematic regions.

Repairs:

-   halo
-   clipped hair
-   lost transparency
-   color spill
-   jagged edge
-   missing whiskers
-   noisy alpha

Never rerun the entire pipeline.

------------------------------------------------------------------------

# Phase 5 --- Perception Memory

Store successful perception decisions.

Track:

-   image fingerprint
-   region policies
-   repair history
-   final quality score

Reuse successful policies for similar images.

------------------------------------------------------------------------

# Phase 6 --- Adaptive Policy Library

Create reusable policies:

-   Studio Portrait
-   Outdoor Portrait
-   Curly Hair
-   Straight Hair
-   Wet Hair
-   Pets
-   Jewelry
-   Glass
-   Plants
-   Food
-   Industrial Objects

Policies are selected automatically.

------------------------------------------------------------------------

# Phase 7 --- Explainability Dashboard v3

Display:

-   Perception Graph
-   Active Region Policies
-   Repair Plan
-   Quality Risk
-   Final Vision Score
-   Region Scores

------------------------------------------------------------------------

# Phase 8 --- Benchmark Expansion

Every benchmark now validates:

-   region detection
-   region policy
-   repair planner
-   policy reuse
-   execution time
-   memory reuse

------------------------------------------------------------------------

# Deliverables

-   Perception Orchestrator
-   Region Intelligence Engine
-   Region Policy Engine
-   Targeted Repair Planner
-   Adaptive Policy Library
-   Perception Memory
-   Explainability Dashboard v3

------------------------------------------------------------------------

# Success Criteria

-   Zero full-pipeline reprocessing for localized defects.
-   Every image processed using region-specific policies.
-   Repair decisions are explainable.
-   Memory improves policy selection over time.
-   Better quality with equal or lower CPU cost.
